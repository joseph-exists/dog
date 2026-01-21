# Pages: Agent-Authored Layout Steel Thread

End-to-end slice: agent proposes a page layout → user accepts → layout saved → page reloads with persisted layout.

## Milestones

- [x] M1: Backend schema + CRUD + API endpoints
- [x] M2: AG-UI schema + event persistence for UI components
- [x] M3: Frontend services + rendering of layout previews
- [x] M4: Page routes load persisted layouts and accept agent proposals
- [ ] M5: Validation, QA, and definition-of-done checklist

## Checkpoints

### M1: Backend schema + CRUD + API endpoints

- [x] Add `pages` table (SQLModel) with JSONB layout storage
- [x] Add Pydantic models for create/update/public
- [x] Add CRUD module for pages
- [x] Add API routes and wire into API router
- [x] Add Alembic migration

#### Schema (SQLModel)

- [x] `Page` table fields
  - [x] `id: uuid.UUID` (PK, default)
  - [x] `entity_type: str` (indexed; e.g., user|agent|team|room)
  - [x] `entity_id: str` (indexed; string to handle UUID or slug)
  - [x] `owner_id: uuid.UUID` (FK user.id, indexed)
  - [x] `layout_version: int` (default 1)
  - [x] `layout_json: dict[str, Any]` (JSONB)
  - [x] `created_at: datetime` (default now)
  - [x] `updated_at: datetime` (default now)
- [x] Unique constraint: `(entity_type, entity_id)`

#### Relationship rules (DATA_MODEL_RULES)

- [x] Define relationships after class definitions using string-based refs
- [x] Keep create/update/public models field-only

#### Pydantic models

- [x] `PageLayoutUpdate`
  - [x] `layout_json: list[TemplateBlock]`
  - [x] `layout_version: int | None`
- [x] `PagePublic`
  - [x] `id, entity_type, entity_id, owner_id, layout_version, layout_json, created_at, updated_at`

#### API endpoints

- [x] `GET /api/v1/pages/{entity_type}/{entity_id}` → `PagePublic | null`
- [x] `POST /api/v1/pages/{entity_type}/{entity_id}/layout` → `PagePublic` (create or overwrite)
- [x] `PUT /api/v1/pages/{page_id}` → `PagePublic` (overwrite layout)
- [x] `DELETE /api/v1/pages/{page_id}` → `{ message }` (optional)

#### Guardrails

- [x] Only owner (or admin) can update/delete
- [ ] Validate layout JSON against `TemplateBlock` schema

### M2: AG-UI schema + UI component persistence

- [x] Add AG-UI component type `page_layout_preview`
  - [x] `layout_json: TemplateBlock[]`
  - [x] `summary?: string`
- [x] Persist `ui_components` in `room_messages` projection (JSONB)
- [x] Ensure `room_message.agent` payload includes `ui_components`
- [x] Filter `agent_internal` messages server-side by default (debug only)

### M3: Frontend services + rendering

- [x] Create `PageService` (ViewModel pattern)
- [x] Avoid new hooks unless approved; use `useQuery` in routes
- [x] Add TS types for `PageLayoutViewModel` and input types
- [x] Extend `AgentUI` types to include `page_layout_preview`
- [ ] Render layout preview component + accept/discard actions

### M4: Page routes load layouts + accept proposals

- [x] User page (`/u/$slug`) loads persisted layout if present
- [x] Team page (`/team/$slug`) loads persisted layout if present
- [x] `PageShell` uses persisted blocks or falls back to template
- [x] Accept action calls `PageService.saveLayout` and invalidates page query

### M5: Validation + QA

- [ ] Manual test: agent proposes layout, user accepts, reload shows saved layout
- [ ] Manual test: user without saved layout sees template
- [ ] Manual test: permissions (non-owner cannot save)
- [ ] Manual test: `agent_internal` messages not visible to standard users

#### Manual Verification Steps

- [ ] Post an agent message containing `page_layout_preview` + `action_buttons` with `page_layout.accept`
- [ ] Click Accept and confirm toast + persisted layout in `GET /api/v1/pages/{entity_type}/{entity_id}`
- [ ] Reload the target page and confirm block order matches the preview

## Checklists

### Implementation Checklist

- [x] Add `Page` models in `backend/app/models.py`
- [x] Add `crud_pages.py`
- [x] Add `pages.py` routes
- [x] Wire routes in `backend/app/api/main.py`
- [x] Add migration
- [x] Add `ui_components` to RoomMessage projection + API
- [x] Add AG-UI `page_layout_preview` schema
- [x] Add `PageService` in `frontend/src/services/pageService.ts`
- [x] Update `/u/$slug` and `/team/$slug` routes to use `PageService`
- [x] Update `AgentUI` types and renderer

### Definition of Done

- [x] Backend stores and returns page layout JSON for an entity
- [x] Frontend loads persisted layout and renders blocks correctly
- [x] Agent can propose a layout and user can accept it
- [x] Accept action persists layout and page reload shows the saved layout
- [x] No raw API types used in components (ViewModel only)
- [x] No new hooks added without approval
- [ ] All new code has JSDoc and no throwaway code
- [x] `agent_internal` messages hidden by default
- [ ] full integration with Shadow Forge (SHADOW_PAGES)
- [ ] Reference Card documentation for engineers to extend into other areas of the application
- [ ] typer review for inclusion

## Notes

- Layout JSON must match `TemplateBlock` shape from `frontend/src/components/Page/registry/pageTemplates.ts`.
- Persisted `ui_components` are ephemeral; the saved page layout is the durable artifact.
