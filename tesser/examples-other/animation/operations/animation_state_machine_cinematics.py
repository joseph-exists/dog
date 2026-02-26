#!/usr/bin/env python3
"""State-machine cinematics stress test for Tesserax."""

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
    Rect,
    RenderConfig,
    Text,
    TimingSpec,
    render_scene,
)
from tesserax.animation import KeyframeAnimation, Parallel, Scene
from tesserax.normalized_export import NormalizedSceneTarget


STATES = ["PATROL", "INVESTIGATE", "CHASE", "EVADE", "RESOLVE", "IDLE"]


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Animated state-machine cinematics stress test.")
    p.add_argument("--duration", type=float, default=12.0, help="Animation seconds.")
    p.add_argument("--dt", type=float, default=0.03, help="Simulation time step.")
    p.add_argument("--fps", type=int, default=24, help="Render FPS.")
    p.add_argument("--seed", type=int, default=73, help="Random seed.")
    p.add_argument(
        "--camera-mode",
        choices=["track", "scripted", "hybrid"],
        default="hybrid",
        help="Camera cue mode.",
    )
    p.add_argument("--world-width", type=int, default=3000, help="World width.")
    p.add_argument("--world-height", type=int, default=2000, help="World height.")
    p.add_argument("--camera-width", type=float, default=960, help="Base camera width.")
    p.add_argument("--camera-height", type=float, default=620, help="Base camera height.")
    p.add_argument("--zoom-min", type=float, default=0.52, help="Minimum zoom factor.")
    p.add_argument("--zoom-max", type=float, default=1.02, help="Maximum zoom factor.")
    p.add_argument("--format", choices=["gif", "mp4"], default="gif", help="Output format.")
    p.add_argument(
        "--output",
        type=str,
        default="state_machine_cinematics.gif",
        help="Output path (extension adjusted to --format).",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)
    duration = max(0.8, args.duration)
    dt = max(0.005, args.dt)
    fps = max(1, args.fps)
    zmin = clamp(args.zoom_min, 0.10, 5.0)
    zmax = clamp(args.zoom_max, zmin + 0.01, 5.0)

    # World + static context.
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
        Text("State Machine Cinematics", size=38, fill=Colors.DarkBlue).move_to(
            Point(args.world_width / 2, 110)
        )
    )
    canvas.add(
        Text(
            f"camera_mode={args.camera_mode}  states={','.join(STATES)}",
            size=15,
            fill=Colors.Gray,
        ).move_to(Point(args.world_width / 2, 148))
    )

    for x in range(140, args.world_width, 260):
        canvas.add(
            Arrow(
                p1=Point(x, 220),
                p2=Point(x, args.world_height - 170),
                stroke=Colors.LightGray.transparent(0.26),
                width=1.0,
                marker_end=None,
            )
        )
    for y in range(220, args.world_height, 220):
        canvas.add(
            Arrow(
                p1=Point(120, y),
                p2=Point(args.world_width - 120, y),
                stroke=Colors.LightGray.transparent(0.26),
                width=1.0,
                marker_end=None,
            )
        )

    # Patrol waypoints.
    waypoints = [
        Point(420, args.world_height - 360),
        Point(880, args.world_height - 620),
        Point(1310, args.world_height - 430),
        Point(1680, args.world_height - 700),
        Point(2140, args.world_height - 500),
        Point(2480, args.world_height - 760),
    ]
    for i, p in enumerate(waypoints):
        canvas.add(Circle(r=8, fill=Colors.LightYellow, stroke=Colors.DarkGray, width=1.0).move_to(p))
        canvas.add(Text(str(i + 1), size=9, fill=Colors.Black).move_to(p))

    # Actors.
    agent = Circle(r=24, fill=Colors.DodgerBlue.transparent(0.9), stroke=Colors.DarkBlue, width=1.5)
    target = Circle(r=18, fill=Colors.DarkOrange.transparent(0.9), stroke=Colors.SaddleBrown, width=1.3)
    scout = Circle(r=14, fill=Colors.MediumVioletRed.transparent(0.84), stroke=Colors.Purple, width=1.2)
    agent.move_to(waypoints[0])
    target.move_to(Point(args.world_width - 560, 560))
    scout.move_to(Point(640, 520))
    canvas.add(agent, target, scout)

    canvas.add(Text("AGENT", size=13, fill=Colors.DarkBlue).move_to(agent.anchor("top").dy(-34)))
    canvas.add(Text("TARGET", size=12, fill=Colors.DarkRed).move_to(target.anchor("top").dy(-28)))
    canvas.add(Text("SCOUT", size=11, fill=Colors.Purple).move_to(scout.anchor("top").dy(-24)))

    # Dynamic relation lines.
    agent_target_link = Arrow(
        p1=lambda: agent.anchor("center"),
        p2=lambda: target.anchor("center"),
        stroke=Colors.MediumBlue.transparent(0.32),
        width=1.4,
        marker_end=None,
    )
    scout_target_link = Arrow(
        p1=lambda: scout.anchor("center"),
        p2=lambda: target.anchor("center"),
        stroke=Colors.MediumVioletRed.transparent(0.30),
        width=1.2,
        marker_end=None,
    )
    canvas.add(agent_target_link, scout_target_link)

    # FSM panel (in world space).
    panel_x = 330
    panel_y = 520
    row_h = 52
    panel = Rect(
        w=380,
        h=row_h * len(STATES) + 46,
        fill=Colors.White.transparent(0.88),
        stroke=Colors.DarkGray.transparent(0.6),
        width=1.2,
    ).move_to(Point(panel_x, panel_y))
    canvas.add(panel)
    canvas.add(Text("FSM", size=16, fill=Colors.Black).move_to(Point(panel_x, panel_y - (row_h * len(STATES)) / 2 - 12)))
    state_rows = {}
    top = panel_y - (row_h * (len(STATES) - 1)) / 2
    for i, s in enumerate(STATES):
        y = top + i * row_h
        state_rows[s] = y
        canvas.add(Text(s, size=12, fill=Colors.Black, anchor="start").move_to(Point(panel_x - 145, y)))
    state_indicator = Circle(r=8, fill=Colors.SeaGreen, stroke=Colors.DarkGreen, width=1.0).move_to(
        Point(panel_x - 168, state_rows["PATROL"])
    )
    canvas.add(state_indicator)

    # Camera.
    camera = Camera(width=args.camera_width, height=args.camera_height, active=True)
    camera.move_to(agent.anchor("center"))
    canvas.add(camera)

    # Tracks.
    tracks = {
        "agent_tx": {},
        "agent_ty": {},
        "agent_rot": {},
        "target_tx": {},
        "target_ty": {},
        "target_rot": {},
        "scout_tx": {},
        "scout_ty": {},
        "cam_tx": {},
        "cam_ty": {},
        "cam_w": {},
        "cam_h": {},
        "ind_ty": {},
    }

    state = "PATROL"
    state_entry = 0.0
    waypoint_idx = 1
    last_seen = target.anchor("center")
    evade_until = -1.0

    agent_pos = Point(waypoints[0].x, waypoints[0].y)
    agent_vel = Point(0, 0)
    target_prev = target.anchor("center")
    scout_phase = 0.0

    alarm_time = duration * 0.16
    resolve_time = duration * 0.78
    idle_time = duration * 0.92

    steps = max(2, int(duration / dt))
    transitions: list[tuple[float, str, str, str]] = []

    def set_state(t: float, new_state: str, reason: str) -> None:
        nonlocal state, state_entry
        if new_state != state:
            transitions.append((t, state, new_state, reason))
            state = new_state
            state_entry = t

    for s in range(steps + 1):
        t = s * dt
        if t > duration:
            t = duration
        k = s / steps

        # Target scripted motion + evade perturbation.
        cx = args.world_width * 0.62
        cy = args.world_height * 0.48
        base_x = cx + 720 * math.sin(0.45 * t + 0.35)
        base_y = cy + 380 * math.sin(0.83 * t)
        target_pos = Point(base_x, base_y)
        if state == "EVADE":
            target_pos = Point(
                target_pos.x + 170 * math.sin(4.2 * t),
                target_pos.y + 90 * math.cos(5.1 * t),
            )
        if state == "RESOLVE":
            meet = Point(args.world_width * 0.72, args.world_height * 0.67)
            alpha = clamp((t - resolve_time) / max(0.1, duration - resolve_time), 0, 1)
            target_pos = target_pos * (1 - alpha) + meet * alpha

        target_vel = target_pos - target_prev
        target_prev = target_pos
        dist = agent_pos.distance(target_pos)

        # Guard-based transitions.
        if state == "PATROL" and t >= alarm_time and dist < 950:
            last_seen = target_pos
            set_state(t, "INVESTIGATE", "sensor_trigger")
        elif state == "INVESTIGATE" and dist < 460:
            set_state(t, "CHASE", "target_in_range")
        elif state == "CHASE" and t > duration * 0.44 and dist < 210:
            evade_until = t + duration * 0.12
            set_state(t, "EVADE", "close_contact")
        elif state == "EVADE" and t >= evade_until:
            set_state(t, "CHASE", "evade_timeout")
        elif state in ("CHASE", "EVADE") and t >= resolve_time:
            set_state(t, "RESOLVE", "mission_phase")
        elif state == "RESOLVE" and t >= idle_time:
            set_state(t, "IDLE", "stabilized")

        # Agent behavior by state.
        if state == "PATROL":
            goal = waypoints[waypoint_idx]
            if agent_pos.distance(goal) < 40:
                waypoint_idx = (waypoint_idx + 1) % len(waypoints)
                goal = waypoints[waypoint_idx]
            speed = 260.0
        elif state == "INVESTIGATE":
            goal = last_seen
            speed = 320.0
        elif state == "CHASE":
            goal = target_pos
            speed = 420.0
        elif state == "EVADE":
            goal = target_pos
            speed = 520.0
        elif state == "RESOLVE":
            goal = Point(args.world_width * 0.70, args.world_height * 0.66)
            speed = 250.0
        else:
            goal = agent_pos
            speed = 0.0

        desired = (goal - agent_pos).normalize() * speed
        steer = (desired - agent_vel) * min(1.0, 3.6 * dt)
        agent_vel = agent_vel + steer
        if state == "IDLE":
            agent_vel = agent_vel * 0.90

        agent_pos = agent_pos + agent_vel * dt
        agent_pos = Point(
            clamp(agent_pos.x, 140, args.world_width - 140),
            clamp(agent_pos.y, 220, args.world_height - 150),
        )

        # Scout tracks target with lag.
        scout_phase += dt
        scout_goal = Point(
            target_pos.x + 180 * math.sin(0.8 * scout_phase),
            target_pos.y - 120 * math.cos(0.9 * scout_phase),
        )
        scout_pos = scout.anchor("center")
        scout_pos = scout_pos + (scout_goal - scout_pos) * min(1.0, 1.8 * dt)

        # Camera cues.
        if args.camera_mode == "track":
            cam_pos = agent_pos
            zoom = 0.86 if state in ("PATROL", "INVESTIGATE") else 0.68
        elif args.camera_mode == "scripted":
            cam_pos = Point(
                640 + (args.world_width - 980) * clamp(t / duration, 0, 1),
                1320 - 560 * math.sin((t / duration) * math.pi),
            )
            zoom = 0.78 + 0.22 * math.sin(2 * math.pi * (t / duration))
        else:  # hybrid
            if state in ("PATROL", "INVESTIGATE"):
                cam_pos = agent_pos * 0.75 + target_pos * 0.25
                zoom = 0.88
            elif state == "CHASE":
                cam_pos = agent_pos * 0.60 + target_pos * 0.40
                zoom = 0.66
            elif state == "EVADE":
                lead = target_pos + target_vel * 1.8
                cam_pos = agent_pos * 0.45 + lead * 0.55
                zoom = 0.56
            elif state == "RESOLVE":
                cam_pos = agent_pos * 0.55 + target_pos * 0.45
                zoom = 0.74
            else:
                cam_pos = agent_pos
                zoom = 0.92

        zoom = clamp(zoom, zmin, zmax)

        # Record tracks.
        tracks["agent_tx"][k] = agent_pos.x
        tracks["agent_ty"][k] = agent_pos.y
        tracks["agent_rot"][k] = math.atan2(agent_vel.y, agent_vel.x) if agent_vel.magnitude() > 1e-3 else 0.0

        tracks["target_tx"][k] = target_pos.x
        tracks["target_ty"][k] = target_pos.y
        tracks["target_rot"][k] = math.atan2(target_vel.y, target_vel.x) if target_vel.magnitude() > 1e-3 else 0.0

        tracks["scout_tx"][k] = scout_pos.x
        tracks["scout_ty"][k] = scout_pos.y

        tracks["cam_tx"][k] = cam_pos.x
        tracks["cam_ty"][k] = cam_pos.y
        tracks["cam_w"][k] = args.camera_width / zoom
        tracks["cam_h"][k] = args.camera_height / zoom

        tracks["ind_ty"][k] = state_rows[state]

    # Apply animations.
    anims = [
        KeyframeAnimation(
            agent,
            tx=tracks["agent_tx"],
            ty=tracks["agent_ty"],
            rotation=tracks["agent_rot"],
        ),
        KeyframeAnimation(
            target,
            tx=tracks["target_tx"],
            ty=tracks["target_ty"],
            rotation=tracks["target_rot"],
        ),
        KeyframeAnimation(scout, tx=tracks["scout_tx"], ty=tracks["scout_ty"]),
        KeyframeAnimation(
            camera,
            tx=tracks["cam_tx"],
            ty=tracks["cam_ty"],
            width=tracks["cam_w"],
            height=tracks["cam_h"],
        ),
        KeyframeAnimation(state_indicator, ty=tracks["ind_ty"]),
        agent_target_link.animate.keyframes(width={0.0: 1.0, 0.5: 2.6, 1.0: 1.0}).repeating(2.6),
        scout_target_link.animate.keyframes(width={0.0: 0.8, 0.5: 2.2, 1.0: 0.8}).repeating(2.2),
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
        f"   camera_mode={args.camera_mode}, duration={duration:.1f}s, fps={fps}, "
        f"transitions={len(transitions)}"
    )
    if transitions:
        for t, s0, s1, why in transitions[:8]:
            print(f"   t={t:5.2f}s  {s0} -> {s1}  ({why})")


if __name__ == "__main__":
    main()
