import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import desc, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    PromptConfig,
    PromptConfigCommitRequest,
    PromptConfigCreate,
    PromptConfigPublic,
    PromptConfigResetWorkingCopyRequest,
    PromptConfigUpdate,
    PromptConfigValidationIssue,
    PromptConfigValidationResponse,
    PromptConfigsPublic,
    PromptConfigVersion,
    PromptConfigVersionPublic,
    PromptConfigVersionsPublic,
    PromptConfigWorkingCopy,
    PromptConfigWorkingCopyPublic,
    PromptConfigWorkingCopyUpdate,
    PromptConfigDraft,
)

router = APIRouter(prefix="/prompt-configs", tags=["prompt-configs"])


def _draft_to_json(draft: PromptConfigDraft) -> dict[str, Any]:
    return draft.model_dump(mode="json", exclude_none=True)


def _draft_from_json(payload_json: dict[str, Any]) -> PromptConfigDraft:
    return PromptConfigDraft.model_validate(payload_json)


def _require_prompt_config_access(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    prompt_config_id: uuid.UUID,
) -> PromptConfig:
    prompt_config = session.get(PromptConfig, prompt_config_id)
    if not prompt_config:
        raise HTTPException(status_code=404, detail="PromptConfig not found")
    if current_user.is_superuser:
        return prompt_config
    if prompt_config.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return prompt_config


@router.get("/", response_model=PromptConfigsPublic)
def list_prompt_configs(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> PromptConfigsPublic:
    statement = select(PromptConfig).offset(skip).limit(limit)
    if not current_user.is_superuser:
        statement = statement.where(PromptConfig.owner_id == current_user.id)
    configs = list(session.exec(statement).all())
    return PromptConfigsPublic(
        data=[PromptConfigPublic.model_validate(config) for config in configs],
        count=len(configs),
    )


@router.get("/{prompt_config_id}", response_model=PromptConfigPublic)
def get_prompt_config(
    session: SessionDep,
    current_user: CurrentUser,
    prompt_config_id: uuid.UUID,
) -> PromptConfigPublic:
    prompt_config = _require_prompt_config_access(
        session=session,
        current_user=current_user,
        prompt_config_id=prompt_config_id,
    )
    return PromptConfigPublic.model_validate(prompt_config)


@router.post("/", response_model=PromptConfigPublic)
def create_prompt_config(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    prompt_config_in: PromptConfigCreate,
) -> PromptConfigPublic:
    prompt_config = PromptConfig(
        name=prompt_config_in.name,
        description=prompt_config_in.description,
        metadata_json=prompt_config_in.metadata_json,
        is_archived=False,
        owner_id=current_user.id,
        latest_version=1,
    )
    session.add(prompt_config)
    session.flush()

    first_version = PromptConfigVersion(
        prompt_config_id=prompt_config.id,
        version_number=1,
        parent_version_id=None,
        commit_message=prompt_config_in.commit_message or "Initial version",
        payload_json=_draft_to_json(prompt_config_in.payload),
        created_by=current_user.id,
    )
    session.add(first_version)

    working_copy = PromptConfigWorkingCopy(
        prompt_config_id=prompt_config.id,
        base_version=1,
        payload_json=_draft_to_json(prompt_config_in.payload),
        has_uncommitted_changes=False,
        updated_by=current_user.id,
    )
    session.add(working_copy)

    session.commit()
    session.refresh(prompt_config)
    return PromptConfigPublic.model_validate(prompt_config)


@router.patch("/{prompt_config_id}", response_model=PromptConfigPublic)
def update_prompt_config(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    prompt_config_id: uuid.UUID,
    prompt_config_in: PromptConfigUpdate,
) -> PromptConfigPublic:
    prompt_config = _require_prompt_config_access(
        session=session,
        current_user=current_user,
        prompt_config_id=prompt_config_id,
    )
    update_data = prompt_config_in.model_dump(exclude_unset=True)
    prompt_config.sqlmodel_update(update_data)
    session.add(prompt_config)
    session.commit()
    session.refresh(prompt_config)
    return PromptConfigPublic.model_validate(prompt_config)


@router.get("/{prompt_config_id}/working-copy", response_model=PromptConfigWorkingCopyPublic)
def get_prompt_config_working_copy(
    session: SessionDep,
    current_user: CurrentUser,
    prompt_config_id: uuid.UUID,
) -> PromptConfigWorkingCopyPublic:
    _require_prompt_config_access(
        session=session,
        current_user=current_user,
        prompt_config_id=prompt_config_id,
    )
    working_copy = session.exec(
        select(PromptConfigWorkingCopy).where(PromptConfigWorkingCopy.prompt_config_id == prompt_config_id)
    ).first()
    if not working_copy:
        raise HTTPException(status_code=404, detail="Working copy not found")
    return PromptConfigWorkingCopyPublic(
        id=working_copy.id,
        prompt_config_id=working_copy.prompt_config_id,
        base_version=working_copy.base_version,
        payload=_draft_from_json(working_copy.payload_json),
        has_uncommitted_changes=working_copy.has_uncommitted_changes,
        updated_at=working_copy.updated_at,
        updated_by=working_copy.updated_by,
    )


@router.put("/{prompt_config_id}/working-copy", response_model=PromptConfigWorkingCopyPublic)
def put_prompt_config_working_copy(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    prompt_config_id: uuid.UUID,
    working_copy_in: PromptConfigWorkingCopyUpdate,
) -> PromptConfigWorkingCopyPublic:
    _require_prompt_config_access(
        session=session,
        current_user=current_user,
        prompt_config_id=prompt_config_id,
    )
    working_copy = session.exec(
        select(PromptConfigWorkingCopy).where(PromptConfigWorkingCopy.prompt_config_id == prompt_config_id)
    ).first()
    if not working_copy:
        working_copy = PromptConfigWorkingCopy(
            prompt_config_id=prompt_config_id,
            base_version=working_copy_in.base_version,
            payload_json=_draft_to_json(working_copy_in.payload),
            has_uncommitted_changes=working_copy_in.has_uncommitted_changes if working_copy_in.has_uncommitted_changes is not None else True,
            updated_by=current_user.id,
        )
    else:
        if (
            working_copy_in.base_version is not None
            and working_copy.base_version is not None
            and working_copy_in.base_version != working_copy.base_version
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Working copy base_version conflict: expected {working_copy_in.base_version}, "
                    f"current is {working_copy.base_version}. Refresh and retry."
                ),
            )
        working_copy.base_version = working_copy_in.base_version
        working_copy.payload_json = _draft_to_json(working_copy_in.payload)
        working_copy.has_uncommitted_changes = (
            working_copy_in.has_uncommitted_changes
            if working_copy_in.has_uncommitted_changes is not None
            else True
        )
        working_copy.updated_by = current_user.id

    session.add(working_copy)
    session.commit()
    session.refresh(working_copy)
    return PromptConfigWorkingCopyPublic(
        id=working_copy.id,
        prompt_config_id=working_copy.prompt_config_id,
        base_version=working_copy.base_version,
        payload=_draft_from_json(working_copy.payload_json),
        has_uncommitted_changes=working_copy.has_uncommitted_changes,
        updated_at=working_copy.updated_at,
        updated_by=working_copy.updated_by,
    )


