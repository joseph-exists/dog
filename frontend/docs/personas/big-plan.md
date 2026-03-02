PLEASE IMPLEMENT THIS PLAN:
# Users Pages Phase 1 Implementation Spec

## Summary

Create a new implementation artifact at `frontend/docs/personas/users-pages-phase-1-implementation-spec.md` that defines a **frontend-first, PageShell-based** Users pages system centered on `UserPersona`, `Work`, audience-specific presentation, and persona-mediated relations.

Phase 1 does **not** implement vouch, privacy grants, anonymous publication, or backend identity restructuring. It does establish the UI contract, route behavior, block taxonomy, frontend view models, and interaction flows needed to validate the model without collapsing back into a direct user-to-user profile system.

The plan reuses two existing repo patterns:

- `PageShell` as the page composition/runtime surface.
- Builder-style typed contracts from Demo/Prompt Builder as the design pattern for local draft/view-model state and future capability growth.

## Product Intent Locked In

The Users pages implementation must represent four distinct surfaces:

1. **A. User homepage**
   A flow of Work the user is interested in.
   Phase 1 is representational only. It does not solve ranking/recommendation logic.

2. **B. UserPersona creation and management**
   A user creates, edits, tags, associates work, publishes/unpublishes, and optionally marks one persona as primary.

3. **C. User page as seen by others**
   Presentation is discriminated by audience and by the degree of work the selected persona has done for that audience.
   The page must present “work for this audience” rather than “this is the whole user.”

4. **D. Relational management**
   All relation management is mediated by `UserPersona`.
   No direct user-to-user relation affordance is exposed.
   A primary persona is optional and explicitly chosen.

## Architectural Decision

Use the existing `/u/$slug` route and `PageShell`, but change the route from a thin page existence wrapper into a **Users-page orchestrator** that loads a typed view model and passes richer context into user-specific blocks.

Do not create a new independent user-page framework in phase 1.

## Route and Surface Model

### Route

Keep:

- `/_layout/u/$slug`

Interpretation in phase 1:

- `slug` continues to resolve to `userId` for now.
- Owner and visitor use the same route but different view-model branches.

### Page Modes

The route orchestrator must derive one of these modes:

- `owner-empty`
- `owner-manage`
- `visitor-view`

### Owner Surface Structure

Owner mode uses one page shell but exposes four coordinated surfaces:

- `Work`
- `Personas`
- `Audience Views`
- `Relations`

These are implemented as blocks plus supporting sheets/dialogs, not as a separate app shell.

### Visitor Surface Structure

Visitor mode is always filtered through an audience lens:

- selected audience context
- visible persona presentation for that audience
- visible work feed for that audience
- visible relation affordances through persona only

If no audience-specific presentation exists, show a sparse “no presentation configured for this audience yet” state, not a generic full user page.

## New Frontend Contracts

Add a new local type file:

- `frontend/src/components/UserPage/types.ts`

Define these types as phase-1 frontend contracts.

### Core enums

```ts
export type UserPageMode = "owner-empty" | "owner-manage" | "visitor-view"

export type AudienceScope =
  | "public"
  | "trusted"
  | "collaborators"
  | "custom"

export type WorkVisibilityState = "draft" | "published"

export type PersonaPublicationState = "draft" | "published"
```

### User page view model

```ts
export interface UserPageViewModel {
  userId: string
  slug: string
  isOwner: boolean
  mode: UserPageMode
  primaryPersonaId: string | null
  selectedPersonaId: string | null
  selectedAudienceScope: AudienceScope
  selectedAudienceLabel: string
  workFeed: UserWorkFeedItem[]
  personas: UserPersonaSummary[]
  audiencePresentations: AudiencePresentationSummary[]
  relations: PersonaRelationSummary[]
}
```

### Work feed item

```ts
export interface UserWorkFeedItem {
  id: string
  title: string
  workType: "demo" | "prompt" | "story" | "page" | "artifact" | "other"
  summary: string | null
  status: WorkVisibilityState
  tags: string[]
  associatedPersonaIds: string[]
  intendedAudienceScopes: AudienceScope[]
  timestampLabel: string
  href: string | null
  isRepresentative: boolean
}
```

