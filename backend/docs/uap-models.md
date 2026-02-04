
what we think we want:

to distinguish (at creation, read, and update) between user_agent_configs which satisfy a certain set of query parameters, while also maintaining our ability to keep all user_agent_configs centralized within one table.

we need to establish a pattern that enables us to map API calls to specific combinations of requirements.

For one possible example:

we expose a "User Agent Config Creation" form on our website.

The user needs to select from 5 different types of User Agent Configs.  

Those types map to the 'provider_type' below.

They select User Agent Config Type 1.

The form they are given maps to the fields required for User Agent Config Type 1. Type 1 requires the parameter 'scope'. (this is critical - different User Agent Config types will have different required parameters.)

They fill out that form, submit it, and it's validated against which fields are required for Agent Config Type 1.  The first time they fill it out, they don't include 'scope'.  It's rejected for being invalid (by API).  They add 'scope=x',resubmit, it passes API validation for Type 1. 

It's then saved to the user_agent_configs table. (Later, if they need to edit this User Agent Config, they are shown only those fields for edit which are required for Agent Config Type 1.)

this makes this user_agent_config usable in the following ways:
 - returned by API search for all user_agent_configs that user created.
 - queryable by API for user_agent_configs created by that user with provider_type=1
 - queryable by API for user_agent_configs created by that user with provider_type=1
 - queryable by API for user_agent_configs created by that user with scope=x



```sql
tinyfoot=# \d user_agent_configs;
                          Table "public.user_agent_configs"
        Column        |            Type             | Collation | Nullable | Default 
----------------------+-----------------------------+-----------+----------+---------
 name                 | character varying(100)      |           |          | 
 slug                 | character varying(50)       |           |          | 
 description          | character varying(500)      |           |          | 
 user_access_provider | uuid                        |           |          | 
 provider_type        | uuid                        |           |          | 
 model_id             | uuid                        |           |          | 
 model_name           | character varying           |           |          | 
 system_prompt        | character varying           |           |          | 
 custom_system_prompt | character varying           |           |          | 
 instructions         | character varying           |           |          | 
 tool_config          | json                        |           |          | 
 deps_config          | json                        |           |          | 
 agent_metadata       | json                        |           |          | 
 is_enabled           | boolean                     |           |          | 
 is_clonable          | boolean                     |           |          | 
 is_visible           | boolean                     |           |          | 
 scope                | character varying           |           |          | 
 participation_mode   | character varying           |           |          | 
 is_coordinator       | boolean                     |           |          | 
 max_tool_iterations  | integer                     |           |          | 
 capabilities         | json                        |           |          | 
 id                   | uuid                        |           | not null | 
 owner_id             | uuid                        |           |          | 
 created_at           | timestamp without time zone |           | not null | 
 updated_at           | timestamp without time zone |           |          | 
 version              | integer                     |           | not null | 
 model                | character varying(20)       |           |          | 
Indexes:
    "user_agent_configs_pkey" PRIMARY KEY, btree (id)
Foreign-key constraints:
    "user_agent_configs_owner_id_fkey" FOREIGN KEY (owner_id) REFERENCES "user"(id)
Referenced by:
    TABLE "agent_personas" CONSTRAINT "agent_personas_agent_id_fkey" FOREIGN KEY (agent_id) REFERENCES user_agent_configs(id) ON DELETE CASCADE
    TABLE "room_participant_bindings" CONSTRAINT "room_participant_bindings_agent_id_fkey" FOREIGN KEY (agent_id) REFERENCES user_agent_configs(id)
```

