"""shadow_git.py - Local git operations for shadow versioning.

Thin wrapper around git subprocess calls. Each entity gets its own
git repository at {SHADOW_REPOS_PATH}/{entity_type}/{entity_id}/.

This replaces the previous Forgejo HTTP API approach with direct
local git operations for simplicity and performance.
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


def ensure_repo(repo_path: Path) -> None:
    """Initialize git repo if it doesn't exist.

    Creates the directory structure and initializes a git repository
    with proper configuration for automated commits.

    Args:
        repo_path: Path where the git repo should exist.
    """
    if (repo_path / ".git").exists():
        return

    repo_path.mkdir(parents=True, exist_ok=True)

    # Initialize repo
    subprocess.run(
        ["git", "init"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    # Configure git identity for this repo (required for commits)
    # Using repo-local config so it doesn't affect system/global settings
    subprocess.run(
        ["git", "config", "user.name", "shadow-system"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "shadow@localhost"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    logger.debug("Initialized shadow repo at %s", repo_path)


def commit_snapshot(
    repo_path: Path,
    entity_type: str,
    snapshot_json: dict[str, Any],
    message: str,
    author: str = "shadow-system",
    filename: str | None = None,
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
    ensure_repo(repo_path)

    resolved_filename = filename or f"{entity_type}.json"
    file_path = repo_path / resolved_filename
    file_path.write_text(json.dumps(snapshot_json, indent=2, default=str))

    try:
        # Stage the file
        subprocess.run(
            ["git", "add", resolved_filename],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # Commit with author info
        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                message,
                "--author",
                f"{author} <{author}@shadow>",
            ],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # Get the commit SHA
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        sha = result.stdout.strip()
        logger.debug("Committed snapshot to %s: %s", repo_path, sha[:8])
        return sha

    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode() if e.stderr else str(e)
        raise CommitError(f"Failed to commit snapshot: {stderr}") from e


def read_snapshot(
    repo_path: Path,
    entity_type: str,
    commit_sha: str,
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
