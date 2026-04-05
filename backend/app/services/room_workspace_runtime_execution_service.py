from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

import websockets

from app.services.room_workspace_connection_service import RoomWorkspaceRuntimeTarget


_SUPPORTED_RUNTIME_PROTOCOLS = frozenset({"ws", "wss"})
_RUNTIME_MESSAGE_TYPE = "room.workspace.runtime.invoke"
_RUNTIME_MESSAGE_VERSION = "2026-04-02"


@dataclass(frozen=True)
class RoomWorkspaceRuntimeInvocationCaller:
    """Identifies who initiated the room-to-runtime invocation."""

    kind: str
    id: str


@dataclass(frozen=True)
class RoomWorkspaceRuntimeInvocationRequest:
    """Backend-owned request envelope for room-to-runtime invocation."""

    target: RoomWorkspaceRuntimeTarget
    input: str
    caller: RoomWorkspaceRuntimeInvocationCaller
    request_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass(frozen=True)
class RoomWorkspaceJsonRpcRequest:
    """A single JSON-RPC request frame for a runtime-managed session."""

    id: str
    method: str
    params: Any = None


@dataclass(frozen=True)
class RoomWorkspaceJsonRpcSession:
    """A JSON-RPC session definition executed over a runtime websocket."""

    requests: tuple[RoomWorkspaceJsonRpcRequest, ...]
    terminal_notification_methods: tuple[str, ...] = ()
    tracked_notification_methods: tuple[str, ...] = ()
    fail_on_server_request: bool = True


@dataclass(frozen=True)
class RoomWorkspaceRuntimeInvocationResult:
    """Normalized runtime invocation result returned to backend callers."""

    request_id: str
    connection_id: str
    workspace_id: str
    endpoint_id: str
    runtime_label: str
    protocol: str
    success: bool
    output_text: str
    raw: Any


class RoomWorkspaceRuntimeExecutionError(ValueError):
    """Raised when backend-mediated runtime execution fails."""


class RoomWorkspaceRuntimeConnectionError(RoomWorkspaceRuntimeExecutionError):
    """Raised when the backend cannot open the runtime websocket."""


class RoomWorkspaceRuntimeResponseTimeoutError(RoomWorkspaceRuntimeExecutionError):
    """Raised when the runtime websocket opens but no response arrives in time."""


def build_room_workspace_runtime_prompt_text(
    request: RoomWorkspaceRuntimeInvocationRequest,
) -> str:
    """Render room runtime invocation intent as plain text for text-first runtimes."""

    return (
        "Room runtime invocation\n"
        f"room_id: {request.target.room_id}\n"
        f"workspace_id: {request.target.workspace_id}\n"
        f"workspace_name: {request.target.workspace_name}\n"
        f"connection_id: {request.target.connection_id}\n"
        f"descriptor_id: {request.target.descriptor_id}\n"
        f"endpoint_id: {request.target.endpoint_id}\n"
        f"endpoint_label: {request.target.endpoint_label}\n"
        f"caller_kind: {request.caller.kind}\n"
        f"caller_id: {request.caller.id}\n"
        "request:\n"
        f"{request.input}"
    )


def build_room_workspace_runtime_invocation_message(
    request: RoomWorkspaceRuntimeInvocationRequest,
) -> dict[str, Any]:
    """Build the common websocket envelope sent to connected agent runtimes."""

    return {
        "type": _RUNTIME_MESSAGE_TYPE,
        "version": _RUNTIME_MESSAGE_VERSION,
        "request_id": request.request_id,
        "room_context": {
            "room_id": str(request.target.room_id),
            "workspace_id": str(request.target.workspace_id),
            "workspace_name": request.target.workspace_name,
            "connection_id": request.target.connection_id,
            "descriptor_id": request.target.descriptor_id,
            "endpoint_id": request.target.endpoint_id,
            "endpoint_label": request.target.endpoint_label,
            "scope": dict(request.target.scope),
        },
        "caller": {
            "kind": request.caller.kind,
            "id": request.caller.id,
        },
        "input": request.input,
    }


