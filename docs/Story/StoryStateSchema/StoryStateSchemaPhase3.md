## Phase 3: API Routes

### File: `backend/app/api/routes/stories.py`

Add nested endpoints:

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| GET | `/{story_id}/versions/{version}/state-schema` | List variables | [x] Complete |
| POST | `/{story_id}/versions/{version}/state-schema` | Create variable | [x] Complete |
| PUT | `/{story_id}/versions/{version}/state-schema/{id}` | Update variable | [x] Complete |
| DELETE | `/{story_id}/versions/{version}/state-schema/{id}` | Delete variable | [x] Complete |
| GET | `/{story_id}/versions/{version}/state-schema/validate` | Check for undefined vars | [x] Complete |

**Authorization:**
- [x] Read: Any authenticated user
- [x] Write: Story owner or superuser only
- [x] Block edits to published_version

**Modify `create_new_story_version`:** [x] Complete - Copy state variables when creating new version from published.

**Modify `publish_story`:** [x] Complete - Call validation, return 422 with undefined variables if any exist (soft block).

---

## Implementation Details

### Imports Added (lines 47, 58-63, 67)
```python
StateSchemaValidationResult,
StoryStateVariable,
StoryStateVariableBase,
StoryStateVariableCreate,
StoryStateVariablePublic,
StoryStateVariablesPublic,
StoryStateVariableUpdate,
```
Also added: `from app import crud`

### Route Locations

| Route | Function | Line |
|-------|----------|------|
| GET state-schema | `read_story_state_schema` | 527 |
| POST state-schema | `create_story_state_variable` | 561 |
| PUT state-schema/{id} | `update_story_state_variable` | 620 |
| DELETE state-schema/{id} | `delete_story_state_variable` | 684 |
| GET state-schema/validate | `validate_story_state_schema` | 731 |

### Modified Functions

| Function | Line | Changes |
|----------|------|---------|
| `publish_story` | 200 | Added state schema validation with force parameter |
| `create_new_story_version` | 264 | Added state variable copying after choice copying |

---

## Deviations from Plan

### 1. Added `force` Parameter to `publish_story`

**Plan:** Return 422 with undefined variables if any exist (soft block).

**Implementation:** Added optional `force: bool = False` query parameter to allow overriding validation.

**Rationale:** The plan mentioned "can_override" in the error response, suggesting override capability. Adding a `force` parameter provides a cleaner API than requiring a separate endpoint or complex error handling. This allows:
- Default behavior: Soft block with 422 error
- Override: Pass `force=true` to bypass validation

**Validation:** This is an enhancement, not a breaking change. The default behavior matches the plan.

### 2. Duplicate Key Check on Update

**Plan:** Not explicitly specified.

**Implementation:** Added duplicate key check when updating a variable's key to prevent conflicts.

**Rationale:** Consistent with create endpoint behavior. Prevents data integrity issues.

---

## Route Details

### GET `/{story_id}/versions/{version}/state-schema`
- Returns: `StoryStateVariablesPublic` (list + count)
- Auth: Any authenticated user
- Pagination: `skip`, `limit` parameters

### POST `/{story_id}/versions/{version}/state-schema`
- Body: `StoryStateVariableBase`
- Returns: `StoryStateVariablePublic`
- Auth: Owner or superuser
- Validates: Story exists, ownership, not published version, no duplicate keys
- Enum validation: Requires `enum_values` when `value_type` is ENUM

### PUT `/{story_id}/versions/{version}/state-schema/{variable_id}`
- Body: `StoryStateVariableUpdate`
- Returns: `StoryStateVariablePublic`
- Auth: Owner or superuser
- Validates: Variable belongs to story/version, no duplicate keys on rename

### DELETE `/{story_id}/versions/{version}/state-schema/{variable_id}`
- Returns: `Message`
- Auth: Owner or superuser
- Validates: Variable belongs to story/version

### GET `/{story_id}/versions/{version}/state-schema/validate`
- Returns: `StateSchemaValidationResult`
- Auth: Owner or superuser
- Returns all undefined variables used in choices

---

## Modified `publish_story` Details

```python
@router.put("/{id}/publish", response_model=StoryPublic)
def publish_story(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    force: bool = False,  # NEW: Override validation
) -> Any:
```

**Validation Flow:**
1. Check story exists and ownership
2. If `force=False`, run `crud.get_undefined_variables_in_choices()`
3. If validation fails, return 422 with:
   - `message`: "Story has undefined state variables"
   - `undefined_variables`: List of undefined variable keys
   - `error_count`: Number of validation errors
   - `hint`: Instructions for resolution
4. If `force=True` or validation passes, proceed with publish

---

## Modified `create_new_story_version` Details

Added after choice copying (line 334):

```python
# Copy all state variables from published_version to new current_version
state_vars_statement = select(StoryStateVariable).where(
    StoryStateVariable.story_id == id,
    StoryStateVariable.story_version == story.published_version,
)
published_vars = session.exec(state_vars_statement).all()

for var in published_vars:
    new_var = StoryStateVariable.model_validate(
        var,
        update={
            "id": uuid.uuid4(),
            "story_version": new_version,
        },
    )
    session.add(new_var)
```

---

## Verification

1. **Syntax Check:**
   ```bash
   cd backend
   python -c "from app.api.routes import stories; print('Import OK')"
   ```

2. **API Testing:**
   - Start backend: `fastapi dev app/main.py`
   - Open Swagger UI: http://localhost:8000/docs
   - Test all 5 state-schema endpoints
   - Test publish with undefined variables (expect 422)
   - Test publish with `force=true` (expect success)
   - Test new version creation (verify variables copied)

3. **Type Checking:**
   ```bash
   mypy app/api/routes/stories.py
   ```

---

Phase 3 implementation complete.
