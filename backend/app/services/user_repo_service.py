from __future__ import annotations

from datetime import datetime
import logging
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from urllib.parse import quote, urlparse, urlunparse

import httpx
from coolname import generate_slug as coolname_generate_slug
from sqlmodel import Session, select

from app.core.config import settings
from app.models import User, UserRepo, UserRepoImportStatus
from app.services.repo_naming import normalize_repo_slug, user_repo_name

logger = logging.getLogger(__name__)


class UserRepoProvisioningError(RuntimeError):
    """Raised when provisioning a user-visible repo fails."""


class UserRepoWriteError(RuntimeError):
    """Base error for user repo write operations."""


class UserRepoWriteNotFound(UserRepoWriteError):
    """Raised when the target repo does not exist."""


class UserRepoWriteUnauthorized(UserRepoWriteError):
    """Raised when the actor cannot modify the repo."""


class UserRepoWriteNotReady(UserRepoWriteError):
    """Raised when the repo is not ready for content writes."""


class UserRepoWriteUnsupportedBranch(UserRepoWriteError):
    """Raised when writes target an unsupported branch."""


class UserRepoWriteConflict(UserRepoWriteError):
    """Raised when optimistic concurrency validation fails."""


class UserRepoWriteValidationError(UserRepoWriteError):
    """Raised when the requested file mutations are invalid."""


class UserRepoWriteFailed(UserRepoWriteError):
    """Raised when git-backed write execution fails."""


@dataclass(frozen=True)
class UserRemoteRepo:
    """Minimal remote repo metadata returned by Gogs."""

    repo_id: int | None
    full_name: str
    ssh_url: str | None
    html_url: str | None


@dataclass(frozen=True)
class UserRepoFileMutation:
    path: str
    operation: str
    content: str | None = None
    encoding: str = "utf-8"


