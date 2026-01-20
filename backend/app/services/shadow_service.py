"""
Shadow Forgejo Service

Provides automatic, invisible git-based versioning for application entities
by mirroring them to Forgejo repositories. Each entity (agent, story, user)
gets its own repo with full JSON snapshots committed on every save.

Architecture:
- Service accounts own repos by entity type (shadow-users, shadow-agents, shadow-stories)
- Users never see or interact with Forgejo directly
- All operations happen automatically on entity save

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

import base64
import json
import logging
import uuid
from datetime import datetime
from typing import Any

import openapi_client
from sqlalchemy.exc import IntegrityError
from openapi_client import (
    ApiException,
    CreateFileOptions,
    CreateRepoOption,
    RepositoryApi,
    UpdateFileOptions,
)
from sqlmodel import Session, select

from app.core.config import settings
from app.models import (
    ShadowRepo,
    ShadowUser,
    ShadowVersion,
    User,
    ShadowOutboxJob,
    ShadowRepoVersionCounter,
)

logger = logging.getLogger(__name__)


# Entity type to service account mapping
SERVICE_ACCOUNT_MAP = {
    "user": "SHADOW_USERS_TOKEN",
    "agent": "SHADOW_AGENTS_TOKEN",
    "story": "SHADOW_STORIES_TOKEN",
    "room": "SHADOW_ROOMS_TOKEN",
    "persona": "SHADOW_PERSONAS_TOKEN",
    "quality": "SHADOW_QUALITIES_TOKEN",
    "trait": "SHADOW_TRAITS_TOKEN",
    "llm_model": "SHADOW_LLM_MODELS_TOKEN",
    "user_llm_provider": "SHADOW_USER_LLM_PROVIDERS_TOKEN",
}

# Service account usernames (must match Forgejo accounts)
SERVICE_ACCOUNT_USERNAMES = {
    "user": "shadow-users",
    "agent": "shadow-agents",
    "story": "shadow-stories",
    "room": "shadow-rooms",
    "persona": "shadow-personas",
    "quality": "shadow-qualities",
    "trait": "shadow-traits",
    "llm_model": "shadow-llm-models",
    "user_llm_provider": "shadow-user-llm-providers",
}


class ShadowService:
    """
    Service for automatic, invisible git-based entity versioning via Forgejo.

    Design decisions (from Shadow-Forgejo-Decisions):
    - Repo-per-entity: Each agent/story/user gets its own repository
    - Full JSON versioning: Complete snapshots, not diffs
    - Every save sync: Version created on each save operation
    - Pretty-printed JSON: For readable git diffs
    - Invisible to users: Service accounts own all repos
    """

    def _get_service_token(self, entity_type: str) -> str | None:
        """
        Get the service account token for an entity type.

        Args:
            entity_type: Type of entity ('agent', 'story', 'user')

        Returns:
            Service account token or None if not configured
        """
        token_attr = SERVICE_ACCOUNT_MAP.get(entity_type)
        if not token_attr:
            logger.warning(f"Unknown entity type for shadow: {entity_type}")
            return None

        token = getattr(settings, token_attr, None)
        if not token:
            logger.debug(f"No service token configured for {entity_type} (set {token_attr})")
            return None

        return token

    def _get_service_username(self, entity_type: str) -> str:
        """Get the service account username for an entity type."""
        return SERVICE_ACCOUNT_USERNAMES.get(entity_type, f"shadow-{entity_type}")

    def _get_api_client(self, token: str) -> openapi_client.ApiClient:
        """Create an API client with the given service account token."""
        config = openapi_client.Configuration(host=settings.SHADOW_FORGEJO_URL)
        config.api_key["AuthorizationHeaderToken"] = token
        config.api_key_prefix["AuthorizationHeaderToken"] = "token"
        return openapi_client.ApiClient(config)

    def is_enabled(self, entity_type: str | None = None) -> bool:
        """
        Check if shadow versioning is enabled.

        Args:
            entity_type: Optional entity type to check specific service account

        Returns:
            True if shadow is enabled and configured
        """
        if not settings.SHADOW_ENABLED:
            return False

        if entity_type:
            return self._get_service_token(entity_type) is not None

        # Check if any service account is configured
        return any(
            getattr(settings, attr, None)
            for attr in SERVICE_ACCOUNT_MAP.values()
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
        if not self.is_enabled("user"):
            logger.debug("Shadow users not enabled")
            return None

        # Check if shadow user already exists
        stmt = select(ShadowUser).where(ShadowUser.user_id == user.id)
        existing = session.exec(stmt).first()

        if existing:
            logger.debug(f"Found existing shadow user for {user.email}")
            return existing

        # Create the shadow user record (repo created lazily on first version)
        repo_name = f"user-{str(user.id)[:8]}"

        shadow_user = ShadowUser(
            user_id=user.id,
            forgejo_repo_name=repo_name,
            forgejo_repo_id=None,  # Set when repo is created
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
        Create or fetch the DB ShadowRepo record only (no Forgejo IO).

        Milestone 3 invariant: only the worker creates/ensures Forgejo repos.
        """
        if not self.is_enabled(entity_type):
            logger.debug(f"Shadow not enabled for {entity_type}")
            return None

        stmt = select(ShadowRepo).where(
            ShadowRepo.entity_type == entity_type,
            ShadowRepo.entity_id == entity_id,
        )
        existing = session.exec(stmt).first()
        if existing:
            return existing

        repo_name = f"{entity_type}-{str(entity_id)[:8]}"
        shadow_repo = ShadowRepo(
            owner_id=owner.id,
            entity_type=entity_type,
            entity_id=entity_id,
            forgejo_repo_name=repo_name,
            forgejo_repo_id=None,
            created_at=datetime.now(),
        )
        session.add(shadow_repo)
        session.commit()
        session.refresh(shadow_repo)
        return shadow_repo

    def ensure_shadow_repo(
        self,
        session: Session,
        owner: User,
        entity_type: str,
        entity_id: uuid.UUID,
    ) -> ShadowRepo | None:
        """
        Get or create a ShadowRepo for an entity.

        Repos are owned by service accounts, not users.

        Args:
            session: Database session
            owner: Application user who owns this entity
            entity_type: Type of entity ('agent', 'story', etc.)
            entity_id: UUID of the entity

        Returns:
            ShadowRepo mapping record, or None if not enabled
        """
        if not self.is_enabled(entity_type):
            logger.debug(f"Shadow not enabled for {entity_type}")
            return None

        # Check if repo already exists
        stmt = select(ShadowRepo).where(
            ShadowRepo.entity_type == entity_type,
            ShadowRepo.entity_id == entity_id,
        )
        existing = session.exec(stmt).first()

        if existing:
            logger.debug(f"Found existing shadow repo for {entity_type}/{entity_id}")
            return existing

        # Create Forgejo repository via service account
        token = self._get_service_token(entity_type)
        if not token:
            return None

        service_username = self._get_service_username(entity_type)
        repo_name = f"{entity_type}-{str(entity_id)[:8]}"
        client = self._get_api_client(token)
        repo_api = RepositoryApi(client)

        forgejo_repo_id = None
        try:
            repo_options = CreateRepoOption(
                name=repo_name,
                description=f"Shadow repository for {entity_type} {entity_id}",
                private=True,
                auto_init=True,  # Creates initial commit with README
            )
            forgejo_repo = repo_api.create_current_user_repo(body=repo_options)
            repo_dict = forgejo_repo.to_dict()
            forgejo_repo_id = repo_dict.get('id')
            logger.info(f"Created Forgejo repo: {service_username}/{repo_name}")

        except ApiException as e:
            if e.status == 409:
                # Repo already exists in Forgejo, fetch it
                logger.warning(f"Repo {repo_name} already exists, fetching...")
                try:
                    forgejo_repo = repo_api.repo_get(
                        owner=service_username,
                        repo=repo_name
                    )
                    forgejo_repo_id = forgejo_repo.to_dict().get('id')
                except ApiException:
                    logger.error(f"Failed to fetch existing repo {repo_name}")
                    pass
            else:
                logger.error(f"Failed to create Forgejo repo: {e.status} - {e.reason}")
                # Continue anyway - we'll try again next time
                pass

        # Create shadow repo record
        shadow_repo = ShadowRepo(
            owner_id=owner.id,
            entity_type=entity_type,
            entity_id=entity_id,
            forgejo_repo_name=repo_name,
            forgejo_repo_id=forgejo_repo_id,
            created_at=datetime.now(),
        )

        session.add(shadow_repo)
        session.commit()
        session.refresh(shadow_repo)

        logger.info(f"Created shadow repo record: {entity_type}/{entity_id}")
        return shadow_repo

    def _allocate_next_version_number(self, session: Session, shadow_repo_id: uuid.UUID) -> int:
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

    def create_version(
        self,
        session: Session,
        shadow_repo: ShadowRepo,
        entity_data: dict[str, Any],
        message: str,
        user: User,
    ) -> ShadowVersion | None:
        """
        Create a new version (commit) for an entity.

        Args:
            session: Database session
            shadow_repo: The shadow repo to commit to
            entity_data: Full entity state as dictionary
            message: Commit message
            user: User creating this version

        Returns:
            ShadowVersion record with commit SHA, or None on failure
        """
        token = self._get_service_token(shadow_repo.entity_type)
        if not token:
            logger.debug(f"No token for {shadow_repo.entity_type}, skipping version")
            return None

        service_username = self._get_service_username(shadow_repo.entity_type)

        # Calculate next version number
        stmt = select(ShadowVersion).where(
            ShadowVersion.shadow_repo_id == shadow_repo.id
        ).order_by(ShadowVersion.version_number.desc())
        latest = session.exec(stmt).first()
        next_version = (latest.version_number + 1) if latest else 1

        # Pretty-print JSON for readable diffs
        json_content = json.dumps(entity_data, indent=2, sort_keys=True, default=str)
        content_b64 = base64.b64encode(json_content.encode()).decode()

        # Commit to Forgejo
        client = self._get_api_client(token)
        repo_api = RepositoryApi(client)

        file_path = f"{shadow_repo.entity_type}.json"
        commit_sha = "pending"

        try:
            # Try to get existing file to get its SHA
            try:
                existing_file = repo_api.repo_get_contents(
                    owner=service_username,
                    repo=shadow_repo.forgejo_repo_name,
                    filepath=file_path,
                )
                existing_sha = existing_file.to_dict().get('sha')

                # Update existing file
                update_options = UpdateFileOptions(
                    content=content_b64,
                    message=message,
                    sha=existing_sha,
                )
                result = repo_api.repo_update_file(
                    owner=service_username,
                    repo=shadow_repo.forgejo_repo_name,
                    filepath=file_path,
                    body=update_options,
                )
            except ApiException as e:
                if e.status == 404:
                    # File doesn't exist, create it
                    create_options = CreateFileOptions(
                        content=content_b64,
                        message=message,
                    )
                    result = repo_api.repo_create_file(
                        owner=service_username,
                        repo=shadow_repo.forgejo_repo_name,
                        filepath=file_path,
                        body=create_options,
                    )
                else:
                    raise

            result_dict = result.to_dict()
            commit_sha = result_dict.get('commit', {}).get('sha', 'unknown')

        except ApiException as e:
            logger.error(f"Failed to commit to Forgejo: {e.status} - {e.reason}")
            # Still create version record with pending SHA for audit trail
            commit_sha = f"error-{e.status}"

        # Create version record
        shadow_version = ShadowVersion(
            shadow_repo_id=shadow_repo.id,
            commit_sha=commit_sha[:40],  # Ensure max length
            version_number=next_version,
            message=message,
            snapshot_json=entity_data,
            created_by_id=user.id,
            created_at=datetime.now(),
        )

        session.add(shadow_version)
        session.commit()
        session.refresh(shadow_version)

        logger.info(
            f"Created version {next_version} ({commit_sha[:8]}) "
            f"for {shadow_repo.forgejo_repo_name}"
        )
        return shadow_version

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
    # High-Level Convenience Methods
    # =========================================================================

    def create_entity_version(
        self,
        session: Session,
        user: User,
        entity_type: str,
        entity_id: uuid.UUID,
        entity_data: dict[str, Any],
        message: str,
    ) -> ShadowVersion | None:
        """
        High-level method to version an entity in one call.

        This is the main entry point for automatic entity versioning.
        Handles all the shadow repo setup automatically and invisibly.

        Args:
            session: Database session
            user: User saving the entity
            entity_type: Type ('agent', 'story', 'user')
            entity_id: Entity UUID
            entity_data: Full entity state
            message: Commit message

        Returns:
            ShadowVersion if created, None if shadowing not enabled
        """
        if not self.is_enabled(entity_type):
            logger.debug(f"Shadow not enabled for {entity_type}")
            return None

        # Get or create shadow repo
        shadow_repo = self.ensure_shadow_repo(
            session, user, entity_type, entity_id
        )
        if not shadow_repo:
            return None

        # Create version
        return self.create_version(
            session, shadow_repo, entity_data, message, user
        )

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
        Milestone 3: enqueue a Shadow write intent (DB-only) for background processing.

        Creates:
        - DB ShadowRepo record (no Forgejo IO)
        - ShadowVersion row with `status="pending"` and `commit_sha="pending"`
        - ShadowOutboxJob row (durable worker queue)
        """
        if not self.is_enabled(entity_type):
            logger.debug(f"Shadow not enabled for {entity_type}")
            return None

        shadow_repo = self.ensure_shadow_repo_db_only(session, user, entity_type, entity_id)
        if not shadow_repo:
            return None

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
            f"Enqueued shadow outbox job for {entity_type}/{entity_id} "
            f"v{shadow_version.version_number} repo={shadow_repo.forgejo_repo_name}"
        )
        return shadow_version

    def create_entity_version_with_owner(
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
        Version an entity where the entity owner and the actor differ.

        Use this for room-scoped updates (e.g., bindings) where the room creator
        is the entity owner, but another participant initiated the change.
        """
        if not self.is_enabled(entity_type):
            logger.debug(f"Shadow not enabled for {entity_type}")
            return None

        shadow_repo = self.ensure_shadow_repo(
            session, owner, entity_type, entity_id
        )
        if not shadow_repo:
            return None

        return self.create_version(
            session, shadow_repo, entity_data, message, actor
        )

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
        """
        if not self.is_enabled(entity_type):
            logger.debug(f"Shadow not enabled for {entity_type}")
            return None

        shadow_repo = self.ensure_shadow_repo_db_only(session, owner, entity_type, entity_id)
        if not shadow_repo:
            return None

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


# Singleton instance
shadow_service = ShadowService()
