from __future__ import annotations

from datetime import datetime
import logging
import uuid
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse

import httpx
from coolname import generate_slug as coolname_generate_slug
from sqlmodel import Session, select

from app.core.config import settings
from app.models import User, UserRepo, UserRepoImportStatus
from app.services.repo_naming import normalize_repo_slug, user_repo_name

logger = logging.getLogger(__name__)


class UserRepoProvisioningError(RuntimeError):
    """Raised when provisioning a user-visible repo fails."""


@dataclass(frozen=True)
class UserRemoteRepo:
    """Minimal remote repo metadata returned by Gogs."""

    repo_id: int | None
    full_name: str
    ssh_url: str | None
    html_url: str | None


class UserRepoService:
    """Service for creating and provisioning user-visible repos in the dog org."""

    def is_configured(self) -> bool:
        return bool(settings.USER_REPO_GOGS_BASE_URL and settings.USER_REPO_GOGS_TOKEN)

    def generate_slug(self) -> str:
        return normalize_repo_slug(coolname_generate_slug())

    def create_user_repo_db_only(
        self,
        *,
        session: Session,
        owner: User,
        display_name: str,
        slug: str | None = None,
        description: str | None = None,
        source_repo_url: str | None = None,
        source_branch: str | None = None,
        import_status: UserRepoImportStatus = UserRepoImportStatus.PENDING,
        import_error: str | None = None,
        imported_at: datetime | None = None,
        is_private: bool = False,
    ) -> UserRepo:
        repo = UserRepo(
            owner_user_id=owner.id,
            slug=normalize_repo_slug(slug or self.generate_slug()),
            display_name=display_name,
            description=description,
            source_repo_url=source_repo_url,
            source_branch=source_branch or settings.USER_REPO_DEFAULT_BRANCH,
            import_status=import_status,
            import_error=import_error,
            imported_at=imported_at,
            gogs_repo_name="",
            gogs_repo_id=None,
            gogs_full_name=None,
            gogs_html_url=None,
            is_private=is_private,
        )
        repo.gogs_repo_name = user_repo_name(repo.slug, repo.id)
        session.add(repo)
        session.commit()
        session.refresh(repo)
        return repo

    def get_user_repo(self, *, session: Session, repo_id: uuid.UUID) -> UserRepo | None:
        return session.get(UserRepo, repo_id)

    def list_user_repos_for_owner(
        self,
        *,
        session: Session,
        owner_user_id: uuid.UUID,
    ) -> list[UserRepo]:
        stmt = (
            select(UserRepo)
            .where(UserRepo.owner_user_id == owner_user_id)
            .order_by(UserRepo.created_at.desc())
        )
        return list(session.exec(stmt).all())

    def clone_user_repo_from_external_source(
        self,
        *,
        session: Session,
        owner: User,
        source_repo_url: str,
        display_name: str | None = None,
        slug: str | None = None,
        description: str | None = None,
        is_private: bool = False,
    ) -> UserRepo:
        normalized_source_url = self._normalize_source_repo_url(source_repo_url)
        derived_slug = slug or self._derive_slug_from_source_url(normalized_source_url)
        repo = self.create_user_repo_db_only(
            session=session,
            owner=owner,
            display_name=display_name or self._derive_display_name_from_source_url(normalized_source_url),
            slug=derived_slug,
            description=description,
            source_repo_url=normalized_source_url,
            source_branch=settings.USER_REPO_DEFAULT_BRANCH,
            import_status=UserRepoImportStatus.IMPORTING,
            import_error=None,
            imported_at=None,
            is_private=is_private,
        )

        if not self.is_configured():
            self._mark_import_failed(
                session=session,
                user_repo=repo,
                message="User repo provisioning is not configured",
            )
            return repo

        try:
            self.ensure_user_repo_remote(session=session, user_repo=repo)
        except UserRepoProvisioningError as exc:
            self._mark_import_failed(
                session=session,
                user_repo=repo,
                message=str(exc),
            )

        return repo

    def ensure_user_repo_remote(
        self,
        *,
        session: Session,
        user_repo: UserRepo,
    ) -> UserRemoteRepo | None:
        if not self.is_configured():
            logger.debug(
                "User repo provisioning skipped for repo_id=%s; service not configured",
                user_repo.id,
            )
            return None

        remote = self._get_repo(user_repo.gogs_repo_name)
        if remote is None:
            if user_repo.source_repo_url:
                remote = self._migrate_repo(user_repo)
            else:
                remote = self._create_repo(user_repo)

        changed = False
        if user_repo.gogs_repo_id != remote.repo_id:
            user_repo.gogs_repo_id = remote.repo_id
            changed = True
        if user_repo.gogs_full_name != remote.full_name:
            user_repo.gogs_full_name = remote.full_name
            changed = True
        if user_repo.gogs_html_url != remote.html_url:
            user_repo.gogs_html_url = remote.html_url
            changed = True
        if user_repo.source_repo_url:
            imported_at = datetime.utcnow()
            if user_repo.import_status != UserRepoImportStatus.READY:
                user_repo.import_status = UserRepoImportStatus.READY
                changed = True
            if user_repo.import_error is not None:
                user_repo.import_error = None
                changed = True
            if user_repo.imported_at is None:
                user_repo.imported_at = imported_at
                changed = True
        if changed:
            session.add(user_repo)
            session.commit()
            session.refresh(user_repo)

        return remote

    def _client(self) -> httpx.Client:
        return httpx.Client(
            base_url=str(settings.USER_REPO_GOGS_BASE_URL).rstrip("/"),
            headers={
                "Authorization": f"token {settings.USER_REPO_GOGS_TOKEN}",
                "Accept": "application/json",
            },
            timeout=settings.USER_REPO_GOGS_TIMEOUT_SECONDS,
        )

    def _get_repo(self, repo_name: str) -> UserRemoteRepo | None:
        path = f"/api/v1/repos/{settings.USER_REPO_GOGS_ORG}/{repo_name}"
        with self._client() as client:
            response = client.get(path)

        if response.status_code == 404:
            return None
        if response.is_error:
            raise UserRepoProvisioningError(
                f"Gogs user repo lookup failed: GET {path} returned "
                f"{response.status_code}"
            )
        return self._parse_repo(response)

    def _create_repo(self, user_repo: UserRepo) -> UserRemoteRepo:
        path = f"/api/v1/org/{settings.USER_REPO_GOGS_ORG}/repos"
        payload = {
            "name": user_repo.gogs_repo_name,
            "description": user_repo.description or "",
            "private": user_repo.is_private,
            "auto_init": False,
            "default_branch": settings.USER_REPO_DEFAULT_BRANCH,
        }
        with self._client() as client:
            response = client.post(path, json=payload)

        if response.status_code in {201, 202}:
            return self._parse_repo(response)
        if response.status_code == 409:
            existing = self._get_repo(user_repo.gogs_repo_name)
            if existing is not None:
                return existing
        raise UserRepoProvisioningError(
            f"Gogs user repo create failed: POST {path} returned "
            f"{response.status_code}"
        )

    def _migrate_repo(self, user_repo: UserRepo) -> UserRemoteRepo:
        if not user_repo.source_repo_url:
            raise UserRepoProvisioningError("Source repo URL is required for migration")

        path = "/api/v1/repos/migrate"
        last_response: httpx.Response | None = None
        payloads = self._build_migration_payloads(user_repo)

        with self._client() as client:
            for payload in payloads:
                response = client.post(path, json=payload)
                if response.status_code in {201, 202}:
                    return self._parse_repo(response)
                if response.status_code == 409:
                    existing = self._get_repo(user_repo.gogs_repo_name)
                    if existing is not None:
                        return existing
                if response.status_code not in {400, 404, 422}:
                    self._raise_api_error(
                        method="POST",
                        path=path,
                        repo_name=user_repo.gogs_repo_name,
                        response=response,
                    )
                last_response = response

        if last_response is None:
            raise UserRepoProvisioningError(
                f"Gogs repo migration failed for {settings.USER_REPO_GOGS_ORG}/{user_repo.gogs_repo_name}"
            )

        self._raise_api_error(
            method="POST",
            path=path,
            repo_name=user_repo.gogs_repo_name,
            response=last_response,
        )

    def _build_migration_payloads(self, user_repo: UserRepo) -> list[dict[str, object]]:
        base_payload: dict[str, object] = {
            "clone_addr": user_repo.source_repo_url,
            "repo_name": user_repo.gogs_repo_name,
            "description": user_repo.description or "",
            "private": user_repo.is_private,
            "mirror": False,
            "service": "git",
            "wiki": False,
            "issues": False,
            "labels": False,
            "milestones": False,
            "pull_requests": False,
            "releases": False,
        }

        payloads: list[dict[str, object]] = [
            {
                **base_payload,
                "repo_owner": settings.USER_REPO_GOGS_ORG,
            }
        ]

        org_id = self._get_org_id(settings.USER_REPO_GOGS_ORG)
        if org_id is not None:
            payloads.append(
                {
                    **base_payload,
                    "uid": org_id,
                }
            )

        return payloads

    def _get_org_id(self, org_name: str) -> int | None:
        candidate_paths = [
            f"/api/v1/orgs/{org_name}",
            f"/api/v1/org/{org_name}",
        ]
        with self._client() as client:
            for path in candidate_paths:
                response = client.get(path)
                if response.status_code == 404:
                    continue
                if response.is_error:
                    self._raise_api_error(
                        method="GET",
                        path=path,
                        repo_name=org_name,
                        response=response,
                    )
                payload = response.json()
                org_id = payload.get("id")
                if isinstance(org_id, int):
                    return org_id
        return None

    def _parse_repo(self, response: httpx.Response) -> UserRemoteRepo:
        payload = response.json()
        return UserRemoteRepo(
            repo_id=payload.get("id"),
            full_name=payload.get(
                "full_name",
                f"{settings.USER_REPO_GOGS_ORG}/{payload.get('name', '')}",
            ),
            ssh_url=payload.get("ssh_url"),
            html_url=payload.get("html_url"),
        )

    def _normalize_source_repo_url(self, source_repo_url: str) -> str:
        parsed = urlparse(source_repo_url.strip())
        if parsed.scheme.lower() != "https":
            raise ValueError("Only https repository URLs are supported")
        if not parsed.netloc or not parsed.path.strip("/"):
            raise ValueError("A valid repository URL is required")
        if parsed.username or parsed.password:
            raise ValueError("Repository URLs must not embed credentials")
        if parsed.params or parsed.query or parsed.fragment:
            raise ValueError("Repository URLs must not include params, query strings, or fragments")

        normalized_path = parsed.path.rstrip("/")
        return urlunparse(
            (
                parsed.scheme.lower(),
                parsed.netloc,
                normalized_path,
                "",
                "",
                "",
            )
        )

    def _derive_slug_from_source_url(self, source_repo_url: str) -> str:
        repo_name = self._extract_repo_basename(source_repo_url)
        return normalize_repo_slug(repo_name)

    def _derive_display_name_from_source_url(self, source_repo_url: str) -> str:
        return self._extract_repo_basename(source_repo_url)

    def _extract_repo_basename(self, source_repo_url: str) -> str:
        path = urlparse(source_repo_url).path.rstrip("/")
        repo_name = path.rsplit("/", 1)[-1]
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]
        repo_name = repo_name.strip()
        if not repo_name:
            raise ValueError("Could not determine repository name from source URL")
        return repo_name

    def _mark_import_failed(
        self,
        *,
        session: Session,
        user_repo: UserRepo,
        message: str,
    ) -> None:
        user_repo.import_status = UserRepoImportStatus.FAILED
        user_repo.import_error = message[:2000]
        user_repo.imported_at = None
        session.add(user_repo)
        session.commit()
        session.refresh(user_repo)

    def _raise_api_error(
        self,
        *,
        method: str,
        path: str,
        repo_name: str,
        response: httpx.Response,
    ) -> None:
        summary = self._summarize_error_body(response)
        raise UserRepoProvisioningError(
            f"Gogs API request failed for {settings.USER_REPO_GOGS_ORG}/{repo_name}: "
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

        if not body:
            return "empty response body"

        return body[:300]


user_repo_service = UserRepoService()
