from __future__ import annotations

import json

import pytest

from tesserax import Canvas, Rect
from tesserax.errors import RenderConfigError, RenderExportError
from tesserax.render import (
    RenderConfig,
    RenderLifecycleHooks,
    TimingSpec,
    ViewportSpec,
    render_batch,
    render_scene,
)


def _simple_canvas() -> Canvas:
    canvas = Canvas(width=200, height=120)
    canvas.add(Rect(80, 40))
    return canvas


def test_render_config_rejects_invalid_format() -> None:
    cfg = RenderConfig(output_path="x.svg", format="svg")  # type: ignore[arg-type]
    cfg.format = "bmp"  # type: ignore[assignment]

    with pytest.raises(RenderConfigError):
        cfg.validate()


def test_render_config_error_message_is_actionable_for_format() -> None:
    cfg = RenderConfig(output_path="x.svg", format="svg")  # type: ignore[arg-type]
    cfg.format = "bmp"  # type: ignore[assignment]
    with pytest.raises(RenderConfigError) as exc:
        cfg.validate()
    msg = str(exc.value)
    assert "parameter='format'" in msg
    assert "invalid_value='bmp'" in msg
    assert "allowed=" in msg
    assert "suggested_fix=" in msg


def test_render_scene_normalizes_suffix_and_writes_svg(tmp_path) -> None:
    canvas = _simple_canvas()
    cfg = RenderConfig(output_path=tmp_path / "diagram", format="svg")

    result = render_scene(canvas, cfg)

    assert result.output_path.name == "diagram.svg"
    assert result.output_path.exists()
    assert result.frame_count == 1
    assert result.duration == 0.0


def test_render_scene_respects_create_parents_false(tmp_path) -> None:
    canvas = _simple_canvas()
    cfg = RenderConfig(
        output_path=tmp_path / "missing" / "diagram.svg",
        format="svg",
        create_parents=False,
    )

    with pytest.raises(RenderExportError) as exc:
        render_scene(canvas, cfg)
    msg = str(exc.value)
    assert "parameter='create_parents'" in msg
    assert "invalid_value=False" in msg
    assert "allowed=" in msg
    assert "suggested_fix=" in msg


def test_render_scene_respects_overwrite_false(tmp_path) -> None:
    canvas = _simple_canvas()
    out = tmp_path / "diagram.svg"
    out.write_text("<svg/>", encoding="utf-8")
    cfg = RenderConfig(output_path=out, format="svg", overwrite=False)

    with pytest.raises(RenderExportError):
        render_scene(canvas, cfg)


def test_render_scene_rejects_animation_format_for_canvas(tmp_path) -> None:
    canvas = _simple_canvas()
    cfg = RenderConfig(output_path=tmp_path / "anim.gif", format="gif")

    with pytest.raises(RenderExportError) as exc:
        render_scene(canvas, cfg)
    msg = str(exc.value)
    assert "parameter='format'" in msg
    assert "invalid_value='gif'" in msg
    assert "allowed=" in msg
    assert "suggested_fix=" in msg


def test_render_batch_returns_ordered_results(tmp_path) -> None:
    c1 = _simple_canvas()
    c2 = _simple_canvas()
    batch = [
        (c1, RenderConfig(output_path=tmp_path / "a", format="svg")),
        (c2, RenderConfig(output_path=tmp_path / "b.svg", format="svg")),
    ]

    results = render_batch(batch)

    assert [r.output_path.name for r in results] == ["a.svg", "b.svg"]
    assert all(r.output_path.exists() for r in results)


def test_render_config_rejects_invalid_timing() -> None:
    cfg = RenderConfig(
        output_path="x.svg",
        format="svg",
        timing=TimingSpec(fps=0),
    )
    with pytest.raises(RenderConfigError):
        cfg.validate()


def test_render_config_rejects_invalid_viewport() -> None:
    cfg = RenderConfig(
        output_path="x.svg",
        format="svg",
        viewport=ViewportSpec(width=-1),
    )
    with pytest.raises(RenderConfigError):
        cfg.validate()


def test_render_config_rejects_non_positive_viewport_height() -> None:
    cfg = RenderConfig(
        output_path="x.svg",
        format="svg",
        viewport=ViewportSpec(height=0),
    )
    with pytest.raises(RenderConfigError):
        cfg.validate()


def test_render_scene_applies_viewport_dimensions(tmp_path) -> None:
    canvas = _simple_canvas()
    cfg = RenderConfig(
        output_path=tmp_path / "viewport.svg",
        format="svg",
        viewport=ViewportSpec(width=320, height=180),
    )

    render_scene(canvas, cfg)

    assert canvas.width == 320
    assert canvas.height == 180


