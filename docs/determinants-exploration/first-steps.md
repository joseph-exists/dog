 What We've Built

  I've created two foundational artifacts in docs/affordances/:

  1. demo-builder.yaml - The Affordance Registry

  14 core affordances across 4 categories:
  Category: Config
  Affordances: create_demo_config, update_demo_config, publish_demo_config
  Purpose: Demo lifecycle
  ────────────────────────────────────────
  Category: Composition
  Affordances: initialize_composition, set_layout_mode, set_runtime_policy, set_persona_policy, set_chat_mode
  Purpose: Composition configuration
  ────────────────────────────────────────
  Category: Panel
  Affordances: add_panel, configure_panel, remove_panel
  Purpose: Panel management
  ────────────────────────────────────────
  Category: Block
  Affordances: add_block, remove_block
  Purpose: Block management
  ────────────────────────────────────────
  Category: Session
  Affordances: create_session, resolve_entry
  Purpose: User session lifecycle
  Each affordance includes:
  - Dimensions it touches (with required/optional/defaults)
  - Preconditions that must be true (with dimension attribution and messages)
  - Effects describing state changes
  - Enables/precludes relationships for downstream reasoning

  Plus 3 composition patterns (minimal_demo, story_explorer, canvas_workshop) showing idiomatic affordance sequences.

  2. affordance-schema.ts - The Query Interface

  5 query operations:
  ┌───────────┬─────────────────────────────────────────┐
  │   Query   │           Question It Answers           │
  ├───────────┼─────────────────────────────────────────┤
  │ available │ "What can I do right now?"              │
  ├───────────┼─────────────────────────────────────────┤
  │ preview   │ "What would happen if I did X?"         │
  ├───────────┼─────────────────────────────────────────┤
  │ pathTo    │ "How do I get from here to there?"      │
  ├───────────┼─────────────────────────────────────────┤
  │ elaborate │ "I want to do X - what must I specify?" │
  ├───────────┼─────────────────────────────────────────┤
  │ explain   │ "Why can't I do X?"                     │
  └───────────┴─────────────────────────────────────────┘
  ★ Insight ─────────────────────────────────────
  The key addition beyond our original spec: I added elaborate and explain queries. These support progressive elaboration
  (starting from intent and filling in dimensions) and diagnostic reasoning (understanding failures and finding
  alternatives). These two queries are where I expect to spend most of my cognitive effort when building demos.
  ─────────────────────────────────────────────────

  ---
  What's Different About This From MCP/Tools
  MCP/Tools Approach: "Here's create_demo, call it"
  Affordance Registry Approach: "Here's create_demo_config, and here's what must be true first, what it changes, and what
  it
     enables"
  ────────────────────────────────────────
  MCP/Tools Approach: Errors on failure
  Affordance Registry Approach: Preview before acting, explain failures
  ────────────────────────────────────────
  MCP/Tools Approach: Blind composition
  Affordance Registry Approach: Dimensional reasoning about compatibility
  ────────────────────────────────────────
  MCP/Tools Approach: Trial and error
  Affordance Registry Approach: pathTo for goal-directed planning
  ---
  Next Steps

  To make this operational, we need:

  1. A loader that parses the YAML into the TypeScript types
  2. Constraint evaluation that executes the predicate strings against context
  3. The query endpoint that implements the 5 operations
  4. An MCP tool or direct integration so I can actually use it

  The minimal path would be:
  - Parse the YAML at startup
  - Implement available and preview first (highest value)
  - Expose via a simple endpoint or tool

  Would you like me to continue with implementation, or would you prefer to review what's here first? I'm also curious:
  reading these affordance definitions, do they capture the structure you have in mind for how demos work, or are there
  dimensions/constraints I'm missing?