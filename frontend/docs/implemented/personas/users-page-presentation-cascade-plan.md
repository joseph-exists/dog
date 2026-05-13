# Users Page Presentation Cascade Plan

## Purpose

This document defines the technical plan for bringing user pages closer to Demo-level presentation flexibility while preserving a single canonical contract for:

- composer-authored user pages
- API-authored user pages
- runtime rendering

The goal is not to add ad hoc theme controls to the composer first.
The goal is to establish a persisted presentation model that both the composer and external callers can rely on.

## Recommendation

Implement the backend-backed presentation contract first, then expose it progressively in the composer.

Reason:

- the hard problem is the persisted shape and cascade semantics
- API creation and composer creation must produce the same runtime result
- frontend-only presentation state would create drift and require a second migration later

The right order is:

1. define the persisted presentation contract
2. persist and validate it in backend page APIs
3. implement runtime cascade resolution
4. expose authoring controls in the composer in phases

## Existing Baseline To Reuse

The repository already has a useful theme vocabulary and cascade model:

- shared Theme registry
- `theme_id`
- `presentation_json`
- CSS-variable-first resolution
- page/cards/instance cascade rules

Relevant references:

- `frontend/src/components/Common/Themes/CASCADING-THEMES.md`
- `frontend/src/components/Agents/docs/THEME-CASCADE-REFERENCE.md`
- `frontend/src/services/themeService.ts`
- Demo composition persistence in backend:
  - `page_theme_id`
  - `cards_theme_id`
  - `presentation_json`

The user-page implementation should align with that vocabulary rather than inventing a separate styling system.

## Product Goal

User pages need to support:

- page-level theme selection
- block-level theme and presentation overrides
- element-level presentation overrides
- deterministic runtime cascade
- direct API creation without the composer
- future extension to richer per-surface and audience-specific presentation

This should still allow user pages to remain semantically different from Demo pages.
The presentation system should be shared; the content constructs should remain domain-specific.

## Non-Goals For The First Presentation Phase

Do not do these in the first phase:

- build a complete free-form visual editor for every presentation field
- support arbitrary executable CSS
- introduce separate frontend-only presentation persistence
- solve full audience-conditional styling at every leaf
- make every block expose every possible presentation override in one pass

## Canonical Persisted Contract

### Top-level page payload

The existing page payload should be extended from:

```ts
{
  layout_json: TemplateBlock[]
  layout_version?: number
}
```

to:

```ts
{
  layout_json: TemplateBlock[]
  layout_version?: number
  page_theme_id?: string | null
  cards_theme_id?: string | null
  presentation_json?: PagePresentationJson
}
```

### Proposed frontend types

```ts
export interface PagePresentationEnvelope {
  pageThemeId: string | null
  cardsThemeId: string | null
  presentation: PagePresentationJson
}

export interface PagePresentationJson {
  tokens?: Record<string, string | number | boolean | null>
  typography?: PresentationTypography
  motion?: PresentationMotion
  layout?: PresentationLayout
  effects?: Record<string, unknown>
  surfaces?: Record<string, SurfacePresentationJson>
}

export interface SurfacePresentationJson {
  tokens?: Record<string, string | number | boolean | null>
  typography?: PresentationTypography
  motion?: PresentationMotion
  layout?: PresentationLayout
  effects?: Record<string, unknown>
}

export interface PresentationTypography {
  font_family_ui?: string
  font_family_display?: string
  size?: "xs" | "sm" | "md" | "lg" | "xl"
  scale?: "compact" | "comfortable" | "expressive"
  line_height?: "tight" | "normal" | "relaxed"
  tracking?: "tight" | "normal" | "wide"
}

export interface PresentationMotion {
  enable?: boolean
  duration_ms?: number
  easing?: string
  reduce_motion_respect?: boolean
  panel_enter_ms?: number
  block_enter_ms?: number
}

export interface PresentationLayout {
  density?: "compact" | "comfortable" | "airy"
  content_width?: "narrow" | "standard" | "wide" | "full"
  block_gap?: string
  block_padding?: string
  align?: "start" | "center" | "stretch"
}
```

### Proposed block payload shape

Each block should support authored presentation metadata without breaking existing content/config semantics:

