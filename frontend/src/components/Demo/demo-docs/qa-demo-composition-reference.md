# QA Demo Composition Reference
> Purpose: copy/paste-ready composition payloads for creating and testing demos with panels, content, layout control, and theming.

## Scope
Use these payloads with:
- `PUT /api/v1/demos/configs/{demo_config_id}/composition`
- `PATCH /api/v1/demos/configs/{demo_config_id}/composition`
- `POST /api/v1/demos/{slug}/session` (to validate resolved runtime/demo behavior)

This aligns with the current `DemoPageComposition` contract.

## 1) Base Template (Full Replace)
```json
{
  "schema_version": 1,
  "layout_mode": "panels",
  "runtime_policy": "auto",
  "persona_policy": "first_available",
  "chat_mode": "participant",
  "fixed_user_persona_id": null,
  "page_theme_id": null,
  "cards_theme_id": null,
  "presentation_json": {},
  "panels": [
    {
      "id": "story-runtime-primary",
      "kind": "storyRuntime",
      "prominence": "primary",
      "order": 1,
      "title": "Story",
      "default_size": 65,
      "min_size": 30,
      "max_size": 85,
      "viewport_mode": "panel",
      "options": {
        "send_runtime_events_to_chat": true,
        "viewer_mode": false
      }
    },
    {
      "id": "chat-aux",
      "kind": "chat",
      "prominence": "auxiliary",
      "order": 2,
      "title": "Chat",
      "default_size": 35,
      "min_size": 20,
      "max_size": 50,
      "viewport_mode": "panel",
      "options": {
        "mode": "participant",
        "include_internal_messages": false
      }
    }
  ],
  "blocks": [
    {
      "id": "context-top",
      "type": "context",
      "region": "top",
      "order": 1,
      "title": "Demo Context",
      "visibility": "visible",
      "presentation_json": {},
      "config_json": {},
      "content_json": {
        "format": "markdown",
        "value": "## Demo Context\nThis block stays constant while the user interacts with story and chat.",
        "metadata": {
          "variant": "card",
          "label": "Overview"
        }
      }
    }
  ],
  "metadata_json": {
    "description": "QA baseline composition",
    "auto_respond": true
  }
}
```

## 2) Example: Required QA Story + Room + Constant Content
Use this to validate the product requirement: constant top content + story runtime + chat in same demo room.

```json
{
  "schema_version": 1,
  "layout_mode": "panels",
  "runtime_policy": "auto",
  "persona_policy": "first_available",
  "chat_mode": "participant",
  "panels": [
    {
      "id": "story",
      "kind": "storyRuntime",
      "prominence": "primary",
      "order": 1,
      "title": "Story Runtime",
      "default_size": 68,
      "min_size": 35,
      "viewport_mode": "panel",
      "options": {
        "send_runtime_events_to_chat": true
      }
    },
    {
      "id": "chat",
      "kind": "chat",
      "prominence": "auxiliary",
      "order": 2,
      "title": "Room Chat",
      "default_size": 32,
      "min_size": 20,
      "viewport_mode": "panel",
      "options": {
        "mode": "participant"
      }
    }
  ],
  "blocks": [
    {
      "id": "intro",
      "type": "content",
      "region": "top",
      "order": 1,
      "title": "Instructions",
      "content_json": {
        "format": "markdown",
        "value": "### Test Steps\n1. Start runtime (or confirm auto-start)\n2. Make one story choice\n3. Send chat message\n4. Verify block remains constant",
        "metadata": {
          "variant": "card"
        }
      }
    }
  ],
  "metadata_json": {
    "auto_respond": true
  }
}
```

## 3) Example: Multiplayer/Observer Demo (Chat + Participant Panel)
```json
{
  "schema_version": 1,
  "layout_mode": "panels",
  "runtime_policy": "manual",
  "persona_policy": "first_available",
  "chat_mode": "observer",
  "panels": [
    {
      "id": "chat-main",
      "kind": "chat",
      "prominence": "primary",
      "order": 1,
      "title": "Conversation",
      "default_size": 70,
      "min_size": 35,
      "options": {
        "mode": "observer",
        "include_internal_messages": true
      }
    },
    {
      "id": "participants",
      "kind": "participantPanel",
      "prominence": "auxiliary",
      "order": 2,
      "title": "Participants",
      "default_size": 30
    }
  ],
  "blocks": [
    {
      "id": "context",
      "type": "context",
      "region": "top",
      "order": 1,
      "title": "What You Are Seeing",
      "content_json": {
        "format": "markdown",
        "value": "Observer mode: verify multiple humans/agents are legible."
      }
    }
  ],
  "metadata_json": {}
}
```

