from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any
from typing import Protocol
from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime

from app.core.db import async_session_maker
from app.services import kennel_client
from app.models import (
    RoomWorkspaceRuntimeInvocation,
    RoomWorkspaceRuntimeInvocationPublic,
    RoomWorkspaceRuntimeInvocationStatus,
)
from app.services.room_workspace_connection_service import (
    RoomWorkspaceRuntimeTarget,
    consume_current_room_workspace_runtime_target,
)
from app.services.room_workspace_runtime_execution_service import (
    RoomWorkspaceRuntimeExecutionError,
    RoomWorkspaceRuntimeInvocationCaller,
    RoomWorkspaceRuntimeInvocationRequest,
    RoomWorkspaceRuntimeInvocationResult,
    RoomWorkspaceJsonRpcRequest,
    RoomWorkspaceJsonRpcSession,
    build_room_workspace_json_rpc_session_payload,
    build_room_workspace_runtime_prompt_text,
    build_room_workspace_runtime_invocation_message,
    execute_room_workspace_runtime_invocation,
    normalize_room_workspace_runtime_response,
)


class RoomWorkspaceRuntimeAdapter(Protocol):
    async def invoke(
        self,
        request: RoomWorkspaceRuntimeInvocationRequest,
    ) -> RoomWorkspaceRuntimeInvocationResult:
        ...


@dataclass(frozen=True)
class WebsocketRoomWorkspaceRuntimeAdapter:
    async def invoke(
        self,
        request: RoomWorkspaceRuntimeInvocationRequest,
    ) -> RoomWorkspaceRuntimeInvocationResult:
        return await execute_room_workspace_runtime_invocation(request)


@dataclass(frozen=True)
class KennelRoutedRoomWorkspaceRuntimeAdapter:
    timeout_seconds: float = 15.0

    async def invoke(
        self,
        request: RoomWorkspaceRuntimeInvocationRequest,
    ) -> RoomWorkspaceRuntimeInvocationResult:
        response = await kennel_client.invoke_agent_runtime(
            request.target.kennel_name,
            service_id=request.target.endpoint_id,
            payload=build_room_workspace_runtime_invocation_message(request),
            timeout_seconds=self.timeout_seconds,
        )
        return normalize_room_workspace_runtime_response(
            request=request,
            response=response.get("response"),
        )


@dataclass(frozen=True)
class JsonRpcKennelRuntimeAdapter:
    timeout_seconds: float = 30.0

    async def invoke_session(
        self,
        request: RoomWorkspaceRuntimeInvocationRequest,
        session: RoomWorkspaceJsonRpcSession,
    ) -> dict[str, Any]:
        response = await kennel_client.invoke_agent_runtime(
            request.target.kennel_name,
            service_id=request.target.endpoint_id,
            invoke_mode="json_rpc",
            json_rpc_session=build_room_workspace_json_rpc_session_payload(session),
            timeout_seconds=self.timeout_seconds,
        )
        payload = response.get("response")
        if not isinstance(payload, dict):
            raise RoomWorkspaceRuntimeExecutionError(
                "Runtime returned an invalid JSON-RPC session payload.",
            )
        return payload


@dataclass(frozen=True)
class CodexExecProfileOptions:
    argv_prefix: tuple[str, ...] = ("codex", "exec")
    cwd_fallback: str = "/home/dev/workspace"
    user: str = "dev"
    extra_args: tuple[str, ...] = ()


