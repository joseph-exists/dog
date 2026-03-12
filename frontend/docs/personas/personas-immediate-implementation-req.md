# Personas Immediate Implementation Requirements

This document turns the current product direction into an immediate engineering contract.

It supersedes vague "audience" language with explicit MVP requirements, explicit ownership of responsibilities, and a concrete next-slice sequence.

## Current Status

Implemented:

- owner persona authoring uses backend `UserPersona`
- owner audience-view authoring uses backend `UserPersonaPresentation`
- composer save now builds a published visitor snapshot from backend-authored persona state
- user-page runtime now resolves the active persona/audience presentation deterministically
- user-page runtime now consumes a backend audience-resolution result instead of relying only on local fallback ordering
- owner composer now supports page audience grants for `user`, `user_persona`, `group`, and `persona_group`
- owner composer now includes audience-outcome preview and clearer publication-state inclusion cues
- project and page audience flows now support published collaborator-persona discovery
- project access UI now supports grants to `user_persona` and `persona_group`
- project access UI now supports basic persona-group creation and membership addition
- project access UI now supports searchable selection for owned personas, persona groups, and legacy groups

Remaining from this contract:

- broader access-path explanation in collaboration UI
- deeper persona-group/project workflow polish

## Non-Negotiable MVP Requirements

### A. Lock the MVP publication model

MVP uses page snapshot publication.

Contract:

- backend `UserPersona` and `UserPersonaPresentation` records are authoritative for owner authoring
- the saved page layout is the visitor contract
- publish/save must serialize a visitor-safe snapshot into page block content
- visitor runtime reads the saved page snapshot, not owner-only editing data

Implication:

- the hybrid system is intentional for MVP
- it is not acceptable for the snapshot to be accidental, stale, or undefined

### B. Lock the MVP audience model

MVP must support real non-public resolution now.

The required MVP scopes are:

- `public`
- `private`
- `group`

These are product scopes, not suggestive labels.

Contract:

- `public`: visible to any visitor
- `private`: visible only to explicitly granted individual viewers
- `group`: visible only to viewers who match one of the explicitly assigned groups

We will map these backend groupings appropriately to the existing:

- `trusted`
- `collaborators`

and add the required additional entities.

- first-presentation fallback


### C. Update composer UI/UX

Composer behavior must truthfully reflect the current persistence model.

Contract:

- persona edits save immediately to backend entities
- audience-view edits save immediately to backend entities
- page layout and other page-owned constructs remain draft-until-save
- the UI must clearly distinguish these two save behaviors

### D. Finish the visitor-safe snapshot contract

The visitor snapshot must be intentional and filtered.

Contract:

- only published personas may enter the snapshot
- only published presentations may enter the snapshot
- only the work explicitly visible for the allowed audience may be renderable through that presentation
- unpublished or unauthorized persona metadata must never leak into the visitor snapshot

## Exact Contracts Required

## 1. Audience Resolution Contract

Engineering must implement one deterministic resolver for user-page visitors.

Required output:

```ts
type ResolvedUserPageAudience = {
  scope: "public" | "private" | "group"
  matchedUserGrantIds: string[]
  matchedGroupIds: string[]
}
```

Resolution rules:

1. owner of the page is treated as fully privileged author/viewer and bypasses audience filtering in compose/manage mode
2. if the viewer has an explicit individual grant, resolved scope is `private`
3. else if the viewer matches one or more granted groups, resolved scope is `group`
4. else resolved scope is `public`

Precedence:

- `private` overrides `group`
- `group` overrides `public`

Required inputs:

- authenticated viewer user id, if present
- viewer-owned `UserPersona` ids
- viewer persona-group memberships
- page/presentation grants for direct users, direct user personas, and persona groups

Note:

- legacy `group` grants may continue to participate during coexistence, but MVP contracts should be written in terms of persona-aware grants

## 2. Presentation Targeting Contract

`UserPersonaPresentation` must stop being treated as free-floating display content.

Required MVP interpretation:

- `audience_scope == "public"` means globally visible
- `audience_scope == "private"` means directly granted viewers only
- `audience_scope == "group"` means viewers matching the referenced group only

Required field use:

- `audience_scope`: `public | private | group`
- `audience_key`:
  - null for `public`
  - null for `private`
  - required for `group`, containing the target `persona_group.id`

