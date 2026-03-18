# Tesser Studio: SVG Library Integration

**Date**: 2026-03-18
**Status**: Approved for MVP

## Overview

Add a "Tesser Studio" panel to the SVG pages that enables users to generate SVGs via any Tesser script, with dynamic form controls based on each script's `input_schema`, and auto-save results to the SVG library.

This turns Tesser from a "demo-only" tool into a general-purpose SVG creation engine accessible from the SVG management interface.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     SvgShell                                │
├──────────────┬──────────────────┬──────────────────────────┤
│ Gallery      │ Operations       │ Tesser Studio (NEW)      │
│ Panel        │ Panel            │                          │
│              │                  │  ┌─────────────────────┐ │
│              │                  │  │ Script Selector     │ │
│              │                  │  ├─────────────────────┤ │
│              │                  │  │ Presets (optional)  │ │
│              │                  │  ├─────────────────────┤ │
│              │                  │  │ Dynamic Form        │ │
│              │                  │  │ (from input_schema) │ │
│              │                  │  ├─────────────────────┤ │
│              │                  │  │ [Generate] Button   │ │
│              │                  │  ├─────────────────────┤ │
│              │                  │  │ Jobs List           │ │
│              │                  │  └─────────────────────┘ │
└──────────────┴──────────────────┴──────────────────────────┘
```

## Data Flow

1. Frontend fetches available scripts → `GET /tesser/scripts`
2. User selects script → fetch schema via `GET /tesser/scripts/{name}/help`
3. User fills dynamic form (or loads preset) → clicks Generate
4. Frontend calls `POST /tesser/scripts/{name}/enqueue` (async)
5. Job ID returned → added to jobs list, poll for status
6. On completion → frontend calls `POST /svgs/from-tesser-job` → gallery refreshes
7. On failure → same endpoint creates failed asset placeholder

## Schema-Driven Form Builder

### Component Structure

```
TesserStudioPanel
├── ScriptSelector (dropdown of available scripts)
├── SchemaForm (dynamic form builder)
│   ├── SchemaField (recursive component)
│   │   ├── StringField (text input, textarea, color picker)
│   │   ├── NumberField (input with optional slider)
│   │   ├── BooleanField (checkbox/switch)
│   │   ├── EnumField (select dropdown)
│   │   ├── ArrayField (list with add/remove)
│   │   │   └── SchemaField (recursive for array items)
│   │   ├── ObjectField (collapsible group)
│   │   │   └── SchemaField (recursive for properties)
│   │   └── ConditionalField (show/hide based on other values)
│   └── FormActions (Generate button, Reset)
└── TesserJobsList (polling job status)
```

### Field Type Mapping

| JSON Schema | UI Control |
|-------------|------------|
| `type: "string"` | Text input |
| `type: "string", format: "color"` | Color picker |
| `type: "string", enum: [...]` | Select dropdown |
| `type: "number"` | Number input (+ slider if min/max defined) |
| `type: "boolean"` | Switch |
| `type: "array"` | List with add/remove buttons |
| `type: "object"` | Collapsible fieldset |
| `if/then/else` or `dependencies` | Conditional visibility |

### State Management

- React Hook Form with recursive schema walker
- Values collected into single `script_input` object matching schema structure
- Presets stored as JSON objects matching schema shape

## Auto-Save Workflow

### Success Case

```python
svg_asset = SvgAsset(
    name=f"{script_name}-{short_uuid}",
    description="",
    visibility="private",
    svg_markup=render_result["svg"],
    metadata_json={
        "source": "tesser",
        "script": script_name,
        "script_input": script_input,
    },
    owner_id=current_user.id,
)
```

### Failure Case

```python
svg_asset = SvgAsset(
    name=f"{script_name}-failed-{short_uuid}",
    svg_markup="",
    metadata_json={
        "source": "tesser",
        "script": script_name,
        "script_input": script_input,
        "error": error_message,
        "failed": True,
    },
    owner_id=current_user.id,
)
```

### Gallery Integration

- Failed assets render with error indicator (red border, error icon)
- All assets editable (name, description) after creation

## Backend Changes

### New Endpoint

```
POST /svgs/from-tesser-job
Body: { job_id: string, name?: string, description?: string }
Returns: SvgAssetPublic
```

Logic:
1. Fetch job status from Tesser
2. If completed: create SvgAsset with svg_markup and metadata
3. If failed: create SvgAsset with empty markup and error in metadata
4. If still running: return 409 Conflict

### Existing Endpoints (no changes)

- `GET /tesser/scripts` — List available scripts
- `GET /tesser/scripts/{name}/help` — Get input_schema
- `POST /tesser/scripts/{name}/enqueue` — Queue async job
- `GET /tesser/jobs/{job_id}` — Poll job status

## Frontend File Structure

```
frontend/src/components/Svg/
├── TesserStudio/
│   ├── TesserStudioPanel.tsx
│   ├── ScriptSelector.tsx
│   ├── SchemaForm/
│   │   ├── SchemaForm.tsx
│   │   ├── SchemaField.tsx
│   │   ├── fields/
│   │   │   ├── StringField.tsx
│   │   │   ├── NumberField.tsx
│   │   │   ├── BooleanField.tsx
│   │   │   ├── EnumField.tsx
│   │   │   ├── ArrayField.tsx
│   │   │   └── ObjectField.tsx
│   │   └── utils/
│   │       ├── schemaParser.ts
│   │       └── defaultValues.ts
│   ├── PresetSelector.tsx
│   ├── TesserJobsList.tsx
│   └── types.ts

frontend/src/hooks/
├── useTesserScripts.ts
├── useTesserJob.ts
└── useSaveFromTesserJob.ts
```

## MVP Scope

### In Scope

- Tesser Studio panel in SvgShell
- Dynamic script selector (all scripts from API)
- Schema-driven form builder (primitives, arrays, nested objects, conditionals)
- Presets support (load preset → populate form)
- Async job submission via enqueue
- Simple jobs list with polling
- Frontend-driven auto-save on completion
- Failed asset placeholders with error metadata
- New backend endpoint: `POST /svgs/from-tesser-job`
- Metadata: source, script, script_input

### Out of Scope (Future)

- Batch job creation UI
- WebSocket real-time updates
- Backend callback-based auto-save
- Retry button on failed assets
- Preset management UI

## Implementation Order

1. Backend: `POST /svgs/from-tesser-job` endpoint
2. Frontend: Hooks (`useTesserScripts`, `useTesserJob`, `useSaveFromTesserJob`)
3. Frontend: SchemaForm components (core complexity)
4. Frontend: TesserStudioPanel assembly
5. Frontend: Integrate into SvgShell
6. Test end-to-end with existing Tesser scripts

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Panel location | New dedicated panel | Prominence for Tesser as first-class tool |
| Script loading | All scripts dynamically | Future scripts "just work" |
| Form approach | Schema-driven | Handles extensive parameterization |
| UX model | Presets + Advanced | Progressive disclosure |
| Save trigger | Frontend-driven (Option B) | Simpler than Redis callbacks for v1 |
| Job tracking | Simple polling list | Leverage existing infrastructure |
| Failure handling | Placeholder assets | Visibility without separate error system |
| Metadata | Reproducible, no provenance | Practical without audit overhead |