@dataclass(frozen=True)
class CodexRoomWorkspaceRuntimeAdapter:
    websocket_adapter: RoomWorkspaceRuntimeAdapter = field(
        default_factory=KennelRoutedRoomWorkspaceRuntimeAdapter,
    )
    json_rpc_adapter: JsonRpcKennelRuntimeAdapter = field(
        default_factory=JsonRpcKennelRuntimeAdapter,
    )
    exec_options_by_profile: dict[str, CodexExecProfileOptions] = field(
        default_factory=lambda: {
            "codex_exec": CodexExecProfileOptions(),
        }
    )

    async def invoke(
        self,
        request: RoomWorkspaceRuntimeInvocationRequest,
    ) -> RoomWorkspaceRuntimeInvocationResult:
        profile = request.target.runtime_profile or "codex_app_server"
        if profile == "codex_app_server":
            return await self._invoke_json_rpc_profile(request)

        exec_options = self.exec_options_by_profile.get(profile)
        if exec_options is None:
            raise RoomWorkspaceRuntimeExecutionError(
                f"Codex runtime profile '{profile}' is not registered for execution.",
            )

        argv = [
            *exec_options.argv_prefix,
            *exec_options.extra_args,
            request.input,
        ]
        response = await kennel_client.invoke_agent_runtime(
            request.target.kennel_name,
            service_id=request.target.endpoint_id,
            invoke_mode="command",
            argv=argv,
            cwd=request.target.workspace_path or exec_options.cwd_fallback,
            user=exec_options.user,
            timeout_seconds=30.0,
        )
        return normalize_room_workspace_runtime_response(
            request=request,
            response=response.get("response"),
        )

    async def _invoke_json_rpc_profile(
        self,
        request: RoomWorkspaceRuntimeInvocationRequest,
    ) -> RoomWorkspaceRuntimeInvocationResult:
        cwd = request.target.workspace_path or "/home/dev/workspace"

        thread_session = RoomWorkspaceJsonRpcSession(
            requests=(
                RoomWorkspaceJsonRpcRequest(
                    id="initialize",
                    method="initialize",
                    params={
                        "clientInfo": {
                            "name": "dog-room-runtime-bridge",
                            "version": "2026-04-03",
                        },
                        "capabilities": {
                            "experimentalApi": False,
                        },
                    },
                ),
                RoomWorkspaceJsonRpcRequest(
                    id="thread/start",
                    method="thread/start",
                    params={
                        "cwd": cwd,
                        "approvalPolicy": "never",
                        "sandbox": "workspace-write",
                        "personality": "pragmatic",
                        "ephemeral": True,
                        "developerInstructions": (
                            "You are the connected workspace runtime for a room-mediated "
                            "execution request. Use the provided room runtime context "
                            "inside each turn input as execution context."
                        ),
                    },
                ),
            ),
        )
        thread_session_result = await self.json_rpc_adapter.invoke_session(
            request,
            thread_session,
        )
        thread_id = _extract_json_rpc_thread_id(thread_session_result)

        turn_session = RoomWorkspaceJsonRpcSession(
            requests=(
                RoomWorkspaceJsonRpcRequest(
                    id="initialize",
                    method="initialize",
                    params={
                        "clientInfo": {
                            "name": "dog-room-runtime-bridge",
                            "version": "2026-04-03",
                        },
                        "capabilities": {
                            "experimentalApi": False,
                        },
                    },
                ),
                RoomWorkspaceJsonRpcRequest(
                    id="turn/start",
                    method="turn/start",
                    params={
                        "threadId": thread_id,
                        "cwd": cwd,
                        "approvalPolicy": "never",
                        "input": [
                            {
                                "type": "text",
                                "text": build_room_workspace_runtime_prompt_text(request),
                            }
                        ],
                    },
                ),
            ),
            terminal_notification_methods=("turn/completed", "error"),
            tracked_notification_methods=("item/agentMessage/delta", "item/completed"),
        )
        turn_session_result = await self.json_rpc_adapter.invoke_session(
            request,
            turn_session,
        )
        return _normalize_json_rpc_runtime_result(
            request=request,
            session_result=turn_session_result,
        )


def _extract_json_rpc_thread_id(session_result: dict[str, Any]) -> str:
    responses = session_result.get("responses")
    if not isinstance(responses, list):
        raise RoomWorkspaceRuntimeExecutionError(
            "Runtime JSON-RPC session did not return any responses.",
        )
    for response in responses:
        if not isinstance(response, dict):
            continue
        result = response.get("result")
        if not isinstance(result, dict):
            continue
        thread = result.get("thread")
        if isinstance(thread, dict) and isinstance(thread.get("id"), str):
            return thread["id"]
    raise RoomWorkspaceRuntimeExecutionError(
        "Runtime JSON-RPC session did not return a thread identifier.",
    )


