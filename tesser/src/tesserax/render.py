from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Literal

from .canvas import Canvas
from .errors import (
    RenderConfigError,
    RenderDependencyError,
    RenderExportError,
    actionable_error,
)

type RenderFormat = Literal["svg", "png", "pdf", "ps", "gif", "mp4"]

_STATIC_FORMATS = {"svg", "png", "pdf", "ps"}
_ANIMATION_FORMATS = {"gif", "mp4"}
_SUPPORTED_FORMATS = _STATIC_FORMATS | _ANIMATION_FORMATS


@dataclass(slots=True)
class RenderLifecycleHooks:
    before_play: Callable[[object, "RenderConfig"], None] | None = None
    after_frame: Callable[[int, int, "RenderConfig"], None] | None = None
    before_save: Callable[[Path, object, "RenderConfig"], None] | None = None
    after_save: Callable[["RenderResult", "RenderConfig"], None] | None = None


@dataclass(slots=True)
class TimingSpec:
    fps: int | None = None
    duration: float | None = None
    seed: int | None = None

    def validate(self) -> None:
        if self.fps is not None and self.fps <= 0:
            raise RenderConfigError(
                actionable_error(
                    parameter="timing.fps",
                    invalid_value=self.fps,
                    allowed="positive integer (> 0)",
                    suggested_fix="Set timing.fps to a value > 0, e.g. 24.",
                )
            )
        if self.duration is not None and self.duration <= 0:
            raise RenderConfigError(
                actionable_error(
                    parameter="timing.duration",
                    invalid_value=self.duration,
                    allowed="positive float (> 0)",
                    suggested_fix="Set timing.duration to a value > 0, e.g. 1.0.",
                )
            )


@dataclass(slots=True)
class ViewportSpec:
    width: float | None = None
    height: float | None = None
    fit_padding: float | None = None
    fit_crop: bool = False

    def validate(self) -> None:
        if self.width is not None and self.width <= 0:
            raise RenderConfigError(
                actionable_error(
                    parameter="viewport.width",
                    invalid_value=self.width,
                    allowed="positive float (> 0)",
                    suggested_fix="Set viewport.width to a value > 0 or omit it.",
                )
            )
        if self.height is not None and self.height <= 0:
            raise RenderConfigError(
                actionable_error(
                    parameter="viewport.height",
                    invalid_value=self.height,
                    allowed="positive float (> 0)",
                    suggested_fix="Set viewport.height to a value > 0 or omit it.",
                )
            )
        if self.fit_padding is not None and self.fit_padding < 0:
            raise RenderConfigError(
                actionable_error(
                    parameter="viewport.fit_padding",
                    invalid_value=self.fit_padding,
                    allowed="float (>= 0)",
                    suggested_fix="Set viewport.fit_padding to 0 or greater, or omit it.",
                )
            )


