from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AgentRunRequest:
    room_id: uuid.UUID
    agent_slug: str
    trigger_message: str
    user_id: uuid.UUID | None = None
    a2a_depth: int = 0
    enable_a2a_tool: bool = False
    enable_ag_ui_tool: bool = False
    enable_workspace_runtime_tool: bool = False


@dataclass(frozen=True)
class AgentRunResult:
    agent_name: str
    content: str
    success: bool
    error: str | None = None
    a2a_triggered: list[str] | None = None
    ui_components: list[dict[str, Any]] | None = None
