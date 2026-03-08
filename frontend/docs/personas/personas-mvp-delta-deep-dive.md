# Personas MVP Delta Deep Dive

## Purpose

This document maps the current personas design in `frontend/docs/personas` against the actual frontend and backend implementation in the repo, with one explicit product constraint:

- vouch is out of scope for MVP

The goal is to answer a narrower question than the broader big plan:

- what remaining work is required so users can create and manage distinct personas
- those personas can shape what other users see
- those personas are not collapsed back into one undifferentiated public user profile

This is a delta analysis, not a new speculative plan.

## Executive Summary

The repo already contains a substantial phase-1 user page implementation:

- `/u/$slug` runtime page exists
- `/u/$slug/compose` owner composer exists
- the `UserPageViewModel` contract exists
- the typed blocks for `primaryPersona`, `workFeed`, `personaManager`, `audiencePresentation`, and `relationshipManager` exist
- the builder validation layer exists

So the main MVP gap is no longer "build the user page UI."

The main MVP gap is that persona identity, audience visibility, and authored persona state are still split across:

- global `Persona` records
- `UserPersona` library junction rows
- page block JSON

That means the system can currently demo persona-shaped pages, but it cannot yet reliably claim that user personas are truly distinct, owner-scoped, and disassociated from each other for other users.

## What Is Already Implemented

### User page runtime and composer

Implemented:

- runtime route at `/u/$slug`
- owner-only composer route at `/u/$slug/compose`
- dedicated user-page builder with:
  - surface navigation
  - validation panel
  - surface editor
  - preview
  - save bar

This matches the direction in `big-plan.md` and `users-page-composer-reference.md`.

### Typed phase-1 user page contracts

Implemented in frontend:

- `UserPageMode`
- `AudienceScope`
- `UserPageViewModel`
- `UserWorkFeedItem`
- `UserPersonaSummary`
- `AudiencePresentationSummary`
- `PersonaRelationSummary`

This is already present in `frontend/src/components/UserPage/types.ts`.

### New block taxonomy

Implemented in the shared page system:

- `primaryPersona`
- `workFeed`
- `personaManager`
- `audiencePresentation`
- `relationshipManager`

These are registered in the page block registry, included in the user template, and rendered by `PageShell`.

### Builder draft adapter and validation

Implemented:

- typed user-page draft adapter
- serialization back to page blocks
- cross-block validation for:
  - missing primary persona references
  - missing presentation persona references
  - missing visible work references
  - missing relation source persona references

This is meaningfully beyond the original high-level concept doc.

### Persona creation and association UX

Implemented:

- create persona from the user page composer
- assign nickname, bios, tags, publication state, and optional primary designation
- associate work items to personas
- create audience views tied to personas
- create persona-mediated relations

So the repo already supports the authoring flow at a UI level.

## What Is Only Partially Real

This is the key delta.

### 1. "User personas" are not yet true user-owned persona entities

Current implementation:

- creating a persona from the user page composer calls `PersonasService.createPersona(...)`
- that creates a global `Persona`
- then the app creates a `UserPersona` row that only links the current user to that global persona

The `UserPersona` backend model currently stores only:

- `persona_id`
- `nickname`
- `is_active`

It does not store:

- short bio
- long bio
- tags
- publication state
- primary designation
- audience-specific publication state
- any page-facing persona metadata beyond nickname/active flag

Those richer authored fields are currently persisted in page block JSON inside `personaManager`, not in a backend user-persona publication model.

Consequence:

- the authored persona a user manages on their page is not actually the same thing as a durable backend entity
- persona metadata can drift between the page JSON and the underlying persona/library records
- the system cannot yet enforce user-scoped persona behavior outside the page layer

### 2. Audience views exist as authored content, but audience resolution is not real

Current implementation:

- audience presentations can be authored and saved in page JSON
- runtime selects an audience scope by taking the first presentation or defaulting to `public`

Not implemented:

- determine the viewer's actual audience scope from relationship/access state
- select the correct presentation for the visiting user
- support per-visitor or per-group audience assignment in backend data
- any gating stronger than "show the stored presentation chosen by frontend defaults"