@router.post("/{prompt_config_id}/versions", response_model=PromptConfigVersionPublic)
def commit_prompt_config_version(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    prompt_config_id: uuid.UUID,
    commit_in: PromptConfigCommitRequest,
) -> PromptConfigVersionPublic:
    prompt_config = _require_prompt_config_access(
        session=session,
        current_user=current_user,
        prompt_config_id=prompt_config_id,
    )
    working_copy = session.exec(
        select(PromptConfigWorkingCopy).where(PromptConfigWorkingCopy.prompt_config_id == prompt_config_id)
    ).first()
    if not working_copy:
        raise HTTPException(status_code=404, detail="Working copy not found")

    next_version_number = (prompt_config.latest_version or 0) + 1
    latest_version = session.exec(
        select(PromptConfigVersion)
        .where(PromptConfigVersion.prompt_config_id == prompt_config_id)
        .order_by(desc(PromptConfigVersion.version_number))
    ).first()

    version = PromptConfigVersion(
        prompt_config_id=prompt_config_id,
        version_number=next_version_number,
        parent_version_id=commit_in.parent_version_id or (latest_version.id if latest_version else None),
        commit_message=commit_in.commit_message or f"Commit version {next_version_number}",
        payload_json=working_copy.payload_json,
        created_by=current_user.id,
    )
    session.add(version)

    prompt_config.latest_version = next_version_number
    working_copy.base_version = next_version_number
    working_copy.has_uncommitted_changes = False
    working_copy.updated_by = current_user.id
    session.add(prompt_config)
    session.add(working_copy)
    session.commit()
    session.refresh(version)

    return PromptConfigVersionPublic(
        id=version.id,
        prompt_config_id=version.prompt_config_id,
        version_number=version.version_number,
        parent_version_id=version.parent_version_id,
        commit_message=version.commit_message,
        payload=_draft_from_json(version.payload_json),
        created_by=version.created_by,
        created_at=version.created_at,
    )


