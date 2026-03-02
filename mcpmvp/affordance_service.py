"""
Affordance Registry Service
===========================

This service provides introspection over the affordance space for Demo-builder
(and potentially other domains). It enables agents to query what's possible,
preview actions, and reason about compositional constraints.

Key concepts:
- Affordance: A typed operation with dimensional metadata
- Context: The current state against which affordances are evaluated
- Query: An introspection operation (available, preview, elaborate, explain)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# PYDANTIC MODELS - Match the TypeScript schema
# ============================================================================


class Dimension(BaseModel):
    """A dimension is an axis along which affordances vary."""

    name: str = ""
    type: str  # enum, range, reference, string, boolean, object
    values: list[str] | None = None
    min: int | None = None
    max: int | None = None
    references: str | None = None
    description: str = ""
    default: Any = None
    constraint: str | None = None
    implications: dict[str, str] | None = None


class Constraint(BaseModel):
    """A constraint that must be true for an affordance to be available."""

    id: str
    predicate: str
    dimension: str
    message: str | None = None


class Effect(BaseModel):
    """Describes what changes when an affordance is invoked."""

    dimension: str
    change: str  # creates, modifies, removes
    target: str
    value: Any = None
    description: str = ""
    conditional: str | None = None


class AffordanceDimension(BaseModel):
    """How a specific dimension is used by an affordance."""

    required: bool = False
    default: Any = None
    constraint: str | None = None
    type: str | None = None


class AffordanceResult(BaseModel):
    """Return type specification for an affordance."""

    type: str
    fields: list[str] | None = None
    description: str | None = None


class Affordance(BaseModel):
    """A typed operation with dimensional metadata."""

    name: str
    description: str
    category: str

    dimensions: dict[str, AffordanceDimension | dict[str, Any]] = Field(default_factory=dict)
    preconditions: list[Constraint] = Field(default_factory=list)
    effects: list[Effect] = Field(default_factory=list)
    enables: list[str] = Field(default_factory=list)
    precludes: list[str] = Field(default_factory=list)
    result: AffordanceResult | None = None


class CompositionPattern(BaseModel):
    """A named sequence of affordances accomplishing a high-level goal."""

    description: str
    sequence: list[dict[str, Any]]
    result: str


class AffordanceRegistry(BaseModel):
    """The complete affordance registry for a domain."""

    version: str
    domain: str
    dimensions: dict[str, Dimension] = Field(default_factory=dict)
    affordances: list[Affordance] = Field(default_factory=list)
    patterns: dict[str, CompositionPattern] = Field(default_factory=dict)


# ============================================================================
# CONTEXT MODELS
# ============================================================================


class UserContext(BaseModel):
    """Current user state."""

    id: str
    is_authenticated: bool = True
    is_superuser: bool = False


class DemoConfigContext(BaseModel):
    """Demo config state for affordance evaluation."""

    id: str
    slug: str
    scope: str  # system, personal, shared
    owner_id: str
    is_active: bool = False


class PanelContext(BaseModel):
    """Panel state within a composition."""

    id: str
    kind: str
    prominence: str = "auxiliary"
    viewport_mode: str = "panel"
    order: int = 0


class BlockContext(BaseModel):
    """Block state within a composition."""

    id: str
    type: str
    region: str = "primary"
    visibility: str = "visible"
    order: int = 0


class CompositionContext(BaseModel):
    """Composition state for affordance evaluation."""

    id: str
    demo_config_id: str
    layout_mode: str = "panels"
    runtime_policy: str = "auto"
    persona_policy: str = "first_available"
    chat_mode: str = "participant"
    panels: list[PanelContext] = Field(default_factory=list)
    blocks: list[BlockContext] = Field(default_factory=list)


class SessionContext(BaseModel):
    """Session state for affordance evaluation."""

    id: str
    demo_config_id: str
    user_id: str
    room_id: str
    status: str = "active"


class Context(BaseModel):
    """Complete context for affordance evaluation."""

    user: UserContext
    demo_config: DemoConfigContext | None = None
    composition: CompositionContext | None = None
    session: SessionContext | None = None

    # For constraint evaluation - arbitrary additional context
    extra: dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# QUERY & RESULT MODELS
# ============================================================================


class Action(BaseModel):
    """A proposed invocation of an affordance."""

    affordance: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class ConstraintViolation(BaseModel):
    """Explains why a constraint was violated."""

    constraint_id: str
    dimension: str
    predicate: str
    message: str
    actual_value: Any = None
    expected: str | None = None


class AffordanceReference(BaseModel):
    """Lightweight reference to an affordance."""

    name: str
    description: str
    category: str
    required_dimensions: list[str] = Field(default_factory=list)
    optional_dimensions: list[str] = Field(default_factory=list)


# --- Query Types ---


class AvailableQuery(BaseModel):
    """Query: What can I do right now?"""

    operation: str = "available"
    context: Context


class AvailableResult(BaseModel):
    """Result of available query."""

    affordances: list[AffordanceReference]
    by_category: dict[str, list[AffordanceReference]]
    unavailable: list[dict[str, Any]] = Field(default_factory=list)


class PreviewQuery(BaseModel):
    """Query: What would happen if I did X?"""

    operation: str = "preview"
    context: Context
    action: Action


class PreviewResult(BaseModel):
    """Result of preview query."""

    valid: bool
    violations: list[ConstraintViolation] = Field(default_factory=list)
    resulting_state: Context | None = None
    newly_enabled: list[AffordanceReference] = Field(default_factory=list)
    newly_precluded: list[AffordanceReference] = Field(default_factory=list)
    effects: list[Effect] = Field(default_factory=list)


class ElaborateQuery(BaseModel):
    """Query: I want to do X - what must I specify?"""

    operation: str = "elaborate"
    context: Context
    intent: dict[str, Any]  # Partial action specification


class RemainingDimension(BaseModel):
    """A dimension that still needs specification."""

    dimension: str
    type: str
    required: bool
    options: list[str] | None = None
    default: Any = None
    description: str = ""


class ElaborateResult(BaseModel):
    """Result of elaborate query."""

    affordance: str
    specified: dict[str, Any]
    remaining: list[RemainingDimension]
    can_proceed: bool
    preview: PreviewResult | None = None


class ExplainQuery(BaseModel):
    """Query: Why can't I do X?"""

    operation: str = "explain"
    context: Context
    action: Action


