class LLMModelBase(SQLModel):
    """Base model for LLM model catalog entries."""
    model_id: str = Field(max_length=100, description="Model identifier (e.g., 'gpt-4o', no provider prefix)")
    display_name: str = Field(max_length=100, description="Human-friendly name (e.g., 'GPT 4o')")
    description: str | None = Field(default=None, max_length=500)
    context_window: int | None = Field(default=None, description="Max tokens in context window")
    is_system: bool = Field(default=False, description="system model")
    is_default: bool = Field(default=False, description="Default/cheapest model for this provider")
    is_enabled: bool = Field(default=True, description="Whether model is available for use")
    is_deprecated: bool = Field(default=False, description="Model is deprecated (still works)")
    sort_order: int = Field(default=0, description="Display ordering within provider")

    # Known capabilities (nullable = unknown)
    has_vision: bool | None = Field(default=None, description="Supports image input")
    has_function_calling: bool | None = Field(default=None, description="Supports function/tool calling")
    has_streaming: bool | None = Field(default=None, description="Supports streaming responses")
    has_json_mode: bool | None = Field(default=None, description="Supports JSON output mode")

    # Additional capabilities as JSON for extensibility
    secondary_capabilities: dict[str, Any] | None = Field(
        default=None,
        description="Additional capability flags as JSON"
    )

class LLMModelCreate(LLMModelBase):
    """Input model for creating a model catalog entry."""
    provider_id: uuid.UUID = Field(
        description="Owner provider spec type for this catalog entry"
    )
    display_name: str | None = Field(
        default=None,
        max_length=100,
        description="extra words here I guess"
    )


class LLMModelUpdate(LLMModelBase):
    """Update model for model catalog entries - all fields optional."""
    display_name: str | None = Field(
        default=None,
        max_length=100,
        description="Optional human-friendly name during updates"
    )
    description: str | None = Field(default=None, max_length=500)
    context_window: int | None = Field(default=None, description="Max tokens in context window")
    is_default: bool | None = Field(default=None, description="Default/cheapest model for this provider")
    is_enabled: bool | None = Field(default=None, description="Whether model is available for use")
    is_deprecated: bool | None = Field(default=None, description="Model is deprecated (still works)")
    sort_order: int | None = Field(default=None, description="Display ordering within provider")
    has_vision: bool | None = Field(default=None, description="Supports image input")
    has_function_calling: bool | None = Field(default=None, description="Supports function/tool calling")
    has_streaming: bool | None = Field(default=None, description="Supports streaming responses")
    has_json_mode: bool | None = Field(default=None, description="Supports JSON output mode")
    secondary_capabilities: dict[str, Any] | None = Field(
        default=None,
        description="Additional capability flags as JSON"
    )


class LLMModel(LLMModelBase, table=True):
    """
    Database model for LLM model catalog.

    Stores available models per provider with their capabilities.
    model_id is the normalized name without provider prefix (e.g., 'gpt-4o').
    """
    __tablename__ = "llmmodel"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    provider_id: uuid.UUID = Field(
        foreign_key="provider_type.id",
        nullable=False,
        index=True,
        description="API base (anthropic, google, openai, openai_compatible, custom, empty)"
    )
    is_system: bool = Field(default=False, index=True)
    # Deprecation tracking
    deprecated_at: datetime | None = Field(default=None, description="When model was deprecated")
    sunset_at: datetime | None = Field(default=None, description="When model will stop working")

    # Soft delete support
    is_deleted: bool = Field(default=False, index=True)
    deleted_at: datetime | None = Field(default=None)

    # Audit timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"onupdate": datetime.now},
    )

    secondary_capabilities: dict[str, Any] | None = Field(
        default=None,
        description="Additional capability flags as JSONB",
        sa_column=Column(JSONB),
    )

    created_by_user_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="user.id",
        nullable=True,
    )


class LLMModelPublic(LLMModelBase):
    """Public API response for a model catalog entry."""
    id: uuid.UUID
    provider_id: uuid.UUID
    deprecated_at: datetime | None
    sunset_at: datetime | None
    is_deleted: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime
    # Denormalized provider info for convenience
    provider_type: str | None = None
    provider_name: str | None = None


class LLMModelsPublic(SQLModel):
    """Collection response for LLMModels."""
    data: list[LLMModelPublic]
    count: int


tinyfoot-# \d llmmodel
                                Table "public.llmmodel"
         Column         |            Type             | Collation | Nullable | Default 
------------------------+-----------------------------+-----------+----------+---------
 model_id               | character varying(100)      |           | not null | 
 display_name           | character varying(100)      |           | not null | 
 description            | character varying(500)      |           |          | 
 context_window         | integer                     |           |          | 
 is_default             | boolean                     |           | not null | 
 is_enabled             | boolean                     |           | not null | 
 is_deprecated          | boolean                     |           | not null | 
 sort_order             | integer                     |           | not null | 
 has_vision             | boolean                     |           |          | 
 has_function_calling   | boolean                     |           |          | 
 has_streaming          | boolean                     |           |          | 
 has_json_mode          | boolean                     |           |          | 
 id                     | uuid                        |           | not null | 
 provider_id            | uuid                        |           | not null | 
 deprecated_at          | timestamp without time zone |           |          | 
 sunset_at              | timestamp without time zone |           |          | 
 is_deleted             | boolean                     |           | not null | 
 deleted_at             | timestamp without time zone |           |          | 
 created_at             | timestamp without time zone |           | not null | 
 updated_at             | timestamp without time zone |           | not null | 
 secondary_capabilities | jsonb                       |           |          | 
 is_system              | boolean                     |           | not null | 
 created_by_user_id     | uuid                        |           |          | 
Indexes:
    "llmmodel_pkey" PRIMARY KEY, btree (id)
    "ix_llmmodel_is_deleted" btree (is_deleted)
    "ix_llmmodel_is_system" btree (is_system)
    "ix_llmmodel_provider_id" btree (provider_id)
Foreign-key constraints:
    "llmmodel_created_by_user_id_fkey" FOREIGN KEY (created_by_user_id) REFERENCES "user"(id)
    "llmmodel_provider_id_fkey" FOREIGN KEY (provider_id) REFERENCES provider_type(id)


