from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.core.config import settings

ApprovalMode = Literal["always", "never"]
TransportType = Literal["streamable_http", "http", "sse", "stdio"]


@dataclass(frozen=True)
class MCPServerDescriptor:
    id: str
    transport: TransportType
    url: str
    enabled: bool = True
    require_approval_default: ApprovalMode = "never"
    scopes: tuple[str, ...] = ("system", "personal")
    tags: tuple[str, ...] = ()
    description: str | None = None


def _base_url() -> str:
    return settings.MCPMVP_BASE_URL.rstrip("/")


def build_mcp_server_registry() -> dict[str, MCPServerDescriptor]:
    base_url = _base_url()
    registry = {
        "affordance": MCPServerDescriptor(
            id="affordance",
            transport="streamable_http",
            url=f"{base_url}/mcp/affordance",
            enabled=settings.MCPMVP_AFFORDANCE_ENABLED,
            require_approval_default="never",
            tags=("introspection", "demo-builder"),
            description="Affordance introspection tools for demo-builder composition planning.",
        ),
        "story": MCPServerDescriptor(
            id="story",
            transport="streamable_http",
            url=f"{base_url}/mcp/story",
            enabled=settings.MCPMVP_STORY_ENABLED,
            require_approval_default="never",
            tags=("story", "introspection"),
            description="Story-builder affordance and navigation introspection tools.",
        ),
    }
    return registry


def list_mcp_server_descriptors(*, include_disabled: bool = False) -> list[MCPServerDescriptor]:
    servers = build_mcp_server_registry().values()
    if include_disabled:
        return list(servers)
    return [server for server in servers if server.enabled]


def get_mcp_server_descriptor(server_id: str) -> MCPServerDescriptor | None:
    return build_mcp_server_registry().get(server_id)