### Persona summary

```ts
export interface UserPersonaSummary {
  id: string
  name: string
  nickname: string | null
  shortBio: string | null
  longBio: string | null
  tags: WeightedTag[]
  publicationState: PersonaPublicationState
  associatedWorkCount: number
  isPrimary: boolean
  isVisibleInCurrentAudience: boolean
}
```

### Weighted tag

```ts
export interface WeightedTag {
  id: string
  label: string
  weight: number
  source: "user" | "system"
}
```

### Audience presentation

```ts
export interface AudiencePresentationSummary {
  id: string
  personaId: string
  audienceScope: AudienceScope
  audienceLabel: string
  headline: string
  framingText: string | null
  visibleWorkIds: string[]
  relationCallToAction:
    | "none"
    | "request_contact"
    | "invite_collaboration"
    | "follow_work"
}
```

### Relation summary

```ts
export interface PersonaRelationSummary {
  id: string
  sourcePersonaId: string
  targetLabel: string
  targetType: "persona" | "external"
  relationKind: "collaborator" | "trusted" | "learning_from" | "working_with"
  audienceScope: AudienceScope
  note: string | null
  status: "active" | "pending"
}
```

## Data Source Strategy

Add a new hook:

- `frontend/src/hooks/useUserPageViewModel.ts`

Responsibilities:

- resolve current auth state
- load persona library via existing `PersonaLibraryService`
- load page layout via existing `usePageEditor("user", userId)`
- derive owner vs visitor mode
- adapt current persona records into `UserPersonaSummary`
- provide placeholder/adapter work feed and relation data

Phase 1 data sourcing rules:

- Personas come from existing `PersonaLibraryService`.
- Primary persona is stored locally in page block content until backend support exists.
- Work feed is represented from seeded/mock/adapted data, not real recommender logic.
- Audience presentations are stored in page block content.
- Relations are represented in page block content or local draft state, not persisted in a backend relation table.

## Block Taxonomy

Add these new block types to the shared page system:

- `workFeed`
- `personaManager`
- `audiencePresentation`
- `relationshipManager`
- `primaryPersona`

### `workFeed` block

Purpose:
Represent the user’s work-interest/work-output flow.

Content contract:

```ts
{
  title?: string
  emptyMessage?: string
  items?: UserWorkFeedItem[]
}
```

Config contract:

```ts
{
  layout?: "stack"
  maxVisible?: number
  showPersonaBadges?: boolean
  showAudienceBadges?: boolean
}
```

Behavior:
- Owner sees all representative items.
- Visitor sees only items listed in the active audience presentation.

### `personaManager` block

Purpose:
Create, edit, tag, publish, and associate work to personas.

Content contract:

```ts
{
  personas?: UserPersonaSummary[]
}
```

Config contract:

```ts
{
  allowCreate?: boolean
  allowPrimarySelection?: boolean
  allowPublishing?: boolean
  allowTagEditing?: boolean
}
```

Behavior:
- Owner only.
- Opens sheets/dialogs for create/edit flows.
- Reuses `PersonaPicker` patterns where possible.

### `audiencePresentation` block

Purpose:
Manage and preview “what this user shows to this audience through this persona.”

Content contract:

```ts
{
  presentations?: AudiencePresentationSummary[]
}
```

Config contract:

```ts
{
  allowAudienceSwitching?: boolean
  showPreviewCards?: boolean
}
```

Behavior:
- Owner: manage all audience presentations and preview them.
- Visitor: render only the selected/derived audience presentation.

### `relationshipManager` block

Purpose:
Represent persona-mediated relations only.

Content contract:

```ts
{
  relations?: PersonaRelationSummary[]
}
```

Config contract:

```ts
{
  allowCreate?: boolean
  allowEditing?: boolean
  audienceScoped?: boolean
}
```

Behavior:
- Every create/edit action requires a source persona.
- No user-level relation affordance is displayed.

