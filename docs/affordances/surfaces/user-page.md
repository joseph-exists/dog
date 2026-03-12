# User Page

Status: `partial`
Primary routes:
- `/u/$slug`
- `/u/$slug/compose`

Primary files:
- `/home/josep/dog/frontend/src/routes/_layout/u.$slug.index.tsx`
- `/home/josep/dog/frontend/src/routes/_layout/u.$slug.compose.tsx`
- `/home/josep/dog/frontend/src/hooks/useUserPageViewModel.ts`
- `/home/josep/dog/frontend/src/services/userPersonaService.ts`
- `/home/josep/dog/frontend/src/services/pageService.ts`
- `/home/josep/dog/frontend/src/components/UserPage/builder/UserPageAudiencePreviewPanel.tsx`

Related backend/services:
- `/home/josep/dog/backend/app/api/routes/user_personas.py`
- `/home/josep/dog/backend/app/api/routes/pages.py`
- `/home/josep/dog/backend/app/api/routes/access.py`
- `/home/josep/dog/backend/app/services/access_control.py`

Last reviewed: `2026-03-10`
Reviewer: `Codex`

## Summary

The user page is now the primary authored surface for persona-shaped identity,
audience-specific presentation, and visitor-facing publication.

Primary user intents:
- create and manage multiple distinct personas
- define audience-specific views of those personas
- publish a visitor-safe snapshot without collapsing identity into one profile

Primary object model:
- `Page`
- `UserPersona`
- `UserPersonaPresentation`
- `AccessGrant`

Key integrations:
- `Projects`
- `Persona Groups`
- `Access / sharing`
- `PageShell`

## Role And State Matrix

| Dimension | Values | Notes |
| --- | --- | --- |
| User role | `owner`, `viewer`, `anonymous`, `system` | only owner can access composer |
| Object state | `page missing`, `draft`, `published`, `audience-matched`, `audience-unmatched` | visitor outcome depends on publication and audience match |
| Data dependency | `published user persona`, `published audience view`, `page snapshot saved`, `page grant present` | these materially change runtime output |
| Source of truth | `useUserPageViewModel`, `UserPersonaService`, `PageService`, backend audience resolver | authoring and runtime are intentionally hybrid for MVP |

## Affordance Inventory

