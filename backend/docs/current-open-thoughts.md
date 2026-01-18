# User Model Registration - Implementation Plan

## Design Decisions (Finalized)

| Decision | Choice | Notes |
|----------|--------|-------|
| Ownership model | Per-user (V1) | Will change in V1.2 |
| Data structure | Reuse `LLMModel` with `is_system=False` + `created_by_user_id` | No new table |
| Provider binding | FK required (V1) | `provider_id` required; type-only binding deferred |
| Visibility | Private only (V1) | Future: cloning via typer commands |
| Pydantic models | Reuse `LLMModelCreate` | No separate `UserLLMModelCreate` |
| Custom indicator | Use `is_system=False` | Exposed in `LLMModelPublic` |
| Unique constraint | `(provider_id, model_id, created_by_user_id)` | Allows same model_id per user |
| Display name | Auto-generate on backend (simple) | From `model_id` if not provided |
| Shadowing | Allowed | Users can create models with same `model_id` as system |
| Provider-less models | Deferred | Solve after initial implementation |

---

## Phase 1: Backend - Model Registration

### 1.1 Model Changes

#### ✅ DONE: `LLMModel` updates
- `created_by_user_id: uuid.UUID | None` - FK to user
- `is_system: bool` - indexed, distinguishes catalog vs user models
- `provider_id` - now `nullable=True`
- UniqueConstraint updated to `("provider_id", "model_id", "created_by_user_id")`

#### ✅ DONE: `LLMModelPublic` updates
- Now exposes `is_system: bool`

#### Deferred: `provider_type` on `LLMModel`
Provider-type-only binding (no FK) deferred to future version.
For V1, `provider_id` is required when creating custom models.

#### ✅ DONE: `LLMProvider` updates
- `created_by_user_id: uuid.UUID | None` - for future user-created providers

---

### 1.2 CRUD Functions

**Location:** `crud.py` (stubs exist at lines 3007-3011, need implementation)

```python
def _generate_display_name(model_id: str) -> str:
    """Simple display name from model_id: 'llama3:70b' -> 'Llama3 70b'"""
    # Replace common separators with spaces, then title case
    name = model_id.replace(":", " ").replace("-", " ").replace("_", " ")
    return name.title()


def create_user_model(
    *,
    session: Session,
    user_id: uuid.UUID,
    model_in: LLMModelCreate,  # Reusing existing model
) -> LLMModel:
    """Create a user-owned custom model."""
    data = model_in.model_dump(exclude={"provider_id"})

    # Auto-generate display_name if not provided
    if not data.get("display_name"):
        data["display_name"] = _generate_display_name(model_in.model_id)

    model = LLMModel(
        **data,
        provider_id=model_in.provider_id,
        created_by_user_id=user_id,
        is_system=False,
    )
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


def get_user_models(
    *,
    session: Session,
    user_id: uuid.UUID,
    provider_type: LLMProviderType | None = None,
) -> list[LLMModel]:
    """Get all custom models for a user."""
    filters = [
        LLMModel.created_by_user_id == user_id,
        LLMModel.is_deleted == False,
    ]
    if provider_type:
        filters.append(LLMModel.provider_type == provider_type)

    stmt = select(LLMModel).where(*filters).order_by(LLMModel.display_name)
    return list(session.exec(stmt).all())


def delete_user_model(
    *,
    session: Session,
    user_id: uuid.UUID,
    model_id: uuid.UUID,
) -> bool:
    """Soft-delete a user's custom model. Returns True if deleted."""
    model = session.get(LLMModel, model_id)
    if not model or model.created_by_user_id != user_id:
        return False

    model.is_deleted = True
    model.deleted_at = datetime.now()
    session.add(model)
    session.commit()
    return True
```

**Deferred:** Delete endpoint - soft-delete implemented but route not exposed in V1.

---

### 1.3 API Routes

**Location:** `llm_catalog.py`

```python
# New authenticated routes for custom models
POST   /llm-catalog/models/custom     # Create custom model (requires auth)
GET    /llm-catalog/models/custom     # List user's custom models (requires auth)
# DELETE deferred to V1.1

# Existing routes - update to include user's models when authenticated
GET    /llm-catalog/models            # System + user's custom (if auth provided)
GET    /llm-catalog/models/grouped    # System + user's custom (if auth provided)
```

