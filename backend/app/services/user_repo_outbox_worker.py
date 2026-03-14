"""
User repo outbox worker.

Processes pending user repo provisioning jobs asynchronously.
This handles importing/cloning repos from external sources into Gogs.

Configuration via env vars:
- USER_REPO_OUTBOX_BATCH_SIZE (default: 5)
- USER_REPO_OUTBOX_LOCK_TTL_SECONDS (default: 300 - longer for large repo clones)
- USER_REPO_OUTBOX_MAX_ATTEMPTS (default: 5)
- USER_REPO_OUTBOX_LOG_LEVEL (default: INFO)
"""

from __future__ import annotations

import logging
import os
import random
import uuid
from datetime import datetime, timedelta

from sqlalchemy import or_
from sqlmodel import Session, select

from app.core.db import engine
from app.models import UserRepo, UserRepoImportStatus, UserRepoOutboxJob
from app.services.user_repo_service import (
    UserRepoProvisioningError,
    user_repo_service,
)

logger = logging.getLogger(__name__)

BATCH_SIZE = int(os.getenv("USER_REPO_OUTBOX_BATCH_SIZE", "5"))
LOCK_TTL_SECONDS = int(os.getenv("USER_REPO_OUTBOX_LOCK_TTL_SECONDS", "300"))
MAX_ATTEMPTS = int(os.getenv("USER_REPO_OUTBOX_MAX_ATTEMPTS", "5"))
ACTIVE_JOB_STATUSES = ("queued", "retryable_error", "processing")


def _now() -> datetime:
    return datetime.utcnow()


def _compute_backoff(attempt_count: int) -> timedelta:
    """Compute exponential backoff with jitter for retries."""
    # Longer delays for repo cloning which can be slow
    delays = [30, 120, 300, 900, 1800]  # 30s, 2m, 5m, 15m, 30m
    idx = min(attempt_count - 1, len(delays) - 1)
    base = delays[idx]
    jitter = random.uniform(0.8, 1.2)
    return timedelta(seconds=int(base * jitter))


def _classify_error(exc: Exception) -> tuple[str, bool]:
    """
    Classify an exception for retry logic.

    Returns:
        Tuple of (error_type, is_fatal).
        Fatal errors won't be retried.
    """
    error_msg = str(exc).lower()

    if isinstance(exc, UserRepoProvisioningError):
        # Check for specific fatal conditions
        if "404" in error_msg and "org" in error_msg:
            return "org_not_found", True
        if "401" in error_msg or "403" in error_msg:
            return "auth_error", True
        # Most provisioning errors are retryable (network issues, timeouts)
        return "provisioning_error", False

    if isinstance(exc, TimeoutError):
        return "timeout", False

    if "connection" in error_msg or "network" in error_msg:
        return "network_error", False

    return "unknown_error", False


def _process_job(job_id: uuid.UUID, worker_id: str) -> None:
    """Process a single user repo outbox job."""
    with Session(engine) as session:
        job = session.get(UserRepoOutboxJob, job_id)
        if not job or job.status != "processing" or job.locked_by != worker_id:
            logger.debug(f"Job {job_id} no longer claimable, skipping")
            return

        user_repo = session.get(UserRepo, job.user_repo_id)
        if not user_repo:
            job.status = "dead"
            job.last_error = "user_repo_not_found"
            job.updated_at = _now()
            session.add(job)
            session.commit()
            logger.warning(f"User repo {job.user_repo_id} not found for job {job_id}")
            return

        # Respect terminal repo states: once canceled/failed, stop processing retries.
        if user_repo.import_status == UserRepoImportStatus.FAILED:
            job.status = "canceled"
            job.locked_at = None
            job.locked_by = None
            job.updated_at = _now()
            if not job.last_error:
                job.last_error = "import_canceled_or_failed"
                job.last_error_at = _now()
            session.add(job)
            session.commit()
            logger.info(
                f"Skipped user repo job {job_id}; repo {user_repo.id} is failed/canceled"
            )
            return

        attempt_number = job.attempt_count + 1

        try:
            # Provision the repo in Gogs
            remote = user_repo_service.ensure_user_repo_remote(
                session=session,
                user_repo=user_repo,
            )

            # Mark job as complete
            job.status = "completed"
            job.attempt_count = attempt_number
            job.locked_at = None
            job.locked_by = None
            job.last_error = None
            job.last_error_at = None
            job.updated_at = _now()
            session.add(job)
            session.commit()

            logger.info(
                f"Provisioned user repo {user_repo.id} ({user_repo.gogs_repo_name}) "
                f"-> {remote.html_url if remote else 'local only'}"
            )
            return

        except Exception as exc:
            error_type, is_fatal = _classify_error(exc)
            backoff = _compute_backoff(attempt_number)

            if attempt_number >= MAX_ATTEMPTS:
                is_fatal = True
                logger.warning(
                    f"User repo job {job_id} exceeded max attempts ({MAX_ATTEMPTS}), marking dead"
                )

            job.attempt_count = attempt_number
            job.last_error = f"{error_type}: {str(exc)[:500]}"
            job.last_error_at = _now()
            job.locked_at = None
            job.locked_by = None
            job.updated_at = _now()

            if is_fatal:
                job.status = "dead"
                # Also mark the user repo import as failed
                if user_repo.source_repo_url:
                    user_repo.import_status = UserRepoImportStatus.FAILED
                    user_repo.import_error = job.last_error
                    session.add(user_repo)
            else:
                job.status = "retryable_error"
                job.run_after = _now() + backoff

            session.add(job)
            session.commit()

            logger.warning(
                f"User repo job {job_id} failed ({error_type}); "
                f"fatal={is_fatal} attempt={attempt_number}"
            )


