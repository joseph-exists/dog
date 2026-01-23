# Traits, Qualities & Archetypes — Frontend Integration Design

> Design for connecting the backend trait/quality/archetype system to the persona frontend.

---

## Current State

### Backend (exists)

| Entity | API | Persona Association |
|--------|-----|---------------------|
| **Trait** | Full CRUD at `/traits/` | Via `PersonaTraitLink` (inherited from archetypes only) |
| **Quality** | Full CRUD at `/qualities/` | Via `PersonaQualityLink` with state management |
| **Archetype** | Full CRUD at `/archetypes/` | Template for persona creation |
| **QualityTraitLink** | CRUD at `/quality-trait-links/` | Defines auto-enable rules |
| **TraitConflicts** | Full CRUD at `/trait-conflicts/` | Validates trait compatibility |

### Frontend (exists)

- `TraitsBlock` — Static display of `TraitItem[]` from page content (no API integration)
- `DomainsBlock` — Static display of domain strings
- `PersonasService.createPersonaFromArchetype()` — Available but unused in UI

### Gap

- No `GET /personas/{id}/traits/` endpoint (traits are written via archetype but never read via REST)
- `TraitsBlock` uses static page content, not live API data
- No qualities display anywhere on persona pages
- No archetype selection in persona creation flow

---

## Design: Three Phases

### Phase 1: Live Data Display (Current Sprint)

**Goal:** Show real traits and qualities on persona detail pages.

#### Backend Change

Add `GET /api/v1/personas/{persona_id}/traits/` endpoint:
- Reads `PersonaTraitLink` for the persona
- Returns `list[TraitPublic]` (same pattern as persona-qualities)
- Read-only (traits come from archetypes)

#### Frontend Changes

1. **Make TraitsBlock API-aware:**
   - Accept optional `entityId` + `entityType` in block config
   - When present, fetch traits from `GET /personas/{id}/traits/`
   - Fall back to static `content.items` if no entity context

2. **Create QualitiesBlock:**
   - New block type showing enabled qualities for a persona
   - Fetch from `GET /personas/{id}/qualities/`
   - Display as purple badges (distinct from pink traits)
   - Add to persona page template

3. **Wire into persona detail page:**
   - Pass `personaId` as entity context to TraitsBlock and QualitiesBlock
   - Blocks auto-fetch when persona ID is available

### Phase 2: Archetype Creation Path

**Goal:** Let users create personas from archetypes (inheriting traits + qualities).

#### Frontend Changes

1. **Add archetype picker to CreatePersonaDialog:**
   - Optional "Start from archetype" selection
   - Fetch archetypes from `GET /archetypes/`
   - When selected, show preview of inherited traits/qualities
   - Submit via `PersonasService.createPersonaFromArchetype()`

2. **Show archetype lineage on persona detail:**
   - If persona was created from archetype, show badge/link
   - Indicate which traits are inherited vs manually added

### Phase 3: Direct Management (Future)

**Goal:** Allow adding/removing traits and qualities directly.

- Add persona-traits write endpoints to backend
- Quality state management UI (enable/disable/remove)
- Trait conflict resolution warnings
- Trait picker with conflict checking

---

## Phase 1 Implementation Details

### Backend: `persona_traits.py` route

```python
@router.get("/{persona_id}/traits/", response_model=list[TraitPublic])
def read_persona_traits(
    persona_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    persona = session.get(Persona, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    stmt = (
        select(Trait)
        .join(PersonaTraitLink, PersonaTraitLink.trait_id == Trait.id)
        .where(PersonaTraitLink.persona_id == persona_id)
    )
    return session.exec(stmt).all()
```

### Frontend: Updated TraitsBlock

The block checks for `config.entityId`:
- If present: uses `useQuery` to fetch from `/personas/{id}/traits/`
- If absent: uses static `content.items` (backwards compatible)

### Frontend: New QualitiesBlock

```typescript
interface QualitiesBlockConfig {
  entityId?: string
  layout?: "badges" | "list"
}

// Fetches from GET /personas/{entityId}/qualities/
// Displays enabled qualities as purple badges
```

### Block Registry Updates

Add to `blockTypes.ts`:
```typescript
{ id: "qualities", label: "Qualities", icon: Gem, ... }
```

Add to persona template in `pageTemplates.ts`:
```typescript
{ type: "qualities", column: "primary", order: 5, ... }
```

---

## File Changes Summary (Phase 1)

| File | Change |
|------|--------|
| `backend/app/api/routes/persona_traits.py` | NEW — Read endpoint |
| `backend/app/api/main.py` | Register persona_traits router |
| `frontend/src/client/` | Regenerate after backend change |
| `frontend/src/components/Page/blocks/TraitsBlock.tsx` | Add API fetching |
| `frontend/src/components/Page/blocks/QualitiesBlock.tsx` | NEW |
| `frontend/src/components/Page/blocks/index.ts` | Export QualitiesBlock |
| `frontend/src/components/Page/registry/blockTypes.ts` | Add "qualities" |
| `frontend/src/components/Page/registry/pageTemplates.ts` | Add qualities to persona template |
| `frontend/src/components/Page/PageShell.tsx` | Add qualities case |
