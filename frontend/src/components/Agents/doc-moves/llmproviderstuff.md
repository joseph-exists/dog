  Additional Design Questions

  1. Model Identifier Format : decision: fully normalized. we can TRUNCATE all providers, agents, etc after this implementation.


  ---
  2. Uniqueness Constraints

  # LLMProvider
  __table_args__ = (
      UniqueConstraint("provider_type", name="uq_llm_provider_type"),  # Only one "openai" provider?
  )

  # LLMModel
  __table_args__ = (
      UniqueConstraint("provider_id", "model_id", name="uq_llm_model_provider_model"),
  )

  Question: Can there be multiple LLMProvider rows with the same provider_type? Yes.
  - If no: One canonical "OpenAI" provider, all users reference it
  - If yes: Allows system OpenAI + user's Azure OpenAI (both openai_compatible)

  ---
  3. OpenAI-Compatible Handling: C. top level requirement.

  This is the tricky one. Current options:
  Approach: A) Special provider type
  Description: openai_compatible remains an enum value. Users can add custom endpoints via UserLLMProvider with custom base_url.
    Models are user-defined, not in LLMModel table.
  ────────────────────────────────────────
  Approach: B) User-created providers
  Description: Users can create their own LLMProvider rows (with is_system=False) for Ollama, vLLM, etc. They also add their own
    LLMModel entries.
  ────────────────────────────────────────
  Approach: C) Hybrid
  Description: System providers are fixed. For openai_compatible, we store a template provider, but models are dynamic/user-defined.


  ---
  4. Enabled State Cascading : implicitly disabled. 

  If LLMProvider.is_enabled = False, should its models be implicitly disabled?

  - Implicit cascade: Simpler, but hidden behavior
  - Explicit per-model: More control, but more maintenance

  Recommendation: Implicit - if provider is disabled, models are unavailable regardless of their own is_enabled state. Document this behavior.

  ---
  5. Default Model per Provider: yes, is_default is the cheapest possible model.

  Should we have is_default: bool on LLMModel?

  Use case: When user selects a provider but not a model, we auto-select the default.

  # LLMModel
  is_default: bool = Field(default=False)  # Only one per provider

  ---
  6. API Endpoint Structure

  What endpoints do we need?

  GET /api/v1/llm-providers                    # List all system providers
  GET /api/v1/llm-providers/{id}               # Get provider details
  GET /api/v1/llm-providers/{id}/models        # Models for a provider
  GET /api/v1/llm-models                       # All models (flat, filterable)
  GET /api/v1/llm-models/grouped               # Models grouped by provider (original request)

  Or simpler for MVP:

  GET /api/v1/llm-providers/supported-models   # Original request - all models grouped

  ---
  7. Seed Data Strategy : deferring decision for now.

  How do we populate initial providers/models?
  ┌─────────────────┬──────────────────────────────────────────────────┐
  │    Approach     │                   Description                    │
  ├─────────────────┼──────────────────────────────────────────────────┤
  │ A) In migration │ INSERT INTO llm_provider... in Alembic migration │
  ├─────────────────┼──────────────────────────────────────────────────┤
  │ B) Seed script  │ Separate python scripts/seed_llm_data.py         │
  ├─────────────────┼──────────────────────────────────────────────────┤
  │ C) App startup  │ Check on startup, insert if missing              │
  └─────────────────┴──────────────────────────────────────────────────┘
  Recommendation: Option A - migrations are versioned, repeatable, and run automatically. Include seed data in the same migration
   that creates the tables.

  ---
  8. Soft Delete - yes to softdelete for both.

  Should we use is_deleted + deleted_at or hard delete?

  For models that get deprecated/removed:
  - Soft delete: Preserves history, agents referencing old models still have context
  - Hard delete: Cleaner, but FK constraints could fail

  Recommendation: Soft delete for LLMModel (models get deprecated), hard delete for LLMProvider (rarely removed).

  ---
  Summary of Open Questions

  1. Model ID format - Keep "provider:model" or just "model_id"?  Just model_id. fully normalized. we can TRUNCATE all providers, agents, etc after this implementation.
  2. Provider uniqueness - One per provider_type or allow multiples? allow multiples - required.
  3. OpenAI-compatible - Option A (special type), B (user-created), or C (hybrid)?  A, but we need to move to C very quickly.
  4. Default model flag - Include is_default yes, the cheapest smallest option (if known)
  5. Endpoint structure - GETs listed, plus queryable schema (with pydantic v2 queryability for api call composition as first class citizen)
  6. Soft delete - For both
