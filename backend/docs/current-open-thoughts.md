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


ADDITION: updated LLMProvider in models.py

 LLMProvider(LLMProviderBase)   

        created_by_user_id: uuid.UUID | None = Field(
          default=None, foreign_key="user.id", nullable=True
      )


  1.2 Add CRUD functions in crud.py

  def create_user_model(*, session, user_id, model_in: UserLLMModelCreate) -> LLMModel
  
  def get_user_models(*, session, user_id, provider_type?) -> list[LLMModel]
  
  def delete_user_model(*, session, user_id, model_id) -> bool  # ownership check - this needs to be a soft-delete.  if a user has created a model for a provider, and it's a valid model for that provider, and other users are using it - then deleting it isn't a great idea?

 def create user_llm_provider(*, session, user_id, ...)
 # what function are we using when users add providers and api keys now?  that 


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

  ---
  User Journey Analysis

  ★ Insight ─────────────────────────────────────
  The "aha moment": When a user types llama3.2:70b, sees "Add as custom model", clicks once, and it just works. No forms,
   no modals, no friction.

  The delight factor: The system learns their models and surfaces them intelligently everywhere.
  ─────────────────────────────────────────────────

  Key User Scenarios
  ┌──────────────────────────────────────┬─────────────────────────────────────┬────────────────────────────────┐
  │               Scenario               │            User Mindset             │            Our Goal            │
  ├──────────────────────────────────────┼─────────────────────────────────────┼────────────────────────────────┤
  │ Ollama user types mistral:7b         │ "I just want to use my local model" │ Zero friction creation         │
  ├──────────────────────────────────────┼─────────────────────────────────────┼────────────────────────────────┤
  │ Azure user has gpt-4-deployment-prod │ "My deployment name is weird"       │ Accept anything, format nicely │
  ├──────────────────────────────────────┼─────────────────────────────────────┼────────────────────────────────┤
  │ Power user with 10 custom models     │ "I need to manage these"            │ Easy overview & cleanup        │
  ├──────────────────────────────────────┼─────────────────────────────────────┼────────────────────────────────┤
  │ New user exploring                   │ "What models can I use?"            │ Clear catalog + custom option  │
  └──────────────────────────────────────┴─────────────────────────────────────┴────────────────────────────────┘
  ---
  Frontend Feature Set

  1. ModelCombobox - The Core Experience

  ┌─ Model ─────────────────────────────────────────┐
  │ 🔍 mistral:7b                                   │
  ├─────────────────────────────────────────────────┤
  │  ⭐ Recently Used                               │
  │     Claude 3.5 Haiku                            │
  │     llama3.2:70b               [Custom]         │
  │                                                 │
  │  📦 Catalog                                     │
  │     GPT-4o                                      │
  │     GPT-4o Mini                                 │
  │     Claude Sonnet 4                             │
  │     ...                                         │
  │                                                 │
  │  ─────────────────────────────────────────────  │
  │  ✨ Add "mistral:7b" as custom model            │  ← appears when no match
  └─────────────────────────────────────────────────┘

  Key behaviors:
  - Type-ahead search across catalog + custom models
  - Recently used section at top (persisted in localStorage or backend)
  - Visual badges distinguish [Custom] vs [Deprecated]
  - Inline creation - one click adds the model, no modal
  - Provider grouping optional (collapsible sections)

  ---
  2. Smart Model ID Parsing

  When user types a custom model, we auto-generate a nice display name:

  function suggestDisplayName(modelId: string): string {
    // "llama3.2:70b" → "Llama 3.2 70B"
    // "ft:gpt-3.5-turbo:acme:abc" → "GPT-3.5 Turbo (Fine-tuned)"
    // "gpt-4-turbo-deployment" → "GPT-4 Turbo Deployment"
    // "mistral-7b-instruct-v0.2" → "Mistral 7B Instruct v0.2"
  }

  Rules:
  - Replace -, _, : with spaces (context-aware)
  - Capitalize appropriately (preserve "GPT", "LLM", version numbers)
  - Detect common patterns: ft: prefix → add "(Fine-tuned)"
  - Detect size indicators: 7b, 70b, 8x7b → "7B", "70B", "8x7B"

  ---
  3. Inline Creation Flow (Zero Friction)

  User types: "deepseek-r1"
             ↓
  No match found, show:
  ┌─────────────────────────────────────────────────┐
  │  ✨ Add "deepseek-r1" as custom model           │
  │     Display name: Deepseek R1      [edit]       │
  │     Provider: OpenAI Compatible    [change]     │
  │                                    [Add Model]  │
  └─────────────────────────────────────────────────┘
             ↓
  User clicks [Add Model]
             ↓
  Model created, immediately selected, dropdown closes
  Toast: "Added Deepseek R1 to your models"

  No modal - everything happens inline in the combobox dropdown.

  ---
  4. Custom Model Visual Treatment

  In dropdowns:
    GPT-4o                              ← catalog (no badge)
    Claude 3.5 Haiku                    ← catalog
    llama3.2:70b            [Custom]    ← user's model (subtle badge)
    old-model               [Custom] ⚠️  ← user's + not recently used

  In display contexts (cards, headers):
  <ModelBadge model={model}>
    {model.isCustom && <Badge variant="outline" className="text-xs">Custom</Badge>}
    {model.displayName}
  </ModelBadge>

  ---
  5. Settings: Custom Models Management

  Add a section in User Settings (near LLM Providers):

  ┌─ Your Custom Models ────────────────────────────┐
  │                                                 │
  │  You have 3 custom models                       │
  │                                                 │
  │  ┌─────────────────────────────────────────┐   │
  │  │ 🔮 Llama 3.2 70B                        │   │
  │  │    llama3.2:70b • OpenAI Compatible     │   │
  │  │    Last used: 2 days ago          [···] │   │ ← menu: edit, delete
  │  └─────────────────────────────────────────┘   │
  │                                                 │
  │  ┌─────────────────────────────────────────┐   │
  │  │ 🔮 Deepseek R1                          │   │
  │  │    deepseek-r1 • OpenAI Compatible      │   │
  │  │    Last used: Today               [···] │   │
  │  └─────────────────────────────────────────┘   │
  │                                                 │
  │  ┌─────────────────────────────────────────┐   │
  │  │ 🔮 GPT-4 Turbo (Fine-tuned)             │   │
  │  │    ft:gpt-4-turbo:acme:xyz • OpenAI     │   │
  │  │    Last used: 1 week ago          [···] │   │
  │  └─────────────────────────────────────────┘   │
  │                                                 │
  │  [+ Add Custom Model]                           │
  │                                                 │
  └─────────────────────────────────────────────────┘

  Features:
  - View all custom models
  - Edit display name / provider type
  - Delete (with confirmation)
  - See last used date
  - Quick add button (for power users who want to pre-register)

  ---
  6. Contextual Onboarding

  First-time hint (shown once per user):

  ┌─ Model ─────────────────────────────────────────┐
  │ 🔍 Select a model...                            │
  ├─────────────────────────────────────────────────┤
  │  💡 Tip: Using Ollama or a custom endpoint?     │
  │     Just type your model name and we'll add it! │
  │                                         [Got it]│
  ├─────────────────────────────────────────────────┤
  │  📦 Catalog                                     │
  │     GPT-4o                                      │

  Provider-specific hints when openai_compatible is selected:

  Using OpenAI Compatible provider?
  Common model formats:
  • Ollama: mistral:7b, llama3:70b
  • vLLM: meta-llama/Llama-2-7b
  • Azure: your-deployment-name

  ---
  7. Recently Used Intelligence

  Track model usage and surface intelligently:

  // Store in localStorage or sync to backend
  interface RecentModel {
    modelValue: string      // "openai:gpt-4o" or "openai_compatible:llama3:70b"
    lastUsedAt: Date
    useCount: number
  }

  // In combobox, sort recently used by:
  // 1. Frequency (useCount)
  // 2. Recency (lastUsedAt)
  // Show top 3-5

  ---
  8. Optional: Capability Quick-Set

  When creating a custom model, offer optional capability toggles:

  ┌─────────────────────────────────────────────────┐
  │  ✨ Add "llama3.2:70b-vision" as custom model   │
  │                                                 │
  │  Display name: Llama 3.2 70B Vision    [edit]   │
  │  Provider: OpenAI Compatible           [change] │
  │                                                 │
  │  Capabilities (optional):                       │
  │  ☐ Supports vision/images                       │
  │  ☐ Supports function calling                    │
  │  ☑ Supports streaming        ← default checked  │
  │                                                 │
  │                               [Add Model]       │
  └─────────────────────────────────────────────────┘

  This helps with future filtering ("show me vision-capable models").

  ---
  Component Architecture

  src/
  ├── components/
  │   ├── ui/
  │   │   └── model-combobox.tsx        # Core combobox component
  │   │
  │   ├── Agents/
  │   │   └── providers/
  │   │       ├── ModelCombobox.tsx      # Wrapper with catalog integration
  │   │       ├── ModelBadge.tsx         # Display with custom/deprecated badges
  │   │       └── InlineModelCreator.tsx # The "add custom" inline form
  │   │
  │   └── UserSettings/
  │       └── CustomModels.tsx           # Settings management page
  │
  ├── hooks/
  │   ├── useLlmCatalog.ts              # + createCustomModel mutation
  │   └── useRecentModels.ts            # Track recently used (new)
  │
  └── services/
      └── llmCatalogService.ts          # + custom model CRUD methods

  ---
  Delight Checklist
  ┌──────────────────────────────────┬────────┬────────┐
  │             Feature              │ Impact │ Effort │
  ├──────────────────────────────────┼────────┼────────┤
  │ ✨ Inline creation (no modal)    │ High   │ Medium │
  ├──────────────────────────────────┼────────┼────────┤
  │ 🔍 Type-ahead search             │ High   │ Low    │
  ├──────────────────────────────────┼────────┼────────┤
  │ 📛 Smart display name generation │ Medium │ Low    │
  ├──────────────────────────────────┼────────┼────────┤
  │ ⭐ Recently used section         │ High   │ Low    │
  ├──────────────────────────────────┼────────┼────────┤
  │ 🏷️ Custom model badges           │ Medium │ Low    │
  ├──────────────────────────────────┼────────┼────────┤
  │ ⚙️ Settings management page      │ Medium │ Medium │
  ├──────────────────────────────────┼────────┼────────┤
  │ 💡 First-time onboarding hint    │ Medium │ Low    │
  ├──────────────────────────────────┼────────┼────────┤
  │ 🎛️ Optional capability toggles   │ Low    │ Medium │
  └──────────────────────────────────┴────────┴────────┘
  ---
  Recommended Build Order

  1. ModelCombobox - Core component with search + free text
  2. Inline creation - The "Add as custom model" flow
  3. Badge treatment - Visual distinction
  4. Settings page - View/manage custom models
  5. Recently used - Polish feature
  6. Onboarding hints - Final polish

  ---
  Would you like me to start implementing the ModelCombobox component, or should we first sketch out the exact
  interaction states in more detail?









