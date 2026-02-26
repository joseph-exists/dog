from __future__ import annotations

from abc import ABC, abstractmethod

from tesserax.core import Point

from .core import Body


class Constraint(ABC):
    _next_id = 1

    def __init__(self) -> None:
        self.constraint_id = f"constraint:{Constraint._next_id}"
        Constraint._next_id += 1

    def bodies(self) -> tuple[Body, ...]:
        return ()

    @abstractmethod
    def solve(self) -> dict[str, object] | None:
        """Apply forces or corrections to satisfy constraint."""
        raise NotImplementedError


class Spring(Constraint):
    def __init__(
        self, a: Body, b: Body, length: float, k: float = 2.0, damping: float = 0.1
    ):
        super().__init__()
        self.a = a
        self.b = b
        self.rest_length = length
        self.stiffness = k
        self.damping = damping

    def bodies(self) -> tuple[Body, ...]:
        return (self.a, self.b)

    def solve(self) -> dict[str, object]:
        # 1. Vector from A to B
        delta = self.b.pos - self.a.pos
        dist = delta.magnitude()

        if dist == 0:
            return {"error": 0.0, "impulse": 0.0}

        # 2. Hooke's Law: F = -k * (current_len - rest_len)
        force_mag = (dist - self.rest_length) * self.stiffness

        # 3. Damping (Resistance to velocity difference)
        # Project relative velocity onto the axis
        rel_vel = self.b.vel - self.a.vel
        normal = delta / dist
        vel_along_normal = rel_vel.x * normal.x + rel_vel.y * normal.y
        damping_force = vel_along_normal * self.damping

        total_force = force_mag + damping_force

        # Apply equal and opposite forces
        f_vector = normal * total_force

        self.a.apply(f_vector)
        self.b.apply(f_vector * -1)  # Newton's 3rd Law
        return {"error": dist - self.rest_length, "impulse": abs(total_force)}


class Rod(Constraint):
    """
    A hard constraint that keeps two bodies at a fixed distance.
    Solves using Position Correction (Jacobi/Gauss-Seidel style).
    """

    def __init__(self, a: Body, b: Body, length: float):
        super().__init__()
        self.a = a
        self.b = b
        self.length = length

    def bodies(self) -> tuple[Body, ...]:
        return (self.a, self.b)

    def solve(self) -> dict[str, object]:
        delta = self.b.pos - self.a.pos
        dist = delta.magnitude()
        if dist == 0:
            return {"error": 0.0, "impulse": 0.0}

        # Error: How far are we from target length?
        error = dist - self.length

        # We want to move them to fix the error.
        # Move proportional to inverse mass (lighter objects move more).
        total_inv_mass = self.a.inv_mass + self.b.inv_mass
        if total_inv_mass == 0:
            return {"error": error, "impulse": 0.0}

        # Correction Vector
        correction = (delta / dist) * (error / total_inv_mass)

        if not self.a.static:
            self.a.pos += correction * self.a.inv_mass
            # Update velocity to prevent fighting next frame (optional but stable)
            # For simple position-based dynamics, we often ignore vel update or zero it along normal

        if not self.b.static:
            self.b.pos -= correction * self.b.inv_mass
        return {"error": error, "impulse": correction.magnitude()}


class Distance(Rod):
    """Alias for Rod with naming aligned to physics API docs."""


class Pin(Constraint):
    def __init__(self, body: Body, anchor: Point, stiffness: float = 1.0):
        super().__init__()
        self.body = body
        self.anchor = Point(anchor.x, anchor.y)
        self.stiffness = stiffness

    def bodies(self) -> tuple[Body, ...]:
        return (self.body,)

    def solve(self) -> dict[str, object]:
        if self.body.static:
            return {"error": 0.0, "impulse": 0.0}
        delta = self.anchor - self.body.pos
        error = delta.magnitude()
        correction = delta * self.stiffness
        self.body.pos += correction
        self.body.vel = self.body.vel * 0.95
        return {"error": error, "impulse": correction.magnitude()}
