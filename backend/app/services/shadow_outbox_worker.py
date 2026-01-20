from __future__ import annotations

"""
Shadow outbox worker (Milestone 3).

Configuration via env vars:
- SHADOW_OUTBOX_POLL_INTERVAL_SECONDS (default: 5)
- SHADOW_OUTBOX_BATCH_SIZE (default: 10)
- SHADOW_OUTBOX_LOCK_TTL_SECONDS (default: 60)
- SHADOW_OUTBOX_WORKER_ID (default: hostname:pid)
- SHADOW_OUTBOX_LOG_LEVEL (default: INFO)

Run:
    python -m app.services.shadow_outbox_worker
"""

import base64
import json
import logging
import os
import random
import socket
import time
import uuid
from datetime import datetime, timedelta
from typing import Any

import openapi_client
from openapi_client import ApiException, CreateFileOptions, CreateRepoOption, RepositoryApi, UpdateFileOptions, UserApi
from sqlalchemy import or_
from sqlmodel import Session, select

from app.core.db import engine
from app.models import (
    ShadowOutboxAttempt,
    ShadowOutboxJob,
    ShadowOutboxRepoLease,
    ShadowRepo,
    ShadowVersion,
)
from app.services.shadow_service import shadow_service

logger = logging.getLogger(__name__)


POLL_INTERVAL_SECONDS = int(os.getenv("SHADOW_OUTBOX_POLL_INTERVAL_SECONDS", "5"))
BATCH_SIZE = int(os.getenv("SHADOW_OUTBOX_BATCH_SIZE", "10"))
LOCK_TTL_SECONDS = int(os.getenv("SHADOW_OUTBOX_LOCK_TTL_SECONDS", "60"))
MAX_ATTEMPTS = int(os.getenv("SHADOW_OUTBOX_MAX_ATTEMPTS", "25"))
WORKER_ID = os.getenv("SHADOW_OUTBOX_WORKER_ID") or f"{socket.gethostname()}:{os.getpid()}"


def _now() -> datetime:
    return datetime.utcnow()


def _compute_backoff(attempt_count: int) -> timedelta:
    delays = [1, 10, 60, 300, 1800]
    idx = min(attempt_count - 1, len(delays) - 1)
    base = delays[idx]
    jitter = random.uniform(0.5, 1.5)
    return timedelta(seconds=int(base * jitter))


def _classify_error(exc: Exception) -> tuple[str, bool]:
    if isinstance(exc, RuntimeError):
        if str(exc).startswith("Missing service token"):
            return "missing_service_token", True
        if str(exc) == "repo_lease_busy":
            return "repo_lease_busy", False
    if isinstance(exc, ApiException):
        if exc.status in (401, 403):
            return f"forgejo_{exc.status}", True
        if exc.status == 404:
            return "forgejo_404", False
        if exc.status == 409:
            return "forgejo_409", False
        if exc.status >= 500:
            return f"forgejo_{exc.status}", False
        return f"forgejo_{exc.status}", True
    return "unknown_error", False


def _acquire_repo_lease(
    *, session: Session, shadow_repo_id: uuid.UUID, worker_id: str
) -> bool:
    stale_before = _now() - timedelta(seconds=LOCK_TTL_SECONDS)
    lease = session.exec(
        select(ShadowOutboxRepoLease)
        .where(ShadowOutboxRepoLease.shadow_repo_id == shadow_repo_id)
        .with_for_update()
    ).first()

    if lease is None:
        lease = ShadowOutboxRepoLease(
            shadow_repo_id=shadow_repo_id,
            locked_at=_now(),
            locked_by=worker_id,
        )
        session.add(lease)
        session.flush()
        return True

    if lease.locked_at is None or lease.locked_at < stale_before:
        lease.locked_at = _now()
        lease.locked_by = worker_id
        session.add(lease)
        session.flush()
        return True

    return False


def _release_repo_lease(
    *, session: Session, shadow_repo_id: uuid.UUID, worker_id: str
) -> None:
    lease = session.exec(
        select(ShadowOutboxRepoLease)
        .where(ShadowOutboxRepoLease.shadow_repo_id == shadow_repo_id)
        .with_for_update()
    ).first()
    if lease and lease.locked_by == worker_id:
        lease.locked_at = None
        lease.locked_by = None
        session.add(lease)


def _get_repo_api(entity_type: str) -> tuple[RepositoryApi, str]:
    token = shadow_service._get_service_token(entity_type)  # noqa: SLF001
    if not token:
        raise RuntimeError(f"Missing service token for entity type: {entity_type}")
    client = shadow_service._get_api_client(token)  # noqa: SLF001
    repo_api = RepositoryApi(client)
    owner = shadow_service._get_service_username(entity_type)  # noqa: SLF001
    try:
        user = UserApi(client).user_get_current()
        owner = user.to_dict().get("login") or user.to_dict().get("username") or owner
    except Exception:
        pass
    return repo_api, owner


def _ensure_forgejo_repo(
    *, session: Session, shadow_repo: ShadowRepo
) -> None:
    repo_api, owner = _get_repo_api(shadow_repo.entity_type)
    repo_name = shadow_repo.forgejo_repo_name
    try:
        repo = repo_api.repo_get(owner=owner, repo=repo_name)
        shadow_repo.forgejo_repo_id = repo.to_dict().get("id")
        session.add(shadow_repo)
        session.flush()
        return
    except ApiException as e:
        if e.status != 404:
            raise

    repo_options = CreateRepoOption(
        name=repo_name,
        description=f"Shadow repository for {shadow_repo.entity_type} {shadow_repo.entity_id}",
        private=True,
        auto_init=True,
    )
    created = repo_api.create_current_user_repo(body=repo_options)
    shadow_repo.forgejo_repo_id = created.to_dict().get("id")
    session.add(shadow_repo)
    session.flush()


