import importlib.util
from pathlib import Path

from tesserax.base import Circle
from tesserax.core import Point
from tesserax.physics.collisions import Collision
from tesserax.physics.events import PhysicsEvent
from tesserax.physics.world import World


def _load_overlay_module():
    root = Path(__file__).resolve().parents[1]
    mod_path = root / "examples-other" / "animation" / "physics" / "animation_physics_overlay.py"
    spec = importlib.util.spec_from_file_location("animation_physics_overlay", mod_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _mk_circle(world: World, x: float, y: float, r: float = 10.0):
    shape = Circle(r).move_to(Point(x, y))
    return world.add(shape)


def test_overlay_event_summary_counts_and_sampling_synthetic():
    overlay = _load_overlay_module()
    events = [
        PhysicsEvent("world.before_step", 0.0, 0, (), {}, 0),
        PhysicsEvent(
            "world.collision_start",
            0.0,
            0,
            ("body:1", "body:2"),
            {"contact_points": [{"x": 1.0, "y": 2.0}]},
            1,
        ),
        PhysicsEvent("world.after_step", 0.1, 0, (), {}, 2),
        PhysicsEvent("world.before_step", 0.1, 1, (), {}, 3),
        PhysicsEvent(
            "world.collision_persist",
            0.1,
            1,
            ("body:1", "body:2"),
            {"contact_points": [{"x": 3.0, "y": 4.0}]},
            4,
        ),
        PhysicsEvent("world.collision_end", 0.2, 1, ("body:1", "body:2"), {}, 5),
        PhysicsEvent("world.after_step", 0.2, 1, (), {}, 6),
    ]

    counts, sampled, total = overlay.summarize_physics_events(events, marker_cap=1)
    assert counts["world.before_step"] == 2
    assert counts["world.after_step"] == 2
    assert counts["world.collision_start"] == 1
    assert counts["world.collision_persist"] == 1
    assert counts["world.collision_end"] == 1
    assert total == 2
    assert len(sampled) == 1
    assert sampled[0][0] == Point(1.0, 2.0)
    assert sampled[0][1] == 0.0


def test_overlay_event_summary_counts_from_world_steps(monkeypatch):
    overlay = _load_overlay_module()
    world = World()
    _mk_circle(world, 0, 0)
    _mk_circle(world, 0, 0)

    calls = {"n": 0}

    def fake_solve(a, b):
        calls["n"] += 1
        if calls["n"] in (1, 2):
            return Collision(a=a, b=b, normal=Point(1, 0), depth=1.0, point=Point(0, 0))
        return None

    monkeypatch.setattr(Collision, "solve", fake_solve)

    world._step(0.1)
    world._step(0.1)
    world._step(0.1)

    counts, sampled, total = overlay.summarize_physics_events(world.events, marker_cap=10)
    assert counts["world.before_step"] == 3
    assert counts["world.after_step"] == 3
    assert counts["world.collision_start"] == 1
    assert counts["world.collision_persist"] == 1
    assert counts["world.collision_end"] == 1
    assert total == 2
    assert len(sampled) == 2