@dataclass(slots=True)
class RenderConfig:
    """Stable configuration for static and animated render output."""

    output_path: str | Path
    format: RenderFormat = "svg"
    overwrite: bool = True
    create_parents: bool = True
    fit_padding: float | None = None
    fit_crop: bool = False
    dpi: int = 300
    timing: TimingSpec | None = None
    viewport: ViewportSpec | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    report_json_path: str | Path | None = None
    report_hook: Callable[["RenderResult"], None] | None = None
    lifecycle_hooks: RenderLifecycleHooks | None = None

    @classmethod
    def from_args(
        cls,
        args: Any,
        *,
        default_format: RenderFormat = "svg",
        output_attr: str = "output",
        format_attr: str = "format",
    ) -> "RenderConfig":
        output = getattr(args, output_attr, None)
        if output is None:
            raise RenderConfigError(
                actionable_error(
                    parameter=output_attr,
                    invalid_value=None,
                    allowed="non-empty output path",
                    suggested_fix=f"Provide --{output_attr.replace('_', '-')} <path> in CLI args.",
                )
            )
        fmt = getattr(args, format_attr, default_format)

        timing = TimingSpec(
            fps=getattr(args, "fps", None),
            duration=getattr(args, "duration", None),
            seed=getattr(args, "seed", None),
        )
        viewport = ViewportSpec(
            width=getattr(args, "width", getattr(args, "world_width", None)),
            height=getattr(args, "height", getattr(args, "world_height", None)),
        )
        if timing.fps is None and timing.duration is None and timing.seed is None:
            timing = None
        if (
            viewport.width is None
            and viewport.height is None
            and viewport.fit_padding is None
            and viewport.fit_crop is False
        ):
            viewport = None

        report_json_path = getattr(args, "report_json", None)
        return cls(
            output_path=output,
            format=fmt,
            timing=timing,
            viewport=viewport,
            report_json_path=report_json_path,
        )

    def validate(self) -> None:
        if self.format not in _SUPPORTED_FORMATS:
            allowed = ", ".join(sorted(_SUPPORTED_FORMATS))
            raise RenderConfigError(
                actionable_error(
                    parameter="format",
                    invalid_value=self.format,
                    allowed=allowed,
                    suggested_fix=f"Set format to one of: {allowed}.",
                )
            )

        if self.dpi <= 0:
            raise RenderConfigError(
                actionable_error(
                    parameter="dpi",
                    invalid_value=self.dpi,
                    allowed="positive integer (> 0)",
                    suggested_fix="Set dpi to a value > 0, e.g. 300.",
                )
            )

        if self.fit_padding is not None and self.fit_padding < 0:
            raise RenderConfigError(
                actionable_error(
                    parameter="fit_padding",
                    invalid_value=self.fit_padding,
                    allowed="float (>= 0)",
                    suggested_fix="Set fit_padding to 0 or greater, or omit it.",
                )
            )

        if self.timing is not None:
            self.timing.validate()
        if self.viewport is not None:
            self.viewport.validate()


@dataclass(slots=True)
class RenderResult:
    output_path: Path
    format: RenderFormat
    frame_count: int | None = None
    duration: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    report_path: Path | None = None


def _normalized_output_path(config: RenderConfig) -> Path:
    path = Path(config.output_path)
    suffix = f".{config.format}"

    if path.suffix.lower() != suffix:
        path = path.with_suffix(suffix)

    if not path.parent.exists():
        if config.create_parents:
            path.parent.mkdir(parents=True, exist_ok=True)
        else:
            raise RenderExportError(
                actionable_error(
                    parameter="create_parents",
                    invalid_value=config.create_parents,
                    allowed=f"True, or an existing parent directory ({path.parent})",
                    suggested_fix="Set create_parents=True or choose an existing parent path.",
                )
            )

    if path.exists() and not config.overwrite:
        raise RenderExportError(
            actionable_error(
                parameter="overwrite",
                invalid_value=config.overwrite,
                allowed=f"True when output file already exists ({path})",
                suggested_fix="Set overwrite=True or choose a different output path.",
            )
        )

    return path


def _apply_timing(target: object, config: RenderConfig) -> None:
    if config.timing is None:
        return
    if config.timing.fps is None:
        return
    if hasattr(target, "fps"):
        setattr(target, "fps", config.timing.fps)


def _apply_viewport(canvas: Canvas, config: RenderConfig) -> None:
    viewport = config.viewport
    if viewport is not None:
        if viewport.width is not None:
            canvas.width = viewport.width
        if viewport.height is not None:
            canvas.height = viewport.height
        fit_padding = viewport.fit_padding
        fit_crop = viewport.fit_crop
    else:
        fit_padding = None
        fit_crop = False

    # Backward-compatible config fields remain valid and apply when viewport
    # fit options are not provided.
    if fit_padding is None:
        fit_padding = config.fit_padding
        fit_crop = config.fit_crop

    if fit_padding is not None:
        canvas.fit(padding=fit_padding, crop=fit_crop)


