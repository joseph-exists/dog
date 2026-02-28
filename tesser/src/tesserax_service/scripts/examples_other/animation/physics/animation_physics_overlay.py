#!/usr/bin/env python3
"""Physics + animation overlay stress test for Tesserax."""

import argparse
import json
import random

from tesserax import (
    Arrow,
    Canvas,
    Circle,
    Colors,
    Point,
    Polyline,
    Rect,
    RenderConfig,
    RenderLifecycleHooks,
    Text,
    render_scene,
)
from tesserax.animation import Delayed, KeyframeAnimation, Parallel, Scene
from tesserax.physics import PhysicsEvent
from tesserax.physics import Drag, Gravity, Material, PrismaticJoint, RevoluteJoint, World
from tesserax.physics.colliders import CircleCollider


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def summarize_physics_events(
    events: list[PhysicsEvent], marker_cap: int
) -> tuple[dict[str, int], list[tuple[Point, float]], int]:
    counts: dict[str, int] = {}
    collision_points: list[tuple[Point, float]] = []
    for event in events:
        counts[event.type] = counts.get(event.type, 0) + 1
        if event.type not in {"world.collision_start", "world.collision_persist"}:
            continue
        points = event.metadata.get("contact_points")
        if not isinstance(points, list):
            continue
        for point in points:
            if not isinstance(point, dict):
                continue
            x = point.get("x")
            y = point.get("y")
            if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                collision_points.append((Point(float(x), float(y)), event.timestamp))

    sampled_collision_points: list[tuple[Point, float]] = []
    if marker_cap > 0 and collision_points:
        step = max(1, len(collision_points) // marker_cap)
        sampled_collision_points = collision_points[::step][:marker_cap]
    return counts, sampled_collision_points, len(collision_points)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Animated physics overlay stress test.")
    p.add_argument("--balls", type=int, default=8, help="Dynamic ball count.")
    p.add_argument("--duration", type=float, default=8.0, help="Simulation/animation seconds.")
    p.add_argument("--dt", type=float, default=0.02, help="Physics step size (seconds).")
    p.add_argument("--fps", type=int, default=24, help="Render FPS.")
    p.add_argument("--gravity", type=float, default=980.0, help="Gravity acceleration.")
    p.add_argument("--drag", type=float, default=0.06, help="Linear drag coefficient.")
    p.add_argument("--restitution", type=float, default=0.78, help="Ball bounciness.")
    p.add_argument(
        "--joint-demo",
        choices=["none", "revolute", "prismatic"],
        default="none",
        help="Optional joint limit-hit demo mode for event callouts.",
    )
    p.add_argument(
        "--vector-scale",
        type=float,
        default=0.10,
        help="Velocity-to-vector scale factor.",
    )
    p.add_argument(
        "--trail-step",
        type=int,
        default=5,
        help="Sampling interval for static trajectory trails.",
    )
    p.add_argument(
        "--event-markers",
        type=int,
        default=100,
        help="Maximum collision contact markers rendered from physics events.",
    )
    p.add_argument(
        "--event-marker-fade",
        type=float,
        default=0.0,
        help="Optional age-based marker fade strength in [0,1].",
    )
    p.add_argument("--seed", type=int, default=41, help="Random seed.")
    p.add_argument("--width", type=int, default=1400, help="Canvas width.")
    p.add_argument("--height", type=int, default=900, help="Canvas height.")
    p.add_argument("--format", choices=["gif", "mp4"], default="gif", help="Output format.")
    p.add_argument(
        "--output",
        type=str,
        default="physics_overlay.gif",
        help="Output path (extension adjusted to --format).",
    )
    p.add_argument(
        "--hook-log-json",
        type=str,
        default="",
        help="Optional path to write lifecycle hook trace as JSON.",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)

    balls = max(1, args.balls)
    duration = max(0.5, args.duration)
    dt = max(0.002, args.dt)
    fps = max(1, args.fps)
    trail_step = max(1, args.trail_step)
    vector_scale = max(0.01, args.vector_scale)
    restitution = clamp(args.restitution, 0.0, 1.0)
    joint_demo = args.joint_demo
    event_marker_cap = max(0, args.event_markers)
    event_marker_fade = clamp(args.event_marker_fade, 0.0, 1.0)

    canvas = Canvas(width=args.width, height=args.height)
    world = World()

    # Background and UI labels.
    canvas.add(
        Rect(
            w=args.width,
            h=args.height,
            fill=Colors.White,
            stroke=Colors.Transparent,
            width=0,
        ).move_to(Point(args.width / 2, args.height / 2))
    )
    canvas.add(
        Text("Physics Overlay Stress Test", size=24, fill=Colors.DarkBlue).move_to(
            Point(args.width / 2, 42)
        )
    )
    canvas.add(
        Text(
            f"balls={balls} duration={duration:.1f}s dt={dt:.3f} gravity={args.gravity:.1f} drag={args.drag:.2f}",
            size=12,
            fill=Colors.Gray,
        ).move_to(Point(args.width / 2, 68))
    )

    # World bounds.
    margin = 80
    floor_y = args.height - margin
    ceil_y = margin + 40
    left_x = margin
    right_x = args.width - margin

    floor = Rect(
        w=right_x - left_x + 40,
        h=20,
        fill=Colors.LightGray,
        stroke=Colors.DarkGray,
        width=1.0,
    ).move_to(Point((left_x + right_x) / 2, floor_y + 10))
    left_wall = Rect(w=20, h=floor_y - ceil_y + 30, fill=Colors.LightGray, stroke=Colors.DarkGray, width=1.0).move_to(
        Point(left_x - 10, (floor_y + ceil_y) / 2)
    )
    right_wall = Rect(w=20, h=floor_y - ceil_y + 30, fill=Colors.LightGray, stroke=Colors.DarkGray, width=1.0).move_to(
        Point(right_x + 10, (floor_y + ceil_y) / 2)
    )
    ceiling = Rect(
        w=right_x - left_x + 40,
        h=16,
        fill=Colors.LightGray.transparent(0.6),
        stroke=Colors.DarkGray.transparent(0.8),
        width=1.0,
    ).move_to(Point((left_x + right_x) / 2, ceil_y - 8))
    canvas.add(floor, left_wall, right_wall, ceiling)

    wall_material = Material(restitution=0.86, friction=0.30)
    world.add(floor, static=True, material=wall_material)
    world.add(left_wall, static=True, material=wall_material)
    world.add(right_wall, static=True, material=wall_material)
    world.add(ceiling, static=True, material=wall_material)

    # Dynamic bodies.
    colors = [
        Colors.Crimson,
        Colors.DodgerBlue,
        Colors.SeaGreen,
        Colors.DarkOrange,
        Colors.MediumVioletRed,
        Colors.Goldenrod,
        Colors.SlateBlue,
        Colors.Teal,
        Colors.IndianRed,
        Colors.CadetBlue,
    ]

    dyn_bodies = []
    for i in range(balls):
        r = rng.uniform(12, 26)
        x = rng.uniform(left_x + 40, right_x - 40)
        y = rng.uniform(ceil_y + 40, ceil_y + 210)
        ball = Circle(
            r=r,
            fill=colors[i % len(colors)].transparent(0.86),
            stroke=Colors.Black.transparent(0.35),
            width=1.0,
        ).move_to(Point(x, y))
        canvas.add(ball)

        body = world.add(
            ball,
            mass=max(0.8, r / 10),
            material=Material(restitution=restitution, friction=0.24),
            collider=CircleCollider(r),
        )
        body.vel = Point(rng.uniform(-220, 220), rng.uniform(-80, 160))
        body.angular_vel = rng.uniform(-1.5, 1.5)
        dyn_bodies.append(body)

    world.fields.append(Gravity(args.gravity))
    if args.drag > 0:
        world.fields.append(Drag(args.drag))
    if dyn_bodies and joint_demo != "none":
        lead = dyn_bodies[0]
        if joint_demo == "revolute":
            lead.rotation = 1.4
            world.joint(
                RevoluteJoint(
                    lead,
                    anchor=Point(lead.pos.x, lead.pos.y),
                    max_angle=0.65,
                )
            )
        else:
            world.joint(
                PrismaticJoint(
                    lead,
                    anchor=Point(left_x, ceil_y + 80),
                    axis=Point(1, 0),
                    min_translation=-20.0,
                    max_translation=45.0,
                )
            )

    # Bake simulation tracks manually so overlays (velocity vectors) can be animated too.
    steps = max(2, int(duration / dt))
    tracks = {}
    history = {}
    for body in dyn_bodies:
        tracks[body] = {"tx": {}, "ty": {}, "rotation": {}, "vx": {}, "vy": {}}
        history[body] = []

    for s in range(steps + 1):
        t = s / steps
        for body in dyn_bodies:
            tracks[body]["tx"][t] = body.pos.x
            tracks[body]["ty"][t] = body.pos.y
            tracks[body]["rotation"][t] = body.rotation
            tracks[body]["vx"][t] = body.vel.x
            tracks[body]["vy"][t] = body.vel.y
            history[body].append(body.pos)
        if s < steps:
            world._step(dt)

    event_counts, sampled_collision_points, collision_point_count = summarize_physics_events(
        world.events,
        marker_cap=event_marker_cap,
    )

    # Overlay trail polylines.
    for body in dyn_bodies:
        pts = [p for i, p in enumerate(history[body]) if i % trail_step == 0]
        if len(pts) > 1:
            trail = Polyline(
                points=pts,
                smoothness=0.25,
                stroke=Colors.DarkGray.transparent(0.18),
                width=1.0,
            )
            canvas.add(trail)

    sampled_times = [ts for _, ts in sampled_collision_points]
    t_min = min(sampled_times) if sampled_times else 0.0
    t_max = max(sampled_times) if sampled_times else 0.0
    t_span = max(1e-9, t_max - t_min)
    for pt, ts in sampled_collision_points:
        age_norm = (t_max - ts) / t_span if sampled_times else 0.0
        alpha = clamp(0.56 * (1.0 - event_marker_fade * age_norm), 0.08, 0.56)
        canvas.add(
            Circle(
                r=2.6,
                fill=Colors.Crimson.transparent(alpha),
                stroke=Colors.Transparent,
                width=0.0,
            ).move_to(pt)
        )

    panel_w = 315
    panel_h = 146
    panel_center = Point(190, 168)
    canvas.add(
        Rect(
            w=panel_w,
            h=panel_h,
            fill=Colors.White.transparent(0.88),
            stroke=Colors.DarkGray.transparent(0.55),
            width=1.0,
        ).move_to(panel_center)
    )
    panel_lines = [
        "Event Diagnostics",
        f"before/after: {event_counts.get('world.before_step', 0)} / {event_counts.get('world.after_step', 0)}",
        f"collision start: {event_counts.get('world.collision_start', 0)}",
        f"collision persist: {event_counts.get('world.collision_persist', 0)}",
        f"collision end: {event_counts.get('world.collision_end', 0)}",
        f"joint limit hits: {event_counts.get('joint.limit_hit', 0)}",
        f"constraint events: {event_counts.get('constraint.applied', 0)}",
        f"contact markers: {len(sampled_collision_points)} / {collision_point_count}",
    ]
    panel_top = panel_center.y - panel_h / 2 + 18
    for idx, line in enumerate(panel_lines):
        canvas.add(
            Text(
                line,
                size=14 if idx == 0 else 12,
                fill=Colors.DarkBlue if idx == 0 else Colors.Gray,
            ).move_to(Point(panel_center.x, panel_top + idx * 18))
        )

    # Build animations: body transform + velocity vector endpoint proxy.
    all_anims = []
    vector_pulses = []
    for body in dyn_bodies:
        shape = body.shape
        tx = tracks[body]["tx"]
        ty = tracks[body]["ty"]
        rr = tracks[body]["rotation"]
        vx = tracks[body]["vx"]
        vy = tracks[body]["vy"]

        all_anims.append(KeyframeAnimation(shape, tx=tx, ty=ty, rotation=rr))

        # Tip proxy drives vector endpoint.
        tip = Circle(r=0.0, fill=Colors.Transparent, stroke=Colors.Transparent, width=0.0)
        tip.move_to(Point(next(iter(tx.values())), next(iter(ty.values()))))
        canvas.add(tip)

        tip_tx = {}
        tip_ty = {}
        for k in tx.keys():
            tip_tx[k] = tx[k] + vx[k] * vector_scale
            tip_ty[k] = ty[k] + vy[k] * vector_scale
        all_anims.append(KeyframeAnimation(tip, tx=tip_tx, ty=tip_ty))

        vec = Arrow(
            p1=lambda s=shape: s.anchor("center"),
            p2=lambda tp=tip: tp.anchor("center"),
            stroke=Colors.MediumBlue.transparent(0.52),
            width=1.2,
            marker_end="arrow",
        )
        canvas.add(vec)
        vector_pulses.append(
            vec.animate.keyframes(width={0.0: 1.0, 0.5: 2.2, 1.0: 1.0}).repeating(2.4)
        )

    combined = Parallel(
        *all_anims,
        Delayed(*vector_pulses, lag_ratio=0.05),
    )

    scene = Scene(canvas, fps=fps, background="white")
    scene.play(combined, duration=duration)
    hook_trace: list[str] = []
    hook_counts = {"after_frame": 0}

    lifecycle_hooks = RenderLifecycleHooks(
        before_play=lambda _target, _cfg: hook_trace.append("before_play"),
        after_frame=lambda _idx, _total, _cfg: hook_counts.__setitem__(
            "after_frame", hook_counts["after_frame"] + 1
        ),
        before_save=lambda _path, _target, _cfg: hook_trace.append("before_save"),
        after_save=lambda _result, _cfg: hook_trace.append("after_save"),
    )
    result = render_scene(
        scene,
        RenderConfig(
            output_path=args.output,
            format=args.format,
            lifecycle_hooks=lifecycle_hooks,
        ),
    )
    print(f"✅ Saved: {result.output_path}")
    print(
        f"   balls={balls}, duration={duration:.1f}s, dt={dt:.3f}, "
        f"frames={int(duration * fps)}"
    )
    print(
        "   events="
        f"before:{event_counts.get('world.before_step', 0)} "
        f"after:{event_counts.get('world.after_step', 0)} "
        f"start:{event_counts.get('world.collision_start', 0)} "
        f"persist:{event_counts.get('world.collision_persist', 0)} "
        f"end:{event_counts.get('world.collision_end', 0)} "
        f"joint_limits:{event_counts.get('joint.limit_hit', 0)}"
    )
    print(f"   hooks={','.join(hook_trace)} after_frame={hook_counts['after_frame']}")

    if args.hook_log_json:
        payload = {
            "output_path": str(result.output_path),
            "hooks": hook_trace,
            "after_frame_count": hook_counts["after_frame"],
        }
        with open(args.hook_log_json, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)


if __name__ == "__main__":
    main()
