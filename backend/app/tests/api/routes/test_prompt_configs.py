from fastapi.testclient import TestClient

from app.core.config import settings


def _draft_payload(*, model_id: str = "gpt-4o-mini", text: str = "Hello") -> dict:
    return {
        "provider": {
            "user_access_provider_id": None,
            "provider_type_id": None,
            "provider_kind": "openai_compatible",
            "base_url": "https://api.example.test/v1",
            "account_label": "test-provider",
        },
        "model": {
            "model_catalog_id": None,
            "model_id": model_id,
            "model_name": model_id,
            "model_family": "gpt-4o",
        },
        "input": {
            "kind": "simple_text",
            "text": text,
            "system": "You are a helpful assistant.",
            "messages": [],
        },
        "params": {
            "provider_kind": "openai_compatible",
            "temperature": 0.2,
            "top_p": 1,
            "max_output_tokens": 256,
            "response_format": {"type": "text"},
            "response_format_json": False,
            "openai": {"previous_response_id": None, "reasoning": {"summary": "auto"}},
            "parallel_tool_calls": True,
        },
        "tools": {
            "tool_mode": "none",
            "tool_allowlist": [],
            "tool_choice": None,
            "max_tool_calls": None,
            "builtin": [],
            "mcp": {"servers": [], "allowed_tools": []},
        },
        "metadata": {
            "tags": ["test"],
            "notes": "integration test payload",
            "template_id": "prompt-builder-m1-test",
            "template_setup": {"ready": True},
        },
    }


def _create_prompt_config(
    client: TestClient,
    token_headers: dict[str, str],
    *,
    name: str = "Prompt Config Test",
    slug: str | None = None,
) -> dict:
    response = client.post(
        f"{settings.API_V1_STR}/prompt-configs/",
        headers=token_headers,
        json={
            "slug": slug,
            "name": name,
            "description": "Prompt config integration test",
            "payload": _draft_payload(),
            "metadata_json": {"source": "tests"},
            "commit_message": "Initial version",
        },
    )
    assert response.status_code == 200
    return response.json()


def test_prompt_config_owner_access_controls(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    normal_user_token_headers: dict[str, str],
) -> None:
    created = _create_prompt_config(client, superuser_token_headers, name="Owner Access")
    prompt_config_id = created["id"]

    # Owner (superuser creator) can access.
    owner_response = client.get(
        f"{settings.API_V1_STR}/prompt-configs/{prompt_config_id}",
        headers=superuser_token_headers,
    )
    assert owner_response.status_code == 200

    # Another non-superuser account is denied.
    denied_response = client.get(
        f"{settings.API_V1_STR}/prompt-configs/{prompt_config_id}",
        headers=normal_user_token_headers,
    )
    assert denied_response.status_code == 403
    assert denied_response.json()["detail"] == "Access denied"


