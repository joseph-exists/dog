> Deprecated: consolidated into `frontend/src/components/Demo/demo-docs/demo-integration-snapshot.md`.

# Demo Entry Route Mapping Spec

Purpose: define how existing `DemoConfig` / `DemoSession` / room runtime data maps into `ResolveDemoEntryPayload`.

Target response model:
- `ResolveDemoEntryPayload` (see `backend/app/api/demo_page_models.py`)

Route target:
- `POST /api/v1/demos/{slug}/session`

---

## 1) Inputs and Source Models

Primary source models:
- `DemoConfig` (`backend/app/models.py`)
- `DemoSession` (`backend/app/models.py`)
- `Room` (`backend/app/models.py`)
- `RoomParticipant` (`backend/app/models.py`)
- `RoomRuntimePublic` projection (`backend/app/models.py`)

Supporting APIs/services:
- existing demo session resolve flow in `backend/app/api/routes/demos.py`
- room runtime read (`get_room_runtime(...)`) or route equivalent

---

## 2) Field-by-Field Mapping

## 2.1 Top-Level Payload

`ResolveDemoEntryPayload.demo_config_id`
- source: `demo_config.id`

`ResolveDemoEntryPayload.demo_session_id`
- source: `demo_session.id`

`ResolveDemoEntryPayload.created`
- source: session resolve/create branch result

`ResolveDemoEntryPayload.composition_source`
- source precedence:
1. `session_override` when per-session override exists (future table)
2. `demo_config` when config-level composition fields are used
3. `type_defaults` when neither exists and system defaults are injected

`ResolveDemoEntryPayload.composition`
- source: resolved composition algorithm (section 3)

`ResolveDemoEntryPayload.room`
- source: room context mapping (section 2.2)

`ResolveDemoEntryPayload.runtime`
- source: runtime context mapping (section 2.3)

---

## 2.2 `room: DemoResolvedRoomContext`

`room.room_id`
- source: `demo_session.room_id`

`room.story_id`
- source: `room.story_id` from `Room`

`room.title`
- source: `room.title` from `Room`

`room.can_write`
- source: participant role resolution for current user:
1. find active `RoomParticipant` where:
   - `room_id == demo_session.room_id`
   - `participant_type == "user"`
   - `participant_id == str(current_user.id)`
   - `active == True`
2. `can_write = (participant.role == "owner")`
3. fallback `False` if not found

---

## 2.3 `runtime: DemoResolvedRuntimeContext`

`runtime.runtime_policy`
- source precedence:
1. `composition.runtime_policy` (if composition exists)
2. fallback `DemoRuntimePolicy.auto`

`runtime.persona_policy`
- source precedence:
1. `composition.persona_policy`
2. fallback `DemoPersonaPolicy.first_available`

`runtime.has_runtime`
- source:
1. attempt runtime read for `room_id`
2. `True` if runtime exists and returns success
3. `False` on 404/410 (no active runtime)
4. for other errors, propagate route error unless explicitly degraded

`runtime.auto_start_attempted`
`runtime.auto_start_succeeded`
`runtime.auto_start_error`
- source:
1. if policy is `manual`: all false/null
2. if policy is `auto` or `owner_only` and backend executes auto-start:
   - set by backend auto-start branch outcome
3. if auto-start remains frontend-side:
   - route sets false/null (frontend computes runtime bootstrap states)

---

## 3) Composition Resolution Algorithm

## 3.1 Current state compatibility

Existing stored fields in `DemoConfig`:
- `default_panels_json`
- `default_layout_json`
- `metadata_json`
- `default_auto_respond`

No persisted `DemoPageComposition` table yet.

## 3.2 Resolution precedence

1. Session override (future; optional)
- if `DemoSession` override exists, use it
- source=`session_override`

2. Config-level composition
- map from `DemoConfig.default_panels_json` + `default_layout_json` + `metadata_json`
- source=`demo_config`

3. Type defaults
- inject defaults when above are absent/empty/invalid
- source=`type_defaults`

## 3.3 Mapping from existing DemoConfig fields

`composition.schema_version`
- default `1`

`composition.layout_mode`
- source:
1. `demo_config.metadata_json.layout_mode` if valid
2. fallback `panels`

