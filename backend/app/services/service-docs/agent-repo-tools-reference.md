# Agent Repo Tools Reference Card

This card explains the room-agent repo tools added for safe read/modify/write flows.

Audience:

- Backend engineers implementing tool/runtime behavior
- UX engineers shaping the agent settings and user-facing states
- Reviewers validating MVP readiness

## What Exists

- `read_repo_file(repo_id, path, ref=None)`
- `write_repo_files(repo_id, branch, commit_message, mutations, expected_head_sha=None)`

Both tools run as the acting room user and validate room membership before touching repos.

## MVP Intent

- Trusted internal environment
- Fast enablement for selected agents
- Clear rollback path (kill switch)
- Keep manual JSON override available for advanced users

## Enablement (`tool_config`)

Either format works:

```json
{
  "enabled_tools": ["read_repo_file", "write_repo_files"]
}
```

```json
{
  "read_repo_file": true,
  "write_repo_files": true
}
```

Primary UX path now toggles these values from the Agent form.

## UX Behavior Contract

- Toggle labels:
  - `Repo Read Tool` -> enables `read_repo_file`
  - `Repo Write Tool` -> enables `write_repo_files`
- Toggle source of truth is `tool_config` on the agent record.
- Advanced JSON editor remains editable; toggles should keep JSON synchronized.
- If kill switch is OFF, toggles may still appear enabled in config but tools are not attached at runtime.
- UX should communicate this as "configured but globally disabled" when surfaced in admin/debug panels.

## Typical Agent Flow

1. Call `read_repo_file(...)`.
2. Parse JSON response.
3. Use `write_hint.branch` and `write_hint.expected_head_sha` from the read response.
4. Call `write_repo_files(...)` with those values and one or more mutations.

## `read_repo_file` Response Shape

Success returns a JSON string with:

- `repo_id`
- `path`
- `resolved_ref`
- `is_binary`
- `is_truncated`
- `content_type`
- `size_bytes`
- `encoding`
- `content`
- `write_hint.branch`
- `write_hint.expected_head_sha`

Error returns a plain text message (for model self-correction).

## `write_repo_files` Mutations

Supported mutation operations:

- `upsert` requires `path`, `operation`, `content`
- `delete` requires `path`, `operation`

Example:

```json
[
  {
    "path": "README.md",
    "operation": "upsert",
    "content": "# Updated"
  },
  {
    "path": "obsolete.txt",
    "operation": "delete"
  }
]
```

## Guardrails

- Acting user must be an active `RoomParticipant`.
- Repo access is authorized as the acting user (owner/superuser rules).
- Existing repo service validation and optimistic concurrency are reused.
- Writes execute in a worker thread so async agent streaming is not blocked.
- Global kill switch: set `AGENT_REPO_TOOLS_ENABLED=false` to disable both repo tools at runtime.

## Runtime/Kill Switch

- Env var: `AGENT_REPO_TOOLS_ENABLED` (default `true`)
- Location: root `.env`
- Effect: when `false`, repo tools are not attached even if `tool_config` enables them.

## Key Wiring Points

- Tool deps carry `acting_user_id` from `AgentRunRequest.user_id`.
- `get_agent_instance_with_tools()` attaches repo tools from `tool_config`.
- Repo operations use existing `user_repo_service` and `user_repo_view_service`.

## File Map

- Tool implementations:
  - `backend/app/services/agent_tools.py`
- Tool attachment + kill switch:
  - `backend/app/services/agent_instance.py`
- Agent form toggles + JSON sync:
  - `frontend/src/components/Agents/Forms/AgentForm.tsx`
- Config:
  - `backend/app/core/config.py`
  - `.env`

## Review Checklist

- Backend:
  - Repo tools attach only when enabled in `tool_config`.
  - Kill switch fully disables runtime attachment.
  - Read/write respect acting-user auth and room membership checks.
- UX:
  - Toggle changes persist through create/edit flows.
  - Reopening an agent reflects saved toggle state correctly.
  - Advanced JSON and toggles remain consistent.
- QA smoke:
  - Enable toggles on an agent.
  - Agent can read file and then write with returned `write_hint`.
  - Flip kill switch off and confirm agent no longer gets repo tools.
