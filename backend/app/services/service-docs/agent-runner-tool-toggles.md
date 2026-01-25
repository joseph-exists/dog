**Agent Runner Tool Toggle Reference**

This reference card helps engineers trace the new tool toggles (`enable_a2a_tool`, `enable_ag_ui_tool`) from high-level entry points down through the streaming runner so they can expose them safely in routes, admin UI, or other orchestration layers.

### 1. Control Flow & Boundaries

- **Caller surface:** routes (e.g., `/rooms.send_message`, websocket message handling) or jobs that currently call `run_agents_for_message`, `run_agent_for_room_streaming`, or `invoke_agent_manually`.
- **Primary orchestrator:** `run_agents_for_message` in `agent_runner.py` now accepts the toggle flags and annotates them on every span _before_ delegating to `run_agent_for_room_streaming`.
- **Per-agent invocation:** `run_agent_for_room_streaming` enriches span metadata and serializes the flags into `AgentRunRequest` so downstream runners see the caller intent.
- **Runner boundary:** `_get_streaming_runner().run` receives the populated `AgentRunRequest`; the streaming runner sets the span tag and passes flags into `get_agent_instance_with_tools`, which is the gate where tools actually start/stop.

### 2. Call hierarchy (simplified)

```
Route handler (rooms/send_message, ws, admin) 
  → agent_runner.run_agents_for_message(user_id, enable_a2a_tool=?, enable_ag_ui_tool=?)
    → (coordinator/regular loop) run_agent_for_room_streaming(..., enable_... flags)
      → StreamingAgentRunner.run(req=AgentRunRequest(enable_... flags))
        → get_agent_instance_with_tools(..., enable_... flags)
          → Agent(params, tools=[request_agent_assistance if enable_a2a_tool, emit_ui_component if enable_ag_ui_tool])
```

### 3. Implementation notes for exposing toggles

1. **Add parameters at the API boundary.** wherever agents are triggered (room routes, WebSocket commands, manual invoke endpoints), extend the handler signature (or payload) to include `enable_a2a_tool`/`enable_ag_ui_tool` defaults. Validate the caller context before flipping them on.
2. **Propagate through service layer.** pass the incoming booleans into `run_agents_for_message` (or `run_agent_for_room_streaming`/`invoke_agent_manually` for single-agent paths). The runner will automatically propagate via `AgentRunRequest`.
3. **Logfire observability.** spans already tag `a2a_tool_enabled` and `ag_ui_tool_enabled` so you can see when a caller opted in. No extra instrumentation is required unless you want more granular metrics on specific routes.
4. **Room-level defaults.** if certain rooms should always have one tool disabled, perform that logic before calling into `agent_runner`. E.g., a room policy service could decide the flag combination and simply pass it through.
5. **Testing & fallbacks.** when the toggles are `False`, no tools are registered—validate callers that rely on A2A or AG-UI now explicitly enable the relevant flag, otherwise those features remain inactive without errors.

### 4. Summary checklist

- [ ] Update route handlers or orchestration layers to accept `enable_a2a_tool`/`enable_ag_ui_tool`.
- [ ] Ensure flags propagate into `run_agents_for_message`/`run_agent_for_room_streaming` as shown above.
- [ ] Use the existing spans (`agent.run_streaming`, `agent.run_agents_for_message`, etc.) to verify the passed flags in Logfire.
- [ ] Document any new API surface or admin controls that allow toggling per-room or per-invocation defaults.
