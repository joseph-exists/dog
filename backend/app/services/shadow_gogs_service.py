from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx
from sqlmodel import Session

from app.core.config import settings
from app.models import ShadowRepo

logger = logging.getLogger(__name__)


class ShadowGogsProvisioningError(RuntimeError):
    """Raised when Gogs repo provisioning fails."""


@dataclass(frozen=True)
class ShadowRemoteRepo:
    """Minimal remote repo metadata returned by Gogs."""

    repo_id: int | None
    full_name: str
    ssh_url: str | None
    html_url: str | None


class ShadowGogsService:
    """Provision shadow repositories in Gogs when configured."""

    def is_configured(self) -> bool:
        return bool(settings.SHADOW_GOGS_BASE_URL and settings.SHADOW_GOGS_TOKEN)

    def ensure_shadow_repo_remote(
        self,
        *,
        session: Session,
        shadow_repo: ShadowRepo,
    ) -> ShadowRemoteRepo | None:
        """
        Ensure the remote Gogs repo exists for a shadow repo.

        Returns None when Gogs provisioning is not configured.
        """
        if not self.is_configured():
            logger.debug(
                "Shadow Gogs provisioning skipped for %s/%s; service not configured",
                shadow_repo.entity_type,
                shadow_repo.entity_id,
            )
            return None

        repo_name = shadow_repo.forgejo_repo_name
        existing = self._get_repo(repo_name)
        if existing is None:
            existing = self._create_repo(repo_name)

        if shadow_repo.forgejo_repo_id != existing.repo_id:
            shadow_repo.forgejo_repo_id = existing.repo_id
            session.add(shadow_repo)
            session.flush()

        return existing

    def _client(self) -> httpx.Client:
        return httpx.Client(
            base_url=str(settings.SHADOW_GOGS_BASE_URL).rstrip("/"),
            headers={
                "Authorization": f"token {settings.SHADOW_GOGS_TOKEN}",
                "Accept": "application/json",
            },
            timeout=settings.SHADOW_GOGS_TIMEOUT_SECONDS,
        )

    def _get_repo(self, repo_name: str) -> ShadowRemoteRepo | None:
        path = f"/api/v1/repos/{settings.SHADOW_GOGS_ORG}/{repo_name}"
        with self._client() as client:
            response = client.get(path)

        if response.status_code == 404:
            return None
        if response.is_error:
            self._raise_api_error(
                method="GET",
                path=path,
                repo_name=repo_name,
                response=response,
            )
        return self._parse_repo(response)

    def _create_repo(self, repo_name: str) -> ShadowRemoteRepo:
        path = f"/api/v1/org/{settings.SHADOW_GOGS_ORG}/repos"
        payload = {
            "name": repo_name,
            "private": True,
            "auto_init": False,
            "default_branch": settings.SHADOW_REPO_DEFAULT_BRANCH,
        }
        with self._client() as client:
            response = client.post(path, json=payload)

        if response.status_code in {201, 202}:
            return self._parse_repo(response)
        if response.status_code == 409:
            existing = self._get_repo(repo_name)
            if existing is not None:
                return existing
        self._raise_api_error(
            method="POST",
            path=path,
            repo_name=repo_name,
            response=response,
        )

    def _parse_repo(self, response: httpx.Response) -> ShadowRemoteRepo:
        payload = response.json()
        return ShadowRemoteRepo(
            repo_id=payload.get("id"),
            full_name=payload.get(
                "full_name",
                f"{settings.SHADOW_GOGS_ORG}/{payload.get('name', '')}",
            ),
            ssh_url=payload.get("ssh_url"),
            html_url=payload.get("html_url"),
        )

    def _raise_api_error(
        self,
        *,
        method: str,
        path: str,
        repo_name: str,
        response: httpx.Response,
    ) -> None:
        summary = self._summarize_error_body(response)

        if method == "POST" and response.status_code == 404:
            raise ShadowGogsProvisioningError(
                f"Gogs repo creation request failed for "
                f"{settings.SHADOW_GOGS_ORG}/{repo_name}: "
                f"{method} {path} returned 404. "
                f"Response summary: {summary}"
            )

        if method == "GET" and response.status_code == 404:
            raise ShadowGogsProvisioningError(
                f"Gogs repo lookup failed unexpectedly for "
                f"{settings.SHADOW_GOGS_ORG}/{repo_name}: "
                f"{method} {path} returned 404. "
                f"Response summary: {summary}"
            )

        raise ShadowGogsProvisioningError(
            f"Gogs API request failed for {settings.SHADOW_GOGS_ORG}/{repo_name}: "
            f"{method} {path} returned {response.status_code}. "
            f"Response summary: {summary}"
        )

    def _summarize_error_body(self, response: httpx.Response) -> str:
        content_type = response.headers.get("content-type", "").lower()
        body = response.text.strip()

        if "application/json" in content_type:
            try:
                payload = response.json()
            except ValueError:
                pass
            else:
                if isinstance(payload, dict):
                    message = payload.get("message") or payload.get("error")
                    if isinstance(message, str) and message.strip():
                        return message.strip()
                return str(payload)[:300]

        if "text/html" in content_type or "<html" in body.lower():
            title = self._extract_html_title(body)
            if title:
                return f"HTML page: {title}"
            return "HTML page response"

        if not body:
            return "empty response body"

        return body[:300]

    def _extract_html_title(self, body: str) -> str | None:
        lower_body = body.lower()
        start = lower_body.find("<title>")
        end = lower_body.find("</title>")
        if start == -1 or end == -1 or end <= start:
            return None
        title = body[start + len("<title>") : end].strip()
        return title or None


shadow_gogs_service = ShadowGogsService()
