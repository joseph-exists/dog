#!/usr/bin/env python3
"""Feynman-like interaction diagram stress test for Tesserax."""

import argparse
import math
import random
from dataclasses import dataclass
from pathlib import Path

from tesserax import Arrow, Canvas, Circle, Colors, Point, Polyline, Rect, Text, RenderConfig, TimingSpec, render_scene
from tesserax.animation import Delayed, Parallel, Scene


@dataclass
class EdgeSpec:
    kind: str  # fermion | photon | gluon
    points: list[Point]
    color: object
    width: float


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def line_points(a: Point, b: Point, steps: int = 40) -> list[Point]:
    pts = []
    for i in range(steps + 1):
        t = i / steps
        pts.append(a + (b - a) * t)
    return pts


def wave_points(
    a: Point,
    b: Point,
    amp: float,
    cycles: float,
    steps: int = 120,
    phase: float = 0.0,
) -> list[Point]:
    d = b - a
    n = Point(-d.y, d.x).normalize()
    pts = []
    for i in range(steps + 1):
        t = i / steps
        base = a + d * t
        off = amp * math.sin((2 * math.pi * cycles * t) + phase)
        pts.append(base + n * off)
    return pts


def coil_points(
    a: Point,
    b: Point,
    amp: float,
    cycles: float,
    steps: int = 180,
) -> list[Point]:
    d = b - a
    n = Point(-d.y, d.x).normalize()
    tdir = d.normalize()
    pts = []
    for i in range(steps + 1):
        t = i / steps
        base = a + d * t
        off_n = amp * math.sin(2 * math.pi * cycles * t)
        off_t = 0.35 * amp * math.sin(4 * math.pi * cycles * t + math.pi / 4)
        pts.append(base + n * off_n + tdir * off_t)
    return pts


