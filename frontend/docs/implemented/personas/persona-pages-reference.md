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

[josep-note: see extended note on this definition below. I am moving very quickly away from the domain language, this may be refactored in very near future]

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

## Current Relationship Structure for archetypes/personas/qualities/traits included as addendum





## New Block Types

### DomainsBlock

Displays domain expertise areas with color-coded hierarchy.

[josep-note: these don't feel right in their current form. I think extensability/integration with the tag structure will be important here.  if I try to model these for [human, agent] concurrently, i think more about capability and accessibility. tools, range, sophistication? desires, motivations, affordances?  There's a distinction between (what we need to do)(what we like doing)(what we're good at) - and there's a further distinction between (how we need to do a thing)(how we want to do a thing) and these distinctions will have an impact on who we want or need to do a thing with.  If we're driven to learn and know, that's a different context then being driven by fear of not completing a task.  If we're driven to become better using a specific tool or way of thinking or way of approaching a problem - then that's a different epistemic position than being driven to be financially successful through the application of solving that particular problem.  These epistemic stances, and our capability to move through them, are part of our relational construct.  If one way we're thinking about the affordance of personas is to enable movement through different affordances of being - so a person/agent/etc isn't stuck in an interpellated approximation of 'who they are and what they are capable of and what they have to do to survive' - then telling a person to choose their domains feels counterproductive.  Tagging seems better, and weighted tagging seems more fluid than a hierarchical structure.  But not too much more noodling.  We need to move. 

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

A persona represents a character profile with identity, expertise domains, and personality traits. Personas can be added to your personal library and assigned to agents or used elsewhere as a userPersona.

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



## ADDENDUM A: current data objects


                          Table "public.archetype"
   Column    |            Type             | Collation | Nullable | Default 
-------------+-----------------------------+-----------+----------+---------
 id          | uuid                        |           | not null | 
 created_at  | timestamp without time zone |           | not null | 
 description | character varying(255)      |           |          | 
 name        | character varying(255)      |           | not null | 
Indexes:
    "archetype_pkey" PRIMARY KEY, btree (id)
Referenced by:
    TABLE "archetypepersonalink" CONSTRAINT "archetypepersonalink_archetype_id_fkey" FOREIGN KEY (archetype_id) REFERENCES archetype(id)
    TABLE "archetypequalitylink" CONSTRAINT "archetypequalitylink_archetype_id_fkey" FOREIGN KEY (archetype_id) REFERENCES archetype(id)
    TABLE "archetypetraitlink" CONSTRAINT "archetypetraitlink_archetype_id_fkey" FOREIGN KEY (archetype_id) REFERENCES archetype(id)
    TABLE "personaqualitylink" CONSTRAINT "personaqualitylink_source_archetype_id_fkey" FOREIGN KEY (source_archetype_id) REFERENCES archetype(id)
    TABLE "personatraitlink" CONSTRAINT "personatraitlink_source_archetype_id_fkey" FOREIGN KEY (source_archetype_id) REFERENCES archetype(id)
    
                            Table "public.trait"
   Column    |            Type             | Collation | Nullable | Default 
-------------+-----------------------------+-----------+----------+---------
 id          | uuid                        |           | not null | 
 created_at  | timestamp without time zone |           | not null | 
 description | character varying(255)      |           |          | 
 name        | character varying(255)      |           | not null | 
Indexes:
    "trait_pkey" PRIMARY KEY, btree (id)
Referenced by:
    TABLE "archetypetraitlink" CONSTRAINT "archetypetraitlink_trait_id_fkey" FOREIGN KEY (trait_id) REFERENCES trait(id)
    TABLE "personaqualitylink" CONSTRAINT "personaqualitylink_source_trait_id_fkey" FOREIGN KEY (source_trait_id) REFERENCES trait(id)
    TABLE "personatraitlink" CONSTRAINT "personatraitlink_trait_id_fkey" FOREIGN KEY (trait_id) REFERENCES trait(id)
    TABLE "qualitytraitlink" CONSTRAINT "qualitytraitlink_trait_id_fkey" FOREIGN KEY (trait_id) REFERENCES trait(id)
    TABLE "traitconflictgroupmember" CONSTRAINT "traitconflictgroupmember_trait_id_fkey" FOREIGN KEY (trait_id) REFERENCES trait(id)

tinyfoot=# \d quality;
                           Table "public.quality"
   Column    |            Type             | Collation | Nullable | Default 
-------------+-----------------------------+-----------+----------+---------
 id          | uuid                        |           | not null | 
 created_at  | timestamp without time zone |           | not null | 
 description | character varying(255)      |           |          | 
 name        | character varying(255)      |           | not null | 
Indexes:
    "quality_pkey" PRIMARY KEY, btree (id)
Referenced by:
    TABLE "archetypequalitylink" CONSTRAINT "archetypequalitylink_quality_id_fkey" FOREIGN KEY (quality_id) REFERENCES quality(id)
    TABLE "personaqualitylink" CONSTRAINT "personaqualitylink_quality_id_fkey" FOREIGN KEY (quality_id) REFERENCES quality(id)
    TABLE "qualityeventtrigger" CONSTRAINT "qualityeventtrigger_quality_id_fkey" FOREIGN KEY (quality_id) REFERENCES quality(id)
    TABLE "qualitytraitlink" CONSTRAINT "qualitytraitlink_quality_id_fkey" FOREIGN KEY (quality_id) REFERENCES quality(id)

[note: persona columns to be refactored in very near future]
tinyfoot=# \d persona;
                               Table "public.persona"
        Column        |            Type             | Collation | Nullable | Default 
----------------------+-----------------------------+-----------+----------+---------
 id                   | uuid                        |           | not null | 
 created_at           | timestamp without time zone |           | not null | 
 description          | character varying(255)      |           |          | 
 name                 | character varying(255)      |           | not null | 
 long_description     | character varying           |           |          | 
 general_domain       | character varying(255)      |           |          | 
 specific_domain      | character varying(255)      |           |          | 
 general_domain_high  | character varying(255)      |           |          | 
 specific_domain_high | character varying(255)      |           |          | 
Indexes:
    "persona_pkey" PRIMARY KEY, btree (id)
Referenced by:
    TABLE "agent_personas" CONSTRAINT "agent_personas_persona_id_fkey" FOREIGN KEY (persona_id) REFERENCES persona(id) ON DELETE CASCADE
    TABLE "archetypepersonalink" CONSTRAINT "archetypepersonalink_persona_id_fkey" FOREIGN KEY (persona_id) REFERENCES persona(id)
    TABLE "personaqualitylink" CONSTRAINT "personaqualitylink_persona_id_fkey" FOREIGN KEY (persona_id) REFERENCES persona(id)
    TABLE "personatraitlink" CONSTRAINT "personatraitlink_persona_id_fkey" FOREIGN KEY (persona_id) REFERENCES persona(id)
    TABLE "room_participant_bindings" CONSTRAINT "room_participant_bindings_persona_id_fkey" FOREIGN KEY (persona_id) REFERENCES persona(id)
    TABLE "userpersona" CONSTRAINT "userpersona_persona_id_fkey" FOREIGN KEY (persona_id) REFERENCES persona(id)
    
[note: event included for consistency, not integrated with any current components, will be used extensively in vouch and recommender systems, along with tag object]
tinyfoot=# \d event
                            Table "public.event"
   Column    |            Type             | Collation | Nullable | Default 
-------------+-----------------------------+-----------+----------+---------
 name        | character varying(255)      |           | not null | 
 description | character varying(100)      |           |          | 
 event_type  | character varying(100)      |           | not null | 
 id          | uuid                        |           | not null | 
 created_at  | timestamp without time zone |           | not null | 
Indexes:
    "event_pkey" PRIMARY KEY, btree (id)
Referenced by:
    TABLE "qualityeventtrigger" CONSTRAINT "qualityeventtrigger_event_id_fkey" FOREIGN KEY (event_id) REFERENCES event(id)


[note: tag will be extended to all primary data objects]
tinyfoot=# \d tag
                       Table "public.tag"
 Column |         Type          | Collation | Nullable | Default 
--------+-----------------------+-----------+----------+---------
 name   | character varying(50) |           | not null | 
 color  | character varying(20) |           |          | 
 id     | uuid                  |           | not null | 
Indexes:
    "tag_pkey" PRIMARY KEY, btree (id)
    "tag_name_key" UNIQUE CONSTRAINT, btree (name)
Referenced by:
    TABLE "storytotag" CONSTRAINT "storytotag_tag_id_fkey" FOREIGN KEY (tag_id) REFERENCES tag(id) ON DELETE CASCADE
