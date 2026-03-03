"""
User repository management API.

Provides endpoints for creating, listing, and retrieving user-visible
repositories that are provisioned in the platform's Gogs instance.
"""

import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    UserRepoImportStatus,
    UserRepoProvisionRequest,
    UserRepoPublic,
    UserReposPublic,
)
from app.services.user_repo_service import user_repo_service
from app.services.user_repo_outbox_worker import create_user_repo_outbox_job

router = APIRouter(prefix="/user-repos", tags=["user-repos"])


def _require_user_repo_access(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    repo_id: uuid.UUID,
):
    """Verify user has access to the specified repo."""
    user_repo = user_repo_service.get_user_repo(session=session, repo_id=repo_id)
    if not user_repo:
        raise HTTPException(status_code=404, detail="UserRepo not found")
    if not current_user.is_superuser and user_repo.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return user_repo


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
        data=[UserRepoPublic.model_validate(repo) for repo in repos],
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
    return UserRepoPublic.model_validate(user_repo)


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

    return UserRepoPublic.model_validate(user_repo)
