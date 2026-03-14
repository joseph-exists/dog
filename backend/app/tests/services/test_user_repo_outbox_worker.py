from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.models import User, UserCreate, UserRepo, UserRepoImportStatus, UserRepoOutboxJob
from app.services import user_repo_outbox_worker


def _create_user(db: Session) -> User:
    user_in = UserCreate(
        email=f"user-repo-outbox-{uuid.uuid4()}@example.com",
        password="password123",
    )
    return crud.create_user(session=db, user_create=user_in)


def _create_repo(
    db: Session,
    *,
    owner: User,
    import_status: UserRepoImportStatus = UserRepoImportStatus.IMPORTING,
) -> UserRepo:
    repo = UserRepo(
        owner_user_id=owner.id,
        slug=f"repo-{uuid.uuid4().hex[:8]}",
        display_name="Outbox Repo",
        description="Repo for outbox tests",
        source_repo_url="https://github.com/example/outbox-repo.git",
        source_branch=settings.USER_REPO_DEFAULT_BRANCH,
        import_status=import_status,
        import_error=None,
        imported_at=datetime.now(timezone.utc),
        gogs_repo_name=f"outbox-{uuid.uuid4().hex[:8]}",
        gogs_repo_id=None,
        gogs_full_name=None,
        gogs_html_url=None,
        is_private=False,
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return repo


def test_create_user_repo_outbox_job_deduplicates_active_jobs(db: Session) -> None:
    owner = _create_user(db)
    repo = _create_repo(db, owner=owner)

    first = user_repo_outbox_worker.create_user_repo_outbox_job(
        session=db,
        user_repo=repo,
    )
    second = user_repo_outbox_worker.create_user_repo_outbox_job(
        session=db,
        user_repo=repo,
    )
    db.commit()

    assert first.id == second.id
    jobs = list(
        db.exec(
            select(UserRepoOutboxJob).where(UserRepoOutboxJob.user_repo_id == repo.id)
        ).all()
    )
    assert len(jobs) == 1


def test_cancel_user_repo_outbox_jobs_marks_only_active_jobs(db: Session) -> None:
    owner = _create_user(db)
    repo = _create_repo(db, owner=owner)

    active_job = UserRepoOutboxJob(user_repo_id=repo.id, status="queued", priority=100)
    completed_job = UserRepoOutboxJob(
        user_repo_id=repo.id,
        status="completed",
        priority=100,
    )
    db.add(active_job)
    db.add(completed_job)
    db.commit()

    canceled_count = user_repo_outbox_worker.cancel_user_repo_outbox_jobs(
        session=db,
        user_repo_id=repo.id,
        reason="test_cancel",
    )
    db.commit()
    db.refresh(active_job)
    db.refresh(completed_job)

    assert canceled_count == 1
    assert active_job.status == "canceled"
    assert active_job.last_error == "test_cancel"
    assert completed_job.status == "completed"


def test_process_job_skips_when_repo_marked_failed(db: Session) -> None:
    owner = _create_user(db)
    repo = _create_repo(db, owner=owner, import_status=UserRepoImportStatus.FAILED)
    job = UserRepoOutboxJob(
        user_repo_id=repo.id,
        status="processing",
        priority=100,
        attempt_count=0,
        locked_at=datetime.utcnow(),
        locked_by="test-worker",
    )
    db.add(job)
    db.commit()

    user_repo_outbox_worker._process_job(job.id, "test-worker")
    db.expire_all()

    updated_job = db.get(UserRepoOutboxJob, job.id)
    assert updated_job is not None
    assert updated_job.status == "canceled"
