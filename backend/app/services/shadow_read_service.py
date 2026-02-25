"""
Shadow Read Service

Read-path for Shadow snapshots with git-first, DB fallback strategy.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from sqlmodel import Session, select

from app.core.config import settings
from app.models import ShadowRepo, ShadowVersion
from app.services.shadow_git import (
    SnapshotNotFoundError,
    get_repo_path,
    read_snapshot,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ShadowSnapshotResult:
    """Result of a shadow snapshot read operation."""

    entity_type: str
    entity_id: uuid.UUID
    version_number: int | None
    commit_sha: str | None
    source: Literal["git", "db"]
    is_stale: bool
    snapshot_json: dict[str, Any]


class ShadowReadError(RuntimeError):
    """Base error for shadow read operations."""

    pass


class ShadowRepoNotFound(ShadowReadError):
    """Raised when a shadow repo doesn't exist."""

    pass


class ShadowVersionNotFound(ShadowReadError):
    """Raised when a shadow version doesn't exist."""

    pass


class ShadowReadService:
    """
    Read-path for Shadow snapshots.

    Git-first with DB fallback:
    - Preferred: read `{entity_type}.json` from local git at the pinned commit SHA
    - Fallback: return `ShadowVersion.snapshot_json` from DB with is_stale=True
    """

    def get_latest_snapshot(
        self,
        *,
        session: Session,
        entity_type: str,
        entity_id: uuid.UUID,
    ) -> ShadowSnapshotResult:
        """Get the latest snapshot for an entity."""
        shadow_repo = self._get_shadow_repo(
            session=session, entity_type=entity_type, entity_id=entity_id
        )
        shadow_version = self._get_latest_committed_version(
            session=session, shadow_repo_id=shadow_repo.id
        )
        if shadow_version is None:
            shadow_version = self._get_latest_pending_version(
                session=session, shadow_repo_id=shadow_repo.id
            )
            if shadow_version is None:
                raise ShadowVersionNotFound(
                    f"No ShadowVersion found for shadow_repo_id={shadow_repo.id}"
                )
        return self._get_snapshot_from_version(
            shadow_repo=shadow_repo,
            shadow_version=shadow_version,
        )

    def get_snapshot_by_version(
        self,
        *,
        session: Session,
        entity_type: str,
        entity_id: uuid.UUID,
        version_number: int,
    ) -> ShadowSnapshotResult:
        """Get a specific version snapshot by version number."""
        shadow_repo = self._get_shadow_repo(
            session=session, entity_type=entity_type, entity_id=entity_id
        )
        shadow_version = self._get_version_by_number(
            session=session,
            shadow_repo_id=shadow_repo.id,
            version_number=version_number,
        )
        return self._get_snapshot_from_version(
            shadow_repo=shadow_repo,
            shadow_version=shadow_version,
        )

    def get_snapshot_by_commit(
        self,
        *,
        session: Session,
        entity_type: str,
        entity_id: uuid.UUID,
        commit_sha: str,
    ) -> ShadowSnapshotResult:
        """Get a specific version snapshot by commit SHA."""
        shadow_repo = self._get_shadow_repo(
            session=session, entity_type=entity_type, entity_id=entity_id
        )
        shadow_version = self._get_version_by_commit(
            session=session, shadow_repo_id=shadow_repo.id, commit_sha=commit_sha
        )
        return self._get_snapshot_from_version(
            shadow_repo=shadow_repo,
            shadow_version=shadow_version,
        )

    def _get_shadow_repo(
        self,
        *,
        session: Session,
        entity_type: str,
        entity_id: uuid.UUID,
    ) -> ShadowRepo:
        """Get shadow repo or raise ShadowRepoNotFound."""
        stmt = select(ShadowRepo).where(
            ShadowRepo.entity_type == entity_type,
            ShadowRepo.entity_id == entity_id,
        )
        shadow_repo = session.exec(stmt).first()
        if not shadow_repo:
            raise ShadowRepoNotFound(
                f"Shadow repo not found for {entity_type}/{entity_id}"
            )
        return shadow_repo

    def _get_latest_version(
        self, *, session: Session, shadow_repo_id: uuid.UUID
    ) -> ShadowVersion:
        """Get the latest version regardless of status."""
        stmt = (
            select(ShadowVersion)
            .where(ShadowVersion.shadow_repo_id == shadow_repo_id)
            .order_by(ShadowVersion.version_number.desc())
        )
        version = session.exec(stmt).first()
        if not version:
            raise ShadowVersionNotFound(
                f"No ShadowVersion found for shadow_repo_id={shadow_repo_id}"
            )
        return version

    def _get_latest_committed_version(
        self, *, session: Session, shadow_repo_id: uuid.UUID
    ) -> ShadowVersion | None:
        """Get the latest committed version, or None if none committed."""
        stmt = (
            select(ShadowVersion)
            .where(
                ShadowVersion.shadow_repo_id == shadow_repo_id,
                ShadowVersion.status == "committed",
            )
            .order_by(ShadowVersion.version_number.desc())
        )
        return session.exec(stmt).first()

    def _get_latest_pending_version(
        self, *, session: Session, shadow_repo_id: uuid.UUID
    ) -> ShadowVersion | None:
        """Get the latest pending/error version, or None if none pending."""
        stmt = (
            select(ShadowVersion)
            .where(
                ShadowVersion.shadow_repo_id == shadow_repo_id,
                ShadowVersion.status.in_(["pending", "error"]),
            )
            .order_by(ShadowVersion.version_number.desc())
        )
        return session.exec(stmt).first()

    def _get_version_by_number(
        self,
        *,
        session: Session,
        shadow_repo_id: uuid.UUID,
        version_number: int,
    ) -> ShadowVersion:
        """Get a specific version by number or raise ShadowVersionNotFound."""
        stmt = select(ShadowVersion).where(
            ShadowVersion.shadow_repo_id == shadow_repo_id,
            ShadowVersion.version_number == version_number,
        )
        version = session.exec(stmt).first()
        if not version:
            raise ShadowVersionNotFound(
                f"ShadowVersion not found for shadow_repo_id={shadow_repo_id} "
                f"version_number={version_number}"
            )
        return version

    def _get_version_by_commit(
        self,
        *,
        session: Session,
        shadow_repo_id: uuid.UUID,
        commit_sha: str,
    ) -> ShadowVersion:
        """Get a specific version by commit SHA or raise ShadowVersionNotFound."""
        stmt = select(ShadowVersion).where(
            ShadowVersion.shadow_repo_id == shadow_repo_id,
            ShadowVersion.commit_sha.startswith(commit_sha),
        )
        version = session.exec(stmt).first()
        if not version:
            raise ShadowVersionNotFound(
                f"ShadowVersion not found for shadow_repo_id={shadow_repo_id} "
                f"commit_sha={commit_sha}"
            )
        return version

    def _get_snapshot_from_version(
        self,
        *,
        shadow_repo: ShadowRepo,
        shadow_version: ShadowVersion,
    ) -> ShadowSnapshotResult:
        """
        Read snapshot from git, falling back to DB if git read fails.

        For pending/error versions, always returns DB snapshot with is_stale=True
        since they haven't been committed to git yet.
        """
        entity_type = shadow_repo.entity_type
        entity_id = shadow_repo.entity_id

        # Pending versions aren't in git yet - return DB snapshot
        if shadow_version.status != "committed":
            return ShadowSnapshotResult(
                entity_type=entity_type,
                entity_id=entity_id,
                version_number=shadow_version.version_number,
                commit_sha=shadow_version.commit_sha,
                source="db",
                is_stale=True,
                snapshot_json=shadow_version.snapshot_json,
            )

        # Try to read from local git
        repo_path = get_repo_path(
            Path(settings.SHADOW_REPOS_PATH),
            entity_type,
            str(entity_id),
        )

        try:
            snapshot_json = read_snapshot(
                repo_path=repo_path,
                entity_type=entity_type,
                commit_sha=shadow_version.commit_sha,
            )
            return ShadowSnapshotResult(
                entity_type=entity_type,
                entity_id=entity_id,
                version_number=shadow_version.version_number,
                commit_sha=shadow_version.commit_sha,
                source="git",
                is_stale=False,
                snapshot_json=snapshot_json,
            )
        except SnapshotNotFoundError as exc:
            logger.warning(
                f"Shadow git read failed for {entity_type}/{entity_id} "
                f"@ {shadow_version.commit_sha}; falling back to DB: {exc}"
            )
            return ShadowSnapshotResult(
                entity_type=entity_type,
                entity_id=entity_id,
                version_number=shadow_version.version_number,
                commit_sha=shadow_version.commit_sha,
                source="db",
                is_stale=True,
                snapshot_json=shadow_version.snapshot_json,
            )


shadow_read_service = ShadowReadService()