def _result_telemetry(target: object, config: RenderConfig) -> tuple[int | None, float | None]:
    if isinstance(target, Canvas):
        return 1, 0.0

    frame_count: int | None = None
    frames = getattr(target, "_frames", None)
    if isinstance(frames, list):
        frame_count = len(frames)

    effective_fps: float | None = None
    if config.timing is not None and config.timing.fps is not None:
        effective_fps = float(config.timing.fps)
    else:
        fps_value = getattr(target, "fps", None)
        if isinstance(fps_value, (int, float)) and fps_value > 0:
            effective_fps = float(fps_value)

    duration: float | None = None
    if frame_count is not None and effective_fps is not None and effective_fps > 0:
        duration = frame_count / effective_fps
    elif config.timing is not None and config.timing.duration is not None:
        duration = float(config.timing.duration)

    return frame_count, duration


def _result_metadata(
    target: object,
    config: RenderConfig,
    output_path: Path,
    *,
    frame_count: int | None,
    duration: float | None,
) -> dict[str, Any]:
    metadata = dict(config.metadata)
    metadata["output_path"] = str(output_path)
    metadata["format"] = config.format

    if config.timing is not None:
        if config.timing.seed is not None:
            metadata["seed"] = config.timing.seed
        if config.timing.fps is not None:
            metadata["fps"] = config.timing.fps
        if config.timing.duration is not None:
            metadata["duration"] = config.timing.duration

    if config.viewport is not None:
        if config.viewport.width is not None:
            metadata["viewport_width"] = config.viewport.width
        if config.viewport.height is not None:
            metadata["viewport_height"] = config.viewport.height
        if config.viewport.fit_padding is not None:
            metadata["viewport_fit_padding"] = config.viewport.fit_padding
        metadata["viewport_fit_crop"] = config.viewport.fit_crop
    elif config.fit_padding is not None:
        metadata["fit_padding"] = config.fit_padding
        metadata["fit_crop"] = config.fit_crop

    if isinstance(target, Canvas):
        metadata["canvas_width"] = target.width
        metadata["canvas_height"] = target.height
    elif hasattr(target, "fps"):
        metadata["fps_effective"] = getattr(target, "fps")

    metadata["frame_count"] = frame_count
    metadata["duration_effective"] = duration

    stable_payload = {
        "format": config.format,
        "timing": {
            "fps": config.timing.fps if config.timing is not None else None,
            "duration": config.timing.duration if config.timing is not None else None,
            "seed": config.timing.seed if config.timing is not None else None,
        },
        "viewport": {
            "width": config.viewport.width if config.viewport is not None else None,
            "height": config.viewport.height if config.viewport is not None else None,
            "fit_padding": (
                config.viewport.fit_padding if config.viewport is not None else config.fit_padding
            ),
            "fit_crop": (
                config.viewport.fit_crop if config.viewport is not None else config.fit_crop
            ),
        },
        "output_name": output_path.name,
    }
    serialized = json.dumps(stable_payload, sort_keys=True, separators=(",", ":"))
    metadata["config_fingerprint"] = hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()[:16]
    return metadata


def _emit_render_report(result: RenderResult, config: RenderConfig) -> None:
    if config.report_json_path is not None:
        report_path = Path(config.report_json_path)
        if report_path.suffix.lower() != ".json":
            report_path = report_path.with_suffix(".json")

        if not report_path.parent.exists():
            if config.create_parents:
                report_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                raise RenderExportError(
                    actionable_error(
                        parameter="create_parents",
                        invalid_value=config.create_parents,
                        allowed=f"True, or an existing report parent directory ({report_path.parent})",
                        suggested_fix="Set create_parents=True or choose an existing report path parent.",
                    )
                )

        report = {
            "output_path": str(result.output_path),
            "format": result.format,
            "frame_count": result.frame_count,
            "duration": result.duration,
            "metadata": result.metadata,
        }
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        result.report_path = report_path

    if config.report_hook is not None:
        config.report_hook(result)


def _emit_before_play(target: object, config: RenderConfig) -> None:
    hooks = config.lifecycle_hooks
    if hooks is not None and hooks.before_play is not None:
        hooks.before_play(target, config)


