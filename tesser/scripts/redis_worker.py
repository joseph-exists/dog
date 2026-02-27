#!/usr/bin/env python3
"""Redis pub/sub worker for Tesser integration.

Consumes JSON messages from a request channel and publishes JSON responses
(with rendered SVG payloads) to a response channel.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

import redis.asyncio as redis

LOG_LEVEL = os.getenv("TESSER_LOG_LEVEL", "INFO").upper()
REDIS_HOST = os.getenv("TESSER_REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("TESSER_REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("TESSER_REDIS_DB", "0"))
REQUEST_CHANNEL = os.getenv("TESSER_REQUEST_CHANNEL", "tesser:requests")
RESPONSE_CHANNEL = os.getenv("TESSER_RESPONSE_CHANNEL", "tesser:responses")
WORKER_ID = os.getenv("TESSER_WORKER_ID", "tesser-worker-1")

APP_ROOT = Path("/app")
EXAMPLES_ROOT = APP_ROOT / "examples-other"
EXAMPLES_INDEX_PATH = EXAMPLES_ROOT / "reference" / "index.md"
EXAMPLES_SCRIPT_PREFIX = "example."

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("tesser.redis_worker")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _render_svg(title: str, subtitle: str | None = None) -> str:
    safe_title = escape(title or "Tesser Render")
    safe_subtitle = escape(subtitle) if subtitle else None
    subtitle_node = (
        f'<text x="360" y="118" text-anchor="middle" fill="#444" '
        f'font-size="16" font-family="sans-serif">{safe_subtitle}</text>'
        if safe_subtitle
        else ""
    )
    return (
        '<svg width="720" height="180" viewBox="0 0 720 180" '
        'xmlns="http://www.w3.org/2000/svg">'
        '<rect x="0" y="0" width="720" height="180" fill="#f7f8fa" stroke="#d7d9df"/>'
        f'<text x="360" y="72" text-anchor="middle" fill="#111" '
        f'font-size="28" font-family="sans-serif">{safe_title}</text>'
        f"{subtitle_node}"
        "</svg>"
    )


def _render_entity_badge(
    entity_type: str,
    entity_id: str,
    title: str | None = None,
    subtitle: str | None = None,
) -> str:
    safe_title = escape(title or f"{entity_type}:{entity_id}")
    safe_subtitle = escape(subtitle or "")
    safe_entity = escape(f"{entity_type}/{entity_id}")
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


def _render_status_strip(
    title: str,
    subtitle: str | None = None,
    status: str | None = None,
) -> str:
    safe_title = escape(title or "Status")
    safe_subtitle = escape(subtitle or "")
    safe_status = escape(status or "ok")
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


def _run_builtin_script(script_name: str, script_input: dict[str, Any]) -> str:
    if script_name == "simple_svg":
        title = str(script_input.get("title") or "Tesser Render")
        subtitle_raw = script_input.get("subtitle")
        subtitle = str(subtitle_raw) if subtitle_raw is not None else None
        return _render_svg(title=title, subtitle=subtitle)
    if script_name == "entity_badge":
        entity_type = str(script_input.get("entity_type") or "entity")
        entity_id = str(script_input.get("entity_id") or "unknown")
        title_raw = script_input.get("title")
        subtitle_raw = script_input.get("subtitle")
        title = str(title_raw) if title_raw is not None else None
        subtitle = str(subtitle_raw) if subtitle_raw is not None else None
        return _render_entity_badge(entity_type, entity_id, title=title, subtitle=subtitle)
    if script_name == "status_strip":
        title = str(script_input.get("title") or "Status")
        subtitle_raw = script_input.get("subtitle")
        status_raw = script_input.get("status")
        subtitle = str(subtitle_raw) if subtitle_raw is not None else None
        status = str(status_raw) if status_raw is not None else None
        return _render_status_strip(title=title, subtitle=subtitle, status=status)
    raise ValueError(f"Unsupported script_name: {script_name}")


SCRIPT_METADATA: dict[str, dict[str, Any]] = {
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
        "help_text": (
            "usage: simple_svg --title <text> [--subtitle <text>]\n\n"
            "Renders a centered title card SVG."
        ),
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
        "help_text": (
            "usage: entity_badge --entity-type <type> --entity-id <id> "
            "[--title <text>] [--subtitle <text>]\n\n"
            "Renders entity metadata badge SVG."
        ),
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
        "help_text": (
            "usage: status_strip --title <text> [--subtitle <text>] [--status <state>]\n\n"
            "Renders status-strip style SVG."
        ),
    },
}

_EXTERNAL_SCRIPT_CACHE: dict[str, dict[str, Any]] | None = None
_EXTERNAL_SCRIPT_PATHS: dict[str, Path] = {}
_EXTERNAL_HELP_CACHE: dict[str, str] = {}


def _script_name_from_relative_path(relative_path: str) -> str:
    normalized = relative_path.replace("\\", "/")
    if normalized.endswith(".py"):
        normalized = normalized[:-3]
    normalized = normalized.replace("/", ".")
    return f"{EXAMPLES_SCRIPT_PREFIX}{normalized}"


def _discover_external_scripts() -> dict[str, dict[str, Any]]:
    global _EXTERNAL_SCRIPT_CACHE

    discovered: dict[str, dict[str, Any]] = {}
    _EXTERNAL_SCRIPT_PATHS.clear()

    if not EXAMPLES_INDEX_PATH.exists():
        _EXTERNAL_SCRIPT_CACHE = discovered
        return discovered

    index_text = EXAMPLES_INDEX_PATH.read_text(encoding="utf-8")
    matches = re.findall(r"`(examples-other/[^`]+\.py)`", index_text)

    seen: set[str] = set()
    for full_path in matches:
        if full_path in seen:
            continue
        seen.add(full_path)

        if not full_path.startswith("examples-other/"):
            continue
        relative_path = full_path[len("examples-other/") :]
        absolute_path = EXAMPLES_ROOT / relative_path
        if not absolute_path.exists():
            continue

        script_name = _script_name_from_relative_path(relative_path)
        discovered[script_name] = {
            "name": script_name,
            "description": f"examples-other script: {relative_path}",
            "input_schema": {
                "type": "object",
                "description": "CLI flag map; keys become --flag-name arguments.",
                "additionalProperties": True,
            },
            "help_text": None,
            "source_path": f"examples-other/{relative_path}",
            "kind": "external_example",
        }
        _EXTERNAL_SCRIPT_PATHS[script_name] = absolute_path

    _EXTERNAL_SCRIPT_CACHE = discovered
    return discovered


def _get_external_help(script_name: str) -> str:
    cached = _EXTERNAL_HELP_CACHE.get(script_name)
    if cached is not None:
        return cached

    script_path = _EXTERNAL_SCRIPT_PATHS.get(script_name)
    if script_path is None:
        raise ValueError(f"Unsupported script_name: {script_name}")

    try:
        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            cwd=APP_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Failed to get --help for {script_name}: {exc}") from exc

    help_text = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
    help_text = help_text.strip() or "(no help output)"
    _EXTERNAL_HELP_CACHE[script_name] = help_text
    return help_text


def _script_input_to_cli_args(script_input: dict[str, Any]) -> list[str]:
    args: list[str] = []

    raw_args = script_input.get("__args__")
    if isinstance(raw_args, list):
        for value in raw_args:
            if isinstance(value, str) and value.strip():
                args.append(value)

    for key in sorted(script_input.keys()):
        if key.startswith("__"):
            continue

        value = script_input[key]
        flag = f"--{key.replace('_', '-')}"

        if isinstance(value, bool):
            if value:
                args.append(flag)
            continue
        if value is None:
            continue
        if isinstance(value, list):
            for item in value:
                args.extend([flag, str(item)])
            continue

        args.extend([flag, str(value)])

    return args


def _run_external_example_script(
    script_name: str,
    script_input: dict[str, Any],
) -> dict[str, Any]:
    script_path = _EXTERNAL_SCRIPT_PATHS.get(script_name)
    if script_path is None:
        raise ValueError(f"Unsupported script_name: {script_name}")

    cli_args = _script_input_to_cli_args(script_input)
    timeout_seconds = float(script_input.get("__timeout_seconds__", 120))
    command = [sys.executable, str(script_path), *cli_args]

    result = subprocess.run(
        command,
        cwd=APP_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout_seconds,
    )

    output_path: str | None = None
    if "--output" in cli_args:
        idx = cli_args.index("--output")
        if idx + 1 < len(cli_args):
            output_path = cli_args[idx + 1]

    output_svg = None
    if output_path:
        resolved_output = Path(output_path)
        if not resolved_output.is_absolute():
            resolved_output = APP_ROOT / resolved_output
        if resolved_output.exists() and resolved_output.suffix.lower() == ".svg":
            output_svg = resolved_output.read_text(encoding="utf-8")

    if result.returncode != 0:
        raise ValueError(
            f"Script failed ({result.returncode}): {script_name}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

    render_payload: dict[str, Any] = {
        "format": "external",
        "command": command,
        "stdout": result.stdout[-8000:] if result.stdout else "",
        "stderr": result.stderr[-8000:] if result.stderr else "",
        "output_path": output_path,
    }
    if output_svg:
        render_payload["format"] = "svg"
        render_payload["svg"] = output_svg
    return render_payload


def _build_render_response(payload: dict[str, Any]) -> dict[str, Any]:
    request_id = payload.get("request_id")
    room_id = payload.get("room_id")
    script_name = str(payload.get("script_name") or "simple_svg")
    script_input_raw = payload.get("script_input")
    script_input = script_input_raw if isinstance(script_input_raw, dict) else {}

    external_catalog = _discover_external_scripts()
    if script_name in external_catalog:
        render_payload = _run_external_example_script(script_name, script_input)
    else:
        render_payload = {"format": "svg", "svg": _run_builtin_script(script_name, script_input)}

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
    scripts = [SCRIPT_METADATA[name] for name in sorted(SCRIPT_METADATA.keys())]
    external_catalog = _discover_external_scripts()
    scripts.extend(external_catalog[name] for name in sorted(external_catalog.keys()))
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

    metadata = SCRIPT_METADATA.get(script_name)
    if metadata is not None:
        help_text = metadata.get("help_text")
        return {
            "request_id": payload.get("request_id"),
            "worker_id": WORKER_ID,
            "status": "ok",
            "type": "tesser.script.help.response",
            "script_name": script_name,
            "help_text": help_text,
            "input_schema": metadata.get("input_schema"),
            "description": metadata.get("description"),
            "completed_at": _now_iso(),
        }

    external_catalog = _discover_external_scripts()
    metadata = external_catalog.get(script_name)
    if metadata is None:
        raise ValueError(f"Unsupported script_name: {script_name}")

    help_text = _get_external_help(script_name)
    return {
        "request_id": payload.get("request_id"),
        "worker_id": WORKER_ID,
        "status": "ok",
        "type": "tesser.script.help.response",
        "script_name": script_name,
        "help_text": help_text,
        "input_schema": metadata.get("input_schema"),
        "description": metadata.get("description"),
        "completed_at": _now_iso(),
    }


def _build_examples_index_response(payload: dict[str, Any]) -> dict[str, Any]:
    if not EXAMPLES_INDEX_PATH.exists():
        raise ValueError(f"Examples index not found at {EXAMPLES_INDEX_PATH}")
    content = EXAMPLES_INDEX_PATH.read_text(encoding="utf-8")
    return {
        "request_id": payload.get("request_id"),
        "worker_id": WORKER_ID,
        "status": "ok",
        "type": "tesser.examples.index.response",
        "path": "examples-other/reference/index.md",
        "content": content,
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
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True,
    )

    pubsub = redis_client.pubsub()
    await pubsub.subscribe(REQUEST_CHANNEL)
    logger.info(
        "Tesser worker listening request_channel=%s response_channel=%s redis=%s:%s db=%s",
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
        await redis_client.close()


if __name__ == "__main__":
    asyncio.run(run())