**Route implementations:**
```python
from app.api.deps import CurrentUser, OptionalUser

@router.post("/models/custom", response_model=LLMModelPublic)
def create_custom_model(
    session: SessionDep,
    current_user: CurrentUser,
    model_in: LLMModelCreate,
) -> Any:
    """Create a custom model for the current user."""
    model = crud.create_user_model(
        session=session,
        user_id=current_user.id,
        model_in=model_in,
    )
    return LLMModelPublic(**model.model_dump())


@router.get("/models/custom", response_model=LLMModelsPublic)
def list_custom_models(
    session: SessionDep,
    current_user: CurrentUser,
    provider_type: LLMProviderType | None = None,
) -> Any:
    """List current user's custom models."""
    models = crud.get_user_models(
        session=session,
        user_id=current_user.id,
        provider_type=provider_type,
    )
    return LLMModelsPublic(
        data=[LLMModelPublic(**m.model_dump()) for m in models],
        count=len(models),
    )
```

---

### 1.4 Pydantic Model Updates

#### Update `LLMModelCreate` for user models
```python
class LLMModelCreate(LLMModelBase):
    """Input model for creating a model catalog entry."""
    provider_id: uuid.UUID  # Required for now (provider-less deferred)
    display_name: str | None = None  # Optional - auto-generated if missing
```

**Note:** Override `display_name` from `LLMModelBase` to make it optional.
CRUD layer auto-generates from `model_id` if not provided (`llama3:70b` -> `Llama3 70b`).

---

### 1.5 Migration

**Check current DB state first** - some changes may already be applied:
- [ ] `is_system` column on `llmmodel` with index
- [ ] `provider_id` nullable
- [ ] `created_by_user_id` column
- [ ] Unique constraint `(provider_id, model_id, created_by_user_id)`
- [ ] Composite index on `(created_by_user_id, is_deleted)` for efficient user queries

---

## Phase 2: Merge User Models into Catalog Queries

### Update `get_llm_models` in crud.py

Add optional `user_id` parameter to include user's custom models:

```python
def get_llm_models(
    *,
    session: Session,
    user_id: uuid.UUID | None = None,  # NEW - include user's models
    skip: int = 0,
    limit: int = 100,
    # ... existing filters ...
) -> tuple[list[tuple[LLMModel, LLMProvider]], int]:
    """
    Get models from catalog.
    If user_id provided, includes user's custom models alongside system models.
    """
    # Base filter: system models OR user's models
    ownership_filter = LLMModel.is_system == True
    if user_id:
        ownership_filter = or_(
            LLMModel.is_system == True,
            LLMModel.created_by_user_id == user_id
        )

    filters = [ownership_filter, LLMModel.is_deleted == False]
    # ... rest of existing filters ...
```

### Update routes to use optional auth

```python
from app.api.deps import OptionalUser  # Need to create this dependency

@router.get("/models", response_model=LLMModelsPublic)
def list_models(
    session: SessionDep,
    current_user: OptionalUser,  # Changed from no auth
    # ... existing params ...
) -> Any:
    """List models. If authenticated, includes user's custom models."""
    results, count = crud.get_llm_models(
        session=session,
        user_id=current_user.id if current_user else None,
        # ... rest ...
    )
```

**Note:** Need to create `OptionalUser` dependency that returns `User | None` without requiring auth.

---

## Checklist

### Phase 1 - Model Registration
- [x] `LLMModel.created_by_user_id` field
- [x] `LLMModel.is_system` field with index
- [x] `LLMModel.provider_id` nullable (in schema, but still required in API for V1)
- [x] UniqueConstraint includes `created_by_user_id`
- [x] `LLMModelPublic` exposes `is_system`
- [x] Make `LLMModelCreate.display_name` optional (override from base)
- [x] Implement `create_user_model` CRUD (with auto-generate display_name)
- [x] Implement `get_user_models` CRUD
- [x] Implement `delete_user_model` CRUD (soft-delete)
- [ ] Create migration (if schema changes needed) - verify DB state first
- [x] Add POST `/models/custom` route
- [x] Add GET `/models/custom` route

### Phase 2 - Merge into Catalog
- [x] Create `OptionalUser` dependency
- [x] Update `get_llm_models` CRUD with `user_id` param
- [x] Update `get_llm_models_grouped` CRUD with `user_id` param
- [x] Update GET `/models` route with optional auth
- [x] Update GET `/models/grouped` route with optional auth

---

## Resolved Questions

| Question | Decision |
|----------|----------|
| Auto-generate display_name? | Yes, simple backend logic: `llama3:70b` -> `Llama3 70b` |
| Provider-less models (no `provider_id`)? | Deferred - require `provider_id` for now |
| Allow shadowing system models? | Yes, users can create models with same `model_id` |
