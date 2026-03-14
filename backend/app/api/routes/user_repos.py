"""
User repository management API.

Provides endpoints for creating, listing, and retrieving user-visible
repositories that are provisioned in the platform's Gogs instance.
"""

import uuid
import logging

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Message,
    UserRepoCommitRequest,
    UserRepoCommitResponse,
    UserRepoFileContent,
    UserRepoImportStatus,
    UserRepoProvisionRequest,
    UserRepoPublic,
    UserRepoReadmeContent,
    UserRepoViewResponse,
    UserReposPublic,
)
from app.services.user_repo_service import (
    UserRepoFileMutation,
    UserRepoWriteConflict,
    UserRepoWriteFailed,
    UserRepoWriteNotFound,
    UserRepoWriteNotReady,
    UserRepoWriteUnauthorized,
    UserRepoWriteUnsupportedBranch,
    UserRepoWriteValidationError,
    user_repo_service,
)
from app.services.user_repo_outbox_worker import (
    cancel_user_repo_outbox_jobs,
    create_user_repo_outbox_job,
    delete_user_repo_outbox_jobs,
)
from app.services.user_repo_view_service import (
    UserRepoBackendUnavailable,
    UserRepoBranchNotFound,
    UserRepoPathError,
    UserRepoViewNotFound,
    user_repo_view_service,
)

router = APIRouter(prefix="/user-repos", tags=["user-repos"])
logger = logging.getLogger(__name__)


def _require_user_repo_access(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    repo_id: uuid.UUID,
):
    """Verify user has access to the specified repo."""
    try:
        return user_repo_view_service.authorize_user_repo_read(
            session=session,
            current_user_id=current_user.id,
            is_superuser=current_user.is_superuser,
            repo_id=repo_id,
        )
    except UserRepoViewNotFound as exc:
        raise HTTPException(status_code=404, detail="UserRepo not found") from exc


def _require_user_repo_write_access(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    repo_id: uuid.UUID,
):
    try:
        return user_repo_service.authorize_user_repo_write(
            session=session,
            current_user_id=current_user.id,
            is_superuser=current_user.is_superuser,
            repo_id=repo_id,
        )
    except (UserRepoWriteNotFound, UserRepoWriteUnauthorized) as exc:
        raise HTTPException(status_code=404, detail="UserRepo not found") from exc


def _raise_user_repo_read_error(exc: Exception) -> None:
    if isinstance(exc, UserRepoViewNotFound):
        raise HTTPException(status_code=404, detail="UserRepo not found") from exc
    if isinstance(exc, UserRepoBranchNotFound):
        raise HTTPException(
            status_code=400,
            detail={"message": "Branch not found", "error_code": "BRANCH_NOT_FOUND"},
        ) from exc
    if isinstance(exc, UserRepoPathError):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, UserRepoBackendUnavailable):
        raise HTTPException(status_code=503, detail="User repo backend unavailable") from exc
    raise exc


def _raise_user_repo_write_error(exc: Exception) -> None:
    if isinstance(exc, UserRepoWriteNotFound):
        raise HTTPException(status_code=404, detail="UserRepo not found") from exc
    if isinstance(exc, UserRepoWriteUnauthorized):
        raise HTTPException(status_code=404, detail="UserRepo not found") from exc
    if isinstance(exc, UserRepoWriteNotReady):
        raise HTTPException(
            status_code=409,
            detail={"message": str(exc), "error_code": "REPO_NOT_READY"},
        ) from exc
    if isinstance(exc, UserRepoWriteUnsupportedBranch):
        raise HTTPException(
            status_code=400,
            detail={"message": str(exc), "error_code": "BRANCH_NOT_WRITABLE"},
        ) from exc
    if isinstance(exc, UserRepoWriteConflict):
        raise HTTPException(
            status_code=409,
            detail={"message": str(exc), "error_code": "HEAD_CONFLICT"},
        ) from exc
    if isinstance(exc, UserRepoWriteValidationError):
        raise HTTPException(
            status_code=422,
            detail={"message": str(exc), "error_code": "INVALID_WRITE_REQUEST"},
        ) from exc
    if isinstance(exc, UserRepoWriteFailed):
        logger.exception("User repo write failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail={"message": "User repo write failed", "error_code": "WRITE_FAILED"},
        ) from exc
    raise exc