class Remediation(BaseModel):
    """How to fix a constraint violation."""

    violation_id: str
    suggestions: list[str] = Field(default_factory=list)
    required_changes: list[dict[str, Any]] = Field(default_factory=list)


class ExplainResult(BaseModel):
    """Result of explain query."""

    action: Action
    violations: list[ConstraintViolation]
    remediation: list[Remediation] = Field(default_factory=list)
    alternatives: list[Action] = Field(default_factory=list)


class PathToQuery(BaseModel):
    """Query: How do I get from here to there?"""

    operation: str = "pathTo"
    context: Context
    goal: dict[str, Any]


class PathToResult(BaseModel):
    """Result of pathTo query."""

    reachable: bool
    blockers: list[str] | None = None
    minimal_path: list[Action] | None = None
    required_dimensions: list[str] = Field(default_factory=list)
    alternatives: list[list[Action]] | None = None
    steps: int = 0


# ============================================================================
# CONSTRAINT EVALUATOR
# ============================================================================


@dataclass
class ConstraintEvaluator:
    """
    Evaluates constraint predicates against a context.

    This is a simple evaluator that handles common predicate patterns.
    It's not a full expression parser, but handles the patterns used
    in our affordance definitions.
    """

    context: Context

    def evaluate(self, constraint: Constraint) -> tuple[bool, str | None]:
        """
        Evaluate a constraint predicate.

        Returns (satisfied, error_message).
        """
        predicate = constraint.predicate.strip()

        try:
            result = self._eval_predicate(predicate)
            if result:
                return True, None
            return False, constraint.message or f"Constraint '{constraint.id}' not satisfied"
        except Exception as e:
            logger.warning(f"Error evaluating constraint '{constraint.id}': {e}")
            # Be permissive on evaluation errors - assume satisfied
            return True, None

    def _eval_predicate(self, predicate: str) -> bool:
        """Evaluate a predicate string."""

        # Handle boolean literals
        if predicate.lower() == "true":
            return True
        if predicate.lower() == "false":
            return False

        # Handle simple property checks: "user.is_authenticated"
        if re.match(r"^[\w.]+$", predicate):
            return bool(self._get_value(predicate))

        # Handle negation: "NOT exists(...)"
        if predicate.startswith("NOT "):
            return not self._eval_predicate(predicate[4:])

        # Handle exists(): "exists(demo_config WHERE id = :config_id)"
        if predicate.startswith("exists("):
            return self._eval_exists(predicate)

        # Handle comparisons BEFORE equality (>=, <= contain = which would match equality regex)
        # Pattern: "composition.panels.length < 8", "node_count >= 2"
        comp_match = re.match(r"(.+?)\s*(<|>|<=|>=)\s*(\d+)", predicate)
        if comp_match:
            left = self._resolve_value(comp_match.group(1).strip())
            op = comp_match.group(2)
            right = int(comp_match.group(3))

            if left is None:
                left = 0

            if op == "<":
                return left < right
            if op == ">":
                return left > right
            if op == "<=":
                return left <= right
            if op == ">=":
                return left >= right

        # Handle equality: "scope != 'system'"
        eq_match = re.match(r"(.+?)\s*(=|!=|==)\s*(.+)", predicate)
        if eq_match:
            left = self._resolve_value(eq_match.group(1).strip())
            op = eq_match.group(2)
            right = self._resolve_value(eq_match.group(3).strip())

            if op in ("=", "=="):
                return left == right
            if op == "!=":
                return left != right

        # Handle OR: "scope != 'system' OR user.is_superuser"
        if " OR " in predicate:
            parts = predicate.split(" OR ")
            return any(self._eval_predicate(p.strip()) for p in parts)

        # Handle AND: "condition1 AND condition2"
        if " AND " in predicate:
            parts = predicate.split(" AND ")
            return all(self._eval_predicate(p.strip()) for p in parts)

        # Handle implies: "kind == 'chat' implies room exists"
        if " implies " in predicate.lower():
            parts = re.split(r"\s+implies\s+", predicate, flags=re.IGNORECASE)
            if len(parts) == 2:
                antecedent = self._eval_predicate(parts[0].strip())
                if not antecedent:
                    return True  # Implication vacuously true
                return self._eval_predicate(parts[1].strip())

        # Handle IS NOT NULL
        if " IS NOT NULL" in predicate:
            prop = predicate.replace(" IS NOT NULL", "").strip()
            return self._get_value(prop) is not None

        # Default: assume satisfied (permissive)
        logger.debug(f"Unhandled predicate pattern: {predicate}")
        return True

    def _eval_exists(self, predicate: str) -> bool:
        """Evaluate exists() predicates."""
        # Extract: exists(entity WHERE condition)
        match = re.match(r"exists\((\w+)(?:\s+WHERE\s+(.+))?\)", predicate)
        if not match:
            return False

        entity = match.group(1)
        # condition = match.group(2)  # Not used yet, but available for future

        # Check if entity exists in context
        if entity == "demo_config":
            return self.context.demo_config is not None
        if entity == "composition":
            return self.context.composition is not None
        if entity == "session":
            return self.context.session is not None
        if entity == "panel":
            return (
                self.context.composition is not None
                and len(self.context.composition.panels) > 0
            )
        if entity == "block":
            return (
                self.context.composition is not None
                and len(self.context.composition.blocks) > 0
            )

        return False

    def _get_value(self, path: str) -> Any:
        """Get a value from context by dotted path.

        For simple names (no dots), also checks context.extra for parameters.
        """
        parts = path.split(".")

        # For simple names, check extra (parameters) first
        if len(parts) == 1 and self.context.extra.get(parts[0]) is not None:
            return self.context.extra[parts[0]]

        obj: Any = self.context

        for part in parts:
            if obj is None:
                return None

            # Handle array length
            if part == "length" and isinstance(obj, list):
                return len(obj)

            # Handle Pydantic model attributes
            if hasattr(obj, part):
                obj = getattr(obj, part)
            elif isinstance(obj, dict):
                obj = obj.get(part)
            else:
                # Fall back to checking extra for this part
                if hasattr(self.context, 'extra') and part in self.context.extra:
                    obj = self.context.extra[part]
                else:
                    return None

        return obj

    def _resolve_value(self, expr: str) -> Any:
        """Resolve an expression to a value."""
        expr = expr.strip()

        # String literal
        if (expr.startswith("'") and expr.endswith("'")) or (
            expr.startswith('"') and expr.endswith('"')
        ):
            return expr[1:-1]

        # Numeric literal
        if expr.isdigit():
            return int(expr)

        # Boolean literal
        if expr.lower() == "true":
            return True
        if expr.lower() == "false":
            return False

        # Parameter reference (:param)
        if expr.startswith(":"):
            return self.context.extra.get(expr[1:])

        # Property path
        return self._get_value(expr)


