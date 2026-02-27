#!/usr/bin/env python3
"""Supply-chain resilience animation stress test for Tesserax.

This script models a small logistics network with:
- directed shipment routes and capacities
- disruption windows that degrade selected routes
- adaptive rerouting through alternate paths
- inventory/backlog dynamics at hubs and stores

The output is an animated network with moving shipment packets, node stress halos,
and a phase indicator panel.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path

from tesserax import Arrow, Camera, Canvas, Circle, Colors, Point, Rect, Text, RenderConfig, TimingSpec, render_scene
from tesserax.animation import KeyframeAnimation, Parallel, Scene


PHASES = ["NORMAL", "DISRUPTION", "ADAPT", "RECOVERY"]


@dataclass
class Node:
    name: str
    tier: str
    pos: Point
    inventory: float
    target_inventory: float
    demand_rate: float


@dataclass
class Route:
    name: str
    src: str
    dst: str
    transit: float
    capacity: float
    category: str


@dataclass
class Shipment:
    src: str
    dst: str
    amount: float
    depart_t: float
    arrive_t: float


@dataclass
class PacketRecord:
    src: Point
    dst: Point
    start: float
    end: float
    color: Colors


@dataclass
class ScenarioPreset:
    demand_scale: float
    supply_rate: float
    shock_start_ratio: float
    shock_duration_ratio: float
    shock_severity: float
    demand_spike: float
    shock_target: str
    store_spike: str
    route_capacity_scale: float
    alt_route_boost: float
    hub_balance_gain: float
    backlog_relief_rate: float


SCENARIOS = {
    "baseline": ScenarioPreset(
        demand_scale=1.0,
        supply_rate=12.0,
        shock_start_ratio=0.30,
        shock_duration_ratio=0.26,
        shock_severity=0.88,
        demand_spike=1.60,
        shock_target="west",
        store_spike="A",
        route_capacity_scale=1.0,
        alt_route_boost=1.0,
        hub_balance_gain=0.35,
        backlog_relief_rate=0.30,
    ),
    "port_strike": ScenarioPreset(
        demand_scale=1.0,
        supply_rate=11.0,
        shock_start_ratio=0.22,
        shock_duration_ratio=0.36,
        shock_severity=0.95,
        demand_spike=1.25,
        shock_target="west",
        store_spike="A",
        route_capacity_scale=0.95,
        alt_route_boost=1.25,
        hub_balance_gain=0.48,
        backlog_relief_rate=0.24,
    ),
    "demand_surge": ScenarioPreset(
        demand_scale=1.20,
        supply_rate=12.5,
        shock_start_ratio=0.28,
        shock_duration_ratio=0.24,
        shock_severity=0.68,
        demand_spike=2.10,
        shock_target="west",
        store_spike="both",
        route_capacity_scale=1.0,
        alt_route_boost=1.15,
        hub_balance_gain=0.42,
        backlog_relief_rate=0.22,
    ),
    "multi_shock": ScenarioPreset(
        demand_scale=1.12,
        supply_rate=11.8,
        shock_start_ratio=0.20,
        shock_duration_ratio=0.45,
        shock_severity=0.92,
        demand_spike=1.90,
        shock_target="both",
        store_spike="both",
        route_capacity_scale=0.92,
        alt_route_boost=1.35,
        hub_balance_gain=0.56,
        backlog_relief_rate=0.20,
    ),
}


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def choose(value: float | str | None, fallback: float | str) -> float | str:
    return fallback if value is None else value


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Animated supply-chain resilience stress test.")
    p.add_argument("--duration", type=float, default=12.0, help="Animation seconds.")
    p.add_argument("--dt", type=float, default=0.04, help="Simulation step (seconds).")
    p.add_argument("--fps", type=int, default=24, help="Render FPS.")
    p.add_argument("--seed", type=int, default=211, help="Random seed.")
    p.add_argument(
        "--scenario",
        choices=sorted(SCENARIOS.keys()),
        default="baseline",
        help="Scenario preset. Other tunables can override preset values.",
    )
    p.add_argument(
        "--policy",
        choices=["balanced", "service_first", "cost_first"],
        default="balanced",
        help="Dispatch policy profile for fulfillment and reroute aggressiveness.",
    )

    p.add_argument("--demand-scale", type=float, default=None, help="Store demand multiplier.")
    p.add_argument("--supply-rate", type=float, default=None, help="Per-port replenishment units/sec.")
    p.add_argument(
        "--route-capacity-scale",
        type=float,
        default=None,
        help="Global multiplier applied to all route capacities.",
    )
    p.add_argument(
        "--alt-route-boost",
        type=float,
        default=None,
        help="Multiplier for alternate route utilization.",
    )
    p.add_argument(
        "--hub-balance-gain",
        type=float,
        default=None,
        help="How aggressively hubs rebalance stock between each other.",
    )
    p.add_argument(
        "--backlog-relief-rate",
        type=float,
        default=None,
        help="Rate for backlog conversion using available store inventory.",
    )

    p.add_argument(
        "--shock-start-ratio",
        type=float,
        default=None,
        help="Disruption start as ratio of total duration.",
    )
    p.add_argument(
        "--shock-duration-ratio",
        type=float,
        default=None,
        help="Disruption duration as ratio of total duration.",
    )
    p.add_argument(
        "--shock-severity",
        type=float,
        default=None,
        help="Capacity loss ratio on disrupted corridors (0..1).",
    )
    p.add_argument(
        "--demand-spike",
        type=float,
        default=None,
        help="Demand multiplier for impacted store(s) during disruption.",
    )
    p.add_argument(
        "--shock-target",
        choices=["none", "west", "east", "both"],
        default=None,
        help="Which corridor(s) receive capacity shock.",
    )
    p.add_argument(
        "--store-spike",
        choices=["none", "A", "B", "both"],
        default=None,
        help="Which store(s) receive demand spike during disruption.",
    )

    p.add_argument(
        "--camera-mode",
        choices=["fixed", "track", "hybrid"],
        default="hybrid",
        help="Camera behavior mode.",
    )
    p.add_argument("--world-width", type=int, default=2500, help="World width.")
    p.add_argument("--world-height", type=int, default=1550, help="World height.")
    p.add_argument("--camera-width", type=float, default=980, help="Camera width.")
    p.add_argument("--camera-height", type=float, default=620, help="Camera height.")

    p.add_argument(
        "--packets-max",
        type=int,
        default=480,
        help="Max visible shipment packets (simulation can exceed this).",
    )
    p.add_argument(
        "--packet-size",
        type=float,
        default=6.0,
        help="Units per rendered shipment packet.",
    )

    p.add_argument("--format", choices=["gif", "mp4"], default="gif", help="Output format.")
    p.add_argument(
        "--report-json",
        type=str,
        default="",
        help="Optional JSON summary output for comparing scenario runs.",
    )
    p.add_argument(
        "--output",
        type=str,
        default="supply_chain_resilience.gif",
        help="Output file (extension adjusted to --format).",
    )
    return p.parse_args()


def build_network(
    width: int,
    height: int,
    demand_scale: float,
    route_capacity_scale: float,
) -> tuple[dict[str, Node], list[Route]]:
    cx = width / 2
    y_port = 260
    y_hub = 780
    y_store = 1260

    nodes = {
        "PORT_W": Node("PORT_W", "port", Point(cx - 700, y_port), 120.0, 160.0, 0.0),
        "PORT_E": Node("PORT_E", "port", Point(cx + 700, y_port), 120.0, 160.0, 0.0),
        "HUB_N": Node("HUB_N", "hub", Point(cx - 410, y_hub), 35.0, 80.0, 0.0),
        "HUB_S": Node("HUB_S", "hub", Point(cx + 410, y_hub), 35.0, 80.0, 0.0),
        "STORE_A": Node("STORE_A", "store", Point(cx - 440, y_store), 14.0, 40.0, 8.4 * demand_scale),
        "STORE_B": Node("STORE_B", "store", Point(cx + 440, y_store), 14.0, 40.0, 8.0 * demand_scale),
    }

    routes = [
        Route(
            "PW_HN",
            "PORT_W",
            "HUB_N",
            transit=1.0,
            capacity=18.0 * route_capacity_scale,
            category="primary",
        ),
        Route(
            "PW_HS",
            "PORT_W",
            "HUB_S",
            transit=1.7,
            capacity=6.0 * route_capacity_scale,
            category="alternate",
        ),
        Route(
            "PE_HS",
            "PORT_E",
            "HUB_S",
            transit=1.0,
            capacity=18.0 * route_capacity_scale,
            category="primary",
        ),
        Route(
            "PE_HN",
            "PORT_E",
            "HUB_N",
            transit=1.7,
            capacity=6.0 * route_capacity_scale,
            category="alternate",
        ),
        Route(
            "HN_HS",
            "HUB_N",
            "HUB_S",
            transit=1.25,
            capacity=7.0 * route_capacity_scale,
            category="balance",
        ),
        Route(
            "HS_HN",
            "HUB_S",
            "HUB_N",
            transit=1.25,
            capacity=7.0 * route_capacity_scale,
            category="balance",
        ),
        Route(
            "HN_SA",
            "HUB_N",
            "STORE_A",
            transit=0.9,
            capacity=9.0 * route_capacity_scale,
            category="primary",
        ),
        Route(
            "HN_SB",
            "HUB_N",
            "STORE_B",
            transit=1.5,
            capacity=4.0 * route_capacity_scale,
            category="alternate",
        ),
        Route(
            "HS_SB",
            "HUB_S",
            "STORE_B",
            transit=0.9,
            capacity=9.0 * route_capacity_scale,
            category="primary",
        ),
        Route(
            "HS_SA",
            "HUB_S",
            "STORE_A",
            transit=1.5,
            capacity=4.0 * route_capacity_scale,
            category="alternate",
        ),
    ]

    return nodes, routes


def edge_capacity_factor(
    route_name: str,
    t: float,
    shock_start: float,
    shock_end: float,
    severity: float,
    disrupted_routes: set[str],
) -> float:
    if shock_start <= t <= shock_end and route_name in disrupted_routes:
        return clamp(1.0 - severity, 0.02, 1.0)
    return 1.0


def phase_at(t: float, duration: float, shock_start: float, shock_end: float) -> str:
    if t < shock_start:
        return "NORMAL"
    if t <= shock_end:
        return "DISRUPTION"
    adapt_end = shock_end + 0.20 * duration
    if t <= adapt_end:
        return "ADAPT"
    return "RECOVERY"


def routes_for_shock_target(shock_target: str) -> set[str]:
    west = {"PW_HN", "HN_SA"}
    east = {"PE_HS", "HS_SB"}
    if shock_target == "west":
        return set(west)
    if shock_target == "east":
        return set(east)
    if shock_target == "both":
        return set(west | east)
    return set()


def demand_multiplier(store_name: str, store_spike: str, demand_spike: float) -> float:
    if store_spike == "none":
        return 1.0
    if store_spike == "both":
        return demand_spike
    if store_spike == "A" and store_name == "STORE_A":
        return demand_spike
    if store_spike == "B" and store_name == "STORE_B":
        return demand_spike
    return 1.0


def packet_keyframes(packet: Circle, rec: PacketRecord, duration: float) -> KeyframeAnimation:
    tx: dict[float, float] = {}
    ty: dict[float, float] = {}
    sx: dict[float, float] = {}
    sy: dict[float, float] = {}

    def stamp(at: float, p: Point) -> None:
        k = clamp(at / duration, 0.0, 1.0)
        tx[k] = p.x
        ty[k] = p.y

    stamp(0.0, rec.src)
    stamp(rec.start, rec.src)
    stamp(rec.end, rec.dst)
    stamp(duration, rec.dst)

    show_k = clamp((rec.start + 0.01 * duration) / duration, 0.0, 1.0)
    hide_k = clamp((rec.end + 0.01 * duration) / duration, 0.0, 1.0)
    sx[0.0] = 0.0
    sy[0.0] = 0.0
    sx[show_k] = 1.0
    sy[show_k] = 1.0
    sx[hide_k] = 0.0
    sy[hide_k] = 0.0
    sx[1.0] = 0.0
    sy[1.0] = 0.0

    return packet.animate.keyframes(tx=tx, ty=ty, sx=sx, sy=sy)


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)
    preset = SCENARIOS[args.scenario]

    duration = max(1.2, args.duration)
    dt = max(0.01, args.dt)
    fps = max(1, args.fps)
    packet_size = max(0.5, args.packet_size)
    packets_max = max(10, args.packets_max)
    demand_scale = float(choose(args.demand_scale, preset.demand_scale))
    supply_rate = float(choose(args.supply_rate, preset.supply_rate))
    shock_start_ratio = float(choose(args.shock_start_ratio, preset.shock_start_ratio))
    shock_duration_ratio = float(choose(args.shock_duration_ratio, preset.shock_duration_ratio))
    shock_severity = float(choose(args.shock_severity, preset.shock_severity))
    demand_spike = float(choose(args.demand_spike, preset.demand_spike))
    shock_target = str(choose(args.shock_target, preset.shock_target))
    store_spike = str(choose(args.store_spike, preset.store_spike))
    route_capacity_scale = float(choose(args.route_capacity_scale, preset.route_capacity_scale))
    alt_route_boost = float(choose(args.alt_route_boost, preset.alt_route_boost))
    hub_balance_gain = float(choose(args.hub_balance_gain, preset.hub_balance_gain))
    backlog_relief_rate = float(choose(args.backlog_relief_rate, preset.backlog_relief_rate))

    if args.policy == "service_first":
        forecast_mult = 1.40
        backlog_weight = 1.35
        alt_policy_boost = 1.55
        hub_policy_gain = 1.25
    elif args.policy == "cost_first":
        forecast_mult = 0.90
        backlog_weight = 0.82
        alt_policy_boost = 0.72
        hub_policy_gain = 0.82
    else:
        forecast_mult = 1.10
        backlog_weight = 1.00
        alt_policy_boost = 1.00
        hub_policy_gain = 1.00

    alt_route_boost *= alt_policy_boost
    hub_balance_gain *= hub_policy_gain

    shock_start = clamp(shock_start_ratio, 0.0, 0.95) * duration
    shock_end = clamp(shock_start_ratio + shock_duration_ratio, 0.02, 0.98) * duration
    shock_end = max(shock_end, shock_start + 0.2)
    disrupted_routes = routes_for_shock_target(shock_target)

    nodes, routes = build_network(
        args.world_width,
        args.world_height,
        demand_scale,
        route_capacity_scale,
    )
    route_by_name = {r.name: r for r in routes}
    route_shapes: dict[str, Arrow] = {}

    canvas = Canvas(width=args.world_width, height=args.world_height)
    canvas.add(
        Rect(
            w=args.world_width,
            h=args.world_height,
            fill=Colors.White,
            stroke=Colors.Transparent,
            width=0.0,
        ).move_to(Point(args.world_width / 2, args.world_height / 2))
    )
    canvas.add(
        Text("Supply Chain Resilience", size=34, fill=Colors.DarkBlue).move_to(
            Point(args.world_width / 2, 78)
        )
    )
    canvas.add(
        Text(
            f"scenario={args.scenario} policy={args.policy} shock_target={shock_target} store_spike={store_spike}",
            size=14,
            fill=Colors.Gray,
        ).move_to(Point(args.world_width / 2, 112))
    )

    # Tier guides.
    for y, label in [(260, "Ports"), (780, "Regional Hubs"), (1260, "Retail Stores")]:
        canvas.add(
            Arrow(
                p1=Point(170, y),
                p2=Point(args.world_width - 170, y),
                stroke=Colors.LightGray.transparent(0.26),
                width=1.0,
                marker_end=None,
            )
        )
        canvas.add(Text(label, size=12, fill=Colors.DarkGray, anchor="start").move_to(Point(145, y - 24)))

    # Routes.
    for r in routes:
        p1 = nodes[r.src].pos
        p2 = nodes[r.dst].pos
        curve = clamp((p2.x - p1.x) / 1800.0, -0.26, 0.26)
        stroke = Colors.MediumBlue.transparent(0.30) if r.category == "primary" else Colors.DarkOrange.transparent(0.28)
        if r.category == "balance":
            stroke = Colors.SeaGreen.transparent(0.30)

        edge = Arrow(
            p1=p1,
            p2=p2,
            curvature=curve,
            stroke=stroke,
            width=1.5,
            marker_end=None,
        )
        route_shapes[r.name] = edge
        canvas.add(edge)

    node_shapes: dict[str, Circle] = {}
    node_halos: dict[str, Circle] = {}
    node_bars: dict[str, Rect] = {}
    base_node_colors = {
        "port": Colors.LightYellow,
        "hub": Colors.LightCyan,
        "store": Colors.MistyRose,
    }
    for node in nodes.values():
        circle = Circle(
            r=32 if node.tier != "store" else 28,
            fill=base_node_colors[node.tier],
            stroke=Colors.DarkBlue.transparent(0.72),
            width=1.4,
        ).move_to(node.pos)
        halo = Circle(
            r=40 if node.tier != "store" else 36,
            fill=Colors.Transparent,
            stroke=Colors.Crimson.transparent(0.66),
            width=0.6,
        ).move_to(node.pos)
        bar = Rect(
            w=16,
            h=58,
            fill=Colors.SeaGreen.transparent(0.58),
            stroke=Colors.DarkGray.transparent(0.44),
            width=0.8,
        ).move_to(Point(node.pos.x + 52, node.pos.y))
        node_shapes[node.name] = circle
        node_halos[node.name] = halo
        node_bars[node.name] = bar
        canvas.add(halo, circle, bar)

        canvas.add(Text(node.name, size=10, fill=Colors.Black).move_to(node.pos))

    # Phase panel.
    panel_x = 360
    panel_y = 420
    row_h = 46
    panel = Rect(
        w=330,
        h=row_h * len(PHASES) + 44,
        fill=Colors.White.transparent(0.90),
        stroke=Colors.DarkGray.transparent(0.65),
        width=1.1,
    ).move_to(Point(panel_x, panel_y))
    canvas.add(panel)
    canvas.add(Text("Network Phase", size=15, fill=Colors.Black).move_to(Point(panel_x, panel_y - 118)))

    phase_rows: dict[str, float] = {}
    top = panel_y - (row_h * (len(PHASES) - 1)) / 2
    for i, ph in enumerate(PHASES):
        y = top + i * row_h
        phase_rows[ph] = y
        canvas.add(Text(ph, size=12, fill=Colors.Black, anchor="start").move_to(Point(panel_x - 110, y)))

    phase_indicator = Circle(r=8, fill=Colors.SeaGreen, stroke=Colors.DarkGreen, width=1.0).move_to(
        Point(panel_x - 132, phase_rows["NORMAL"])
    )
    canvas.add(phase_indicator)

    camera = Camera(width=args.camera_width, height=args.camera_height, active=True)
    camera.move_to(Point(args.world_width / 2, args.world_height / 2))
    canvas.add(camera)

    # Simulation state.
    in_transit: list[Shipment] = []
    packet_records: list[PacketRecord] = []
    backlog = {"STORE_A": 0.0, "STORE_B": 0.0}
    total_demand = {"STORE_A": 0.0, "STORE_B": 0.0}
    total_unmet = {"STORE_A": 0.0, "STORE_B": 0.0}
    peak_total_backlog = 0.0

    steps = max(2, int(duration / dt))
    tracks: dict[str, dict[float, float]] = {
        "phase_ty": {},
        "cam_tx": {},
        "cam_ty": {},
    }
    for name in nodes:
        tracks[f"halo_w_{name}"] = {}
        tracks[f"bar_sy_{name}"] = {}

    phase_counts = {ph: 0 for ph in PHASES}
    dispatch_total = 0

    def create_dispatch(route: Route, t: float, qty: float) -> None:
        nonlocal dispatch_total
        qty = max(0.0, qty)
        if qty <= 1e-6:
            return
        src_node = nodes[route.src]
        if src_node.inventory <= 0:
            return

        send_qty = min(qty, src_node.inventory)
        src_node.inventory -= send_qty
        dispatch_total += 1

        in_transit.append(
            Shipment(
                src=route.src,
                dst=route.dst,
                amount=send_qty,
                depart_t=t,
                arrive_t=t + route.transit,
            )
        )

        if len(packet_records) >= packets_max:
            return

        pieces = max(1, min(4, int(math.ceil(send_qty / packet_size))))
        for _ in range(pieces):
            if len(packet_records) >= packets_max:
                break
            jitter = rng.uniform(-0.06, 0.06)
            start_t = clamp(t + jitter, 0.0, duration)
            end_t = clamp(t + route.transit + jitter, start_t + 0.02, duration)
            color = Colors.MediumBlue if route.category == "primary" else Colors.DarkOrange
            if route.category == "balance":
                color = Colors.SeaGreen
            packet_records.append(
                PacketRecord(
                    src=nodes[route.src].pos,
                    dst=nodes[route.dst].pos,
                    start=start_t,
                    end=end_t,
                    color=color,
                )
            )

    for s in range(steps + 1):
        t = min(duration, s * dt)
        k = s / steps

        # Port replenishment.
        nodes["PORT_W"].inventory += supply_rate * dt
        nodes["PORT_E"].inventory += supply_rate * dt

        # Arrivals.
        remaining: list[Shipment] = []
        for shipment in in_transit:
            if shipment.arrive_t <= t:
                nodes[shipment.dst].inventory += shipment.amount
            else:
                remaining.append(shipment)
        in_transit = remaining

        # Demand consumption at stores.
        for store_name in ("STORE_A", "STORE_B"):
            d = nodes[store_name].demand_rate
            if shock_start <= t <= shock_end:
                d *= demand_multiplier(store_name, store_spike, max(1.0, demand_spike))
            need = d * dt
            available = nodes[store_name].inventory
            used = min(available, need)
            nodes[store_name].inventory -= used
            unmet = need - used
            backlog[store_name] += unmet
            total_demand[store_name] += need
            total_unmet[store_name] += unmet

        # Backlog relief from existing inventory.
        for store_name in ("STORE_A", "STORE_B"):
            relief = min(nodes[store_name].inventory * backlog_relief_rate * dt, backlog[store_name])
            nodes[store_name].inventory -= relief
            backlog[store_name] -= relief

        inbound = {name: 0.0 for name in nodes}
        for shipment in in_transit:
            inbound[shipment.dst] += shipment.amount

        # Route-specific capacity under disruption.
        cap = {}
        for r in routes:
            f = edge_capacity_factor(
                r.name,
                t,
                shock_start,
                shock_end,
                shock_severity,
                disrupted_routes,
            )
            cap[r.name] = r.capacity * f * dt

        # Port -> hub replenishment policy.
        for rn in ("PW_HN", "PE_HS", "PW_HS", "PE_HN"):
            r = route_by_name[rn]
            dst = nodes[r.dst]
            desired = max(0.0, dst.target_inventory + 18.0 - (dst.inventory + inbound[r.dst]))
            create_dispatch(r, t, min(cap[rn], desired))

        # Hub balancing when one side is stressed.
        h_n = nodes["HUB_N"].inventory
        h_s = nodes["HUB_S"].inventory
        if h_n > h_s + 16.0:
            create_dispatch(route_by_name["HN_HS"], t, min(cap["HN_HS"], (h_n - h_s) * hub_balance_gain))
        elif h_s > h_n + 16.0:
            create_dispatch(route_by_name["HS_HN"], t, min(cap["HS_HN"], (h_s - h_n) * hub_balance_gain))

        # Hub -> store fulfillment (prioritize backlog + near-term demand).
        need_a = backlog["STORE_A"] * backlog_weight + nodes["STORE_A"].demand_rate * forecast_mult * dt
        need_b = backlog["STORE_B"] * backlog_weight + nodes["STORE_B"].demand_rate * forecast_mult * dt

        # Primary flows first.
        create_dispatch(route_by_name["HN_SA"], t, min(cap["HN_SA"], need_a))
        create_dispatch(route_by_name["HS_SB"], t, min(cap["HS_SB"], need_b))

        # Alternate rerouting picks up residual pressure.
        residual_a = max(0.0, need_a - cap["HN_SA"])
        residual_b = max(0.0, need_b - cap["HS_SB"])
        alt_a = residual_a + (0.25 * alt_route_boost) * need_a
        alt_b = residual_b + (0.25 * alt_route_boost) * need_b
        create_dispatch(route_by_name["HS_SA"], t, min(cap["HS_SA"], alt_a))
        create_dispatch(route_by_name["HN_SB"], t, min(cap["HN_SB"], alt_b))

        # Record phase and node stress tracks.
        phase = phase_at(t, duration, shock_start, shock_end)
        phase_counts[phase] += 1
        tracks["phase_ty"][k] = phase_rows[phase]
        peak_total_backlog = max(peak_total_backlog, backlog["STORE_A"] + backlog["STORE_B"])

        # Stress is backlog for stores, inventory deficit for hubs/ports.
        max_backlog = 1.0 + max(backlog.values())
        for name, node in nodes.items():
            if node.tier == "store":
                stress = backlog[name] / max_backlog
            else:
                deficit = max(0.0, node.target_inventory - node.inventory)
                stress = deficit / max(1.0, node.target_inventory)
            stress = clamp(stress, 0.0, 1.0)
            tracks[f"halo_w_{name}"][k] = 0.8 + 4.0 * stress
            tracks[f"bar_sy_{name}"][k] = 0.28 + 1.35 * stress

        # Camera cues.
        if args.camera_mode == "fixed":
            cam = Point(args.world_width / 2, args.world_height / 2)
        else:
            # risk hotspot: store with larger backlog
            hot_store = "STORE_A" if backlog["STORE_A"] >= backlog["STORE_B"] else "STORE_B"
            hot = nodes[hot_store].pos
            corridor = Point(
                (nodes["PORT_W"].pos.x + nodes["HUB_N"].pos.x) / 2,
                (nodes["PORT_W"].pos.y + nodes["HUB_N"].pos.y) / 2,
            )

            if args.camera_mode == "track":
                cam = hot * 0.72 + corridor * 0.28
            else:  # hybrid
                if t < shock_start:
                    cam = nodes["HUB_N"].pos * 0.5 + nodes["HUB_S"].pos * 0.5
                elif t <= shock_end:
                    cam = hot * 0.6 + corridor * 0.4
                else:
                    center = Point(args.world_width / 2, args.world_height / 2)
                    cam = hot * 0.45 + center * 0.55

        tracks["cam_tx"][k] = cam.x
        tracks["cam_ty"][k] = cam.y

    # Build packet visuals.
    packet_anims = []
    for i, rec in enumerate(packet_records):
        pkt = Circle(
            r=4.0 + (i % 2),
            fill=rec.color.transparent(0.86),
            stroke=Colors.Black.transparent(0.22),
            width=0.7,
        ).move_to(rec.src)
        canvas.add(pkt)
        packet_anims.append(packet_keyframes(pkt, rec, duration=duration))

    anims = [
        KeyframeAnimation(phase_indicator, ty=tracks["phase_ty"]),
        KeyframeAnimation(camera, tx=tracks["cam_tx"], ty=tracks["cam_ty"]),
    ]

    for name in nodes:
        anims.append(KeyframeAnimation(node_halos[name], width=tracks[f"halo_w_{name}"]))
        anims.append(KeyframeAnimation(node_bars[name], sy=tracks[f"bar_sy_{name}"]))

    # Pulse disrupted corridors during shock.
    shock_k0 = clamp(shock_start / duration, 0.0, 1.0)
    shock_k1 = clamp(shock_end / duration, 0.0, 1.0)
    for rn in sorted(disrupted_routes):
        anims.append(
            route_shapes[rn].animate.keyframes(
                width={0.0: 1.5, shock_k0: 1.5, (shock_k0 + shock_k1) / 2: 3.8, shock_k1: 1.5, 1.0: 1.5}
            )
        )

    scene = Scene(canvas, fps=fps, background="white")
    scene.play(Parallel(*(anims + packet_anims)), duration=duration)

    result = render_scene(
        scene,
        RenderConfig(
            output_path=args.output,
            format=args.format,
            timing=TimingSpec(fps=fps, duration=duration, seed=args.seed),
        ),
    )
    out = result.output_path

    worst_backlog = max(backlog.values())
    total_demand_sum = total_demand["STORE_A"] + total_demand["STORE_B"]
    total_unmet_sum = total_unmet["STORE_A"] + total_unmet["STORE_B"]
    service_level = 1.0 if total_demand_sum <= 1e-9 else max(0.0, 1.0 - (total_unmet_sum / total_demand_sum))
    dominant_phase = max(phase_counts.items(), key=lambda kv: kv[1])[0]

    print(f"✅ Saved: {out}")
    print(
        f"   scenario={args.scenario} policy={args.policy} duration={duration:.1f}s fps={fps} dt={dt:.3f} camera_mode={args.camera_mode} "
        f"visible_packets={len(packet_records)} dispatches={dispatch_total}"
    )
    print(
        f"   shock=[{shock_start:.2f}s,{shock_end:.2f}s] severity={shock_severity:.2f} target={shock_target} "
        f"peak_store_backlog={worst_backlog:.2f} peak_total_backlog={peak_total_backlog:.2f} "
        f"service_level={service_level:.3f} dominant_phase={dominant_phase}"
    )

    if args.report_json:
        report_path = Path(args.report_json)
        report = {
            "scenario": args.scenario,
            "policy": args.policy,
            "seed": args.seed,
            "duration": duration,
            "dt": dt,
            "fps": fps,
            "camera_mode": args.camera_mode,
            "shock": {
                "start_s": shock_start,
                "end_s": shock_end,
                "severity": shock_severity,
                "target": shock_target,
                "store_spike": store_spike,
                "demand_spike": demand_spike,
            },
            "config": {
                "demand_scale": demand_scale,
                "supply_rate": supply_rate,
                "route_capacity_scale": route_capacity_scale,
                "alt_route_boost": alt_route_boost,
                "hub_balance_gain": hub_balance_gain,
                "backlog_relief_rate": backlog_relief_rate,
                "packets_max": packets_max,
                "packet_size": packet_size,
            },
            "metrics": {
                "dispatch_total": dispatch_total,
                "visible_packets": len(packet_records),
                "peak_store_backlog": worst_backlog,
                "peak_total_backlog": peak_total_backlog,
                "final_backlog_store_a": backlog["STORE_A"],
                "final_backlog_store_b": backlog["STORE_B"],
                "total_demand": total_demand_sum,
                "total_unmet": total_unmet_sum,
                "service_level": service_level,
                "dominant_phase": dominant_phase,
            },
        }
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"   report_json={report_path}")


if __name__ == "__main__":
    main()