```ts
export interface PageBlockInstance {
  id: string
  type: string
  column: "primary" | "auxiliary"
  order: number
  config: Record<string, unknown>
  content: Record<string, unknown>
  visibility?: "visible" | "hidden"
  theme_id?: string | null
  presentation_json?: BlockPresentationJson
}
```

```ts
export interface BlockPresentationJson {
  tokens?: Record<string, string | number | boolean | null>
  typography?: PresentationTypography
  motion?: PresentationMotion
  layout?: PresentationLayout
  effects?: Record<string, unknown>
  elements?: Record<string, ElementPresentationJson>
}
```

### Proposed element payload shape

```ts
export interface ElementPresentationJson {
  theme_id?: string | null
  tokens?: Record<string, string | number | boolean | null>
  typography?: PresentationTypography
  motion?: PresentationMotion
  layout?: PresentationLayout
  effects?: Record<string, unknown>
  visibility?: "inherit" | "visible" | "hidden"
}
```

## Why This Shape

This contract preserves the existing repo vocabulary:

- theme ids remain references to registry themes
- `presentation_json` remains the authored override envelope
- tokens remain the final shared integration contract into runtime CSS variables

It also gives a path for:

- page-level themes
- block-level themes
- element-level local overrides

without requiring every block to understand every presentation field equally.

## Merge And Cascade Rules

### Canonical precedence

The recommended cascade for user pages is:

1. application defaults (`:root`)
2. page theme tokens from `page_theme_id`
3. cards theme tokens from `cards_theme_id`
4. page `presentation_json`
5. block-type defaults from registry or renderer defaults
6. block `theme_id`
7. block `presentation_json`
8. element `theme_id`
9. element `presentation_json`

Nearest layer wins for overlapping keys.

### Important semantic rules

#### Rule 1: Theme and presentation are different layers

- `theme_id` references reusable token bundles
- `presentation_json` expresses authored overrides and local presentation intent

Do not collapse these into one field.

#### Rule 2: Tokens are the runtime contract

All higher-level presentation fields should normalize toward tokens and a small set of render hints.

That means:

- `typography`, `motion`, `layout`, and `effects` are authored structures
- runtime resolution may translate them into CSS variables, explicit classes, or renderer props

#### Rule 3: Page themes own the page surface

Consistent with the existing theme docs:

- page themes may set `--background`
- cards themes must not own the page surface

#### Rule 4: Block type defaults are code-owned

Each block renderer may define stable presentation defaults for readability and structure.

These defaults are not persisted unless the author overrides them.

#### Rule 5: Element ids must be deterministic

Element-level presentation is only safe if element keys are stable.

Examples:

- `header`
- `title`
- `subtitle`
- `meta`
- `tagList`
- `cta`
- `emptyState`
- `itemCard`
- `itemTitle`
- `itemBadge`

Do not use fragile DOM-derived selectors or generated ids.

#### Rule 6: Unknown presentation keys are stored but not guaranteed

Backend should allow unknown JSON keys inside `presentation_json` to preserve forward compatibility.
Frontend renderers should only consume supported keys.

## Proposed Backend API Shape

### Backward-compatible page response

Current page response is effectively:

```json
{
  "id": "...",
  "entity_type": "user",
  "entity_id": "...",
  "owner_id": "...",
  "layout_version": 3,
  "layout_json": [ ... ],
  "created_at": "...",
  "updated_at": "..."
}
```

Proposed page response:

```json
{
  "id": "...",
  "entity_type": "user",
  "entity_id": "...",
  "owner_id": "...",
  "layout_version": 3,
  "layout_json": [ ... ],
  "page_theme_id": null,
  "cards_theme_id": null,
  "presentation_json": {},
  "created_at": "...",
  "updated_at": "..."
}
```

### Backward-compatible upsert payload

```json
{
  "layout_json": [ ... ],
  "layout_version": 3,
  "page_theme_id": "uuid-or-null",
  "cards_theme_id": "uuid-or-null",
  "presentation_json": {
    "tokens": {
      "--page-accent": "oklch(0.68 0.16 230)"
    },
    "layout": {
      "density": "comfortable"
    }
  }
}
```

### Example block payload

