from __future__ import annotations

from tesserax.base import Circle
from tesserax.core import Point
from tesserax.physics.collisions import Collision
from tesserax.physics.constraints import Spring
from tesserax.physics.joints import RevoluteJoint
from tesserax.physics.world import World


def _mk_circle(world: World, x: float, y: float, r: float = 10.0):
    shape = Circle(r).move_to(Point(x, y))
    return world.add(shape)


def test_physics_event_contract_payload_and_order(monkeypatch):
    world = World()
    a = _mk_circle(world, 0, 0)
    b = _mk_circle(world, 0, 0)

    world.constraint(Spring(a, b, length=8.0, k=1.0, damping=0.05))
    a.rotation = 2.0
    world.joint(RevoluteJoint(a, anchor=Point(0, 0), max_angle=0.8))

    calls = {"n": 0}

    def fake_solve(x, y):
        calls["n"] += 1
        if calls["n"] in (1, 2):
            return Collision(a=x, b=y, normal=Point(1, 0), depth=1.0, point=Point(0, 0))
        return None

    monkeypatch.setattr(Collision, "solve", fake_solve)

    world._step(0.1)  # collision_start
    world._step(0.1)  # collision_persist
    world._step(0.1)  # collision_end

    types = [e.type for e in world.events]
    for required in (
        "world.before_step",
        "world.after_step",
        "constraint.applied",
        "joint.limit_hit",
        "world.collision_start",
        "world.collision_persist",
        "world.collision_end",
    ):
        assert required in types

    for event in world.events:
        assert event.schema_version == "1.0.0"
        assert isinstance(event.type, str)
        assert isinstance(event.timestamp, float)
        assert isinstance(event.step_index, int)
        assert isinstance(event.entities, tuple)
        assert isinstance(event.metadata, dict)

    emissions = [(e.step_index, e.emission_order) for e in world.events]
    assert emissions == sorted(emissions)

    by_type = {}
    for e in world.events:
        by_type.setdefault(e.type, []).append(e)

    before = by_type["world.before_step"][0]
    assert {"dt", "body_count", "constraint_count", "joint_count"} <= set(before.metadata.keys())

    after = by_type["world.after_step"][0]
    assert {"dt", "collision_count", "active_collision_pairs"} <= set(after.metadata.keys())

    constraint = by_type["constraint.applied"][0]
    assert {"constraint_type", "constraint_id", "error", "impulse"} <= set(
        constraint.metadata.keys()
    )

    joint = by_type["joint.limit_hit"][0]
    assert {"joint_type", "joint_id", "error", "impulse", "active_limits"} <= set(
        joint.metadata.keys()
    )

    collision = by_type["world.collision_start"][0]
    assert {"normal", "penetration", "relative_speed", "contact_points"} <= set(
        collision.metadata.keys()
    )
