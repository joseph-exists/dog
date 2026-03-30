from __future__ import annotations

from app.models import (
    WorkspaceBootstrapIntent,
    WorkspaceStartupIntentAgentService,
    WorkspaceStartupIntentProfile,
)
from app.services.workspace_bootstrap_service import WorkspaceBootstrapPlan
from app.services.workspace_service import (
    _kennel_runtime_preset_from_bootstrap_intent,
    _resolve_kennel_runtime_preset,
    build_workspace_kennel_provisioning_request,
)


def test_kennel_runtime_preset_is_inferred_for_supported_agent_profile() -> None:
    intent = WorkspaceBootstrapIntent(
        startup_intent=WorkspaceStartupIntentAgentService(agent_profile="codex"),
    )

    runtime_preset = _kennel_runtime_preset_from_bootstrap_intent(intent)

    assert runtime_preset == "codex"


def test_kennel_runtime_preset_is_not_inferred_for_agent_profile_without_preset() -> None:
    intent = WorkspaceBootstrapIntent(
        startup_intent=WorkspaceStartupIntentAgentService(agent_profile="hermes"),
    )

    runtime_preset = _kennel_runtime_preset_from_bootstrap_intent(intent)

    assert runtime_preset is None


def test_kennel_runtime_preset_is_not_inferred_for_non_agent_startup() -> None:
    intent = WorkspaceBootstrapIntent(
        startup_intent=WorkspaceStartupIntentProfile(profile="vite"),
    )

    runtime_preset = _kennel_runtime_preset_from_bootstrap_intent(intent)

    assert runtime_preset is None


def test_explicit_runtime_preset_wins_over_inferred_runtime_preset() -> None:
    runtime_preset = _resolve_kennel_runtime_preset(
        explicit_runtime_preset="claude_code",
        bootstrap_intent=WorkspaceBootstrapIntent(
            startup_intent=WorkspaceStartupIntentAgentService(agent_profile="codex"),
        ),
    )

    assert runtime_preset == "claude_code"


def test_build_workspace_kennel_provisioning_request_keeps_explicit_flavour_and_adds_runtime_preset() -> None:
    request = build_workspace_kennel_provisioning_request(
        kennel_name="env-1234abcd",
        workspace_kind="ephemeral",
        workspace_flavour="cuda",
        explicit_runtime_preset=None,
        bootstrap_intent=WorkspaceBootstrapIntent(
            startup_intent=WorkspaceStartupIntentAgentService(agent_profile="codex"),
        ),
        resolved_repo_url="https://github.com/example/app.git",
        bootstrap_plan=WorkspaceBootstrapPlan(),
    )

    assert request.create.as_payload() == {
        "name": "env-1234abcd",
        "kind": "ephemeral",
        "flavour": "cuda",
        "runtime_preset": "codex",
    }


def test_build_workspace_kennel_provisioning_request_supports_mixed_mode_assets_plus_explicit_plan() -> None:
    bootstrap_plan = WorkspaceBootstrapPlan()
    request = build_workspace_kennel_provisioning_request(
        kennel_name="env-1234abcd",
        workspace_kind="ephemeral",
        workspace_flavour="dev",
        explicit_runtime_preset=None,
        bootstrap_intent=WorkspaceBootstrapIntent(
            startup_intent=WorkspaceStartupIntentAgentService(agent_profile="claude_code"),
        ),
        resolved_repo_url="https://github.com/example/app.git",
        bootstrap_plan=bootstrap_plan,
        explicit_env_vars={"WORKSPACE_NAME": "app"},
        projected_env_vars={"DOG_PLATFORM_SERVICE_COUNT": "2"},
        projected_runtime_files={
            "/home/dev/.dog/platform-services/agent-runtime.json": '{"services":[]}'
        },
    )

    assert request.inject.user == "dev"
    assert request.inject.repo_url == "https://github.com/example/app.git"
    assert request.inject.runtime_preset == "claude_code"
    assert request.inject.bootstrap_plan == bootstrap_plan
    assert request.inject.env_vars == {
        "DOG_PLATFORM_SERVICE_COUNT": "2",
        "WORKSPACE_NAME": "app",
    }
    assert request.inject.runtime_files == {
        "/home/dev/.dog/platform-services/agent-runtime.json": '{"services":[]}'
    }


def test_build_workspace_kennel_provisioning_request_explicit_env_vars_override_projected_values() -> None:
    request = build_workspace_kennel_provisioning_request(
        kennel_name="env-1234abcd",
        workspace_kind="ephemeral",
        workspace_flavour="dev",
        explicit_runtime_preset=None,
        bootstrap_intent=WorkspaceBootstrapIntent(),
        resolved_repo_url=None,
        bootstrap_plan=WorkspaceBootstrapPlan(),
        explicit_env_vars={"DOG_PLATFORM_SERVICE_COUNT": "9", "USER_SETTING": "enabled"},
        projected_env_vars={"DOG_PLATFORM_SERVICE_COUNT": "2", "DOG_PLATFORM_SERVICES_PATH": "/tmp/x"},
    )

    assert request.inject.env_vars == {
        "DOG_PLATFORM_SERVICE_COUNT": "9",
        "DOG_PLATFORM_SERVICES_PATH": "/tmp/x",
        "USER_SETTING": "enabled",
    }


def test_build_workspace_kennel_provisioning_request_uses_explicit_runtime_preset() -> None:
    request = build_workspace_kennel_provisioning_request(
        kennel_name="env-1234abcd",
        workspace_kind="ephemeral",
        workspace_flavour="dev",
        explicit_runtime_preset="claude_code",
        bootstrap_intent=WorkspaceBootstrapIntent(
            startup_intent=WorkspaceStartupIntentAgentService(agent_profile="codex"),
        ),
        resolved_repo_url=None,
        bootstrap_plan=WorkspaceBootstrapPlan(),
    )

    assert request.create.runtime_preset == "claude_code"
    assert request.inject.runtime_preset == "claude_code"
