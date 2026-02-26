from __future__ import annotations

import io

import imageio.v2 as imageio
import numpy as np

from tesserax.normalized_export import (
    NormalizedSceneTarget,
    normalize_scene_frames,
)
from tesserax.render import RenderConfig, render_scene


def _png_bytes(width: int, height: int, rgb: tuple[int, int, int]) -> bytes:
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    arr[:, :, 0] = rgb[0]
    arr[:, :, 1] = rgb[1]
    arr[:, :, 2] = rgb[2]
    buf = io.BytesIO()
    imageio.imwrite(buf, arr, format="png")
    return buf.getvalue()


def test_normalize_scene_frames_pads_to_target_size() -> None:
    frames = [
        _png_bytes(24, 12, (255, 0, 0)),
        _png_bytes(10, 20, (0, 255, 0)),
    ]
    out = normalize_scene_frames(frames, out_width=48, out_height=32)
    assert len(out) == 2
    assert all(frame.shape == (32, 48, 4) for frame in out)


def test_normalized_scene_target_emits_loop_for_gif(monkeypatch, tmp_path) -> None:
    calls: list[dict] = []

    def fake_mimsave(dest, frames, format=None, **kwargs):
        calls.append(
            {
                "dest": str(dest),
                "format": format,
                "kwargs": kwargs,
                "frame_shape": tuple(frames[0].shape),
            }
        )

    monkeypatch.setattr("tesserax.normalized_export.imageio.mimsave", fake_mimsave)

    class FakeScene:
        def __init__(self) -> None:
            self.fps = 12
            self._frames = [_png_bytes(12, 12, (25, 25, 25))]

    target = NormalizedSceneTarget(scene=FakeScene(), out_width=40, out_height=30)
    target.save(str(tmp_path / "x.gif"), format="gif")
    assert calls
    assert calls[0]["format"] == "gif"
    assert calls[0]["kwargs"]["fps"] == 12
    assert calls[0]["kwargs"]["loop"] == 0
    assert calls[0]["frame_shape"] == (30, 40, 4)


def test_render_scene_accepts_normalized_scene_target(monkeypatch, tmp_path) -> None:
    calls: list[dict] = []

    def fake_mimsave(dest, frames, format=None, **kwargs):
        calls.append({"format": format, "kwargs": kwargs, "shape": tuple(frames[0].shape)})

    monkeypatch.setattr("tesserax.normalized_export.imageio.mimsave", fake_mimsave)

    class FakeScene:
        def __init__(self) -> None:
            self.fps = 24
            self._frames = [_png_bytes(8, 8, (1, 2, 3)), _png_bytes(16, 8, (3, 2, 1))]

    target = NormalizedSceneTarget(scene=FakeScene(), out_width=64, out_height=48)
    result = render_scene(
        target,
        RenderConfig(output_path=tmp_path / "normalized", format="gif"),
    )
    assert result.output_path.name == "normalized.gif"
    assert result.frame_count == 2
    assert result.duration == 2 / 24
    assert calls
    assert calls[0]["shape"] == (48, 64, 4)
