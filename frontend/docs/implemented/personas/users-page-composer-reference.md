# Users Page Composer Reference

## Purpose

This document is the working technical and functional reference for the current Users page authoring tool.

It is intended for:

- people composing a user page in the current frontend
- engineers extending the composer
- product/design work that needs to distinguish what exists now from what still needs to be built

This reference describes the current implemented behavior, not the aspirational end state.

## Current Surfaces

There are now two distinct surfaces for a user page:

- Runtime page: `/u/$slug`
- Composer: `/u/$slug/compose`

The runtime page is the published or preview-like surface.
The composer is the owner-only authoring surface.

The runtime page should be treated as the place where a user sees the resulting page.
The composer should be treated as the place where a user structures, edits, and validates that page.

## Core Mental Model

The current user-page system is organized around four constructs:

- Work
- Personas
- Audience Views
- Relations

Those constructs are expressed through page blocks, but the composer should be understood as construct-oriented first and block-oriented second.

The current typed constructs are:

- `identity`
- `bio`
- `primaryPersona`
- `workFeed`
- `personaManager`
- `audiencePresentation`
- `relationshipManager`

These typed constructs are held in a dedicated draft adapter layer and serialized back into page blocks on save.

## Authoring Workflow

### Recommended sequence

The current effective sequence for composing a user page is:

1. Set `identity` and `bio` so the page has a baseline orientation.
2. Create or curate personas in `personaManager`.
3. Optionally choose a `primaryPersona`.
4. Add representative work in `workFeed`.
5. Create audience-specific views in `audiencePresentation`.
6. Define persona-mediated relations in `relationshipManager`.
7. Review validation issues and runtime preview before saving.

This order matters because later constructs depend on earlier ones:

- audience presentations reference personas and work ids
- relations reference a source persona
- primary persona must refer to a known persona

## Composer Layout

The composer currently has these major regions:

- block palette
- surface navigation
- validation panel
- surface editor
- block editor sheet
- runtime preview
- save bar

### What each region does

`BlockPalette`
- Adds blocks to the primary or auxiliary column.
- For typed construct blocks, the adapter enforces single-instance behavior.

`UserPageBuilderNavigator`
- Changes the working surface:
  - `overview`
  - `layout`
  - `work`
  - `personas`
  - `audiences`
  - `relations`

`UserPageBuilderValidationPanel`
- Shows cross-construct problems in the current draft.

`UserPageBuilderSurfaceEditor`
- Shows scoped block inventory for the selected surface.
- Supports select, move, hide/show, reset, and delete.

`BlockEditorSheet`
- Edits content for the currently selected block.

`UserPageBuilderPreview`
- Renders the current unsaved draft using runtime block rendering.

`UserPageBuilderSaveBar`
- Persists the serialized block layout back to the page service.

## Block-Level Reference

### `identity`

Purpose:
- Establish the page’s top-level name and tagline.

Use it for:
- user-facing orientation
- minimal runtime identification

Do not use it for:
- audience-specific framing
- persona-specific claims

### `bio`

Purpose:
- Provide general framing text for the page.

Use it for:
- stable overview context
- explanation of what kind of work or perspective the page represents

Do not use it for:
- audience-specific presentation
- relation-specific messaging

### `primaryPersona`

Purpose:
- Explicitly designate a primary persona, if the user wants one.

Rules:
- optional
- explicit only
- no automatic fallback or inference

Use it for:
- orienting the page toward one persona without collapsing all identity into it

### `workFeed`

Purpose:
- Represent the flow of work surfaced by the page.

Current content shape:
- title
- empty message
- items

Each work item currently carries:
- type
- title
- summary
- tags
- associated persona ids
- intended audience scopes
- representative flag
- optional href

Use it for:
- representative artifacts
- demos, prompts, stories, pages, or other work-like outputs

Current limitation:
- this is still frontend-modeled work, not a dedicated backend `Work` entity

### `personaManager`

Purpose:
- Create, edit, tag, and manage user personas.

Current behavior:
- owner-only
- persona summaries are persisted in block content
- persona library APIs are reused where available

Use it for:
- shaping the page’s authored personas
- associating page-level persona metadata

Current limitation:
- persona management is still partly page-content-driven rather than fully backed by a dedicated persona publication model

### `audiencePresentation`

Purpose:
- Define what a given audience sees through a given persona.

Each presentation currently includes:
- persona id
- audience scope
- audience label
- headline
- framing text
- visible work ids
- relation call to action

Use it for:
- public view
- trusted view
- collaborator view
- custom audience framing

This is the main construct that prevents the page from becoming a single undifferentiated profile.

### `relationshipManager`

Purpose:
- Define persona-mediated relations.

Each relation currently includes:
- source persona id
- target label
- target type
- relation kind
- audience scope
- note
- status

Rules:
- every relation must originate from a persona
- there is no user-to-user relation UI at the page level

## Validation Rules

The current builder validation checks:

- more than one persona marked primary
- primary persona id missing from managed personas
- audience presentation persona id missing from managed personas
- audience presentation visible work ids missing from work feed
- relation source persona id missing from managed personas

These are draft-level validations.
They are intended to catch cross-block reference problems before save or preview confusion.

## Draft Adapter Behavior

The composer now edits a typed draft first, then serializes to page blocks.