```python
class UserAgentConfigBase(SQLModel):
    """Base properties shared by all agent config representations."""
    name: str = Field(max_length=100, description="Display name")
    slug: str = Field(max_length=50, description="Unique identifier/registry key")
    description: str | None = Field(default=None, max_length=500)
    user_access_provider: uuid.UUID | None = Field(default=None, foreign_key="user_access_provider.id", description="User-selected provider associated with this agent config")
    provider_type: uuid.UUID | None = Field(default_factory=uuid.uuid4)
    model: str | None=Field(default=None, max_length=20, description="friendly name of model as specified by api and user access providers")
    model_id: uuid.UUID | None = Field(default=None, foreign_key="user_access_provider.id", description="model associated with this agent config")
    # LLMModels table
    model_name: str = Field(default="friendly model name")
    system_prompt: str | None = None
    custom_system_prompt: str | None = Field(default=None, description="Optional user override for system prompt")
    instructions: str | None = Field(default=None, description="big ass text field for lots of words.")
    # JSON configuration fields
    tool_config: dict | None = Field(default=None, sa_column=Column(JSON))
    deps_config: dict | None = Field(default=None, sa_column=Column(JSON))
    agent_metadata: dict | None = Field(default=None, sa_column=Column(JSON))

    # Behavior flags
    is_enabled: bool = Field(default=True)
    is_clonable: bool = Field(default=False)
    is_visible: bool = Field(default=False)
    scope: str = Field(default="personal")  # "personal" | "system"
    participation_mode: str = Field(default="on_mention")  # "always" | "on_mention" | "manual"

    # Coordinator mode: if True, this agent processes messages FIRST
    # before other agents, acting as an orchestrator that routes to specialists
    is_coordinator: bool = Field(default=False)

    # Maximum number of LLM requests per agent run (prevents runaway tool loops)
    max_tool_iterations: int = Field(default=10)

    # Agent capabilities for discovery and A2A coordination
    # e.g., ["story-structure", "dialogue", "character-development", "plot-twists"]
    capabilities: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    @field_validator("capabilities", mode="before")
    @classmethod
    def capabilities_none_to_list(cls, v: list[str] | None) -> list[str]:
        """Convert NULL from database to empty list."""
        return v if v is not None else []

class UserAgentConfigCreate(UserAgentConfigBase):
    pass

class UserAgentConfigUpdate(UserAgentConfigBase):
    name: str | None = Field(default=None, max_length=100, description="Display name")
    slug: str | None = Field(default=None, max_length=50, description="Unique identifier/registry key")
    description: str | None = Field(default=None, max_length=500)
    user_access_provider: uuid.UUID | None = Field(default=None, description="User-selected provider associated with this agent config")
    provider_type: uuid.UUID | None=Field(default_factory=uuid.uuid4)
    model_id: uuid.UUID | None = Field(default=None, description="model associated with this agent config")
    model: str | None=Field(default=None, max_length=20, description="friendly name of model as specified by api and user access providers")
    model_name: str | None = Field(default=None)
    system_prompt: str | None = Field(default=None)
    custom_system_prompt: str | None = Field(default=None, description="Optional user override for system prompt")
    instructions: str | None = Field(default=None, description="big ass text field for lots of words.")
    tool_config: dict | None = Field(default=None)
    deps_config: dict | None = Field(default=None)
    agent_metadata: dict | None = Field(default=None)
    is_enabled: bool | None = Field(default=None)
    is_clonable: bool | None = Field(default=None)
    is_visible: bool | None = Field(default=None)
    scope: str | None = Field(default=None)
    participation_mode: str | None = Field(default=None)
    is_coordinator: bool | None = Field(default=None)
    max_tool_iterations: int | None = Field(default=None)
    capabilities: list[str] | None = Field(default=None)

class UserAgentConfig(UserAgentConfigBase, table=True):
    __tablename__ = "user_agent_configs"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID | None = Field(default_factory=uuid.uuid4, foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime | None = Field(default=None, sa_column_kwargs={"onupdate": datetime.now})
    version: int = Field(default=1)
    name: str | None = Field(default=None, max_length=100, description="Display name")
    slug: str | None = Field(default=None, max_length=50, description="Unique identifier/registry key")
    description: str | None = Field(default=None, max_length=500)
    user_access_provider: uuid.UUID | None = Field(default=None, description="User-selected provider associated with this agent config")
    provider_type: uuid.UUID | None = Field(default_factory=uuid.uuid4)
    model: str | None=Field(default=None, max_length=20, description="friendly name of model as specified by api and user access providers")
    model_id: uuid.UUID | None = Field(default=None, description="model associated with this agent config")
    model_name: str | None = Field(default=None)
    system_prompt: str | None = Field(default=None)
    custom_system_prompt: str | None = Field(default=None, description="Optional user override for system prompt")
    instructions: str | None = Field(default=None, description="big ass text field for lots of words.")
    tool_config: dict | None = Field(default=None, sa_column=Column(JSON))
    deps_config: dict | None = Field(default=None, sa_column=Column(JSON))
    agent_metadata: dict | None = Field(default=None, sa_column=Column(JSON))
    is_enabled: bool | None = Field(default=None)
    is_clonable: bool | None = Field(default=None)
    is_visible: bool | None = Field(default=None)
    scope: str | None = Field(default=None)
    participation_mode: str | None = Field(default=None)
    is_coordinator: bool | None = Field(default=None)
    max_tool_iterations: int | None = Field(default=None)
    capabilities: list[str] | None = Field(default=None, sa_column=Column(JSON))

class UserAgentConfigPublic(UserAgentConfigBase):
    id: uuid.UUID
    owner_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime | None
    version: int
    name: str | None = Field(default=None, max_length=100, description="Display name")
    slug: str | None = Field(default=None, max_length=50, description="Unique identifier/registry key")
    description: str | None = Field(default=None, max_length=500)
    user_access_provider: uuid.UUID | None = Field(default=None, description="User-selected provider associated with this agent config")
    provider_type: uuid.UUID | None = Field(default_factory=uuid.uuid4)
    model: str | None=Field(default=None, max_length=20, description="friendly name of model as specified by api and user access providers")
    model_id: uuid.UUID | None = Field(default=None, description="model associated with this agent config")
    model_name: str | None = Field(default=None)
    system_prompt: str | None = Field(default=None)
    custom_system_prompt: str | None = Field(default=None, description="Optional user override for system prompt")
    instructions: str | None = Field(default=None, description="big ass text field for lots of words.")
    tool_config: dict | None = Field(default=None)
    deps_config: dict | None = Field(default=None)
    agent_metadata: dict | None = Field(default=None)
    is_enabled: bool | None = Field(default=None)
    is_clonable: bool | None = Field(default=None)
    is_visible: bool | None = Field(default=None)
    scope: str | None = Field(default=None)
    participation_mode: str | None = Field(default=None)
    is_coordinator: bool | None = Field(default=None)
    max_tool_iterations: int | None = Field(default=None)
    capabilities: list[str] | None = Field(default=None)

class UserAgentConfigsPublic(SQLModel):
    data: list[UserAgentConfigPublic]
    count: int
```