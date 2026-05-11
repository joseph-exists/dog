from __future__ import annotations

import mimetypes
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sqlmodel import Session, select

from app.core.config import settings
from app.models import Room, RoomParticipant, ShadowRepo, User
from app.services.shadow_git import (
    CommitError,
    FileReadError,
    WriteConflictError,
    WriteValidationError,
    commit_file_mutations,
    get_head_sha,
    get_repo_remote_url,
    read_file_at_ref,
)
from app.services.shadow_service import shadow_service
from app.services.user_repo_service import (
    UserRepoFileMutation,
    UserRepoWriteConflict,
    UserRepoWriteFailed,
    UserRepoWriteNotFound,
    UserRepoWriteUnauthorized,
    UserRepoWriteValidationError,
)


RESERVED_ROOM_ARTIFACT_PATHS = {"room.json", "room_events.redis.json"}
MAX_INLINE_TEXT_BYTES = 1024 * 1024


@dataclass(frozen=True)
class RoomArtifactFileContent:
    room_id: uuid.UUID
    path: str
    ref: str
    is_binary: bool
    is_truncated: bool
    content_type: str | None
    size_bytes: int
    encoding: str | None
    content: str | None
    expected_head_sha: str | None


@dataclass(frozen=True)
class RoomArtifactCommitResult:
    room_id: uuid.UUID
    branch: str
    previous_head_sha: str | None
    new_head_sha: str
    commit_message: str
    committed_at: datetime
    changed_paths: list[str]


class RoomArtifactRepoNotReady(UserRepoWriteFailed):
    """Raised when the room artifact repo cannot be initialized yet."""


