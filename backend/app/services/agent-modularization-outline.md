Implementation Outline: Agent Service Modularization

Purpose
Provide a concrete, module-by-module outline for refactoring backend/app/services/agent_runner.py
into smaller components while preserving current behavior.

Scope
- Room context building and caching
- Agent instance and credential resolution
- Streaming and non-streaming runners
- A2A orchestration
- Agent selection (coordinators + participation modes)
- Event emission and token streaming
- Error handling policy

Module: backend/app/services/agent_context.py
Responsibility
- Build RoomContext for a room_id with a consistent message limit and optional caching.

Key types
- RoomContext (from app.services.context_provider)

Functions
- async def build(room_id: uuid.UUID, session: AsyncSession, message_limit: int = 20) -> RoomContext
  - Calls existing build_room_context.
  - Optional cache layer keyed by (room_id, message_limit, last_activity).
  - Returns RoomContext for downstream use.

Notes
- Keep as a thin wrapper initially; add caching only after tests/metrics.

Module: backend/app/services/agent_instance.py
Responsibility
- Centralize agent config retrieval, credential resolution, model construction, and tool wiring.

Key types
- AgentConfig, LLMProviderType
- AgentDeps (from app.services.agent_tools)

Functions
- async def get_agent_config(session: AsyncSession, slug: str) -> AgentConfig | None
  - Database lookup for AgentConfig.
- async def resolve_user_credentials(session: AsyncSession, user_id: uuid.UUID, agent_config: AgentConfig)
  -> tuple[str, str | None, LLMProviderType | None, str | None]
  - Resolve model override and provider credentials.
- def create_model_with_credentials(model_name: str, api_key: str | None,
  provider_type: LLMProviderType | None, base_url: str | None) -> Any
  - Create provider-backed model when API key is present.
- async def get_agent_instance(session: AsyncSession, slug: str) -> Agent[Any, Any] | None
  - Create agent without tools.
- async def get_agent_instance_with_tools(session: AsyncSession, slug: str, user_id: uuid.UUID | None,
  enable_a2a_tool: bool, enable_ag_ui_tool: bool) -> Agent[AgentDeps, str] | None
  - Create agent with A2A + AG-UI tools.

Notes
- Tool definitions live in backend/app/services/agent_tools.py.

Module: backend/app/services/agent_selection.py
Responsibility
- Resolve room participants into coordinator and regular agent lists.
- Apply participation mode checks for regular agents.

Functions
- async def resolve_participants(session: AsyncSession, room_id: uuid.UUID)
  -> list[RoomParticipant]
  - Query active agent participants.
- async def resolve_agent_identifier(session: AsyncSession, participant_id: str)
  -> tuple[str | None, str | None, AgentConfig | None]
  - Move existing resolve_agent_identifier logic.
- def should_agent_respond_to_message(config: AgentConfig, trigger_message: str)
  -> tuple[bool, str]
  - Move participation mode logic.
- async def select_agents_for_message(session: AsyncSession, room_id: uuid.UUID, trigger_message: str)
  -> tuple[list[tuple[str, str, AgentConfig]], list[tuple[str, str, AgentConfig, str]]]
  - Returns coordinators and regular agents ready to run.

Notes
- Keep log messages to maintain current observability.

Module: backend/app/services/a2a_orchestrator.py
Responsibility
- Detect agent mentions and trigger A2A runs with depth control.

Functions
- def detect_mentions(message: str) -> set[str]
  - Move existing mention parsing.
- async def is_agent_in_room(session: AsyncSession, room_id: uuid.UUID, agent_identifier: str)
  -> tuple[bool, str | None, AgentConfig | None]
  - Move existing room membership check.
- async def process_mentions(response: str, responding_agent_slug: str, room_id: uuid.UUID,
  session: AsyncSession, current_depth: int, run_agent: Callable)
  -> list[AgentRunResult]
  - Uses detect_mentions and is_agent_in_room.
  - Respects configured A2A depth limit.
  - Delegates to StreamingAgentRunner for each triggered agent.

Notes
- Runner is injected to keep orchestration independent of run implementation.