```json
{
  "id": "work-feed-1",
  "type": "workFeed",
  "column": "primary",
  "order": 4,
  "config": {},
  "content": {
    "title": "Work Flow",
    "items": []
  },
  "visibility": "visible",
  "theme_id": "block-theme-uuid",
  "presentation_json": {
    "tokens": {
      "--card-radius": "18px"
    },
    "elements": {
      "title": {
        "tokens": {
          "--foreground": "oklch(0.2 0.02 250)"
        }
      },
      "itemBadge": {
        "theme_id": "badge-theme-uuid",
        "tokens": {
          "--badge-border-opacity": "0.24"
        }
      }
    }
  }
}
```

## Proposed Backend Model Changes

### Extend `Page`

The simplest aligned backend change is to extend the existing `pages` table rather than creating a second presentation table immediately.

Proposed fields:

```py
class PageBase(SQLModel):
    entity_type: str
    entity_id: str
    owner_id: UUID
    layout_version: int = 1
    layout_json: list[dict[str, Any]]
    page_theme_id: UUID | None = None
    cards_theme_id: UUID | None = None
    presentation_json: dict[str, Any] = Field(default_factory=dict)
```

### Why extend `Page` first

- minimal new conceptual surface
- consistent with Demo composition storage
- one payload for both composer and API callers
- lowest-friction migration path from current page API

### Validation requirements

Backend should validate:

- `page_theme_id` references a visible theme in category `page`
- `cards_theme_id` references a visible theme in category `card`
- block `theme_id` references a visible theme in category `card`
- element `theme_id` references a visible theme in an allowed category
- `presentation_json` values are JSON objects if present

Backend should not fully validate every nested presentation key semantically in phase 1.
That should remain mostly frontend/runtime-owned while the contract is stabilizing.

## Frontend Runtime Resolution

### New runtime resolver layer

Add a shared resolver for page/block/element presentation:

```ts
export interface ResolvedPresentation {
  tokens: Record<string, string>
  typography?: PresentationTypography
  motion?: PresentationMotion
  layout?: PresentationLayout
  effects?: Record<string, unknown>
}

export function resolvePagePresentation(...)
export function resolveBlockPresentation(...)
export function resolveElementPresentation(...)
```

### Suggested source order in runtime

`PageShell`
- resolves page theme + cards theme + page presentation

Each block wrapper
- resolves page scope + block defaults + block theme + block presentation

Each declared element wrapper
- resolves page scope + block scope + element theme + element presentation

### Rendering integration

Prefer:

- transparent wrappers
- CSS variable application through style objects
- small renderer-specific interpretation layers for typography/layout/effects

Avoid:

- ad hoc class branching for every presentation feature
- unstructured inline style mutation in every block renderer

## Composer Implications

The composer should not begin by exposing every level of the cascade at once.

### Authoring sequence

Phase-in the UI in this order:

1. page-level themes and top-level `presentation_json`
2. block-level `theme_id` and `presentation_json`
3. element-level `presentation_json`
4. optional element-level `theme_id`

### Why not element-first

- element ids need to stabilize first
- authors need to understand page and block scopes before leaf scopes
- block-level overrides will solve most real needs initially

## API-Creation Implications

External callers should be able to create a complete user page in one request using the same payload shape the composer saves.

That implies:

- page contract must be self-contained
- themes must be referenceable by UUID
- `presentation_json` must be preserved end-to-end
- runtime must not depend on frontend-only derived state

This is the main reason the backend contract comes before advanced composer UI.

## Proposed Type Additions In Frontend

### Update page service types

```ts
export interface PageLayoutViewModel {
  id: string
  entityType: string
  entityId: string
  ownerId: string
  layoutVersion: number
  layout: TemplateBlock[]
  pageThemeId: string | null
  cardsThemeId: string | null
  presentation: PagePresentationJson
  createdAt: Date
  updatedAt: Date
}

export interface SavePageLayoutInput {
  entityType: string
  entityId: string
  layout: TemplateBlock[]
  layoutVersion?: number
  pageThemeId?: string | null
  cardsThemeId?: string | null
  presentation?: PagePresentationJson
}
```

### Update block type

```ts
export interface TemplateBlock {
  id?: string
  type: BlockType
  column: "primary" | "auxiliary"
  order: number
  config: Record<string, unknown>
  content?: Record<string, unknown>
  visibility?: "visible" | "hidden"
  theme_id?: string | null
  presentation_json?: BlockPresentationJson
}
```

## Proposed Backend Schema Additions

### Pydantic / SQLModel payloads

