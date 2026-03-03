from __future__ import annotations

import mimetypes
import subprocess
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlmodel import Session

from app.core.config import settings
from app.models import (
    ShadowRepo,
    ShadowRepoCommitSummary,
    ShadowRepoFileContent,
    ShadowRepoSummary,
    ShadowRepoTreeEntry,
    ShadowRepoViewResponse,
)
from app.services.shadow_git import ensure_repo, get_repo_path, get_repo_remote_url
from app.services.shadow_read_service import ShadowRepoNotFound, shadow_read_service


class ShadowRepoViewError(RuntimeError):
    """Base error for shadow repo view reads."""


class ShadowRepoViewNotFound(ShadowRepoViewError):
    """Raised when repo view data is unavailable."""


@dataclass(frozen=True)
class AuthorizedShadowRepo:
    shadow_repo: ShadowRepo
    ref: str


class ShadowRepoViewService:
    def authorize_shadow_repo_read(
        self,
        *,
        session: Session,
        current_user_id: uuid.UUID,
        is_superuser: bool,
        entity_type: str,
        entity_id: uuid.UUID,
    ) -> AuthorizedShadowRepo:
        try:
            shadow_repo = shadow_read_service._get_shadow_repo(
                session=session,
                entity_type=entity_type,
                entity_id=entity_id,
            )
        except ShadowRepoNotFound as exc:
            raise ShadowRepoViewNotFound("Shadow repo not found") from exc

        if not is_superuser and shadow_repo.owner_id != current_user_id:
            raise ShadowRepoViewNotFound("Shadow repo not found")

        return AuthorizedShadowRepo(
            shadow_repo=shadow_repo,
            ref=settings.SHADOW_REPO_DEFAULT_BRANCH,
        )

    def get_repo_view(
        self,
        *,
        session: Session,
        entity_type: str,
        entity_id: uuid.UUID,
        path: str = "",
        commit_limit: int = 10,
    ) -> ShadowRepoViewResponse:
        shadow_read_service._get_shadow_repo(
            session=session,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        repo_path = self._ensure_repo_path(
            entity_type=entity_type,
            entity_id=entity_id,
        )
        ref = settings.SHADOW_REPO_DEFAULT_BRANCH

        commits = self._list_recent_commits(repo_path=repo_path, limit=commit_limit)
        tree = self._list_tree(repo_path=repo_path, ref=ref, path=path)

        latest_commit = commits[0] if commits else None
        summary = ShadowRepoSummary(
            entity_type=entity_type,
            entity_id=entity_id,
            repo_available=True,
            default_branch=ref,
            latest_commit_sha=latest_commit.sha if latest_commit else None,
            latest_commit_message=latest_commit.message if latest_commit else None,
            latest_commit_authored_at=latest_commit.authored_at if latest_commit else None,
        )

        return ShadowRepoViewResponse(
            summary=summary,
            commits=commits,
            tree=tree,
            tree_root_path=path,
            ref=ref,
        )

    def get_file_content(
        self,
        *,
        session: Session,
        entity_type: str,
        entity_id: uuid.UUID,
        path: str,
    ) -> ShadowRepoFileContent:
        shadow_read_service._get_shadow_repo(
            session=session,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        if not path.strip():
            raise ShadowRepoViewNotFound("File path is required")

        repo_path = self._ensure_repo_path(
            entity_type=entity_type,
            entity_id=entity_id,
        )
        ref = settings.SHADOW_REPO_DEFAULT_BRANCH
        content = self._read_file(repo_path=repo_path, ref=ref, path=path)
        content_type, _ = mimetypes.guess_type(path)

        return ShadowRepoFileContent(
            path=path,
            ref=ref,
            content=content,
            encoding="utf-8",
            size_bytes=len(content.encode("utf-8")),
            content_type=content_type,
        )

    def _ensure_repo_path(self, *, entity_type: str, entity_id: uuid.UUID) -> Path:
        repo_path = get_repo_path(
            Path(settings.SHADOW_REPOS_PATH),
            entity_type,
            str(entity_id),
        )
        remote_url = get_repo_remote_url(
            settings.SHADOW_REPO_URL_TEMPLATE,
            entity_type,
            str(entity_id),
        )
        try:
            ensure_repo(
                repo_path,
                remote_url=remote_url,
                default_branch=settings.SHADOW_REPO_DEFAULT_BRANCH,
            )
        except subprocess.CalledProcessError as exc:
            raise ShadowRepoViewNotFound("Shadow repo not found") from exc

        if not (repo_path / ".git").exists():
            raise ShadowRepoViewNotFound("Shadow repo not found")
        return repo_path

    def _list_recent_commits(
        self,
        *,
        repo_path: Path,
        limit: int,
    ) -> list[ShadowRepoCommitSummary]:
        result = subprocess.run(
            [
                "git",
                "log",
                f"-n{max(1, limit)}",
                "--date=iso-strict",
                "--pretty=format:%H%x1f%s%x1f%an%x1f%aI",
            ],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return []

        commits: list[ShadowRepoCommitSummary] = []
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            parts = line.split("\x1f")
            if len(parts) != 4:
                continue
            sha, message, author_name, authored_at = parts
            commit_time = None
            if authored_at:
                try:
                    commit_time = datetime.fromisoformat(authored_at).astimezone(
                        timezone.utc
                    )
                except ValueError:
                    commit_time = None
            commits.append(
                ShadowRepoCommitSummary(
                    sha=sha,
                    short_sha=sha[:8],
                    message=message,
                    author_name=author_name or None,
                    authored_at=commit_time,
                )
            )
        return commits

    def _list_tree(
        self,
        *,
        repo_path: Path,
        ref: str,
        path: str,
    ) -> list[ShadowRepoTreeEntry]:
        treeish = ref if not path else f"{ref}:{path}"
        result = subprocess.run(
            ["git", "ls-tree", "-l", treeish],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise ShadowRepoViewNotFound("Shadow repo not found")

        entries: list[ShadowRepoTreeEntry] = []
        base_path = path.rstrip("/")
        for line in result.stdout.splitlines():
            if not line.strip() or "\t" not in line:
                continue
            metadata, name = line.split("\t", 1)
            parts = metadata.split()
            if len(parts) < 4:
                continue
            entry_type = "directory" if parts[1] == "tree" else "file"
            size_token = parts[3]
            full_path = f"{base_path}/{name}" if base_path else name
            entries.append(
                ShadowRepoTreeEntry(
                    path=full_path,
                    name=name,
                    entry_type=entry_type,
                    size_bytes=None if size_token == "-" else int(size_token),
                )
            )
        return entries

    def _read_file(self, *, repo_path: Path, ref: str, path: str) -> str:
        result = subprocess.run(
            ["git", "show", f"{ref}:{path}"],
            cwd=repo_path,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise ShadowRepoViewNotFound("Shadow repo not found")
        return result.stdout.decode("utf-8", errors="replace")


shadow_repo_view_service = ShadowRepoViewService()
