from __future__ import annotations

from abc import ABC, abstractmethod

from tesserax.core import Point

from .core import Body


def _dot(a: Point, b: Point) -> float:
    return a.x * b.x + a.y * b.y


class Joint(ABC):
    _next_id = 1

    def __init__(self) -> None:
        self.joint_id = f"joint:{Joint._next_id}"
        Joint._next_id += 1

    @abstractmethod
    def bodies(self) -> tuple[Body, ...]:
        raise NotImplementedError

    @abstractmethod
    def solve(self) -> dict[str, object] | None:
        raise NotImplementedError


class RevoluteJoint(Joint):
    def __init__(
        self,
        body: Body,
        anchor: Point,
        *,
        min_angle: float | None = None,
        max_angle: float | None = None,
        stiffness: float = 1.0,
    ) -> None:
        super().__init__()
        self.body = body
        self.anchor = Point(anchor.x, anchor.y)
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.stiffness = stiffness

    def bodies(self) -> tuple[Body, ...]:
        return (self.body,)

    def solve(self) -> dict[str, object]:
        if self.body.static:
            return {"error": 0.0, "impulse": 0.0, "active_limits": []}

        delta = self.anchor - self.body.pos
        correction = delta * self.stiffness
        self.body.pos += correction

        active_limits: list[str] = []
        angle_error = 0.0
        if self.min_angle is not None and self.body.rotation < self.min_angle:
            angle_error = self.min_angle - self.body.rotation
            self.body.rotation = self.min_angle
            self.body.angular_vel = 0.0
            active_limits.append("min_angle")
        if self.max_angle is not None and self.body.rotation > self.max_angle:
            angle_error = self.body.rotation - self.max_angle
            self.body.rotation = self.max_angle
            self.body.angular_vel = 0.0
            active_limits.append("max_angle")

        return {
            "error": delta.magnitude() + abs(angle_error),
            "impulse": correction.magnitude() + abs(angle_error),
            "active_limits": active_limits,
        }


class PrismaticJoint(Joint):
    def __init__(
        self,
        body: Body,
        anchor: Point,
        axis: Point,
        *,
        min_translation: float | None = None,
        max_translation: float | None = None,
        stiffness: float = 1.0,
    ) -> None:
        super().__init__()
        self.body = body
        self.anchor = Point(anchor.x, anchor.y)
        unit = axis.normalize()
        self.axis = unit if unit.magnitude() > 0 else Point.right()
        self.min_translation = min_translation
        self.max_translation = max_translation
        self.stiffness = stiffness

    def bodies(self) -> tuple[Body, ...]:
        return (self.body,)

    def solve(self) -> dict[str, object]:
        if self.body.static:
            return {"error": 0.0, "impulse": 0.0, "active_limits": []}

        rel = self.body.pos - self.anchor
        translation = _dot(rel, self.axis)
        on_axis = self.axis * translation
        perp = rel - on_axis

        # Pull the body back to the joint axis.
        perpendicular_correction = perp * self.stiffness
        self.body.pos -= perpendicular_correction

        active_limits: list[str] = []
        clamped = translation
        if self.min_translation is not None and clamped < self.min_translation:
            clamped = self.min_translation
            active_limits.append("min_translation")
        if self.max_translation is not None and clamped > self.max_translation:
            clamped = self.max_translation
            active_limits.append("max_translation")

        limit_correction = Point.zero()
        if clamped != translation:
            target = self.anchor + self.axis * clamped
            limit_correction = target - self.body.pos
            self.body.pos += limit_correction * self.stiffness

        return {
            "error": perpendicular_correction.magnitude() + abs(clamped - translation),
            "impulse": perpendicular_correction.magnitude() + limit_correction.magnitude(),
            "active_limits": active_limits,
            "translation": clamped,
        }
