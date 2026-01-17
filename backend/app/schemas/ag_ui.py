"""
AG-UI: Agent-Generated UI Components

This module defines the schema for structured UI components that agents can emit
alongside their text responses. These enable rich, interactive experiences where
agents don't just respond with text, but with actionable UI elements.

Design Philosophy:
- Components are declarative (describe WHAT to render, not HOW)
- Frontend interprets components and renders with appropriate styling
- Graceful degradation: if frontend doesn't support a component, show text fallback
- Extensible: new component types can be added without breaking existing code

Usage:
    from app.schemas.ag_ui import UICard, UIComponent, AgentUIResponse

    # Agent emits structured response
    response = AgentUIResponse(
        content="Here's your character analysis:",
        ui_components=[
            UIComponent(
                type="card",
                data=UICard(
                    title="Character: Elena",
                    subtitle="Protagonist",
                    body="A determined scientist...",
                    variant="highlight",
                ).model_dump(),
            )
        ],
    )
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# =============================================================================
# Component Data Schemas
# =============================================================================


class UICard(BaseModel):
    """
    A card component for highlighting information.

    Use for: character profiles, story summaries, important notes, warnings.
    """

    title: str = Field(..., description="Card title/heading")
    subtitle: str | None = Field(default=None, description="Optional subtitle")
    body: str = Field(..., description="Main card content (supports markdown)")
    footer: str | None = Field(default=None, description="Optional footer text")
    variant: Literal["default", "highlight", "warning", "success", "info"] = Field(
        default="default",
        description="Visual style variant",
    )
    icon: str | None = Field(default=None, description="Optional icon name (e.g., 'user', 'book', 'alert')")


class UIListItem(BaseModel):
    """A single item in a list component."""

    label: str = Field(..., description="Item label/title")
    description: str | None = Field(default=None, description="Optional description")
    icon: str | None = Field(default=None, description="Optional icon")
    badge: str | None = Field(default=None, description="Optional badge/tag text")
    badge_variant: Literal["default", "success", "warning", "error"] | None = None


class UIList(BaseModel):
    """
    A list component for displaying multiple items.

    Use for: character lists, plot points, scene breakdowns, suggestions.
    """

    title: str | None = Field(default=None, description="Optional list title")
    items: list[UIListItem] = Field(..., description="List items")
    ordered: bool = Field(default=False, description="Whether to show as numbered list")
    variant: Literal["default", "compact", "detailed"] = Field(default="default")


class UITableColumn(BaseModel):
    """Column definition for a table."""

    key: str = Field(..., description="Data key for this column")
    header: str = Field(..., description="Column header text")
    align: Literal["left", "center", "right"] = Field(default="left")


class UITable(BaseModel):
    """
    A table component for structured data display.

    Use for: character comparisons, scene timelines, trait matrices.
    """

    title: str | None = Field(default=None, description="Optional table title")
    columns: list[UITableColumn] = Field(..., description="Column definitions")
    rows: list[dict[str, Any]] = Field(..., description="Row data (key-value pairs)")
    striped: bool = Field(default=True, description="Alternate row colors")
    compact: bool = Field(default=False, description="Use compact spacing")


class UIProgressItem(BaseModel):
    """A single progress indicator."""

    label: str = Field(..., description="Progress item label")
    value: int = Field(..., ge=0, le=100, description="Progress percentage (0-100)")
    color: Literal["blue", "green", "yellow", "red", "purple"] = Field(default="blue")


class UIProgress(BaseModel):
    """
    Progress indicators for showing completion or metrics.

    Use for: story completion, character development arcs, pacing analysis.
    """

    title: str | None = Field(default=None, description="Optional section title")
    items: list[UIProgressItem] = Field(..., description="Progress items")
    show_percentage: bool = Field(default=True, description="Show percentage labels")


class UIActionButton(BaseModel):
    """A single action button."""

    label: str = Field(..., description="Button text")
    action: str = Field(..., description="Action identifier (e.g., 'expand_character', 'generate_dialogue')")
    variant: Literal["primary", "secondary", "outline", "ghost"] = Field(default="secondary")
    icon: str | None = Field(default=None, description="Optional button icon")
    disabled: bool = Field(default=False)


class UIActionButtons(BaseModel):
    """
    Action buttons for user interaction.

    Use for: offering next steps, providing options, enabling agent re-invocation.
    """

    buttons: list[UIActionButton] = Field(..., description="Action buttons")
    layout: Literal["horizontal", "vertical", "grid"] = Field(default="horizontal")


class UICodeBlock(BaseModel):
    """
    A code or formatted text block.

    Use for: dialogue formatting, script excerpts, technical content.
    """

    code: str = Field(..., description="Code/text content")
    language: str | None = Field(default=None, description="Language for syntax highlighting")
    title: str | None = Field(default=None, description="Optional title/filename")
    line_numbers: bool = Field(default=False, description="Show line numbers")


class UIQuote(BaseModel):
    """
    A blockquote for highlighted text or dialogue.

    Use for: character quotes, story excerpts, important passages.
    """

    text: str = Field(..., description="Quote text")
    attribution: str | None = Field(default=None, description="Who said it / source")
    variant: Literal["default", "highlight", "subtle"] = Field(default="default")


class UIAlert(BaseModel):
    """
    An alert/notice component.

    Use for: warnings, tips, important information, errors.
    """

    title: str | None = Field(default=None, description="Alert title")
    message: str = Field(..., description="Alert message")
    variant: Literal["info", "success", "warning", "error"] = Field(default="info")
    dismissible: bool = Field(default=False)


class UICollapsible(BaseModel):
    """
    Collapsible/accordion content section.

    Use for: optional details, spoilers, expanded explanations.
    """

    title: str = Field(..., description="Collapsed header text")
    content: str = Field(..., description="Expandable content (markdown)")
    default_open: bool = Field(default=False)
    icon: str | None = Field(default=None)


class UITabs(BaseModel):
    """
    Tabbed content for organizing multiple sections.

    Use for: multiple character profiles, alternative suggestions, categorized content.
    """

    tabs: list[dict[str, str]] = Field(
        ...,
        description="List of {label: str, content: str} tab definitions",
    )
    default_tab: int = Field(default=0, description="Index of default active tab")


class UIDivider(BaseModel):
    """
    A visual divider/separator.

    Use for: separating sections, creating visual breaks.
    """

    label: str | None = Field(default=None, description="Optional center label")
    variant: Literal["solid", "dashed", "dotted"] = Field(default="solid")


# =============================================================================
# Component Type Enum and Union
# =============================================================================

UIComponentType = Literal[
    "card",
    "list",
    "table",
    "progress",
    "action_buttons",
    "code",
    "quote",
    "alert",
    "collapsible",
    "tabs",
    "divider",
]


# =============================================================================
# Main Component Wrapper
# =============================================================================


class UIComponent(BaseModel):
    """
    A single UI component that can be emitted by an agent.

    The `type` field determines how `data` should be interpreted.
    Frontend uses `type` to select the appropriate renderer.
    """

    type: UIComponentType = Field(..., description="Component type identifier")
    data: dict[str, Any] = Field(..., description="Component-specific data")
    id: str | None = Field(default=None, description="Optional unique ID for targeting")
    fallback_text: str | None = Field(
        default=None,
        description="Text to show if component type isn't supported",
    )


# =============================================================================
# Agent Response with UI Components
# =============================================================================


class AgentUIResponse(BaseModel):
    """
    Complete agent response with optional UI components.

    This is the structure agents can use to return rich responses.
    The `content` field contains the text response (always required).
    The `ui_components` field contains optional structured UI elements.
    """

    content: str = Field(..., description="Text response content (markdown supported)")
    ui_components: list[UIComponent] = Field(
        default_factory=list,
        description="Optional UI components to render",
    )

    def has_ui(self) -> bool:
        """Check if response includes UI components."""
        return len(self.ui_components) > 0


# =============================================================================
# Helper Functions for Creating Components
# =============================================================================


def make_card(
    title: str,
    body: str,
    *,
    subtitle: str | None = None,
    variant: str = "default",
    icon: str | None = None,
) -> UIComponent:
    """Quick helper to create a card component."""
    return UIComponent(
        type="card",
        data=UICard(
            title=title,
            body=body,
            subtitle=subtitle,
            variant=variant,  # type: ignore
            icon=icon,
        ).model_dump(),
    )


def make_alert(
    message: str,
    *,
    title: str | None = None,
    variant: str = "info",
) -> UIComponent:
    """Quick helper to create an alert component."""
    return UIComponent(
        type="alert",
        data=UIAlert(
            message=message,
            title=title,
            variant=variant,  # type: ignore
        ).model_dump(),
    )


def make_list(
    items: list[str | dict],
    *,
    title: str | None = None,
    ordered: bool = False,
) -> UIComponent:
    """Quick helper to create a list component from strings or dicts."""
    list_items = []
    for item in items:
        if isinstance(item, str):
            list_items.append(UIListItem(label=item))
        else:
            list_items.append(UIListItem(**item))

    return UIComponent(
        type="list",
        data=UIList(
            title=title,
            items=list_items,
            ordered=ordered,
        ).model_dump(),
    )


def make_action_buttons(
    *buttons: tuple[str, str],
    layout: str = "horizontal",
) -> UIComponent:
    """
    Quick helper to create action buttons.

    Args:
        *buttons: Tuples of (label, action) pairs
        layout: Button layout style

    Example:
        make_action_buttons(
            ("Expand", "expand_section"),
            ("Generate More", "regenerate"),
        )
    """
    return UIComponent(
        type="action_buttons",
        data=UIActionButtons(
            buttons=[
                UIActionButton(label=label, action=action) for label, action in buttons
            ],
            layout=layout,  # type: ignore
        ).model_dump(),
    )


def make_quote(
    text: str,
    *,
    attribution: str | None = None,
    variant: str = "default",
) -> UIComponent:
    """Quick helper to create a quote component."""
    return UIComponent(
        type="quote",
        data=UIQuote(
            text=text,
            attribution=attribution,
            variant=variant,  # type: ignore
        ).model_dump(),
    )
