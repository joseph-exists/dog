
● Implementation Plan: AG-UI Readiness Enhancements

  Executive Summary

  Objective: Add two nullable JSONB fields to existing projections to enable AG-UI protocol support (Phase 4) without breaking changes.

  Scope: Database schema enhancement only - no API changes required (backward compatible).

  Effort: ~30 minutes (1 migration, 2 model updates, 2 test updates)

  ---
  Enhancement 1: Button Options for Interactive Messages

  Rationale

  Minimog §3.2.P4 (lines 446, 456-462) specifies button_options JSONB field for AG-UI interactive elements. Adding now prevents future migration complexity.

  Implementation Checklist

  1. Model Updates

  - File: backend/app/models.py
  - Locate RoomMessage (database model with table=True)
  - Add field after content:
  button_options: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB))
  - Update RoomMessagePublic (API response model) with same field
  - Validation: Field is nullable, no breaking changes

  2. Database Migration

  - Command: docker compose exec backend alembic revision --autogenerate -m "Add button_options to room_messages"
  - Review: Generated migration adds nullable JSONB column
  - Apply: docker compose exec backend alembic upgrade head
  - Verify:
  \d room_messages  -- Check button_options column exists
  SELECT column_name, data_type, is_nullable
  FROM information_schema.columns
  WHERE table_name='room_messages' AND column_name='button_options';

  3. CRUD Updates (Optional - No Logic Changes)

  - File: backend/app/crud.py
  - Action: No changes needed (field is auto-included in model serialization)
  - Note: Agent can populate button_options in future by passing it in event payload

  4. Documentation

  - Add comment to RoomMessage model:
  # AG-UI interactive buttons: [{"label": str, "value": str, "style": str}]
  # Used in Phase 4 for agent-provided UI actions

  ---
  Enhancement 2: Metadata Field for Event Extensibility

  Rationale

  Minimog §3.1.E1 mentions extensible event payloads. Adding generic metadata field enables event enrichment (e.g., trace IDs, performance metrics) without schema changes.

  Implementation Checklist

  1. Model Updates

  - File: backend/app/models.py
  - Locate RoomEvent (database model with table=True)
  - Add field after payload:
  enrichment_metadata: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB))
  - Note: No public model needed (events are internal)

  2. Database Migration

  - Command: docker compose exec backend alembic revision --autogenerate -m "Add metadata to room_events"
  - Review: Generated migration adds nullable JSONB column
  - Apply: docker compose exec backend alembic upgrade head
  - Verify:
  \d room_events  -- Check metadata column exists

  3. Event Emitter Update (Optional)

  - File: backend/app/services/event_emitter.py
  - Action: No changes needed now
  - Future Use: Add optional metadata parameter to emit_event() when needed

  4. Documentation

  - Add comment to RoomEvent model:
  # Optional metadata for event enrichment (trace IDs, performance metrics, etc.)
  # Use sparingly - keep events focused on domain logic in payload

  ---
  Testing Strategy

  Integration Tests

  - File: backend/app/tests/api/routes/test_rooms.py
  - Test: Verify GET /rooms/{id}/messages returns button_options: null for existing messages
  - Test: Verify messages with button_options (when added) serialize correctly

  Database Tests

  - File: backend/app/tests/test_models.py (or create if not exists)
  - Test: Create RoomMessage with button_options and verify persistence
  - Test: Create RoomEvent with metadata and verify persistence

  Backward Compatibility

  - Run existing test suite: docker compose exec backend pytest
  - Expected: All 19+ tests pass (nullable fields don't break existing logic)

  ---
  Migration Execution Plan

  Pre-Migration Checklist

  - Backup current database schema (if production):
  docker compose exec db pg_dump -U postgres -d tinyfoot > backup_pre_button_metadata.sql
  - Review current migration status: docker compose exec backend alembic current

  Execution Sequence

  # 1. Enter backend container
  docker compose exec backend bash

  # 2. Create migrations (in sequence)
  alembic revision --autogenerate -m "Add button_options to room_messages"
  alembic revision --autogenerate -m "Add metadata to room_events"

  # 3. Review generated files
  cat app/alembic/versions/*_add_button_options*.py
  cat app/alembic/versions/*_add_metadata*.py

  # 4. Apply migrations
  alembic upgrade head

  # 5. Verify
  alembic current
  psql -U postgres -d tinyfoot -c "\d room_messages"
  psql -U postgres -d tinyfoot -c "\d room_events"

  Post-Migration Verification

  - Check migration history: docker compose exec backend alembic history
  - Verify no errors in application logs: docker compose logs backend --tail=50
  - Run smoke test: Create room → Send message → Verify response includes button_options: null

  ---
  Rollback Plan (If Needed)

  # Identify current revision
  docker compose exec backend alembic current

  # Rollback one migration
  docker compose exec backend alembic downgrade -1

  # Rollback both migrations
  docker compose exec backend alembic downgrade -2

  # Restore from backup (if critical)
  docker compose exec -T db psql -U postgres -d tinyfoot < backup_pre_button_metadata.sql

  ---
  Alignment with Project Standards

  RULES.md Compliance

  - ✅ Database Migration Workflow (§151-191): Follows autogenerate → review → apply pattern
  - ✅ SQLModel Patterns (§54-98): Nullable fields on database models with proper type hints
  - ✅ No Breaking Changes: Existing API contracts unchanged (backward compatible)

  Data Model Best Practices Compliance

  - ✅ Field Definitions: Using Field() with sa_column for SQLAlchemy-specific column types (JSONB)
  - ✅ Type Hints: dict[str, Any] | None for proper type checking
  - ✅ No Relationship Changes: Pure field additions (no circular reference concerns)

  Steel Thread Alignment

  - ✅ Phase Boundary: Enhancements are Phase 3/4 prep, don't block current work
  - ✅ Event Sourcing: Metadata field maintains immutability principle (events never updated)
  - ✅ Projection Pattern: button_options in projection, not event log (follows CQRS)

  ---
  Success Criteria

  - Migrations applied cleanly (exit code 0)
  - room_messages.button_options column exists as nullable JSONB
  - room_events.metadata column exists as nullable JSONB
  - All existing tests pass (19/19 minimum)
  - GET /rooms/{id}/messages response includes button_options field (null for existing messages)
  - No API breaking changes (frontend requires no updates)

  ---
  Optional: Future Usage Examples

  Button Options (Phase 4 - AG-UI):
  # In agent_runner.py when emitting room_message.agent event
  await emit_event(
      room_id=room_id,
      event_type="room_message.agent",
      payload={
          "agent_name": "StoryAdvisor",
          "content": "Would you like me to analyze your pacing?",
          "button_options": [
              {"label": "Yes, analyze", "value": "analyze_pacing", "style": "primary"},
              {"label": "No, thanks", "value": "skip", "style": "secondary"}
          ]
      }
  )

  Event Metadata (Phase 4 - Observability):
  # In emit_event() for tracing
  await emit_event(
      room_id=room_id,
      event_type="room_message.agent",
      payload={...},
      enrichment_ metadata={
          "trace_id": request_context.trace_id,
          "latency_ms": 1234,
          "model": "gpt-4"
      }
  )

  ---
  Recommendation

  Proceed immediately - These are zero-risk additions that prevent future migration complexity. Total effort: ~30 minutes. Can be done in parallel with Phase 3 planning.