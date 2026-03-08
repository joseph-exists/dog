# Agent Project Inheritance Implementation Spec

Status: `proposed`
Last reviewed: `2026-03-08`
Related notes: `docs/assemblage/agent-derivation.md`

## Purpose

Define the minimum backend semantics for project-derived access to agent
resources, where an agent resource is a `UserAgentConfig` attached to a
`Project` via `project_resources`.

This spec is intentionally narrow:
- project attachment makes agents discoverable in a project context
- project inheritance may grant `view` and `use`
- project inheritance does not grant agent configuration ownership or share management

## Resource Identity

- Canonical project resource:
  - `resource_type="agent"`
  - `resource_id=<UserAgentConfig.id>`
- Project attachment refers to the stored agent configuration object, not:
  - a room participant binding
  - a runtime agent instance
  - a prompt config

## Protected Operations

The backend should reason about four distinct operations on an agent resource:

- `view`
  - Read sanitized metadata for discovery and selection.
- `use`
  - Invoke or select the agent in a room, demo, or project-scoped workflow.
- `edit`
  - Modify the underlying `UserAgentConfig`.
- `manage`
  - Delete the config, change direct sharing, or alter ownership-sensitive bindings.

`use` and `edit` must remain separate. A collaborator being allowed to run an
agent in a project must not imply permission to change its configuration.

## Derived Agent Capabilities

The implementation should expose these derived capability checks:

- `can_view_agent_in_project`
- `can_use_agent_in_project`
- `can_edit_agent_config`

Recommended meaning:

- `can_view_agent_in_project`
  - User may see the agent in project rosters, selectors, and detail summaries.
- `can_use_agent_in_project`
  - User may select or invoke the agent from eligible project-linked surfaces.
- `can_edit_agent_config`
  - User may mutate the `UserAgentConfig` itself.

## Backend Permission Matrix

| Subject basis | View agent | Use agent | Edit config | Manage config |
| --- | --- | --- | --- | --- |
| Superuser | yes | yes | yes | yes |
| Agent owner | yes | yes | yes | yes |
| Direct agent viewer grant | yes | no | no | no |
| Direct agent editor grant | yes | yes | yes | no |
| Project viewer via attached project | yes | no | no | no |
| Project editor via attached project | yes | yes | no | no |
| Project manager/owner on attached project only | yes | yes | no | no |
| No matching grant | no | no | no | no |

Notes:

- Project-derived access does not grant `edit` or `manage` on the agent config.
- Direct agent grants outrank project-derived grants.
- Owner and superuser remain absolute overrides.

## Capability Mapping

Map resolved roles and relationships into derived capabilities as follows:

| Basis | `can_view_agent_in_project` | `can_use_agent_in_project` | `can_edit_agent_config` |
| --- | --- | --- | --- |
| Superuser | yes | yes | yes |
| Agent owner | yes | yes | yes |
| Direct agent viewer | yes | no | no |
| Direct agent editor | yes | yes | yes |
| Project viewer | yes | no | no |
| Project editor | yes | yes | no |
| Project manager/owner only | yes | yes | no |
| None | no | no | no |

This is the intended first-pass policy:

- direct agent grants control editability
- project grants control discoverability and runtime usability
- attachment alone does not imply runtime auto-participation

## Resolution Order

When computing agent access for a user, the backend should resolve in this order:

1. superuser
2. agent owner
3. direct agent grant
4. project-derived grant from any attached project
5. deny

If multiple attached projects apply, the highest project-derived capability wins.
Direct agent grants still take precedence over all project-derived results.

## Runtime Safety Rules

Project-derived `use` is allowed only if the runtime credential model is valid.
For the first implementation, enforce these rules:

- project-derived `use` does not expose provider secrets or raw access-provider bindings
- project-derived `use` may be denied at runtime if the referenced agent depends on
  credentials unavailable to the calling user
- project-derived `view` returns sanitized metadata only

This keeps project sharing from turning into implicit delegation of another
user's private model access.

## Surface Semantics

Default surface behavior for attached agents:

- `Project`
  - attached agents are discoverable in the project resource set
- `Room`, `Demo`, `Story`
  - attached agents may be shown as discoverable or suggested
  - attached agents are not auto-added as participants
  - explicit room/demo rules still govern actual participation and execution

## Revocation Semantics

When an agent is detached from a project or a project grant is revoked:

- project-derived `view` and `use` disappear immediately
- direct agent grants remain unchanged
- existing room participant bindings are not automatically removed

Automatic cleanup of downstream bindings is deferred to a later convenience flow.

## Recommended Backend Interfaces

Minimum backend additions:

- capability resolver for agent resources
  - input: `user`, `agent_id`
  - output: derived agent capabilities
- project-derived fallback in agent access evaluation
  - inspect `project_resources` where `resource_type="agent"`
- sanitized agent read model for project viewers
- optional endpoint:
  - `GET /access/agent/{agent_id}/capabilities/me`

Recommended response shape:

```json
{
  "resource_type": "agent",
  "resource_id": "uuid",
  "can_view_agent_in_project": true,
  "can_use_agent_in_project": false,
  "can_edit_agent_config": false,
  "resolution_basis": "project_viewer"
}
```

## Non-Goals For This Phase

- delegated project-based edit rights for `UserAgentConfig`
- automatic room participant injection from project attachment
- automatic credential sharing across users
- ownership transfer through project membership
