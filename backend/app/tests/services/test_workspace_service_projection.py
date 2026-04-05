from __future__ import annotations

import uuid

from app.models import (
    Workspace,
    WorkspaceServiceKind,
    WorkspaceServiceStatus,
    WorkspaceStatus,
)
from app.services.workspace_service import (
    _fallback_service_summaries,
    _services_ready_for_workspace,
)


def test_fallback_service_summaries_marks_agent_runtime_unknown_when_ready_but_discovery_missing() -> None:
    workspace = Workspace(
        owner_id=uuid.uuid4(),
        name="agent-runtime",
        status=WorkspaceStatus.ready,
        meta={
            "declared_services": [
                {
                    "id": "codex",
                    "label": "Codex Runtime",
                    "kind": "agent_runtime",
                    "runtime_id": "codex",
                    "runtime_profile": "codex_app_server",
                    "transport_kind": "websocket",
                    "protocol": "ws",
                    "source": "bootstrap_profile",
                }
            ],
            "kennel_inject_request": {
                "bootstrap_profile": "codex_app_server",
            },
        },
    )

    services = _fallback_service_summaries(workspace)

    assert len(services) == 1
    assert services[0].kind == WorkspaceServiceKind.agent_runtime
    assert services[0].runtime_id == "codex"
    assert services[0].runtime_profile == "codex_app_server"
    assert services[0].transport_kind == "websocket"
    assert services[0].status == WorkspaceServiceStatus.unknown
    assert services[0].readiness_message == (
        "Agent runtime was declared, but live discovery is currently unavailable."
    )


def test_services_ready_prefers_agent_runtime_state_when_present() -> None:
    services = _fallback_service_summaries(
        Workspace(
            owner_id=uuid.uuid4(),
            name="mixed-runtime",
            status=WorkspaceStatus.starting,
            meta={
                "declared_services": [
                    {
                        "id": "vite",
                        "label": "Vite Dev Server",
                        "kind": "web_app",
                        "protocol": "http",
                        "port": 5173,
                        "path": "/",
                        "source": "bootstrap_profile",
                    },
                    {
                        "id": "codex",
                        "label": "Codex Runtime",
                        "kind": "agent_runtime",
                        "runtime_id": "codex",
                        "runtime_profile": "codex_app_server",
                        "transport_kind": "websocket",
                        "protocol": "ws",
                        "source": "bootstrap_profile",
                    },
                ]
            },
        )
    )

    assert _services_ready_for_workspace(services) is False

    services[1].status = WorkspaceServiceStatus.ready

    assert _services_ready_for_workspace(services) is True