def test_render_scene_applies_timing_fps_to_scene_like_target(tmp_path) -> None:
    class FakeScene:
        def __init__(self) -> None:
            self.fps = 30
            self.saved: tuple[str, str] | None = None

        def save(self, dest: str, format: str | None = None) -> None:
            self.saved = (dest, format or "")

    scene = FakeScene()
    cfg = RenderConfig(
        output_path=tmp_path / "anim.gif",
        format="gif",
        timing=TimingSpec(fps=12, duration=2.5),
    )

    result = render_scene(scene, cfg)

    assert scene.fps == 12
    assert scene.saved is not None
    assert result.output_path.name == "anim.gif"


def test_render_scene_captures_seed_and_fingerprint_metadata(tmp_path) -> None:
    canvas = _simple_canvas()
    cfg = RenderConfig(
        output_path=tmp_path / "meta.svg",
        format="svg",
        timing=TimingSpec(seed=227, fps=24),
    )

    result = render_scene(canvas, cfg)

    assert result.metadata["seed"] == 227
    assert result.metadata["fps"] == 24
    assert "config_fingerprint" in result.metadata
    assert len(str(result.metadata["config_fingerprint"])) == 16


def test_render_scene_writes_json_report_when_configured(tmp_path) -> None:
    canvas = _simple_canvas()
    report_path = tmp_path / "reports" / "render_result"
    cfg = RenderConfig(
        output_path=tmp_path / "report.svg",
        format="svg",
        timing=TimingSpec(seed=11),
        report_json_path=report_path,
    )

    result = render_scene(canvas, cfg)

    assert result.report_path is not None
    assert result.report_path.name == "render_result.json"
    payload = json.loads(result.report_path.read_text(encoding="utf-8"))
    assert payload["output_path"].endswith("report.svg")
    assert payload["frame_count"] == 1
    assert payload["duration"] == 0.0
    assert payload["metadata"]["seed"] == 11


def test_render_scene_invokes_report_hook(tmp_path) -> None:
    canvas = _simple_canvas()
    seen: list[str] = []

    def hook(result) -> None:
        seen.append(result.output_path.name)

    cfg = RenderConfig(
        output_path=tmp_path / "hook.svg",
        format="svg",
        report_hook=hook,
    )

    render_scene(canvas, cfg)

    assert seen == ["hook.svg"]


def test_render_scene_invokes_lifecycle_hooks_for_canvas(tmp_path) -> None:
    canvas = _simple_canvas()
    seen: list[str] = []

    def before_play(target, cfg) -> None:
        assert target is canvas
        assert cfg.format == "svg"
        seen.append("before_play")

    def before_save(path, target, cfg) -> None:
        assert path.name == "lifecycle.svg"
        assert target is canvas
        assert cfg.format == "svg"
        seen.append("before_save")

    def after_save(result, cfg) -> None:
        assert result.output_path.name == "lifecycle.svg"
        assert cfg.format == "svg"
        seen.append("after_save")

    cfg = RenderConfig(
        output_path=tmp_path / "lifecycle.svg",
        format="svg",
        lifecycle_hooks=RenderLifecycleHooks(
            before_play=before_play,
            before_save=before_save,
            after_save=after_save,
        ),
    )
    render_scene(canvas, cfg)
    assert seen == ["before_play", "before_save", "after_save"]


def test_render_scene_invokes_after_frame_for_scene_like_target(tmp_path) -> None:
    class FakeScene:
        def __init__(self) -> None:
            self.fps = 24
            self._frames = [b"a", b"b", b"c"]
            self.saved: tuple[str, str] | None = None

        def save(self, dest: str, format: str | None = None) -> None:
            self.saved = (dest, format or "")

    scene = FakeScene()
    seen: list[str] = []
    frame_indexes: list[int] = []
    frame_totals: list[int] = []

    cfg = RenderConfig(
        output_path=tmp_path / "lifecycle.gif",
        format="gif",
        lifecycle_hooks=RenderLifecycleHooks(
            before_play=lambda target, _cfg: seen.append("before_play"),
            after_frame=lambda idx, total, _cfg: (
                frame_indexes.append(idx),
                frame_totals.append(total),
            ),
            before_save=lambda path, target, _cfg: seen.append("before_save"),
            after_save=lambda result, _cfg: seen.append("after_save"),
        ),
    )

    result = render_scene(scene, cfg)
    assert scene.saved is not None
    assert frame_indexes == [0, 1, 2]
    assert frame_totals == [3, 3, 3]
    assert result.frame_count == 3
    assert result.duration == pytest.approx(3 / 24)
    assert seen == ["before_play", "before_save", "after_save"]