Module: backend/app/services/agent_events.py
Responsibility
- Publish tokens and emit final agent messages.

Functions
- async def publish_token(room_id: uuid.UUID, agent_name: str, token: str) -> None
  - Wrap publish_agent_token.
- async def emit_message(session: AsyncSession, room_id: uuid.UUID, agent_name: str, content: str,
  ui_components: list[UIComponent] | None) -> None
  - Wrap emit_event with payload assembly.

Notes
- Keep payload shape identical to current events.

Module: backend/app/services/agent_errors.py
Responsibility
- Normalize error handling across runners.

Functions
- async def handle_error(session: AsyncSession, room_id: uuid.UUID, agent_name: str, exc: Exception)
  -> AgentRunResult
  - Map ModelAPIError separately for detailed logging.
  - Emit fallback error message via AgentEventPublisher.
  - Return AgentRunResult with success=False and error string.

Notes
- Keeps current user-facing error strings unless changed intentionally.

Module: backend/app/services/agent_runner_streaming.py
Responsibility
- Run agent with token streaming and optional A2A.

Dependencies
- RoomContextService
- AgentEventPublisher
- A2AOrchestrator
- AgentErrorHandler
- Agent instance builder (get_agent_instance_with_tools)
  - A2A trigger uses injected runner instead of direct call

Functions
- async def run(req: AgentRunRequest, session: AsyncSession) -> AgentRunResult
  Steps:
  1) Check agent availability via AgentSelectionService.resolve_agent_identifier.
  2) Build context via RoomContextService.build.
  3) Build agent via get_agent_instance_with_tools (enable tools).
  4) Build prompt via build_agent_prompt (backend/app/services/agent_prompt.py).
  5) Stream tokens, publish via AgentEventPublisher.publish_token.
  6) Emit final message with UI components.
  7) Process A2A mentions via A2AOrchestrator.process_mentions.
  8) Return AgentRunResult.

Notes
- Keep run_stream semantics identical to current implementation.

Module: backend/app/services/agent_runner_non_streaming.py
Responsibility
- Run agent without streaming, single response.

Dependencies
- RoomContextService
- AgentEventPublisher
- AgentErrorHandler
- Agent instance builder (get_agent_instance)

Functions
- async def run(req: AgentRunRequest, session: AsyncSession) -> AgentRunResult
  Steps:
  1) Check agent availability.
  2) Build context.
  3) Build agent without tools.
  4) Build prompt.
  5) agent.run(full_prompt)
  6) Emit final message via AgentEventPublisher.
  7) Return AgentRunResult.

Module: backend/app/services/agent_runner.py (facade)
Responsibility
- Preserve public API while delegating to new modules.

Functions
- run_agents_for_message: uses AgentSelectionService + StreamingAgentRunner.
- run_agent_for_room: calls NonStreamingAgentRunner.
- run_agent_for_room_streaming: calls StreamingAgentRunner.
- invoke_agent_manually: uses AgentSelectionService and StreamingAgentRunner.
- request_agent_assistance and emit_ui_component live in backend/app/services/agent_tools.py.

Module: backend/app/services/agent_prompt.py
Responsibility
- Build agent prompts with room context and agent awareness.

Functions
- def build_agent_prompt(trigger_message: str, context: RoomContext, current_agent_slug: str | None) -> str

Module: backend/app/services/agent_tools.py
Responsibility
- A2A and AG-UI tools + AgentDeps.

Functions
- class AgentDeps
- async def request_agent_assistance(...)
- def emit_ui_component(...)

Migration Plan (Incremental)
1) Extract AgentSelectionService and agent instance helpers without changing call sites.
2) Extract RoomContextService (thin wrapper).
3) Add AgentEventPublisher and AgentErrorHandler; wire into streaming runner.
4) Extract Streaming and NonStreaming runners; adapt existing functions to delegate.
5) Extract A2AOrchestrator and pass runner injection.
6) agent_factory.py removed (unused).

Non-Goals
- Change database schema or event payloads.
- Introduce caching without monitoring/metrics.