@dataclass(frozen=True)
class UserRepoCommitResult:
    repo_id: uuid.UUID
    branch: str
    previous_head_sha: str
    new_head_sha: str
    commit_message: str
    committed_at: datetime
    changed_paths: list[str]


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

    def authorize_user_repo_write(
        self,
        *,
        session: Session,
        current_user_id: uuid.UUID,
        is_superuser: bool,
        repo_id: uuid.UUID,
    ) -> UserRepo:
        user_repo = self.get_user_repo(session=session, repo_id=repo_id)
        if user_repo is None:
            raise UserRepoWriteNotFound("User repo not found")
        if is_superuser or user_repo.owner_user_id == current_user_id:
            return user_repo
        raise UserRepoWriteUnauthorized("User repo is not writable")

    def commit_user_repo_changes(
        self,
        *,
        session: Session,
        repo_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        branch: str,
        mutations: list[UserRepoFileMutation],
        commit_message: str,
        expected_head_sha: str,
        is_superuser: bool = False,
    ) -> UserRepoCommitResult:
        user_repo = self.authorize_user_repo_write(
            session=session,
            current_user_id=actor_user_id,
            is_superuser=is_superuser,
            repo_id=repo_id,
        )
        if user_repo.import_status != UserRepoImportStatus.READY:
            raise UserRepoWriteNotReady("User repo is not ready for writes")

        normalized_branch = (branch or "").strip()
        default_branch = user_repo.source_branch or settings.USER_REPO_DEFAULT_BRANCH
        if normalized_branch != default_branch:
            raise UserRepoWriteUnsupportedBranch(
                f"Writes are only supported for branch {default_branch}"
            )

        normalized_expected_head_sha = (expected_head_sha or "").strip()
        if not normalized_expected_head_sha:
            raise UserRepoWriteValidationError("expected_head_sha is required")

        normalized_commit_message = commit_message.strip()
        if not normalized_commit_message:
            raise UserRepoWriteValidationError("commit_message is required")

        normalized_mutations = self._normalize_write_mutations(mutations)
        actor = session.get(User, actor_user_id)
        if actor is None:
            raise UserRepoWriteUnauthorized("Actor user not found")

        return self._commit_changes_to_remote(
            user_repo=user_repo,
            actor=actor,
            branch=normalized_branch,
            mutations=normalized_mutations,
            commit_message=normalized_commit_message,
            expected_head_sha=normalized_expected_head_sha,
        )

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
        ready_at = datetime.utcnow()
        if user_repo.import_status != UserRepoImportStatus.READY:
            user_repo.import_status = UserRepoImportStatus.READY
            changed = True
        if user_repo.import_error is not None:
            user_repo.import_error = None
            changed = True
        if user_repo.imported_at is None:
            user_repo.imported_at = ready_at
            changed = True
        if changed:
            session.add(user_repo)
            session.commit()
            session.refresh(user_repo)

        return remote

    def delete_user_repo_remote(self, *, user_repo: UserRepo) -> bool:
        """
        Best-effort remote delete for a user repo.

        Returns True when a remote repo was deleted, False when it was already absent
        or provisioning is not configured.
        """
        if not self.is_configured():
            return False

        owner = self._repo_api_owner(user_repo=user_repo)
        path = f"/api/v1/repos/{owner}/{user_repo.gogs_repo_name}"
        with self._client() as client:
            response = client.delete(path)

        if response.status_code == 404:
            return False
        if response.status_code in {200, 202, 204}:
            return True
        raise UserRepoProvisioningError(
            f"Gogs user repo delete failed: DELETE {path} returned {response.status_code}"
        )

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

    def _resolve_repo_head_sha(self, *, user_repo: UserRepo, ref: str) -> str:
        owner = self._repo_api_owner(user_repo=user_repo)
        path = f"/api/v1/repos/{owner}/{user_repo.gogs_repo_name}/commits/{quote(ref, safe='')}"
        with self._client() as client:
            response = client.get(
                path,
                headers={"Accept": "application/vnd.gogs.sha"},
            )

        if response.status_code == 404:
            raise UserRepoWriteUnsupportedBranch("Branch not found")
        if response.is_error:
            raise UserRepoWriteFailed(
                f"Gogs head lookup failed: GET {path} returned {response.status_code}"
            )

        sha = response.text.strip()
        if not sha:
            raise UserRepoWriteUnsupportedBranch("Branch not found")
        return sha

    def _repo_api_owner(self, *, user_repo: UserRepo) -> str:
        full_name = (user_repo.gogs_full_name or "").strip()
        if "/" in full_name:
            owner, _, _repo_name = full_name.partition("/")
            if owner.strip():
                return owner.strip()
        return settings.USER_REPO_GOGS_ORG

    def _normalize_write_mutations(
        self,
        mutations: list[UserRepoFileMutation],
    ) -> list[UserRepoFileMutation]:
        if not mutations:
            raise UserRepoWriteValidationError("At least one mutation is required")

        normalized: list[UserRepoFileMutation] = []
        seen_paths: set[str] = set()
        for mutation in mutations:
            normalized_path = self._normalize_repo_path(mutation.path)
            if normalized_path in seen_paths:
                raise UserRepoWriteValidationError(
                    f"Duplicate mutation path: {normalized_path}"
                )
            seen_paths.add(normalized_path)

            operation = mutation.operation.strip().lower()
            if operation not in {"upsert", "delete"}:
                raise UserRepoWriteValidationError(
                    f"Unsupported mutation operation: {mutation.operation}"
                )
            if operation == "upsert":
                if mutation.content is None:
                    raise UserRepoWriteValidationError(
                        f"Mutation content is required for {normalized_path}"
                    )
                if mutation.encoding.lower() != "utf-8":
                    raise UserRepoWriteValidationError(
                        f"Unsupported encoding for {normalized_path}: {mutation.encoding}"
                    )
                normalized.append(
                    UserRepoFileMutation(
                        path=normalized_path,
                        operation=operation,
                        content=mutation.content,
                        encoding="utf-8",
                    )
                )
            else:
                if mutation.content is not None:
                    raise UserRepoWriteValidationError(
                        f"Delete mutation must not include content for {normalized_path}"
                    )
                normalized.append(
                    UserRepoFileMutation(
                        path=normalized_path,
                        operation=operation,
                        content=None,
                        encoding="utf-8",
                    )
                )

        return normalized

    def _normalize_repo_path(self, path: str) -> str:
        normalized = path.strip().strip("/")
        if not normalized:
            raise UserRepoWriteValidationError("Mutation path is required")
        parts = normalized.split("/")
        if any(part in {"", ".", ".."} for part in parts):
            raise UserRepoWriteValidationError(f"Invalid repo path: {path}")
        return "/".join(parts)

    def _commit_changes_to_remote(
        self,
        *,
        user_repo: UserRepo,
        actor: User,
        branch: str,
        mutations: list[UserRepoFileMutation],
        commit_message: str,
        expected_head_sha: str,
    ) -> UserRepoCommitResult:
        remote_url = self._build_authenticated_git_remote_url(user_repo=user_repo)
        writes_root = Path(settings.USER_REPO_WRITES_PATH)
        writes_root.mkdir(parents=True, exist_ok=True)

        try:
            with tempfile.TemporaryDirectory(
                dir=writes_root,
                prefix=f"{user_repo.id}-",
            ) as temp_dir_name:
                temp_dir = Path(temp_dir_name)
                worktree_dir = temp_dir / "repo"
                git_env = self._build_git_auth_env(worktree_dir=temp_dir)
                self._git_clone_for_write(
                    remote_url=remote_url,
                    branch=branch,
                    worktree_dir=worktree_dir,
                    env=git_env,
                )
                self._git_ensure_head(
                    worktree_dir=worktree_dir,
                    expected_head_sha=expected_head_sha,
                )
                self._git_config_commit_identity(worktree_dir=worktree_dir)
                changed_paths = self._apply_write_mutations(
                    worktree_dir=worktree_dir,
                    mutations=mutations,
                )
                if not self._git_has_staged_changes(worktree_dir=worktree_dir):
                    raise UserRepoWriteValidationError("Requested changes produce no diff")

                author = f"{actor.email} <{actor.email}>"
                self._git_commit(
                    worktree_dir=worktree_dir,
                    commit_message=commit_message,
                    author=author,
                )
                new_head_sha = self._git_rev_parse_head(worktree_dir=worktree_dir)
                self._git_push(
                    worktree_dir=worktree_dir,
                    branch=branch,
                    env=git_env,
                )
        except UserRepoWriteError:
            raise
        except subprocess.CalledProcessError as exc:
            stderr = (
                exc.stderr.decode()
                if isinstance(exc.stderr, bytes)
                else exc.stderr or str(exc)
            )
            raise UserRepoWriteFailed(stderr.strip()) from exc
        except OSError as exc:
            raise UserRepoWriteFailed(str(exc)) from exc

        return UserRepoCommitResult(
            repo_id=user_repo.id,
            branch=branch,
            previous_head_sha=expected_head_sha,
            new_head_sha=new_head_sha,
            commit_message=commit_message,
            committed_at=datetime.utcnow(),
            changed_paths=changed_paths,
        )

    def _build_authenticated_git_remote_url(self, *, user_repo: UserRepo) -> str:
        base_url = urlparse(str(settings.USER_REPO_GOGS_BASE_URL).rstrip("/"))
        base_path_prefix = base_url.path.rstrip("/")

        if user_repo.gogs_html_url:
            parsed = urlparse(user_repo.gogs_html_url)
            path = parsed.path if parsed.path.endswith(".git") else f"{parsed.path}.git"
            return urlunparse(
                (
                    base_url.scheme,
                    base_url.netloc,
                    f"{base_path_prefix}{path}",
                    "",
                    "",
                    "",
                )
            )

        owner = self._repo_api_owner(user_repo=user_repo)
        return urlunparse(
            (
                base_url.scheme,
                base_url.netloc,
                f"{base_path_prefix}/{owner}/{user_repo.gogs_repo_name}.git",
                "",
                "",
                "",
            )
        )

    def _build_git_auth_env(self, *, worktree_dir: Path) -> dict[str, str]:
        username = (settings.USER_REPO_GIT_USERNAME or "").strip()
        password = settings.USER_REPO_GIT_PASSWORD or ""
        if not username or not password:
            raise UserRepoWriteFailed(
                "HTTP git credentials are not configured for user repo writes"
            )

        askpass_path = worktree_dir / ".git-askpass"
        askpass_path.write_text(
            "\n".join(
                [
                    "#!/bin/sh",
                    'case "$1" in',
                    f"  *Username*) printf '%s\\n' {shlex.quote(username)} ;;",
                    f"  *Password*) printf '%s\\n' {shlex.quote(password)} ;;",
                    "  *) printf '\\n' ;;",
                    "esac",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        askpass_path.chmod(0o700)

        env = os.environ.copy()
        env["GIT_ASKPASS"] = str(askpass_path)
        env["GIT_TERMINAL_PROMPT"] = "0"
        return env

    def _git_clone_for_write(
        self,
        *,
        remote_url: str,
        branch: str,
        worktree_dir: Path,
        env: dict[str, str],
    ) -> None:
        subprocess.run(
            [
                "git",
                "clone",
                "--branch",
                branch,
                "--single-branch",
                remote_url,
                str(worktree_dir),
            ],
            check=True,
            capture_output=True,
            env=env,
        )

    def _git_ensure_head(self, *, worktree_dir: Path, expected_head_sha: str) -> None:
        actual_head_sha = self._git_rev_parse_head(worktree_dir=worktree_dir)
        if actual_head_sha != expected_head_sha:
            raise UserRepoWriteConflict("Repo head no longer matches expected_head_sha")

    def _git_config_commit_identity(self, *, worktree_dir: Path) -> None:
        self._run_git(
            worktree_dir,
            ["config", "user.name", "dog-repo-service"],
        )
        self._run_git(
            worktree_dir,
            ["config", "user.email", "dog-repo-service@localhost"],
        )

    def _apply_write_mutations(
        self,
        *,
        worktree_dir: Path,
        mutations: list[UserRepoFileMutation],
    ) -> list[str]:
        changed_paths: list[str] = []
        for mutation in mutations:
            target_path = worktree_dir / mutation.path
            if mutation.operation == "upsert":
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text(mutation.content or "", encoding=mutation.encoding)
            else:
                if not target_path.exists():
                    raise UserRepoWriteValidationError(
                        f"Cannot delete missing file: {mutation.path}"
                    )
                if target_path.is_dir():
                    raise UserRepoWriteValidationError(
                        f"Delete only supports files: {mutation.path}"
                    )
                target_path.unlink()
            self._run_git(
                worktree_dir,
                ["add", "--all", "--", mutation.path],
            )
            changed_paths.append(mutation.path)
        return changed_paths

    def _git_has_staged_changes(self, *, worktree_dir: Path) -> bool:
        result = self._run_git(
            worktree_dir,
            ["diff", "--cached", "--quiet"],
            check=False,
        )
        return result.returncode != 0

    def _git_commit(
        self,
        *,
        worktree_dir: Path,
        commit_message: str,
        author: str,
    ) -> None:
        result = self._run_git(
            worktree_dir,
            ["commit", "-m", commit_message, "--author", author],
            check=False,
            text=True,
        )
        if result.returncode != 0:
            output = (result.stderr or result.stdout).strip()
            raise UserRepoWriteFailed(output or "git commit failed")

    def _git_push(
        self,
        *,
        worktree_dir: Path,
        branch: str,
        env: dict[str, str],
    ) -> None:
        result = self._run_git(
            worktree_dir,
            ["push", "origin", f"HEAD:{branch}"],
            check=False,
            text=True,
            env=env,
        )
        if result.returncode != 0:
            output = (result.stderr or result.stdout).strip()
            if "non-fast-forward" in output or "[rejected]" in output:
                raise UserRepoWriteConflict(output or "git push rejected")
            raise UserRepoWriteFailed(output or "git push failed")

    def _git_rev_parse_head(self, *, worktree_dir: Path) -> str:
        return self._run_git(
            worktree_dir,
            ["rev-parse", "HEAD"],
            text=True,
        ).stdout.strip()

    def _run_git(
        self,
        repo_path: Path,
        args: list[str],
        *,
        check: bool = True,
        text: bool = False,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            ["git", *args],
            cwd=repo_path,
            check=check,
            capture_output=True,
            text=text,
            env=env,
        )

    def _normalize_source_repo_url(self, source_repo_url: str) -> str:
        parsed = urlparse(source_repo_url.strip())
        # if parsed.scheme.lower() != "https":
        #     raise ValueError("Only https repository URLs are supported")
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