```py
class PageLayoutUpdate(SQLModel):
    layout_json: list[dict[str, Any]]
    layout_version: int | None = None
    page_theme_id: UUID | None = None
    cards_theme_id: UUID | None = None
    presentation_json: dict[str, Any] = Field(default_factory=dict)
```

```py
class PagePublic(SQLModel):
    id: UUID
    entity_type: str
    entity_id: str
    owner_id: UUID
    layout_version: int
    layout_json: list[dict[str, Any]]
    page_theme_id: UUID | None = None
    cards_theme_id: UUID | None = None
    presentation_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
```

## Phased Implementation Order

### Phase 0: Contract Definition

Deliverables:

- finalize persisted page-level fields
- finalize block-level `theme_id` + `presentation_json`
- finalize element-level envelope and deterministic element key rules
- document merge precedence

Acceptance criteria:

- engineers can author a valid page payload without the composer
- frontend and backend both reference the same contract

### Phase 1: Backend Persistence

Deliverables:

- extend `pages` table with:
  - `page_theme_id`
  - `cards_theme_id`
  - `presentation_json`
- extend page CRUD and API models
- preserve backward compatibility for pages with only `layout_json`
- validate theme references lightly

Acceptance criteria:

- existing pages still load
- API callers can persist presentation metadata
- composer can round-trip new fields without loss

### Phase 2: Runtime Resolution

Deliverables:

- add shared resolver utilities for page/block/element presentation
- update `PageShell` and user-page block wrappers to consume page and block presentation
- support transparent scope wrappers with token layering

Acceptance criteria:

- page themes affect page surface
- cards themes affect block/card surfaces
- block presentation overrides page defaults

### Phase 3: Composer Page-Level Presentation

Deliverables:

- page theme picker
- cards theme picker
- page-level `presentation_json` editor
- preview integration

Acceptance criteria:

- user can author page-wide presentation without editing raw JSON externally

### Phase 4: Composer Block-Level Presentation

Deliverables:

- block theme picker
- block-level presentation editor
- block preview reflecting unsaved changes

Acceptance criteria:

- user can style individual blocks without breaking page-level inheritance

### Phase 5: Element-Level Presentation

Deliverables:

- deterministic element registries per block type
- element presentation editor UI
- runtime wrappers at declared element boundaries

Acceptance criteria:

- user can style named elements predictably
- unsupported element keys are ignored safely

### Phase 6: API + Regression Coverage

Deliverables:

- API examples for user-page creation
- round-trip tests for page save/load
- runtime cascade tests
- composer tests for page/block/element preview fidelity

Acceptance criteria:

- same payload works from API and composer
- cascade precedence remains stable under regression tests

## Required Test Matrix

### Backend

- page payload without presentation fields still succeeds
- page payload with valid `page_theme_id` succeeds
- invalid theme category on `page_theme_id` is rejected
- block `theme_id` persists through round trip
- `presentation_json` persists without mutation

### Frontend runtime

- page theme sets page background when no downstream override exists
- cards theme overrides card tokens but not page background
- block `presentation_json.tokens` overrides page/cards tokens
- element `presentation_json.tokens` overrides block tokens

### Composer

- page-level theme change updates preview without save
- block-level theme change updates preview without save
- save/load round trip preserves page/block presentation metadata
- unsupported element keys do not break preview

## Open Decisions

These decisions should be made explicitly before implementation starts:

### 1. Should blocks support both `theme_id` and `presentation_json` immediately?

Recommendation:
- yes for blocks
- yes for page
- element-level `theme_id` can be deferred if needed

### 2. Should element-level support begin with tokens only?

Recommendation:
- yes

Reason:
- element-level tokens are the safest and most composable first slice
- richer element-level motion/effects can follow after the element registry is proven

### 3. Should page API remain page-specific or move toward a generalized composition envelope?

Recommendation:
- keep the existing page API
- extend its payload

Reason:
- smaller migration
- lower risk
- still compatible with future composition-envelope extraction if needed

## Suggested Immediate Next Step

The next concrete implementation step should be:

1. extend the backend `Page` model and page APIs to persist `page_theme_id`, `cards_theme_id`, and `presentation_json`
2. extend the frontend `PageService` and `TemplateBlock` types to round-trip those fields
3. stop there before building new composer UI

That gives a stable canonical contract first, which is the necessary foundation for both composer-driven and API-driven page creation.
