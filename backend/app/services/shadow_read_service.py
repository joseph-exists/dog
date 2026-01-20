from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from typing import Any, Literal

import openapi_client
from openapi_client import ApiException, RepositoryApi
from sqlmodel import Session, select

from app.core.config import settings
from app.models import ShadowRepo, ShadowVersion
from app.services.shadow_service import shadow_service

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ShadowSnapshotResult:
    entity_type: str
    entity_id: uuid.UUID
    version_number: int | None
    commit_sha: str | None
    source: Literal["forgejo", "db"]
    is_stale: bool
    snapshot_json: dict[str, Any]


class ShadowReadError(RuntimeError):
    pass


class ShadowRepoNotFound(ShadowReadError):
    pass


class ShadowVersionNotFound(ShadowReadError):
    pass


class ShadowReadService:
    """
    Read-path for Shadow snapshots.

    Forgejo-first with DB fallback:
    - Preferred: read `{entity_type}.json` from Forgejo at the pinned commit SHA
    - Fallback: return `ShadowVersion.snapshot_json` from DB with is_stale=True
    """

    def __init__(self, request_timeout_seconds: float = 5.0) -> None:
        self._request_timeout_seconds = request_timeout_seconds

    @property
    def request_timeout_seconds(self) -> float:
        return self._request_timeout_seconds

    def get_latest_snapshot(
        self,
        *,
        session: Session,
        entity_type: str,
        entity_id: uuid.UUID,
    ) -> ShadowSnapshotResult:
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
            session=session,
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
        shadow_repo = self._get_shadow_repo(
            session=session, entity_type=entity_type, entity_id=entity_id
        )
        shadow_version = self._get_version_by_number(
            session=session, shadow_repo_id=shadow_repo.id, version_number=version_number
        )
        return self._get_snapshot_from_version(
            session=session,
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
        shadow_repo = self._get_shadow_repo(
            session=session, entity_type=entity_type, entity_id=entity_id
        )
        shadow_version = self._get_version_by_commit(
            session=session, shadow_repo_id=shadow_repo.id, commit_sha=commit_sha
        )
        return self._get_snapshot_from_version(
            session=session,
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
        stmt = select(ShadowRepo).where(
            ShadowRepo.entity_type == entity_type,
            ShadowRepo.entity_id == entity_id,
        )
        shadow_repo = session.exec(stmt).first()
        if not shadow_repo:
            raise ShadowRepoNotFound(f"Shadow repo not found for {entity_type}/{entity_id}")
        return shadow_repo

    def _get_latest_version(self, *, session: Session, shadow_repo_id: uuid.UUID) -> ShadowVersion:
        stmt = (
            select(ShadowVersion)
            .where(ShadowVersion.shadow_repo_id == shadow_repo_id)
            .order_by(ShadowVersion.version_number.desc())
        )
        version = session.exec(stmt).first()
        if not version:
            raise ShadowVersionNotFound(f"No ShadowVersion found for shadow_repo_id={shadow_repo_id}")
        return version

    def _get_latest_committed_version(
        self, *, session: Session, shadow_repo_id: uuid.UUID
    ) -> ShadowVersion | None:
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
        stmt = select(ShadowVersion).where(
            ShadowVersion.shadow_repo_id == shadow_repo_id,
            ShadowVersion.version_number == version_number,
        )
        version = session.exec(stmt).first()
        if not version:
            raise ShadowVersionNotFound(
                f"ShadowVersion not found for shadow_repo_id={shadow_repo_id} version_number={version_number}"
            )
        return version

    def _get_version_by_commit(
        self,
        *,
        session: Session,
        shadow_repo_id: uuid.UUID,
        commit_sha: str,
    ) -> ShadowVersion:
        stmt = select(ShadowVersion).where(
            ShadowVersion.shadow_repo_id == shadow_repo_id,
            ShadowVersion.commit_sha.startswith(commit_sha),
        )
        version = session.exec(stmt).first()
        if not version:
            raise ShadowVersionNotFound(
                f"ShadowVersion not found for shadow_repo_id={shadow_repo_id} commit_sha={commit_sha}"
            )
        return version

    def _get_snapshot_from_version(
        self,
        *,
        session: Session,
        shadow_repo: ShadowRepo,
        shadow_version: ShadowVersion,
    ) -> ShadowSnapshotResult:
        entity_type = shadow_repo.entity_type
        entity_id = shadow_repo.entity_id

        token = shadow_service._get_service_token(entity_type)  # noqa: SLF001
        if not token:
            return ShadowSnapshotResult(
                entity_type=entity_type,
                entity_id=entity_id,
                version_number=shadow_version.version_number,
                commit_sha=shadow_version.commit_sha,
                source="db",
                is_stale=True,
                snapshot_json=shadow_version.snapshot_json,
            )

        try:
            snapshot_json = self._read_json_file_from_forgejo(
                token=token,
                entity_type=entity_type,
                repo_name=shadow_repo.forgejo_repo_name,
                commit_sha=shadow_version.commit_sha,
            )
            return ShadowSnapshotResult(
                entity_type=entity_type,
                entity_id=entity_id,
                version_number=shadow_version.version_number,
                commit_sha=shadow_version.commit_sha,
                source="forgejo",
                is_stale=False,
                snapshot_json=snapshot_json,
            )
        except Exception as exc:
            logger.warning(
                f"Shadow Forgejo read failed for {entity_type}/{entity_id} @ {shadow_version.commit_sha}; "
                f"falling back to DB snapshot: {exc}"
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

    def _read_json_file_from_forgejo(
        self,
        *,
        token: str,
        entity_type: str,
        repo_name: str,
        commit_sha: str,
    ) -> dict[str, Any]:
        config = openapi_client.Configuration(host=settings.SHADOW_FORGEJO_URL)
        config.api_key["AuthorizationHeaderToken"] = token
        config.api_key_prefix["AuthorizationHeaderToken"] = "token"
        api_client = openapi_client.ApiClient(config)
        repo_api = RepositoryApi(api_client)

        owner = shadow_service._get_service_username(entity_type)  # noqa: SLF001
        filepath = f"{entity_type}.json"

        try:
            raw = repo_api.repo_get_raw_file(
                owner=owner,
                repo=repo_name,
                filepath=filepath,
                ref=commit_sha,
                _request_timeout=self._request_timeout_seconds,
            )
        except ApiException as exc:
            raise ShadowReadError(f"Forgejo read failed: {exc}") from exc

        try:
            text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else str(raw)
            return json.loads(text)
        except Exception as exc:
            raise ShadowReadError("Failed to decode JSON snapshot from Forgejo") from exc


shadow_read_service = ShadowReadService()