@router.get("/", response_model=UserReposPublic)
def list_user_repos(
    session: SessionDep,
    current_user: CurrentUser,
) -> UserReposPublic:
    """List all repositories owned by the current user."""
    repos = user_repo_service.list_user_repos_for_owner(
        session=session,
        owner_user_id=current_user.id,
    )
    return UserReposPublic(
        data=[
            user_repo_view_service.to_public_model(user_repo=repo)
            for repo in repos
        ],
        count=len(repos),
    )


@router.get("/{repo_id}", response_model=UserRepoPublic)
def get_user_repo(
    session: SessionDep,
    current_user: CurrentUser,
    repo_id: uuid.UUID,
) -> UserRepoPublic:
    """
    Get a single repository by ID.

    Use this endpoint to poll for import status after creating a repo.
    Check the `import_status` field:
    - `importing`: Still being cloned from source
    - `ready`: Successfully imported
    - `failed`: Import failed (check `import_error` for details)
    """
    user_repo = _require_user_repo_access(
        session=session,
        current_user=current_user,
        repo_id=repo_id,
    )
    return user_repo_view_service.to_public_model(user_repo=user_repo)


@router.post("/{repo_id}/cancel", response_model=UserRepoPublic)
def cancel_user_repo_import(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    repo_id: uuid.UUID,
) -> UserRepoPublic:
    user_repo = _require_user_repo_write_access(
        session=session,
        current_user=current_user,
        repo_id=repo_id,
    )

    if user_repo.import_status == UserRepoImportStatus.READY:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Ready repositories cannot be canceled.",
                "error_code": "REPO_NOT_IMPORTING",
            },
        )

    canceled_jobs = cancel_user_repo_outbox_jobs(
        session=session,
        user_repo_id=user_repo.id,
        reason="canceled_by_user",
    )
    user_repo.import_status = UserRepoImportStatus.FAILED
    user_repo.import_error = (
        f"Import canceled by user. Stopped {canceled_jobs} pending job(s)."
    )
    session.add(user_repo)
    session.commit()
    session.refresh(user_repo)
    return user_repo_view_service.to_public_model(user_repo=user_repo)


@router.delete("/{repo_id}", response_model=Message)
def delete_user_repo(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    repo_id: uuid.UUID,
) -> Message:
    user_repo = _require_user_repo_write_access(
        session=session,
        current_user=current_user,
        repo_id=repo_id,
    )

    cancel_user_repo_outbox_jobs(
        session=session,
        user_repo_id=user_repo.id,
        reason="deleted_by_user",
    )
    deleted_jobs = delete_user_repo_outbox_jobs(
        session=session,
        user_repo_id=user_repo.id,
    )

    try:
        user_repo_service.delete_user_repo_remote(user_repo=user_repo)
    except Exception:
        logger.exception(
            "User repo remote delete failed for %s/%s",
            user_repo.owner_user_id,
            user_repo.gogs_repo_name,
        )

    session.delete(user_repo)
    session.commit()
    return Message(
        message=(
            f"User repo deleted. Removed {deleted_jobs} queued import job(s)."
        )
    )