@router.get("/{prompt_config_id}/versions", response_model=PromptConfigVersionsPublic)
def list_prompt_config_versions(
    session: SessionDep,
    current_user: CurrentUser,
    prompt_config_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
) -> PromptConfigVersionsPublic:
    _require_prompt_config_access(
        session=session,
        current_user=current_user,
        prompt_config_id=prompt_config_id,
    )
    versions = list(
        session.exec(
            select(PromptConfigVersion)
            .where(PromptConfigVersion.prompt_config_id == prompt_config_id)
            .order_by(desc(PromptConfigVersion.version_number))
            .offset(skip)
            .limit(limit)
        ).all()
    )
    return PromptConfigVersionsPublic(
        data=[
            PromptConfigVersionPublic(
                id=version.id,
                prompt_config_id=version.prompt_config_id,
                version_number=version.version_number,
                parent_version_id=version.parent_version_id,
                commit_message=version.commit_message,
                payload=_draft_from_json(version.payload_json),
                created_by=version.created_by,
                created_at=version.created_at,
            )
            for version in versions
        ],
        count=len(versions),
    )


@router.get("/{prompt_config_id}/versions/{version_id}", response_model=PromptConfigVersionPublic)
def get_prompt_config_version(
    session: SessionDep,
    current_user: CurrentUser,
    prompt_config_id: uuid.UUID,
    version_id: uuid.UUID,
) -> PromptConfigVersionPublic:
    _require_prompt_config_access(
        session=session,
        current_user=current_user,
        prompt_config_id=prompt_config_id,
    )
    version = session.get(PromptConfigVersion, version_id)
    if not version or version.prompt_config_id != prompt_config_id:
        raise HTTPException(status_code=404, detail="Version not found")
    return PromptConfigVersionPublic(
        id=version.id,
        prompt_config_id=version.prompt_config_id,
        version_number=version.version_number,
        parent_version_id=version.parent_version_id,
        commit_message=version.commit_message,
        payload=_draft_from_json(version.payload_json),
        created_by=version.created_by,
        created_at=version.created_at,
    )


@router.post("/{prompt_config_id}/working-copy/reset", response_model=PromptConfigWorkingCopyPublic)
def reset_prompt_config_working_copy(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    prompt_config_id: uuid.UUID,
    reset_in: PromptConfigResetWorkingCopyRequest,
) -> PromptConfigWorkingCopyPublic:
    prompt_config = _require_prompt_config_access(
        session=session,
        current_user=current_user,
        prompt_config_id=prompt_config_id,
    )
    working_copy = session.exec(
        select(PromptConfigWorkingCopy).where(PromptConfigWorkingCopy.prompt_config_id == prompt_config_id)
    ).first()
    if not working_copy:
        raise HTTPException(status_code=404, detail="Working copy not found")

    target_version: PromptConfigVersion | None = None
    if reset_in.version_id:
        target_version = session.get(PromptConfigVersion, reset_in.version_id)
        if not target_version or target_version.prompt_config_id != prompt_config_id:
            raise HTTPException(status_code=404, detail="Version not found")
    else:
        target_version = session.exec(
            select(PromptConfigVersion)
            .where(PromptConfigVersion.prompt_config_id == prompt_config_id)
            .where(PromptConfigVersion.version_number == prompt_config.latest_version)
        ).first()

    if not target_version:
        raise HTTPException(status_code=404, detail="No target version available for reset")

    working_copy.payload_json = target_version.payload_json
    working_copy.base_version = target_version.version_number
    working_copy.has_uncommitted_changes = False
    working_copy.updated_by = current_user.id
    session.add(working_copy)
    session.commit()
    session.refresh(working_copy)
    return PromptConfigWorkingCopyPublic(
        id=working_copy.id,
        prompt_config_id=working_copy.prompt_config_id,
        base_version=working_copy.base_version,
        payload=_draft_from_json(working_copy.payload_json),
        has_uncommitted_changes=working_copy.has_uncommitted_changes,
        updated_at=working_copy.updated_at,
        updated_by=working_copy.updated_by,
    )


@router.post("/validate", response_model=PromptConfigValidationResponse)
def validate_prompt_config_payload(
    payload: PromptConfigDraft,
) -> PromptConfigValidationResponse:
    # Placeholder for richer server-side semantic validation rules.
    # Structural validation is already enforced through PromptConfigDraft.
    issues: list[PromptConfigValidationIssue] = []
    if payload.provider.user_access_provider_id is None:
        issues.append(
            PromptConfigValidationIssue(
                code="provider_required",
                severity="error",
                message="A user access provider is required.",
                path="provider.user_access_provider_id",
            )
        )
    if not payload.model.model_id:
        issues.append(
            PromptConfigValidationIssue(
                code="model_required",
                severity="error",
                message="A model selection is required.",
                path="model.model_id",
            )
        )
    return PromptConfigValidationResponse(issues=issues)
