"""
CRUD operations for Theme bindings and resolution.

Handles user preference bindings, authored bindings, and the
specificity-based resolution cascade.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.crud_themes import get_system_default_theme, get_theme_visible_to_user
from app.models import (
    BatchResolvedThemesResponse,
    BindingType,
    EntityContext,
    ResolvedThemeResponse,
    ResolutionSource,
    Theme,
    ThemeBinding,
    ThemeCategory,
    ThemePublic,
    ThemeSlot,
)


# =============================================================================
# Slot to Category Mapping
# =============================================================================

SLOT_TO_CATEGORY: dict[ThemeSlot, ThemeCategory] = {
    ThemeSlot.page: ThemeCategory.page,
    ThemeSlot.cards: ThemeCategory.card,
    ThemeSlot.syntax: ThemeCategory.syntax,
    ThemeSlot.motion: ThemeCategory.motion,
}


# =============================================================================
# User Preference Bindings
# =============================================================================


async def get_user_bindings(
    session: AsyncSession,
    user_id: UUID,
    context_prefix: str | None = None,
) -> list[ThemeBinding]:
    """
    Get all user preference bindings for a user.

    Optionally filter by context_key prefix (e.g., "page:story" to get
    all bindings for story page and its panels).
    """
    filters = [
        ThemeBinding.binding_type == BindingType.user_pref,
        ThemeBinding.owner_id == user_id,
    ]

    if context_prefix:
        filters.append(ThemeBinding.context_key.startswith(context_prefix))

    statement = select(ThemeBinding).where(*filters)
    result = await session.exec(statement)
    return list(result.all())


async def get_user_binding(
    session: AsyncSession,
    user_id: UUID,
    context_key: str,
    slot: ThemeSlot,
) -> ThemeBinding | None:
    """Get a specific user preference binding."""
    statement = select(ThemeBinding).where(
        ThemeBinding.binding_type == BindingType.user_pref,
        ThemeBinding.owner_id == user_id,
        ThemeBinding.context_key == context_key,
        ThemeBinding.slot == slot,
    )
    result = await session.exec(statement)
    return result.one_or_none()


async def set_user_pref_binding(
    session: AsyncSession,
    user_id: UUID,
    context_key: str,
    slot: ThemeSlot,
    theme_id: UUID,
) -> ThemeBinding:
    """
    Set or update a user preference binding.

    Uses upsert pattern: updates if exists, creates if not.
    """
    existing = await get_user_binding(session, user_id, context_key, slot)

    if existing:
        existing.theme_id = theme_id
        existing.updated_at = datetime.utcnow()
        session.add(existing)
    else:
        existing = ThemeBinding(
            binding_type=BindingType.user_pref,
            owner_id=user_id,
            context_key=context_key,
            slot=slot,
            theme_id=theme_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(existing)

    await session.commit()
    await session.refresh(existing)
    return existing


async def clear_user_pref_binding(
    session: AsyncSession,
    user_id: UUID,
    context_key: str,
    slot: ThemeSlot,
) -> bool:
    """
    Clear a user preference binding.

    Returns True if a binding was deleted, False if none existed.
    """
    existing = await get_user_binding(session, user_id, context_key, slot)

    if existing:
        await session.delete(existing)
        await session.commit()
        return True

    return False


# =============================================================================
# Authored Bindings
# =============================================================================


async def get_authored_bindings(
    session: AsyncSession,
    entity_id: UUID,
    context_prefix: str | None = None,
) -> list[ThemeBinding]:
    """
    Get all authored bindings for an entity.

    The entity_id is the owner_id for authored bindings (e.g., story ID).
    """
    filters = [
        ThemeBinding.binding_type == BindingType.authored,
        ThemeBinding.owner_id == entity_id,
    ]

    if context_prefix:
        filters.append(ThemeBinding.context_key.startswith(context_prefix))

    statement = select(ThemeBinding).where(*filters)
    result = await session.exec(statement)
    return list(result.all())


async def get_authored_binding(
    session: AsyncSession,
    entity_id: UUID,
    context_key: str,
    slot: ThemeSlot,
) -> ThemeBinding | None:
    """Get a specific authored binding."""
    statement = select(ThemeBinding).where(
        ThemeBinding.binding_type == BindingType.authored,
        ThemeBinding.owner_id == entity_id,
        ThemeBinding.context_key == context_key,
        ThemeBinding.slot == slot,
    )
    result = await session.exec(statement)
    return result.one_or_none()


async def set_authored_binding(
    session: AsyncSession,
    entity_id: UUID,
    context_key: str,
    slot: ThemeSlot,
    theme_id: UUID,
) -> ThemeBinding:
    """
    Set or update an authored binding.

    Authorization (entity ownership) must be verified by caller.
    """
    existing = await get_authored_binding(session, entity_id, context_key, slot)

    if existing:
        existing.theme_id = theme_id
        existing.updated_at = datetime.utcnow()
        session.add(existing)
    else:
        existing = ThemeBinding(
            binding_type=BindingType.authored,
            owner_id=entity_id,
            context_key=context_key,
            slot=slot,
            theme_id=theme_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(existing)

    await session.commit()
    await session.refresh(existing)
    return existing


async def clear_authored_binding(
    session: AsyncSession,
    entity_id: UUID,
    context_key: str,
    slot: ThemeSlot,
) -> bool:
    """
    Clear an authored binding.

    Authorization (entity ownership) must be verified by caller.
    Returns True if a binding was deleted, False if none existed.
    """
    existing = await get_authored_binding(session, entity_id, context_key, slot)

    if existing:
        await session.delete(existing)
        await session.commit()
        return True

    return False


# =============================================================================
# Resolution Algorithm
# =============================================================================


def build_specificity_cascade(context_path: list[str]) -> list[str]:
    """
    Build context keys from most specific to least specific.

    Example:
        ["page:story", "panel:debug"] produces:
        - "page:story/panel:debug"
        - "page:story/panel:*"
        - "page:story"
        - "page:*"
        - "*"
    """
    if not context_path:
        return ["*"]

    keys = []

    # Start with full path and progressively reduce
    for length in range(len(context_path), 0, -1):
        # Exact match at this length
        exact_key = "/".join(context_path[:length])
        keys.append(exact_key)

        # Wildcard at the last segment
        if ":" in context_path[length - 1]:
            segment_type = context_path[length - 1].split(":")[0]
            wildcard_path = context_path[: length - 1] + [f"{segment_type}:*"]
            wildcard_key = "/".join(wildcard_path)
            if wildcard_key not in keys:
                keys.append(wildcard_key)

    # Global wildcard
    keys.append("*")

    return keys


async def resolve_theme(
    session: AsyncSession,
    user_id: UUID,
    context_path: list[str],
    slot: ThemeSlot,
    entity_context: EntityContext | None = None,
) -> ResolvedThemeResponse:
    """
    Resolve the effective theme for a context.

    Resolution order:
    1. Authored bindings (if entity_context provided) - most specific to least
    2. User preference bindings - most specific to least
    3. System default theme

    Returns the resolved theme with source information.
    """
    candidates = build_specificity_cascade(context_path)
    category = SLOT_TO_CATEGORY[slot]

    # Phase 1: Check authored bindings (if entity context provided)
    if entity_context:
        for key in candidates:
            binding = await get_authored_binding(
                session, entity_context.entity_id, key, slot
            )
            if binding:
                theme = await get_theme_visible_to_user(
                    session, binding.theme_id, user_id
                )
                if theme:
                    return ResolvedThemeResponse(
                        theme=ThemePublic.model_validate(theme),
                        source=ResolutionSource.authored,
                        context_key_matched=key,
                    )

    # Phase 2: Check user preference bindings
    for key in candidates:
        binding = await get_user_binding(session, user_id, key, slot)
        if binding:
            theme = await get_theme_visible_to_user(
                session, binding.theme_id, user_id
            )
            if theme:
                return ResolvedThemeResponse(
                    theme=ThemePublic.model_validate(theme),
                    source=ResolutionSource.user_pref,
                    context_key_matched=key,
                )

    # Phase 3: System default
    default_theme = await get_system_default_theme(session, category)
    if default_theme:
        return ResolvedThemeResponse(
            theme=ThemePublic.model_validate(default_theme),
            source=ResolutionSource.system_default,
            context_key_matched=None,
        )

    # No theme available
    return ResolvedThemeResponse(
        theme=None,
        source=ResolutionSource.none,
        context_key_matched=None,
    )


async def batch_resolve_themes(
    session: AsyncSession,
    user_id: UUID,
    context_path: list[str],
    slots: list[ThemeSlot],
    entity_context: EntityContext | None = None,
) -> BatchResolvedThemesResponse:
    """
    Resolve multiple theme slots in a single request.

    More efficient than multiple single resolutions when loading a page
    that needs page, cards, syntax, and motion themes.
    """
    results: dict[ThemeSlot, ResolvedThemeResponse] = {}

    for slot in slots:
        results[slot] = await resolve_theme(
            session, user_id, context_path, slot, entity_context
        )

    return BatchResolvedThemesResponse(results=results)
