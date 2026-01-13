## Phase 2: CRUD Operations

### File: `backend/app/crud.py`

Add after story requirement functions:

[x] - `get_story_state_variables(session, story_id, story_version, skip, limit)` → tuple[list, int]
[x] - `create_story_state_variable(session, variable_in)` → StoryStateVariable
[x] - `update_story_state_variable(session, variable_id, variable_in)` → StoryStateVariable
[x] - `delete_story_state_variable(session, variable_id)` → None
[x] - `get_undefined_variables_in_choices(session, story_id, story_version)` → StateSchemaValidationResult

Key validation logic in `get_undefined_variables_in_choices`:
[x] 1. Get all defined variable keys from schema
[x] 2. Get all choices for nodes in this story version
[x] 3. Extract keys from `requires_state` and `sets_state`
[x] 4. Report any keys not in schema as errors

---

## Implementation Details

### Location
All functions added to `backend/app/crud.py` starting at line 696, after the `check_story_requirements` function.

### Imports Added
Added to the model imports (lines 56-61):
- `StoryStateVariable`
- `StoryStateVariableCreate`
- `StoryStateVariableUpdate`
- `StateSchemaValidationError`
- `StateSchemaValidationResult`
- `StateValueType`

### Function Signatures

```python
def get_story_state_variables(
    *, session: Session, story_id: uuid.UUID, story_version: int,
    skip: int = 0, limit: int = 100
) -> tuple[list[StoryStateVariable], int]

def create_story_state_variable(
    *, session: Session, variable_in: StoryStateVariableCreate
) -> StoryStateVariable

def update_story_state_variable(
    *, session: Session, variable_id: uuid.UUID, variable_in: StoryStateVariableUpdate
) -> StoryStateVariable

def delete_story_state_variable(
    *, session: Session, variable_id: uuid.UUID
) -> None

def get_undefined_variables_in_choices(
    *, session: Session, story_id: uuid.UUID, story_version: int
) -> StateSchemaValidationResult
```

---

## Deviations from Plan

### None - Implementation matches plan exactly

The implementation follows the original plan with no significant deviations:

1. **Function signatures**: Match the planned signatures exactly
2. **Return types**: All return types match plan
3. **Validation logic**: The `get_undefined_variables_in_choices` function implements all 4 validation steps as specified
4. **Error handling**: Functions raise `ValueError` for not-found cases (consistent with existing CRUD patterns)

---

## Additional Implementation Notes

### Enum Validation
The `create_story_state_variable` function includes validation that `enum_values` must be provided when `value_type` is `ENUM`. This prevents creation of invalid enum variables.

### Empty Node Handling
The `get_undefined_variables_in_choices` function handles the case where a story version has no nodes by returning an early success result with empty used/undefined variable lists.

### Timestamp Updates
The `update_story_state_variable` function automatically updates the `updated_at` timestamp when a variable is modified.

---

## Verification

To verify the implementation:

1. Start the backend: `fastapi dev app/main.py`
2. Check for import errors on startup
3. Run type checking: `mypy app/crud.py`
4. Run linter: `ruff check app/crud.py`

Phase 2 implementation complete.
