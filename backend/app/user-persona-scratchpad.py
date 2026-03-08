 import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Any

from sqlalchemy import JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, SQLModel


"""
Concrete recommendation for MVP persona data modeling.

This file is a schema/design scratchpad, not production code.

Goals locked in:

1. A UserPersona is always derived from an upstream Persona.
2. Persona visibility must be explicit:
   - private: owned by one user; only that user may derive UserPersonas from it
   - system: published/global; any user may derive UserPersonas from it
3. presentation_json is visual presentation-as-data only.
   It is not audience resolution, permissioning, or segmentation state.
4. Vouch is out of scope for MVP.
5. We will not build private -> system migration for MVP.

Recommended model split:

- Persona:
  canonical upstream archetypal/persona definition with explicit visibility
- UserPersona:
  user-owned derived persona state used across user-facing surfaces
- UserPersonaPresentation:
  audience-specific authored presentation of a UserPersona

This split keeps identity/state separate from audience-facing presentation.
"""


# ---------------------------------------------------------------------------
# Shared enums (all migrated to models.py)
# ---------------------------------------------------------------------------


class PersonaVisibility(str, PyEnum):
    PRIVATE = "private"
    SYSTEM = "system"


class UserPersonaPublicationState(str, PyEnum):
    DRAFT = "draft"
    PUBLISHED = "published"


class AudienceScope(str, PyEnum):
    PUBLIC = "public"
    TRUSTED = "trusted"
    COLLABORATORS = "collaborators"
    CUSTOM = "custom"


class PresentationPublicationState(str, PyEnum):
    DRAFT = "draft"
    PUBLISHED = "published"


# ---------------------------------------------------------------------------
# Recommended Persona extension (added to )
# ---------------------------------------------------------------------------


class PersonaBaseRecommended(SQLModel):
    """
    Recommended extension to the upstream Persona model.

    Intent:
    - system personas are globally available and effectively immutable for MVP
    - private personas are owner-scoped and not globally published
    """

    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)
    long_description: str | None = Field(default=None)
    general_domain: str | None = Field(default=None, max_length=255)
    specific_domain: str | None = Field(default=None, max_length=255)
    general_domain_high: str | None = Field(default=None, max_length=255)
    specific_domain_high: str | None = Field(default=None, max_length=255)

    visibility: PersonaVisibility = Field(default=PersonaVisibility.PRIVATE)
    owner_user_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="user.id",
        description=(
            "Required when visibility=private. Null for system personas."
        ),
    )


"""
Recommended Persona invariants:

1. If visibility=private:
   - owner_user_id is required
   - only owner_user_id may create UserPersona rows derived from this Persona
   - persona is excluded from global listing surfaces

2. If visibility=system:
   - owner_user_id is null
   - persona may be listed in global library/catalog surfaces
   - any user may create a derived UserPersona from it

3. MVP does not support converting private personas into system personas.
"""


# ---------------------------------------------------------------------------
# Recommended UserPersona model
# ---------------------------------------------------------------------------


class UserPersonaBaseRecommended(SQLModel):
    """
    User-owned derived state.

    This is the product model that should replace page-JSON as the source of truth
    for authored persona identity/state on user pages.
    """

    nickname: str | None = Field(default=None, max_length=255)
    description: str | None = Field(
        default=None,
        max_length=255,
        description="Short user-authored summary for this derived persona.",
    )
    short_bio: str | None = Field(default=None, max_length=500)
    long_bio: str | None = Field(default=None)

    tags_json: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False),
        description=(
            "Weighted tags. Example: "
            '[{"id":"systems-0","label":"systems","weight":0.8,"source":"user"}]'
        ),
    )

    publication_state: UserPersonaPublicationState = Field(
        default=UserPersonaPublicationState.DRAFT
    )
    is_primary: bool = Field(default=False)
    is_active: bool = Field(default=True)
    sort_order: int = Field(default=0, ge=0)

    presentation_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False),
        description=(
            "Visual presentation-as-data for this UserPersona. "
            "Not audience resolution, permissioning, or segmentation."
        ),
    )


class UserPersonaCreateRecommended(UserPersonaBaseRecommended):
    persona_id: uuid.UUID


class UserPersonaUpdateRecommended(SQLModel):
    nickname: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=255)
    short_bio: str | None = Field(default=None, max_length=500)
    long_bio: str | None = Field(default=None)
    tags_json: list[dict[str, Any]] | None = None
    publication_state: UserPersonaPublicationState | None = None
    is_primary: bool | None = None
    is_active: bool | None = None
    sort_order: int | None = Field(default=None, ge=0)
    presentation_json: dict[str, Any] | None = None