def _extract_json_rpc_notification_output_text(
    notifications: list[dict[str, Any]],
) -> str:
    delta_parts: list[str] = []
    completed_items: list[str] = []

    for notification in notifications:
        method = notification.get("method")
        params = notification.get("params")
        if method == "item/agentMessage/delta" and isinstance(params, dict):
            delta = params.get("delta")
            if isinstance(delta, str):
                delta_parts.append(delta)
        elif method == "item/completed" and isinstance(params, dict):
            item = params.get("item")
            if not isinstance(item, dict):
                continue
            if item.get("type") != "agentMessage":
                continue
            text = item.get("text")
            if isinstance(text, str):
                phase = item.get("phase")
                if phase == "finalAnswer":
                    return text
                completed_items.append(text)

    if delta_parts:
        return "".join(delta_parts).strip()
    if completed_items:
        return completed_items[-1]
    return ""


def _normalize_json_rpc_runtime_result(
    *,
    request: RoomWorkspaceRuntimeInvocationRequest,
    session_result: dict[str, Any],
) -> RoomWorkspaceRuntimeInvocationResult:
    terminal_notification = session_result.get("terminal_notification")
    notifications_raw = session_result.get("notifications")
    notifications = [
        notification
        for notification in notifications_raw
        if isinstance(notification, dict)
    ] if isinstance(notifications_raw, list) else []

    if isinstance(terminal_notification, dict) and terminal_notification.get("method") == "error":
        params = terminal_notification.get("params")
        if isinstance(params, dict) and isinstance(params.get("message"), str):
            message = params["message"]
        else:
            message = json.dumps(params, ensure_ascii=True)
        raise RoomWorkspaceRuntimeExecutionError(
            f"Runtime JSON-RPC session reported an error notification: {message}",
        )

    output_text = _extract_json_rpc_notification_output_text(notifications)
    if not output_text:
        output_text = json.dumps(session_result, ensure_ascii=True)

    return RoomWorkspaceRuntimeInvocationResult(
        request_id=request.request_id,
        connection_id=request.target.connection_id,
        workspace_id=str(request.target.workspace_id),
        endpoint_id=request.target.endpoint_id,
        runtime_label=request.target.endpoint_label,
        protocol=request.target.protocol,
        success=True,
        output_text=output_text,
        raw=session_result,
    )


_DEFAULT_ADAPTER = KennelRoutedRoomWorkspaceRuntimeAdapter()
_CODEX_ADAPTER = CodexRoomWorkspaceRuntimeAdapter()
_DEFAULT_RUNTIME_ADAPTERS: dict[str, RoomWorkspaceRuntimeAdapter] = {
    "codex": _CODEX_ADAPTER,
    "claude_code": _DEFAULT_ADAPTER,
    "hermes": _DEFAULT_ADAPTER,
}


@dataclass
class RoomWorkspaceRuntimeAdapterRegistry:
    adapters_by_runtime_id: dict[str, RoomWorkspaceRuntimeAdapter]
    default_adapter: RoomWorkspaceRuntimeAdapter | None = None
    profile_specific_adapters: dict[tuple[str, str], RoomWorkspaceRuntimeAdapter] = field(
        default_factory=dict,
    )

    def resolve(self, target: RoomWorkspaceRuntimeTarget) -> RoomWorkspaceRuntimeAdapter:
        if isinstance(target.runtime_id, str) and isinstance(target.runtime_profile, str):
            profile_adapter = self.profile_specific_adapters.get(
                (target.runtime_id, target.runtime_profile)
            )
            if profile_adapter is not None:
                return profile_adapter
        runtime_candidates = [
            target.runtime_id,
            target.endpoint_id,
        ]
        for candidate in runtime_candidates:
            if isinstance(candidate, str):
                adapter = self.adapters_by_runtime_id.get(candidate)
                if adapter is not None:
                    return adapter
        if self.default_adapter is not None:
            return self.default_adapter
        raise RoomWorkspaceRuntimeExecutionError(
            "No runtime adapter is registered for the connected workspace runtime.",
        )


