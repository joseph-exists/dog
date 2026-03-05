"""
Shadow outbox worker.

Processes pending shadow versions by committing them to local git repositories.

Configuration via env vars:
- SHADOW_OUTBOX_POLL_INTERVAL_SECONDS (default: 5)
- SHADOW_OUTBOX_BATCH_SIZE (default: 10)
- SHADOW_OUTBOX_LOCK_TTL_SECONDS (default: 60)
- SHADOW_OUTBOX_WORKER_ID (default: hostname:pid)
- SHADOW_OUTBOX_LOG_LEVEL (default: INFO)

Run:
    python -m app.services.shadow_outbox_worker
"""

from __future__ import annotations

import logging
import os
import random
import socket
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import or_
from sqlmodel import Session, select

from app.core.config import settings
from app.core.db import engine
from app.models import (
    RoomEvent,
    ShadowOutboxAttempt,
    ShadowOutboxJob,
    ShadowRepo,
    ShadowVersion,
)
from app.services.shadow_git import (
    CommitError,
    commit_snapshot,
    get_repo_remote_url,
    get_repo_path,
)

logger = logging.getLogger(__name__)


POLL_INTERVAL_SECONDS = int(os.getenv("SHADOW_OUTBOX_POLL_INTERVAL_SECONDS", "5"))
BATCH_SIZE = int(os.getenv("SHADOW_OUTBOX_BATCH_SIZE", "10"))
LOCK_TTL_SECONDS = int(os.getenv("SHADOW_OUTBOX_LOCK_TTL_SECONDS", "60"))
MAX_ATTEMPTS = int(os.getenv("SHADOW_OUTBOX_MAX_ATTEMPTS", "25"))
WORKER_ID = os.getenv("SHADOW_OUTBOX_WORKER_ID") or f"{socket.gethostname()}:{os.getpid()}"


def _now() -> datetime:
    return datetime.utcnow()


def _compute_backoff(attempt_count: int) -> timedelta:
    """Compute exponential backoff with jitter."""
    delays = [1, 10, 60, 300, 1800]
    idx = min(attempt_count - 1, len(delays) - 1)
    base = delays[idx]
    jitter = random.uniform(0.5, 1.5)
    return timedelta(seconds=int(base * jitter))


def _classify_error(exc: Exception) -> tuple[str, bool]:
    """
    Classify an exception for retry logic.

    Returns:
        Tuple of (error_type, is_fatal).
        Fatal errors won't be retried.
    """
    if isinstance(exc, CommitError):
        # Git commit failures are generally retryable
        return "git_commit_error", False
    if isinstance(exc, FileNotFoundError):
        return "file_not_found", True
    if isinstance(exc, PermissionError):
        return "permission_error", True
    if isinstance(exc, OSError):
        # Disk full, etc. - retryable
        return "os_error", False
    return "unknown_error", False


def _get_entity_repo_path(entity_type: str, entity_id: uuid.UUID) -> Path:
    """Get the local git repo path for an entity."""
    return get_repo_path(
        Path(settings.SHADOW_REPOS_PATH),
        entity_type,
        str(entity_id),
    )


def _build_room_redis_snapshot(
    *, session: Session, room_id: uuid.UUID
) -> dict[str, Any]:
    """Build a snapshot of room events for the room_events.redis.json file."""
    events = session.exec(
        select(RoomEvent)
        .where(RoomEvent.room_id == room_id)
        .order_by(RoomEvent.room_sequence.asc())
    ).all()
    return {
        "schema_version": 1,
        "entity_type": "room_redis",
        "room_id": str(room_id),
        "events": [
            {
                "type": "event",
                "sequence": event.room_sequence,
                "event_type": event.event_type,
                "payload": event.payload,
                "created_at": event.created_at.isoformat()
                if event.created_at
                else None,
            }
            for event in events
        ],
    }


