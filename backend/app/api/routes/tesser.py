"""
API routes for Tesser script execution.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser
from app.models import (
    TesserExamplesIndexResponse,
    TesserScriptPublic,
    TesserScriptHelpResponse,
    TesserScriptRunRequest,
    TesserScriptRunResponse,
    TesserScriptsPublic,
)
from app.services.tesser_service import (
    get_tesser_examples_index,
    TesserRenderTimeoutError,
    get_tesser_script_help,
    list_tesser_scripts,
    request_tesser,
)

router = APIRouter()


@router.get("/scripts", response_model=TesserScriptsPublic)
async def list_scripts(current_user: CurrentUser) -> Any:
    _ = current_user
    try:
        scripts_payload = await list_tesser_scripts()
    except TesserRenderTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    scripts = [TesserScriptPublic.model_validate(item) for item in scripts_payload]
    return TesserScriptsPublic(data=scripts, count=len(scripts))


@router.get("/examples/index", response_model=TesserExamplesIndexResponse)
async def get_examples_index(current_user: CurrentUser) -> Any:
    _ = current_user
    try:
        response = await get_tesser_examples_index()
    except TesserRenderTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(exc),
        ) from exc
    if str(response.get("status") or "") == "error":
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=response.get("error") or "Failed to fetch examples index",
        )
    content = response.get("content")
    if not isinstance(content, str):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Tesser examples index response missing content",
        )
    path = response.get("path")
    return TesserExamplesIndexResponse(
        path=str(path or "examples-other/reference/index.md"),
        content=content,
    )


@router.get("/scripts/{script_name}/help", response_model=TesserScriptHelpResponse)
async def get_script_help(current_user: CurrentUser, script_name: str) -> Any:
    _ = current_user
    try:
        response = await get_tesser_script_help(script_name)
    except TesserRenderTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(exc),
        ) from exc

    if str(response.get("status") or "") == "error":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=response.get("error") or f"Unknown tesser script '{script_name}'",
        )

    return TesserScriptHelpResponse(
        script_name=script_name,
        help_text=response.get("help_text"),
        description=response.get("description"),
        input_schema=response.get("input_schema")
        if isinstance(response.get("input_schema"), dict)
        else {},
    )


@router.post("/scripts/{script_name}/run", response_model=TesserScriptRunResponse)
async def run_script(
    current_user: CurrentUser,
    script_name: str,
    payload: TesserScriptRunRequest,
) -> Any:
    _ = current_user
    try:
        response = await request_tesser(
            script_name=script_name,
            script_input=payload.script_input,
            room_id=payload.room_id,
            timeout_seconds=payload.timeout_seconds,
        )
    except TesserRenderTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(exc),
        ) from exc

    if str(response.get("status") or "") == "error":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=response.get("error") or f"Failed to run script '{script_name}'",
        )

    return TesserScriptRunResponse(
        request_id=response.get("request_id"),
        script_name=script_name,
        status=str(response.get("status") or "error"),
        render=response.get("render") if isinstance(response.get("render"), dict) else None,
        error=response.get("error"),
        completed_at=response.get("completed_at"),
        worker_id=response.get("worker_id"),
    )