def get_room_workspace_runtime_adapter_registry() -> RoomWorkspaceRuntimeAdapterRegistry:
    return RoomWorkspaceRuntimeAdapterRegistry(
        adapters_by_runtime_id=dict(_DEFAULT_RUNTIME_ADAPTERS),
        default_adapter=_DEFAULT_ADAPTER,
    )


@dataclass(frozen=True)
class RoomWorkspaceRuntimeInvocationExecution:
    target: RoomWorkspaceRuntimeTarget
    result: RoomWorkspaceRuntimeInvocationResult
    invocation: RoomWorkspaceRuntimeInvocationPublic


def _runtime_invocation_error_category(exc: Exception) -> str:
    if exc.__class__.__name__ == "RoomWorkspaceRuntimeConnectionError":
        return "connection_error"
    if exc.__class__.__name__ == "RoomWorkspaceRuntimeResponseTimeoutError":
        return "response_timeout"
    if exc.__class__.__name__ == "RoomWorkspaceRuntimeTargetResolutionError":
        return "target_resolution_error"
    return "execution_error"


async def _create_runtime_invocation_record(
    *,
    target: RoomWorkspaceRuntimeTarget,
    request: RoomWorkspaceRuntimeInvocationRequest,
) -> RoomWorkspaceRuntimeInvocationPublic:
    async with async_session_maker() as session:
        record = RoomWorkspaceRuntimeInvocation(
            request_id=request.request_id,
            room_id=target.room_id,
            workspace_id=target.workspace_id,
            connection_id=target.connection_id,
            runtime_id=target.runtime_id,
            runtime_profile=target.runtime_profile,
            caller_kind=request.caller.kind,
            caller_id=request.caller.id,
            status=RoomWorkspaceRuntimeInvocationStatus.running,
            started_at=datetime.utcnow(),
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)
        return RoomWorkspaceRuntimeInvocationPublic.model_validate(record)


async def _update_runtime_invocation_record(
    *,
    invocation_id: UUID,
    status: RoomWorkspaceRuntimeInvocationStatus,
    error_category: str | None = None,
) -> RoomWorkspaceRuntimeInvocationPublic:
    async with async_session_maker() as session:
        record = await session.get(RoomWorkspaceRuntimeInvocation, invocation_id)
        if record is None:
            raise RoomWorkspaceRuntimeExecutionError(
                "Runtime invocation record is missing.",
            )
        record.status = status
        record.error_category = error_category
        record.completed_at = datetime.utcnow()
        session.add(record)
        await session.commit()
        await session.refresh(record)
        return RoomWorkspaceRuntimeInvocationPublic.model_validate(record)


async def invoke_room_workspace_runtime(
    session: AsyncSession,
    *,
    room_id: UUID,
    input: str,
    caller: RoomWorkspaceRuntimeInvocationCaller,
    adapter_registry: RoomWorkspaceRuntimeAdapterRegistry | None = None,
) -> RoomWorkspaceRuntimeInvocationExecution:
    target = await consume_current_room_workspace_runtime_target(
        session,
        room_id=room_id,
    )
    registry = adapter_registry or get_room_workspace_runtime_adapter_registry()
    adapter = registry.resolve(target)
    request = RoomWorkspaceRuntimeInvocationRequest(
        target=target,
        input=input,
        caller=caller,
    )
    invocation = await _create_runtime_invocation_record(
        target=target,
        request=request,
    )
    try:
        result = await adapter.invoke(request)
    except Exception as exc:
        await _update_runtime_invocation_record(
            invocation_id=invocation.id,
            status=RoomWorkspaceRuntimeInvocationStatus.failed,
            error_category=_runtime_invocation_error_category(exc),
        )
        raise

    completed_invocation = await _update_runtime_invocation_record(
        invocation_id=invocation.id,
        status=RoomWorkspaceRuntimeInvocationStatus.completed,
    )
    return RoomWorkspaceRuntimeInvocationExecution(
        target=target,
        result=result,
        invocation=completed_invocation,
    )
