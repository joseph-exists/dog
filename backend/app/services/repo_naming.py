from __future__ import annotations

import re
import uuid


DEFAULT_SHADOW_ORG = "shadow"
DEFAULT_USER_REPOS_ORG = "dog"

_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
_DASH_TRIM_RE = re.compile(r"^-+|-+$")


def shadow_repo_name(entity_type: str, entity_id: uuid.UUID | str) -> str:
    """Return the deterministic shadow repo name for an entity."""
    return f"{entity_type}-{entity_id}"


def shadow_repo_full_name(
    entity_type: str,
    entity_id: uuid.UUID | str,
    *,
    org: str = DEFAULT_SHADOW_ORG,
) -> str:
    """Return the org-qualified shadow repo name."""
    return f"{org}/{shadow_repo_name(entity_type, entity_id)}"


def normalize_repo_slug(value: str) -> str:
    """Normalize a user-facing slug into a stable repo-safe slug."""
    normalized = _NON_ALNUM_RE.sub("-", value.strip().lower())
    normalized = _DASH_TRIM_RE.sub("", normalized)
    return normalized or "repo"


def short_id(value: uuid.UUID | str, *, length: int = 8) -> str:
    """Return a short stable identifier prefix."""
    return str(value).replace("-", "")[:length]


def user_repo_name(slug: str, repo_id: uuid.UUID | str) -> str:
    """Return the agreed dog-org user repo name format."""
    return f"{normalize_repo_slug(slug)}-{short_id(repo_id)}"


def user_repo_full_name(
    slug: str,
    repo_id: uuid.UUID | str,
    *,
    org: str = DEFAULT_USER_REPOS_ORG,
) -> str:
    """Return the org-qualified user-visible repo name."""
    return f"{org}/{user_repo_name(slug, repo_id)}"