def _emit_after_frames(target: object, config: RenderConfig) -> None:
    hooks = config.lifecycle_hooks
    if hooks is None or hooks.after_frame is None:
        return
    frames = getattr(target, "_frames", None)
    if isinstance(frames, list):
        total = len(frames)
        for index in range(total):
            hooks.after_frame(index, total, config)


def _emit_before_save(output_path: Path, target: object, config: RenderConfig) -> None:
    hooks = config.lifecycle_hooks
    if hooks is not None and hooks.before_save is not None:
        hooks.before_save(output_path, target, config)


def _emit_after_save(result: RenderResult, config: RenderConfig) -> None:
    hooks = config.lifecycle_hooks
    if hooks is not None and hooks.after_save is not None:
        hooks.after_save(result, config)


def render_scene(target: object, config: RenderConfig) -> RenderResult:
    """
    Render a static Canvas or an animation Scene-like object using one policy.

    Canvas targets support static formats: svg, png, pdf, ps.
    Scene-like targets support animation formats: gif, mp4.
    """

    config.validate()
    output_path = _normalized_output_path(config)
    _apply_timing(target, config)
    _emit_before_play(target, config)

    if isinstance(target, Canvas):
        if config.format not in _STATIC_FORMATS:
            raise RenderExportError(
                actionable_error(
                    parameter="format",
                    invalid_value=config.format,
                    allowed=", ".join(sorted(_STATIC_FORMATS)),
                    suggested_fix=f"Use a static format for Canvas: {', '.join(sorted(_STATIC_FORMATS))}.",
                )
            )

        _apply_viewport(target, config)
        _emit_before_save(output_path, target, config)

        try:
            target.save(output_path, dpi=config.dpi)
        except ImportError as exc:
            raise RenderDependencyError(str(exc)) from exc
        except ValueError as exc:
            raise RenderExportError(str(exc)) from exc

        frame_count, duration = _result_telemetry(target, config)
        result = RenderResult(
            output_path=output_path,
            format=config.format,
            frame_count=frame_count,
            duration=duration,
            metadata=_result_metadata(
                target,
                config,
                output_path,
                frame_count=frame_count,
                duration=duration,
            ),
        )
        _emit_after_save(result, config)
        _emit_render_report(result, config)
        return result

    if config.format not in _ANIMATION_FORMATS:
        raise RenderExportError(
            actionable_error(
                parameter="format",
                invalid_value=config.format,
                allowed=", ".join(sorted(_ANIMATION_FORMATS)),
                suggested_fix=f"Use an animation format for Scene-like targets: {', '.join(sorted(_ANIMATION_FORMATS))}.",
            )
        )

    try:
        _emit_after_frames(target, config)
        _emit_before_save(output_path, target, config)
        save = getattr(target, "save")
    except AttributeError as exc:
        raise RenderExportError(
            actionable_error(
                parameter="target",
                invalid_value=type(target).__name__,
                allowed="Canvas or Scene-like object with save(...)",
                suggested_fix="Pass a Canvas or Scene-like target exposing save(dest, format=...).",
            )
        ) from exc

    try:
        save(str(output_path), format=config.format)
    except TypeError:
        save(str(output_path))
    except ImportError as exc:
        raise RenderDependencyError(str(exc)) from exc
    except ValueError as exc:
        raise RenderExportError(str(exc)) from exc

    frame_count, duration = _result_telemetry(target, config)
    result = RenderResult(
        output_path=output_path,
        format=config.format,
        frame_count=frame_count,
        duration=duration,
        metadata=_result_metadata(
            target,
            config,
            output_path,
            frame_count=frame_count,
            duration=duration,
        ),
    )
    _emit_after_save(result, config)
    _emit_render_report(result, config)
    return result


def render_batch(batch: Iterable[tuple[object, RenderConfig]]) -> list[RenderResult]:
    """Render a sequence of (target, config) pairs and return ordered results."""
    results: list[RenderResult] = []
    for target, config in batch:
        results.append(render_scene(target, config))
    return results
