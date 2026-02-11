# Persona Pages — Reference Card

> Quick reference for engineers working with the Persona listing and detail pages, and for users interacting with the system.

---

## Architecture at a Glance

```
/personas (listing)
├── PersonasPage (header + search + create button)
│   ├── CreatePersonaDialog (form: name, description, domains)
│   └── PersonasListContent
│       ├── "My Library" section → LibraryPersonaCard (with remove)
│       └── "All Personas" section → PersonaCard (clickthrough)

/persona/$personaId (detail)
└── PageShell (block-based editor, reused from user pages)
    ├── BlockPalette (sidebar, edit mode)
    ├── PageHeader (breadcrumbs, save, edit toggle)
    ├── PageLayout (resizable two-column)
    │   ├── Primary: IdentityBlock, BioBlock, DomainsBlock, TraitsBlock
    │   └── Auxiliary: RelationshipsBlock
    └── BlockEditorSheet (content editing)
```

**Layout:** Detail page is full-bleed (`_layout.tsx` → `fullBleedRoutes`). Listing page is standard (max-width, padded).

---

## File Map

| Layer | Path | Purpose |
|-------|------|---------|
| Listing Route | `src/routes/_layout/personas.tsx` | Library + catalog listing with search |
| Detail Route | `src/routes/_layout/persona.$personaId.tsx` | Block-based detail page |
| Create Dialog | `src/components/Persona/CreatePersonaDialog.tsx` | Form with archetype picker |
| Detail Dialog | `src/components/Persona/PersonaDetailDialog.tsx` | Inline view/edit dialog |
| Entity Type | `src/components/Page/registry/entityTypes.ts` | "persona" entry (pink, Smile icon) |
| Page Template | `src/components/Page/registry/pageTemplates.ts` | "persona" default blocks |
| Block Types | `src/components/Page/registry/blockTypes.ts` | "domains", "traits", "qualities" entries |
| DomainsBlock | `src/components/Page/blocks/DomainsBlock.tsx` | Domain expertise display |
| TraitsBlock | `src/components/Page/blocks/TraitsBlock.tsx` | API-connected trait badges |
| QualitiesBlock | `src/components/Page/blocks/QualitiesBlock.tsx` | API-connected quality badges |
| PageShell | `src/components/Page/PageShell.tsx` | Block renderer (domains/traits/qualities cases) |
| Blocks Index | `src/components/Page/blocks/index.ts` | Exports all block components |
| Backend Route | `backend/app/api/routes/persona_traits.py` | GET /personas/{id}/traits/ endpoint |
| Layout Config | `src/routes/_layout.tsx` | Route titles + fullBleedRoutes |
| Route Tree | `src/routeTree.gen.ts` | Auto-generated (TanStack Router plugin) |

---

## Data Sources

### Persona API (`PersonasService`)

| Method | Endpoint | Returns |
|--------|----------|---------|
| `readPersonas({ limit })` | `GET /api/v1/personas/` | `PersonasPublic { data, count }` |
| `createPersona({ requestBody })` | `POST /api/v1/personas/` | `PersonaPublic` |
| `readPersona({ id })` | `GET /api/v1/personas/{id}` | `Persona` |
| `updatePersona({ id, requestBody })` | `PUT /api/v1/personas/{id}` | `PersonaPublic` |
| `deletePersona({ id })` | `DELETE /api/v1/personas/{id}` | `Message` |
| `createPersonaFromArchetype(...)` | `POST /api/v1/personas/from-archetype/{id}` | `PersonaPublic` |

### PersonaPublic Shape

```typescript
{
  id: string
  name: string
  description?: string | null
  long_description?: string | null
  general_domain?: string | null
  specific_domain?: string | null
  general_domain_high?: string | null
  specific_domain_high?: string | null
  created_at: string
}
```

### Library API (`UserPersonasService` / `PersonaLibraryService`)

The listing page uses `PersonaLibraryService.getLibrary(owner)` which joins junction entries (UserPersonaPublic) with full PersonaPublic data. Returns `LibraryPersona[]`.

### Traits & Qualities APIs

| Service | Method | Endpoint | Returns |
|---------|--------|----------|---------|
| `PersonaTraitsService` | `readPersonaTraits({ personaId })` | `GET /personas/{id}/traits/` | `TraitPublic[]` |
| `PersonaQualitiesService` | `readPersonaQualities({ personaId })` | `GET /personas/{id}/qualities/` | `QualityPublic[]` |
| `ArchetypesService` | `readArchetypes({ limit })` | `GET /archetypes/` | `ArchetypesPublic` |

### Archetype Inheritance

When a persona is created via `createPersonaFromArchetype`:
- All archetype traits are copied with `is_inherited=true`
- Trait-dependent qualities are auto-enabled
- Source archetype ID is tracked in `PersonaTraitLink.source_archetype_id`

---

## Query Keys

| Key | Used By | Purpose |
|-----|---------|---------|
| `["personas", "all"]` | Listing page | All personas (catalog) |
| `["persona-library", userId]` | Listing page | User's library entries |
| `["pages", "persona", personaId]` | Detail page (via `usePageEditor`) | Block-based page data |
| `["persona-traits", personaId]` | TraitsBlock | Live trait data for persona |
| `["persona-qualities", personaId]` | QualitiesBlock | Live quality data for persona |
| `["archetypes"]` | CreatePersonaDialog | Available archetypes for creation |

---

## New Block Types

### DomainsBlock

Displays domain expertise areas with color-coded hierarchy.

| Prop | Type | Description |
|------|------|-------------|
| `config.showHierarchy` | `boolean` | Show high-level vs specific grouping (default: true) |
| `content.generalDomain` | `string?` | General domain label |
| `content.specificDomain` | `string?` | Specific domain label |
| `content.generalDomainHigh` | `string?` | High-level general domain |
| `content.specificDomainHigh` | `string?` | High-level specific domain |

