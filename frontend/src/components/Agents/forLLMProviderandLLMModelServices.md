  **LLMProvider** (system catalog entry):
  ```python
  class LLMProvider(LLMProviderBase, table=True):
  id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
  name: str                           # "OpenAI", "Anthropic"
  provider_type: LLMProviderType      # Existing enum
  base_url: str | None                # For openai_compatible
  is_enabled: bool = True
  is_system: bool = True              # False for user-created (future)
  is_deleted: bool = False
  deleted_at: datetime | None
  created_at: datetime
  updated_at: datetime
  ```

  **LLMModel** (model catalog entry):
  ```python
  class LLMModel(LLMModelBase, table=True):
  id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
  provider_id: uuid.UUID              # FK → LLMProvider
  model_id: str                       # "gpt-4o" (no prefix)
  display_name: str                   # "GPT-4o"
  description: str | None
  context_window: int | None
  is_default: bool = False            # Cheapest/smallest per provider
  is_enabled: bool = True
  is_deprecated: bool = False
  deprecated_at: datetime | None
  sunset_at: datetime | None
  sort_order: int = 0

  # Known capabilities (nullable)
  has_vision: bool | None
  has_function_calling: bool | None
  has_streaming: bool | None
  has_json_mode: bool | None
  secondary_capabilities: dict | None  # JSON

  is_deleted: bool = False
  deleted_at: datetime | None
  created_at: datetime
  updated_at: datetime
  ```

  **Query Models** (Pydantic v2 for API filtering):
  ```python
  class LLMProviderQuery(BaseModel):
  provider_type: LLMProviderType | None = None
  is_enabled: bool | None = None
  is_system: bool | None = None
  include_deleted: bool = False

  class LLMModelQuery(BaseModel):
  provider_id: uuid.UUID | None = None
  provider_type: LLMProviderType | None = None
  is_enabled: bool | None = None
  is_deprecated: bool | None = None
  is_default: bool | None = None
  has_vision: bool | None = None
  has_function_calling: bool | None = None
  has_streaming: bool | None = None
  has_json_mode: bool | None = None
  include_deleted: bool = False
  ```

  **Response Models**:
  - `LLMProviderPublic` - includes computed `model_count`
  - `LLMModelPublic` - includes denormalized `provider_type`, `provider_name`
  - `LLMProviderWithModels` - provider with nested models list
  - `LLMModelsGrouped` - `{ providers: [...], total_models: int }`
