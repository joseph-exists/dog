## 🚨 Common Pitfalls to Avoid

| Pitfall | Solution |
|---------|----------|
| Updating events directly | Always emit new events instead |
| Managing transactions in CRUD | Use `AsyncSessionTransactionDep` in routes, not `session.begin()` in CRUD |
| Using AsyncSessionDep for writes | Use `AsyncSessionTransactionDep` for POST/PATCH/DELETE routes |
| Not flushing after emit_event | `emit_event()` includes `session.flush()` automatically |
| Nested transaction errors | Route owns transaction; CRUD functions should not call `session.begin()` |
| Loading too much context | Limit to 20 messages + story outline |
| Blocking operations in tools | Use `async`/`await` or `asyncio.to_thread()` |
| Missing authorization checks | Always call `check_room_membership()` before operations |
| Not handling agent errors | Wrap in try/except, return friendly message |
| Not checking room membership | Always validate via room_participants before operations |
| Missing participant events | Emit participant.joined/left for users AND agents |
| Tight coupling to agent | Use AGENT_REGISTRY for decoupling |