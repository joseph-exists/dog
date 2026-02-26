from __future__ import annotations

import io
from dataclasses import dataclass

import imageio.v2 as imageio
import numpy as np


def _to_rgba(frame: np.ndarray) -> np.ndarray:
    if frame.ndim == 2:
        return np.stack([frame, frame, frame, np.full_like(frame, 255)], axis=-1)
    if frame.shape[2] == 3:
        alpha = np.full((frame.shape[0], frame.shape[1], 1), 255, dtype=frame.dtype)
        return np.concatenate([frame, alpha], axis=2)
    return frame


def pad_frame_to_size(frame: np.ndarray, *, out_width: int, out_height: int) -> np.ndarray:
    h, w = frame.shape[:2]
    canvas = np.full((out_height, out_width, 4), 255, dtype=np.uint8)
    y0 = max(0, (out_height - h) // 2)
    x0 = max(0, (out_width - w) // 2)
    y1 = min(out_height, y0 + h)
    x1 = min(out_width, x0 + w)
    fy1 = min(h, y1 - y0)
    fx1 = min(w, x1 - x0)
    canvas[y0:y1, x0:x1] = frame[:fy1, :fx1]
    return canvas


def normalize_scene_frames(
    frames: list[bytes], *, out_width: int, out_height: int
) -> list[np.ndarray]:
    normalized: list[np.ndarray] = []
    for raw in frames:
        arr = imageio.imread(io.BytesIO(raw))
        rgba = _to_rgba(arr)
        normalized.append(
            pad_frame_to_size(rgba, out_width=out_width, out_height=out_height)
        )
    return normalized


@dataclass(slots=True)
class NormalizedSceneTarget:
    """Scene-like wrapper exporting normalized frame size via save(dest, format=...)."""

    scene: object
    out_width: int
    out_height: int

    @property
    def _frames(self) -> list[bytes]:
        return getattr(self.scene, "_frames")

    @property
    def fps(self) -> int:
        return int(getattr(self.scene, "fps"))

    @fps.setter
    def fps(self, value: int) -> None:
        setattr(self.scene, "fps", value)

    def save(self, dest: str, format: str | None = None) -> None:
        fmt = format or "gif"
        frames = normalize_scene_frames(
            self._frames, out_width=self.out_width, out_height=self.out_height
        )
        kwargs: dict[str, int] = {"fps": self.fps}
        if fmt == "mp4":
            kwargs["quality"] = 8
        else:
            kwargs["loop"] = 0
        imageio.mimsave(dest, frames, format=fmt, **kwargs)
