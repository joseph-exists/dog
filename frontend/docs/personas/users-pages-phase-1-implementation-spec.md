# Users Pages Phase 1 Implementation Spec

## Summary

Phase 1 implements Users pages as a frontend-first extension of the existing `PageShell` system. The new slice is organized around four coordinated surfaces:

- Work flow
- Persona management
- Audience views
- Persona-mediated relations

This phase does not implement vouch, privacy grants, anonymous publication, or backend identity restructuring. It does establish the route orchestration, local view-model contract, block taxonomy, and persisted page-content seams needed to test the model in the frontend.

## Current-State Gap

The current user route at [`frontend/src/routes/_layout/u.$slug.tsx`](/home/josep/dog/frontend/src/routes/_layout/u.$slug.tsx) only gates between create-page, not-found, and a generic `PageShell("user", userId)` render. The persona system exists, but it is still library-centric and not yet expressed as a user-page surface with audience discrimination or persona-mediated relations.

The implementation in this phase bridges that gap by:

- introducing a typed user-page view model
- adding user-specific blocks to the shared page registry
- keeping user-page metadata in block content JSON
- reusing the existing persona library APIs only where they already fit

## Route Model

Route:

- `/_layout/u/$slug`

Phase-1 assumptions:

- `slug === userId`
- owner and visitor share the same route
- owner-specific mutation happens through existing page edit mode

Derived page modes:

- `owner-empty`
- `owner-manage`
- `visitor-view`

The route now uses `useUserPageViewModel(slug)` to derive:

- ownership
- page existence
- persona library data for the owner
- persisted user-page block data
- a normalized `UserPageViewModel`

## View-Model Contract

Primary local contracts live in [`frontend/src/components/UserPage/types.ts`](/home/josep/dog/frontend/src/components/UserPage/types.ts).

Key types:

- `UserPageViewModel`
- `UserWorkFeedItem`
- `UserPersonaSummary`
- `AudiencePresentationSummary`
- `PersonaRelationSummary`
- `WeightedTag`

Normalization and derived-state helpers live in [`frontend/src/hooks/useUserPageViewModel.ts`](/home/josep/dog/frontend/src/hooks/useUserPageViewModel.ts).

Important behavior:

- persona library data is only loaded for the page owner
- primary persona is stored in the `primaryPersona` block content
- work feed, audience presentations, and relations are stored in their respective block contents
- visitor-facing work filtering is derived from the active audience presentation

## Block Taxonomy

Added block types:

- `primaryPersona`
- `workFeed`
- `personaManager`
- `audiencePresentation`
- `relationshipManager`

These are registered in:

- [`frontend/src/components/Page/registry/blockTypes.ts`](/home/josep/dog/frontend/src/components/Page/registry/blockTypes.ts)
- [`frontend/src/components/Page/registry/pageTemplates.ts`](/home/josep/dog/frontend/src/components/Page/registry/pageTemplates.ts)
- [`frontend/src/components/Page/PageShell.tsx`](/home/josep/dog/frontend/src/components/Page/PageShell.tsx)

Default user template:

Primary column:

1. `identity`
2. `bio`
3. `primaryPersona`
4. `workFeed`
5. `audiencePresentation`

Auxiliary column:

1. `personaManager`
2. `relationshipManager`

## Owner Interaction Flows

### Persona management

`PersonaManagerBlock` uses [`UserPersonaEditorSheet`](/home/josep/dog/frontend/src/components/UserPage/UserPersonaEditorSheet.tsx) to:

- create a persona via existing persona APIs
- add it to the current user’s persona library
- store user-page-specific metadata locally in page block content
- optionally set it as primary

### Work association

`WorkFeedBlock` uses [`UserWorkAssociationSheet`](/home/josep/dog/frontend/src/components/UserPage/UserWorkAssociationSheet.tsx) to:

- add work items
- associate personas
- assign audience scope
- mark representative work

### Audience presentation

`AudiencePresentationBlock` uses [`AudiencePresentationSheet`](/home/josep/dog/frontend/src/components/UserPage/AudiencePresentationSheet.tsx) to:

- choose a persona
- define an audience scope and label
- select visible work
- author headline and framing text
- choose a relation CTA

### Relation management

`RelationshipManagerBlock` uses [`PersonaRelationSheet`](/home/josep/dog/frontend/src/components/UserPage/PersonaRelationSheet.tsx) to:

- choose a source persona first
- describe the target
- classify the relation
- assign audience scope
- store relation metadata in block content

## Visitor Rendering Rules

Visitors do not see owner-management controls.

Instead, the page renders:

- audience-filtered work
- the active audience presentation
- persona-mediated relation affordances

If no audience presentation exists for the selected scope, the visitor sees a sparse empty state rather than a generic user profile.

## Deferred Backend Work

Explicitly deferred from phase 1:

- directional visibility grants
- vouch computation
- anonymous publication / claiming flows
- a dedicated backend `Work` entity
- persisted backend primary-persona support
- persona relation backend tables and APIs

## Validation Notes

This phase is validated by:

- TypeScript integration across `PageShell`, route orchestration, and block contracts
- unit coverage for normalization helpers in [`frontend/tests-unit/user-page-view-model.spec.ts`](/home/josep/dog/frontend/tests-unit/user-page-view-model.spec.ts)

The current implementation is intentionally opinionated about edit-mode gating: owner mutations are performed through the existing page editing lifecycle so user-page metadata remains persisted in page block content rather than floating in transient route state.
