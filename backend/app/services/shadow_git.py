"""shadow_git.py - Git operations for shadow versioning.

Thin wrapper around git subprocess calls. Each entity gets its own
git repository cached at {SHADOW_REPOS_PATH}/{entity_type}/{entity_id}/.
When configured, repos are synced with remote URLs derived from a template.
"""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ShadowGitError(Exception):
    """Base exception for shadow git operations."""

    pass


class SnapshotNotFoundError(ShadowGitError):
    """Raised when a snapshot cannot be read (invalid SHA or missing file)."""

    pass


class CommitError(ShadowGitError):
    """Raised when a commit operation fails."""

    pass


def _run_git(
    repo_path: Path,
    args: list[str],
    *,
    check: bool = True,
    text: bool = False,
) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]:
    """Run a git command in repo_path."""
    return subprocess.run(
        ["git", *args],
        cwd=repo_path,
        check=check,
        capture_output=True,
        text=text,
    )


def _ensure_local_identity(repo_path: Path) -> None:
    """Configure local git identity for automated commits."""
    _run_git(repo_path, ["config", "user.name", "shadow-system"])
    _run_git(repo_path, ["config", "user.email", "shadow@localhost"])


def _checkout_tracking_branch(
    repo_path: Path,
    *,
    remote_name: str,
    branch: str,
) -> None:
    """Ensure local working tree is on the expected branch."""
    local_branch = _run_git(
        repo_path,
        ["rev-parse", "--abbrev-ref", "HEAD"],
        check=False,
        text=True,
    ).stdout.strip()
    if local_branch != branch:
        _run_git(repo_path, ["checkout", "-B", branch])

    remote_branch_exists = _run_git(
        repo_path,
        ["rev-parse", "--verify", f"{remote_name}/{branch}"],
        check=False,
    ).returncode == 0
    if remote_branch_exists:
        _run_git(
            repo_path,
            ["branch", "--set-upstream-to", f"{remote_name}/{branch}", branch],
            check=False,
        )
        _run_git(repo_path, ["pull", "--ff-only", remote_name, branch], check=False)


def ensure_repo(
    repo_path: Path,
    *,
    remote_url: str | None = None,
    remote_name: str = "origin",
    default_branch: str = "main",
) -> None:
    """Initialize git repo if it doesn't exist.

    Creates the directory structure and initializes a git repository
    with proper configuration for automated commits.

    Args:
        repo_path: Path where the git repo should exist.
    """
    if not (repo_path / ".git").exists():
        repo_path.parent.mkdir(parents=True, exist_ok=True)
        if remote_url:
            subprocess.run(
                [
                    "git",
                    "clone",
                    "--origin",
                    remote_name,
                    remote_url,
                    str(repo_path),
                ],
                check=True,
                capture_output=True,
            )
        else:
            repo_path.mkdir(parents=True, exist_ok=True)
            _run_git(repo_path, ["init", "-b", default_branch])

    if remote_url:
        current_remote = _run_git(
            repo_path,
            ["remote", "get-url", remote_name],
            check=False,
            text=True,
        )
        if current_remote.returncode != 0:
            _run_git(repo_path, ["remote", "add", remote_name, remote_url])
        elif current_remote.stdout.strip() != remote_url:
            _run_git(repo_path, ["remote", "set-url", remote_name, remote_url])

        _run_git(repo_path, ["fetch", remote_name, "--prune"], check=False)
        _checkout_tracking_branch(
            repo_path,
            remote_name=remote_name,
            branch=default_branch,
        )
    else:
        current_branch = _run_git(
            repo_path,
            ["rev-parse", "--abbrev-ref", "HEAD"],
            check=False,
            text=True,
        )
        if current_branch.returncode != 0 or current_branch.stdout.strip() != default_branch:
            _run_git(repo_path, ["checkout", "-B", default_branch], check=False)

    _ensure_local_identity(repo_path)

    logger.debug("Initialized shadow repo at %s", repo_path)


