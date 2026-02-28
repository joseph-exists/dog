from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

import httpx
from coolname import generate_slug as coolname_generate_slug
from sqlmodel import Session, select

from app.core.config import settings
from app.models import User, UserRepo
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
        is_private: bool = False,
    ) -> UserRepo:
        repo = UserRepo(
            owner_user_id=owner.id,
            slug=normalize_repo_slug(slug or self.generate_slug()),
            display_name=display_name,
            description=description,
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
            "default_branch": "main",
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


user_repo_service = UserRepoService()