def _process_job(job_id: uuid.UUID, worker_id: str) -> None:
    """Process a single shadow outbox job."""
    with Session(engine) as session:
        job = session.get(ShadowOutboxJob, job_id)
        if not job or job.status != "processing" or job.locked_by != worker_id:
            return

        shadow_version = session.get(ShadowVersion, job.shadow_version_id)
        shadow_repo = session.get(ShadowRepo, job.shadow_repo_id)
        if not shadow_version or not shadow_repo:
            job.status = "dead"
            job.last_error = "missing_shadow_repo_or_version"
            job.updated_at = _now()
            session.add(job)
            session.commit()
            return

        attempt_number = job.attempt_count + 1
        attempt = ShadowOutboxAttempt(
            outbox_job_id=job.id,
            attempt_number=attempt_number,
            started_at=_now(),
            result="started",
        )
        session.add(attempt)
        session.flush()

        repo_path = _get_entity_repo_path(shadow_repo.entity_type, shadow_repo.entity_id)
        repo_remote_url = get_repo_remote_url(
            settings.SHADOW_REPO_URL_TEMPLATE,
            shadow_repo.entity_type,
            str(shadow_repo.entity_id),
        )

        try:
            # Commit the main entity snapshot
            commit_sha = commit_snapshot(
                repo_path=repo_path,
                entity_type=shadow_repo.entity_type,
                snapshot_json=shadow_version.snapshot_json,
                message=shadow_version.message,
                remote_url=repo_remote_url,
                default_branch=settings.SHADOW_REPO_DEFAULT_BRANCH,
            )

            # For rooms, also commit the events snapshot
            if shadow_repo.entity_type == "room":
                room_snapshot = _build_room_redis_snapshot(
                    session=session,
                    room_id=shadow_repo.entity_id,
                )
                commit_sha = commit_snapshot(
                    repo_path=repo_path,
                    entity_type=shadow_repo.entity_type,
                    snapshot_json=room_snapshot,
                    message=f"{shadow_version.message} (redis events)",
                    filename="room_events.redis.json",
                    remote_url=repo_remote_url,
                    default_branch=settings.SHADOW_REPO_DEFAULT_BRANCH,
                )

            # Update version record
            shadow_version.commit_sha = commit_sha
            shadow_version.status = "committed"
            shadow_version.committed_at = _now()
            shadow_version.last_error = None
            shadow_version.updated_at = _now()
            session.add(shadow_version)

            # Mark job as complete
            job.status = "committed"
            job.attempt_count = attempt_number
            job.locked_at = None
            job.locked_by = None
            job.last_error = None
            job.last_error_at = None
            job.updated_at = _now()
            session.add(job)

            # Record successful attempt
            attempt.result = "success"
            attempt.finished_at = _now()
            attempt.forgejo_repo = str(repo_path)  # TODO: rename field in migration
            attempt.forgejo_commit_sha = commit_sha  # TODO: rename field in migration
            session.add(attempt)

            session.commit()
            logger.info(
                f"Committed shadow version {shadow_version.id} "
                f"({commit_sha[:8]}) to {repo_path}"
            )
            return

        except Exception as exc:
            error_type, is_fatal = _classify_error(exc)
            backoff = _compute_backoff(attempt_number)
            if attempt_number >= MAX_ATTEMPTS:
                is_fatal = True

            shadow_version.status = "error"
            shadow_version.last_error = str(exc)
            shadow_version.updated_at = _now()
            session.add(shadow_version)

            job.attempt_count = attempt_number
            job.last_error = str(exc)
            job.last_error_at = _now()
            job.locked_at = None
            job.locked_by = None
            job.updated_at = _now()
            if is_fatal:
                job.status = "dead"
            else:
                job.status = "retryable_error"
                job.run_after = _now() + backoff
            session.add(job)

            attempt.result = "fatal_error" if is_fatal else "retryable_error"
            attempt.error_type = error_type
            attempt.error_message = str(exc)
            attempt.finished_at = _now()
            session.add(attempt)

            session.commit()
            logger.warning(
                f"Shadow outbox job {job.id} failed ({error_type}); "
                f"fatal={is_fatal} attempt={attempt_number}"
            )


