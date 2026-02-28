import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.models import UserRepoProvisionRequest, UserRepoPublic, UserReposPublic
from app.services.user_repo_service import (
    UserRepoProvisioningError,
    user_repo_service,
)

router = APIRouter(prefix="/user-repos", tags=["user-repos"])


def _require_user_repo_access(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    repo_id: uuid.UUID,
):
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
    user_repo = _require_user_repo_access(
        session=session,
        current_user=current_user,
        repo_id=repo_id,
    )
    return UserRepoPublic.model_validate(user_repo)


@router.post("/", response_model=UserRepoPublic)
def create_user_repo(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    repo_in: UserRepoProvisionRequest,
) -> UserRepoPublic:
    user_repo = user_repo_service.create_user_repo_db_only(
        session=session,
        owner=current_user,
        display_name=repo_in.display_name,
        slug=repo_in.slug,
        description=repo_in.description,
        is_private=repo_in.is_private,
    )

    try:
        user_repo_service.ensure_user_repo_remote(
            session=session,
            user_repo=user_repo,
        )
    except UserRepoProvisioningError as exc:
        session.delete(user_repo)
        session.commit()
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    return UserRepoPublic.model_validate(user_repo)
