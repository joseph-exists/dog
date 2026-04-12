from __future__ import annotations

from datetime import datetime, timezone
import uuid

from app.models import (
    UserRepo,
    UserRepoImportStatus,
    WorkspaceBootstrapIntent,
    WorkspaceStartupIntentAgentService,
    WorkspaceStartupIntentProfile,
)
from app.services.workspace_bootstrap_service import WorkspaceBootstrapPlan
from app.services.workspace_service import (
    _materialized_user_repo_clone_url,
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


def test_kennel_runtime_preset_is_inferred_for_hermes_agent_profile() -> None:
    intent = WorkspaceBootstrapIntent(
        startup_intent=WorkspaceStartupIntentAgentService(agent_profile="hermes"),
    )

    runtime_preset = _kennel_runtime_preset_from_bootstrap_intent(intent)

    assert runtime_preset == "hermes"


def test_kennel_runtime_preset_is_not_inferred_for_non_agent_startup() -> None:
    intent = WorkspaceBootstrapIntent(
        startup_intent=WorkspaceStartupIntentProfile(profile="vite"),
    )

    runtime_preset = _kennel_runtime_preset_from_bootstrap_intent(intent)

    assert runtime_preset is None


def test_kennel_runtime_preset_is_not_inferred_for_unknown_agent_profile() -> None:
    intent = WorkspaceBootstrapIntent(
        startup_intent=WorkspaceStartupIntentAgentService(agent_profile="custom_agent"),
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
    assert request.inject.bootstrap_plan is None


def test_build_workspace_kennel_provisioning_request_delegates_codex_agent_startup_to_kennel() -> None:
    bootstrap_plan = WorkspaceBootstrapPlan(
        steps=[
            {
                "type": "run_command",
                "phase": "starting_services",
                "label": "Start Codex Runtime",
                "command": "codex",
                "cwd": "/home/dev/workspace",
                "background": True,
                "service_name": "codex",
            }
        ]
    )
    request = build_workspace_kennel_provisioning_request(
        kennel_name="env-1234abcd",
        workspace_kind="persistent",
        workspace_flavour="dev",
        explicit_runtime_preset=None,
        bootstrap_intent=WorkspaceBootstrapIntent(
            startup_intent=WorkspaceStartupIntentAgentService(agent_profile="codex"),
        ),
        resolved_repo_url=None,
        bootstrap_plan=bootstrap_plan,
        projected_env_vars={"DOG_PLATFORM_SERVICE_COUNT": "2"},
        projected_runtime_files={
            "/home/dev/.dog/platform-services/agent-runtime.json": '{"services":[]}'
        },
    )

    assert request.inject.runtime_preset == "codex"
    assert request.inject.bootstrap_profile is None
    assert request.inject.bootstrap_plan is None
    assert request.inject.env_vars == {"DOG_PLATFORM_SERVICE_COUNT": "2"}
    assert request.inject.runtime_files == {
        "/home/dev/.dog/platform-services/agent-runtime.json": '{"services":[]}'
    }


def test_build_workspace_kennel_provisioning_request_delegates_hermes_agent_startup_to_kennel() -> None:
    bootstrap_plan = WorkspaceBootstrapPlan(
        steps=[
            {
                "type": "run_command",
                "phase": "starting_services",
                "label": "Start Hermes Runtime",
                "command": "hermes",
                "cwd": "/home/dev/workspace",
                "background": True,
                "service_name": "hermes",
            }
        ]
    )
    request = build_workspace_kennel_provisioning_request(
        kennel_name="env-1234abcd",
        workspace_kind="persistent",
        workspace_flavour="dev",
        explicit_runtime_preset=None,
        bootstrap_intent=WorkspaceBootstrapIntent(
            startup_intent=WorkspaceStartupIntentAgentService(agent_profile="hermes"),
        ),
        resolved_repo_url=None,
        bootstrap_plan=bootstrap_plan,
        projected_env_vars={"DOG_PLATFORM_SERVICE_COUNT": "2"},
    )

    assert request.inject.runtime_preset == "hermes"
    assert request.inject.bootstrap_profile == "hermes_api_server"
    assert request.inject.bootstrap_plan is None
    assert request.inject.env_vars == {"DOG_PLATFORM_SERVICE_COUNT": "2"}


def test_build_workspace_kennel_provisioning_request_normalizes_hermes_flavour_to_dev() -> None:
    request = build_workspace_kennel_provisioning_request(
        kennel_name="env-1234abcd",
        workspace_kind="persistent",
        workspace_flavour="cuda",
        explicit_runtime_preset=None,
        bootstrap_intent=WorkspaceBootstrapIntent(
            startup_intent=WorkspaceStartupIntentAgentService(agent_profile="hermes"),
        ),
        resolved_repo_url=None,
        bootstrap_plan=WorkspaceBootstrapPlan(),
    )

    assert request.create.flavour == "dev"
    assert request.create.runtime_preset == "hermes"


def test_build_workspace_kennel_provisioning_request_supports_mixed_mode_assets_plus_explicit_plan() -> None:
    bootstrap_plan = WorkspaceBootstrapPlan()
    request = build_workspace_kennel_provisioning_request(
        kennel_name="env-1234abcd",
        workspace_kind="ephemeral",
        workspace_flavour="dev",
        explicit_runtime_preset=None,
        bootstrap_intent=WorkspaceBootstrapIntent(
            startup_intent=WorkspaceStartupIntentAgentService(agent_profile="claude_code"),
            bootstrap_profile="claude_code_remote_control",
        ),
        resolved_repo_url="https://github.com/example/app.git",
        bootstrap_plan=bootstrap_plan,
        explicit_bootstrap_profile="claude_code_remote_control",
        explicit_env_vars={"WORKSPACE_NAME": "app"},
        explicit_runtime_files={"/home/dev/.claude/settings.json": '{"env":{"A":"1"}}'},
        projected_env_vars={"DOG_PLATFORM_SERVICE_COUNT": "2"},
        projected_runtime_files={
            "/home/dev/.dog/platform-services/agent-runtime.json": '{"services":[]}'
        },
    )

    assert request.inject.user == "dev"
    assert request.inject.repo_url == "https://github.com/example/app.git"
    assert request.inject.runtime_preset == "claude_code"
    assert request.inject.bootstrap_profile == "claude_code_remote_control"
    assert request.inject.bootstrap_plan == bootstrap_plan
    assert request.inject.env_vars == {
        "DOG_PLATFORM_SERVICE_COUNT": "2",
        "WORKSPACE_NAME": "app",
    }
    assert request.inject.runtime_files == {
        "/home/dev/.claude/settings.json": '{"env":{"A":"1"}}',
        "/home/dev/.dog/platform-services/agent-runtime.json": '{"services":[]}'
    }


def test_build_workspace_kennel_provisioning_request_preserves_explicit_codex_bootstrap_override() -> None:
    bootstrap_plan = WorkspaceBootstrapPlan()
    request = build_workspace_kennel_provisioning_request(
        kennel_name="env-1234abcd",
        workspace_kind="ephemeral",
        workspace_flavour="dev",
        explicit_runtime_preset=None,
        bootstrap_intent=WorkspaceBootstrapIntent(
            startup_intent=WorkspaceStartupIntentAgentService(agent_profile="codex"),
            bootstrap_profile="codex_app_server",
        ),
        resolved_repo_url=None,
        bootstrap_plan=bootstrap_plan,
        explicit_bootstrap_profile="codex_app_server",
    )

    assert request.inject.runtime_preset == "codex"
    assert request.inject.bootstrap_profile == "codex_app_server"
    assert request.inject.bootstrap_plan == bootstrap_plan


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
    bootstrap_plan = WorkspaceBootstrapPlan()
    request = build_workspace_kennel_provisioning_request(
        kennel_name="env-1234abcd",
        workspace_kind="ephemeral",
        workspace_flavour="dev",
        explicit_runtime_preset="claude_code",
        bootstrap_intent=WorkspaceBootstrapIntent(
            startup_intent=WorkspaceStartupIntentAgentService(agent_profile="codex"),
        ),
        resolved_repo_url=None,
        bootstrap_plan=bootstrap_plan,
    )

    assert request.create.runtime_preset == "claude_code"
    assert request.inject.runtime_preset == "claude_code"
    assert request.inject.bootstrap_plan == bootstrap_plan


def test_build_workspace_kennel_provisioning_request_explicit_runtime_files_override_projected_values() -> None:
    request = build_workspace_kennel_provisioning_request(
        kennel_name="env-1234abcd",
        workspace_kind="ephemeral",
        workspace_flavour="dev",
        explicit_runtime_preset=None,
        bootstrap_intent=WorkspaceBootstrapIntent(
            runtime_files={"/home/dev/.dog/platform-services/agent-runtime.json": '{"services":["explicit"]}'}
        ),
        resolved_repo_url=None,
        bootstrap_plan=WorkspaceBootstrapPlan(),
        explicit_runtime_files={
            "/home/dev/.dog/platform-services/agent-runtime.json": '{"services":["explicit"]}'
        },
        projected_runtime_files={
            "/home/dev/.dog/platform-services/agent-runtime.json": '{"services":["projected"]}'
        },
    )

    assert request.inject.runtime_files == {
        "/home/dev/.dog/platform-services/agent-runtime.json": '{"services":["explicit"]}'
    }


def test_materialized_user_repo_clone_url_prefers_repo_html_url_for_workspace_clone(
    monkeypatch,
) -> None:
    repo = UserRepo(
        id=uuid.uuid4(),
        owner_user_id=uuid.uuid4(),
        slug="svg3d",
        display_name="svg3d",
        source_repo_url="https://github.com/prideout/svg3d/",
        source_branch="main",
        import_status=UserRepoImportStatus.READY,
        imported_at=datetime.now(timezone.utc),
        gogs_repo_name="svg3d-12345678",
        gogs_repo_id=123,
        gogs_full_name="dog/svg3d-12345678",
        gogs_html_url="http://localhost:3001/dog/svg3d-12345678",
        is_private=False,
    )

    monkeypatch.setattr(
        "app.services.user_repo_service.settings.USER_REPO_GOGS_BASE_URL",
        "http://gittin:3000",
    )
    monkeypatch.setattr(
        "app.services.workspace_service.settings.USER_REPO_WORKSPACE_CLONE_BASE_URL",
        None,
    )

    materialized_url = _materialized_user_repo_clone_url(repo)

    assert materialized_url == "http://localhost:3001/dog/svg3d-12345678.git"


def test_materialized_user_repo_clone_url_prefers_explicit_workspace_clone_base_url(
    monkeypatch,
) -> None:
    repo = UserRepo(
        id=uuid.uuid4(),
        owner_user_id=uuid.uuid4(),
        slug="svg3d",
        display_name="svg3d",
        source_repo_url="https://github.com/prideout/svg3d/",
        source_branch="main",
        import_status=UserRepoImportStatus.READY,
        imported_at=datetime.now(timezone.utc),
        gogs_repo_name="svg3d-12345678",
        gogs_repo_id=123,
        gogs_full_name="dog/svg3d-12345678",
        gogs_html_url="http://localhost:3001/dog/svg3d-12345678",
        is_private=False,
    )

    monkeypatch.setattr(
        "app.services.workspace_service.settings.USER_REPO_WORKSPACE_CLONE_BASE_URL",
        "https://git.example.test",
    )

    materialized_url = _materialized_user_repo_clone_url(repo)

    assert materialized_url == "https://git.example.test/dog/svg3d-12345678.git"


def test_materialized_user_repo_clone_url_falls_back_to_internal_gittin_remote_without_html_url(
    monkeypatch,
) -> None:
    repo = UserRepo(
        id=uuid.uuid4(),
        owner_user_id=uuid.uuid4(),
        slug="svg3d",
        display_name="svg3d",
        source_repo_url="https://github.com/prideout/svg3d/",
        source_branch="main",
        import_status=UserRepoImportStatus.READY,
        imported_at=datetime.now(timezone.utc),
        gogs_repo_name="svg3d-12345678",
        gogs_repo_id=123,
        gogs_full_name="dog/svg3d-12345678",
        gogs_html_url=None,
        is_private=False,
    )

    monkeypatch.setattr(
        "app.services.user_repo_service.settings.USER_REPO_GOGS_BASE_URL",
        "http://gittin:3000",
    )
    monkeypatch.setattr(
        "app.services.workspace_service.settings.USER_REPO_WORKSPACE_CLONE_BASE_URL",
        None,
    )

    materialized_url = _materialized_user_repo_clone_url(repo)

    assert materialized_url == "http://gittin:3000/dog/svg3d-12345678.git"