Consequence:

- the system can author multiple audience views
- but it cannot yet reliably say "viewer X sees persona A while viewer Y sees persona B"

This is the biggest product gap for the "disassociated from each other for other users" requirement.

### 3. Visitor-visible persona isolation is representational, not enforced

Current implementation:

- visitor runtime filters work through audience presentations
- if no presentation exists, visitor sees sparse empty state
- direct user-to-user relation UI is avoided

But:

- personas shown to visitors are derived from page JSON plus frontend filtering
- there is no backend publication object enforcing what persona metadata is public for which audience
- there is no stable model for "this persona presentation is published to this audience and hidden from all others"

Consequence:

- the UX points in the right direction
- the data model does not yet guarantee it

### 4. Work is still page-authored metadata, not a canonical work system

Current implementation:

- work items are authored in `workFeed` block content
- each work item stores persona associations and intended audiences in page JSON

Not implemented:

- canonical backend `Work` entity for user pages
- durable work-to-persona relation model
- reliable reuse of existing demos/prompts/pages as first-class page work references

Consequence:

- sufficient for UX validation
- weak for long-term integrity

For MVP this may be acceptable if the requirement is only "author a persona-shaped page," not "ship a unified work graph."

### 5. Relations are authored, but still page-local

Current implementation:

- relations are persona-mediated in the UI
- relation summaries are saved in `relationshipManager` block content

Not implemented:

- backend relation table for user-page persona relations
- identity-aware target resolution
- relationship-driven audience access logic

Consequence:

- good representational MVP surface
- not enough to drive real audience segmentation

## High-Priority Mismatches Against MVP Needs

If the MVP requirement is:

- a user can create multiple distinct personas
- a user can manage them
- other users do not see those personas collapsed into one single identity

then these are the highest-priority remaining gaps.

### P0: Define the backend source of truth for user-owned persona state

This is the most important unresolved item.

Right now the source of truth is split:

- global `Persona`
- user library junction
- page JSON

For MVP, product and engineering need one explicit answer:

1. treat `UserPersona` as the real user-owned persona entity and extend it
2. or create a new user-persona publication/profile model

At minimum, the backend-owned record for a user's page persona needs fields for:

- owner user id
- backing persona id or null
- display name / nickname policy
- short bio
- long bio
- weighted tags
- publication state
- primary flag
- optional stable ordering

Without this, persona management remains page-content-driven rather than product-model-driven.

### P0: Define how visitor audience is resolved

This must be explicit for MVP.

Today there is no real answer to:

- how does the system know whether a viewer is `public`, `trusted`, `collaborators`, or `custom`?

Without vouches, MVP can still ship with a reduced audience model, but it needs one of these decisions:

1. `public` only for MVP
2. manual owner-managed allowlists/groups
3. simple relation-derived scopes from explicit persona relations

If none of these are implemented, the audience-specific persona experience is not real.

### P0: Bind published visitor experience to persona presentation, not generic page content

The runtime should guarantee:

- visitors only see audience-eligible persona presentation
- visitors only see work explicitly attached to that presentation
- visitors do not see unpublished persona metadata

The current frontend approximates this, but the data contract does not yet guarantee it.

### P1: Decide whether persona creation should remain globally catalogued

Current behavior creates a global `Persona`, then links it to the user.

That creates a product question:

- should a user-created persona be globally discoverable in `/personas`?

If the answer is no for MVP, current implementation is wrong in product terms.

If the answer is yes, product should explicitly accept that these are reusable shared personas, not purely private user-owned personas.

This is a major identity semantics decision, not just an implementation detail.

### P1: Move authored persona fields out of page JSON

The page can still reference persona ids and presentation ids, but the persona's authored metadata should not live only inside block content if the feature is considered core product data.

Otherwise:

- edits do not have a clean transactional boundary
- page duplication can duplicate persona state incorrectly
- other surfaces cannot reliably consume the persona

### P1: Clarify primary persona semantics

There is a design inconsistency between docs:

- `big-plan.md` references an implicit hidden fallback persona if no primary exists
- current composer/runtime explicitly model primary persona as optional and not inferred

