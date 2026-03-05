from __future__ import annotations

import mimetypes
import uuid
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

from sqlmodel import Session

from app.core.config import settings
from app.models import (
    ShadowRepoCommitSummary,
    ShadowRepoTreeEntry,
    UserRepo,
    UserRepoFileContent,
    UserRepoImportStatus,
    UserRepoPublic,
    UserRepoReadmeContent,
    UserRepoSummary,
    UserRepoViewResponse,
    UserRepoViewerCapabilities,
)
from app.services.user_repo_service import user_repo_service

MAX_TEXT_PREVIEW_BYTES = 1_000_000
README_CANDIDATE_PATHS = ("README.md", "README", "readme.md", "Readme.md")


class UserRepoViewError(RuntimeError):
    """Base error for user repo view reads."""


class UserRepoViewNotFound(UserRepoViewError):
    """Raised when the requested repo is unavailable or unauthorized."""


class UserRepoBranchNotFound(UserRepoViewError):
    """Raised when the requested branch/ref is unsupported."""


class UserRepoPathError(UserRepoViewError):
    """Raised when the requested repo path is invalid for the operation."""


class UserRepoBackendUnavailable(UserRepoViewError):
    """Raised when the backing forge cannot satisfy the request."""


class UserRepoViewService:
    def build_capabilities(self, *, user_repo: UserRepo) -> UserRepoViewerCapabilities:
        repo_ready = user_repo.import_status == UserRepoImportStatus.READY
        default_branch = user_repo.source_branch or settings.USER_REPO_DEFAULT_BRANCH
        return UserRepoViewerCapabilities(
            has_file_tree=repo_ready,
            has_blob_content=repo_ready,
            has_commit_history=repo_ready,
            has_search=False,
            has_branches=False,
            default_branch=default_branch,
        )

    def to_public_model(self, *, user_repo: UserRepo) -> UserRepoPublic:
        public_model = UserRepoPublic.model_validate(user_repo, from_attributes=True)
        return public_model.model_copy(
            update={
                "default_branch": (
                    user_repo.source_branch or settings.USER_REPO_DEFAULT_BRANCH
                ),
                "capabilities": self.build_capabilities(user_repo=user_repo),
            }
        )

    def authorize_user_repo_read(
        self,
        *,
        session: Session,
        current_user_id: uuid.UUID,
        is_superuser: bool,
        repo_id: uuid.UUID,
    ) -> UserRepo:
        user_repo = user_repo_service.get_user_repo(session=session, repo_id=repo_id)
        if user_repo is None:
            raise UserRepoViewNotFound("User repo not found")
        if is_superuser or user_repo.owner_user_id == current_user_id:
            return user_repo
        if user_repo.is_private:
            raise UserRepoViewNotFound("User repo not found")
        return user_repo

    def get_repo_view(
        self,
        *,
        session: Session,
        repo_id: uuid.UUID,
        path: str = "",
        ref: str | None = None,
        commit_limit: int = 10,
    ) -> UserRepoViewResponse:
        user_repo = self._require_ready_repo(session=session, repo_id=repo_id)
        resolved_ref, commit_sha = self._resolve_commit_ref(
            user_repo=user_repo,
            requested_ref=ref,
        )
        commits = (
            self._list_recent_commits(
                user_repo=user_repo,
                ref=resolved_ref,
                limit=commit_limit,
            )
            if commit_limit > 0
            else []
        )
        tree = self._list_tree(
            user_repo=user_repo,
            commit_sha=commit_sha,
            path=path,
        )
        latest_commit = commits[0] if commits else None
        summary = UserRepoSummary(
            repo_id=user_repo.id,
            slug=user_repo.slug,
            display_name=user_repo.display_name,
            repo_available=True,
            default_branch=resolved_ref,
            latest_commit_sha=latest_commit.sha if latest_commit else None,
            latest_commit_message=latest_commit.message if latest_commit else None,
            latest_commit_authored_at=latest_commit.authored_at if latest_commit else None,
        )
        return UserRepoViewResponse(
            summary=summary,
            commits=commits,
            tree=tree,
            tree_root_path=path,
            ref=resolved_ref,
        )

    def get_file_content(
        self,
        *,
        session: Session,
        repo_id: uuid.UUID,
        path: str,
        ref: str | None = None,
    ) -> UserRepoFileContent:
        user_repo = self._require_ready_repo(session=session, repo_id=repo_id)
        _resolved_ref, commit_sha = self._resolve_commit_ref(
            user_repo=user_repo,
            requested_ref=ref,
        )
        return self._read_file(user_repo=user_repo, commit_sha=commit_sha, path=path)

    def get_readme(
        self,
        *,
        session: Session,
        repo_id: uuid.UUID,
        ref: str | None = None,
    ) -> UserRepoReadmeContent:
        user_repo = self._require_ready_repo(session=session, repo_id=repo_id)
        _resolved_ref, commit_sha = self._resolve_commit_ref(
            user_repo=user_repo,
            requested_ref=ref,
        )
        for candidate in README_CANDIDATE_PATHS:
            try:
                file_content = self._read_file(
                    user_repo=user_repo,
                    commit_sha=commit_sha,
                    path=candidate,
                )
            except UserRepoPathError:
                continue
            return UserRepoReadmeContent(
                **file_content.model_dump(),
                resolved_from_path=candidate,
            )
        raise UserRepoViewNotFound("README not found")

    def _require_ready_repo(self, *, session: Session, repo_id: uuid.UUID) -> UserRepo:
        user_repo = user_repo_service.get_user_repo(session=session, repo_id=repo_id)
        if user_repo is None:
            raise UserRepoViewNotFound("User repo not found")
        if user_repo.import_status != UserRepoImportStatus.READY:
            raise UserRepoViewNotFound("User repo not found")
        return user_repo

    def _resolve_commit_ref(
        self,
        *,
        user_repo: UserRepo,
        requested_ref: str | None,
    ) -> tuple[str, str]:
        repo_metadata = self._get_repo_metadata(user_repo=user_repo)
        default_branch = (
            str(repo_metadata.get("default_branch") or "").strip()
            or user_repo.source_branch
            or settings.USER_REPO_DEFAULT_BRANCH
        )
        resolved_ref = (requested_ref or default_branch).strip() or default_branch
        commit_sha = self._resolve_commit_sha(user_repo=user_repo, ref=resolved_ref)
        return resolved_ref, commit_sha

    def _repo_api_owner(self, *, user_repo: UserRepo) -> str:
        full_name = (user_repo.gogs_full_name or "").strip()
        if "/" in full_name:
            owner, _, _repo_name = full_name.partition("/")
            if owner.strip():
                return owner.strip()
        return settings.USER_REPO_GOGS_ORG

    def _repo_api_path(self, *, user_repo: UserRepo, suffix: str = "") -> str:
        return (
            f"/api/v1/repos/{self._repo_api_owner(user_repo=user_repo)}"
            f"/{user_repo.gogs_repo_name}{suffix}"
        )

    def _client(self):
        return user_repo_service._client()

    def _request_json(
        self,
        *,
        user_repo: UserRepo,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        with self._client() as client:
            response = client.get(path, params=params)
        if response.status_code == 404:
            raise UserRepoPathError("Path not found")
        if response.is_error:
            raise UserRepoBackendUnavailable(
                f"Gogs user repo read failed: GET {path} returned {response.status_code}"
            )
        return response.json()

    def _request_text(
        self,
        *,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> str:
        with self._client() as client:
            response = client.get(path, params=params, headers=headers)
        if response.status_code == 404:
            raise UserRepoPathError("Path not found")
        if response.is_error:
            raise UserRepoBackendUnavailable(
                f"Gogs user repo read failed: GET {path} returned {response.status_code}"
            )
        return response.text

    def _request_bytes(
        self,
        *,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> bytes:
        with self._client() as client:
            response = client.get(path, params=params, headers=headers)
        if response.status_code == 404:
            raise UserRepoPathError("Path not found")
        if response.is_error:
            raise UserRepoBackendUnavailable(
                f"Gogs user repo read failed: GET {path} returned {response.status_code}"
            )
        return response.content

    def _get_repo_metadata(self, *, user_repo: UserRepo) -> dict[str, Any]:
        payload = self._request_json(
            user_repo=user_repo,
            path=self._repo_api_path(user_repo=user_repo),
        )
        if not isinstance(payload, dict):
            raise UserRepoBackendUnavailable("Invalid repo metadata response")
        return payload

    def _resolve_commit_sha(self, *, user_repo: UserRepo, ref: str) -> str:
        path = self._repo_api_path(
            user_repo=user_repo,
            suffix=f"/commits/{quote(ref, safe='')}",
        )
        sha = self._request_text(
            path=path,
            headers={"Accept": "application/vnd.gogs.sha"},
        ).strip()
        if not sha:
            raise UserRepoBranchNotFound("Branch not found")
        return sha

    def _list_recent_commits(
        self,
        *,
        user_repo: UserRepo,
        ref: str,
        limit: int,
    ) -> list[ShadowRepoCommitSummary]:
        try:
            payload = self._request_json(
                user_repo=user_repo,
                path=self._repo_api_path(user_repo=user_repo, suffix="/commits"),
                params={"sha": ref, "limit": max(1, limit)},
            )
        except UserRepoPathError:
            return []

        if not isinstance(payload, list):
            return []

        commits: list[ShadowRepoCommitSummary] = []
        for entry in payload:
            if not isinstance(entry, dict):
                continue
            sha = str(entry.get("sha") or "").strip()
            commit = entry.get("commit")
            if not sha or not isinstance(commit, dict):
                continue
            author = commit.get("author") if isinstance(commit.get("author"), dict) else {}
            authored_at = None
            date_value = author.get("date")
            if isinstance(date_value, str) and date_value:
                try:
                    authored_at = datetime.fromisoformat(
                        date_value.replace("Z", "+00:00")
                    ).astimezone(timezone.utc)
                except ValueError:
                    authored_at = None
            commits.append(
                ShadowRepoCommitSummary(
                    sha=sha,
                    short_sha=sha[:8],
                    message=str(commit.get("message") or "").strip() or sha[:8],
                    author_name=(
                        str(author.get("name")).strip()
                        if author.get("name") is not None
                        else None
                    ),
                    authored_at=authored_at,
                )
            )
        return commits

    def _list_tree(
        self,
        *,
        user_repo: UserRepo,
        commit_sha: str,
        path: str,
    ) -> list[ShadowRepoTreeEntry]:
        normalized_path = path.strip("/")
        tree_sha = commit_sha
        base_path = ""

        if normalized_path:
            for segment in normalized_path.split("/"):
                payload = self._get_git_tree(user_repo=user_repo, tree_sha=tree_sha)
                entries = payload.get("tree")
                if not isinstance(entries, list):
                    raise UserRepoPathError("Path not found")
                next_entry = next(
                    (
                        entry
                        for entry in entries
                        if isinstance(entry, dict)
                        and str(entry.get("path") or "").strip() == segment
                    ),
                    None,
                )
                if not isinstance(next_entry, dict):
                    raise UserRepoPathError("Path not found")
                if str(next_entry.get("type") or "").strip() != "tree":
                    raise UserRepoPathError("Path points to a file")
                next_sha = str(next_entry.get("sha") or "").strip()
                if not next_sha:
                    raise UserRepoPathError("Path not found")
                tree_sha = next_sha
                base_path = (
                    f"{base_path}/{segment}" if base_path else segment
                )

        payload = self._get_git_tree(user_repo=user_repo, tree_sha=tree_sha)
        entries = payload.get("tree")
        if not isinstance(entries, list):
            raise UserRepoPathError("Path not found")

        result: list[ShadowRepoTreeEntry] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            name = str(entry.get("path") or "").strip()
            entry_type = str(entry.get("type") or "").strip()
            if not name or entry_type not in {"tree", "blob"}:
                continue
            size_value = entry.get("size")
            full_path = f"{base_path}/{name}" if base_path else name
            result.append(
                ShadowRepoTreeEntry(
                    path=full_path,
                    name=name,
                    entry_type="directory" if entry_type == "tree" else "file",
                    size_bytes=size_value if isinstance(size_value, int) else None,
                )
            )
        return result

    def _get_git_tree(self, *, user_repo: UserRepo, tree_sha: str) -> dict[str, Any]:
        payload = self._request_json(
            user_repo=user_repo,
            path=self._repo_api_path(
                user_repo=user_repo,
                suffix=f"/git/trees/{quote(tree_sha, safe='')}",
            ),
        )
        if not isinstance(payload, dict):
            raise UserRepoBackendUnavailable("Invalid git tree response")
        return payload

    def _read_file(
        self,
        *,
        user_repo: UserRepo,
        commit_sha: str,
        path: str,
    ) -> UserRepoFileContent:
        normalized_path = path.strip("/")
        if not normalized_path:
            raise UserRepoPathError("File path is required")

        tree_entries = self._list_tree(
            user_repo=user_repo,
            commit_sha=commit_sha,
            path="/".join(normalized_path.split("/")[:-1]),
        )
        file_entry = next((entry for entry in tree_entries if entry.path == normalized_path), None)
        if file_entry is None or file_entry.entry_type != "file":
            raise UserRepoPathError("Path is not a file")

        raw_bytes = self._request_bytes(
            path=self._repo_api_path(
                user_repo=user_repo,
                suffix=f"/raw/{quote(commit_sha, safe='')}/{quote(normalized_path, safe='/')}",
            ),
        )

        size_bytes = file_entry.size_bytes or len(raw_bytes)
        content_type, _ = mimetypes.guess_type(normalized_path)
        is_binary = b"\x00" in raw_bytes[:8192]
        is_truncated = len(raw_bytes) > MAX_TEXT_PREVIEW_BYTES
        truncation_reason = (
            f"Preview limited to {MAX_TEXT_PREVIEW_BYTES} bytes"
            if is_truncated
            else None
        )
        preview_bytes = raw_bytes[:MAX_TEXT_PREVIEW_BYTES] if is_truncated else raw_bytes
        is_unsupported_preview = is_binary
        content = "" if is_binary else preview_bytes.decode("utf-8", errors="replace")

        return UserRepoFileContent(
            path=normalized_path,
            ref=commit_sha,
            content=content,
            encoding="utf-8",
            size_bytes=size_bytes,
            content_type=content_type,
            is_binary=is_binary,
            is_truncated=is_truncated,
            truncation_reason=truncation_reason,
            is_unsupported_preview=is_unsupported_preview,
        )


user_repo_view_service = UserRepoViewService()
