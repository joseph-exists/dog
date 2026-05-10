# Provider API Payload Tree Debug

Status: `debug artifact`
Created: `2026-04-28`
Sources:
- `docs/affordances/journeys/debug-prompt-message-logs.md`
- `docs/affordances/journeys/debug-prompt-agent.md` (currently empty)

## Purpose

Visualize the hierarchy of the provider API call captured in the debug logs.
This is intended to help identify which elements must remain durable inside Dog
for audit/replay, and which elements should not be sent upstream as part of the
model-facing request.

## Request Envelope Tree

The captured provider call is an OpenAI-compatible chat completions request.

```text
Request options
├── method: "post"
├── url: "/chat/completions"
├── headers
│   └── User-Agent: "pydantic-ai/1.30.1"
├── files: null
├── idempotency_key: "stainless-python-retry-..."
└── json_data
    ├── model: "qwen/qwen3-235b-a22b"
    ├── stream: true
    ├── stream_options
    │   └── include_usage: true
    ├── tool_choice: "auto"
    ├── messages
    │   ├── [0] system
    │   │   ├── role: "system"
    │   │   └── content
    │   │       ├── base model identity/instruction text
    │   │       └── configured agent persona/system prompt text
    │   └── [1] user
    │       ├── role: "user"
    │       └── content
    │           ├── Additional context
    │           │   └── [shadow] shadow.agent.summary
    │           │       └── serialized Python dict rendered into prompt text
    │           └── User message
    │               └── "Hello @Qwenzorius, I hope you have been very well"
    └── tools
        └── [0] function tool
            ├── type: "function"
            ├── function
            │   ├── name: "invoke_connected_workspace_runtime"
            │   ├── description
            │   │   ├── invoke current room workspace runtime
            │   │   └── describes backend-owned websocket envelope and selected runtime
            │   ├── parameters
            │   │   ├── type: "object"
            │   │   ├── additionalProperties: false
            │   │   ├── properties
            │   │   │   └── input
            │   │   │       └── type: "string"
            │   │   └── required
            │   │       └── "input"
            │   └── strict: true
            └── provider-visible tool schema
```

## Model-Facing Payload Tree

This is the portion under `json_data` that the provider receives as the model
request body.

```text
json_data
├── messages
│   ├── system message
│   │   ├── role
│   │   │   └── "system"
│   │   └── content
│   │       ├── provider/model identity instruction
│   │       └── Dog agent system/persona instruction
│   └── user message
│       ├── role
│       │   └── "user"
│       └── content
│           ├── prompt-builder section: "Additional context"
│           │   └── extra_context item
│           │       ├── source label
│           │       │   └── "shadow"
│           │       ├── context_type
│           │       │   └── "shadow.agent.summary"
│           │       └── payload rendered inline as text
│           │           ├── entity_type: "agent"
│           │           ├── entity_id: agent UUID
│           │           ├── version_number: 1
│           │           ├── commit_sha: shadow commit SHA
│           │           ├── source: "db"
│           │           ├── is_stale: true
│           │           └── summary
│           │               ├── agent
│           │               │   ├── id: same agent UUID
│           │               │   ├── slug: "visionary-chubby-guan-of-art"
│           │               │   ├── name: "Qwenzorius"
│           │               │   ├── description: "Qwen the mighty"
│           │               │   ├── participation_mode: "always"
│           │               │   └── capabilities: []
│           │               └── agent_personas: []
│           └── prompt-builder section: "User message"
│               └── user-authored message text with @mention
├── model
│   └── "qwen/qwen3-235b-a22b"
├── streaming controls
│   ├── stream: true
│   └── stream_options.include_usage: true
└── tool calling
    ├── tool_choice: "auto"
    └── tools
        └── invoke_connected_workspace_runtime schema
            ├── provider-visible tool name
            ├── provider-visible tool description
            └── provider-visible JSON schema for arguments
```

## Prompt Construction Tree

This view maps the observed `messages[1].content` back to the local prompt
builder sections.

```text
build_agent_prompt(trigger_message, context, current_agent_slug)
├── conversation_context
│   ├── story_data section
│   │   └── not present in this captured call
│   ├── story_runtime section
│   │   └── not present in this captured call
│   ├── active_agents section
│   │   └── not present in this captured call
│   ├── recent_messages section
│   │   └── not present in this captured call
│   └── extra_contexts section
│       └── present
│           └── shadow.agent.summary
│               ├── durable/audit metadata
│               │   ├── entity_type
│               │   ├── entity_id
│               │   ├── version_number
│               │   ├── commit_sha
│               │   ├── source
│               │   └── is_stale
│               └── model-relevant summary candidate
│                   ├── agent.slug/name/description
│                   ├── participation_mode
│                   ├── capabilities
│                   └── agent_personas
└── trigger message
    └── appended as "User message: ..."
```

## Candidate Review Points

- `shadow.agent.summary` is being sent as a raw serialized dict inside the user
  prompt. This mixes durable replay metadata with model-facing context.
- The payload repeats agent identity in several places:
  `system.content`, `shadow.agent.summary.summary.agent`, and the user's
  explicit `@Qwenzorius` mention.
- Shadow bookkeeping fields are provider-visible:
  `entity_id`, `version_number`, `commit_sha`, `source`, and `is_stale`.
- Tool availability is provider-visible even when the user message is a simple
  greeting. In this trace only `invoke_connected_workspace_runtime` is attached,
  but the full function name, description, and argument schema are still sent.
- `stream_options.include_usage` is provider API metadata, not prompt content;
  it is useful operationally but should be considered separately from prompt
  construction cleanup.

## Separation Target

```text
Dog durable invocation record
├── full room_context_json
├── shadow metadata and provenance
├── prompt hash and builder version
├── tool resolution metadata
└── response/event linkage

Provider-facing request
├── minimal system instruction
├── user message
├── concise model-relevant context only
└── tool schemas only when needed for this run
```

## Implementation Pass: 2026-04-28

Applied the separation target in the backend prompt/tool construction path:

- Full `RoomContext.extra_contexts` remains available in the durable
  `AgentInvocation.room_context_json` audit record.
- Provider-facing prompt rendering now uses a dedicated extra-context renderer
  instead of dumping raw context payloads into `messages[1].content`.
- Current-agent `shadow.agent.summary` is skipped in the provider prompt because
  the agent identity belongs in `system_prompt`.
- Non-self Shadow summaries are rendered as concise model-facing summaries, with
  audit/provenance fields such as `entity_id`, `version_number`, `commit_sha`,
  `source`, and `is_stale` removed.
- System contexts are pruned before prompt insertion:
  - canvas SVG payloads are omitted from prompt text;
  - demo composition is summarized by panel/block labels;
  - workspace connection context keeps high-level state/capabilities while
    omitting endpoint URLs/auth metadata.
- Workspace runtime tool schema exposure is now intent-gated at the streaming
  runner boundary. A simple greeting no longer sends
  `invoke_connected_workspace_runtime`; execution-oriented requests still can.

Remaining follow-up candidates:

- Replace keyword intent gating with an explicit product-level tool exposure
  policy if operators need deterministic per-room/per-message controls.
- Add DebugPanel fields for "provider-facing prompt" versus "durable context"
  once the audit API exposes both separately.
