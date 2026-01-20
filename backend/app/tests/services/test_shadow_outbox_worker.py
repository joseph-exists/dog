from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlmodel import Session, select

from app import crud
from app.models import ShadowOutboxJob, ShadowRepo, ShadowVersion, User, UserCreate
from app.services.shadow_service import shadow_service
from app.services import shadow_outbox_worker


def _create_user(db: Session) -> uuid.UUID:
    user_in = UserCreate(email=f"shadow-outbox-{uuid.uuid4()}@example.com", password="password123")
    user = crud.create_user(session=db, user_create=user_in)
    return user.id


def _create_repo(db: Session, *, owner_id: uuid.UUID) -> ShadowRepo:
    entity_id = uuid.uuid4()
    repo = ShadowRepo(
        owner_id=owner_id,
        entity_type="agent",
        entity_id=entity_id,
        forgejo_repo_name=f"agent-{str(entity_id)[:8]}",
        forgejo_repo_id=None,
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return repo


def _create_version(
    db: Session, *, shadow_repo_id: uuid.UUID, created_by_id: uuid.UUID, status: str = "pending"
) -> ShadowVersion:
    version = ShadowVersion(
        shadow_repo_id=shadow_repo_id,
        commit_sha="pending",
        version_number=1,
        message="test version",
        snapshot_json={"entity_type": "agent"},
        created_by_id=created_by_id,
        status=status,
        updated_at=datetime.utcnow(),
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


def test_outbox_worker_success_commits(db: Session, monkeypatch) -> None:
    owner_id = _create_user(db)
    repo = _create_repo(db, owner_id=owner_id)
    version = _create_version(db, shadow_repo_id=repo.id, created_by_id=owner_id)

    job = ShadowOutboxJob(
        shadow_repo_id=repo.id,
        shadow_version_id=version.id,
        entity_type=repo.entity_type,
        entity_id=repo.entity_id,
        status="processing",
        attempt_count=0,
        run_after=datetime.utcnow(),
        locked_at=datetime.utcnow(),
        locked_by="test-worker",
        priority=100,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(job)
    db.commit()

    monkeypatch.setattr(shadow_outbox_worker, "_ensure_forgejo_repo", lambda **_: None)
    monkeypatch.setattr(shadow_outbox_worker, "_commit_snapshot", lambda **_: "abc123")

    shadow_outbox_worker._process_job(job.id, "test-worker")
    db.expire_all()

    updated_version = db.get(ShadowVersion, version.id)
    updated_job = db.get(ShadowOutboxJob, job.id)
    assert updated_version.status == "committed"
    assert updated_version.commit_sha == "abc123"
    assert updated_job.status == "committed"


def test_outbox_worker_retryable_sets_backoff(db: Session, monkeypatch) -> None:
    owner_id = _create_user(db)
    repo = _create_repo(db, owner_id=owner_id)
    version = _create_version(db, shadow_repo_id=repo.id, created_by_id=owner_id)

    job = ShadowOutboxJob(
        shadow_repo_id=repo.id,
        shadow_version_id=version.id,
        entity_type=repo.entity_type,
        entity_id=repo.entity_id,
        status="processing",
        attempt_count=0,
        run_after=datetime.utcnow(),
        locked_at=datetime.utcnow(),
        locked_by="test-worker",
        priority=100,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(job)
    db.commit()

    monkeypatch.setattr(
        shadow_outbox_worker, "_acquire_repo_lease", lambda **_: (_ for _ in ()).throw(RuntimeError("repo_lease_busy"))
    )

    shadow_outbox_worker._process_job(job.id, "test-worker")
    db.expire_all()

    updated_job = db.get(ShadowOutboxJob, job.id)
    updated_version = db.get(ShadowVersion, version.id)
    assert updated_job.status == "retryable_error"
    assert updated_job.run_after > datetime.utcnow() - timedelta(seconds=1)
    assert updated_version.status == "pending"


def test_outbox_worker_fatal_marks_dead(db: Session, monkeypatch) -> None:
    owner_id = _create_user(db)
    repo = _create_repo(db, owner_id=owner_id)
    version = _create_version(db, shadow_repo_id=repo.id, created_by_id=owner_id)

    job = ShadowOutboxJob(
        shadow_repo_id=repo.id,
        shadow_version_id=version.id,
        entity_type=repo.entity_type,
        entity_id=repo.entity_id,
        status="processing",
        attempt_count=0,
        run_after=datetime.utcnow(),
        locked_at=datetime.utcnow(),
        locked_by="test-worker",
        priority=100,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(job)
    db.commit()

    monkeypatch.setattr(
        shadow_outbox_worker,
        "_ensure_forgejo_repo",
        lambda **_: (_ for _ in ()).throw(RuntimeError("Missing service token for entity type: agent")),
    )

    shadow_outbox_worker._process_job(job.id, "test-worker")
    db.expire_all()

    updated_job = db.get(ShadowOutboxJob, job.id)
    updated_version = db.get(ShadowVersion, version.id)
    assert updated_job.status == "dead"
    assert updated_version.status == "error"


def test_repair_missing_outbox_jobs(db: Session) -> None:
    owner_id = _create_user(db)
    repo = _create_repo(db, owner_id=owner_id)
    version = _create_version(db, shadow_repo_id=repo.id, created_by_id=owner_id)

    created = shadow_outbox_worker.repair_missing_outbox_jobs()
    assert created >= 1
    db.expire_all()

    job = db.exec(
        select(ShadowOutboxJob).where(ShadowOutboxJob.shadow_version_id == version.id)
    ).first()
    assert job is not None


def test_repo_lease_blocks_second_worker(db: Session) -> None:
    owner_id = _create_user(db)
    repo = _create_repo(db, owner_id=owner_id)

    with Session(db.get_bind()) as session:
        assert shadow_outbox_worker._acquire_repo_lease(
            session=session, shadow_repo_id=repo.id, worker_id="worker-a"
        )
        session.commit()

    with Session(db.get_bind()) as session:
        assert not shadow_outbox_worker._acquire_repo_lease(
            session=session, shadow_repo_id=repo.id, worker_id="worker-b"
        )
        session.commit()


def test_enqueue_creates_version_and_job(db: Session, monkeypatch) -> None:
    owner_id = _create_user(db)
    entity_id = uuid.uuid4()

    monkeypatch.setattr(shadow_service, "_get_service_token", lambda *_: "test-token")

    version = shadow_service.enqueue_entity_version(
        session=db,
        user=db.get(User, owner_id),
        entity_type="agent",
        entity_id=entity_id,
        entity_data={"entity_type": "agent"},
        message="enqueue test",
    )
    assert version is not None
    assert version.status == "pending"

    job = db.exec(
        select(ShadowOutboxJob).where(ShadowOutboxJob.shadow_version_id == version.id)
    ).first()
    assert job is not None