def commit_snapshot(
    repo_path: Path,
    entity_type: str,
    snapshot_json: dict[str, Any],
    message: str,
    author: str = "shadow-system",
    filename: str | None = None,
    remote_url: str | None = None,
    remote_name: str = "origin",
    default_branch: str = "main",
) -> str:
    """Write snapshot to JSON file, commit, and return SHA.

    Args:
        repo_path: Path to the git repository.
        entity_type: Entity type (used as default filename).
        snapshot_json: The snapshot data to commit.
        message: Commit message.
        author: Author name for the commit.
        filename: Optional custom filename. Defaults to "{entity_type}.json".

    Returns:
        The commit SHA.

    Raises:
        CommitError: If the commit operation fails.
    """
    ensure_repo(
        repo_path,
        remote_url=remote_url,
        remote_name=remote_name,
        default_branch=default_branch,
    )

    resolved_filename = filename or f"{entity_type}.json"
    file_path = repo_path / resolved_filename
    file_path.write_text(json.dumps(snapshot_json, indent=2, default=str))

    try:
        # Stage the file
        _run_git(repo_path, ["add", resolved_filename])

        # Commit with author info
        commit_result = _run_git(
            repo_path,
            [
                "commit",
                "-m",
                message,
                "--author",
                f"{author} <{author}@shadow>",
            ],
            check=False,
            text=True,
        )
        if commit_result.returncode != 0:
            # Treat no-op commits as success and reuse current HEAD.
            if "nothing to commit" not in (commit_result.stdout + commit_result.stderr):
                raise CommitError(
                    "Failed to commit snapshot: "
                    f"{(commit_result.stderr or commit_result.stdout).strip()}"
                )

        # Get the commit SHA
        result = _run_git(repo_path, ["rev-parse", "HEAD"], text=True)
        sha = result.stdout.strip()

        if remote_url:
            _run_git(
                repo_path,
                ["push", remote_name, f"HEAD:{default_branch}"],
            )

        logger.debug("Committed snapshot to %s: %s", repo_path, sha[:8])
        return sha

    except subprocess.CalledProcessError as e:
        if isinstance(e.stderr, bytes):
            stderr = e.stderr.decode()
        else:
            stderr = e.stderr or str(e)
        raise CommitError(f"Failed to commit snapshot: {stderr}") from e


def commit_text_file(
    repo_path: Path,
    *,
    filename: str,
    content: str,
    message: str,
    author: str = "shadow-system",
    remote_url: str | None = None,
    remote_name: str = "origin",
    default_branch: str = "main",
) -> str:
    """Write a text file, commit it, and optionally push."""
    ensure_repo(
        repo_path,
        remote_url=remote_url,
        remote_name=remote_name,
        default_branch=default_branch,
    )

    file_path = repo_path / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content)

    try:
        _run_git(repo_path, ["add", filename])
        commit_result = _run_git(
            repo_path,
            [
                "commit",
                "-m",
                message,
                "--author",
                f"{author} <{author}@shadow>",
            ],
            check=False,
            text=True,
        )
        if commit_result.returncode != 0 and "nothing to commit" not in (
            commit_result.stdout + commit_result.stderr
        ):
            raise CommitError(
                "Failed to commit file: "
                f"{(commit_result.stderr or commit_result.stdout).strip()}"
            )

        sha = _run_git(repo_path, ["rev-parse", "HEAD"], text=True).stdout.strip()
        if remote_url:
            _run_git(repo_path, ["push", remote_name, f"HEAD:{default_branch}"])
        return sha
    except subprocess.CalledProcessError as e:
        if isinstance(e.stderr, bytes):
            stderr = e.stderr.decode()
        else:
            stderr = e.stderr or str(e)
        raise CommitError(f"Failed to commit file: {stderr}") from e


def read_snapshot(
    repo_path: Path,
    entity_type: str,
    commit_sha: str,
    remote_url: str | None = None,
    remote_name: str = "origin",
    default_branch: str = "main",
) -> dict[str, Any]:
    """Read snapshot at a specific commit.

    Args:
        repo_path: Path to the git repository.
        entity_type: Entity type (determines filename).
        commit_sha: The commit SHA to read from.

    Returns:
        The snapshot data as a dictionary.

    Raises:
        SnapshotNotFoundError: If the commit or file doesn't exist.
    """
    try:
        ensure_repo(
            repo_path,
            remote_url=remote_url,
            remote_name=remote_name,
            default_branch=default_branch,
        )
        result = subprocess.run(
            ["git", "show", f"{commit_sha}:{entity_type}.json"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)

    except subprocess.CalledProcessError as e:
        stderr = e.stderr if e.stderr else str(e)
        raise SnapshotNotFoundError(
            f"Cannot read snapshot at {commit_sha}: {stderr}"
        ) from e
    except json.JSONDecodeError as e:
        raise SnapshotNotFoundError(
            f"Invalid JSON in snapshot at {commit_sha}: {e}"
        ) from e


def get_latest_commit(repo_path: Path) -> str | None:
    """Get HEAD commit SHA, or None if no commits exist.

    Args:
        repo_path: Path to the git repository.

    Returns:
        The HEAD commit SHA, or None if the repo has no commits.
    """
    if not (repo_path / ".git").exists():
        return None

    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        # No commits yet (orphan branch)
        return None

    return result.stdout.strip()


def get_repo_path(base_path: Path, entity_type: str, entity_id: str) -> Path:
    """Compute the repository path for an entity.

    Args:
        base_path: Base path for all shadow repos (SHADOW_REPOS_PATH).
        entity_type: Entity type (e.g., "room", "agent").
        entity_id: Entity UUID as string.

    Returns:
        Path to the entity's git repository.
    """
    return base_path / entity_type / entity_id


def get_repo_remote_url(
    repo_url_template: str | None,
    entity_type: str,
    entity_id: str,
) -> str | None:
    """Build a repo URL from template if configured."""
    if not repo_url_template:
        return None
    return repo_url_template.format(entity_type=entity_type, entity_id=entity_id)