## 4) Example: Page-Sized Panel
Use to verify full-viewport panel behavior.

```json
{
  "schema_version": 1,
  "layout_mode": "panels",
  "runtime_policy": "manual",
  "persona_policy": "first_available",
  "chat_mode": "participant",
  "panels": [
    {
      "id": "canvas-full",
      "kind": "canvas",
      "prominence": "primary",
      "order": 1,
      "title": "Canvas",
      "viewport_mode": "page"
    }
  ],
  "blocks": [],
  "metadata_json": {
    "note": "Only one panel may use viewport_mode='page'"
  }
}
```

## 5) Example: Theme Overrides
Apply composition-level and panel-level theming.

```json
{
  "schema_version": 1,
  "layout_mode": "panels",
  "runtime_policy": "auto",
  "persona_policy": "first_available",
  "chat_mode": "participant",
  "page_theme_id": "11111111-1111-1111-1111-111111111111",
  "cards_theme_id": "22222222-2222-2222-2222-222222222222",
  "panels": [
    {
      "id": "story",
      "kind": "storyRuntime",
      "prominence": "primary",
      "order": 1,
      "theme_id": "33333333-3333-3333-3333-333333333333",
      "presentation_json": {
        "chrome": "minimal"
      }
    },
    {
      "id": "chat",
      "kind": "chat",
      "prominence": "auxiliary",
      "order": 2
    }
  ],
  "blocks": [
    {
      "id": "context",
      "type": "content",
      "region": "top",
      "order": 1,
      "theme_id": "44444444-4444-4444-4444-444444444444",
      "presentation_json": {
        "density": "comfortable"
      },
      "content_json": {
        "format": "markdown",
        "value": "Theme override example"
      }
    }
  ],
  "metadata_json": {}
}
```

## 6) Patch Example (Minimal)
Change runtime policy and add one block without replacing the full composition.

```json
{
  "runtime_policy": "owner_only",
  "blocks": [
    {
      "id": "test-status",
      "type": "content",
      "region": "top",
      "order": 99,
      "title": "Run Status",
      "content_json": {
        "format": "markdown",
        "value": "Owner-only runtime policy is active."
      }
    }
  ]
}
```

## Validation Checklist (QA)
1. `POST /demos/{slug}/session` returns:
- `composition`
- `composition_source`
- `room` and `runtime` contexts.
2. Panel order/size/prominence matches JSON.
3. `viewport_mode="page"` consumes full workspace.
4. Constant content block remains visible through story/chat actions.
5. Theme bindings + overrides apply at page/cards/panel/block levels.
6. Runtime policy behavior matches `auto` / `manual` / `owner_only`.

## Appendix A: Field Domains and Combinatorics

### A.1 Where to set `story_id` for a demo
For new demo room creation, backend now resolves story in this order:
1. `composition.metadata_json.story_id`
2. `demo_config.metadata_json.story_id`
3. `null` (no story attached)

Expected type: UUID string (must reference an existing Story row).

If an invalid/non-existent story id is configured, resolve/create session returns `400`.

### A.2 Top-level composition fields

| Field | Type | Domain / Allowed Values | Notes |
|---|---|---|---|
| `schema_version` | number | `>= 1` | Current value: `1` |
| `layout_mode` | string | `"panels"` or `"tabs"` | Shell preference |
| `runtime_policy` | string | `"auto"`, `"manual"`, `"owner_only"` | Runtime bootstrap behavior |
| `persona_policy` | string | `"first_available"`, `"fixed_user_persona"`, `"manual_prompt"` | Persona selection strategy |
| `chat_mode` | string | `"participant"` or `"observer"` | Chat panel mode default |
| `fixed_user_persona_id` | UUID/null | Valid UUID or null | Required when `persona_policy=fixed_user_persona` |
| `page_theme_id` | UUID/null | Valid UUID or null | Composition-level page theme |
| `cards_theme_id` | UUID/null | Valid UUID or null | Composition-level cards theme |
| `presentation_json` | object | free-form JSON object | UI/render hints |
| `panels` | array | `DemoPanelSpec[]` | At least one panel OR block required |
| `blocks` | array | `DemoBlockSpec[]` | Optional but recommended for context |
| `metadata_json` | object | free-form JSON object | Recommended place for demo-specific flags |