For MVP, the current implementation is simpler and probably better:

- primary persona is optional
- no implicit visible fallback

But product should lock this so backend contracts match it.

## What Can Be Deferred From MVP

These items do not block the narrower MVP if product accepts the current scope cut.

### Safe to defer

- vouch system
- rich privacy grants
- anonymous publication
- full backend relation graph
- canonical work backend
- advanced presentation cascade authoring UI
- cross-surface theme editor for user pages

### Probably also deferable

- complex custom audience groups
- multi-layer relation workflows
- automated audience derivation from social graph

## Recommended MVP Shape

If the goal is to ship the smallest honest version of "distinct personas for other users," the cleanest MVP is:

### Visitor model

- public audience only
- optionally one additional manually assigned non-public audience later if needed

### Persona model

- user owns multiple personas
- persona metadata is persisted in a backend user-owned record
- each persona has `draft` or `published`
- one optional primary persona

### Presentation model

- audience presentation rows reference:
  - one user-owned persona
  - one audience scope
  - visible work ids
  - headline/framing text

### Runtime rule

- visitor sees only the published presentation that matches their audience scope
- if none matches, show sparse empty state

That would satisfy the user-facing requirement without implementing vouch.

## Concrete Remaining Work

### Backend work required for MVP

#### 1. Create a real backend contract for user-owned persona state

Required:

- durable storage for user-authored persona metadata
- API read/write endpoints for that model
- contract for publish/unpublish
- contract for primary persona designation

This is the single highest-priority request.

#### 2. Create a real backend contract for audience presentations

Required:

- durable audience presentation records
- reference to user-owned persona
- reference to visible work items or interim work ids
- audience scope
- publication/runtime eligibility rules

#### 3. Decide and implement audience resolution

Minimum MVP option:

- always resolve visitor to `public`

Better MVP option:

- support `public` plus one manually managed non-public audience path

#### 4. Decide product semantics for user-created personas

Required decision:

- globally reusable persona catalog entries
- or user-owned page personas not exposed as shared catalog personas

Current implementation behaves like the former.

### Frontend work required for MVP

#### 1. Stop treating page JSON as the source of truth for persona metadata

The page should reference backend-owned persona state, not carry the entire persona object as primary persistence.

#### 2. Update `useUserPageViewModel` to derive from backend persona/presentation records

Today it hydrates from block content plus owner-only library data.

For MVP it should instead compose:

- page layout
- user-owned persona records
- audience presentation records
- viewer audience resolution

#### 3. Make visitor audience selection deterministic

Current behavior uses the first available presentation or `public`.

That should be replaced with explicit runtime audience resolution.

#### 4. Decide whether composer still edits page blocks or edits product entities plus page references

Recommended:

- composer edits product entities for personas/presentations
- page blocks remain the layout and rendering shell

### Optional frontend work that can wait

- richer presentation controls using `page_theme_id` / `cards_theme_id` / `presentation_json`
- advanced browse and management variants beyond the current composer

## Notable Implementation Risks If Shipped As-Is

### Risk 1: Persona data drift

The same conceptual persona is currently represented across multiple stores.

### Risk 2: Audience claims exceed reality

The UI suggests audience-specific visibility, but backend audience resolution does not exist yet.

### Risk 3: User-created personas may leak into the shared persona universe unintentionally

Because creation currently goes through the global `Persona` API, product may accidentally ship shared/global semantics where private/user-owned semantics were intended.

### Risk 4: Runtime isolation is soft

The runtime mostly depends on frontend filtering of page-authored JSON, not backend-enforced publication/access semantics.

## Bottom Line

The user-page personas system is already far enough along to validate the UX model.

What is not finished for MVP is the product data model.

If vouch is excluded, the minimum honest MVP should focus on three things:

1. real backend-owned user persona records
2. real backend-owned audience presentation records
3. explicit visitor audience resolution, even if that resolution is only `public` for the first release

Without those three pieces, the system remains a strong prototype of persona-shaped pages rather than a finished MVP for distinct, disassociated user personas.
