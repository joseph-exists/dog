from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import redis.asyncio as redis

from tesserax_service.contracts import RenderRequest
from tesserax_service.registry import get_script_spec, list_script_specs
from tesserax_service.runtime import execute_render
from tesserax_service import scripts as _scripts  # noqa: F401

LOG_LEVEL = os.getenv("TESSER_LOG_LEVEL", "INFO").upper()
REDIS_HOST = os.getenv("TESSER_REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("TESSER_REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("TESSER_REDIS_DB", "0"))
REQUEST_CHANNEL = os.getenv("TESSER_REQUEST_CHANNEL", "tesser:requests")
RESPONSE_CHANNEL = os.getenv("TESSER_RESPONSE_CHANNEL", "tesser:responses")
WORKER_ID = os.getenv("TESSER_WORKER_ID", "tesser-worker-1")
ARTIFACTS_ROOT = Path(os.getenv("TESSER_ARTIFACTS_ROOT", "/data/artifacts/redis-bridge"))
EXAMPLES_INDEX_PATH = Path("/app/examples-other/reference/index.md")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("tesser.redis_bridge")


BUILTIN_SCRIPT_METADATA: dict[str, dict[str, Any]] = {
    "simple_svg": {
        "name": "simple_svg",
        "description": "Render a basic title/subtitle SVG card.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "subtitle": {"type": "string"},
            },
            "required": ["title"],
        },
        "help_text": "usage: simple_svg --title <text> [--subtitle <text>]",
    },
    "entity_badge": {
        "name": "entity_badge",
        "description": "Render entity badge SVG for entity_type/entity_id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_type": {"type": "string"},
                "entity_id": {"type": "string"},
                "title": {"type": "string"},
                "subtitle": {"type": "string"},
            },
            "required": ["entity_type", "entity_id"],
        },
        "help_text": "usage: entity_badge --entity-type <type> --entity-id <id> [--title <text>] [--subtitle <text>]",
    },
    "status_strip": {
        "name": "status_strip",
        "description": "Render status-strip SVG with heading and detail line.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "subtitle": {"type": "string"},
                "status": {"type": "string"},
            },
            "required": ["title"],
        },
        "help_text": "usage: status_strip --title <text> [--subtitle <text>] [--status <state>]",
    },
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _render_svg(title: str, subtitle: str | None = None) -> str:
    safe_title = (title or "Tesser Render").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    safe_subtitle = (
        subtitle.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if subtitle
        else None
    )
    subtitle_node = (
        f'<text x="360" y="118" text-anchor="middle" fill="#444" font-size="16" font-family="sans-serif">{safe_subtitle}</text>'
        if safe_subtitle
        else ""
    )
    return (
        '<svg width="720" height="180" viewBox="0 0 720 180" xmlns="http://www.w3.org/2000/svg">'
        '<rect x="0" y="0" width="720" height="180" fill="#f7f8fa" stroke="#d7d9df"/>'
        f'<text x="360" y="72" text-anchor="middle" fill="#111" font-size="28" font-family="sans-serif">{safe_title}</text>'
        f"{subtitle_node}"
        "</svg>"
    )


