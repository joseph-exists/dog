from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, TypeVar

from sqlmodel import Session, select

from app.core.redis import get_redis
from app.models import ShadowRepo
from app.services.shadow_read_service import (
    ShadowSnapshotResult,
    shadow_read_service,
)
from app.services.shadow_summaries import SUMMARY_DISPATCH

logger = logging.getLogger(__name__)

"""Shadow Summary Service with Caching.
Note: uses run_sync when handed an async session to safely access sync helpers.
"""

@dataclass(frozen=True)
class ShadowSummaryResult:
    entity_type: str
    entity_id: uuid.UUID
    version_number: int | None
    commit_sha: str | None
    source: str
    is_stale: bool
    summary: dict[str, Any]


class ShadowSummaryService:
    """
    Summary read service with Redis caching.

    Caches summaries by (shadow_repo_id, commit_sha) for prompt usage.
    """

    def __init__(self) -> None:
        self._latest_ttl_seconds = 120
        self._pinned_ttl_seconds = 3600

    async def get_latest_summary(
        self,
        *,
        session: Session,
        entity_type: str,
        entity_id: uuid.UUID,
    ) -> ShadowSummaryResult:
        snapshot = await self._run_sync(
            session,
            shadow_read_service.get_latest_snapshot,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        return await self._summarize_with_cache(
            session=session,
            snapshot=snapshot,
            ttl_seconds=self._latest_ttl_seconds,
        )

    async def get_summary_by_version(
        self,
        *,
        session: Session,
        entity_type: str,
        entity_id: uuid.UUID,
        version_number: int,
    ) -> ShadowSummaryResult:
        snapshot = await self._run_sync(
            session,
            shadow_read_service.get_snapshot_by_version,
            entity_type=entity_type,
            entity_id=entity_id,
            version_number=version_number,
        )
        return await self._summarize_with_cache(
            session=session,
            snapshot=snapshot,
            ttl_seconds=self._pinned_ttl_seconds,
        )

    async def get_summary_by_commit(
        self,
        *,
        session: Session,
        entity_type: str,
        entity_id: uuid.UUID,
        commit_sha: str,
    ) -> ShadowSummaryResult:
        snapshot = await self._run_sync(
            session,
            shadow_read_service.get_snapshot_by_commit,
            entity_type=entity_type,
            entity_id=entity_id,
            commit_sha=commit_sha,
        )
        return await self._summarize_with_cache(
            session=session,
            snapshot=snapshot,
            ttl_seconds=self._pinned_ttl_seconds,
        )

    async def _summarize_with_cache(
        self,
        *,
        session: Session,
        snapshot: ShadowSnapshotResult,
        ttl_seconds: int,
    ) -> ShadowSummaryResult:
        shadow_repo_id = await self._run_sync(
            session,
            self._get_shadow_repo_id,
            entity_type=snapshot.entity_type,
            entity_id=snapshot.entity_id,
        )
        cache_key = self._cache_key(shadow_repo_id, snapshot.commit_sha)
        if cache_key:
            cached = await self._get_cached_summary(cache_key)
            if cached:
                return cached

        summary_func = SUMMARY_DISPATCH.get(snapshot.entity_type)
        if not summary_func:
            summary = {"raw": snapshot.snapshot_json}
        else:
            summary = summary_func(snapshot.snapshot_json)

        result = ShadowSummaryResult(
            entity_type=snapshot.entity_type,
            entity_id=snapshot.entity_id,
            version_number=snapshot.version_number,
            commit_sha=snapshot.commit_sha,
            source=snapshot.source,
            is_stale=snapshot.is_stale,
            summary=summary,
        )

        if cache_key:
            await self._set_cached_summary(cache_key, result, ttl_seconds)
        return result

    _T = TypeVar("_T")

    async def _run_sync(
        self,
        session: Session,
        func: Callable[..., _T],
        **kwargs: Any,
    ) -> _T:
        run_sync = getattr(session, "run_sync", None)
        if callable(run_sync):
            return await run_sync(lambda sync_session: func(session=sync_session, **kwargs))
        return func(session=session, **kwargs)

    def _get_shadow_repo_id(
        self,
        *,
        session: Session,
        entity_type: str,
        entity_id: uuid.UUID,
    ) -> uuid.UUID | None:
        stmt = select(ShadowRepo).where(
            ShadowRepo.entity_type == entity_type,
            ShadowRepo.entity_id == entity_id,
        )
        shadow_repo = session.exec(stmt).first()
        return shadow_repo.id if shadow_repo else None

    def _cache_key(
        self, shadow_repo_id: uuid.UUID | None, commit_sha: str | None
    ) -> str | None:
        if not shadow_repo_id or not commit_sha:
            return None
        return f"shadow:summary:{shadow_repo_id}:{commit_sha}"

    async def _get_cached_summary(self, cache_key: str) -> ShadowSummaryResult | None:
        try:
            redis = await get_redis()
            raw = await redis.get(cache_key)
            if not raw:
                return None
            data = json.loads(raw)
            return ShadowSummaryResult(
                entity_type=data["entity_type"],
                entity_id=uuid.UUID(data["entity_id"]),
                version_number=data.get("version_number"),
                commit_sha=data.get("commit_sha"),
                source=data.get("source", "forgejo"),
                is_stale=bool(data.get("is_stale")),
                summary=data.get("summary", {}),
            )
        except Exception as exc:
            logger.warning(f"Shadow summary cache read failed: {exc}")
            return None

    async def _set_cached_summary(
        self,
        cache_key: str,
        result: ShadowSummaryResult,
        ttl_seconds: int,
    ) -> None:
        try:
            redis = await get_redis()
            payload = {
                "entity_type": result.entity_type,
                "entity_id": str(result.entity_id),
                "version_number": result.version_number,
                "commit_sha": result.commit_sha,
                "source": result.source,
                "is_stale": result.is_stale,
                "summary": result.summary,
                "cached_at": datetime.now(tz=timezone.utc).isoformat(),
            }
            await redis.setex(cache_key, ttl_seconds, json.dumps(payload))
        except Exception as exc:
            logger.warning(f"Shadow summary cache write failed: {exc}")


shadow_summary_service = ShadowSummaryService()
