"""
Pydantic schemas for API and event payloads.

These are non-database models used for:
- API request/response validation
- Event payloads
- Agent UI components (AG-UI)
"""

from app.schemas.ag_ui import (
    AgentUIResponse,
    UIActionButton,
    UIActionButtons,
    UIAlert,
    UICard,
    UICodeBlock,
    UICollapsible,
    UIComponent,
    UIComponentType,
    UIDivider,
    UIList,
    UIListItem,
    UIProgress,
    UIProgressItem,
    UIQuote,
    UITable,
    UITableColumn,
    UITabs,
    make_action_buttons,
    make_alert,
    make_card,
    make_list,
    make_quote,
)

__all__ = [
    # Response wrapper
    "AgentUIResponse",
    # Component wrapper
    "UIComponent",
    "UIComponentType",
    # Component data types
    "UICard",
    "UIList",
    "UIListItem",
    "UITable",
    "UITableColumn",
    "UIProgress",
    "UIProgressItem",
    "UIActionButtons",
    "UIActionButton",
    "UICodeBlock",
    "UIQuote",
    "UIAlert",
    "UICollapsible",
    "UITabs",
    "UIDivider",
    # Helper functions
    "make_card",
    "make_alert",
    "make_list",
    "make_action_buttons",
    "make_quote",
]
