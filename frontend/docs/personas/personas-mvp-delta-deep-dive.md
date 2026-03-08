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

Since the first draft of this deep dive, the backend has moved forward materially:

- `Persona` now has explicit visibility semantics (`private` vs `system`)
- `UserPersona` as owner-scoped entity
- `UserPersonaPresentation` as a separate audience-facing model
- access grants support `user_persona` and `persona_group` subjects
- persona-mediated collaboration groups/workspaces co-exist with user groups

That changes the state of the plan in an important way:

- the product data model is no longer blocked on its core persona entities
- the backend now has the right primitives for persona-mediated publication and persona-mediated collaboration
- the remaining MVP work is now primarily integration, audience-resolution policy, frontend adoption, and migration rather than greenfield modeling

## What Changed

### Persona model is now coherent enough for MVP

The backend now supports:

- `Persona.visibility` and `Persona.owner_user_id`
- `UserPersona` fields for authored persona metadata:
  - description
  - short bio
  - long bio
  - tags
  - publication state
  - primary designation
  - sort order
  - visual `presentation_json`
- `UserPersonaPresentation` as a separate model for:
  - audience scope
  - audience label
  - headline
  - framing text
  - visible work ids
  - relation call to action
  - presentation-level publication state
  - visual `presentation_json`



### Persona derivation semantics are now explicit

The model supports the intended product rule:

- `system` Personas are globally derivable
- `private` Personas are owner-scoped and only derivable by the user who owns them

### Persona-mediated collaboration is now represented in backend data

In addition to user groups, the backend exposes persona-mediated collaboration primitives (exported in frontend/src/client with types, schemas, and services)

- `PersonaGroup`
- `PersonaGroupMembership`
- access grants to:
  - `user_persona`
  - `persona_group`

The access resolver now considers:

- direct user grants
- direct user-persona grants
- legacy user-group grants
- persona-group grants
- project-derived grants flowing through those same subject types

the backend supports:

- users collaborating through personas
- projects/workspaces being shared to persona-defined groups
- attached resources inheriting access from those persona-mediated project grants

## Affordances Enabled

These are the main plan-level affordances unlocked by the recent implementation.

### 1. persisted persona-authored identity 

- persona identity is a backend-owned product entity through `UserPersona`

Affordance:

- user pages can evolve toward referencing personas rather than owning all persona state inline
- the same user persona can participate consistently across page, project, workspace, and access systems

### 2. Audience-facing presentation is separable from persona identity

Before:

- there was no stable backend distinction between "the persona" and "how that persona is presented to an audience"

Now:

- `UserPersonaPresentation` provides that distinction

Affordance:

- one persona can support multiple audience-facing views without collapsing identity and presentation into one record
- the frontend can shift from block-owned audience view JSON to backend-owned presentation records

### 3. Private personas are now a first-class concept

Before:

- persona authorship risked accidentally producing globally visible/shared entities

Now:

- `Persona.visibility` makes private vs system semantics explicit

Affordance:

- users can derive `UserPersona` state from private upstream personas without forcing those upstream personas into the global catalog
- the plan can support distinct user-authored personas without requiring public/global publication

### 4. Collaboration can now be mediated through personas instead of only accounts

Before:

- group and project access collapsed collaboration identity back to the raw user account

Now:

- persona groups and persona-subject grants coexist with legacy user-group grants

Affordance:

- a project/workspace can now be shared to a persona-mediated group
- access can be granted directly to a specific user persona
- attached resources can inherit those project/workspace grants

This is a major step toward the broader product vision where users associate through personas rather than only through account-level identity.

### 5. The backend supports coexistence 

The implementation intentionally leaves the concurrent user path in place:

- user `group` access still works
- persona-mediated `persona_group` access now works in parallel

Affordance:

- frontend and product flows can migrate incrementally
- workspace/project features do not need to pause until every legacy group/share path is replaced
- the repo can support mixed-mode rollout while the persona system is integrated into more surfaces

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

### 1. Frontend user pages still do not consume the new backend persona model

The backend model now exists, but the frontend user-page runtime/composer still largely hydrates from page block content.

