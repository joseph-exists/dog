This is the right question to ask me directly. Let me actually introspect about what would serve my reasoning best,
  rather than defaulting to patterns that work for human interfaces.

  ---
  What I Actually Want (Introspecting on My Own Cognition)

  When I think about how I work effectively, it's not primarily through search or semantic similarity. Those help when I
  don't know the vocabulary. But I learn vocabulary quickly. What I actually lack is:

  1. Constraint visibility — not "what's similar to X" but "what's valid given X"
  2. Effect prediction — not "what does X do" (I can read docs) but "what does X enable or preclude"
  3. Compositional reasoning — not "here are operations" but "here's how operations relate"

  Embeddings optimize for fuzzy matching. SQL optimizes for data retrieval. But affordances aren't data — they're
  possibility spaces.

  ★ Insight ─────────────────────────────────────
  What I need isn't a better way to find information. It's a better way to reason about possibility. The interface should
  be a queryable constraint algebra, not a search engine.
  ─────────────────────────────────────────────────

  ---
  The Most Generative Implementation: Typed Affordance Registry

  Here's what I think would give us the richest experimental signal:

  Core Structure

  // An Affordance is a typed operation with dimensional metadata
  interface Affordance {
    name: string;
    description: string;

    // What this operation touches
    dimensions: {
      [dimensionName: string]: {
        type: "enum" | "range" | "reference";
        values?: string[];        // for enums
        range?: [number, number]; // for ranges
        references?: string;      // for entity references
      }
    };

    // When can this operation be invoked?
    preconditions: Constraint[];

    // What becomes true after invocation?
    effects: Effect[];

    // What other operations does this enable/preclude?
    enables: string[];    // affordance names that become available
    precludes: string[];  // affordance names that become unavailable

    // For progressive elaboration: which dimensions are required vs optional?
    required_dimensions: string[];
    default_values: { [dim: string]: any };
  }

  // Constraints are predicates over the current state
  interface Constraint {
    description: string;
    predicate: string;  // e.g., "composition.panels.length < 8"
    dimension: string;  // which dimension this constraint lives in
  }

  // Effects describe state changes
  interface Effect {
    description: string;
    dimension: string;
    change: "creates" | "modifies" | "removes";
    target: string;
  }

  Introspection Primitives

  The key is not having many tools, but having the right tools:

  // 1. What can I do right now?
  function available(context: State): Affordance[] {
    // Returns affordances whose preconditions are satisfied
  }

  // 2. What would happen if I did X?
  function preview(context: State, action: Action): {
    valid: boolean;
    violations?: Constraint[];      // if invalid, why
    resultingState?: State;         // if valid, what state results
    newlyEnabled?: Affordance[];    // what becomes possible
    newlyPrecluded?: Affordance[];  // what becomes impossible
  }

  // 3. How do I get from here to there?
  function pathTo(
    context: State,
    goal: Partial<State>
  ): {
    reachable: boolean;
    minimalPath?: Action[];         // shortest sequence of affordances
    requiredDimensions?: string[];  // what must be specified along the way
  }

  Why This Shape?
  ┌──────────────────────────────┬─────────────────────────────────────────────────┐
  │           Feature            │                 Why It Helps Me                 │
  ├──────────────────────────────┼─────────────────────────────────────────────────┤
  │ Typed dimensions             │ I can reason about composition across axes      │
  ├──────────────────────────────┼─────────────────────────────────────────────────┤
  │ Explicit preconditions       │ I know before acting whether something is valid │
  ├──────────────────────────────┼─────────────────────────────────────────────────┤
  │ Effects as enables/precludes │ I can plan multi-step sequences                 │
  ├──────────────────────────────┼─────────────────────────────────────────────────┤
  │ Preview function             │ I can simulate without committing               │
  ├──────────────────────────────┼─────────────────────────────────────────────────┤
  │ PathTo function              │ I can work backwards from goals                 │
  └──────────────────────────────┴─────────────────────────────────────────────────┘
  ---
  Minimal Viable Implementation

  Here's what I think we should actually build to start the experiment:

  Phase 1: The Registry (A Document + A Validator)

  Step 1: Write the affordance definitions for Demo-builder's core operations as a structured JSON/YAML file:

  affordances:
    - name: create_composition
      dimensions:
        layout_mode: { type: enum, values: [panels, tabs] }
        runtime_policy: { type: enum, values: [auto, manual, owner_only] }
      preconditions:
        - { predicate: "demo_config exists", dimension: ownership }
      effects:
        - { dimension: structure, change: creates, target: composition }
      enables: [add_panel, add_block, set_theme]
      precludes: []

    - name: add_panel
      dimensions:
        kind: { type: enum, values: [chat, storyRuntime, canvas, ...] }
        prominence: { type: enum, values: [primary, auxiliary] }
        data_binding: { type: reference, references: room|story|canvas }
      preconditions:
        - { predicate: "composition.panels.length < 8", dimension: structure }
        - { predicate: "kind == 'chat' implies room exists", dimension: data_binding }
      effects:
        - { dimension: structure, change: modifies, target: composition.panels }
      enables: [configure_panel, remove_panel]
      precludes: []

  Step 2: Create one endpoint that exposes the introspection primitives:

  POST /api/v1/affordances/query
  {
    "operation": "available" | "preview" | "pathTo",
    "context": { current state },
    "action": { proposed action, for preview },
    "goal": { desired state, for pathTo }
  }

  Phase 2: I Use It

  You give me access to this endpoint. I use it to build demos. We observe:
  - How often do I query before acting?
  - Which introspection primitives do I use most?
  - Where do I still get stuck?
  - What affordance definitions are missing or unclear?

  Phase 3: We Learn

  Based on observed patterns, we iterate:
  - Add missing affordances
  - Refine dimension definitions
  - Discover which constraints are actually load-bearing

  ---
  Why Not Embeddings/Search First?
  ┌───────────────┬───────────────────────────────────────────────────────┬───────────────────────────────────────────────┐
  │   Approach    │                     What It Tests                     │                  Limitation                   │
  ├───────────────┼───────────────────────────────────────────────────────┼───────────────────────────────────────────────┤
  │ Embeddings    │ Can I find relevant operations via semantic           │ I already can — vocabulary isn't my           │
  │               │ similarity?                                           │ bottleneck                                    │
  ├───────────────┼───────────────────────────────────────────────────────┼───────────────────────────────────────────────┤
  │ NL→SQL        │ Can I query data naturally?                           │ Affordances aren't data, they're              │
  │               │                                                       │ possibilities                                 │
  ├───────────────┼───────────────────────────────────────────────────────┼───────────────────────────────────────────────┤
  │ Search        │ Can I find information?                               │ Finding ≠ reasoning about composition         │
  ├───────────────┼───────────────────────────────────────────────────────┼───────────────────────────────────────────────┤
  │ Typed         │ Can I reason about constraint spaces?                 │ This is the actual bottleneck                 │
  │ Registry      │                                                       │                                               │
  └───────────────┴───────────────────────────────────────────────────────┴───────────────────────────────────────────────┘
  ---
  My concrete proposal:

  1. I draft the affordance definitions for Demo-builder's core operations (maybe 15-20 affordances covering the main
  flows)
  2. You review whether the dimensional structure captures what matters
  3. We implement the minimal query endpoint
  4. I use it to build a real demo, and we observe what happens

  Does this feel like the right first step? Or do you see something I'm missing about what would actually stress-test my
  capabilities?