### A.3 Panel fields

| Field | Type | Domain / Allowed Values | Notes |
|---|---|---|---|
| `id` | string | unique per panel list | Required |
| `kind` | string | `"chat"`, `"storyRuntime"`, `"participantPanel"`, `"content"`, `"a2ui"`, `"debug"`, `"canvas"`, `"storyEditor"`, `"storyPlayer"` | Renderer support may vary by frontend wiring |
| `prominence` | string | `"primary"` or `"auxiliary"` | Controls layout grouping |
| `order` | number | integer `>= 1` | Sort order |
| `title` | string/null | any | Optional display label |
| `default_size` | number/null | `1..100` | Preferred initial split |
| `min_size` | number/null | `1..100` | Minimum split size |
| `max_size` | number/null | `1..100` | Maximum split size |
| `viewport_mode` | string | `"panel"` or `"page"` | Max one panel may be `"page"` |
| `theme_id` | UUID/null | valid UUID or null | Panel-level theme override |
| `presentation_json` | object | free-form JSON object | Panel presentation overrides |
| `options` | object | kind-specific | See below |

Kind-specific `options`:
- `chat`: `mode` (`participant|observer`), `include_internal_messages` (bool)
- `storyRuntime`: `send_runtime_events_to_chat` (bool), `viewer_mode` (bool)
- `content`: `sticky` (bool), `content_json` (Content object)
- others: generic `options.data` object

### A.4 Block fields

| Field | Type | Domain / Allowed Values | Notes |
|---|---|---|---|
| `id` | string | unique per block list | Required |
| `type` | string | `"context"`, `"story"`, `"agentRoster"`, `"orchestratorState"`, `"toolCapability"`, `"contributionFeed"`, `"content"` | |
| `region` | string | `"top"`, `"primary"`, `"auxiliary"`, `"footer"` | Placement hint |
| `order` | number | integer `>= 1` | Sort order in region |
| `title` | string/null | any | Optional |
| `visibility` | string | `"visible"` or `"hidden"` | |
| `theme_id` | UUID/null | valid UUID or null | Block-level theme override |
| `presentation_json` | object | free-form JSON object | Render/display hints |
| `config_json` | object | free-form JSON object | Block config |
| `content_json` | object | Content object (recommended) | Payload rendered by content-capable blocks |

### A.5 High-value combinatoric test matrix

1. Runtime policy x story attachment
- `auto/manual/owner_only` x `{story_id set, story_id missing}`

2. Panel layout permutations
- `{1 primary}`, `{1 primary + 1 aux}`, `{2 primary + 2 aux}`, `{1 page-sized}`

3. Theme layering
- `{no theme}`, `{composition page/cards}`, `{panel override}`, `{block override}`, `{all combined}`

4. Content format coverage in `content_json`
- `markdown`, `json`, `html`, `svg`, `code`, `image`

5. Persona policy coverage
- `first_available`, `fixed_user_persona` (with valid id), `manual_prompt`

## Appendix B: Web UI API Walkthroughs (Step-by-Step)

Assumptions:
1. You are already authenticated in the Web UI API tool.
2. You have a valid `story_id` UUID available.
3. Frontend demo route is available at:
- `https://<frontend-host>/demo/<demo-slug>`

General note on identifiers:
1. `demo_config_id` comes from the `POST /api/v1/demos/` response.
2. `demo_slug` is the slug you send in that same create call.

### Walkthrough 1: Baseline Template

Step 1: Call `POST /api/v1/demos/` with payload:
```json
{
  "slug": "qa-baseline-template",
  "title": "QA Baseline Template",
  "scope": "personal",
  "is_active": true,
  "default_auto_respond": true,
  "metadata_json": {}
}
```

