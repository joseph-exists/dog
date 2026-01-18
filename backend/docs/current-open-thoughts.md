  ★ Insight ─────────────────────────────────────
  Why this matters strategically:
  - Discover which models are trending (e.g., lots of users adding deepseek-r1)
  - Identify when to add official catalog support
  - Understand custom endpoint usage patterns (Ollama vs vLLM vs Azure)
  - Potential for community-contributed model metadata
  ─────────────────────────────────────────────────

  ---
  Scope of Work: User Model Registration

  Key Design Decisions First
  Question: Ownership model
  Options: Per-user vs. Global (shared)
  Recommendation: Per-user - simpler permissions, cleaner data
  ────────────────────────────────────────
  Question: Data structure
  Options: New UserLLMModel table vs. created_by on LLMModel
  Recommendation: Reuse LLMModel with is_system=false + created_by_user_id
  ────────────────────────────────────────
  Question: Provider binding
  Options: Tied to specific UserLLMProvider vs. provider type only
  Recommendation: Provider type only - more flexible, model works across user's providers
  ────────────────────────────────────────
  Question: Visibility
  Options: Private only vs. can share
  Recommendation: Private only (v1) - avoids moderation complexity
  ---
  Implementation Phases

  Phase 1: Backend - Model Registration

  Estimated: ~2-3 hours

  1.1 Update LLMModel in models.py

  class LLMModel(LLMModelBase, table=True):
      # ... existing fields ...

      # New field for user-created models
      created_by_user_id: uuid.UUID | None = Field(
          default=None, foreign_key="user.id", nullable=True
      )
      # is_system already exists (True=catalog, False=user-created)

  1.2 Add CRUD functions in crud.py

  def create_user_model(*, session, user_id, model_in: UserLLMModelCreate) -> LLMModel
  def get_user_models(*, session, user_id, provider_type?) -> list[LLMModel]
  def delete_user_model(*, session, user_id, model_id) -> bool  # ownership check

  1.3 New API routes in llm_catalog.py

  # User's custom models
  POST   /llm-catalog/models/custom          # Create custom model
  GET    /llm-catalog/models/custom          # List user's custom models
  DELETE /llm-catalog/models/custom/{id}     # Delete (ownership enforced)

  # Update existing endpoints to include user's models
  GET    /llm-catalog/models                 # Now includes user's custom models
  GET    /llm-catalog/models/grouped         # Now includes user's custom models

  1.4 New Pydantic models

  class UserLLMModelCreate(BaseModel):
      provider_type: LLMProviderType
      model_id: str                    # "llama3.2:70b"
      display_name: str | None = None  # Optional, auto-generated if missing
      description: str | None = None
      # Capabilities optional - users may not know
      has_vision: bool | None = None
      has_function_calling: bool | None = None

  1.5 Migration

  - Add created_by_user_id column
  - Add index on (created_by_user_id, is_deleted)

  ---
  Phase 2: Backend - Merge User Models into Catalog Queries

  Estimated: ~1 hour

  Update existing CRUD functions to optionally include user's custom models:

  def get_llm_models(
      *, session, user_id: uuid.UUID | None = None,  # NEW
      provider_type?, is_enabled?, ...
  ) -> tuple[list[LLMModel], int]:
      """
      Returns system models + user's custom models (if user_id provided)
      """
      query = select(LLMModel).where(
          or_(
              LLMModel.is_system == True,
              LLMModel.created_by_user_id == user_id
          ),
          LLMModel.is_deleted == False
      )

  ---
  Phase 3: Frontend - Combobox Component

  Estimated: ~1-2 hours

  3.1 Add shadcn Combobox

  npx shadcn@latest add combobox

  3.2 Create ModelCombobox component

  interface ModelComboboxProps {
    value: string
    onChange: (value: string) => void
    providerType?: LLMProviderType
    allowCustom?: boolean
    placeholder?: string
  }

  // Features:
  // - Searchable dropdown with catalog models
  // - Free text input for custom models
  // - Shows "Create custom model" option when input doesn't match
  // - Grouped by provider type

  ---
  Phase 4: Frontend - Integrate Custom Models

  Estimated: ~2-3 hours

  4.1 Update llmCatalogService.ts

  // New methods
  async createCustomModel(data: CreateCustomModelInput): Promise<CatalogModelViewModel>
  async listCustomModels(): Promise<CatalogModelViewModel[]>
  async deleteCustomModel(modelId: string): Promise<void>

  4.2 Update useLlmCatalog hook

  export function useLlmCatalog() {
    // Existing grouped query now includes user's custom models
    // (backend handles the merge)

    // New mutation for creating custom models
    const createCustomModel = useMutation({ ... })

    return {
      ...existing,
      createCustomModel,
      isCreatingModel: createCustomModel.isPending,
    }
  }

  4.3 Update ProviderModelSelector

  - Replace Select with ModelCombobox
  - On selecting unknown model → prompt to save to catalog
  - Show "Custom" badge for user-created models

  ---
  Phase 5: Graceful Fallback Display

  Estimated: ~30 mins

  Update formatModelName and display components:

  interface ModelDisplayInfo {
    label: string
    isCustom: boolean
    isDeprecated: boolean
  }

  function getModelDisplayInfo(
    modelValue: string,
    catalog: ModelOption[]
  ): ModelDisplayInfo {
    const match = catalog.find(m => m.value === modelValue)
    if (match) {
      return { label: match.label, isCustom: !match.isSystem, isDeprecated: match.isDeprecated }
    }
    // Fallback for completely unknown models
    return {
      label: formatRawModelId(modelValue),
      isCustom: true,
      isDeprecated: false
    }
  }

  ---
  Summary
  ┌─────────┬────────────────────────────────┬────────────┐
  │  Phase  │              Work              │  Estimate  │
  ├─────────┼────────────────────────────────┼────────────┤
  │ Phase 1 │ Backend model registration     │ 2-3 hrs    │
  ├─────────┼────────────────────────────────┼────────────┤
  │ Phase 2 │ Merge user models into queries │ 1 hr       │
  ├─────────┼────────────────────────────────┼────────────┤
  │ Phase 3 │ Combobox component             │ 1-2 hrs    │
  ├─────────┼────────────────────────────────┼────────────┤
  │ Phase 4 │ Frontend integration           │ 2-3 hrs    │
  ├─────────┼────────────────────────────────┼────────────┤
  │ Phase 5 │ Graceful fallback display      │ 30 mins    │
  ├─────────┼────────────────────────────────┼────────────┤
  │ Total   │                                │ 7-10 hours │
  └─────────┴────────────────────────────────┴────────────┘
  ---
  Data You'll Capture

  -- Analytics queries you can run later:
  SELECT model_id, COUNT(*) as user_count
  FROM llmmodel
  WHERE is_system = false
  GROUP BY model_id
  ORDER BY user_count DESC;

  -- "What custom models are users adding most?"
  -- "Which provider_type has the most custom models?"
  -- "Should we add official support for 'deepseek-r1'?"

  ---
  Would you like me to start with Phase 1 (backend model registration), or would you prefer to refine the design
  decisions first?