**Badge variants:** High = amber, General = blue, Specific = emerald.

### TraitsBlock

Displays personality traits as badges or list items. **API-connected:** when `entityId` is provided, fetches real trait data from `GET /personas/{id}/traits/`.

| Prop | Type | Description |
|------|------|-------------|
| `config.layout` | `"badges" \| "list"` | Visual layout (default: "badges") |
| `config.maxVisible` | `number` | Max items shown (default: 12) |
| `content.items` | `TraitItem[]` | Static fallback: `{ id, label, category? }` |
| `entityId` | `string?` | When provided, fetches traits from API |

**Color:** Pink badges. **Data priority:** API data > static content.

### QualitiesBlock

Displays enabled persona qualities as badges or list items. **API-connected:** fetches from `GET /personas/{id}/qualities/`.

| Prop | Type | Description |
|------|------|-------------|
| `config.layout` | `"badges" \| "list"` | Visual layout (default: "badges") |
| `config.maxVisible` | `number` | Max items shown (default: 12) |
| `content.items` | `QualityItem[]` | Static fallback: `{ id, label, description? }` |
| `entityId` | `string?` | When provided, fetches qualities from API |

**Color:** Purple badges (distinct from pink traits).

---

## Persona Page Template

Default blocks for new persona pages (defined in `pageTemplates.ts`):

| Order | Column | Block | Purpose |
|-------|--------|-------|---------|
| 1 | primary | Identity | Name + tagline |
| 2 | primary | Bio | Description / long description |
| 3 | primary | Domains | Domain expertise display |
| 4 | primary | Traits | Personality traits (API-fetched) |
| 5 | primary | Qualities | Enabled qualities (API-fetched) |
| 1 | auxiliary | Relationships | Linked entities |

---

## Engineering: Common Tasks

### Add a new field to PersonaCreate dialog

Edit `src/components/Persona/CreatePersonaDialog.tsx`:
1. Add state variable
2. Add form field in the dialog body
3. Include in `payload` object passed to `mutation.mutate()`

### Change default template blocks

Edit `src/components/Page/registry/pageTemplates.ts` → find the "persona" template and modify `defaultBlocks` array.

### Add a new block type for personas

Follow the pattern in [user-pages-reference.md](./user-pages-reference.md#adding-a-new-block-type):
1. Add to `BlockType` union in `blockTypes.ts`
2. Create component in `blocks/`
3. Export from `blocks/index.ts`
4. Add case in `PageShell.tsx` → `renderBlock()`
5. Optionally add to persona template

### Change ownership / edit permissions

Edit `src/routes/_layout/persona.$personaId.tsx`:
```tsx
// Currently: any authenticated user can edit
const isOwner = !!user

// To restrict to creator:
// const isOwner = user?.id === persona.created_by
```

---

## User Guide: Personas

### What is a Persona?

A persona represents a character profile with identity, expertise domains, and personality traits. Personas can be added to your personal library and assigned to agents or used in rooms as a userPersona.

### Browsing Personas (`/personas`)

The listing page has two sections:

1. **My Library** — Personas you've added to your collection. You can remove entries with the trash icon.
2. **All Personas** — The full catalog of available personas (excludes ones already in your library).

Use the **search bar** to filter by name, description, or domain.

### Creating a Persona

Click **Create Persona** to open the creation dialog:

| Field | Required | Description |
|-------|----------|-------------|
| Archetype | No | Optional template to inherit traits and qualities from |
| Name | Yes | Display name (e.g., "Creative Writer") |
| Description | No | Short summary (up to 300 chars) |
| General Domain | No | Broad expertise area (e.g., "Arts") |
| Specific Domain | No | Narrow specialty (e.g., "Fiction Writing") |

**Creating from an archetype:** When an archetype is selected, the persona inherits all traits and auto-enables trait-dependent qualities. The button changes to "Create from Archetype". Inherited traits are marked with `is_inherited=true` in the database.

After creation, the persona appears in the catalog and you can navigate to its detail page.

### Viewing a Persona Detail (`/persona/:id`)

The detail page uses a block-based layout:

- **Identity** — Name and tagline
- **Bio** — Extended description
- **Domains** — Color-coded expertise areas
- **Traits** — Inherited personality traits (fetched from API, pink badges)
- **Qualities** — Enabled qualities (fetched from API, purple badges)
- **Relationships** — Links to related entities (agents, users, teams)

### Editing a Persona Page

Any authenticated user can toggle **Edit Mode** via the header button:

- **Add blocks** from the sidebar palette
- **Reorder** blocks with up/down arrows
- **Hide/Show** blocks with the visibility toggle
- **Delete** blocks with the trash icon
- **Edit content** by clicking a block to open the editor sheet
- **Save** changes with the Save button (or cancel to discard)

### Adding Personas to Your Library

From the catalog section on `/personas`, click any persona card to view it. To add it to your library, use the PersonaPicker component (available in room settings or agent configuration).

---

## Relationship to Other Systems

| System | Connection |
|--------|------------|
| **PersonaPicker** | Component for selecting/managing personas in rooms/agents. See [persona-picker-reference.md](./persona-picker-reference.md) |
| **User Pages** | Same block-based page editor. See [user-pages-reference.md](./user-pages-reference.md) |
| **Agent Pages** | Agents can have persona libraries via `AgentPersonasService` |
| **Archetypes** | Personas can be created from archetypes via `createPersonaFromArchetype` |
| **Traits/Qualities** | Stored separately, displayed in TraitsBlock. APIs: `TraitsService`, `QualitiesService` |