def _claim_jobs(session: Session, worker_id: str) -> list[uuid.UUID]:
    """Claim a batch of jobs for processing."""
    now = _now()
    stale_before = now - timedelta(seconds=LOCK_TTL_SECONDS)
    stmt = (
        select(ShadowOutboxJob)
        .where(
            ShadowOutboxJob.status.in_(["queued", "retryable_error", "processing"]),
            ShadowOutboxJob.run_after <= now,
            or_(
                ShadowOutboxJob.locked_at.is_(None),
                ShadowOutboxJob.locked_at < stale_before,
            ),
        )
        .order_by(ShadowOutboxJob.priority.asc(), ShadowOutboxJob.run_after.asc())
        .limit(BATCH_SIZE)
        .with_for_update(skip_locked=True)
    )
    jobs = list(session.exec(stmt).all())
    for job in jobs:
        job.status = "processing"
        job.locked_at = now
        job.locked_by = worker_id
        job.updated_at = now
        session.add(job)
    session.commit()
    return [job.id for job in jobs]


def run_worker() -> None:
    """Main worker loop."""
    logging.basicConfig(level=os.getenv("SHADOW_OUTBOX_LOG_LEVEL", "INFO"))
    logger.info(
        f"Shadow outbox worker starting (id={WORKER_ID}, "
        f"poll={POLL_INTERVAL_SECONDS}s, batch={BATCH_SIZE})"
    )
    while True:
        try:
            with Session(engine) as session:
                job_ids = _claim_jobs(session, WORKER_ID)
            if not job_ids:
                time.sleep(POLL_INTERVAL_SECONDS)
                continue
            for job_id in job_ids:
                _process_job(job_id, WORKER_ID)
        except Exception as exc:
            logger.exception(f"Shadow outbox worker loop error: {exc}")
            time.sleep(POLL_INTERVAL_SECONDS)


def repair_missing_outbox_jobs() -> int:
    """
    Repair job: create outbox rows for pending/error ShadowVersions with no job.
    """
    created = 0
    with Session(engine) as session:
        stmt = (
            select(ShadowVersion)
            .where(ShadowVersion.status.in_(["pending", "error"]))
            .where(
                ~ShadowVersion.id.in_(
                    select(ShadowOutboxJob.shadow_version_id)
                )
            )
        )
        versions = list(session.exec(stmt).all())
        for version in versions:
            repo = session.get(ShadowRepo, version.shadow_repo_id)
            if not repo:
                continue
            job = ShadowOutboxJob(
                shadow_repo_id=version.shadow_repo_id,
                shadow_version_id=version.id,
                entity_type=repo.entity_type,
                entity_id=repo.entity_id,
                status="queued",
                attempt_count=0,
                run_after=_now(),
                locked_at=None,
                locked_by=None,
                last_error=None,
                last_error_at=None,
                priority=100,
                created_at=_now(),
                updated_at=_now(),
            )
            session.add(job)
            created += 1
        session.commit()
    return created


