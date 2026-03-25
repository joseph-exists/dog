from __future__ import annotations

import uuid

import pytest

from app.models import (
    WorkspaceBootstrapIntent,
    WorkspaceBootstrapPhase,
    WorkspaceExternalUrlRepoSource,
    WorkspaceInstallIntentAuto,
    WorkspaceInstallIntentProfile,
    WorkspaceStartupIntentAgentService,
    WorkspaceStartupIntentProfile,
    WorkspaceUserRepoSource,
)
from app.services.workspace_bootstrap_service import (
    AGENT_SERVICE_PROFILES,
    WorkspaceBootstrapValidationError,
    generate_bootstrap_plan,
)


def test_generate_bootstrap_plan_builds_clone_install_and_start_steps() -> None:
    intent = WorkspaceBootstrapIntent(
        repo_source=WorkspaceExternalUrlRepoSource(
            repo_url="https://github.com/example/app.git",
            ref="main",
        ),
        install_intent=WorkspaceInstallIntentAuto(),
        startup_intent=WorkspaceStartupIntentProfile(profile="vite"),
        env_vars={"API_BASE_URL": "http://localhost:8000"},
        ssh_pubkey="ssh-ed25519 AAAA test@example",
    )

    plan = generate_bootstrap_plan(
        intent,
        materialized_repo_url="https://github.com/example/app.git",
    )

    assert plan.workspace_path == "/home/dev/workspace"
    assert [step.type for step in plan.steps] == [
        "add_ssh_key",
        "write_env_vars",
        "clone_repo",
        "run_command",
        "run_command",
    ]
    assert plan.steps[2].phase == WorkspaceBootstrapPhase.materializing_repo
    assert plan.steps[2].ref == "main"
    assert plan.steps[3].phase == WorkspaceBootstrapPhase.installing_dependencies
    assert plan.steps[4].phase == WorkspaceBootstrapPhase.starting_services
    assert plan.steps[4].background is True


def test_generate_bootstrap_plan_uses_repo_source_ref_for_user_repo() -> None:
    repo_id = uuid.uuid4()
    intent = WorkspaceBootstrapIntent(
        repo_source=WorkspaceUserRepoSource(repo_id=repo_id, ref="feature/demo"),
    )

    plan = generate_bootstrap_plan(
        intent,
        materialized_repo_url="ssh://git@example.com/dog/repo.git",
    )

    assert len(plan.steps) == 1
    assert plan.steps[0].type == "clone_repo"
    assert plan.steps[0].ref == "feature/demo"


def test_generate_bootstrap_plan_rejects_unknown_install_profile() -> None:
    intent = WorkspaceBootstrapIntent(
        install_intent=WorkspaceInstallIntentProfile(profile="ruby"),
    )

    with pytest.raises(WorkspaceBootstrapValidationError) as exc_info:
        generate_bootstrap_plan(intent, materialized_repo_url=None)

    assert exc_info.value.error_code == "WORKSPACE_INSTALL_PROFILE_UNSUPPORTED"


@pytest.mark.parametrize(
    ("agent_profile", "service_name"),
    [
        ("codex", "codex"),
        ("claude_code", "claude_code"),
        ("hermes", "hermes"),
    ],
)
def test_generate_bootstrap_plan_supports_known_agent_service_profiles(
    agent_profile: str,
    service_name: str,
) -> None:
    intent = WorkspaceBootstrapIntent(
        startup_intent=WorkspaceStartupIntentAgentService(agent_profile=agent_profile),
    )

    plan = generate_bootstrap_plan(intent, materialized_repo_url=None)

    assert len(plan.steps) == 1
    assert plan.steps[0].type == "run_command"
    assert plan.steps[0].phase == WorkspaceBootstrapPhase.starting_services
    assert plan.steps[0].background is True
    assert plan.steps[0].service_name == service_name
    assert AGENT_SERVICE_PROFILES[agent_profile].command_env_var in plan.steps[0].command


def test_generate_bootstrap_plan_rejects_unknown_agent_service_profile() -> None:
    intent = WorkspaceBootstrapIntent(
        startup_intent=WorkspaceStartupIntentAgentService(agent_profile="default"),
    )

    with pytest.raises(WorkspaceBootstrapValidationError) as exc_info:
        generate_bootstrap_plan(intent, materialized_repo_url=None)

    assert exc_info.value.error_code == "WORKSPACE_AGENT_PROFILE_UNSUPPORTED"
