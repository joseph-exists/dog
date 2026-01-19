● Implementation complete. Here's the summary:

  Changes Made

  1. app/services/agent_runner.py

  New imports:
  - pydantic_ai.providers.openai.OpenAIProvider
  - pydantic_ai.providers.anthropic.AnthropicProvider
  - pydantic_ai.providers.google_gla.GoogleGLAProvider
  - pydantic_ai.models.* for OpenAI, Anthropic, Gemini
  - app.core.security.decrypt_api_key
  - app.models.UserAgentSettings, UserLLMProvider, LLMProviderType

  New functions:
  - resolve_user_credentials() - Looks up UserAgentSettings for model override, finds UserLLMProvider, decrypts API key
  - create_model_with_credentials() - Creates the appropriate PydanticAI Model with Provider based on provider type

  Modified functions:
  - get_agent_instance_with_tools() - Added user_id parameter, calls credential resolution
  - run_agent_for_room_streaming() - Added user_id parameter, passes to instance creation
  - run_agents_for_message() - Added user_id parameter, passes to streaming function

  2. app/api/routes/rooms.py

  - Updated send_message() to pass user_id=current_user.id to run_agents_for_message()

  3. app/api/routes/websocket.py

  - Updated websocket handler to pass user_id=user.id to run_agents_for_message()

  New Flow

  User sends message in Room
           ↓
  Route Handler (has current_user.id)
           ↓
  run_agents_for_message(user_id=current_user.id)
           ↓
  run_agent_for_room_streaming(user_id=user_id)
           ↓
  get_agent_instance_with_tools(user_id=user_id)
           ↓
  resolve_user_credentials() → (model_name, api_key, provider_type)
           ↓
  create_model_with_credentials() → OpenAIModel/AnthropicModel/GeminiModel
           ↓
  Agent(model_with_credentials, ...)
           ↓
  agent.run_stream() uses user's API key! ✅

  Credential Resolution Order

  1. Check UserAgentSettings for model override for this agent
  2. Check UserAgentSettings.provider_id for explicit provider
  3. Fall back to user's default provider for the model's provider type
  4. Fall back to environment variables (no user provider)

  Control Flow and Call Hierarchy Mapping (Refactor Analysis)

  Agent runner and context provider mapping below, focused on control flow and call hierarchy for refactor analysis. File refs inline.

  **agent_runner.py**

  Control flow (major entry points)
  - `run_agents_for_message` in `backend/app/services/agent_runner.py` orchestrates two phases: coordinator agents first (always run), then regular agents filtered by participation mode; each run delegates to `run_agent_for_room_streaming`.
  - `run_agent_for_room_streaming` in `backend/app/services/agent_runner.py` performs availability check → context build → agent instantiation with tools/credentials → stream run → emit final event (and UI components) → A2A mention processing.
  - `run_agent_for_room` in `backend/app/services/agent_runner.py` is the non-streaming single-agent path: availability check → context build → agent instantiation (no tools) → run → emit final event.
  - `invoke_agent_manually` in `backend/app/services/agent_runner.py` validates agent + room participation, then delegates to `run_agent_for_room_streaming`.
  - A2A tool path: `request_agent_assistance` in `backend/app/services/agent_runner.py` → `_run_agent_for_tool_call` (non-streaming, no tools on target agent, no event/token emission).

  Call hierarchy (key functions)
  - `run_agents_for_message`
    - `resolve_agent_identifier` (per participant)
    - `should_agent_respond_to_message` (regular agents)
    - `run_agent_for_room_streaming`
      - `is_agent_available` → `resolve_agent_identifier`
      - `build_room_context` in `backend/app/services/context_provider.py`
      - `get_agent_instance_with_tools`
        - `get_agent_config`
        - `resolve_user_credentials`
          - `decrypt_api_key`
          - model/provider resolution (UserAgentSettings/UserLLMProvider)
        - `create_model_with_credentials`
      - `build_agent_prompt`
      - `agent.run_stream(...)`
      - `publish_agent_token` (per chunk)
      - `emit_event` (final message)
      - `A2AOrchestrator.process_mentions` (A2A)
        - `detect_mentions`
        - `is_agent_in_room`
          - `resolve_agent_identifier`
        - `run_agent_for_room_streaming` (recursive A2A, depth+1)
  - `run_agent_for_room`
    - `is_agent_available` → `resolve_agent_identifier`
    - `build_room_context`
    - `get_agent_instance`
      - `get_agent_config`
    - `build_agent_prompt`
    - `agent.run(...)`
    - `emit_event`
  - `request_agent_assistance`
    - `is_agent_in_room`
    - `_run_agent_for_tool_call`
      - `get_agent_instance`
      - `build_room_context`
      - `build_agent_prompt`
      - `agent.run(...)` (non-streaming)
  - `emit_ui_component` is a tool used within agent runs; it appends to `AgentDeps.ui_components` for later inclusion in emitted event.

  Control flow notes to flag for refactor
  - A2A recursion uses a configured depth limit in `A2AOrchestrator.process_mentions` and `request_agent_assistance`, but `run_agent_for_room_streaming` is still the recursion entry (depth passed via parameter).
  - `build_room_context` is invoked in every run (streaming + non-streaming + A2A tool), so it’s a hot path.
  - Coordinator bypasses participation checks; regular agents use `should_agent_respond_to_message`.

  **context_provider.py**

  Control flow (single entry point)
  - `build_room_context` in `backend/app/services/context_provider.py` loads room → story → recent messages → participants → active agent details → returns `RoomContext`.

  Call hierarchy (key functions)
  - `build_room_context`
    - DB queries:
      - `select(Room)` by `room_id`
      - `select(Story)` by `room.story_id` (optional)
      - `select(RoomMessage)` by room, ordered desc, limit `message_limit`
      - `select(RoomParticipant)` by room and active
      - Agent details per participant:
        - try UUID → `session.get(AgentConfig, uuid)`
        - fallback by slug → `select(AgentConfig).where(slug == participant_id)`
    - Constructs:
      - `recent_messages` (chronological)
      - `participants` list
      - `active_agents` list of `AgentInfo`
      - `room_metadata`
    - Returns `RoomContext` dataclass.

  Mermaid Diagram

  ```mermaid
  flowchart TD
    subgraph agent_runner.py
      RAM[run_agents_for_message] -->|coordinators| RARS[run_agent_for_room_streaming]
      RAM -->|regular agents| RARS
      RAM --> RAR[run_agent_for_room]
      RAM --> IAM[invoke_agent_manually]
      RARS --> IAA[is_agent_available]
      RARS --> BRC[build_room_context]
      RARS --> GAIT[get_agent_instance_with_tools]
      GAIT --> RUC[resolve_user_credentials]
      RUC --> CMC[create_model_with_credentials]
      RARS --> BAP[build_agent_prompt]
      RARS --> ARS[agent.run_stream]
      RARS --> EEVT[emit_event]
      RARS --> PAR[A2AOrchestrator.process_mentions]
      PAR --> DMA[detect_mentions]
      PAR --> IAR[is_agent_in_room]
      PAR --> RARS
      RAR --> IAA
      RAR --> BRC
      RAR --> GAI[get_agent_instance]
      RAR --> BAP
      RAR --> AR[agent.run]
      RAR --> EEVT
      RAA[request_agent_assistance] --> IAR
      RAA --> RAFT[_run_agent_for_tool_call]
      RAFT --> GAI
      RAFT --> BRC
      RAFT --> BAP
      RAFT --> AR
    end

    subgraph context_provider.py
      BRC --> ROOM[select Room]
      BRC --> STORY[select Story]
      BRC --> MSGS[select RoomMessage]
      BRC --> PART[select RoomParticipant]
      BRC --> AG[AgentConfig lookups]
      BRC --> RC[RoomContext]
    end
  ```
