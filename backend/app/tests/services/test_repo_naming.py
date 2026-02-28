from __future__ import annotations

import uuid

from app.services.repo_naming import (
    normalize_repo_slug,
    shadow_repo_full_name,
    shadow_repo_name,
    short_id,
    user_repo_full_name,
    user_repo_name,
)


def test_shadow_repo_name_uses_full_uuid() -> None:
    entity_id = uuid.UUID("38c2f6cb-bce2-4e0e-b91e-19c9eec82a8a")
    assert shadow_repo_name("agent", entity_id) == (
        "agent-38c2f6cb-bce2-4e0e-b91e-19c9eec82a8a"
    )


def test_shadow_repo_full_name_uses_shadow_org() -> None:
    entity_id = uuid.UUID("3e26d320-732b-437b-b875-e03880364fe8")
    assert shadow_repo_full_name("story", entity_id) == (
        "shadow/story-3e26d320-732b-437b-b875-e03880364fe8"
    )


def test_normalize_repo_slug() -> None:
    assert normalize_repo_slug("  My Demo Repo!  ") == "my-demo-repo"
    assert normalize_repo_slug("___") == "repo"


def test_short_id_removes_hyphens() -> None:
    assert short_id("550e8400-e29b-41d4-a716-446655440000") == "550e8400"


def test_user_repo_name_uses_slug_and_short_id() -> None:
    repo_id = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
    assert user_repo_name("My Demo Repo", repo_id) == "my-demo-repo-550e8400"


def test_user_repo_full_name_uses_dog_org() -> None:
    repo_id = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
    assert user_repo_full_name("Launch Plan", repo_id) == "dog/launch-plan-550e8400"