def packet_keyframes(
    packet: Circle,
    pts: list[Point],
    start: float,
    travel: float,
) -> object:
    tx: dict[float, float] = {}
    ty: dict[float, float] = {}
    sx: dict[float, float] = {}
    sy: dict[float, float] = {}

    def stamp(t: float, p: Point) -> None:
        t = clamp(t, 0.0, 1.0)
        tx[t] = p.x
        ty[t] = p.y

    stamp(0.0, pts[0])
    stamp(start, pts[0])
    eps = 0.01
    sx[0.0] = 0.0
    sy[0.0] = 0.0
    sx[clamp(start + eps, 0, 1)] = 1.0
    sy[clamp(start + eps, 0, 1)] = 1.0

    seg = travel / max(1, len(pts) - 1)
    t = start
    for p in pts[1:]:
        t += seg
        stamp(t, p)

    hide = clamp(t + eps, 0, 1)
    sx[hide] = 0.0
    sy[hide] = 0.0
    sx[1.0] = 0.0
    sy[1.0] = 0.0
    stamp(1.0, pts[-1])

    return packet.animate.keyframes(tx=tx, ty=ty, sx=sx, sy=sy)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Animated Feynman-like interaction stress test.")
    p.add_argument(
        "--style",
        choices=["qed", "qcd", "mixed"],
        default="mixed",
        help="Interaction family to render.",
    )
    p.add_argument("--packets", type=int, default=260, help="Animated quanta/packet count.")
    p.add_argument("--duration", type=float, default=10.0, help="Animation seconds.")
    p.add_argument("--fps", type=int, default=24, help="Capture FPS.")
    p.add_argument("--wave-amp", type=float, default=12.0, help="Wave/coil amplitude.")
    p.add_argument("--wave-cycles", type=float, default=7.0, help="Wave/coil cycle count.")
    p.add_argument("--edge-pulses", type=int, default=18, help="Number of propagators with pulse animation.")
    p.add_argument("--seed", type=int, default=83, help="Random seed.")
    p.add_argument("--width", type=int, default=1800, help="Canvas width.")
    p.add_argument("--height", type=int, default=1000, help="Canvas height.")
    p.add_argument("--format", choices=["gif", "mp4"], default="gif", help="Output format.")
    p.add_argument(
        "--output",
        type=str,
        default="feynman_like_interactions.gif",
        help="Output path (extension adjusted to --format).",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)
    packets = max(1, args.packets)
    duration = max(0.6, args.duration)
    fps = max(1, args.fps)
    amp = max(1.0, args.wave_amp)
    cycles = max(1.0, args.wave_cycles)

    canvas = Canvas(width=args.width, height=args.height)
    canvas.add(
        Rect(
            w=args.width,
            h=args.height,
            fill=Colors.White,
            stroke=Colors.Transparent,
            width=0,
        ).move_to(Point(args.width / 2, args.height / 2))
    )
    canvas.add(Text("Feynman-like Interaction Stress Test", size=30, fill=Colors.DarkBlue).move_to(Point(args.width / 2, 52)))
    canvas.add(
        Text(
            f"style={args.style} packets={packets} wave_amp={amp:.1f} wave_cycles={cycles:.1f}",
            size=13,
            fill=Colors.Gray,
        ).move_to(Point(args.width / 2, 82))
    )

    # Canonical vertices (roughly left-to-right scattering layout).
    v = {
        "in_top": Point(220, 260),
        "in_bot": Point(220, 760),
        "v1": Point(700, 500),
        "v2": Point(1120, 500),
        "out_top": Point(1580, 260),
        "out_bot": Point(1580, 760),
        "gluon_top": Point(930, 250),
        "gluon_bot": Point(930, 760),
    }

    # Draw labeled vertices.
    for name in ["v1", "v2", "gluon_top", "gluon_bot"]:
        canvas.add(Circle(r=8, fill=Colors.Black, stroke=Colors.Black, width=1).move_to(v[name]))
    canvas.add(Text("e⁻", size=18, fill=Colors.Black).move_to(v["in_top"].dx(-55)))
    canvas.add(Text("e⁺", size=18, fill=Colors.Black).move_to(v["in_bot"].dx(-55)))
    canvas.add(Text("μ⁻", size=18, fill=Colors.Black).move_to(v["out_top"].dx(55)))
    canvas.add(Text("μ⁺", size=18, fill=Colors.Black).move_to(v["out_bot"].dx(55)))

    edges: list[EdgeSpec] = []

    # Fermion lines (straight with arrows).
    fermion_color = Colors.DarkBlue.transparent(0.75)
    if args.style in ("qed", "mixed"):
        qed_fermions = [
            ("in_top", "v1"),
            ("in_bot", "v1"),
            ("v2", "out_top"),
            ("v2", "out_bot"),
        ]
        for a, b in qed_fermions:
            p1, p2 = v[a], v[b]
            arrow = Arrow(
                p1=p1,
                p2=p2,
                stroke=fermion_color,
                width=2.0,
                marker_end="arrow",
            )
            canvas.add(arrow)
            edges.append(
                EdgeSpec(
                    kind="fermion",
                    points=line_points(p1, p2, steps=46),
                    color=Colors.DodgerBlue,
                    width=2.0,
                )
            )

        # Photon propagator.
        photon_pts = wave_points(v["v1"], v["v2"], amp=amp, cycles=cycles, steps=180)
        photon = Polyline(
            points=photon_pts,
            stroke=Colors.DarkOrange.transparent(0.85),
            width=2.0,
            smoothness=0.0,
        )
        canvas.add(photon)
        canvas.add(Text("γ", size=18, fill=Colors.DarkOrange).move_to(v["v1"].d(210, -30)))
        edges.append(
            EdgeSpec(
                kind="photon",
                points=photon_pts,
                color=Colors.DarkOrange,
                width=2.0,
            )
        )

    if args.style in ("qcd", "mixed"):
        # Quark lines.
        q_edges = [
            (Point(300, 420), v["gluon_top"]),
            (Point(300, 620), v["gluon_bot"]),
            (v["gluon_top"], Point(1530, 420)),
            (v["gluon_bot"], Point(1530, 620)),
        ]
        for p1, p2 in q_edges:
            q = Arrow(
                p1=p1,
                p2=p2,
                stroke=Colors.SeaGreen.transparent(0.78),
                width=2.0,
                marker_end="arrow",
            )
            canvas.add(q)
            edges.append(
                EdgeSpec(
                    kind="fermion",
                    points=line_points(p1, p2, steps=52),
                    color=Colors.SeaGreen,
                    width=2.0,
                )
            )

        # Gluon exchange (coils).
        g_pts = coil_points(v["gluon_top"], v["gluon_bot"], amp=amp * 0.95, cycles=cycles + 1.5, steps=220)
        gluon = Polyline(
            points=g_pts,
            stroke=Colors.MediumVioletRed.transparent(0.85),
            width=2.1,
            smoothness=0.0,
        )
        canvas.add(gluon)
        canvas.add(Text("g", size=18, fill=Colors.MediumVioletRed).move_to(v["gluon_top"].d(32, 250)))
        edges.append(
            EdgeSpec(
                kind="gluon",
                points=g_pts,
                color=Colors.MediumVioletRed,
                width=2.1,
            )
        )

    # Vertex pulse animations.
    vertices = []
    for name in ["v1", "v2", "gluon_top", "gluon_bot"]:
        dot = Circle(r=8, fill=Colors.Black, stroke=Colors.Black, width=1).move_to(v[name])
        dot.hide()
        canvas.add(dot)
        vertices.append(dot)
    vertex_pulses = [
        dot.animate.keyframes(
            sx={0.0: 1.0, 0.5: 1.45, 1.0: 1.0},
            sy={0.0: 1.0, 0.5: 1.45, 1.0: 1.0},
            width={0.0: 1.0, 0.5: 2.8, 1.0: 1.0},
        ).repeating(3.0)
        for dot in vertices
    ]

    # Optional propagator pulse subset.
    pulse_anims = []
    pulse_count = min(args.edge_pulses, len(edges))
    for e in rng.sample(edges, k=pulse_count) if pulse_count > 0 else []:
        # Attach a thin helper polyline to pulse width on top of existing edge.
        overlay = Polyline(
            points=e.points,
            stroke=e.color.transparent(0.45),
            width=e.width,
            smoothness=0.0,
        )
        canvas.add(overlay)
        pulse_anims.append(
            overlay.animate.keyframes(width={0.0: e.width, 0.5: e.width * 1.8, 1.0: e.width}).repeating(2.4)
        )

    # Moving packets along propagators.
    packet_anims = []
    for i in range(packets):
        e = rng.choice(edges)
        p = Circle(
            r=3.2 + (i % 2) * 0.8,
            fill=e.color.transparent(0.92),
            stroke=Colors.Black.transparent(0.2),
            width=0.4,
        )
        p.move_to(e.points[0])
        canvas.add(p)

        start = rng.uniform(0.0, 0.72) + (i % 11) * 0.006
        travel = rng.uniform(0.10, 0.30)
        if start + travel > 0.98:
            travel = 0.98 - start
        packet_anims.append(packet_keyframes(p, e.points, start=start, travel=max(0.06, travel)))

    combined = Parallel(
        *packet_anims,
        *pulse_anims,
        Delayed(*vertex_pulses, lag_ratio=0.05),
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
    out = result.output_path
    print(f"✅ Saved: {out}")
    print(f"   style={args.style}, edges={len(edges)}, packets={packets}, frames={int(duration * fps)}")


if __name__ == "__main__":
    main()