class UserPersonaRecommended(UserPersonaBaseRecommended, table=True):
    """
    Recommended replacement for the current thin UserPersona join model.

    This remains derived from Persona by design.
    """

    __tablename__ = "userpersona"
    __table_args__ = (
        UniqueConstraint("user_id", "persona_id", name="uq_userpersona_user_persona"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        ondelete="CASCADE",
    )
    persona_id: uuid.UUID = Field(
        foreign_key="persona.id",
        nullable=False,
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )


"""
Recommended UserPersona invariants:

1. UserPersona is the source of truth for:
   - nickname
   - derived bios/description
   - tags
   - publication state
   - primary designation
   - visual presentation defaults

2. Enforce at most one primary UserPersona per user.
   Recommended implementation:
   - partial unique index on (user_id) where is_primary = true
   If partial indexes are awkward in SQLModel migration flow, enforce in service
   layer first and add index in alembic.

3. Service-layer create validation:
   - if Persona.visibility == private, require Persona.owner_user_id == current_user.id
   - if Persona.visibility == system, allow derivation by any user

4. Current page blocks should stop persisting full persona records as source of truth.
   Page blocks should reference UserPersona ids and render backend-owned state.
"""


# ---------------------------------------------------------------------------
# Recommended UserPersonaPresentation model
# ---------------------------------------------------------------------------


class UserPersonaPresentationBaseRecommended(SQLModel):
    """
    Audience-specific presentation of a UserPersona.

    This is where audience-facing framing belongs.
    It is intentionally separate from UserPersona.presentation_json.
    """

    audience_scope: AudienceScope = Field(default=AudienceScope.PUBLIC)
    audience_key: str | None = Field(
        default=None,
        max_length=255,
        description=(
            "Optional identifier for custom/manual audience grouping. "
            "Null for standard scopes."
        ),
    )
    audience_label: str = Field(min_length=1, max_length=255)

    headline: str = Field(min_length=1, max_length=255)
    framing_text: str | None = Field(default=None)

    visible_work_ids_json: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False),
        description=(
            "Interim work references exposed to this audience presentation."
        ),
    )

    relation_call_to_action: str = Field(
        default="none",
        max_length=64,
        description=(
            "UI affordance only. Example values: none, request_contact, "
            "invite_collaboration, follow_work."
        ),
    )

    publication_state: PresentationPublicationState = Field(
        default=PresentationPublicationState.DRAFT
    )

    presentation_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False),
        description=(
            "Visual presentation-as-data for this audience-specific presentation."
        ),
    )


class UserPersonaPresentationCreateRecommended(
    UserPersonaPresentationBaseRecommended
):
    user_persona_id: uuid.UUID


class UserPersonaPresentationUpdateRecommended(SQLModel):
    audience_scope: AudienceScope | None = None
    audience_key: str | None = Field(default=None, max_length=255)
    audience_label: str | None = Field(default=None, min_length=1, max_length=255)
    headline: str | None = Field(default=None, min_length=1, max_length=255)
    framing_text: str | None = None
    visible_work_ids_json: list[str] | None = None
    relation_call_to_action: str | None = Field(default=None, max_length=64)
    publication_state: PresentationPublicationState | None = None
    presentation_json: dict[str, Any] | None = None


class UserPersonaPresentationRecommended(
    UserPersonaPresentationBaseRecommended, table=True
):
    __tablename__ = "userpersonapresentation"
    __table_args__ = (
        UniqueConstraint(
            "user_persona_id",
            "audience_scope",
            "audience_key",
            name="uq_userpersona_presentation_audience",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_persona_id: uuid.UUID = Field(
        foreign_key="userpersona.id",
        nullable=False,
        ondelete="CASCADE",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )


"""
Recommended UserPersonaPresentation invariants:

1. One UserPersona may have many presentations.
2. Each presentation targets exactly one audience scope (+ optional audience_key).
3. publication_state is per presentation, not folded into UserPersona.
4. presentation_json remains visual only.
"""


# ---------------------------------------------------------------------------
# MVP product recommendation
# ---------------------------------------------------------------------------


"""
Recommended MVP decisions:

1. Build Persona visibility now.
   - Add Persona.visibility and Persona.owner_user_id
   - Private personas are not globally listable
   - System personas are globally listable

2. Expand UserPersona now.
   - Move authored user-page persona metadata out of page JSON
   - Keep Persona -> UserPersona derivation intact

3. Build UserPersonaPresentation now.
   - This is the missing contract for audience-facing persona presentation
   - Keep it separate from visual theming/presentation_json

4. Keep audience resolution simple for MVP.
   Recommended minimum:
   - fully support PUBLIC at runtime
   - allow authoring of other scopes if needed, but do not claim full automated
     segmentation until the audience-resolution model exists

5. Do not implement private -> system promotion for MVP.
   - Treat that as a later admin/publication workflow
"""


# ---------------------------------------------------------------------------
# Required service-layer rules
# ---------------------------------------------------------------------------


"""
Minimum service/API rules implied by this recommendation:

- create Persona:
  - default to visibility=private for user-authored personas unless explicitly
    created as system by privileged/admin workflow

- list Personas for global picker/catalog:
  - return only system personas

- list Personas for owner derivation:
  - return system personas plus owner's private personas

- create UserPersona:
  - validate Persona visibility and ownership rules

- update UserPersona:
  - if setting is_primary=true, unset any existing primary persona for that user
    inside one transaction

- read visitor-facing user page view model:
  - load UserPersona rows
  - load UserPersonaPresentation rows
  - choose presentation by resolved audience scope
  - render only published UserPersona + published UserPersonaPresentation state
"""