### `primaryPersona` block

Purpose:
Make explicit that a primary persona is optional and chosen, not inferred.

Content contract:

```ts
{
  primaryPersonaId?: string | null
  explanation?: string
}
```

Config contract:

```ts
{
  allowUnset?: boolean
  emphasizeOptionality?: boolean
}
```

Behavior:
- Owner only.
- If unset, show a neutral state.
- Never auto-select based on activity.

## Route Composition Defaults

Update the user page template in `pageTemplates.ts` so new user pages default to:

Primary column:
1. `identity`
2. `bio`
3. `primaryPersona`
4. `workFeed`
5. `audiencePresentation`

Auxiliary column:
1. `personaManager`
2. `relationshipManager`

Keep existing generic blocks available, but these become the default user-page composition.

## Interaction Flows

### 1. Create first persona

Entry point:
- `personaManager` block empty state

Flow:
- open sheet
- enter name
- optional short bio
- optional initial tags
- create in draft state
- offer “set as primary” checkbox, default unchecked
- return to persona list

Phase-1 persistence:
- create real persona record using existing persona create capability if feasible
- store user-page-only metadata in page block content

### 2. Mark primary persona

Entry point:
- `primaryPersona` block
- persona card action in `personaManager`

Rules:
- only one primary persona
- explicit set/unset
- no implicit fallback
- if primary persona is unpublished, owner still sees it as primary; visitors do not

### 3. Associate work with persona

Entry point:
- `personaManager` sheet
- `workFeed` item action

Flow:
- choose one or more personas
- assign audience scopes
- mark representative or not
- save to page content draft

### 4. Publish/modify persona presentation

Entry point:
- `audiencePresentation` block

Flow:
- choose persona
- choose audience scope
- author headline and framing text
- select visible work items
- choose relation CTA
- save preview

Rule:
- publication in phase 1 means “renderable in visitor mode,” not a backend publication workflow.

### 5. Visitor page view

Flow:
- route resolves user
- derive or default to `public` audience
- display matching audience presentation
- filter work feed to `visibleWorkIds`
- expose relation CTA only through persona context

### 6. Relation management

Entry point:
- `relationshipManager` block

Flow:
- choose source persona first
- choose target label/type
- choose relation kind
- choose audience scope
- optional note
- save

Rule:
- if no source persona is selected, creation action is disabled.

## Reuse From Existing Systems

### PersonaPicker reuse

Use `PersonaPicker` as the base selection primitive for:

- selecting primary persona
- assigning personas to work items
- choosing source persona for relation creation

Do not reuse it as the full management surface; wrap it inside user-page-specific sheets.

### Builder-pattern reuse

Model the phase-1 user page state like Builder drafts:

- stable local types
- normalization layer in one file
- route orchestrator composes surface state
- blocks read explicit typed content, not ad hoc blobs

Do not build a capability registry in phase 1.
Do structure types so a registry can be added later without breaking the contracts.

## Public APIs / Interfaces / Types

### Existing interfaces extended

Add block registrations in:

- `frontend/src/components/Page/registry/blockTypes.ts`
- `frontend/src/components/Page/registry/pageTemplates.ts`
- `frontend/src/components/Page/PageShell.tsx`

### New local-only interfaces

Add:

- `UserPageViewModel`
- `UserWorkFeedItem`
- `UserPersonaSummary`
- `AudiencePresentationSummary`
- `PersonaRelationSummary`
- `WeightedTag`

### No backend API changes in phase 1

Backend/API work is explicitly deferred.
Any missing fields required by the UI are stored in page block content or derived in the view-model adapter.

## File-Level Implementation Plan

### 1. Documentation artifact

Create:

- `frontend/docs/personas/users-pages-phase-1-implementation-spec.md`

Contents:
- problem framing
- current-state gap analysis
- route model
- block taxonomy
- view-model contracts
- interaction flows
- deferred backend items

### 2. View-model layer

Create:

- `frontend/src/components/UserPage/types.ts`
- `frontend/src/hooks/useUserPageViewModel.ts`

