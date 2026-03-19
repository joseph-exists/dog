"""
API routes for Tesser script execution.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser
from app.models import (
    TesserExamplesIndexResponse,
    TesserJobStatusResponse,
    TesserScriptEnqueueRequest,
    TesserScriptEnqueueResponse,
    TesserScriptPublic,
    TesserScriptHelpResponse,
    TesserScriptRunRequest,
    TesserScriptRunResponse,
    TesserScriptsPublic,
)
from app.services.tesser_service import (
    enqueue_tesser,
    get_tesser_examples_index,
    get_tesser_job_status,
    TesserRenderTimeoutError,
    get_tesser_script_help,
    list_tesser_scripts,
    request_tesser,
)

router = APIRouter()


@router.get("/scripts", response_model=TesserScriptsPublic)
async def list_scripts(
    current_user: CurrentUser,
    format: str | None = Query(default=None),
) -> Any:
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
    if format:
        requested_format = format.strip().lower()
        scripts_payload = [
            item
            for item in scripts_payload
            if requested_format
            in {
                str(candidate).strip().lower()
                for candidate in item.get("supported_formats", [])
                if isinstance(candidate, str)
            }
        ]
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
        supported_formats=(
            list(response.get("supported_formats"))
            if isinstance(response.get("supported_formats"), list)
            else []
        ),
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


@router.post("/scripts/{script_name}/enqueue", response_model=TesserScriptEnqueueResponse)
async def enqueue_script(
    current_user: CurrentUser,
    script_name: str,
    payload: TesserScriptEnqueueRequest,
) -> Any:
    _ = current_user
    try:
        response = await enqueue_tesser(
            script_name=script_name,
            script_input=payload.script_input,
            room_id=payload.room_id,
        )
    except TesserRenderTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(exc),
        ) from exc

    if str(response.get("status") or "") == "error":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=response.get("error") or f"Failed to enqueue script '{script_name}'",
        )

    return TesserScriptEnqueueResponse(
        request_id=str(response.get("request_id") or ""),
        job_id=str(response.get("job_id") or response.get("request_id") or ""),
        script_name=script_name,
        status=str(response.get("status") or "queued"),
        runtime_profile=(
            str(response.get("runtime_profile"))
            if response.get("runtime_profile") is not None
            else None
        ),
        resolved_capabilities=(
            list(response.get("resolved_capabilities"))
            if isinstance(response.get("resolved_capabilities"), list)
            else []
        ),
        queued_at=(
            str(response.get("queued_at"))
            if response.get("queued_at") is not None
            else None
        ),
        completed_at=(
            str(response.get("completed_at"))
            if response.get("completed_at") is not None
            else None
        ),
        render=response.get("render") if isinstance(response.get("render"), dict) else None,
        error=str(response.get("error")) if response.get("error") is not None else None,
        worker_id=(
            str(response.get("worker_id"))
            if response.get("worker_id") is not None
            else None
        ),
    )


@router.get("/jobs/{job_id}", response_model=TesserJobStatusResponse)
async def get_job_status(current_user: CurrentUser, job_id: str) -> Any:
    _ = current_user
    try:
        response = await get_tesser_job_status(job_id=job_id)
    except TesserRenderTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(exc),
        ) from exc

    if str(response.get("status") or "") == "not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=response.get("error") or f"Unknown tesser job '{job_id}'",
        )

    return TesserJobStatusResponse(
        request_id=str(response.get("request_id") or ""),
        job_id=str(response.get("job_id") or job_id),
        status=str(response.get("status") or "queued"),
        script_name=(
            str(response.get("script_name"))
            if response.get("script_name") is not None
            else None
        ),
        room_id=(
            str(response.get("room_id")) if response.get("room_id") is not None else None
        ),
        runtime_profile=(
            str(response.get("runtime_profile"))
            if response.get("runtime_profile") is not None
            else None
        ),
        resolved_capabilities=(
            list(response.get("resolved_capabilities"))
            if isinstance(response.get("resolved_capabilities"), list)
            else []
        ),
        queued_at=(
            str(response.get("queued_at"))
            if response.get("queued_at") is not None
            else None
        ),
        completed_at=(
            str(response.get("completed_at"))
            if response.get("completed_at") is not None
            else None
        ),
        render=response.get("render") if isinstance(response.get("render"), dict) else None,
        error=str(response.get("error")) if response.get("error") is not None else None,
        worker_id=(
            str(response.get("worker_id"))
            if response.get("worker_id") is not None
            else None
        ),
    )
