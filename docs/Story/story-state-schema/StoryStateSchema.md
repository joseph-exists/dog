# StoryStateSchema Implementation Plan

## Summary

Added a `StoryStateVariable` model that allows authors to define a schema for story state variables. Variables are versioned per `story_version` (like StoryNode), support boolean/number/string/enum types, and enable validation of undefined variables during publish.

## Design Decisions

| Decision | Choice |
|----------|--------|
| Versioning | Per story_version (locked when published) |
| Value Types | boolean, number, string, enum |
| Validation | Soft block (allow save, block publish) |
| Categories | Yes, optional grouping field |

---

## Phase 1: Backend Model

### File: `backend/app/models.py`

Added after StoryRequirement models (~line 645):

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

**1.4 Relationships** (added at end of models.py with other post-definitions)
```python
Story.state_variables = Relationship(
    back_populates="story",
    sa_relationship_kwargs={"cascade": "all, delete-orphan"}
)
StoryStateVariable.story = Relationship(back_populates="state_variables")
```

---

## Phase 2: CRUD Operations

### File: `backend/app/crud.py`

Add after story requirement functions:

- `get_story_state_variables(session, story_id, story_version, skip, limit)` → tuple[list, int]
- `create_story_state_variable(session, variable_in)` → StoryStateVariable
- `update_story_state_variable(session, variable_id, variable_in)` → StoryStateVariable
- `delete_story_state_variable(session, variable_id)` → None
- `get_undefined_variables_in_choices(session, story_id, story_version)` → StateSchemaValidationResult

Key validation logic in `get_undefined_variables_in_choices`:
1. Get all defined variable keys from schema
2. Get all choices for nodes in this story version
3. Extract keys from `requires_state` and `sets_state`
4. Report any keys not in schema as errors

---

## Phase 3: API Routes

### File: `backend/app/api/routes/stories.py`

Add nested endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/{story_id}/versions/{version}/state-schema` | List variables |
| POST | `/{story_id}/versions/{version}/state-schema` | Create variable |
| PUT | `/{story_id}/versions/{version}/state-schema/{id}` | Update variable |
| DELETE | `/{story_id}/versions/{version}/state-schema/{id}` | Delete variable |
| GET | `/{story_id}/versions/{version}/state-schema/validate` | Check for undefined vars |

**Authorization:**
- Read: Any authenticated user
- Write: Story owner or superuser only
- Block edits to published_version

**Modified `create_new_story_version`:** Copy state variables when creating new version from published.

**Modified `publish_story`:** Call validation, return 422 with undefined variables if any exist (soft block).

---

## Phase 4: Database Migration

```bash
cd backend
alembic revision --autogenerate -m "Add StoryStateVariable model"
alembic upgrade head
```

---

## Phase 5: Frontend - API Client

```bash
cd frontend
npm run generate-client
```

This generates types and service methods for the new endpoints.

---

## Phase 6: Frontend Components

### 6.1 New Hook: `useStateSchema.ts`
Location: `frontend/src/hooks/stories/useStateSchema.ts`

```typescript
export const useStateSchema = (storyId: string, version: number) => {
  return useQuery({
    queryKey: ["stories", storyId, "state-schema", version],
    queryFn: () => StoriesService.readStoryStateSchema({ storyId, version }),
  })
}

export const useCreateStateVariable = (storyId: string, version: number) => { ... }
export const useUpdateStateVariable = (storyId: string, version: number) => { ... }
export const useDeleteStateVariable = (storyId: string, version: number) => { ... }
```

### 6.2 StateSchemaEditor Component
Location: `frontend/src/components/Stories/StoryEditor/StateSchema/StateSchemaEditor.tsx`

- Table listing all variables (key, type, default, category, description)
- Add/Edit/Delete with modals
- Group by category with collapsible sections
- Show usage count per variable

### 6.3 Enhanced StateConditionEditor
Modify: `frontend/src/components/Stories/shared/StateConditionEditor.tsx`

Add optional `schema` prop:
- Key field becomes autocomplete from schema keys
- Type auto-selects based on variable definition
- Enum variables show dropdown of allowed values
- Warning badge for undefined variables

### 6.4 Validation Integration
Modify: `frontend/src/components/Stories/shared/storyValidation.ts`

Add `validateStateSchema()` function that checks all choices for undefined variables.

Modify: `frontend/src/hooks/stories/usePublishWorkflow.ts`

Merge schema validation into publish validation result.

---

## Implementation Order

| Step | Task | Files |
|------|------|-------|
| 1 | Add models + enum | `models.py` |
| 2 | Add relationships | `models.py` (end) |
| 3 | Create migration | `alembic/versions/` |
| 4 | Add CRUD functions | `crud.py` |
| 5 | Add API routes | `api/routes/stories.py` |
| 6 | Modify version copy | `api/routes/stories.py` |
| 7 | Add publish validation | `api/routes/stories.py` |
| 8 | Generate client | `npm run generate-client` |
| 9 | Create useStateSchema hook | `hooks/stories/useStateSchema.ts` |
| 10 | Create StateSchemaEditor | `components/Stories/StoryEditor/StateSchema/` |
| 11 | Enhance StateConditionEditor | `components/Stories/shared/StateConditionEditor.tsx` |
| 12 | Update validation | `storyValidation.ts`, `usePublishWorkflow.ts` |

---

## Verification

1. **Backend API Testing:**
   - Start backend: `fastapi dev app/main.py`
   - Open Swagger UI: http://localhost:8000/docs
   - Test CRUD operations on state-schema endpoints
   - Test validation endpoint returns undefined variables

2. **Frontend Testing:**
   - Create a story with state variables
   - Add choices with requires_state/sets_state
   - Verify autocomplete shows defined variables
   - Verify undefined variables show warnings
   - Try to publish with undefined variables → should show soft block

3. **Integration Testing:**
   - Create story → add schema → add nodes/choices using schema → publish
   - Create new version → verify schema copied
   - Edit schema in new version → verify published version unchanged