def backfill_orphaned_repos(
    *,
    entity_types: list[str] | None = None,
    limit: int | None = None,
    dry_run: bool = False,
) -> dict[str, int]:
    """
    Backfill versions for ShadowRepos that have no versions.

    These orphaned repos were created due to a transaction bug where the repo
    was committed before the version/job. This function re-snapshots the
    current entity state and creates versions.

    Args:
        entity_types: Only backfill these types (default: all)
        limit: Max repos to process (default: unlimited)
        dry_run: If True, just count without creating

    Returns:
        Dict with counts: {'processed': N, 'created': N, 'skipped': N, 'errors': N}
    """
    from app.services.shadow_exporters import (
        build_agent_snapshot,
        build_persona_snapshot,
        build_room_snapshot,
        build_story_snapshot,
    )
    from app.models import User, UserAgentConfig, Story, Persona, Room

    # Map entity types to their snapshot builders
    snapshot_builders = {
        "agent": lambda session, entity_id: build_agent_snapshot(
            session=session, agent_id=entity_id
        ),
        "story": lambda session, entity_id: build_story_snapshot(
            session=session, story_id=entity_id
        ),
        "persona": lambda session, entity_id: build_persona_snapshot(
            session=session, persona_id=entity_id
        ),
        "room": lambda session, entity_id: build_room_snapshot(
            session=session, room_id=entity_id
        ),
    }

    stats = {"processed": 0, "created": 0, "skipped": 0, "errors": 0}

    with Session(engine) as session:
        # Find repos without versions
        repos_with_versions = session.exec(
            select(ShadowVersion.shadow_repo_id).distinct()
        ).all()
        version_repo_ids = set(repos_with_versions)

        stmt = select(ShadowRepo).where(~ShadowRepo.id.in_(version_repo_ids))
        if entity_types:
            stmt = stmt.where(ShadowRepo.entity_type.in_(entity_types))
        if limit:
            stmt = stmt.limit(limit)

        orphaned_repos = list(session.exec(stmt).all())
        logger.info(f"Found {len(orphaned_repos)} orphaned repos to backfill")

        for repo in orphaned_repos:
            stats["processed"] += 1

            if repo.entity_type not in snapshot_builders:
                logger.debug(
                    f"Skipping {repo.entity_type}/{repo.entity_id} - no snapshot builder"
                )
                stats["skipped"] += 1
                continue

            if dry_run:
                logger.info(f"[DRY RUN] Would backfill {repo.entity_type}/{repo.entity_id}")
                stats["created"] += 1
                continue

            try:
                # Build snapshot from current entity state
                snapshot = snapshot_builders[repo.entity_type](session, repo.entity_id)

                # Get owner for the version
                owner = session.get(User, repo.owner_id)
                if not owner:
                    logger.warning(f"Owner not found for repo {repo.id}, skipping")
                    stats["skipped"] += 1
                    continue

                # Create version
                version = ShadowVersion(
                    shadow_repo_id=repo.id,
                    commit_sha="pending",
                    version_number=1,
                    message=f"Backfill: initial snapshot of {repo.entity_type}",
                    snapshot_json=snapshot,
                    created_by_id=owner.id,
                    created_at=_now(),
                    status="pending",
                    committed_at=None,
                    last_error=None,
                    updated_at=_now(),
                )
                session.add(version)
                session.flush()

                # Create job
                job = ShadowOutboxJob(
                    shadow_repo_id=repo.id,
                    shadow_version_id=version.id,
                    entity_type=repo.entity_type,
                    entity_id=repo.entity_id,
                    status="queued",
                    attempt_count=0,
                    run_after=_now(),
                    locked_at=None,
                    locked_by=None,
                    last_error=None,
                    last_error_at=None,
                    priority=200,  # Lower priority than normal operations
                    created_at=_now(),
                    updated_at=_now(),
                )
                session.add(job)
                session.commit()

                logger.info(f"Backfilled {repo.entity_type}/{repo.entity_id}")
                stats["created"] += 1

            except Exception as exc:
                logger.warning(
                    f"Failed to backfill {repo.entity_type}/{repo.entity_id}: {exc}"
                )
                stats["errors"] += 1
                session.rollback()

    return stats


if __name__ == "__main__":
    mode = os.getenv("SHADOW_OUTBOX_MODE", "worker")
    if mode == "repair_missing_jobs":
        created = repair_missing_outbox_jobs()
        logger.info(f"Created {created} missing outbox jobs")
    elif mode == "backfill_orphaned_repos":
        entity_types = os.getenv("SHADOW_BACKFILL_TYPES", "").split(",")
        entity_types = [t.strip() for t in entity_types if t.strip()] or None
        limit = int(os.getenv("SHADOW_BACKFILL_LIMIT", "0")) or None
        dry_run = os.getenv("SHADOW_BACKFILL_DRY_RUN", "false").lower() == "true"
        stats = backfill_orphaned_repos(
            entity_types=entity_types,
            limit=limit,
            dry_run=dry_run,
        )
        logger.info(f"Backfill complete: {stats}")
    else:
        run_worker()
