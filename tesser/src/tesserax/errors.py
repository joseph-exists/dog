from __future__ import annotations


class RenderError(Exception):
    """Base class for render pipeline errors."""


class RenderConfigError(RenderError):
    """Raised when render configuration is invalid."""


class RenderExportError(RenderError):
    """Raised when export/output policy fails."""


class RenderDependencyError(RenderError):
    """Raised when optional export dependencies are unavailable."""


def actionable_error(
    *,
    parameter: str,
    invalid_value: object,
    allowed: str,
    suggested_fix: str,
) -> str:
    return (
        f"parameter='{parameter}' invalid_value={invalid_value!r}. "
        f"allowed={allowed}. suggested_fix={suggested_fix}"
    )