def test_prompt_config_create_generates_and_returns_slug(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    created = _create_prompt_config(
        client,
        superuser_token_headers,
        name="Slug Flow",
        slug=None,
    )
    assert isinstance(created["slug"], str)
    assert created["slug"]


def test_prompt_config_can_be_read_by_slug(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    created = _create_prompt_config(
        client,
        superuser_token_headers,
        name="Read By Slug",
        slug="prompt-read-by-slug",
    )
    response = client.get(
        f"{settings.API_V1_STR}/prompt-configs/slug/{created['slug']}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]
    assert response.json()["slug"] == "prompt-read-by-slug"


def test_prompt_config_slug_must_be_unique(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    _create_prompt_config(
        client,
        superuser_token_headers,
        name="Slug A",
        slug="prompt-unique-slug",
    )
    duplicate = client.post(
        f"{settings.API_V1_STR}/prompt-configs/",
        headers=superuser_token_headers,
        json={
            "slug": "prompt-unique-slug",
            "name": "Slug B",
            "description": "Prompt config integration test",
            "payload": _draft_payload(),
            "metadata_json": {"source": "tests"},
            "commit_message": "Initial version",
        },
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "PromptConfig slug already exists"


def test_prompt_config_commit_creates_next_version_and_resets_working_copy(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    created = _create_prompt_config(client, superuser_token_headers, name="Commit Flow")
    prompt_config_id = created["id"]

    # Update working copy so we have uncommitted changes before commit.
    put_response = client.put(
        f"{settings.API_V1_STR}/prompt-configs/{prompt_config_id}/working-copy",
        headers=superuser_token_headers,
        json={
            "base_version": 1,
            "has_uncommitted_changes": True,
            "payload": _draft_payload(model_id="gpt-4.1-mini", text="Updated draft"),
        },
    )
    assert put_response.status_code == 200
    updated_working_copy = put_response.json()
    assert updated_working_copy["base_version"] == 1
    assert updated_working_copy["has_uncommitted_changes"] is True
    assert updated_working_copy["payload"]["model"]["model_id"] == "gpt-4.1-mini"

    # Commit a new immutable version.
    commit_response = client.post(
        f"{settings.API_V1_STR}/prompt-configs/{prompt_config_id}/versions",
        headers=superuser_token_headers,
        json={"commit_message": "Add updated prompt settings"},
    )
    assert commit_response.status_code == 200
    committed_version = commit_response.json()
    assert committed_version["version_number"] == 2
    assert committed_version["commit_message"] == "Add updated prompt settings"
    assert committed_version["payload"]["model"]["model_id"] == "gpt-4.1-mini"

    # PromptConfig latest_version advances.
    config_response = client.get(
        f"{settings.API_V1_STR}/prompt-configs/{prompt_config_id}",
        headers=superuser_token_headers,
    )
    assert config_response.status_code == 200
    assert config_response.json()["latest_version"] == 2

    # Working copy is rebased and marked clean after commit.
    working_copy_response = client.get(
        f"{settings.API_V1_STR}/prompt-configs/{prompt_config_id}/working-copy",
        headers=superuser_token_headers,
    )
    assert working_copy_response.status_code == 200
    committed_working_copy = working_copy_response.json()
    assert committed_working_copy["base_version"] == 2
    assert committed_working_copy["has_uncommitted_changes"] is False


def test_prompt_config_working_copy_conflict_returns_409(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    created = _create_prompt_config(client, superuser_token_headers, name="Conflict Flow")
    prompt_config_id = created["id"]

    # Read current base_version so the first write is always against the live value.
    current_working_copy = client.get(
        f"{settings.API_V1_STR}/prompt-configs/{prompt_config_id}/working-copy",
        headers=superuser_token_headers,
    )
    assert current_working_copy.status_code == 200
    current_base_version = current_working_copy.json()["base_version"]

    # First write succeeds with matching base_version.
    first_update = client.put(
        f"{settings.API_V1_STR}/prompt-configs/{prompt_config_id}/working-copy",
        headers=superuser_token_headers,
        json={
            "base_version": current_base_version,
            "has_uncommitted_changes": True,
            "payload": _draft_payload(text="first writer"),
        },
    )
    assert first_update.status_code == 200
    assert first_update.json()["base_version"] == current_base_version

    # Stale write with outdated base_version should be rejected.
    conflict_update = client.put(
        f"{settings.API_V1_STR}/prompt-configs/{prompt_config_id}/working-copy",
        headers=superuser_token_headers,
        json={
            "base_version": max(current_base_version - 1, 0),
            "has_uncommitted_changes": True,
            "payload": _draft_payload(text="stale writer"),
        },
    )
    assert conflict_update.status_code == 409
    assert "base_version conflict" in conflict_update.json()["detail"]


def test_delete_prompt_config_removes_working_copy_and_versions(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    created = _create_prompt_config(client, superuser_token_headers, name="Delete Flow")
    prompt_config_id = created["id"]

    commit_response = client.post(
        f"{settings.API_V1_STR}/prompt-configs/{prompt_config_id}/versions",
        headers=superuser_token_headers,
        json={"commit_message": "Second version before delete"},
    )
    assert commit_response.status_code == 200

    delete_response = client.delete(
        f"{settings.API_V1_STR}/prompt-configs/{prompt_config_id}",
        headers=superuser_token_headers,
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "PromptConfig deleted"

    get_deleted = client.get(
        f"{settings.API_V1_STR}/prompt-configs/{prompt_config_id}",
        headers=superuser_token_headers,
    )
    assert get_deleted.status_code == 404

    get_deleted_working_copy = client.get(
        f"{settings.API_V1_STR}/prompt-configs/{prompt_config_id}/working-copy",
        headers=superuser_token_headers,
    )
    assert get_deleted_working_copy.status_code == 404

    list_deleted_versions = client.get(
        f"{settings.API_V1_STR}/prompt-configs/{prompt_config_id}/versions",
        headers=superuser_token_headers,
    )
    assert list_deleted_versions.status_code == 404


def test_prompt_config_validate_normalizes_legacy_and_new_fields(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    payload = _draft_payload()
    payload["params"]["response_format_json"] = True
    payload["params"]["response_format"] = None
    payload["tools"]["tool_choice"] = "dispatch_to_math"
    payload["tools"]["max_tool_calls"] = 3
    payload["tools"]["mcp"] = {
        "servers": [
            {
                "id": "docs-server",
                "url": "https://mcp.example.test",
                "allowed_tools": ["search_docs"],
                "require_approval": "never",
            }
        ]
    }

    response = client.post(
        f"{settings.API_V1_STR}/prompt-configs/validate",
        headers=superuser_token_headers,
        json=payload,
    )
    assert response.status_code == 200
    assert isinstance(response.json()["issues"], list)


def test_prompt_config_resolve_preview_returns_effective_config(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/prompt-configs/resolve-preview",
        headers=superuser_token_headers,
        json={
            "agent_slug": "missing-agent-slug",
            "room_id": None,
            "payload": _draft_payload(model_id="gpt-4.1-mini"),
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Agent not found"