class RoomArtifactRepoService:
    """Room-scoped facade over the room shadow repository for opaque artifacts."""

    def authorize_room_artifact_access(
        self,
        *,
        session: Session,
        room_id: uuid.UUID,
        acting_user_id: uuid.UUID,
    ) -> tuple[Room, User]:
        room = session.get(Room, room_id)
        if room is None:
            raise UserRepoWriteNotFound("Room not found")

        participant = session.exec(
            select(RoomParticipant).where(
                RoomParticipant.room_id == room_id,
                RoomParticipant.participant_type == "user",
                RoomParticipant.participant_id == str(acting_user_id),
                RoomParticipant.active.is_(True),
            )
        ).first()
        if participant is None:
            raise UserRepoWriteUnauthorized("User is not an active room participant")

        actor = session.get(User, acting_user_id)
        if actor is None:
            raise UserRepoWriteUnauthorized("Actor user not found")

        return room, actor

    def ensure_room_shadow_repo(
        self,
        *,
        session: Session,
        room: Room,
        actor: User,
    ) -> ShadowRepo:
        shadow_repo = shadow_service.get_shadow_repo(
            session,
            entity_type="room",
            entity_id=room.room_id,
        )
        if shadow_repo is not None:
            return shadow_repo

        owner = session.get(User, room.creator_id) or actor
        shadow_repo = shadow_service.ensure_shadow_repo_db_only(
            session,
            owner=owner,
            entity_type="room",
            entity_id=room.room_id,
        )
        if shadow_repo is None:
            raise RoomArtifactRepoNotReady("Room shadow repos are not enabled")
        session.commit()
        session.refresh(shadow_repo)
        return shadow_repo

    def read_room_file(
        self,
        *,
        session: Session,
        room_id: uuid.UUID,
        acting_user_id: uuid.UUID,
        path: str,
        ref: str | None = None,
    ) -> RoomArtifactFileContent:
        room, actor = self.authorize_room_artifact_access(
            session=session,
            room_id=room_id,
            acting_user_id=acting_user_id,
        )
        self.ensure_room_shadow_repo(session=session, room=room, actor=actor)
        repo_path = self._repo_path(room_id)
        remote_url = self._remote_url(room_id)
        branch = settings.SHADOW_REPO_DEFAULT_BRANCH

        try:
            resolved_ref, raw_content = read_file_at_ref(
                repo_path,
                path=path,
                ref=ref,
                remote_url=remote_url,
                default_branch=branch,
            )
        except WriteValidationError as exc:
            raise UserRepoWriteValidationError(str(exc)) from exc
        except FileReadError as exc:
            raise UserRepoWriteNotFound(str(exc)) from exc

        head_sha = get_head_sha(
            repo_path,
            remote_url=remote_url,
            default_branch=branch,
        )
        content_type = mimetypes.guess_type(path)[0]
        is_truncated = len(raw_content) > MAX_INLINE_TEXT_BYTES
        try:
            content = raw_content[:MAX_INLINE_TEXT_BYTES].decode("utf-8")
            is_binary = False
            encoding = "utf-8"
        except UnicodeDecodeError:
            content = None
            is_binary = True
            encoding = None

        return RoomArtifactFileContent(
            room_id=room_id,
            path=path.strip().strip("/"),
            ref=resolved_ref,
            is_binary=is_binary,
            is_truncated=is_truncated,
            content_type=content_type,
            size_bytes=len(raw_content),
            encoding=encoding,
            content=content,
            expected_head_sha=head_sha,
        )

    def commit_room_file_changes(
        self,
        *,
        session: Session,
        room_id: uuid.UUID,
        acting_user_id: uuid.UUID,
        branch: str,
        mutations: list[UserRepoFileMutation],
        commit_message: str,
        expected_head_sha: str | None,
    ) -> RoomArtifactCommitResult:
        room, actor = self.authorize_room_artifact_access(
            session=session,
            room_id=room_id,
            acting_user_id=acting_user_id,
        )
        self.ensure_room_shadow_repo(session=session, room=room, actor=actor)

        normalized_branch = (branch or "").strip() or settings.SHADOW_REPO_DEFAULT_BRANCH
        if normalized_branch != settings.SHADOW_REPO_DEFAULT_BRANCH:
            raise UserRepoWriteValidationError(
                "Writes are only supported for branch "
                f"{settings.SHADOW_REPO_DEFAULT_BRANCH}"
            )

        parsed_mutations = [
            {
                "path": mutation.path,
                "operation": mutation.operation,
                "content": mutation.content,
            }
            for mutation in mutations
        ]
        repo_path = self._repo_path(room_id)
        remote_url = self._remote_url(room_id)

        try:
            previous_head, new_head, changed_paths = commit_file_mutations(
                repo_path,
                mutations=parsed_mutations,
                message=commit_message,
                expected_head_sha=expected_head_sha,
                author=f"room-user-{actor.id}",
                reserved_paths=RESERVED_ROOM_ARTIFACT_PATHS,
                remote_url=remote_url,
                default_branch=normalized_branch,
            )
        except WriteConflictError as exc:
            raise UserRepoWriteConflict(str(exc)) from exc
        except WriteValidationError as exc:
            raise UserRepoWriteValidationError(str(exc)) from exc
        except CommitError as exc:
            raise UserRepoWriteFailed(str(exc)) from exc

        return RoomArtifactCommitResult(
            room_id=room_id,
            branch=normalized_branch,
            previous_head_sha=previous_head,
            new_head_sha=new_head,
            commit_message=commit_message,
            committed_at=datetime.utcnow(),
            changed_paths=changed_paths,
        )

    def get_room_head_sha(
        self,
        *,
        room_id: uuid.UUID,
    ) -> str | None:
        return get_head_sha(
            self._repo_path(room_id),
            remote_url=self._remote_url(room_id),
            default_branch=settings.SHADOW_REPO_DEFAULT_BRANCH,
        )

    def _repo_path(self, room_id: uuid.UUID) -> Path:
        return shadow_service.get_entity_repo_path("room", room_id)

    def _remote_url(self, room_id: uuid.UUID) -> str | None:
        return get_repo_remote_url(
            settings.SHADOW_REPO_URL_TEMPLATE,
            "room",
            str(room_id),
        )


room_artifact_repo_service = RoomArtifactRepoService()
