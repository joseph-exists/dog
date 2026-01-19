Agent Services Guide

Purpose
Provide engineers a practical reference for using, debugging, and extending the agent services.

Scope
- Agent orchestration and runners
- Context aggregation (room + extra contexts)
- A2A (agent-to-agent) communication
- Streaming vs non-streaming paths
- Debugging and testing

High-Level Architecture
- agent_runner.py: Public entry points for running agents and coordinator orchestration.
- agent_runner_streaming.py: Streaming run loop + A2A processing.
- agent_runner_non_streaming.py: Non-streaming run loop.
- agent_instance.py: Agent construction and credential resolution.
- agent_prompt.py: Prompt assembly.
- agent_selection.py: Participant resolution and participation modes.
- context_provider.py: Builds RoomContext from room data and extra contexts.
- context_store.py: ContextItem store (Redis-backed by default).
- agent_tools.py: PydanticAI tools (A2A request + AG-UI components).

Key Entry Points
- run_agents_for_message(room_id, trigger_message, session, user_id=None)
  - High-level coordinator + participation mode orchestration.
- run_agent_for_room_streaming(room_id, agent_name, trigger_message, session, user_id=None, a2a_depth=0)
  - Streaming tokens + optional A2A chaining.
- run_agent_for_room(room_id, agent_name, trigger_message, session)
  - Non-streaming run.
- invoke_agent_manually(room_id, agent_slug, trigger_message, session)
  - Manual invocation regardless of participation mode.

Participation Modes
- always: responds to every message.
- on_mention: responds only when mentioned (@slug or @Display Name).
- manual: only responds when explicitly invoked.

Context Provider (RoomContext)
RoomContext combines:
- room metadata
- story data (if linked)
- recent messages
- participants + active agents
- extra_contexts (multi-source context items)

Extra Contexts (Multi-Source)
ContextItem fields:
- room_id, agent_slug (optional), context_type, payload, source, created_at, expires_at

Aggregation rules:
- Room-wide + agent-specific items included when agent_slug is provided.
- Ordered by source priority (seed → backend → frontend) then created_at.

Default Store
- RoomContextService uses RedisContextStore by default (same Redis as event_emitter).
- Override by passing a store to RoomContextService or directly to build_room_context.

Prompt Assembly
build_agent_prompt adds:
- story info
- other agents in room
- recent messages
- additional context (extra_contexts)

Agent Construction (Credentials)
get_agent_instance_with_tools resolves credentials in this order:
1) UserAgentSettings model override
2) Explicit UserLLMProvider
3) Default provider for model type
4) Environment variables (no user provider)

AG-UI Components
Agents can emit structured UI components using emit_ui_component tool.
Components are collected during streaming and attached to the final room_message.agent event.

A2A (Agent-to-Agent)
- Agents can request help via request_agent_assistance tool.
- A2A triggers on @mentions in agent responses.
- Depth limited by DEFAULT_MAX_A2A_DEPTH.

Debugging Tips
- Enable debug logging for app.services.* to trace prompts and A2A triggers.
- Check Redis connectivity if streaming tokens or context store look stale.
- Use room event logs to verify emitted room_message.agent payloads.

Common Failure Modes
- Agent not found: check AgentConfig slug and RoomParticipant participant_id.
- Provider errors: verify provider credentials and base_url.
- A2A recursion limit: DEFAULT_MAX_A2A_DEPTH reached.
- Redis unavailable: streaming tokens or context store may silently degrade.

Testing
Key tests:
- backend/app/tests/services/test_agent_selection.py
- backend/app/tests/services/test_agent_runner_non_streaming.py
- backend/app/tests/services/test_context_store.py
- backend/app/tests/services/test_context_provider_extra_contexts.py
- backend/app/tests/services/test_agent_prompt_extra_contexts.py

Suggested Commands
- pytest backend/app/tests/services/test_agent_selection.py -v
- pytest backend/app/tests/services/test_agent_runner_non_streaming.py -v
- pytest backend/app/tests/services/test_context_store.py -v
- pytest backend/app/tests/services/test_context_provider_extra_contexts.py -v
- pytest backend/app/tests/services/test_agent_prompt_extra_contexts.py -v

Extension Points
- Replace RedisContextStore with DB-backed store when persistence is required.
- Add expiration cleanup for ContextItem expires_at.
- Add per-agent context scoping in higher-level callers (pass agent_slug).
- Consolidate error handling via AgentErrorHandler (if introduced).
