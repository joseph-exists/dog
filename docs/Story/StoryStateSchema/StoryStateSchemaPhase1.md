## Phase 1: Backend Model : COMPLETE.  ALL code added to models.py for phase 1.

### File: `backend/app/models.py`

Add after StoryRequirement models (~line 645):

**1.1 StateValueType Enum**
```python
class StateValueType(str, Enum):
    BOOLEAN = "boolean"
    NUMBER = "number"
    STRING = "string"
    ENUM = "enum"
```

**1.2 Model Hierarchy**
```python
class StoryStateVariableBase(SQLModel):
    key: str = Field(min_length=1, max_length=100)
    value_type: StateValueType = Field(default=StateValueType.STRING)
    default_value: Any | None = Field(default=None, sa_column=Column(JSON))
    enum_values: list[str] | None = Field(default=None, sa_column=Column(JSON))
    description: str | None = Field(default=None, max_length=500)
    category: str | None = Field(default=None, max_length=100)

class StoryStateVariableCreate(StoryStateVariableBase):
    story_id: uuid.UUID
    story_version: int

class StoryStateVariableUpdate(SQLModel):
    key: str | None = Field(default=None, min_length=1, max_length=100)
    value_type: StateValueType | None = None
    default_value: Any | None = None
    enum_values: list[str] | None = None
    description: str | None = Field(default=None, max_length=500)
    category: str | None = Field(default=None, max_length=100)

class StoryStateVariable(StoryStateVariableBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    story_id: uuid.UUID = Field(foreign_key="story.id", nullable=False, ondelete="CASCADE")
    story_version: int = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class StoryStateVariablePublic(StoryStateVariableBase):
    id: uuid.UUID
    story_id: uuid.UUID
    story_version: int

class StoryStateVariablesPublic(SQLModel):
    data: list[StoryStateVariablePublic]
    count: int
```

**1.3 Validation Response Models**
```python
class StateSchemaValidationError(SQLModel):
    variable_key: str
    used_in: str  # "requires_state" or "sets_state"
    choice_id: uuid.UUID
    choice_text: str
    from_node_id: uuid.UUID
    from_node_title: str

class StateSchemaValidationResult(SQLModel):
    is_valid: bool
    errors: list[StateSchemaValidationError]
    defined_variables: list[str]
    used_variables: list[str]
    undefined_variables: list[str]
```

**1.4 Relationships** (add at end of models.py with other post-definitions)
```python
Story.state_variables = Relationship(
    back_populates="story",
    sa_relationship_kwargs={"cascade": "all, delete-orphan"}
)
StoryStateVariable.story = Relationship(back_populates="state_variables")
```