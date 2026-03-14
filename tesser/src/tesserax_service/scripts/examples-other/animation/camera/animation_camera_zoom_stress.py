#!/usr/bin/env python3
"""Camera zoom stress test with frame-size normalization for stable export."""

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
from tesserax.animation import Parallel, Scene
from tesserax.normalized_export import NormalizedSceneTarget


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Animated camera zoom stress test.")
    p.add_argument("--duration", type=float, default=10.0, help="Animation seconds.")
    p.add_argument("--fps", type=int, default=24, help="Capture FPS.")
    p.add_argument("--seed", type=int, default=61, help="Random seed.")
    p.add_argument("--world-width", type=int, default=3200, help="World width.")
    p.add_argument("--world-height", type=int, default=2200, help="World height.")
    p.add_argument("--camera-width", type=float, default=980, help="Initial camera width.")
    p.add_argument("--camera-height", type=float, default=620, help="Initial camera height.")
    p.add_argument("--zoom-min", type=float, default=0.45, help="Minimum zoom factor.")
    p.add_argument("--zoom-max", type=float, default=1.05, help="Maximum zoom factor.")
    p.add_argument("--zoom-cycles", type=float, default=3.0, help="Zoom pulse cycles.")
    p.add_argument(
        "--mode",
        choices=["hero", "scripted", "hybrid"],
        default="hybrid",
        help="Camera movement mode.",
    )
    p.add_argument("--format", choices=["gif", "mp4"], default="gif", help="Output format.")
    p.add_argument(
        "--output",
        type=str,
        default="camera_zoom_stress.gif",
        help="Output path (extension adjusted to --format).",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)
    duration = max(0.5, args.duration)
    fps = max(1, args.fps)
    zmin = clamp(args.zoom_min, 0.10, 10.0)
    zmax = clamp(args.zoom_max, zmin + 0.01, 10.0)
    cycles = max(0.2, args.zoom_cycles)

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
        Text("Camera Zoom Stress Test", size=40, fill=Colors.DarkBlue).move_to(
            Point(args.world_width / 2, 120)
        )
    )
    canvas.add(
        Text(
            f"mode={args.mode} zoom=[{zmin:.2f},{zmax:.2f}] cycles={cycles:.1f}",
            size=18,
            fill=Colors.Gray,
        ).move_to(Point(args.world_width / 2, 165))
    )

    # Rich scene geometry to expose zoom/detail changes.
    for x in range(140, args.world_width, 240):
        canvas.add(
            Arrow(
                p1=Point(x, 220),
                p2=Point(x, args.world_height - 180),
                stroke=Colors.LightGray.transparent(0.28),
                width=1.0,
                marker_end=None,
            )
        )
    for y in range(220, args.world_height, 210):
        canvas.add(
            Arrow(
                p1=Point(120, y),
                p2=Point(args.world_width - 120, y),
                stroke=Colors.LightGray.transparent(0.28),
                width=1.0,
                marker_end=None,
            )
        )

    for i in range(70):
        x = rng.uniform(180, args.world_width - 180)
        y = rng.uniform(280, args.world_height - 160)
        w = rng.uniform(28, 90)
        h = rng.uniform(18, 56)
        canvas.add(
            Rect(
                w=w,
                h=h,
                fill=Colors.Honeydew if i % 2 == 0 else Colors.MistyRose,
                stroke=Colors.Gray.transparent(0.6),
                width=0.8,
            ).move_to(Point(x, y))
        )

    hero = Circle(r=26, fill=Colors.DodgerBlue.transparent(0.9), stroke=Colors.DarkBlue, width=1.5)
    hero.move_to(Point(420, args.world_height - 360))
    escort = Circle(r=18, fill=Colors.DarkOrange.transparent(0.9), stroke=Colors.SaddleBrown, width=1.3)
    escort.move_to(Point(args.world_width - 480, 420))
    canvas.add(hero, escort)
    canvas.add(Text("HERO", size=14, fill=Colors.DarkBlue).move_to(hero.anchor("top").dy(-34)))
    canvas.add(Text("ESCORT", size=12, fill=Colors.DarkRed).move_to(escort.anchor("top").dy(-28)))

    hero_pts = [
        Point(420, args.world_height - 360),
        Point(1020, args.world_height - 620),
        Point(1560, 1080),
        Point(2130, 760),
        Point(2710, 1330),
        Point(args.world_width - 320, args.world_height - 320),
    ]
    escort_pts = [
        Point(args.world_width - 480, 420),
        Point(2470, 740),
        Point(1910, 520),
        Point(1460, 910),
        Point(980, 680),
        Point(540, 970),
    ]
    phase = [0.0, 0.20, 0.40, 0.62, 0.80, 1.0]
    hero_anim = hero.animate.keyframes(
        tx={t: p.x for t, p in zip(phase, hero_pts)},
        ty={t: p.y for t, p in zip(phase, hero_pts)},
    )
    escort_anim = escort.animate.keyframes(
        tx={t: p.x for t, p in zip(phase, escort_pts)},
        ty={t: p.y for t, p in zip(phase, escort_pts)},
    )

    camera = Camera(width=args.camera_width, height=args.camera_height, active=True)
    camera.move_to(hero.anchor("center"))
    canvas.add(camera)

    if args.mode == "hero":
        cam_move = camera.animate.track(hero)
    elif args.mode == "scripted":
        cam_move = camera.animate.keyframes(
            tx={0.0: 700, 0.3: 1320, 0.55: 1960, 0.8: 2550, 1.0: 2820},
            ty={0.0: 1420, 0.3: 980, 0.55: 740, 0.8: 1120, 1.0: 820},
        )
    else:  # hybrid
        cam_move = Parallel(
            camera.animate.track(hero),
            camera.animate.keyframes(
                tx={0.0: hero_pts[0].x, 0.45: hero_pts[2].x, 0.75: escort_pts[4].x, 1.0: hero_pts[-1].x},
                ty={0.0: hero_pts[0].y, 0.45: hero_pts[2].y, 0.75: escort_pts[4].y, 1.0: hero_pts[-1].y},
            ),
        )

    # Explicit zoom stress (camera size animation).
    z0 = 0.5 * (zmin + zmax)
    zoom_anim = camera.animate.keyframes(
        width={
            0.0: args.camera_width / z0,
            0.25: args.camera_width / zmax,
            0.50: args.camera_width / zmin,
            0.75: args.camera_width / zmax,
            1.0: args.camera_width / z0,
        },
        height={
            0.0: args.camera_height / z0,
            0.25: args.camera_height / zmax,
            0.50: args.camera_height / zmin,
            0.75: args.camera_height / zmax,
            1.0: args.camera_height / z0,
        },
    ).repeating(cycles)

    link = Arrow(
        p1=lambda: hero.anchor("center"),
        p2=lambda: escort.anchor("center"),
        stroke=Colors.MediumVioletRed.transparent(0.32),
        width=1.4,
        marker_end=None,
    )
    canvas.add(link)
    link_anim = link.animate.keyframes(width={0.0: 1.0, 0.5: 3.0, 1.0: 1.0}).repeating(2.2)

    combo = Parallel(hero_anim, escort_anim, cam_move, zoom_anim, link_anim)
    scene = Scene(canvas, fps=fps, background="white")
    scene.play(combo, duration=duration)

    # Stable export despite variable camera crop dimensions.
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
        f"   mode={args.mode}, duration={duration:.1f}s, fps={fps}, "
        f"zoom=[{zmin:.2f},{zmax:.2f}], cycles={cycles:.1f}"
    )


if __name__ == "__main__":
    main()
