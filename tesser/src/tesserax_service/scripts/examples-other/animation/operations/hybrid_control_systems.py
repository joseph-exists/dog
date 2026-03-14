#!/usr/bin/env python3
"""Hybrid control systems demo: discrete modes + continuous dynamics."""

import argparse
import math
import random

from tesserax import (
    Arrow,
    Camera,
    Canvas,
    Circle,
    Colors,
    Point,
    Polyline,
    Rect,
    RenderConfig,
    Text,
    TimingSpec,
    render_scene,
)
from tesserax.animation import KeyframeAnimation, Parallel, Scene
from tesserax.normalized_export import NormalizedSceneTarget


MODES = ["CRUISE", "AVOID", "RECOVER", "HOLD"]


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Hybrid control systems stress test.")
    p.add_argument("--duration", type=float, default=12.0, help="Simulation/animation seconds.")
    p.add_argument("--dt", type=float, default=0.03, help="Control integration step.")
    p.add_argument("--fps", type=int, default=24, help="Render FPS.")
    p.add_argument("--seed", type=int, default=131, help="Random seed.")
    p.add_argument("--obstacles", type=int, default=6, help="Obstacle count.")
    p.add_argument("--camera", choices=["track", "scripted", "hybrid"], default="hybrid")
    p.add_argument("--world-width", type=int, default=2800)
    p.add_argument("--world-height", type=int, default=1900)
    p.add_argument("--camera-width", type=float, default=920)
    p.add_argument("--camera-height", type=float, default=600)
    p.add_argument("--zoom-min", type=float, default=0.58)
    p.add_argument("--zoom-max", type=float, default=1.00)
    p.add_argument("--format", choices=["gif", "mp4"], default="gif")
    p.add_argument("--output", type=str, default="hybrid_control_systems.gif")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)
    duration = max(0.8, args.duration)
    dt = max(0.005, args.dt)
    fps = max(1, args.fps)
    zmin = clamp(args.zoom_min, 0.10, 5.0)
    zmax = clamp(args.zoom_max, zmin + 0.01, 5.0)

    canvas = Canvas(width=args.world_width, height=args.world_height)
    canvas.add(
        Rect(
            w=args.world_width,
            h=args.world_height,
            fill=Colors.White,
            stroke=Colors.Transparent,
            width=0,
        ).move_to(Point(args.world_width / 2, args.world_height / 2))
    )
    canvas.add(
        Text("Hybrid Control Systems", size=34, fill=Colors.DarkBlue).move_to(
            Point(args.world_width / 2, 92)
        )
    )
    canvas.add(
        Text(
            f"modes={','.join(MODES)} camera={args.camera} obstacles={args.obstacles}",
            size=14,
            fill=Colors.Gray,
        ).move_to(Point(args.world_width / 2, 126))
    )

    # World guides.
    for x in range(160, args.world_width, 260):
        canvas.add(
            Polyline(
                points=[Point(x, 180), Point(x, args.world_height - 140)],
                stroke=Colors.LightGray.transparent(0.26),
                width=1.0,
            )
        )
    for y in range(180, args.world_height, 230):
        canvas.add(
            Polyline(
                points=[Point(130, y), Point(args.world_width - 130, y)],
                stroke=Colors.LightGray.transparent(0.26),
                width=1.0,
            )
        )

    # Start/goal.
    start = Point(260, args.world_height - 260)
    goal = Point(args.world_width - 280, 280)
    canvas.add(Circle(r=18, fill=Colors.LightGreen, stroke=Colors.DarkGreen, width=1.3).move_to(start))
    canvas.add(Text("START", size=10, fill=Colors.DarkGreen).move_to(start.dy(-30)))
    canvas.add(Circle(r=20, fill=Colors.LightYellow, stroke=Colors.Goldenrod, width=1.3).move_to(goal))
    canvas.add(Text("GOAL", size=10, fill=Colors.DarkOrange).move_to(goal.dy(-32)))

    # Obstacles.
    obs = []
    for i in range(max(1, args.obstacles)):
        r = rng.uniform(52, 112)
        x = rng.uniform(560, args.world_width - 520)
        y = rng.uniform(320, args.world_height - 320)
        o = Circle(
            r=r,
            fill=Colors.MistyRose.transparent(0.45),
            stroke=Colors.Crimson.transparent(0.55),
            width=1.2,
        ).move_to(Point(x, y))
        canvas.add(o)
        obs.append((Point(x, y), r))

    # Agent + overlays.
    agent = Circle(r=24, fill=Colors.DodgerBlue.transparent(0.9), stroke=Colors.DarkBlue, width=1.5).move_to(start)
    canvas.add(agent)
    canvas.add(Text("AGENT", size=12, fill=Colors.DarkBlue).move_to(agent.anchor("top").dy(-34)))
    vel_tip = Circle(r=0.0, fill=Colors.Transparent, stroke=Colors.Transparent, width=0.0).move_to(start)
    canvas.add(vel_tip)
    vel_vec = Arrow(
        p1=lambda: agent.anchor("center"),
        p2=lambda: vel_tip.anchor("center"),
        stroke=Colors.MediumBlue.transparent(0.50),
        width=1.5,
        marker_end="arrow",
    )
    canvas.add(vel_vec)

    # FSM panel.
    panel_x, panel_y = 360, 560
    row_h = 54
    canvas.add(
        Rect(
            w=340,
            h=row_h * len(MODES) + 44,
            fill=Colors.White.transparent(0.9),
            stroke=Colors.DarkGray.transparent(0.6),
            width=1.1,
        ).move_to(Point(panel_x, panel_y))
    )
    canvas.add(Text("Hybrid Mode", size=16, fill=Colors.Black).move_to(Point(panel_x, panel_y - (row_h * len(MODES)) / 2 - 14)))
    mode_y = {}
    y0 = panel_y - (row_h * (len(MODES) - 1)) / 2
    for i, m in enumerate(MODES):
        yy = y0 + i * row_h
        mode_y[m] = yy
        canvas.add(Text(m, size=12, fill=Colors.Black, anchor="start").move_to(Point(panel_x - 120, yy)))
    mode_dot = Circle(r=8, fill=Colors.SeaGreen, stroke=Colors.DarkGreen, width=1.0).move_to(Point(panel_x - 142, mode_y["CRUISE"]))
    canvas.add(mode_dot)

    # Camera.
    camera = Camera(width=args.camera_width, height=args.camera_height, active=True).move_to(start)
    canvas.add(camera)

    # Tracks.
    tracks = {
        "agent_tx": {},
        "agent_ty": {},
        "agent_rot": {},
        "tip_tx": {},
        "tip_ty": {},
        "mode_ty": {},
        "cam_tx": {},
        "cam_ty": {},
        "cam_w": {},
        "cam_h": {},
    }
    trail_pts = []
    transitions: list[tuple[float, str, str, str]] = []

    # State.
    mode = "CRUISE"
    mode_enter = 0.0
    pos = Point(start.x, start.y)
    vel = Point(0, 0)
    hold_until = -1.0
    recover_until = -1.0

    steps = max(2, int(duration / dt))
    for s in range(steps + 1):
        t = min(duration, s * dt)
        k = s / steps

        def set_mode(new_mode: str, reason: str) -> None:
            nonlocal mode, mode_enter, hold_until, recover_until
            if new_mode != mode:
                transitions.append((t, mode, new_mode, reason))
                mode = new_mode
                mode_enter = t
                if new_mode == "HOLD":
                    hold_until = t + 0.8
                if new_mode == "RECOVER":
                    recover_until = t + 1.6

        # Sensing.
        to_goal = goal - pos
        dist_goal = to_goal.magnitude()
        nearest = None
        nearest_dist = 1e9
        for c, r in obs:
            d = pos.distance(c) - r
            if d < nearest_dist:
                nearest_dist = d
                nearest = (c, r)

        # Guards.
        if mode == "CRUISE" and nearest_dist < 240:
            set_mode("AVOID", "obstacle_near")
        elif mode == "AVOID" and nearest_dist > 300:
            set_mode("RECOVER", "clearance")
        elif mode == "RECOVER" and t >= recover_until:
            set_mode("CRUISE", "recover_done")
        elif mode in ("CRUISE", "RECOVER") and dist_goal < 190:
            set_mode("HOLD", "goal_reached")
        elif mode == "HOLD" and t >= hold_until:
            set_mode("CRUISE", "hold_done")

        # Control law by mode.
        if mode == "CRUISE":
            desired = to_goal.normalize() * 360
            steer_gain = 2.5
            damp = 0.96
        elif mode == "AVOID":
            c, r = nearest if nearest else (goal, 0)
            away = (pos - c).normalize() * 420
            tangent = Point(-away.y, away.x) * 0.45
            goal_pull = to_goal.normalize() * 110
            desired = away + tangent + goal_pull
            steer_gain = 4.6
            damp = 0.90
        elif mode == "RECOVER":
            desired = to_goal.normalize() * 290
            steer_gain = 2.2
            damp = 0.95
        else:  # HOLD
            desired = Point(0, 0)
            steer_gain = 4.0
            damp = 0.82

        acc = (desired - vel) * steer_gain
        vel = vel + acc * dt
        vel = vel * damp
        speed = vel.magnitude()
        if speed > 520:
            vel = vel.normalize() * 520
        pos = pos + vel * dt

        # bounds
        pos = Point(
            clamp(pos.x, 120, args.world_width - 120),
            clamp(pos.y, 180, args.world_height - 120),
        )
        trail_pts.append(pos)

        # Camera cues.
        if args.camera == "track":
            cam_pos = pos
            zoom = 0.86 if mode in ("CRUISE", "RECOVER") else 0.64
        elif args.camera == "scripted":
            cam_pos = Point(
                620 + (args.world_width - 1000) * clamp(t / duration, 0, 1),
                1450 - 640 * math.sin((t / duration) * math.pi),
            )
            zoom = 0.75 + 0.2 * math.sin(2 * math.pi * (t / duration))
        else:  # hybrid
            if mode == "AVOID":
                c, _ = nearest if nearest else (goal, 0)
                cam_pos = pos * 0.62 + c * 0.38
                zoom = 0.58
            elif mode == "HOLD":
                cam_pos = pos * 0.5 + goal * 0.5
                zoom = 0.92
            else:
                cam_pos = pos * 0.74 + goal * 0.26
                zoom = 0.78
        zoom = clamp(zoom, zmin, zmax)

        # record tracks
        tracks["agent_tx"][k] = pos.x
        tracks["agent_ty"][k] = pos.y
        tracks["agent_rot"][k] = math.atan2(vel.y, vel.x) if vel.magnitude() > 1e-4 else 0.0
        tracks["tip_tx"][k] = pos.x + vel.x * 0.20
        tracks["tip_ty"][k] = pos.y + vel.y * 0.20
        tracks["mode_ty"][k] = mode_y[mode]
        tracks["cam_tx"][k] = cam_pos.x
        tracks["cam_ty"][k] = cam_pos.y
        tracks["cam_w"][k] = args.camera_width / zoom
        tracks["cam_h"][k] = args.camera_height / zoom

    # add static trail
    if len(trail_pts) > 1:
        canvas.add(
            Polyline(
                points=trail_pts,
                smoothness=0.35,
                stroke=Colors.DarkGray.transparent(0.26),
                width=1.2,
            )
        )

    anims = [
        KeyframeAnimation(
            agent,
            tx=tracks["agent_tx"],
            ty=tracks["agent_ty"],
            rotation=tracks["agent_rot"],
        ),
        KeyframeAnimation(vel_tip, tx=tracks["tip_tx"], ty=tracks["tip_ty"]),
        KeyframeAnimation(mode_dot, ty=tracks["mode_ty"]),
        KeyframeAnimation(
            camera,
            tx=tracks["cam_tx"],
            ty=tracks["cam_ty"],
            width=tracks["cam_w"],
            height=tracks["cam_h"],
        ),
        vel_vec.animate.keyframes(width={0.0: 1.1, 0.5: 2.5, 1.0: 1.1}).repeating(2.8),
    ]

    scene = Scene(canvas, fps=fps, background="white")
    scene.play(Parallel(*anims), duration=duration)

    target = NormalizedSceneTarget(
        scene=scene,
        out_width=int(args.camera_width),
        out_height=int(args.camera_height),
    )
    result = render_scene(
        target,
        RenderConfig(
            output_path=args.output,
            format=args.format,
            timing=TimingSpec(fps=fps, duration=duration, seed=args.seed),
        ),
    )
    out = result.output_path

    print(f"✅ Saved: {out}")
    print(
        f"   camera={args.camera} duration={duration:.1f}s dt={dt:.3f} "
        f"transitions={len(transitions)}"
    )
    for t, m0, m1, why in transitions[:10]:
        print(f"   t={t:5.2f}s  {m0} -> {m1}  ({why})")


if __name__ == "__main__":
    main()
