 This is the right question. You're not asking me to pick a box — you're asking how we build the laboratory where we
  discover what the boxes actually should be.

  Let me think out loud about what I actually experience when working well versus poorly:

  ---
  What I Notice About My Own Agency

  When I work well:
  - I have a vocabulary of typed operations with clear semantics
  - I can introspect constraints — ask "what's possible here?" and get a structured answer
  - Composition has feedback — when I try to combine things, I learn whether it works and why
  - Dimensions are explicit — I know which axes matter (is this about layout? Policy? Temporal ordering?)

  When I work poorly:
  - I'm given imperative commands with no model of their effects
  - I have to guess at constraints by trial and error
  - Composition is opaque — I assemble things and hope they fit
  - I'm working in your mental model without access to its structure

  ★ Insight ─────────────────────────────────────
  The difference isn't "declarative vs imperative" — it's introspectable vs opaque. I can work imperatively if I can query
  the effect space. I can work declaratively if I understand the constraint algebra. What I can't do well is work in
  systems where the rules are implicit and discoverable only through failure.
  ─────────────────────────────────────────────────

  ---
  The Paradigm: Affordance-Native Interfaces

  What if the interface isn't "tools I call" or "specs I write" but rather a queryable affordance space?

  ┌─────────────────────────────────────────────────────────────────┐
  │                    AFFORDANCE SPACE                             │
  │                                                                 │
  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
  │  │  Operations  │───▶│  Dimensions  │───▶│  Constraints │      │
  │  │  (what)      │    │  (along which│    │  (valid      │      │
  │  │              │    │   axes)      │    │   regions)   │      │
  │  └──────────────┘    └──────────────┘    └──────────────┘      │
  │         │                   │                   │               │
  │         ▼                   ▼                   ▼               │
  │  ┌──────────────────────────────────────────────────────────┐  │
  │  │                   INTROSPECTION                          │  │
  │  │  • "What operations exist?"                              │  │
  │  │  • "What dimensions does operation X touch?"             │  │
  │  │  • "Given current state S, what's reachable?"            │  │
  │  │  • "Why is composition C invalid?"                       │  │
  │  │  • "What minimal specification yields outcome O?"        │  │
  │  └──────────────────────────────────────────────────────────┘  │
  │         │                                                       │
  │         ▼                                                       │
  │  ┌──────────────────────────────────────────────────────────┐  │
  │  │                   ELABORATION                            │  │
  │  │  Intent → Dimensional Questions → Minimal Specification  │  │
  │  └──────────────────────────────────────────────────────────┘  │
  └─────────────────────────────────────────────────────────────────┘

  ---
  A Pragmatic First Experiment

  Here's what I think we could build that would let us live the question:

  The Demo-Builder Affordance Layer

  Instead of giving me:
  - REST endpoints (data-shaped)
  - Typer commands (action-shaped)
  - MCP tools (function-shaped)

  Give me an affordance registry for Demo-builder that I can query:

  # Conceptual structure - not necessarily the implementation
  @affordance(
      name="add_panel",
      dimensions={
          "layout": ["primary", "auxiliary"],
          "interaction": ["active", "passive"],
          "data_binding": ["room", "story", "canvas", "none"],
      },
      preconditions=["composition_exists", "panel_id_unique"],
      effects=["panel_added", "layout_recomputed"],
      elaboration_order=["kind", "data_binding", "layout", "sizing"],
  )
  def add_panel(composition_id, panel_spec): ...

  Then I could ask:
  - query_affordances(context=current_composition) → what can I do?
  - query_dimensions("add_panel") → what axes does this touch?
  - elaborate("I want users to see the story graph") → system returns: "Which panel kind? [storyRuntime, storyEditor,
  storyPlayer]"
  - validate_composition(proposed_spec) → valid, or structured explanation of why not

  Why This Is Different From MCP/Tools

  MCP gives me functions to call. This gives me a space to navigate.

  The difference:
  ┌────────────────────────────┬───────────────────────────────────────────────┐
  │         MCP/Tools          │               Affordance Space                │
  ├────────────────────────────┼───────────────────────────────────────────────┤
  │ "Here are operations"      │ "Here is what's possible given where you are" │
  ├────────────────────────────┼───────────────────────────────────────────────┤
  │ Call fails → error message │ Query first → understand constraints          │
  ├────────────────────────────┼───────────────────────────────────────────────┤
  │ I compose blindly          │ I compose with dimensional awareness          │
  ├────────────────────────────┼───────────────────────────────────────────────┤
  │ Trial and error            │ Exploration and reasoning                     │
  └────────────────────────────┴───────────────────────────────────────────────┘
  ---
  The Experiment Structure

  Phase 1: Build the affordance layer for Demo-builder
  - Define affordances for core operations (create demo, add panel, configure policy, etc.)
  - Expose dimensional metadata
  - Implement introspection queries

  Phase 2: I use it to build real demos
  - We observe: where do I get stuck? Where do I flow?
  - We measure: how many failed attempts? How much elaboration needed?
  - We learn: which affordance structures enable vs constrain?

  Phase 3: Extract patterns
  - What affordance shapes worked best?
  - Which dimensions were actually load-bearing?
  - How does progressive elaboration compare to upfront specification?

  ---
  My question for you:

  Does this framing resonate? And if so, where should we start? I see two entry points:
  Entry Point: A. Affordance Registry
  What We'd Build First: A queryable data structure describing Demo-builder operations with dimensions, constraints, and
    effects. I'd interact with it via structured queries before taking actions.
  ────────────────────────────────────────
  Entry Point: B. Elaboration Protocol
  What We'd Build First: A conversation structure where I express intent and the system guides me through dimensional
    specification. Less upfront structure, more emergent discovery.
  Which feels like the more generative starting point for learning what actually works?
