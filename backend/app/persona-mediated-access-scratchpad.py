import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Any

from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, SQLModel


"""
Concrete recommended schema revision for persona-mediated collaboration.

Problem:
- Current groups and access grants are user-account mediated.
- The project/workspace vision requires collaboration to happen through
  UserPersona identity, not directly through the underlying User account.

Design goals:
1. A collaboration container is owned/managed through a UserPersona.
2. Group/workspace membership is expressed through UserPersona.
3. Grants can still be applied to groups for efficient sharing.
4. Existing project/resource grant pipeline remains recognizable.
5. Account-level access checks still resolve from the current authenticated user,
   but through the set of UserPersonas that user controls.

This is a schema/design scratchpad, not production code.
"""


# ---------------------------------------------------------------------------
# Shared enums
# ---------------------------------------------------------------------------


class CollaborationContainerType(str, PyEnum):
    GROUP = "group"
    WORKSPACE = "workspace"


class PersonaMembershipRole(str, PyEnum):
    MEMBER = "member"
    MANAGER = "manager"


class PersonaGrantSubjectType(str, PyEnum):
    USER = "user"
    USER_PERSONA = "user_persona"
    GROUP = "group"


class PersonaGrantRole(str, PyEnum):
    VIEWER = "viewer"
    EDITOR = "editor"
    MANAGER = "manager"


# ---------------------------------------------------------------------------
# Recommended replacement for UserGroup
# ---------------------------------------------------------------------------


class PersonaGroupBase(SQLModel):
    """
    Persona-mediated collaboration container.

    This replaces the semantics of a purely user-owned group.
    """

    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    container_type: CollaborationContainerType = Field(
        default=CollaborationContainerType.GROUP
    )
    is_active: bool = Field(default=True)

    metadata_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False),
        description="Non-permission metadata only.",
    )


class PersonaGroupCreate(PersonaGroupBase):
    owner_user_persona_id: uuid.UUID


class PersonaGroupUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None
    metadata_json: dict[str, Any] | None = None


class PersonaGroup(PersonaGroupBase, table=True):
    """
    Collaboration group/workspace owned through a UserPersona.
    """

    __tablename__ = "persona_groups"
    __table_args__ = (
        UniqueConstraint(
            "owner_user_persona_id",
            "name",
            name="uq_persona_groups_owner_persona_name",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_user_persona_id: uuid.UUID = Field(
        foreign_key="userpersona.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )


"""
Recommended invariants:

1. The authenticated user may create a PersonaGroup only if they own the
   `owner_user_persona_id`.
2. The owner UserPersona is the management anchor for the group/workspace.
3. For MVP, ownership transfer is out of scope.
"""


# ---------------------------------------------------------------------------
# Recommended replacement for UserGroupMembership
# ---------------------------------------------------------------------------


class PersonaGroupMembershipBase(SQLModel):
    """
    Membership in a collaboration container through a specific UserPersona.
    """

    role: PersonaMembershipRole = Field(default=PersonaMembershipRole.MEMBER)
    is_active: bool = Field(default=True)

    metadata_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False),
        description="Context metadata, not authorization logic.",
    )


class PersonaGroupMembershipCreate(PersonaGroupMembershipBase):
    user_persona_id: uuid.UUID


class PersonaGroupMembershipUpdate(SQLModel):
    role: PersonaMembershipRole | None = None
    is_active: bool | None = None
    metadata_json: dict[str, Any] | None = None


class PersonaGroupMembership(PersonaGroupMembershipBase, table=True):
    __tablename__ = "persona_group_memberships"
    __table_args__ = (
        UniqueConstraint(
            "group_id",
            "user_persona_id",
            name="uq_persona_group_memberships_group_user_persona",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    group_id: uuid.UUID = Field(
        foreign_key="persona_groups.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    user_persona_id: uuid.UUID = Field(
        foreign_key="userpersona.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )


"""
Recommended invariants:

1. Membership is persona-scoped, not user-scoped.
2. The same underlying user may join the same group through multiple personas
   only if product wants that; for MVP, prefer allowing only one persona per
   user per group via a service-layer rule.
3. The owner persona should also appear as an active manager membership, either
   explicitly persisted or implicitly synthesized.
"""


# ---------------------------------------------------------------------------
# Recommended replacement/extension for AccessGrant
# ---------------------------------------------------------------------------


class PersonaAccessGrantBase(SQLModel):
    """
    Object-scoped grant model with persona-aware subjects.
    """

    resource_type: str = Field(min_length=1, max_length=50, index=True)
    resource_id: uuid.UUID = Field(index=True)

    subject_type: PersonaGrantSubjectType
    subject_id: uuid.UUID

    role: PersonaGrantRole = Field(default=PersonaGrantRole.VIEWER)


class PersonaAccessGrantCreate(PersonaAccessGrantBase):
    pass


class PersonaAccessGrant(PersonaAccessGrantBase, table=True):
    __tablename__ = "persona_access_grants"
    __table_args__ = (
        UniqueConstraint(
            "resource_type",
            "resource_id",
            "subject_type",
            "subject_id",
            name="uq_persona_access_grants_resource_subject",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    granted_by_user_persona_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="userpersona.id",
        index=True,
        description=(
            "Persona context used to issue the grant, when applicable."
        ),
    )
    granted_by_user_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


"""
Recommended grant semantics:

1. Direct grants may target:
   - user
   - user_persona
   - group

2. For workspace/project sharing, the preferred subject is `group`.

3. `granted_by_user_persona_id` captures collaboration context.
   It should not replace `granted_by_user_id`, since authenticated ownership
   and audit still belong to the account.
"""


# ---------------------------------------------------------------------------
# Recommended project/workspace integration
# ---------------------------------------------------------------------------


"""
Recommended end-to-end pipeline:

1. User creates a UserPersona.
2. User creates a PersonaGroup using one owned UserPersona as the owner persona.
3. User adds other members by their UserPersona ids.
4. User creates a Project or Workspace as usual.
5. User grants `group` access to the project/workspace resource.
6. Access resolution for the current authenticated user proceeds through:
   - direct user grants
   - direct user_persona grants on personas they own
   - group grants for groups containing personas they own
   - project-derived grants for attached resources

This preserves the current project grant pattern while making the
collaboration identity persona-mediated.
"""


# ---------------------------------------------------------------------------
# Required access-resolution changes
# ---------------------------------------------------------------------------


"""
Recommended runtime resolution algorithm for an authenticated user:

1. Load all active UserPersona ids owned by the authenticated user.
2. Resolve grants in this order:
   - direct `user` grants
   - direct `user_persona` grants where subject_id in owned persona ids
   - `group` grants where subject_id in groups containing owned persona ids
3. For non-project resources, also consider project-derived grants using the
   same subject-resolution rules.

Important consequence:
- access is still checked against the authenticated user account
- collaboration identity is mediated by the personas that user controls

This avoids requiring a separate login/session per persona.
"""


# ---------------------------------------------------------------------------
# Migration strategy from current Phase-0 model
# ---------------------------------------------------------------------------


"""
Recommended migration path:

1. Introduce `PersonaGroup` and `PersonaGroupMembership` alongside existing
   `UserGroup` and `UserGroupMembership`.
2. Extend access grants to support `user_persona` subject_type.
3. Update access resolver to read from persona groups first, then fall back to
   legacy user groups during migration.
4. Migrate project/workspace sharing surfaces to persona groups.
5. Remove legacy user-group-only path after frontend and API migration stabilize.

For MVP, if full coexistence is too expensive, a direct replacement is also
reasonable, but the above path is lower-risk.
"""