def build_room_workspace_json_rpc_session_payload(
    session: RoomWorkspaceJsonRpcSession,
) -> dict[str, Any]:
    """Serialize a backend JSON-RPC session definition for kennel transport."""

    return {
        "requests": [
            {
                "id": request.id,
                "method": request.method,
                "params": request.params,
            }
            for request in session.requests
        ],
        "terminal_notification_methods": list(session.terminal_notification_methods),
        "tracked_notification_methods": list(session.tracked_notification_methods),
        "fail_on_server_request": session.fail_on_server_request,
    }


def _coerce_output_text(payload: Any) -> str:
    if isinstance(payload, str):
        return payload
    if isinstance(payload, dict):
        for key in ("output_text", "content", "message", "output"):
            value = payload.get(key)
            if isinstance(value, str):
                return value
        if isinstance(payload.get("result"), str):
            return str(payload["result"])
    return json.dumps(payload, ensure_ascii=True)


def _normalize_runtime_response(
    *,
    request: RoomWorkspaceRuntimeInvocationRequest,
    response: Any,
) -> RoomWorkspaceRuntimeInvocationResult:
    if isinstance(response, bytes):
        try:
            response = response.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise RoomWorkspaceRuntimeExecutionError(
                "Runtime returned a non-UTF-8 websocket payload.",
            ) from exc

    raw_payload: Any = response
    success = True
    request_id = request.request_id

    if isinstance(response, str):
        try:
            raw_payload = json.loads(response)
        except json.JSONDecodeError:
            raw_payload = response

    if isinstance(raw_payload, dict):
        if isinstance(raw_payload.get("request_id"), str):
            request_id = raw_payload["request_id"]
        if isinstance(raw_payload.get("success"), bool):
            success = raw_payload["success"]
        elif isinstance(raw_payload.get("status"), str):
            success = raw_payload["status"].lower() not in {"error", "failed", "failure"}

    return RoomWorkspaceRuntimeInvocationResult(
        request_id=request_id,
        connection_id=request.target.connection_id,
        workspace_id=str(request.target.workspace_id),
        endpoint_id=request.target.endpoint_id,
        runtime_label=request.target.endpoint_label,
        protocol=request.target.protocol,
        success=success,
        output_text=_coerce_output_text(raw_payload),
        raw=raw_payload,
    )


def normalize_room_workspace_runtime_response(
    *,
    request: RoomWorkspaceRuntimeInvocationRequest,
    response: Any,
) -> RoomWorkspaceRuntimeInvocationResult:
    return _normalize_runtime_response(request=request, response=response)


async def execute_room_workspace_runtime_invocation(
    request: RoomWorkspaceRuntimeInvocationRequest,
    *,
    timeout_seconds: float = 15.0,
    websocket_connect: Any = None,
) -> RoomWorkspaceRuntimeInvocationResult:
    """
    Execute a room-owned invocation against the resolved runtime target.

    This transport layer is runtime-agnostic on purpose. Codex, Claude Code,
    and Hermes may return different response payloads, but they all receive the
    same websocket request envelope.
    """

    if request.target.protocol not in _SUPPORTED_RUNTIME_PROTOCOLS:
        raise RoomWorkspaceRuntimeExecutionError(
            f"Runtime endpoint protocol '{request.target.protocol}' is not supported by the websocket execution adapter.",
        )

    connect = websocket_connect or websockets.connect
    message = build_room_workspace_runtime_invocation_message(request)
    websocket = None

    try:
        websocket = await connect(
            request.target.url,
            open_timeout=timeout_seconds,
            close_timeout=timeout_seconds,
        ).__aenter__()
    except asyncio.TimeoutError as exc:
        raise RoomWorkspaceRuntimeConnectionError(
            "Runtime invocation failed while opening the websocket connection.",
        ) from exc
    except Exception as exc:
        raise RoomWorkspaceRuntimeConnectionError(
            f"Runtime invocation failed before the websocket opened: {exc}",
        ) from exc

    try:
        try:
            await websocket.send(json.dumps(message))
            response = await asyncio.wait_for(websocket.recv(), timeout=timeout_seconds)
        except asyncio.TimeoutError as exc:
            raise RoomWorkspaceRuntimeResponseTimeoutError(
                "Runtime invocation timed out after the websocket opened while waiting for a response.",
            ) from exc
        except Exception as exc:
            raise RoomWorkspaceRuntimeExecutionError(
                f"Runtime invocation failed after the websocket opened: {exc}",
            ) from exc
    finally:
        await websocket.__aexit__(None, None, None)

    return _normalize_runtime_response(request=request, response=response)