| Affordance | User-visible control | Route or location | Preconditions | Outcome | Evidence |
| --- | --- | --- | --- | --- | --- |
| create page | `Create Page` button/dialog | `/u/$slug`, `/u/$slug/compose` | signed in as owner, no page yet | page layout is created and saved | [/home/josep/dog/frontend/src/routes/_layout/u.$slug.index.tsx](/home/josep/dog/frontend/src/routes/_layout/u.$slug.index.tsx#L28) |
| open composer | `Open Composer` button | `/u/$slug` | owner, page exists | navigates to composer | [/home/josep/dog/frontend/src/routes/_layout/u.$slug.index.tsx](/home/josep/dog/frontend/src/routes/_layout/u.$slug.index.tsx#L114) |
| create/edit persona | `Create Persona`, edit icon, sheet | `/u/$slug/compose` | owner, page exists | backend `UserPersona` is created or updated | [/home/josep/dog/frontend/src/components/Page/blocks/PersonaManagerBlock.tsx](/home/josep/dog/frontend/src/components/Page/blocks/PersonaManagerBlock.tsx#L59) |
| create/edit audience view | `Add View`, edit icon, sheet | `/u/$slug/compose` | owner, page exists, saved persona | backend `UserPersonaPresentation` is created or updated | [/home/josep/dog/frontend/src/components/Page/blocks/AudiencePresentationBlock.tsx](/home/josep/dog/frontend/src/components/Page/blocks/AudiencePresentationBlock.tsx#L67) |
| set primary persona | primary selection in persona flow | `/u/$slug/compose` | owner, persona exists | primary persona block and backend state align | [/home/josep/dog/frontend/src/components/Page/blocks/PrimaryPersonaBlock.tsx](/home/josep/dog/frontend/src/components/Page/blocks/PrimaryPersonaBlock.tsx#L42) |
| preview audience outcome | audience preview panel | `/u/$slug/compose` | owner, page exists | simulated published visitor result is shown | [/home/josep/dog/frontend/src/components/UserPage/builder/UserPageAudiencePreviewPanel.tsx](/home/josep/dog/frontend/src/components/UserPage/builder/UserPageAudiencePreviewPanel.tsx#L1) |
| grant page audience access | audience access card | `/u/$slug/compose` | owner, page saved | page grant added for `user`, `user_persona`, `group`, or `persona_group` | [/home/josep/dog/frontend/src/routes/_layout/u.$slug.compose.tsx](/home/josep/dog/frontend/src/routes/_layout/u.$slug.compose.tsx#L347) |
| publish visitor snapshot | `Save User Page` | `/u/$slug/compose` | owner, valid draft | page snapshot is rebuilt from published personas/presentations | [/home/josep/dog/frontend/src/services/userPersonaService.ts](/home/josep/dog/frontend/src/services/userPersonaService.ts#L176) |
| view runtime page | page shell runtime | `/u/$slug` | page exists; audience may be anonymous or granted | runtime renders from snapshot plus resolved audience | [/home/josep/dog/frontend/src/hooks/useUserPageViewModel.ts](/home/josep/dog/frontend/src/hooks/useUserPageViewModel.ts#L553) |

## Use Case: Author Distinct Personas For One User

Status: `verified`
Primary persona: `owner`
Priority: `P0`

### User Goal

Create multiple user-owned personas without collapsing them into one undifferentiated profile.

### Entry Points

- `/u/$slug/compose`
- `Create Persona`

### Preconditions

- must be signed in as the page owner
- page must exist

### Primary Affordances

- persona manager block
- user persona editor sheet
- primary persona designation

### Main Success Path

1. Owner opens composer.
2. Owner creates a persona or edits an existing persona.
3. Persona persists to backend `UserPersona`.
4. Composer shows publication state and snapshot inclusion cues.

### Alternate Paths

- owner creates persona before selecting a primary persona
- owner keeps persona in `draft` and excludes it from visitor snapshot

### Outcomes

- multiple distinct personas are persisted
- primary persona remains explicit and reversible

### Empty, Error, and Blocked States

- Empty: persona manager invites owner to create first persona
- Error: backend validation or missing backend reference toast
- Blocked: non-owner cannot access composer

### Integration Touchpoints

- `Pages`: snapshot is rebuilt on save
- `Audience Views`: persona identity anchors audience-specific presentation
- `Projects`: published personas are discoverable for collaboration targeting

### Evidence

- [/home/josep/dog/frontend/src/components/Page/blocks/PersonaManagerBlock.tsx](/home/josep/dog/frontend/src/components/Page/blocks/PersonaManagerBlock.tsx#L1)
- [/home/josep/dog/backend/app/api/routes/user_personas.py](/home/josep/dog/backend/app/api/routes/user_personas.py#L1)

### Walkthrough Readiness

- `ready`

## Use Case: Author Audience-Specific Persona Views

Status: `verified`
Primary persona: `owner`
Priority: `P0`

### User Goal

Define different audience-facing presentations of a persona and explicitly control what work is visible in each.

### Entry Points

- `/u/$slug/compose`
- `Add View`

### Preconditions

- owner is signed in
- at least one saved persona exists

### Primary Affordances

- audience presentation sheet
- visible work selection
- publication state control
- audience outcome preview

### Main Success Path

1. Owner creates or edits an audience view.
2. Owner selects persona, scope, visible work, and publication state.
3. View persists to backend `UserPersonaPresentation`.
4. Preview panel shows what a published visitor would receive.

### Alternate Paths

- owner creates a `custom` audience view keyed to a specific target id
- owner leaves view in draft to stage later publication

### Outcomes

- audience view is persisted
- work visibility is scoped to that presentation
- draft vs published state is visible in authoring UI

### Empty, Error, and Blocked States

- Empty: no view exists for current audience lens
- Error: missing saved persona or presentation conflict
- Blocked: no work exists to attach yet

### Integration Touchpoints

- `Work Feed`: visible work ids drive runtime filtering
- `Access`: audience scopes become meaningful only when grants or keys exist
- `Pages`: only published views serialize into visitor snapshot

### Evidence

- [/home/josep/dog/frontend/src/components/Page/blocks/AudiencePresentationBlock.tsx](/home/josep/dog/frontend/src/components/Page/blocks/AudiencePresentationBlock.tsx#L1)
- [/home/josep/dog/frontend/src/components/UserPage/AudiencePresentationSheet.tsx](/home/josep/dog/frontend/src/components/UserPage/AudiencePresentationSheet.tsx#L1)

### Walkthrough Readiness

- `ready`

## Use Case: Publish A Visitor-Safe Persona Page

Status: `partial`
Primary persona: `owner`
Priority: `P0`

### User Goal

Save a page such that visitors see only the published persona and presentation state that matches their audience.

### Entry Points

- `/u/$slug/compose`
- `Save User Page`

### Preconditions

- owner is signed in
- page exists
- draft passes blocking validation

### Primary Affordances

- save bar
- validation panel
- audience preview panel

### Main Success Path

1. Owner edits personas, audience views, and layout.
2. Owner reviews validation and audience preview.
3. Owner saves page.
4. Snapshot is rebuilt from published persona and presentation records.
5. Visitor runtime reads snapshot plus resolved audience.

### Alternate Paths

- owner saves layout changes while leaving some personas/views in draft
- owner publishes only public and trusted layers first

### Outcomes

- saved page content becomes the visitor contract
- unpublished personas and views stay out of the visitor snapshot

### Empty, Error, and Blocked States

- Empty: page not yet created
- Error: validation issues block save or backend save fails
- Blocked: unresolved references in draft

### Integration Touchpoints

- `UserPersonaService.buildPublishedSnapshot`
- backend audience resolution endpoint
- visitor runtime view model

### Evidence

- [/home/josep/dog/frontend/src/services/userPersonaService.ts](/home/josep/dog/frontend/src/services/userPersonaService.ts#L176)
- [/home/josep/dog/frontend/src/hooks/useUserPageViewModel.ts](/home/josep/dog/frontend/src/hooks/useUserPageViewModel.ts#L553)

### Walkthrough Readiness

- `partial`: the core path is real, but operators still need stronger downstream explanation of why a specific visitor matched a specific access path

## Use Case: Grant Non-Public Access To A User Page

Status: `partial`
Primary persona: `owner`
Priority: `P1`

### User Goal

Allow specific users, personas, groups, or persona groups to resolve into non-public audience views on the page.

### Entry Points

- `/u/$slug/compose`
- audience access card

### Preconditions

- owner is signed in
- page has been saved at least once

### Primary Affordances

- grant subject type selector
- owned persona/group selectors
- published collaborator persona discovery
- grant list and revoke controls

### Main Success Path

1. Owner opens audience access panel.
2. Owner selects a target subject type.
3. Owner grants page access.
4. Runtime audience resolver can match that visitor into `trusted` or `collaborators`.

### Alternate Paths

- owner grants direct access to a collaborator persona
- owner uses custom audience keys for a more specific targeted view

### Outcomes

- page has explicit non-public audience grants
- audience preview can simulate those targeted states

### Empty, Error, and Blocked States

- Empty: no grants yet; page resolves to public by default
- Error: grant upsert/revoke failure
- Blocked: page must exist before access can be managed

### Integration Touchpoints

- `AccessService`
- `Persona Groups`
- published collaborator persona discovery

### Evidence

- [/home/josep/dog/frontend/src/routes/_layout/u.$slug.compose.tsx](/home/josep/dog/frontend/src/routes/_layout/u.$slug.compose.tsx#L347)
- [/home/josep/dog/backend/app/services/access_control.py](/home/josep/dog/backend/app/services/access_control.py#L279)

### Walkthrough Readiness

- `partial`: the mechanism is present, but the operator mental model still depends on reading labels like `trusted` and `collaborators` correctly

## Cross-Surface Journey: Author Page Identity And Reuse It In Collaboration

Status: `partial`

### Surfaces Involved

- `User Page`
- `Projects`
- `Persona Groups`

### Trigger

User wants a persona authored on their page to participate in a shared workspace or project.

### Journey Steps

1. User creates and publishes one or more personas on `/u/$slug/compose`.
2. User discovers collaborator personas or creates a persona group in project access UI.
3. User grants a project to a persona group or direct user persona.
4. Shared project/resource access resolves through persona-mediated paths.

### Integration Risks

- project/resource surfaces still explain access reasons inconsistently
- project ownership and share-management remain user-account anchored
- richer attached-resource capability inheritance is still a future layer

### User Value

Lets a user shape identity and collaboration through personas rather than only through the raw user account.

### Walkthrough Candidate

`yes`

## Open Questions And Gaps

- visitor runtime now resolves audience, but downstream explanation is still weaker than the underlying model
- page audience labels are operationally meaningful, but still somewhat overloaded for non-technical users
- current prototype does not yet turn persona-mediated page access into a broader notification or invitation lifecycle
- the next significant unlock would be deeper project/resource explanation rather than more page CRUD

## Walkthrough Backlog

| Walkthrough | Surface | Persona | Readiness | Notes |
| --- | --- | --- | --- | --- |
| create first persona page | `User Page` | `owner` | `ready` | strongest current authored persona flow |
| publish two personas with different audience views | `User Page` | `owner` | `ready` | demonstrates persona separation clearly |
| grant trusted page access to a collaborator persona | `User Page` | `owner` | `partial` | mechanism exists; explanation needs polish |
| compare public vs collaborators preview outcomes | `User Page` | `owner` | `ready` | strong operator-facing walkthrough |

