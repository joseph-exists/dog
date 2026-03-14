#!/usr/bin/env python3
"""Camera tracking and cinematic view-control stress test for Tesserax."""

import argparse
import bisect
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
from tesserax.animation import Delayed, Parallel, Scene, Sequence


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def phase_reparam(phases: list[float]):
    """Map global normalized time -> waypoint index-progress normalized time."""
    if len(phases) < 2:
        return lambda t: max(0.0, min(1.0, t))

    u_values = [i / (len(phases) - 1) for i in range(len(phases))]

    def mapper(t: float) -> float:
        t_clamped = max(0.0, min(1.0, t))
        idx = bisect.bisect_right(phases, t_clamped) - 1
        idx = max(0, min(idx, len(phases) - 2))
        t0, t1 = phases[idx], phases[idx + 1]
        u0, u1 = u_values[idx], u_values[idx + 1]
        if t1 - t0 <= 1e-12:
            return u1
        local = (t_clamped - t0) / (t1 - t0)
        return u0 + (u1 - u0) * local

    return mapper


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Animated camera-track stress test.")
    p.add_argument(
        "--mode",
        choices=["track", "scripted", "hybrid", "switch"],
        default="hybrid",
        help="Camera behavior mode.",
    )
    p.add_argument("--duration", type=float, default=10.0, help="Animation seconds.")
    p.add_argument("--fps", type=int, default=24, help="Capture FPS.")
    p.add_argument("--seed", type=int, default=53, help="Random seed.")
    p.add_argument("--world-width", type=int, default=2800, help="World canvas width.")
    p.add_argument("--world-height", type=int, default=1800, help="World canvas height.")
    p.add_argument("--camera-width", type=float, default=840, help="Camera viewport width.")
    p.add_argument("--camera-height", type=float, default=520, help="Camera viewport height.")
    p.add_argument("--format", choices=["gif", "mp4"], default="gif", help="Output format.")
    p.add_argument(
        "--output",
        type=str,
        default="camera_track.gif",
        help="Output file path (extension adjusted to --format).",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)
    duration = max(0.5, args.duration)
    fps = max(1, args.fps)

    canvas = Canvas(width=args.world_width, height=args.world_height)

    # Background world frame.
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
        Text("Camera Track Capability Demo", size=34, fill=Colors.DarkBlue).move_to(
            Point(args.world_width / 2, 110)
        )
    )
    canvas.add(
        Text(
            f"mode={args.mode} world={args.world_width}x{args.world_height}",
            size=16,
            fill=Colors.Gray,
        ).move_to(Point(args.world_width / 2, 150))
    )

    # Draw a coarse world grid for motion perception.
    for x in range(160, args.world_width, 240):
        canvas.add(
            Arrow(
                p1=Point(x, 180),
                p2=Point(x, args.world_height - 160),
                stroke=Colors.LightGray.transparent(0.35),
                width=1.0,
                marker_end=None,
            )
        )
    for y in range(220, args.world_height, 220):
        canvas.add(
            Arrow(
                p1=Point(140, y),
                p2=Point(args.world_width - 140, y),
                stroke=Colors.LightGray.transparent(0.35),
                width=1.0,
                marker_end=None,
            )
        )

    # World landmarks.
    landmarks = []
    for i in range(14):
        x = 220 + (i % 7) * ((args.world_width - 440) / 6)
        y = 340 + (i // 7) * 760 + rng.uniform(-70, 70)
        lm = Rect(
            w=70,
            h=46,
            fill=Colors.Honeydew if i % 2 == 0 else Colors.MistyRose,
            stroke=Colors.DarkGray.transparent(0.6),
            width=1.0,
        ).move_to(Point(x, y))
        canvas.add(lm)
        canvas.add(Text(f"S{i+1}", size=11, fill=Colors.Black).move_to(Point(x, y)))
        landmarks.append(lm)

    # Two moving actors.
    hero = Circle(r=22, fill=Colors.DodgerBlue.transparent(0.90), stroke=Colors.DarkBlue, width=1.4)
    decoy = Circle(r=18, fill=Colors.DarkOrange.transparent(0.88), stroke=Colors.SaddleBrown, width=1.2)
    hero.move_to(Point(360, args.world_height - 320))
    decoy.move_to(Point(args.world_width - 440, 320))
    canvas.add(hero, decoy)
    canvas.add(Text("HERO", size=13, fill=Colors.DarkBlue).move_to(hero.anchor("top").dy(-30)))
    canvas.add(Text("DECOY", size=13, fill=Colors.DarkRed).move_to(decoy.anchor("top").dy(-26)))

    # Paths for actor keyframes.
    hero_path = [
        Point(360, args.world_height - 320),
        Point(920, args.world_height - 510),
        Point(1430, 980),
        Point(1880, 680),
        Point(2440, 1140),
        Point(args.world_width - 260, args.world_height - 260),
    ]
    decoy_path = [
        Point(args.world_width - 440, 320),
        Point(2220, 620),
        Point(1710, 380),
        Point(1310, 760),
        Point(900, 520),
        Point(460, 860),
    ]
    phases = [0.0, 0.18, 0.38, 0.60, 0.80, 1.0]
    hero_route = Polyline(hero_path, smoothness=0.18)
    decoy_route = Polyline(decoy_path, smoothness=0.18)

    pace = phase_reparam(phases)
    hero_spin = hero.animate.keyframes(rotation={0.0: 0.0, 0.5: 2 * math.pi, 1.0: 4 * math.pi})
    hero_move = hero.animate.follow(hero_route, rotate=False).rated(pace)
    decoy_move = decoy.animate.follow(decoy_route, rotate=False).rated(pace)
    hero_anim = Parallel(hero_move, hero_spin)
    decoy_anim = decoy_move

    # Dynamic vectors to help read motion.
    hero_link = Arrow(
        p1=lambda: hero.anchor("center"),
        p2=lambda: decoy.anchor("center"),
        stroke=Colors.MediumVioletRed.transparent(0.38),
        width=1.6,
        marker_end=None,
    )
    canvas.add(hero_link)

    # Camera configuration.
    camera = Camera(width=args.camera_width, height=args.camera_height, active=True)
    camera.move_to(hero.anchor("center"))
    canvas.add(camera)

    # Camera behavior modes.
    if args.mode == "track":
        cam_anim = camera.animate.track(hero, rotation=False)
    elif args.mode == "scripted":
        cam_anim = camera.animate.keyframes(
            tx={0.0: 520, 0.28: 1180, 0.55: 1800, 0.78: 2280, 1.0: 2580},
            ty={0.0: 1380, 0.28: 980, 0.55: 740, 0.78: 1020, 1.0: 760},
        )
    elif args.mode == "switch":
        cam_anim = Sequence(
            camera.animate.track(hero).weight(0.50),
            camera.animate.track(decoy).weight(0.50),
        )
    else:  # hybrid
        cam_anim = Sequence(
            camera.animate.track(hero).weight(0.55),
            camera.animate.keyframes(
                tx={0.0: hero_path[3].x, 1.0: decoy_path[3].x},
                ty={0.0: hero_path[3].y, 1.0: decoy_path[3].y},
            ).weight(0.15),
            camera.animate.track(decoy).weight(0.30),
        )

    combined = Parallel(
        hero_anim,
        decoy_anim,
        cam_anim,
        Delayed(
            hero_link.animate.keyframes(width={0.0: 1.2, 0.5: 2.8, 1.0: 1.2}).repeating(2.5),
            lag_ratio=0.0,
        ),
    )

    scene = Scene(canvas, fps=fps, background="white")
    scene.play(combined, duration=duration)

    result = render_scene(
        scene,
        RenderConfig(
            output_path=args.output,
            format=args.format,
            timing=TimingSpec(fps=fps, duration=duration, seed=args.seed),
        ),
    )
    print(f"✅ Saved: {result.output_path}")
    print(
        f"   mode={args.mode}, duration={duration:.1f}s, fps={fps}, "
        f"camera={args.camera_width:.0f}x{args.camera_height:.0f}"
    )


if __name__ == "__main__":
    main()