`composition.runtime_policy`
- source:
1. `demo_config.metadata_json.runtime_policy` if valid
2. fallback `auto`

`composition.persona_policy`
- source:
1. `demo_config.metadata_json.persona_policy` if valid
2. fallback `first_available`

`composition.chat_mode`
- source:
1. `demo_config.metadata_json.chat_mode` if valid
2. fallback `participant`

`composition.fixed_user_persona_id`
- source:
1. `demo_config.metadata_json.fixed_user_persona_id` if UUID + policy requires
2. else `None`

`composition.page_theme_id` / `cards_theme_id`
- source:
1. `demo_config.metadata_json.page_theme_id` / `cards_theme_id` if UUID
2. else `None`

`composition.presentation_json`
- source:
1. `demo_config.metadata_json.presentation_json` if object
2. else `{}`

`composition.panels`
- source:
1. parse `demo_config.default_panels_json` into `DemoPanelSpec[]`
2. if empty/invalid, inject defaults:
   - `storyRuntime` primary
   - `chat` auxiliary

`composition.blocks`
- source:
1. parse `demo_config.default_layout_json` into `DemoBlockSpec[]` only when payload represents block rows
2. OR parse `demo_config.metadata_json.blocks` when present
3. fallback `[]`

`composition.metadata_json`
- source: `demo_config.metadata_json` (sanitized dict)

---

## 4) Sanitization / Validation Rules During Mapping

Enforce with `DemoPageCompositionBase` validators after mapping:
- unique panel IDs
- unique block IDs
- max one `viewport_mode="page"` panel
- required `fixed_user_persona_id` when persona policy is fixed
- non-empty composition (at least one panel or block)

Route behavior on invalid mapped config:
- recommended: log warning + fallback to `type_defaults` composition
- set `composition_source="type_defaults"`
- include warning in server logs with `demo_config.id` / `slug`

---

## 5) Pseudocode

```python
async def resolve_demo_entry_payload(
    *,
    session: AsyncSession,
    current_user: User,
    demo_slug: str,
) -> ResolveDemoEntryPayload:
    demo_config = await get_demo_config_by_slug_visible_to_user(...)
    demo_session, created = await get_or_create_demo_session(...)

    room = await get_room_by_id(demo_session.room_id)
    participant = await get_active_user_participant(room.room_id, current_user.id)
    can_write = bool(participant and participant.role == "owner")

    composition, source = resolve_composition_from_config_or_defaults(demo_config)
    # model_validate enforces contract + sanitization fallback policy
    composition = DemoPageCompositionBase.model_validate(composition)

    runtime_policy = composition.runtime_policy
    persona_policy = composition.persona_policy

    runtime = await try_get_runtime(room.room_id)  # returns None on 404/410
    has_runtime = runtime is not None

    # optional backend auto-start block (if implemented backend-side)
    auto_start_attempted = False
    auto_start_succeeded = False
    auto_start_error = None
    if should_backend_auto_start(runtime_policy, can_write, has_runtime):
        auto_start_attempted = True
        try:
            await auto_start_runtime(...)
            auto_start_succeeded = True
            has_runtime = True
        except Exception as exc:
            auto_start_error = str(exc)

    return ResolveDemoEntryPayload(
        demo_config_id=demo_config.id,
        demo_session_id=demo_session.id,
        created=created,
        composition=composition,
        composition_source=source,
        room=DemoResolvedRoomContext(
            room_id=room.room_id,
            story_id=room.story_id,
            title=room.title,
            can_write=can_write,
        ),
        runtime=DemoResolvedRuntimeContext(
            has_runtime=has_runtime,
            runtime_policy=runtime_policy,
            persona_policy=persona_policy,
            auto_start_attempted=auto_start_attempted,
            auto_start_succeeded=auto_start_succeeded,
            auto_start_error=auto_start_error,
        ),
    )
```

---

## 6) Implementation Notes

- This spec allows immediate route integration even before introducing a new DB table for `DemoPageComposition`.
- After composition table exists, only section 3 precedence changes (session/config/default source), payload contract remains stable.
- Given planned client refactor, endpoint can be upgraded to this payload in one cutover.
