For agent resources, the core problem is: what does it mean to "access" an agent? Until that is explicit, inheritance from `project -> agent` will stay ambiguous.

Implementation spec: `docs/assemblage/agent-project-inheritance-spec.md`

The key definitions I would lock down are these.

- `Agent Resource Identity`
  - A project-associated agent should mean a `UserAgentConfig` record, not a runtime instance, room participant, or prompt config.
  - Canonical resource key: `resource_type="agent"`, `resource_id=<UserAgentConfig.id>`.

- `Access Surface`
  - Define which operations are being protected.
  - At minimum:
    - `view`: see agent metadata/config summary
    - `use`: invoke the agent in a room/demo/workflow
    - `edit`: modify the `UserAgentConfig`
    - `manage`: delete, rebind providers, alter sharing
  - If you do not separate `use` from `edit`, you will over-grant.

- `Inheritance Meaning`
  - Decide what project membership should inherit to attached agents.
  - Recommended default:
    - project `viewer` -> agent `view`
    - project `editor` -> agent `use`
    - project `manager`/owner -> no automatic `edit` on the agent config unless explicitly granted
  - Reason: using an agent in a shared workspace is not the same as co-authoring its configuration.

- `Ownership Boundary`
  - Agent owner remains the `UserAgentConfig.owner_id`.
  - Project attachment does not transfer ownership.
  - Project membership should not let collaborators mutate provider bindings, prompts, credentials, or tool config unless you explicitly opt into that later.

- `Execution Context`
  - Define whose credentials and provider bindings an attached agent runs under.
  - This is the highest-risk area.
  - Recommended default:
    - an attached agent can only run if its underlying provider/access setup is valid for the calling user or for a shared/org-safe provider model you define later.
    - do not silently let project viewers use another user's private provider-backed agent.

- `Visibility vs Usability`
  - Separate “visible in project” from “runnable in project”.
  - An agent may appear in the project roster but be marked:
    - `visible_not_runnable`
    - `runnable`
    - `editable`
  - This avoids confusing authorization with runtime capability.

- `Attachment Semantics`
  - Decide whether attaching an agent means:
    - merely cataloging it in the project
    - making it selectable in rooms/demos linked to the project
    - auto-exposing it to orchestration surfaces
  - Recommended default: attachment is catalog/discovery only; use in a room/demo requires that surface’s own explicit rules.

- `Cross-Surface Propagation`
  - If a room, story, or demo belongs to a project that has attached agents, define whether those agents become:
    - discoverable
    - suggested
    - auto-available
  - Recommended default: discoverable only, no automatic participant injection.

- `Conflict Resolution`
  - Define precedence between:
    - direct agent grants
    - project-derived grants
    - owner/superuser override
  - Recommended order:
    1. superuser
    2. agent owner
    3. direct agent grant
    4. project-derived agent capability
  - Direct grants should beat inherited grants.

- `Revocation Semantics`
  - If agent is detached from project, what stops?
  - Recommended default:
    - project-derived visibility/use disappears immediately
    - existing room participant bindings are not force-removed automatically
    - future convenience cleanup can be explicit

- `Credential Safety Model`
  - Define whether an attached agent can expose:
    - system prompt
    - tool list
    - provider/model details
    - secrets-derived configuration
  - Recommendation:
    - viewers get sanitized metadata only
    - editors/use-capable users get runnable interface, not raw secrets
    - only owner/admin gets full config edit surface

If you want a clean first implementation, I would formalize three derived agent capabilities only:

- `can_view_agent_in_project`
- `can_use_agent_in_project`
- `can_edit_agent_config`

And I would map them like this:

- agent owner/admin: all three
- direct agent editor grant: all three except ownership-only settings if needed
- project viewer: `can_view_agent_in_project`
- project editor: `can_view_agent_in_project` + `can_use_agent_in_project`
- no project role: none

That keeps project inheritance useful without accidentally turning shared projects into delegated agent-config administration.

If you want, I can turn this into a short implementation spec with a backend permission matrix and recommended endpoint changes.