If current enums do not match this contract, they must be updated now. Current MVP semantic placeholders can be extended or overwritten.

## 3. Snapshot Serialization Contract

On page save/publish, the system must build a visitor-safe snapshot from backend-owned persona entities.

Required snapshot content:

- `primaryPersona.primaryPersonaId`
- `personaManager.personas`
- `audiencePresentation.presentations`
- existing `workFeed.items`
- existing relation snapshot only if relations remain in MVP scope

Required filtering:

- only `UserPersona.publication_state == "published"` personas serialize
- only `UserPersonaPresentation.publication_state == "published"` presentations serialize
- if a presentation references an unpublished persona, it does not serialize
- if primary persona is unpublished or absent from serialized personas, primary persona becomes null in snapshot

Required persona snapshot fields:

- base persona id used by page/runtime references
- `userPersonaId`
- visitor-safe name/nickname/bio/tags/publication state

Required presentation snapshot fields:

- presentation id
- `userPersonaId`
- referenced persona id
- scope
- `audience_key`
- label
- headline
- framing text
- visible work ids
- relation CTA

## 4. Visitor Runtime Contract

Visitor runtime must render from the page snapshot plus resolved audience, not from owner-only backend edit data.

Required runtime algorithm:

1. load saved page snapshot
2. resolve audience for current viewer
3. select the best matching serialized presentation in precedence order:
   - `private`
   - `group`
   - `public`
4. render only work included in that presentation's visible work ids
5. if no presentation matches, render the explicit sparse empty state

The runtime must not:

- select the first presentation by array order
- silently fall back from unauthorized non-public content
- expose unpublished persona content just because it exists in backend authoring data

## System Responsibilities

### Backend responsibilities

- support the audience-resolution inputs needed above
- support group and direct-grant resolution for page visitors
- expose or enable the data needed to build the visitor snapshot
- persist publication-state-aware persona and presentation records

### Frontend responsibilities

- use backend entities for owner authoring
- serialize the filtered snapshot on save/publish
- render visitors strictly from snapshot plus resolved audience
- make composer save semantics explicit

## Immediate Sequence

## Slice 1: Replace placeholder audience scopes with real MVP scopes

Required work:

- update frontend `AudienceScope` contract to `public | private | group`
- update backend presentation/API usage to match
- update composer UI labels and controls

Deliverable:

- no remaining ambiguous audience labels in MVP surfaces

## Slice 2: Implement page audience grants and resolver

Required work:

- define how a user page stores direct viewer grants and group grants
- implement audience resolution using:
  - direct user grants
  - direct user-persona grants
  - persona-group grants
  - legacy user-group grants only where coexistence still requires them

Deliverable:

- one deterministic `ResolvedUserPageAudience`

## Slice 3: Implement snapshot serialization on save/publish

Required work:

- pull current backend personas/presentations during save
- filter to published visitor-safe content
- write snapshot into page blocks
- clear invalid primary persona references during serialization

Deliverable:

- saved page content is now the intentional visitor publication contract

## Slice 4: Rewire visitor runtime to the resolved audience + snapshot

Required work:

- stop using first-presentation fallback behavior
- resolve visitor audience first
- select matching snapshot presentation by precedence

Deliverable:

- visitor persona isolation is enforced by runtime behavior, not just represented in authoring UI

## Slice 5: Update composer UX copy and save affordances

Required work:

- label immediate-save persona operations clearly
- keep layout/page-shell draft save separate
- remove misleading language that implies all edits are staged together

Deliverable:

- product behavior is understandable without engineering explanation

## Out of Scope For This Immediate Slice

- vouch
- advanced relation automation
- canonical backend work graph
- full persona-mediated workspace UX
- replacing page snapshot publication with backend canonical publication

## Definition of Done For Personas MVP

The MVP is done when all of the following are true:

- a user can create multiple personas
- those personas are authored through backend product entities
- a user can create public, private, and group-scoped presentations
- the system can deterministically resolve which audience a visitor belongs to
- saved page content contains an intentional visitor-safe snapshot
- visitor runtime shows only the presentation and work allowed for that audience
- composer UI truthfully communicates which edits save immediately and which remain draft state