@router.post("/", response_model=UserRepoPublic, status_code=status.HTTP_202_ACCEPTED)
def create_user_repo(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    repo_in: UserRepoProvisionRequest,
) -> UserRepoPublic:
    """
    Create a new repository by importing from an external source.

    This endpoint returns immediately with status `importing`. The actual
    clone operation happens asynchronously via the outbox worker.

    Poll `GET /user-repos/{id}` to check when `import_status` becomes
    `ready` or `failed`.

    Returns:
        202 Accepted: Repository created, import queued
        422 Unprocessable Entity: Invalid source URL
    """
    # Validate the source URL early (before creating DB records)
    try:
        normalized_url = user_repo_service._normalize_source_repo_url(
            repo_in.source_repo_url
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    # Create the DB record with IMPORTING status
    user_repo = user_repo_service.create_user_repo_db_only(
        session=session,
        owner=current_user,
        display_name=repo_in.display_name
        or user_repo_service._derive_display_name_from_source_url(normalized_url),
        slug=repo_in.slug
        or user_repo_service._derive_slug_from_source_url(normalized_url),
        description=repo_in.description,
        source_repo_url=normalized_url,
        import_status=UserRepoImportStatus.IMPORTING,
        is_private=repo_in.is_private,
    )

    # Queue the async provisioning job
    create_user_repo_outbox_job(
        session=session,
        user_repo=user_repo,
        priority=100,  # Default priority
    )
    session.commit()

    return user_repo_view_service.to_public_model(user_repo=user_repo)


@router.get("/{repo_id}/tree", response_model=UserRepoViewResponse)
def get_user_repo_tree(
    session: SessionDep,
    current_user: CurrentUser,
    repo_id: uuid.UUID,
    path: str = Query(default=""),
    ref: str | None = Query(default=None),
    commit_limit: int = Query(default=10, ge=0, le=100),
) -> UserRepoViewResponse:
    _require_user_repo_access(
        session=session,
        current_user=current_user,
        repo_id=repo_id,
    )
    try:
        return user_repo_view_service.get_repo_view(
            session=session,
            repo_id=repo_id,
            path=path,
            ref=ref,
            commit_limit=commit_limit,
        )
    except (
        UserRepoViewNotFound,
        UserRepoBranchNotFound,
        UserRepoPathError,
        UserRepoBackendUnavailable,
    ) as exc:
        _raise_user_repo_read_error(exc)


@router.get("/{repo_id}/file", response_model=UserRepoFileContent)
def get_user_repo_file(
    session: SessionDep,
    current_user: CurrentUser,
    repo_id: uuid.UUID,
    path: str = Query(..., min_length=1),
    ref: str | None = Query(default=None),
) -> UserRepoFileContent:
    _require_user_repo_access(
        session=session,
        current_user=current_user,
        repo_id=repo_id,
    )
    try:
        return user_repo_view_service.get_file_content(
            session=session,
            repo_id=repo_id,
            path=path,
            ref=ref,
        )
    except (
        UserRepoViewNotFound,
        UserRepoBranchNotFound,
        UserRepoPathError,
        UserRepoBackendUnavailable,
    ) as exc:
        _raise_user_repo_read_error(exc)


@router.get("/{repo_id}/readme", response_model=UserRepoReadmeContent)
def get_user_repo_readme(
    session: SessionDep,
    current_user: CurrentUser,
    repo_id: uuid.UUID,
    ref: str | None = Query(default=None),
) -> UserRepoReadmeContent:
    _require_user_repo_access(
        session=session,
        current_user=current_user,
        repo_id=repo_id,
    )
    try:
        return user_repo_view_service.get_readme(
            session=session,
            repo_id=repo_id,
            ref=ref,
        )
    except (
        UserRepoViewNotFound,
        UserRepoBranchNotFound,
        UserRepoPathError,
        UserRepoBackendUnavailable,
    ) as exc:
        _raise_user_repo_read_error(exc)


@router.post("/{repo_id}/commits", response_model=UserRepoCommitResponse)
def commit_user_repo_changes(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    repo_id: uuid.UUID,
    commit_in: UserRepoCommitRequest,
) -> UserRepoCommitResponse:
    try:
        result = user_repo_service.commit_user_repo_changes(
            session=session,
            repo_id=repo_id,
            actor_user_id=current_user.id,
            branch=commit_in.branch,
            mutations=[
                UserRepoFileMutation(
                    path=mutation.path,
                    operation=mutation.operation,
                    content=mutation.content,
                    encoding=mutation.encoding,
                )
                for mutation in commit_in.mutations
            ],
            commit_message=commit_in.commit_message,
            expected_head_sha=commit_in.expected_head_sha,
            is_superuser=current_user.is_superuser,
        )
    except (
        UserRepoWriteNotFound,
        UserRepoWriteUnauthorized,
        UserRepoWriteNotReady,
        UserRepoWriteUnsupportedBranch,
        UserRepoWriteConflict,
        UserRepoWriteValidationError,
        UserRepoWriteFailed,
    ) as exc:
        _raise_user_repo_write_error(exc)

    return UserRepoCommitResponse(
        repo_id=result.repo_id,
        branch=result.branch,
        previous_head_sha=result.previous_head_sha,
        new_head_sha=result.new_head_sha,
        commit_message=result.commit_message,
        committed_at=result.committed_at,
        changed_paths=result.changed_paths,
    )