def _commit_snapshot(
    *, shadow_repo: ShadowRepo, snapshot_json: dict[str, Any], message: str
) -> str:
    repo_api, owner = _get_repo_api(shadow_repo.entity_type)
    file_path = f"{shadow_repo.entity_type}.json"
    json_content = json.dumps(snapshot_json, indent=2, sort_keys=True, default=str)
    content_b64 = base64.b64encode(json_content.encode()).decode()

    try:
        existing_file = repo_api.repo_get_contents(
            owner=owner,
            repo=shadow_repo.forgejo_repo_name,
            filepath=file_path,
        )
        existing_sha = existing_file.to_dict().get("sha")
        update_options = UpdateFileOptions(
            content=content_b64,
            message=message,
            sha=existing_sha,
        )
        result = repo_api.repo_update_file(
            owner=owner,
            repo=shadow_repo.forgejo_repo_name,
            filepath=file_path,
            body=update_options,
        )
    except ApiException as e:
        if e.status != 404:
            raise
        create_options = CreateFileOptions(
            content=content_b64,
            message=message,
        )
        result = repo_api.repo_create_file(
            owner=owner,
            repo=shadow_repo.forgejo_repo_name,
            filepath=file_path,
            body=create_options,
        )

    result_dict = result.to_dict()
    return result_dict.get("commit", {}).get("sha", "unknown")


def _process_job(job_id: uuid.UUID, worker_id: str) -> None:
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

        try:
            if not _acquire_repo_lease(
                session=session, shadow_repo_id=shadow_repo.id, worker_id=worker_id
            ):
                raise RuntimeError("repo_lease_busy")

            _ensure_forgejo_repo(session=session, shadow_repo=shadow_repo)
            commit_sha = _commit_snapshot(
                shadow_repo=shadow_repo,
                snapshot_json=shadow_version.snapshot_json,
                message=shadow_version.message,
            )

            shadow_version.commit_sha = commit_sha
            shadow_version.status = "committed"
            shadow_version.committed_at = _now()
            shadow_version.last_error = None
            shadow_version.updated_at = _now()
            session.add(shadow_version)

            job.status = "committed"
            job.attempt_count = attempt_number
            job.locked_at = None
            job.locked_by = None
            job.last_error = None
            job.last_error_at = None
            job.updated_at = _now()
            session.add(job)

            attempt.result = "success"
            attempt.finished_at = _now()
            attempt.forgejo_repo = f"{_get_repo_api(shadow_repo.entity_type)[1]}/{shadow_repo.forgejo_repo_name}"
            attempt.forgejo_commit_sha = commit_sha
            session.add(attempt)

            _release_repo_lease(
                session=session, shadow_repo_id=shadow_repo.id, worker_id=worker_id
            )
            session.commit()
            return

        except Exception as exc:
            error_type, is_fatal = _classify_error(exc)
            backoff = _compute_backoff(attempt_number)
            if attempt_number >= MAX_ATTEMPTS:
                is_fatal = True

            if error_type != "repo_lease_busy":
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

            try:
                _release_repo_lease(
                    session=session, shadow_repo_id=shadow_repo.id, worker_id=worker_id
                )
            except Exception:
                pass

            session.commit()
            logger.warning(
                f"Shadow outbox job {job.id} failed ({error_type}); "
                f"fatal={is_fatal} attempt={attempt_number}"
            )


def _claim_jobs(session: Session, worker_id: str) -> list[uuid.UUID]:
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


def repair_missing_forgejo_commits(limit: int = 100) -> int:
    """
    Repair job: re-enqueue committed versions whose Forgejo file/commit is missing.
    """
    enqueued = 0
    with Session(engine) as session:
        stmt = (
            select(ShadowVersion)
            .where(ShadowVersion.status == "committed")
            .limit(limit)
        )
        versions = list(session.exec(stmt).all())
        for version in versions:
            shadow_repo = session.get(ShadowRepo, version.shadow_repo_id)
            if not shadow_repo:
                continue
            try:
                repo_api, owner = _get_repo_api(shadow_repo.entity_type)
                repo_api.repo_get_contents(
                    owner=owner,
                    repo=shadow_repo.forgejo_repo_name,
                    filepath=f"{shadow_repo.entity_type}.json",
                    ref=version.commit_sha,
                )
                continue
            except ApiException as exc:
                error_type, is_fatal = _classify_error(exc)
                if is_fatal:
                    continue
                existing = session.exec(
                    select(ShadowOutboxJob)
                    .where(ShadowOutboxJob.shadow_version_id == version.id)
                ).first()
                if not existing:
                    job = ShadowOutboxJob(
                        shadow_repo_id=shadow_repo.id,
                        shadow_version_id=version.id,
                        entity_type=shadow_repo.entity_type,
                        entity_id=shadow_repo.entity_id,
                        status="queued",
                        attempt_count=0,
                        run_after=_now(),
                        locked_at=None,
                        locked_by=None,
                        last_error=f"repair_missing_commit:{error_type}",
                        last_error_at=_now(),
                        priority=100,
                        created_at=_now(),
                        updated_at=_now(),
                    )
                    session.add(job)
                    enqueued += 1
        session.commit()
    return enqueued


if __name__ == "__main__":
    mode = os.getenv("SHADOW_OUTBOX_MODE", "worker")
    if mode == "repair_missing_jobs":
        created = repair_missing_outbox_jobs()
        logger.info(f"Created {created} missing outbox jobs")
    elif mode == "repair_missing_commits":
        enqueued = repair_missing_forgejo_commits()
        logger.info(f"Enqueued {enqueued} repair jobs for missing commits")
    else:
        run_worker()
