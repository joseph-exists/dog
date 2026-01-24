# Archetypes & Archetype Pages Design

**Date:** 2026-01-24

## Overview

Create a full archetype management UI with listing page, detail pages (block-based), and entity-type-aware blocks for traits/qualities. Archetypes are "character templates" that define trait and quality sets inherited by personas.

## Architecture: Service Resolver Pattern

Blocks become entity-type-generic. Instead of hardcoding `PersonaTraitsService` inside blocks, a service resolver layer dispatches to the correct API based on `entityType`:

```
TraitsBlock / QualitiesBlock
    accepts (entityType?, entityId?)
        ↓
useEntityTraits(entityType, entityId) / useEntityQualities(entityType, entityId)
        ↓ resolves via registry map
EntityServiceRegistry: { persona → PersonaTraitsService, archetype → ArchetypeTraitsService }
        ↓ returns data
Block renders traits/qualities (or falls back to static content.items)
```

## Backend: New Sub-Resource Endpoints

### `backend/app/api/routes/archetype_traits.py`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/archetypes/{archetype_id}/traits/` | List traits for archetype |
| POST | `/archetypes/{archetype_id}/traits/{trait_id}` | Add trait to archetype |
| DELETE | `/archetypes/{archetype_id}/traits/{trait_id}` | Remove trait from archetype |

### `backend/app/api/routes/archetype_qualities.py`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/archetypes/{archetype_id}/qualities/` | List qualities for archetype |
| POST | `/archetypes/{archetype_id}/qualities/{quality_id}` | Add quality to archetype |
| DELETE | `/archetypes/{archetype_id}/qualities/{quality_id}` | Remove quality from archetype |

Uses `ArchetypeTraitLink` and `ArchetypeQualityLink` join tables.

## Frontend Client Additions

Manual additions to `sdk.gen.ts` and `types.gen.ts`:

- `ArchetypeTraitsService` — `readArchetypeTraits`, `addTraitToArchetype`, `removeTraitFromArchetype`
- `ArchetypeQualitiesService` — `readArchetypeQualities`, `addQualityToArchetype`, `removeQualityFromArchetype`

## Frontend: Service Resolver Hooks

### `hooks/useEntityTraits.ts`

- Maps `entityType` → fetch function
- Returns `useQuery` result
- Falls back to disabled query if entityType/entityId not provided

### `hooks/useEntityQualities.ts`

- Same pattern for qualities

## Frontend: Block Updates

### TraitsBlock & QualitiesBlock

- Replace direct `PersonaTraitsService`/`PersonaQualitiesService` calls with resolver hooks
- Props change: add `entityType?: string` alongside existing `entityId?: string`
- Fallback unchanged: if hook returns empty, use static `content.items`

### PageShell

- Pass `entityType` prop down to blocks alongside `entityId`

## Frontend: Editor Form Updates

### QualitiesForm

- Accepts `entityType` + `entityId`
- Resolves add/remove API from a map (no hardcoded service references)
- Works for both personas and archetypes

### TraitsForm

- Accepts `entityType` + `entityId`
- `entityType === "archetype"` → editable toggle UI (archetypes own traits)
- `entityType === "persona"` → read-only with inheritance note
- Uses resolver for add/remove when editable

## Frontend: Pages & Components

### Listing Page: `routes/_layout/archetypes.tsx`

- Card grid layout (matches personas listing)
- Each card: name, description, trait count badge, quality count badge
- "Create Archetype" button → CreateArchetypeDialog
- Cards link to `/archetype/$archetypeId`

### Detail Page: `routes/_layout/archetype.$archetypeId.tsx`

- Auto-create pattern: fetch archetype → hydrate identity/bio → PageShell
- Uses `entityType="archetype"` so blocks dispatch to archetype APIs
- Same `useEffect` + `useRef` guard as persona page

### CreateArchetypeDialog

- Fields: name (required), description (optional)
- Calls `ArchetypesService.createArchetype()`
- On success, navigates to new archetype detail page

### Page Template: `"archetype"`

| Block | Column | Order | Notes |
|-------|--------|-------|-------|
| identity | primary | 1 | Name + description |
| bio | primary | 2 | Longer description |
| traits | primary | 3 | Editable for archetypes |
| qualities | primary | 4 | Editable for archetypes |
| relationships | auxiliary | 1 | Personas from this archetype |

### Sidebar

- Add "Archetypes" entry to AppSidebar (near "Personas")

## Implementation Order

1. Backend endpoints (archetype_traits + archetype_qualities routes)
2. Frontend client (ArchetypeTraitsService + ArchetypeQualitiesService)
3. Service resolver hooks (useEntityTraits, useEntityQualities)
4. Block updates (TraitsBlock + QualitiesBlock use hooks, accept entityType)
5. PageShell update (pass entityType to blocks and editor forms)
6. Editor form updates (QualitiesForm + TraitsForm entity-type-aware)
7. Page template (add "archetype" to registry)
8. Archetype listing page (/archetypes + CreateArchetypeDialog)
9. Archetype detail page (/archetype/$archetypeId with auto-create + hydrate)
10. Sidebar link (add to AppSidebar)

## Key Design Decisions

- **No hardcoded services in blocks** — resolver pattern keeps blocks generic
- **Editable traits for archetypes** — archetypes are the source of truth for traits
- **Auto-create + hydrate on load** — same pattern as persona pages
- **Block-based pages** — reuses PageShell, gets edit mode and block palette for free
- **Fallback to static content** — blocks work with or without entity context