def _claim_jobs(session: Session, worker_id: str) -> list[uuid.UUID]:
    """Claim a batch of jobs for processing."""
    now = _now()
    stale_before = now - timedelta(seconds=LOCK_TTL_SECONDS)

    stmt = (
        select(UserRepoOutboxJob)
        .where(
            UserRepoOutboxJob.status.in_(ACTIVE_JOB_STATUSES),
            UserRepoOutboxJob.run_after <= now,
            or_(
                UserRepoOutboxJob.locked_at.is_(None),
                UserRepoOutboxJob.locked_at < stale_before,
            ),
        )
        .order_by(
            UserRepoOutboxJob.priority.asc(),
            UserRepoOutboxJob.run_after.asc(),
        )
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

    if jobs:
        logger.debug(f"Claimed {len(jobs)} user repo jobs")

    return [job.id for job in jobs]


def create_user_repo_outbox_job(
    *,
    session: Session,
    user_repo: UserRepo,
    priority: int = 100,
) -> UserRepoOutboxJob:
    """
    Create an outbox job for async user repo provisioning.

    Call this instead of user_repo_service.ensure_user_repo_remote()
    when you want async processing.
    """
    existing = session.exec(
        select(UserRepoOutboxJob)
        .where(
            UserRepoOutboxJob.user_repo_id == user_repo.id,
            UserRepoOutboxJob.status.in_(ACTIVE_JOB_STATUSES),
        )
        .order_by(UserRepoOutboxJob.created_at.desc())
        .limit(1)
    ).first()
    if existing is not None:
        return existing

    job = UserRepoOutboxJob(
        user_repo_id=user_repo.id,
        status="queued",
        priority=priority,
        attempt_count=0,
        run_after=_now(),
    )
    session.add(job)
    session.flush()
    return job


def cancel_user_repo_outbox_jobs(
    *,
    session: Session,
    user_repo_id: uuid.UUID,
    reason: str = "canceled_by_user",
) -> int:
    """Mark active user-repo outbox jobs as canceled so worker will ignore them."""
    jobs = list(
        session.exec(
            select(UserRepoOutboxJob).where(
                UserRepoOutboxJob.user_repo_id == user_repo_id,
                UserRepoOutboxJob.status.in_(ACTIVE_JOB_STATUSES),
            )
        ).all()
    )
    if not jobs:
        return 0

    now = _now()
    for job in jobs:
        job.status = "canceled"
        job.locked_at = None
        job.locked_by = None
        job.run_after = now
        job.updated_at = now
        job.last_error = reason
        job.last_error_at = now
        session.add(job)
    session.flush()
    return len(jobs)


def delete_user_repo_outbox_jobs(
    *,
    session: Session,
    user_repo_id: uuid.UUID,
) -> int:
    """Delete all outbox jobs for a user repo."""
    jobs = list(
        session.exec(
            select(UserRepoOutboxJob).where(UserRepoOutboxJob.user_repo_id == user_repo_id)
        ).all()
    )
    for job in jobs:
        session.delete(job)
    session.flush()
    return len(jobs)