### 3. Blocks

Create:

- `frontend/src/components/Page/blocks/WorkFeedBlock.tsx`
- `frontend/src/components/Page/blocks/PersonaManagerBlock.tsx`
- `frontend/src/components/Page/blocks/AudiencePresentationBlock.tsx`
- `frontend/src/components/Page/blocks/RelationshipManagerBlock.tsx`
- `frontend/src/components/Page/blocks/PrimaryPersonaBlock.tsx`

Update exports in:

- `frontend/src/components/Page/blocks/index.ts`

### 4. Registry wiring

Update:

- `frontend/src/components/Page/registry/blockTypes.ts`
- `frontend/src/components/Page/registry/pageTemplates.ts`
- `frontend/src/components/Page/PageShell.tsx`

### 5. Route orchestration

Update:

- `frontend/src/routes/_layout/u.$slug.tsx`

Changes:
- replace current thin wrapper behavior with orchestration using `useUserPageViewModel`
- keep create-page flow
- pass owner/visitor-aware rendering context into blocks through block content/config or wrapper props

### 6. Supporting owner dialogs/sheets

Add user-page-specific management surfaces under:

- `frontend/src/components/UserPage/`

Recommended components:
- `UserPersonaEditorSheet.tsx`
- `UserWorkAssociationSheet.tsx`
- `AudiencePresentationSheet.tsx`
- `PersonaRelationSheet.tsx`

## Test Cases and Scenarios

### Unit tests

1. `useUserPageViewModel` returns `owner-empty` when owner has no page.
2. `useUserPageViewModel` returns `owner-manage` when page exists and viewer is owner.
3. `useUserPageViewModel` returns `visitor-view` for non-owner viewers.
4. Primary persona normalization allows exactly one selected ID or `null`.
5. Audience presentation filtering returns only work items listed in `visibleWorkIds`.
6. Relation creation validation rejects missing `sourcePersonaId`.
7. Persona tag normalization preserves weight bounds and source labels.
8. Visitor mode never renders owner-only management controls.

### Component tests

1. `PrimaryPersonaBlock` shows neutral empty state when unset.
2. `PersonaManagerBlock` shows create CTA when no personas exist.
3. `WorkFeedBlock` renders persona badges and audience badges when configured.
4. `AudiencePresentationBlock` previews multiple audience cards for owner mode.
5. `RelationshipManagerBlock` disables create action until a source persona is chosen.

### Route/integration scenarios

1. Owner visits `/u/:slug` with no page and sees create-page flow.
2. Owner with existing page sees work/persona/audience/relation surfaces.
3. Visitor sees only audience-filtered work feed and presentation.
4. Visitor never sees unpublished persona-management UI.
5. Changing selected audience preview in owner mode updates the visible filtered work preview.
6. Unsetting the primary persona keeps all persona records intact and removes only the designation.

## Acceptance Criteria

- Users page is no longer just a generic profile shell.
- The route presents Work, Personas, Audience Views, and Relations as distinct surfaces.
- Persona management is clearly owner-only.
- Visitor presentation is audience-scoped, not full-profile scoped.
- All relation actions are persona-mediated.
- Primary persona is explicit and optional.
- The implementation uses shared `PageShell` infrastructure, not a separate new framework.
- The design leaves clear seams for future backend work on grants, vouch, and work entities.

## Assumptions and Defaults

- `slug === userId` remains true in phase 1.
- “Work” is represented as a frontend view model and may point to existing demos/prompts/stories/pages without introducing a new backend `Work` entity yet.
- Audience scopes are frontend enums for now: `public`, `trusted`, `collaborators`, `custom`.
- Publishing in phase 1 means “included in visitor rendering,” not a durable backend publication state.
- Tags are weighted and editable in the UI contract now, even if current backend persona domains still exist underneath.
- Existing persona library APIs remain the source of truth for available personas.
- No vouch engine, directional grants, mutual reveal, or anonymity protocol is implemented in this phase.
- If a visitor audience cannot be derived, default to `public`.