def _render_entity_badge(entity_type: str, entity_id: str, title: str | None = None, subtitle: str | None = None) -> str:
    safe_title = (title or f"{entity_type}:{entity_id}").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    safe_subtitle = (subtitle or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    safe_entity = f"{entity_type}/{entity_id}".replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    subtitle_node = (
        f'<text x="24" y="98" fill="#374151" font-size="14" font-family="sans-serif">{safe_subtitle}</text>'
        if safe_subtitle
        else ""
    )
    return (
        '<svg width="720" height="180" viewBox="0 0 720 180" xmlns="http://www.w3.org/2000/svg">'
        '<rect x="0" y="0" width="720" height="180" fill="#f8fafc" stroke="#dbe3ee"/>'
        '<rect x="24" y="26" rx="8" ry="8" width="190" height="28" fill="#111827"/>'
        f'<text x="36" y="46" fill="#f9fafb" font-size="13" font-family="sans-serif">{safe_entity}</text>'
        f'<text x="24" y="78" fill="#111827" font-size="30" font-family="sans-serif">{safe_title}</text>'
        f"{subtitle_node}"
        "</svg>"
    )


def _render_status_strip(title: str, subtitle: str | None = None, status: str | None = None) -> str:
    safe_title = (title or "Status").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    safe_subtitle = (subtitle or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    safe_status = (status or "ok").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    subtitle_node = (
        f'<text x="28" y="116" fill="#334155" font-size="15" font-family="sans-serif">{safe_subtitle}</text>'
        if safe_subtitle
        else ""
    )
    return (
        '<svg width="720" height="180" viewBox="0 0 720 180" xmlns="http://www.w3.org/2000/svg">'
        '<rect x="0" y="0" width="720" height="180" fill="#fffef7" stroke="#e7e5d0"/>'
        '<rect x="24" y="24" width="672" height="18" fill="#111827"/>'
        f'<text x="30" y="38" fill="#f9fafb" font-size="12" font-family="sans-serif">{safe_status}</text>'
        f'<text x="28" y="88" fill="#111827" font-size="30" font-family="sans-serif">{safe_title}</text>'
        f"{subtitle_node}"
        "</svg>"
    )


def _run_builtin_script(script_name: str, script_input: dict[str, Any]) -> dict[str, Any]:
    if script_name == "simple_svg":
        svg = _render_svg(str(script_input.get("title") or "Tesser Render"), str(script_input.get("subtitle")) if script_input.get("subtitle") is not None else None)
    elif script_name == "entity_badge":
        svg = _render_entity_badge(
            str(script_input.get("entity_type") or "entity"),
            str(script_input.get("entity_id") or "unknown"),
            str(script_input.get("title")) if script_input.get("title") is not None else None,
            str(script_input.get("subtitle")) if script_input.get("subtitle") is not None else None,
        )
    elif script_name == "status_strip":
        svg = _render_status_strip(
            str(script_input.get("title") or "Status"),
            str(script_input.get("subtitle")) if script_input.get("subtitle") is not None else None,
            str(script_input.get("status")) if script_input.get("status") is not None else None,
        )
    else:
        raise ValueError(f"Unsupported script_name: {script_name}")
    return {"format": "svg", "svg": svg}


def _registry_script_metadata() -> list[dict[str, Any]]:
    scripts: list[dict[str, Any]] = []
    for spec in list_script_specs():
        scripts.append(
            {
                "name": spec.script_id,
                "description": f"{spec.kind} script ({spec.default_runtime_profile})",
                "input_schema": {"type": "object", "additionalProperties": True},
                "help_text": (
                    f"script: {spec.script_id}\n"
                    f"kind: {spec.kind}\n"
                    f"default_runtime_profile: {spec.default_runtime_profile}\n"
                    f"enabled: {spec.enabled}"
                ),
                "kind": spec.kind,
                "enabled": spec.enabled,
                "disabled_reason": spec.disabled_reason,
            }
        )
    return scripts


def _select_formats(script_input: dict[str, Any]) -> list[str]:
    raw_formats = script_input.get("__formats__")
    if isinstance(raw_formats, list) and all(isinstance(item, str) and item for item in raw_formats):
        return raw_formats
    raw_format = script_input.get("format")
    if isinstance(raw_format, str) and raw_format.strip():
        return [raw_format.strip()]
    return ["svg"]


def _run_registry_script(script_name: str, script_input: dict[str, Any], request_id: str | None) -> dict[str, Any]:
    spec = get_script_spec(script_name)
    output_dir = ARTIFACTS_ROOT / (request_id or "adhoc")
    request = RenderRequest(
        script_id=script_name,
        params=dict(script_input),
        output_dir=str(output_dir),
        formats=_select_formats(script_input),
        basename="render",
        request_id=request_id,
        runtime_profile=None,
    )
    result = execute_render(request)
    render_payload: dict[str, Any] = {
        "format": "external",
        "artifacts": [artifact.to_dict() for artifact in result.artifacts],
        "manifest_path": result.manifest_path,
        "runtime_profile": result.runtime_profile,
        "resolved_capabilities": result.resolved_capabilities,
    }
    svg_artifact = next((artifact for artifact in result.artifacts if artifact.media_type == "image/svg+xml"), None)
    if svg_artifact is not None:
        svg_path = Path(svg_artifact.path)
        if svg_path.exists():
            render_payload["format"] = "svg"
            render_payload["svg"] = svg_path.read_text(encoding="utf-8")
    if spec.kind in {"runner", "utility"}:
        render_payload["format"] = render_payload.get("format", "external")
    return render_payload


def _build_render_response(payload: dict[str, Any]) -> dict[str, Any]:
    request_id = payload.get("request_id")
    room_id = payload.get("room_id")
    script_name = str(payload.get("script_name") or "simple_svg")
    script_input_raw = payload.get("script_input")
    script_input = script_input_raw if isinstance(script_input_raw, dict) else {}

    if script_name in BUILTIN_SCRIPT_METADATA:
        render_payload = _run_builtin_script(script_name, script_input)
    else:
        render_payload = _run_registry_script(script_name, script_input, request_id)

    return {
        "request_id": request_id,
        "room_id": room_id,
        "worker_id": WORKER_ID,
        "script_name": script_name,
        "status": "ok",
        "type": "tesser.script.response",
        "render": render_payload,
        "received_at": payload.get("sent_at"),
        "completed_at": _now_iso(),
    }


def _build_list_scripts_response(payload: dict[str, Any]) -> dict[str, Any]:
    scripts = [BUILTIN_SCRIPT_METADATA[name] for name in sorted(BUILTIN_SCRIPT_METADATA)]
    scripts.extend(_registry_script_metadata())
    return {
        "request_id": payload.get("request_id"),
        "worker_id": WORKER_ID,
        "status": "ok",
        "type": "tesser.scripts.list.response",
        "scripts": scripts,
        "completed_at": _now_iso(),
    }


def _build_script_help_response(payload: dict[str, Any]) -> dict[str, Any]:
    script_name = str(payload.get("script_name") or "")
    if script_name in BUILTIN_SCRIPT_METADATA:
        metadata = BUILTIN_SCRIPT_METADATA[script_name]
    else:
        spec = get_script_spec(script_name)
        metadata = {
            "name": script_name,
            "description": f"{spec.kind} script ({spec.default_runtime_profile})",
            "input_schema": {"type": "object", "additionalProperties": True},
            "help_text": (
                f"script: {script_name}\n"
                f"kind: {spec.kind}\n"
                f"default_runtime_profile: {spec.default_runtime_profile}\n"
                f"enabled: {spec.enabled}\n"
                f"disabled_reason: {spec.disabled_reason or ''}"
            ),
        }
    return {
        "request_id": payload.get("request_id"),
        "worker_id": WORKER_ID,
        "status": "ok",
        "type": "tesser.script.help.response",
        "script_name": script_name,
        "help_text": metadata.get("help_text"),
        "input_schema": metadata.get("input_schema"),
        "description": metadata.get("description"),
        "completed_at": _now_iso(),
    }


def _build_examples_index_response(payload: dict[str, Any]) -> dict[str, Any]:
    if not EXAMPLES_INDEX_PATH.exists():
        raise ValueError(f"Examples index not found at {EXAMPLES_INDEX_PATH}")
    return {
        "request_id": payload.get("request_id"),
        "worker_id": WORKER_ID,
        "status": "ok",
        "type": "tesser.examples.index.response",
        "path": "examples-other/reference/index.md",
        "content": EXAMPLES_INDEX_PATH.read_text(encoding="utf-8"),
        "completed_at": _now_iso(),
    }


async def _process_message(redis_client: redis.Redis, raw_data: str) -> None:
    payload: dict[str, Any] = {}
    message_type = "tesser.script.response"
    try:
        payload = json.loads(raw_data)
        request_type = str(payload.get("type") or "tesser.script.request")
        if request_type == "tesser.scripts.list.request":
            message_type = "tesser.scripts.list.response"
            response = _build_list_scripts_response(payload)
        elif request_type == "tesser.examples.index.request":
            message_type = "tesser.examples.index.response"
            response = _build_examples_index_response(payload)
        elif request_type == "tesser.script.help.request":
            message_type = "tesser.script.help.response"
            response = _build_script_help_response(payload)
        else:
            message_type = "tesser.script.response"
            response = _build_render_response(payload)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to process tesser message")
        request_id = payload.get("request_id") if isinstance(payload, dict) else None
        error_payload = {
            "request_id": request_id,
            "status": "error",
            "type": message_type,
            "worker_id": WORKER_ID,
            "error": str(exc),
            "completed_at": _now_iso(),
        }
        await redis_client.publish(RESPONSE_CHANNEL, json.dumps(error_payload))
        return

    await redis_client.publish(RESPONSE_CHANNEL, json.dumps(response))
    logger.info("Published tesser response request_id=%s", response.get("request_id"))


async def run() -> None:
    ARTIFACTS_ROOT.mkdir(parents=True, exist_ok=True)
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True,
    )
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(REQUEST_CHANNEL)
    logger.info(
        "Tesser redis bridge listening request_channel=%s response_channel=%s redis=%s:%s db=%s",
        REQUEST_CHANNEL,
        RESPONSE_CHANNEL,
        REDIS_HOST,
        REDIS_PORT,
        REDIS_DB,
    )
    try:
        async for message in pubsub.listen():
            if message.get("type") != "message":
                continue
            data = message.get("data")
            if not isinstance(data, str):
                continue
            await _process_message(redis_client, data)
    finally:
        await pubsub.unsubscribe(REQUEST_CHANNEL)
        await pubsub.close()
        await redis_client.aclose()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