# ============================================================================
# AFFORDANCE SERVICE
# ============================================================================


@dataclass
class AffordanceService:
    """
    Service for querying the affordance registry.

    This is the main interface for agents to introspect what's possible.
    """

    registry: AffordanceRegistry
    _affordance_map: dict[str, Affordance] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Build lookup maps."""
        self._affordance_map = {a.name: a for a in self.registry.affordances}

    # --- Query Operations ---

    def available(self, context: Context) -> AvailableResult:
        """Query: What affordances are available given the current context?"""
        available_list: list[AffordanceReference] = []
        unavailable_list: list[dict[str, Any]] = []

        for affordance in self.registry.affordances:
            violations = self._check_preconditions(affordance, context)
            ref = self._to_reference(affordance)

            if not violations:
                available_list.append(ref)
            else:
                unavailable_list.append(
                    {
                        "affordance": affordance.name,
                        "blocked_by": [v.model_dump() for v in violations],
                    }
                )

        # Group by category
        by_category: dict[str, list[AffordanceReference]] = {}
        for ref in available_list:
            by_category.setdefault(ref.category, []).append(ref)

        return AvailableResult(
            affordances=available_list,
            by_category=by_category,
            unavailable=unavailable_list,
        )

    def preview(self, context: Context, action: Action) -> PreviewResult:
        """Query: What would happen if this action were taken?"""
        affordance = self._affordance_map.get(action.affordance)
        if not affordance:
            return PreviewResult(
                valid=False,
                violations=[
                    ConstraintViolation(
                        constraint_id="affordance_exists",
                        dimension="structure",
                        predicate=f"exists({action.affordance})",
                        message=f"Unknown affordance: {action.affordance}",
                    )
                ],
            )

        # Check preconditions
        violations = self._check_preconditions(affordance, context, action.parameters)
        if violations:
            return PreviewResult(valid=False, violations=violations)

        # Simulate resulting state
        resulting_state = self._simulate_effects(affordance, context, action.parameters)

        # Determine newly enabled/precluded affordances
        current_available = {a.name for a in self.available(context).affordances}
        new_available = {a.name for a in self.available(resulting_state).affordances}

        newly_enabled = [
            self._to_reference(self._affordance_map[name])
            for name in new_available - current_available
            if name in self._affordance_map
        ]
        newly_precluded = [
            self._to_reference(self._affordance_map[name])
            for name in current_available - new_available
            if name in self._affordance_map
        ]

        return PreviewResult(
            valid=True,
            resulting_state=resulting_state,
            newly_enabled=newly_enabled,
            newly_precluded=newly_precluded,
            effects=affordance.effects,
        )

    def elaborate(
        self, context: Context, intent: dict[str, Any]
    ) -> ElaborateResult:
        """Query: What dimensions still need specification for this intent?"""
        affordance_name = intent.get("affordance", "")
        affordance = self._affordance_map.get(affordance_name)

        if not affordance:
            return ElaborateResult(
                affordance=affordance_name,
                specified={},
                remaining=[],
                can_proceed=False,
            )

        parameters = intent.get("parameters", {})
        specified = dict(parameters)
        remaining: list[RemainingDimension] = []

        for dim_name, dim_spec in affordance.dimensions.items():
            # Normalize dimension spec
            if isinstance(dim_spec, dict):
                required = dim_spec.get("required", False)
                default = dim_spec.get("default")
                dim_type = dim_spec.get("type", "string")
            else:
                required = dim_spec.required
                default = dim_spec.default
                dim_type = dim_spec.type or "string"

            if dim_name not in parameters:
                # Get dimension definition from registry
                registry_dim = self.registry.dimensions.get(dim_name)
                options = None
                description = ""

                if registry_dim:
                    options = registry_dim.values
                    description = registry_dim.description

                remaining.append(
                    RemainingDimension(
                        dimension=dim_name,
                        type=dim_type,
                        required=required,
                        options=options,
                        default=default,
                        description=description,
                    )
                )

        # Can proceed if no required dimensions are missing
        can_proceed = all(not r.required for r in remaining)

        # If can proceed, include preview
        preview = None
        if can_proceed:
            action = Action(affordance=affordance_name, parameters=parameters)
            preview = self.preview(context, action)

        return ElaborateResult(
            affordance=affordance_name,
            specified=specified,
            remaining=remaining,
            can_proceed=can_proceed,
            preview=preview,
        )

    def explain(self, context: Context, action: Action) -> ExplainResult:
        """Query: Why did this action fail, and how can it be fixed?"""
        preview_result = self.preview(context, action)

        if preview_result.valid:
            return ExplainResult(
                action=action,
                violations=[],
                remediation=[],
            )

        # Generate remediation suggestions
        remediation: list[Remediation] = []
        for violation in preview_result.violations:
            suggestions: list[str] = []
            required_changes: list[dict[str, Any]] = []

            # Generate context-specific suggestions
            if "authenticated" in violation.constraint_id:
                suggestions.append("Ensure user is logged in")
            elif "superuser" in violation.constraint_id:
                suggestions.append("This action requires superuser privileges")
            elif "exists" in violation.predicate:
                # Extract entity from exists predicate
                match = re.search(r"exists\((\w+)", violation.predicate)
                if match:
                    entity = match.group(1)
                    suggestions.append(f"Create {entity} first")
            elif "permission" in violation.constraint_id:
                suggestions.append("Verify ownership or request access")

            remediation.append(
                Remediation(
                    violation_id=violation.constraint_id,
                    suggestions=suggestions,
                    required_changes=required_changes,
                )
            )

        return ExplainResult(
            action=action,
            violations=preview_result.violations,
            remediation=remediation,
        )

    def path_to(self, context: Context, goal: dict[str, Any]) -> PathToResult:
        """
        Query: What sequence of affordances reaches the goal state?

        This is a simplified implementation that handles common patterns.
        A full implementation would use BFS/A* search over the affordance space.
        """
        # For now, use pattern matching for common goals
        target_entity = goal.get("entity")
        target_state = goal.get("state", {})

        if target_entity == "published_demo":
            # Common path: create → initialize → add_panel → publish
            return PathToResult(
                reachable=True,
                minimal_path=[
                    Action(
                        affordance="create_demo_config",
                        parameters={"scope": "personal", "title": "New Demo", "slug": "new-demo"},
                    ),
                    Action(affordance="initialize_composition", parameters={}),
                    Action(
                        affordance="add_panel",
                        parameters={"panel_kind": "chat", "panel_prominence": "primary"},
                    ),
                    Action(affordance="publish_demo_config", parameters={}),
                ],
                required_dimensions=["scope", "title", "slug", "panel_kind"],
                steps=4,
            )

        # Default: not reachable (would need full search implementation)
        return PathToResult(
            reachable=False,
            blockers=["Path search not implemented for this goal pattern"],
            steps=0,
        )

    # --- Helper Methods ---

    def _check_preconditions(
        self,
        affordance: Affordance,
        context: Context,
        parameters: dict[str, Any] | None = None,
    ) -> list[ConstraintViolation]:
        """Check all preconditions for an affordance."""
        # Merge parameters into context.extra for constraint evaluation
        eval_context = context.model_copy()
        if parameters:
            eval_context.extra = {**context.extra, **parameters}

        evaluator = ConstraintEvaluator(eval_context)
        violations: list[ConstraintViolation] = []

        for constraint in affordance.preconditions:
            satisfied, message = evaluator.evaluate(constraint)
            if not satisfied:
                violations.append(
                    ConstraintViolation(
                        constraint_id=constraint.id,
                        dimension=constraint.dimension,
                        predicate=constraint.predicate,
                        message=message or f"Constraint {constraint.id} not satisfied",
                    )
                )

        return violations

    def _simulate_effects(
        self,
        affordance: Affordance,
        context: Context,
        parameters: dict[str, Any],
    ) -> Context:
        """
        Simulate the effects of an affordance on the context.

        This is a simplified simulation - a full implementation would
        apply each effect to transform the context.
        """
        # For now, return a shallow copy with basic transformations
        new_context = context.model_copy(deep=True)

        for effect in affordance.effects:
            target = effect.target

            # Handle common effect patterns
            if effect.change == "creates" and "demo_config" in target:
                new_context.demo_config = DemoConfigContext(
                    id="simulated-id",
                    slug=parameters.get("slug", "simulated"),
                    scope=parameters.get("scope", "personal"),
                    owner_id=context.user.id,
                    is_active=False,
                )

            elif effect.change == "creates" and "composition" in target:
                if new_context.demo_config:
                    new_context.composition = CompositionContext(
                        id="simulated-composition-id",
                        demo_config_id=new_context.demo_config.id,
                        layout_mode=parameters.get("layout_mode", "panels"),
                    )

            elif effect.change == "modifies" and "composition.panels" in target:
                if new_context.composition:
                    new_panel = PanelContext(
                        id=f"panel-{len(new_context.composition.panels) + 1}",
                        kind=parameters.get("panel_kind", "content"),
                        prominence=parameters.get("panel_prominence", "auxiliary"),
                        viewport_mode=parameters.get("panel_viewport", "panel"),
                        order=len(new_context.composition.panels),
                    )
                    new_context.composition.panels.append(new_panel)

            elif effect.change == "modifies" and "is_active" in target:
                if new_context.demo_config:
                    new_context.demo_config.is_active = effect.value or True

        return new_context

    def _to_reference(self, affordance: Affordance) -> AffordanceReference:
        """Convert an affordance to a lightweight reference."""
        required = []
        optional = []

        for dim_name, dim_spec in affordance.dimensions.items():
            if isinstance(dim_spec, dict):
                is_required = dim_spec.get("required", False)
            else:
                is_required = dim_spec.required

            if is_required:
                required.append(dim_name)
            else:
                optional.append(dim_name)

        return AffordanceReference(
            name=affordance.name,
            description=affordance.description,
            category=affordance.category,
            required_dimensions=required,
            optional_dimensions=optional,
        )


# ============================================================================
# REGISTRY LOADER
# ============================================================================


def load_registry_from_yaml(path: Path) -> AffordanceRegistry:
    """Load an affordance registry from a YAML file."""
    with open(path) as f:
        data = yaml.safe_load(f)

    # Parse dimensions - they come as dict with name as key
    dimensions: dict[str, Dimension] = {}
    for name, dim_data in data.get("dimensions", {}).items():
        dim_data["name"] = name
        dimensions[name] = Dimension(**dim_data)

    # Parse affordances
    affordances: list[Affordance] = []
    for aff_data in data.get("affordances", []):
        # Parse preconditions
        preconditions = [Constraint(**c) for c in aff_data.get("preconditions", [])]

        # Parse effects
        effects = [Effect(**e) for e in aff_data.get("effects", [])]

        # Parse result
        result = None
        if "result" in aff_data:
            result = AffordanceResult(**aff_data["result"])

        # Parse dimension specs
        dim_specs: dict[str, AffordanceDimension | dict[str, Any]] = {}
        for dim_name, dim_data in aff_data.get("dimensions", {}).items():
            if isinstance(dim_data, dict):
                dim_specs[dim_name] = dim_data
            else:
                dim_specs[dim_name] = {"default": dim_data}

        affordances.append(
            Affordance(
                name=aff_data["name"],
                description=aff_data["description"],
                category=aff_data["category"],
                dimensions=dim_specs,
                preconditions=preconditions,
                effects=effects,
                enables=aff_data.get("enables", []),
                precludes=aff_data.get("precludes", []),
                result=result,
            )
        )

    # Parse patterns
    patterns: dict[str, CompositionPattern] = {}
    for name, pattern_data in data.get("patterns", {}).items():
        patterns[name] = CompositionPattern(**pattern_data)

    return AffordanceRegistry(
        version=data.get("version", "0.0.0"),
        domain=data.get("domain", "unknown"),
        dimensions=dimensions,
        affordances=affordances,
        patterns=patterns,
    )


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_service_instance: AffordanceService | None = None


def get_affordance_service(registry_path: Path | None = None) -> AffordanceService:
    """
    Get or create the affordance service singleton.

    If registry_path is provided, (re)loads from that path.
    Otherwise uses the default demo-builder registry.
    """
    global _service_instance

    if _service_instance is None or registry_path is not None:
        if registry_path is None:
            # Default to demo-builder registry
            registry_path = Path(__file__).parent / "demo-builder.yaml"

        if not registry_path.exists():
            raise FileNotFoundError(f"Affordance registry not found: {registry_path}")

        registry = load_registry_from_yaml(registry_path)
        _service_instance = AffordanceService(registry=registry)
        logger.info(f"Loaded affordance registry: {registry.domain} v{registry.version}")

    return _service_instance