Step 2: Call `PUT /api/v1/demos/configs/{demo_config_id}/composition` with the **Base Template** payload from Section 1, and set:
- `metadata_json.story_id = "<your-story-id>"`

Step 3: Call `POST /api/v1/demos/qa-baseline-template/session` with no body.

Step 4: Open:
- `https://<frontend-host>/demo/qa-baseline-template`

Expected browser result:
1. A demo header and a two-panel layout (Story + Chat).
2. Top context block content visible and persistent.
3. Story runtime available for start/auto-start depending on runtime state/policy.

### Walkthrough 2: Required QA Story + Room + Constant Content

Step 1: Call `POST /api/v1/demos/` with payload:
```json
{
  "slug": "qa-story-chat-constant-content",
  "title": "QA Story Chat Constant Content",
  "scope": "personal",
  "is_active": true,
  "default_auto_respond": true,
  "metadata_json": {}
}
```

Step 2: Call `PUT /api/v1/demos/configs/{demo_config_id}/composition` with the **Example: Required QA Story + Room + Constant Content** payload from Section 2, and set:
- `metadata_json.story_id = "<your-story-id>"`

Step 3: Call `POST /api/v1/demos/qa-story-chat-constant-content/session`.

Step 4: Open:
- `https://<frontend-host>/demo/qa-story-chat-constant-content`

Expected browser result:
1. Constant top content/instructions block remains visible during interaction.
2. Story panel and chat panel both active in same demo room.
3. You can make a story choice and send chat messages without losing the top block.

### Walkthrough 3: Multiplayer / Observer Demo

Step 1: Call `POST /api/v1/demos/` with payload:
```json
{
  "slug": "qa-multiplayer-observer",
  "title": "QA Multiplayer Observer",
  "scope": "personal",
  "is_active": true,
  "default_auto_respond": false,
  "metadata_json": {}
}
```

Step 2: Call `PUT /api/v1/demos/configs/{demo_config_id}/composition` with the **Example: Multiplayer/Observer Demo** payload from Section 3.

Optional story binding for this scenario:
- `metadata_json.story_id = "<your-story-id>"` (only if you also want runtime checks)

Step 3: Call `POST /api/v1/demos/qa-multiplayer-observer/session`.

Step 4: Open:
- `https://<frontend-host>/demo/qa-multiplayer-observer`

Expected browser result:
1. Chat-focused layout with participant panel (if mapped in current frontend panel wiring).
2. Chat mode should reflect observer settings.
3. Context block explains observer scenario.

### Walkthrough 4: Page-Sized Panel

Step 1: Call `POST /api/v1/demos/` with payload:
```json
{
  "slug": "qa-page-sized-panel",
  "title": "QA Page Sized Panel",
  "scope": "personal",
  "is_active": true,
  "default_auto_respond": false,
  "metadata_json": {}
}
```

Step 2: Call `PUT /api/v1/demos/configs/{demo_config_id}/composition` with the **Example: Page-Sized Panel** payload from Section 4.

Step 3: Call `POST /api/v1/demos/qa-page-sized-panel/session`.

Step 4: Open:
- `https://<frontend-host>/demo/qa-page-sized-panel`

Expected browser result:
1. The configured page-sized panel consumes the available workspace.
2. Split-panel chrome should be minimized/absent for that view mode.

### Walkthrough 5: Theme Overrides

Step 1: Call `POST /api/v1/demos/` with payload:
```json
{
  "slug": "qa-theme-overrides",
  "title": "QA Theme Overrides",
  "scope": "personal",
  "is_active": true,
  "default_auto_respond": true,
  "metadata_json": {}
}
```

Step 2: Call `PUT /api/v1/demos/configs/{demo_config_id}/composition` with the **Example: Theme Overrides** payload from Section 5.

Important:
1. Replace placeholder theme UUIDs with real theme IDs from your environment.
2. To include story runtime testing, set `metadata_json.story_id = "<your-story-id>"`.

Step 3: Call `POST /api/v1/demos/qa-theme-overrides/session`.

Step 4: Open:
- `https://<frontend-host>/demo/qa-theme-overrides`

Expected browser result:
1. Page/cards theme cascade applied.
2. Panel/block-level theme overrides applied where specified.
3. Theme picker interactions still work on top of authored defaults.
