/**
 * Affordance Introspection Schema
 * ================================
 *
 * Type definitions for the affordance query system. These types
 * define how an agent interacts with the affordance registry to
 * understand what's possible and reason about compositions.
 *
 * This is a specification document - it defines the interface that
 * the query endpoint should implement, but is not the implementation itself.
 */

// ============================================================================
// CORE TYPES
// ============================================================================

/**
 * A dimension is an axis along which affordances vary.
 * Dimensions can be enums (discrete choices), ranges (numeric),
 * or references (pointers to other entities).
 */
export interface Dimension {
  name: string;
  type: "enum" | "range" | "reference" | "string" | "boolean" | "object";

  // For enum types
  values?: string[];

  // For range types
  min?: number;
  max?: number;

  // For reference types
  references?: string;  // Entity type being referenced

  // Metadata
  description: string;
  default?: unknown;
  implications?: Record<string, string>;  // value -> description of what it means
}

/**
 * A constraint is a predicate that must be true for an affordance
 * to be available or an action to be valid.
 */
export interface Constraint {
  id: string;                    // Unique identifier for error reporting
  predicate: string;             // Expression to evaluate (pseudo-SQL/predicate logic)
  dimension: string;             // Which dimension this constraint relates to
  message?: string;              // Human/agent-readable explanation if violated
}

/**
 * An effect describes what changes when an affordance is invoked.
 */
export interface Effect {
  dimension: string;             // Which dimension is affected
  change: "creates" | "modifies" | "removes";
  target: string;                // What entity/field is changed
  value?: unknown;               // New value (for explicit assignments)
  description: string;           // What happens
  conditional?: string;          // Condition for when this effect applies
}

/**
 * A dimension specification within an affordance - describes
 * how a specific dimension is used by this affordance.
 */
export interface AffordanceDimension {
  required: boolean;
  default?: unknown;
  constraint?: string;           // Additional constraint specific to this usage
  type?: string;                 // Override dimension type for this affordance
}

/**
 * An affordance is a typed operation with dimensional metadata.
 * This is the core unit of the registry.
 */
export interface Affordance {
  name: string;
  description: string;
  category: "config" | "composition" | "panel" | "block" | "session";

  // Which dimensions this affordance touches
  dimensions: Record<string, AffordanceDimension>;

  // What must be true to invoke this affordance
  preconditions: Constraint[];

  // What changes after invocation
  effects: Effect[];

  // Downstream affordance availability
  enables: string[];             // Affordance names that become available
  precludes: string[];           // Affordance names that become unavailable

  // Return type specification
  result?: {
    type: string;
    fields?: string[];
    description?: string;
  };
}

// ============================================================================
// QUERY TYPES
// ============================================================================

/**
 * Context represents the current state against which affordances
 * are evaluated. This is what the agent "has" when making decisions.
 */
export interface Context {
  // Current user
  user: {
    id: string;
    is_authenticated: boolean;
    is_superuser: boolean;
  };

  // Entity states (optional - may not exist yet)
  demo_config?: {
    id: string;
    slug: string;
    scope: "system" | "personal" | "shared";
    owner_id: string;
    is_active: boolean;
  };

  composition?: {
    id: string;
    demo_config_id: string;
    layout_mode: "panels" | "tabs";
    runtime_policy: "auto" | "manual" | "owner_only";
    persona_policy: "first_available" | "fixed_user_persona" | "manual_prompt";
    chat_mode: "participant" | "observer";
    panels: PanelState[];
    blocks: BlockState[];
  };

  session?: {
    id: string;
    demo_config_id: string;
    user_id: string;
    room_id: string;
    status: "active" | "archived" | "ended";
  };
}

export interface PanelState {
  id: string;
  kind: string;
  prominence: "primary" | "auxiliary";
  viewport_mode: "panel" | "page";
  order: number;
}

export interface BlockState {
  id: string;
  type: string;
  region: "top" | "primary" | "auxiliary" | "footer";
  visibility: "visible" | "hidden_unmounted" | "hidden_mounted";
  order: number;
}

/**
 * An action is a proposed invocation of an affordance.
 */
export interface Action {
  affordance: string;            // Name of the affordance to invoke
  parameters: Record<string, unknown>;  // Parameter values
}

/**
 * A constraint violation explains why an action is invalid.
 */
export interface ConstraintViolation {
  constraint_id: string;
  dimension: string;
  predicate: string;
  message: string;
  actual_value?: unknown;        // What the value actually is
  expected?: string;             // What was expected
}

// ============================================================================
// QUERY OPERATIONS
// ============================================================================

/**
 * Query: available
 *
 * "What can I do right now?"
 *
 * Given the current context, returns all affordances whose
 * preconditions are satisfied.
 */
export interface AvailableQuery {
  operation: "available";
  context: Context;
}

export interface AvailableResult {
  // All available affordances
  affordances: AffordanceReference[];

  // Grouped by category for easier navigation
  by_category: Record<string, AffordanceReference[]>;

