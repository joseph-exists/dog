Next Steps

Task 1: Complete:
Injected active_for_context into build_room_context – in context_provider.py (lines 264-283); add a where(RoomMessage.active_for_context == True)  before the limit(message_limit) so agents only see messages marked as active. 


Task 2:
Expose filtered context via RoomContextService/runner – since agent_context.RoomContextService.build just proxies to build_room_context (agent_context.py (lines 17-33)), you can add a parameter like filter_active_context: bool and thread it through the streaming/non-streaming runners in agent_runner.py (and any CLI/orchestrator entry points) so the choice can be toggled per-agent or per-api call.

Sync shadow/extra-context paths where relevant – the shadow-derived items in shadow_context_loader.py and context_store.py never refer to RoomMessage.active_for_context; that’s fine, but if you eventually derive message summaries or clips there, make sure they respect the flag before emitting context items that will end up inside RoomContext.extra_contexts.


Provide invalidation hooks – the frontend already emits message.context_toggled/message_deleted events handled by event_emitter (and publish state to Redis). Ensure those events not only update RoomMessage.active_for_context but also invalidate any cached context (in Redis or the UI) before the next LLM call; e.g., when _handle_message_context_toggled runs, push a notification so agents rebuild context via the filtered query rather than reuse stale state.


Consider a context-cache filter layer – if you ever cache RoomContext per room/agent (e.g., via ContextItemStore), add a predicate there that prunes any cached messages whose active_for_context is now False before handing the context back. That keeps cached prompts consistent with the latest UI actions.


These locations give you a reliable pattern: update the projection flag through the existing handlers (event_emitter.py (lines 1039-1124)), read it where contexts are formally built (context_provider → agent_context → agent_runner), and optionally gate any caches/extra-context stores around that same predicate so LLM prompts always reflect the frontend’s intention.