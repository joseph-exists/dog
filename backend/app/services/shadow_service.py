"""
Shadow Service

Provides automatic, invisible git-based versioning for application entities
by storing them in local git repositories. Each entity (agent, story, user, room)
gets its own repo with full JSON snapshots committed on every save.

Architecture:
- Each entity gets a git repo at {SHADOW_REPOS_PATH}/{entity_type}/{entity_id}/
- Worker processes pending versions via outbox pattern
- All operations happen automatically on entity save
- Users never see or interact with shadow repos directly

Usage:
    from app.services.shadow_service import shadow_service

    # On entity save (automatic, no user involvement):
    version = shadow_service.enqueue_entity_version(
        session=session,
        user=current_user,
        entity_type="agent",
        entity_id=agent.id,
        entity_data=agent.model_dump(),
        message="Update agent configuration"
    )
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core.config import settings
from app.models import (
    ShadowOutboxJob,
    ShadowRepo,
    ShadowRepoVersionCounter,
    ShadowUser,
    ShadowVersion,
    User,
)
from app.services.shadow_git import get_repo_path
from app.services.shadow_gogs_service import shadow_gogs_service
from app.services.repo_naming import shadow_repo_name

logger = logging.getLogger(__name__)


class ShadowService:
    """
    Service for automatic, invisible git-based entity versioning.

    Design decisions:
    - Repo-per-entity: Each agent/story/user/room gets its own git repository
    - Full JSON versioning: Complete snapshots, not diffs
    - Every save sync: Version created on each save operation
    - Pretty-printed JSON: For readable git diffs
    - Invisible to users: System manages all repos automatically
    """

    def is_enabled(self, entity_type: str | None = None) -> bool:
        """
        Check if shadow versioning is enabled.

        Args:
            entity_type: Optional entity type (ignored, kept for API compat)

        Returns:
            True if shadow versioning is enabled
        """
        return settings.SHADOW_ENABLED

    def get_entity_repo_path(self, entity_type: str, entity_id: uuid.UUID) -> Path:
        """
        Get the git repository path for an entity.

        Args:
            entity_type: Type of entity ('agent', 'story', etc.)
            entity_id: UUID of the entity

        Returns:
            Path to the entity's git repository
        """
        return get_repo_path(
            Path(settings.SHADOW_REPOS_PATH),
            entity_type,
            str(entity_id),
        )

    # =========================================================================
    # ShadowUser Management (User Profile Repos)
    # =========================================================================

    def ensure_shadow_user(
        self,
        session: Session,
        user: User,
    ) -> ShadowUser | None:
        """
        Get or create a ShadowUser profile repo for an application user.

        This is system-managed - users don't see or control it.

        Args:
            session: Database session
            user: Application User to shadow

        Returns:
            ShadowUser mapping record, or None if not enabled
        """
        if not self.is_enabled():
            logger.debug("Shadow versioning not enabled")
            return None

        # Check if shadow user already exists
        stmt = select(ShadowUser).where(ShadowUser.user_id == user.id)
        existing = session.exec(stmt).first()

        if existing:
            logger.debug(f"Found existing shadow user for {user.email}")
            return existing

        # Create the shadow user record (repo created lazily on first version)
        repo_name = shadow_repo_name("user", user.id)

        shadow_user = ShadowUser(
            user_id=user.id,
            forgejo_repo_name=repo_name,  # TODO: rename field in migration
            forgejo_repo_id=None,
            created_at=datetime.now(),
        )

        session.add(shadow_user)
        session.commit()
        session.refresh(shadow_user)

        logger.info(f"Created shadow user record for {user.email}: {repo_name}")
        return shadow_user

    def get_shadow_user(self, session: Session, user: User) -> ShadowUser | None:
        """Get existing ShadowUser for a user, if any."""
        stmt = select(ShadowUser).where(ShadowUser.user_id == user.id)
        return session.exec(stmt).first()

    # =========================================================================
    # ShadowRepo Management
    # =========================================================================

    def ensure_shadow_repo_db_only(
        self,
        session: Session,
        owner: User,
        entity_type: str,
        entity_id: uuid.UUID,
    ) -> ShadowRepo | None:
        """
        Create or fetch the DB ShadowRepo record only (no git IO).

        The worker will initialize the actual git repo when processing jobs.

        Args:
            session: Database session
            owner: User who owns this entity
            entity_type: Type of entity ('agent', 'story', etc.)
            entity_id: UUID of the entity

        Returns:
            ShadowRepo record, or None if not enabled
        """
        if not self.is_enabled():
            logger.debug("Shadow versioning not enabled")
            return None

        stmt = select(ShadowRepo).where(
            ShadowRepo.entity_type == entity_type,
            ShadowRepo.entity_id == entity_id,
        )
        existing = session.exec(stmt).first()
        if existing:
            return existing

        # repo_name kept for backward compat, but actual path is computed
        repo_name = shadow_repo_name(entity_type, entity_id)
        shadow_repo = ShadowRepo(
            owner_id=owner.id,
            entity_type=entity_type,
            entity_id=entity_id,
            forgejo_repo_name=repo_name,  # TODO: rename field in migration
            forgejo_repo_id=None,
            created_at=datetime.now(),
        )
        session.add(shadow_repo)
        # NOTE: Don't commit here - let caller commit atomically with version/job.
        # This prevents orphaned repos when version creation fails.
        session.flush()  # Get the ID without committing
        return shadow_repo

    def _allocate_next_version_number(
        self, session: Session, shadow_repo_id: uuid.UUID
    ) -> int:
        """
        Allocate the next per-repo ShadowVersion.version_number using a counter table.

        This avoids the race-prone "select max(version)+1" under concurrent enqueues.
        """
        while True:
            counter = session.exec(
                select(ShadowRepoVersionCounter)
                .where(ShadowRepoVersionCounter.shadow_repo_id == shadow_repo_id)
                .with_for_update()
            ).first()

            if counter is None:
                try:
                    counter = ShadowRepoVersionCounter(
                        shadow_repo_id=shadow_repo_id,
                        next_version_number=2,
                        updated_at=datetime.utcnow(),
                    )
                    session.add(counter)
                    session.flush()
                    return 1
                except IntegrityError:
                    session.rollback()
                    continue

            version_number = counter.next_version_number
            counter.next_version_number = counter.next_version_number + 1
            counter.updated_at = datetime.utcnow()
            session.add(counter)
            session.flush()
            return version_number

    def get_shadow_repo(
        self,
        session: Session,
        entity_type: str,
        entity_id: uuid.UUID,
    ) -> ShadowRepo | None:
        """Get existing ShadowRepo for an entity, if any."""
        stmt = select(ShadowRepo).where(
            ShadowRepo.entity_type == entity_type,
            ShadowRepo.entity_id == entity_id,
        )
        return session.exec(stmt).first()

    # =========================================================================
    # Version Management
    # =========================================================================

    def get_version_history(
        self,
        session: Session,
        shadow_repo: ShadowRepo,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ShadowVersion]:
        """
        Get version history for a shadow repo.

        Args:
            session: Database session
            shadow_repo: The shadow repo
            limit: Maximum versions to return
            offset: Number of versions to skip

        Returns:
            List of ShadowVersion records, newest first
        """
        stmt = (
            select(ShadowVersion)
            .where(ShadowVersion.shadow_repo_id == shadow_repo.id)
            .order_by(ShadowVersion.version_number.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(session.exec(stmt).all())

    def get_version(
        self,
        session: Session,
        shadow_repo: ShadowRepo,
        version_number: int | None = None,
        commit_sha: str | None = None,
    ) -> ShadowVersion | None:
        """
        Get a specific version by number or SHA.

        Args:
            session: Database session
            shadow_repo: The shadow repo
            version_number: Version number to retrieve
            commit_sha: Commit SHA to retrieve (partial match supported)

        Returns:
            ShadowVersion if found, None otherwise
        """
        stmt = select(ShadowVersion).where(
            ShadowVersion.shadow_repo_id == shadow_repo.id
        )

        if version_number is not None:
            stmt = stmt.where(ShadowVersion.version_number == version_number)
        elif commit_sha is not None:
            # Support partial SHA matching
            stmt = stmt.where(ShadowVersion.commit_sha.startswith(commit_sha))
        else:
            # Get latest
            stmt = stmt.order_by(ShadowVersion.version_number.desc())

        return session.exec(stmt).first()

    # =========================================================================
    # High-Level Convenience Methods (Outbox Pattern)
    # =========================================================================

    def enqueue_entity_version(
        self,
        session: Session,
        user: User,
        entity_type: str,
        entity_id: uuid.UUID,
        entity_data: dict[str, Any],
        message: str,
    ) -> ShadowVersion | None:
        """
        Enqueue a shadow write intent (DB-only) for background processing.

        This is the main entry point for automatic entity versioning.
        The worker will commit to the local git repo asynchronously.

        Creates:
        - DB ShadowRepo record (no git IO)
        - ShadowVersion row with `status="pending"` and `commit_sha="pending"`
        - ShadowOutboxJob row (durable worker queue)

        Args:
            session: Database session
            user: User saving the entity
            entity_type: Type ('agent', 'story', 'room', etc.)
            entity_id: Entity UUID
            entity_data: Full entity state
            message: Commit message

        Returns:
            ShadowVersion if created, None if shadowing not enabled
        """
        if not self.is_enabled():
            logger.debug("Shadow versioning not enabled")
            return None

        shadow_repo = self.ensure_shadow_repo_db_only(
            session, user, entity_type, entity_id
        )
        if not shadow_repo:
            return None

        self._ensure_shadow_repo_remote_best_effort(
            session=session,
            shadow_repo=shadow_repo,
        )

        version_number = self._allocate_next_version_number(session, shadow_repo.id)
        shadow_version = ShadowVersion(
            shadow_repo_id=shadow_repo.id,
            commit_sha="pending",
            version_number=version_number,
            message=message,
            snapshot_json=entity_data,
            created_by_id=user.id,
            created_at=datetime.now(),
            status="pending",
            committed_at=None,
            last_error=None,
            updated_at=datetime.utcnow(),
        )
        session.add(shadow_version)
        session.flush()

        job = ShadowOutboxJob(
            shadow_repo_id=shadow_repo.id,
            shadow_version_id=shadow_version.id,
            entity_type=entity_type,
            entity_id=entity_id,
            status="queued",
            attempt_count=0,
            run_after=datetime.utcnow(),
            locked_at=None,
            locked_by=None,
            last_error=None,
            last_error_at=None,
            priority=100,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(job)

        session.commit()
        session.refresh(shadow_version)

        logger.info(
            f"Enqueued shadow version for {entity_type}/{entity_id} "
            f"v{shadow_version.version_number}"
        )
        return shadow_version

    def enqueue_entity_version_with_owner(
        self,
        session: Session,
        owner: User,
        actor: User,
        entity_type: str,
        entity_id: uuid.UUID,
        entity_data: dict[str, Any],
        message: str,
    ) -> ShadowVersion | None:
        """
        Like enqueue_entity_version, but allows a distinct owner vs actor.

        Use this for room-scoped updates where the room creator is the
        entity owner, but another participant initiated the change.

        Args:
            session: Database session
            owner: User who owns the entity
            actor: User who made this change
            entity_type: Type of entity
            entity_id: Entity UUID
            entity_data: Full entity state
            message: Commit message

        Returns:
            ShadowVersion if created, None if not enabled
        """
        if not self.is_enabled():
            logger.debug("Shadow versioning not enabled")
            return None

        shadow_repo = self.ensure_shadow_repo_db_only(
            session, owner, entity_type, entity_id
        )
        if not shadow_repo:
            return None

        self._ensure_shadow_repo_remote_best_effort(
            session=session,
            shadow_repo=shadow_repo,
        )

        version_number = self._allocate_next_version_number(session, shadow_repo.id)
        shadow_version = ShadowVersion(
            shadow_repo_id=shadow_repo.id,
            commit_sha="pending",
            version_number=version_number,
            message=message,
            snapshot_json=entity_data,
            created_by_id=actor.id,
            created_at=datetime.now(),
            status="pending",
            committed_at=None,
            last_error=None,
            updated_at=datetime.utcnow(),
        )
        session.add(shadow_version)
        session.flush()

        job = ShadowOutboxJob(
            shadow_repo_id=shadow_repo.id,
            shadow_version_id=shadow_version.id,
            entity_type=entity_type,
            entity_id=entity_id,
            status="queued",
            attempt_count=0,
            run_after=datetime.utcnow(),
            locked_at=None,
            locked_by=None,
            last_error=None,
            last_error_at=None,
            priority=100,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(job)

        session.commit()
        session.refresh(shadow_version)
        return shadow_version

    def get_entity_history(
        self,
        session: Session,
        entity_type: str,
        entity_id: uuid.UUID,
        limit: int = 50,
    ) -> list[ShadowVersion]:
        """
        Get version history for an entity.

        Args:
            session: Database session
            entity_type: Type of entity
            entity_id: Entity UUID
            limit: Max versions to return

        Returns:
            List of versions, newest first. Empty if not shadowed.
        """
        shadow_repo = self.get_shadow_repo(session, entity_type, entity_id)
        if not shadow_repo:
            return []

        return self.get_version_history(session, shadow_repo, limit)

    def _ensure_shadow_repo_remote_best_effort(
        self,
        *,
        session: Session,
        shadow_repo: ShadowRepo,
    ) -> None:
        """Attempt remote provisioning without blocking local shadow enqueue."""
        try:
            shadow_gogs_service.ensure_shadow_repo_remote(
                session=session,
                shadow_repo=shadow_repo,
            )
        except Exception:
            logger.warning(
                "Shadow remote provisioning failed for %s/%s; continuing with local-only enqueue",
                shadow_repo.entity_type,
                shadow_repo.entity_id,
                exc_info=True,
            )


# Singleton instance
shadow_service = ShadowService()
