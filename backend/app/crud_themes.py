"""
CRUD operations for Theme registry.

Handles theme creation, retrieval, updates, and deletion with
scope-based visibility rules.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlmodel import func, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import (
    Theme,
    ThemeCategory,
    ThemeCreate,
    ThemeScope,
    ThemeUpdate,
)


async def get_theme_by_id(
    session: AsyncSession,
    theme_id: UUID,
) -> Theme | None:
    """Fetch a theme by ID."""
    return await session.get(Theme, theme_id)


async def get_theme_visible_to_user(
    session: AsyncSession,
    theme_id: UUID,
    user_id: UUID,
) -> Theme | None:
    """
    Fetch a theme by ID if visible to the user.

    Visibility rules:
    - system: visible to all
    - org/shared: visible to all org users (simplified: all authenticated users)
    - personal: visible only to owner
    """
    theme = await session.get(Theme, theme_id)
    if not theme:
        return None

    # System, org, and shared themes are visible to all authenticated users
    if theme.scope in (ThemeScope.system, ThemeScope.org, ThemeScope.shared):
        return theme

    # Personal themes only visible to owner
    if theme.scope == ThemeScope.personal and theme.owner_id == user_id:
        return theme

    return None


async def list_themes(
    session: AsyncSession,
    *,
    user_id: UUID,
    category: ThemeCategory | None = None,
    scope: ThemeScope | None = None,
    include_system: bool = True,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[Theme], int]:
    """
    List themes visible to the user with optional filters.

    Returns themes matching:
    - System themes (if include_system=True)
    - Org and shared themes (visible to all)
    - User's personal themes
    """
    # Build visibility filter
    visibility_conditions = []

    if include_system:
        visibility_conditions.append(Theme.scope == ThemeScope.system)

    # Org and shared visible to all authenticated users
    visibility_conditions.append(Theme.scope == ThemeScope.org)
    visibility_conditions.append(Theme.scope == ThemeScope.shared)

    # Personal themes only for owner
    visibility_conditions.append(
        (Theme.scope == ThemeScope.personal) & (Theme.owner_id == user_id)
    )

    filters = [or_(*visibility_conditions)]

    # Apply optional filters
    if category:
        filters.append(Theme.category == category)
    if scope:
        filters.append(Theme.scope == scope)

    statement = (
        select(Theme)
        .where(*filters)
        .order_by(Theme.is_system.desc(), Theme.name)
        .offset(skip)
        .limit(limit)
    )
    result = await session.exec(statement)
    themes = list(result.all())

    count_statement = select(func.count()).select_from(Theme).where(*filters)
    count_result = await session.exec(count_statement)
    count = count_result.one()

    return themes, count


async def list_available_themes(
    session: AsyncSession,
    user_id: UUID,
    category: ThemeCategory,
) -> list[Theme]:
    """
    List all themes available for a user to bind in a specific category.

    This is the primary query for theme pickers - returns all themes
    the user can select from for a given slot.
    """
    visibility_conditions = [
        Theme.scope == ThemeScope.system,
        Theme.scope == ThemeScope.org,
        Theme.scope == ThemeScope.shared,
        (Theme.scope == ThemeScope.personal) & (Theme.owner_id == user_id),
    ]

    statement = (
        select(Theme)
        .where(
            or_(*visibility_conditions),
            Theme.category == category,
        )
        .order_by(Theme.is_system.desc(), Theme.name)
    )
    result = await session.exec(statement)
    return list(result.all())


async def create_theme(
    session: AsyncSession,
    *,
    owner_id: UUID,
    theme_in: ThemeCreate,
) -> Theme:
    """
    Create a new user theme.

    Note: System themes are created via seed_system_themes, not this function.
    """
    theme = Theme(
        name=theme_in.name,
        description=theme_in.description,
        category=theme_in.category,
        scope=theme_in.scope,
        tokens=theme_in.tokens,
        owner_id=owner_id,
        is_system=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(theme)
    await session.commit()
    await session.refresh(theme)
    return theme


async def update_theme(
    session: AsyncSession,
    theme: Theme,
    theme_update: ThemeUpdate,
) -> Theme:
    """
    Update an existing theme.

    Constraints enforced by caller:
    - Cannot update system themes
    - Cannot change scope to/from system
    """
    update_data = theme_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(theme, key, value)

    theme.updated_at = datetime.utcnow()
    session.add(theme)
    await session.commit()
    await session.refresh(theme)
    return theme


async def delete_theme(
    session: AsyncSession,
    theme: Theme,
) -> None:
    """
    Delete a theme.

    Note: Associated bindings are cascade-deleted.
    Constraints enforced by caller:
    - Cannot delete system themes
    """
    await session.delete(theme)
    await session.commit()


async def seed_system_themes(
    session: AsyncSession,
    themes: list[dict[str, Any]],
) -> list[Theme]:
    """
    Seed system themes (called during migrations/startup).

    Each dict should contain:
    - name: str
    - description: str | None
    - category: ThemeCategory
    - tokens: dict

    Skips themes that already exist (by name + category + is_system).
    """
    created = []

    for theme_data in themes:
        # Check if system theme already exists
        statement = select(Theme).where(
            Theme.name == theme_data["name"],
            Theme.category == theme_data["category"],
            Theme.is_system == True,
        )
        result = await session.exec(statement)
        existing = result.one_or_none()

        if existing:
            continue

        theme = Theme(
            name=theme_data["name"],
            description=theme_data.get("description"),
            category=theme_data["category"],
            scope=ThemeScope.system,
            tokens=theme_data.get("tokens", {}),
            owner_id=None,
            is_system=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(theme)
        created.append(theme)

    if created:
        await session.commit()
        for theme in created:
            await session.refresh(theme)

    return created


async def get_system_default_theme(
    session: AsyncSession,
    category: ThemeCategory,
) -> Theme | None:
    """
    Get the default system theme for a category.

    Convention: The system theme named "Default" is the fallback.
    """
    statement = select(Theme).where(
        Theme.is_system == True,
        Theme.category == category,
        Theme.name == "Default",
    )
    result = await session.exec(statement)
    return result.one_or_none()
