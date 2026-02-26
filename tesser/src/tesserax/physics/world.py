from tesserax.animation import Animation, Parallel, KeyframeAnimation
from tesserax.core import Bounds
from .core import Body
from .forces import Field
from .constraints import Constraint
from .joints import Joint
from .collisions import Collision
from .events import EventDispatcher, PhysicsEvent


class PhysicsAnimation(Parallel):
    def __init__(
        self, *animations: Animation, bounds: Bounds | None = None, **kwargs
    ) -> None:
        super().__init__(*animations, **kwargs)
        self.bounds = bounds


class World:
    def __init__(self):
        self.bodies: list[Body] = []
        self.fields: list[Field] = []
        self.constraints: list[Constraint] = []
        self.joints: list[Joint] = []
        self.events: list[PhysicsEvent] = []
        self.dispatcher = EventDispatcher()
        self._step_index = 0
        self._time = 0.0
        self._emission_order = 0
        self._active_collision_pairs: set[tuple[int, int]] = set()

    def on_event(self, handler):
        self.dispatcher.subscribe(handler)
        return handler

    def _entity(self, body: Body) -> str:
        return f"body:{body.body_id}"

    def _emit(
        self,
        event_type: str,
        *,
        entities: tuple[str, ...] = (),
        metadata: dict[str, object] | None = None,
        timestamp: float | None = None,
    ) -> None:
        event = PhysicsEvent(
            type=event_type,
            timestamp=self._time if timestamp is None else timestamp,
            step_index=self._step_index,
            entities=entities,
            metadata={} if metadata is None else metadata,
            emission_order=self._emission_order,
        )
        self._emission_order += 1
        self.events.append(event)
        self.dispatcher.emit(event)

    def add(self, shape, **kwargs) -> Body:
        b = Body(shape, **kwargs)
        self.bodies.append(b)
        return b

    def constraint(self, c: Constraint):
        self.constraints.append(c)
        return c

    def joint(self, j: Joint):
        self.joints.append(j)
        return j

    def simulate(self, duration: float, dt: float = 0.01) -> PhysicsAnimation:
        steps = int(duration / dt)

        # Tracks now include 'rotation'
        tracks = {b: {"tx": {}, "ty": {}, "rotation": {}} for b in self.bodies}

        time = 0.0
        for _ in range(steps):
            t_norm = time / duration if duration > 0 else 0

            # 1. Record
            for b in self.bodies:
                tracks[b]["tx"][t_norm] = b.pos.x
                tracks[b]["ty"][t_norm] = b.pos.y
                tracks[b]["rotation"][t_norm] = b.rotation  # Radians

            # 2. Physics Step
            self._step(dt)
            time += dt

        # 3. Bake and Compute Bounds
        anims = []
        all_bounds = []

        for b, props in tracks.items():
            anims.append(
                KeyframeAnimation(
                    b.shape,
                    tx=props["tx"],
                    ty=props["ty"],
                    rotation=props["rotation"],  # This maps to transform.rotation
                )
            )

            # Compute approximate bounds for this body over the entire simulation
            # We assume the AABB of the shape + the min/max translations
            local = b.shape.local()
            tx_values = props["tx"].values()
            ty_values = props["ty"].values()

            if tx_values and ty_values:
                min_tx, max_tx = min(tx_values), max(tx_values)
                min_ty, max_ty = min(ty_values), max(ty_values)

                # Union of the shape at its min position and max position
                # This is a safe approximation for "camera fitting" purposes
                # (width/height remain constant in local space)
                b_bounds = Bounds(
                    x=min_tx + local.x,
                    y=min_ty + local.y,
                    width=(max_tx - min_tx) + local.width,
                    height=(max_ty - min_ty) + local.height,
                )
                all_bounds.append(b_bounds)

        total_bounds = Bounds.union(*all_bounds) if all_bounds else None

        return PhysicsAnimation(*anims, bounds=total_bounds)

    def _step(self, dt: float):
        self._emit(
            "world.before_step",
            metadata={
                "dt": dt,
                "body_count": len(self.bodies),
                "constraint_count": len(self.constraints),
                "joint_count": len(self.joints),
            },
            timestamp=self._time,
        )

        # 1. Apply Fields (Gravity, Drag)
        for f in self.fields:
            f.apply(self.bodies)

        # 2. Solve Constraints (Springs apply forces)
        for c in self.constraints:
            solve_info = c.solve() or {}
            entities = tuple(self._entity(b) for b in c.bodies())
            self._emit(
                "constraint.applied",
                entities=entities,
                metadata={
                    "constraint_type": c.__class__.__name__,
                    "constraint_id": c.constraint_id,
                    "error": float(solve_info.get("error", 0.0)),
                    "impulse": float(solve_info.get("impulse", 0.0)),
                },
            )
        for j in self.joints:
            solve_info = j.solve() or {}
            active_limits = solve_info.get("active_limits") or []
            if not isinstance(active_limits, list):
                active_limits = [str(active_limits)]
            if active_limits:
                entities = tuple(self._entity(b) for b in j.bodies())
                self._emit(
                    "joint.limit_hit",
                    entities=entities,
                    metadata={
                        "joint_type": j.__class__.__name__,
                        "joint_id": j.joint_id,
                        "error": float(solve_info.get("error", 0.0)),
                        "impulse": float(solve_info.get("impulse", 0.0)),
                        "active_limits": [str(x) for x in active_limits],
                    },
                )

        # 3. Integrate (Move objects)
        for b in self.bodies:
            b.integrate(dt)

        # 4. Resolve Collisions (Impulses)
        # Naive O(N^2) - Fine for < 100 objects
        count = len(self.bodies)
        current_pairs: set[tuple[int, int]] = set()
        collision_count = 0
        for i in range(count):
            for j in range(i + 1, count):
                a = self.bodies[i]
                b = self.bodies[j]

                # Optimization: Don't check static vs static
                if a.static and b.static:
                    continue

                if col := Collision.solve(a, b):
                    pair = (
                        (a.body_id, b.body_id)
                        if a.body_id < b.body_id
                        else (b.body_id, a.body_id)
                    )
                    current_pairs.add(pair)
                    event_type = (
                        "world.collision_start"
                        if pair not in self._active_collision_pairs
                        else "world.collision_persist"
                    )
                    rel_vel = (col.b.vel - col.a.vel).magnitude()
                    self._emit(
                        event_type,
                        entities=(self._entity(col.a), self._entity(col.b)),
                        metadata={
                            "normal": {"x": col.normal.x, "y": col.normal.y},
                            "penetration": col.depth,
                            "relative_speed": rel_vel,
                            "contact_points": [
                                {"x": col.point.x, "y": col.point.y},
                            ],
                        },
                    )
                    collision_count += 1
                    col.resolve()

        ended_pairs = self._active_collision_pairs - current_pairs
        for a_id, b_id in sorted(ended_pairs):
            self._emit(
                "world.collision_end",
                entities=(f"body:{a_id}", f"body:{b_id}"),
                metadata={},
            )
        self._active_collision_pairs = current_pairs

        self._time += dt
        self._emit(
            "world.after_step",
            metadata={
                "dt": dt,
                "collision_count": collision_count,
                "active_collision_pairs": len(self._active_collision_pairs),
            },
            timestamp=self._time,
        )
        self._step_index += 1
