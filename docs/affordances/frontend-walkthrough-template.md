# Frontend Functional Use Case Template

## Purpose

Use this template to document a frontend surface in a way that can be turned
into user walkthroughs, QA scripts, and future affordance registries.

This template is optimized for the current product shape:
- library/index surfaces
- detail/configuration surfaces
- compositional shells with panels/blocks
- runtime collaboration surfaces
- cross-surface journeys

## Documentation Rules

- Document what is implemented now, not only what is intended.
- Separate verified behavior from planned or partial behavior.
- Tie each use case to concrete UI affordances and route entry points.
- Record role gates, state gates, and integration dependencies explicitly.
- Keep one section per user goal; do not mix multiple goals into one walkthrough.

## Surface Header

```md
# <Surface Name>

Status: `stub | partial | verified`
Primary routes:
- `<route>`
- `<route>`

Primary files:
- `<path>`
- `<path>`

Related backend/services:
- `<path or endpoint>`
- `<path or endpoint>`

Last reviewed: `<YYYY-MM-DD>`
Reviewer: `<name>`
```

## Surface Summary

```md
## Summary

Short description of what this surface is for.

Primary user intents:
- `<intent 1>`
- `<intent 2>`
- `<intent 3>`

Primary object model:
- `<entity>`
- `<entity>`

Key integrations:
- `<surface/system>`
- `<surface/system>`
```

## Role and State Matrix

```md
## Role And State Matrix

| Dimension | Values | Notes |
| --- | --- | --- |
| User role | `owner`, `editor`, `viewer`, `system`, `anonymous` | Use actual product roles only |
| Object state | `<draft/published/active/inactive/etc.>` | Include states that change affordances |
| Data dependency | `<room attached>`, `<repo ready>`, `<story published>` | Preconditions that materially affect UX |
| Source of truth | `<frontend hook/service/backend rule>` | Where this rule is enforced today |
```

## Affordance Inventory

```md
## Affordance Inventory

| Affordance | User-visible control | Route or location | Preconditions | Outcome | Evidence |
| --- | --- | --- | --- | --- | --- |
| `<create item>` | `<button/dialog/menu>` | `<route/panel>` | `<auth/state>` | `<item created>` | `<file>` |
| `<edit item>` | `<button/dialog/menu>` | `<route/panel>` | `<auth/state>` | `<item updated>` | `<file>` |
| `<delete item>` | `<button/dialog/menu>` | `<route/panel>` | `<auth/state>` | `<item removed>` | `<file>` |
```

## High-Level Functional Use Cases

Repeat this block once per user goal.

```md
## Use Case: <User Goal>

Status: `stub | partial | verified`
Primary persona: `<owner | collaborator | operator | viewer>`
Priority: `P0 | P1 | P2`

### User Goal

What the user is trying to accomplish.

### Entry Points

- `<route>`
- `<dialog/button/deeplink>`

### Preconditions

- `<must be signed in>`
- `<must have entity access>`
- `<must have supporting object>`

### Primary Affordances

- `<main control or interaction>`
- `<secondary control>`

### Main Success Path

1. `<step>`
2. `<step>`
3. `<step>`

### Alternate Paths

- `<alternate path>`
- `<alternate path>`

### Outcomes

- `<observable success result>`
- `<resulting navigation/state change>`

### Empty, Error, and Blocked States

- Empty: `<what user sees>`
- Error: `<what user sees>`
- Blocked: `<permission/state denial>`

### Integration Touchpoints

- `<surface/system>`: `<how it intersects>`
- `<surface/system>`: `<how it intersects>`

### Evidence

- `<absolute file path>`
- `<absolute file path>`

### Walkthrough Readiness

- `ready`: can be turned directly into user walkthrough
- `partial`: flow exists but contains gaps, unclear permissioning, or weak UX
- `blocked`: missing implementation or missing validation
```

## Cross-Surface Journey Block

Use this when the user goal spans multiple surfaces.

```md
## Cross-Surface Journey: <Journey Name>

Status: `stub | partial | verified`

### Surfaces Involved

- `<surface>`
- `<surface>`
- `<surface>`

### Trigger

What starts the journey.

### Journey Steps

1. `<surface A action>`
2. `<surface B action>`
3. `<surface C action>`

### Integration Risks

- `<role mismatch>`
- `<state mismatch>`
- `<missing attachment/binding>`

### User Value

Why this journey matters.

### Walkthrough Candidate

`yes | no`
```

## Open Questions and Gaps

```md
## Open Questions And Gaps

- `<unknown or ambiguous behavior>`
- `<planned but not wired behavior>`
- `<needs backend validation>`
```

## Walkthrough Backlog

```md
## Walkthrough Backlog

| Walkthrough | Surface | Persona | Readiness | Notes |
| --- | --- | --- | --- | --- |
| `<name>` | `<surface>` | `<persona>` | `ready` | `<note>` |
| `<name>` | `<surface>` | `<persona>` | `partial` | `<note>` |
| `<name>` | `<surface>` | `<persona>` | `blocked` | `<note>` |
```

## Recommended Review Sequence

For this codebase, review in this order:

1. Index/library page
2. Detail/configuration page
3. Creation/edit dialogs
4. Runtime or panel composition hooks
5. Cross-surface entry/exit links
6. Permission and empty/error states
