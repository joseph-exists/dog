import math

from tesserax.base import Circle
from tesserax.core import Point
from tesserax.physics.collisions import Collision
from tesserax.physics.constraints import Constraint, Pin, Spring
from tesserax.physics.joints import PrismaticJoint, RevoluteJoint
from tesserax.physics.world import World


class _NoOpConstraint(Constraint):
    def solve(self):
        return None


def _mk_circle(world: World, x: float, y: float, r: float = 10.0):
    shape = Circle(r).move_to(Point(x, y))
    return world.add(shape)


def test_world_step_emits_before_after_events(monkeypatch):
    world = World()
    _mk_circle(world, 0, 0)
    _mk_circle(world, 100, 0)

    monkeypatch.setattr(Collision, "solve", lambda a, b: None)
    got = []
    world.on_event(lambda e: got.append(e.type))
    world._step(0.1)

    assert got[0] == "world.before_step"
    assert got[-1] == "world.after_step"
    assert got == ["world.before_step", "world.after_step"]


def test_world_collision_start_persist_end_lifecycle(monkeypatch):
    world = World()
    a = _mk_circle(world, 0, 0)
    b = _mk_circle(world, 0, 0)

    calls = {"n": 0}

    def fake_solve(x, y):
        calls["n"] += 1
        if calls["n"] in (1, 2):
            return Collision(a=x, b=y, normal=Point(1, 0), depth=1.0, point=Point(0, 0))
        return None

    monkeypatch.setattr(Collision, "solve", fake_solve)
    got = []
    world.on_event(lambda e: got.append(e.type))

    world._step(0.1)  # start
    world._step(0.1)  # persist
    world._step(0.1)  # end

    assert "world.collision_start" in got
    assert "world.collision_persist" in got
    assert "world.collision_end" in got

    i_start = got.index("world.collision_start")
    i_persist = got.index("world.collision_persist")
    i_end = got.index("world.collision_end")
    assert i_start < i_persist < i_end


def test_world_constraint_event_emitted():
    world = World()
    _mk_circle(world, 0, 0)
    _mk_circle(world, 40, 0)
    world.constraint(_NoOpConstraint())

    got = []
    world.on_event(lambda e: got.append(e.type))
    world._step(0.05)

    assert "constraint.applied" in got


def test_constraint_event_includes_rfc_metadata_and_entities():
    world = World()
    a = _mk_circle(world, 0, 0)
    b = _mk_circle(world, 40, 0)
    world.constraint(Spring(a, b, length=20.0, k=1.4, damping=0.05))

    got = []
    world.on_event(lambda e: got.append(e))
    world._step(0.05)

    ev = next(e for e in got if e.type == "constraint.applied")
    assert ev.entities == (f"body:{a.body_id}", f"body:{b.body_id}")
    assert ev.metadata["constraint_type"] == "Spring"
    assert str(ev.metadata["constraint_id"]).startswith("constraint:")
    assert isinstance(ev.metadata["error"], float)
    assert isinstance(ev.metadata["impulse"], float)
    assert ev.schema_version == "1.0.0"


def test_pin_constraint_emits_single_entity():
    world = World()
    a = _mk_circle(world, 12, 8)
    world.constraint(Pin(a, Point(20, 20), stiffness=0.4))

    got = []
    world.on_event(lambda e: got.append(e))
    world._step(0.1)

    ev = next(e for e in got if e.type == "constraint.applied")
    assert ev.entities == (f"body:{a.body_id}",)
    assert ev.metadata["constraint_type"] == "Pin"


def test_world_event_metadata_contains_collision_fields(monkeypatch):
    world = World()
    _mk_circle(world, 0, 0)
    _mk_circle(world, 0, 0)

    def fake_solve(a, b):
        a.vel = Point(2, 0)
        b.vel = Point(-1, 0)
        return Collision(a=a, b=b, normal=Point(1, 0), depth=2.5, point=Point(1, 2))

    monkeypatch.setattr(Collision, "solve", fake_solve)

    got = []
    world.on_event(lambda e: got.append(e))
    world._step(0.1)

    col = next(e for e in got if e.type == "world.collision_start")
    assert col.metadata["penetration"] == 2.5
    assert math.isclose(col.metadata["relative_speed"], 3.0, abs_tol=1e-9)
    cp = col.metadata["contact_points"][0]
    assert cp["x"] == 1
    assert cp["y"] == 2
    assert col.schema_version == "1.0.0"


def test_revolute_joint_limit_hit_event_contains_metadata():
    world = World()
    body = _mk_circle(world, 15, 20)
    body.rotation = 1.8
    world.joint(RevoluteJoint(body, anchor=Point(15, 20), max_angle=0.9))

    got = []
    world.on_event(lambda e: got.append(e))
    world._step(0.05)

    ev = next(e for e in got if e.type == "joint.limit_hit")
    assert ev.entities == (f"body:{body.body_id}",)
    assert ev.metadata["joint_type"] == "RevoluteJoint"
    assert str(ev.metadata["joint_id"]).startswith("joint:")
    assert "max_angle" in ev.metadata["active_limits"]
    assert isinstance(ev.metadata["error"], float)
    assert isinstance(ev.metadata["impulse"], float)
    assert ev.schema_version == "1.0.0"


def test_prismatic_joint_limit_hit_event_contains_metadata():
    world = World()
    body = _mk_circle(world, 100, 12)
    world.joint(
        PrismaticJoint(
            body,
            anchor=Point(0, 0),
            axis=Point(1, 0),
            min_translation=-5,
            max_translation=30,
        )
    )

    got = []
    world.on_event(lambda e: got.append(e))
    world._step(0.05)

    ev = next(e for e in got if e.type == "joint.limit_hit")
    assert ev.entities == (f"body:{body.body_id}",)
    assert ev.metadata["joint_type"] == "PrismaticJoint"
    assert str(ev.metadata["joint_id"]).startswith("joint:")
    assert "max_translation" in ev.metadata["active_limits"]
    assert isinstance(ev.metadata["error"], float)
    assert isinstance(ev.metadata["impulse"], float)


def test_joint_limit_hit_order_is_between_before_and_after():
    world = World()
    body = _mk_circle(world, 15, 15)
    body.rotation = 2.0
    world.joint(RevoluteJoint(body, anchor=Point(15, 15), max_angle=0.8))

    got = []
    world.on_event(lambda e: got.append(e.type))
    world._step(0.05)

    i_before = got.index("world.before_step")
    i_joint = got.index("joint.limit_hit")
    i_after = got.index("world.after_step")
    assert i_before < i_joint < i_after