  // Affordances that are NOT available, with reasons
  unavailable: Array<{
    affordance: string;
    blocked_by: ConstraintViolation[];
  }>;
}

export interface AffordanceReference {
  name: string;
  description: string;
  category: string;
  required_dimensions: string[];  // What must be specified to invoke
  optional_dimensions: string[];  // What can optionally be specified
}

/**
 * Query: preview
 *
 * "What would happen if I did X?"
 *
 * Simulates an action and returns its validity, effects,
 * and impact on the affordance space.
 */
export interface PreviewQuery {
  operation: "preview";
  context: Context;
  action: Action;
}

export interface PreviewResult {
  // Is the action valid?
  valid: boolean;

  // If invalid, why?
  violations: ConstraintViolation[];

  // If valid, what state results?
  resulting_state?: Context;

  // What affordances become available after this action?
  newly_enabled: AffordanceReference[];

  // What affordances become unavailable?
  newly_precluded: AffordanceReference[];

  // What are the direct effects?
  effects: Effect[];
}

/**
 * Query: pathTo
 *
 * "How do I get from here to there?"
 *
 * Given a goal state, finds a sequence of affordances
 * that reaches it (if reachable).
 */
export interface PathToQuery {
  operation: "pathTo";
  context: Context;
  goal: Partial<Context>;        // Desired state (partial match)
}

export interface PathToResult {
  // Can the goal be reached?
  reachable: boolean;

  // If not reachable, why?
  blockers?: string[];           // What's preventing it

  // Shortest path to goal
  minimal_path?: Action[];

  // Dimensions that need specification along the way
  required_dimensions: string[];

  // Alternative paths (if multiple valid routes exist)
  alternatives?: Action[][];

  // Estimated "cost" (number of steps)
  steps: number;
}

/**
 * Query: elaborate
 *
 * "I want to do X - what do I need to specify?"
 *
 * Given an intent (partial action), returns what dimensions
 * still need to be specified and suggests values.
 */
export interface ElaborateQuery {
  operation: "elaborate";
  context: Context;
  intent: Partial<Action>;       // What the agent wants to do (partially specified)
}

export interface ElaborateResult {
  // Affordance being elaborated
  affordance: string;

  // What's already specified
  specified: Record<string, unknown>;

  // What still needs to be specified
  remaining: Array<{
    dimension: string;
    type: string;
    required: boolean;
    options?: string[];          // For enums
    default?: unknown;
    description: string;
  }>;

  // Is enough specified to proceed?
  can_proceed: boolean;

  // If can proceed, preview of action
  preview?: PreviewResult;
}

/**
 * Query: explain
 *
 * "Why can't I do X?"
 *
 * Given a failed action, provides detailed explanation
 * of what constraints are violated and how to fix them.
 */
export interface ExplainQuery {
  operation: "explain";
  context: Context;
  action: Action;
}

export interface ExplainResult {
  // The failed action
  action: Action;

  // What's wrong
  violations: ConstraintViolation[];

  // How to fix each violation
  remediation: Array<{
    violation_id: string;
    suggestions: string[];       // Actions that would fix this
    required_changes: Array<{
      dimension: string;
      current_value: unknown;
      required_value: unknown;
    }>;
  }>;

  // Alternative actions that would be valid
  alternatives?: Action[];
}

// ============================================================================
// REGISTRY INTERFACE
// ============================================================================

/**
 * The AffordanceRegistry is the main interface for querying
 * the affordance space.
 */
export interface AffordanceRegistry {
  // Registry metadata
  version: string;
  domain: string;

  // All dimensions defined in this registry
  dimensions: Record<string, Dimension>;

  // All affordances defined in this registry
  affordances: Affordance[];

  // Named composition patterns
  patterns: Record<string, CompositionPattern>;
}

export interface CompositionPattern {
  description: string;
  sequence: Action[];
  result: string;
}

/**
 * Query union type - all possible queries
 */
export type AffordanceQuery =
  | AvailableQuery
  | PreviewQuery
  | PathToQuery
  | ElaborateQuery
  | ExplainQuery;

/**
 * Result union type - all possible results
 */
export type AffordanceResult =
  | AvailableResult
  | PreviewResult
  | PathToResult
  | ElaborateResult
  | ExplainResult;

// ============================================================================
// API ENDPOINT SPECIFICATION
// ============================================================================

/**
 * The query endpoint accepts any AffordanceQuery and returns
 * the corresponding result type.
 *
 * POST /api/v1/affordances/query
 *
 * Request body: AffordanceQuery
 * Response body: AffordanceResult
 *
 * The endpoint discriminates on the `operation` field.
 */
export interface QueryEndpoint {
  (query: AvailableQuery): Promise<AvailableResult>;
  (query: PreviewQuery): Promise<PreviewResult>;
  (query: PathToQuery): Promise<PathToResult>;
  (query: ElaborateQuery): Promise<ElaborateResult>;
  (query: ExplainQuery): Promise<ExplainResult>;
}