Consequence:

- the old page-JSON source-of-truth behavior still exists in the frontend layer
- the main remaining gap is now adapter/integration work rather than missing backend entities

### 2. Audience views exist as authored content, but audience resolution is not real

Current state:

- `UserPersonaPresentation` now exists in backend data
- frontend runtime still does not resolve viewer audience from a canonical access/relationship policy

Not implemented:

- determine the viewer's actual audience scope from relationship/access state
- select the correct presentation for the visiting user
- support per-visitor or per-group audience assignment in backend data

Consequence:

- the data shape is now available
- the runtime selection policy is still a remaining product/implementation decision

This remains the biggest product gap for the "disassociated from each other for other users" requirement.

### 3. Visitor-visible persona isolation is representational, not enforced

The backend now has the right publication entities, but the frontend visitor flow has not yet been rewired to them.

Consequence:

- this is no longer a schema problem
- it is now a runtime integration and policy-enforcement problem

### 4. Work is still page-authored metadata, not a canonical work system

NOTE: Work is still in design. Keep current system working for MVP. 

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

### 5. Persona-mediated collaboration exists, but frontend workspaces/projects have not adopted it yet

The backend now supports persona groups and persona-mediated grants, but this is still backend-first.

Consequence:

- the plan now has viable collaboration primitives
- the remaining work is exposing them through frontend workflows and aligning project/workspace UX to those primitives

## High-Priority Mismatches Against MVP Needs

If the MVP requirement is:

- a user can create multiple distinct personas
- a user can manage them
- other users do not see those personas collapsed into one single identity

then these are the highest-priority remaining gaps.

### P0: Rewire frontend user-page composition and runtime to the backend persona contracts

This is now the most important item.

The key backend records exist. The MVP now depends on:

- reading `UserPersona` from backend data using exported client services 
- reading `UserPersonaPresentation` from backend data using exported client services
- persisting changes through those APIs rather than only through page block JSON

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

### P1: Integrate persona-group collaboration into project/workspace UX

The backend primitives now exist, but the frontend still needs:

- persona-group creation and management flows
- project/workspace sharing UI that can target persona groups and user personas
- clear display of why a user has access through a particular persona/group path

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

#### 1. Add migrations and tests for the new persona, presentation, and persona-group models

The shape now exists in backend code, but the remaining backend-critical work is operationalization:

- alembic migrations
- CRUD and route test coverage
- integrity constraints where still only service-enforced

#### 2. Define and implement audience resolution policy

The backend now stores audience-facing presentations, but the runtime still needs a deterministic policy for mapping viewer -> audience scope.

#### 3. Extend collaboration/audience policy from backend primitives to product rules

The system now has persona groups and persona-mediated grants. Product still needs to decide:

- how those groups map into audience scopes, if at all
- whether non-public persona presentations are driven by access grants, relation state, group membership, or a simpler MVP rule

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

### Risk 1: Frontend/backend drift during migration

The backend model has advanced faster than the frontend composition/runtime layer.

### Risk 2: Audience claims still exceed runtime policy

The storage model now exists, but viewer-to-audience resolution is still not finalized.

### Risk 3: Persona-group access may outpace frontend explanation

The backend now supports persona-mediated access paths; frontend surfaces may lag in explaining why a user has access.

### Risk 4: Runtime isolation is still soft until frontend adopts backend publication data

The new backend entities reduce this risk, but they do not remove it until the frontend uses them.

## Bottom Line

The user-page personas system is now beyond the stage of being only a strong prototype.

The backend now has the core data model required for:

1. real backend-owned user persona records
2. real backend-owned audience presentation records
3. persona-mediated collaboration and access-control primitives

That moves the plan forward in a concrete way:

- distinct personas can now exist as durable backend entities
- audience-facing presentation has a backend home
- projects/workspaces can now be shared through persona-mediated groups rather than only raw user groups

The remaining MVP blockers are now:

1. frontend adoption of the new backend contracts
2. explicit audience-resolution policy
3. migrations, tests, and rollout integration

That is a much stronger position than the earlier state, where the main blocker was the absence of the underlying product model itself.