This gives one mutation boundary for:

- content updates
- add block
- delete block
- reset block
- move block
- toggle visibility

Important consequences:

- typed construct blocks behave as single-instance constructs
- deleting a typed construct block resets its typed draft state
- re-adding a typed construct block restores default content/config instead of stale hidden state
- runtime preview always renders serialized output from the current draft

This is the key implementation seam that keeps the composer coherent as complexity increases.

## Effective Usage Guidance

### For page authors

Use the composer when:

- you are defining personas
- you are changing audience views
- you are associating work
- you are editing relations
- you are restructuring the page

Use the runtime page when:

- you want to inspect the page as a viewer would encounter it
- you want to enter the composer from a stable published surface

### For engineers

When adding new authoring behavior:

- prefer changing typed draft constructs first
- only serialize back to blocks at preview/save boundaries
- avoid introducing direct route-local mutations of block arrays if the adapter can own them

When adding new user-page semantics:

- decide whether the new concept is:
  - a typed construct
  - a generic block concern
  - a future backend concern

Do not add new semantics directly into random block content blobs if they need cross-construct validation or stable authoring behavior.

## What The Current Tool Does Well

- separates runtime page and composer into distinct routes
- gives users a dedicated authoring surface rather than overloading `/u/$slug`
- preserves a typed draft model behind the composer
- supports preview against the current unsaved draft
- supports persona-mediated rather than user-mediated relations
- supports audience-specific presentation framing

## Current Limitations

The current tool is still phase-1 and has important limits.

### Data model limits

- `slug === userId`
- work is frontend-modeled rather than backend-native
- primary persona is stored in page content, not backend identity state
- relations are stored in page content, not a backend relation model
- audience scopes are frontend enums with limited derivation logic

### Authoring UX limits

- many editors still use raw ids, arrays, and text fields rather than richer pickers
- the composer is block-aware, but not yet fully construct-native in every workflow
- there is no drag-and-drop layout editing
- layout logic is still tied to page block columns/orders

### Publication and access-control limits

- no vouch system
- no directional grants
- no anonymous publishing or claim flows
- no audience derivation beyond current frontend assumptions
- no durable backend publication workflow for personas or audience views

## Remaining Work To Meet The Intended Model

This is the current scope gap between phase 1 and the model the system appears to need.

### 1. Strengthen typed hydration and normalization

Needed:
- duplicate typed construct detection during draft hydration
- normalization of invalid or legacy layouts
- clearer recovery behavior when serialized blocks and typed constructs diverge

Why:
- this keeps the adapter boundary trustworthy as the system evolves

### 2. Make authoring more construct-native

Needed:
- dedicated editors for persona-to-work association
- dedicated editors for audience-view composition
- dedicated editors for relation creation and editing
- less reliance on generic block forms for the core user-page flows

Why:
- user-page authoring is not just block editing
- the current tool still exposes internal page-system mechanics more than ideal

### 3. Improve selectors and references

Needed:
- persona pickers instead of raw persona ids
- work selectors instead of manual work-item references
- audience selectors with explicit semantics
- relation target selection patterns

Why:
- current correctness depends too much on careful manual entry

### 4. Add stronger preview modes

Needed:
- audience-preview switching
- owner vs visitor preview mode
- clearer sparse states for missing audience views
- optional preview of unpublished or partial persona configurations

Why:
- the core idea of the page depends on discriminated presentation

### 5. Introduce backend support where the frontend seam is no longer enough

Needed:
- real work entity model
- persisted primary-persona support
- persisted persona-mediated relation model
- persona publication state beyond page content
- audience visibility and grant logic

Why:
- some of the intended semantics are now beyond what block-content persistence should carry

### 6. Add route- and UX-level regression coverage

Needed:
- tests proving `/u/$slug` and `/u/$slug/compose` remain distinct
- adapter tests for hydration recovery
- compositor tests for surface-driven workflows

Why:
- this system now depends heavily on route separation and typed draft integrity

## Recommended Next Scope Boundary

Before expanding feature breadth further, the next coherent scope would be:

1. strengthen typed hydration and validation
2. replace raw-id authoring with persona/work/audience selectors
3. move the core user-page workflows out of generic block forms and into composer-native editors

That would make the current tool substantially more usable without prematurely committing to backend identity and access-control architecture.

## Source Files

Primary implementation files:

- `frontend/src/routes/_layout/u.$slug.index.tsx`
- `frontend/src/routes/_layout/u.$slug.compose.tsx`
- `frontend/src/components/UserPage/builder/userPageBuilderAdapter.ts`
- `frontend/src/components/UserPage/builder/userPageBuilderSchema.ts`
- `frontend/src/components/UserPage/builder/UserPageBuilderPreview.tsx`
- `frontend/src/components/UserPage/builder/UserPageBuilderSurfaceEditor.tsx`
- `frontend/src/hooks/useUserPageViewModel.ts`

Supporting user-page authoring components:

- `frontend/src/components/UserPage/UserPersonaEditorSheet.tsx`
- `frontend/src/components/UserPage/UserWorkAssociationSheet.tsx`
- `frontend/src/components/UserPage/AudiencePresentationSheet.tsx`
- `frontend/src/components/UserPage/PersonaRelationSheet.tsx`
