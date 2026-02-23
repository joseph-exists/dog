# QA Content + Block Browser Validation Reference
> Purpose: fast, repeatable browser validation of content formats and block behavior using demo composition APIs.

## Scope
Use this with:
- `POST /api/v1/demos/`
- `PUT /api/v1/demos/configs/{demo_config_id}/composition`
- `POST /api/v1/demos/{slug}/session`

Frontend route:
- `https://<frontend-host>/demo/<slug>`

Assumptions:
1. You are authenticated in the Web UI API tool.
2. You have a valid `story_id` UUID if you want story/runtime checks.

---

## Quick Pattern (Same for Every Example)
Step 1: `POST /api/v1/demos/` to create a config (`slug`, `title`, `scope=personal`).

Step 2: `PUT /api/v1/demos/configs/{demo_config_id}/composition` with the example payload.

Step 3: `POST /api/v1/demos/{slug}/session`.

Step 4: Open `https://<frontend-host>/demo/{slug}` and validate expected UI behavior.

---

## Example 1: Markdown Context Block (Top Region)
Step 1 payload:
```json
{
  "slug": "qa-content-markdown-top",
  "title": "QA Markdown Top Block",
  "scope": "personal",
  "is_active": true,
  "default_auto_respond": true,
  "metadata_json": {}
}
```

Step 2 payload:
```json
{
  "schema_version": 1,
  "layout_mode": "panels",
  "runtime_policy": "manual",
  "persona_policy": "first_available",
  "chat_mode": "participant",
  "panels": [
    { "id": "chat", "kind": "chat", "prominence": "primary", "order": 1, "title": "Chat" }
  ],
  "blocks": [
    {
      "id": "md-top",
      "type": "context",
      "region": "top",
      "order": 1,
      "title": "Overview",
      "visibility": "visible",
      "content_json": {
        "format": "markdown",
        "value": "## Markdown Block\n- bullet A\n- bullet B\n`inline code`",
        "metadata": { "variant": "card" }
      }
    }
  ],
  "metadata_json": {}
}
```

Expected browser result:
1. Markdown block appears above panel area.
2. Heading/list/inline code formatting renders correctly.
3. Chat panel remains functional below.

---

## Example 2: Code Block (Shiki Highlighting)
Step 1 payload:
```json
{
  "slug": "qa-content-code-shiki",
  "title": "QA Code Block Shiki",
  "scope": "personal",
  "is_active": true,
  "default_auto_respond": true,
  "metadata_json": {}
}
```

Step 2 payload:
```json
{
  "schema_version": 1,
  "layout_mode": "panels",
  "runtime_policy": "manual",
  "persona_policy": "first_available",
  "chat_mode": "participant",
  "panels": [
    { "id": "chat", "kind": "chat", "prominence": "auxiliary", "order": 2, "title": "Chat" }
  ],
  "blocks": [
    {
      "id": "code-top",
      "type": "content",
      "region": "top",
      "order": 1,
      "title": "Code Snippet",
      "content_json": {
        "format": "code",
        "value": "def greet(name: str) -> str:\n    return f\"hello {name}\"",
        "metadata": {
          "variant": "card",
          "options": {
            "language": "python",
            "lineNumbers": true,
            "highlightLines": [2],
            "copyable": true
          }
        }
      }
    }
  ],
  "metadata_json": {}
}
```

Expected browser result:
1. Code is syntax-highlighted (Shiki path).
2. Line numbers and highlighted line styling visible.
3. Copy button appears on hover.

---

## Example 3: JSON Content Panel (Panel Payload)
Step 1 payload:
```json
{
  "slug": "qa-content-panel-json",
  "title": "QA Content Panel JSON",
  "scope": "personal",
  "is_active": true,
  "default_auto_respond": true,
  "metadata_json": {}
}
```

Step 2 payload:
```json
{
  "schema_version": 1,
  "layout_mode": "panels",
  "runtime_policy": "manual",
  "persona_policy": "first_available",
  "chat_mode": "participant",
  "panels": [
    {
      "id": "json-content",
      "kind": "content",
      "prominence": "primary",
      "order": 1,
      "title": "JSON Content",
      "options": {
        "content_json": {
          "format": "json",
          "value": {
            "testCase": "content-panel-json",
            "flags": { "a": true, "b": false },
            "items": [1, 2, 3]
          },
          "metadata": {
            "variant": "card",
            "options": { "viewMode": "tree", "interactive": true }
          }
        }
      }
    },
    { "id": "chat", "kind": "chat", "prominence": "auxiliary", "order": 2, "title": "Chat" }
  ],
  "blocks": [],
  "metadata_json": {}
}
```

Expected browser result:
1. Content panel renders authored JSON payload (not the `ContentRendererDemo` showcase).
2. JSON viewer behavior matches options.
3. Auxiliary chat remains present.

---

## Example 4: HTML and Safety Check
Step 1 payload:
```json
{
  "slug": "qa-content-html-safety",
  "title": "QA HTML Safety",
  "scope": "personal",
  "is_active": true,
  "default_auto_respond": true,
  "metadata_json": {}
}
```

Step 2 payload:
```json
{
  "schema_version": 1,
  "layout_mode": "panels",
  "runtime_policy": "manual",
  "persona_policy": "first_available",
  "chat_mode": "participant",
  "panels": [{ "id": "chat", "kind": "chat", "prominence": "primary", "order": 1 }],
  "blocks": [
    {
      "id": "html-top",
      "type": "content",
      "region": "top",
      "order": 1,
      "content_json": {
        "format": "html",
        "value": "<div><h3>Safe HTML</h3><p><strong>Bold</strong> text</p><script>alert('x')</script></div>",
        "metadata": { "variant": "card", "options": { "sanitize": true } }
      }
    }
  ],
  "metadata_json": {}
}
```

Expected browser result:
1. HTML structure renders.
2. Unsafe script content is not executed/rendered as active script.

---

## Example 5: Region Ordering + Hidden Block + Story Integration
Step 1 payload:
```json
{
  "slug": "qa-block-regions-order-hidden",
  "title": "QA Regions Order Hidden",
  "scope": "personal",
  "is_active": true,
  "default_auto_respond": true,
  "metadata_json": {}
}
```

Step 2 payload (replace `<story-id>`):
```json
{
  "schema_version": 1,
  "layout_mode": "panels",
  "runtime_policy": "auto",
  "persona_policy": "first_available",
  "chat_mode": "participant",
  "panels": [
    { "id": "story", "kind": "storyRuntime", "prominence": "primary", "order": 1, "title": "Story" },
    { "id": "chat", "kind": "chat", "prominence": "auxiliary", "order": 2, "title": "Chat" }
  ],
  "blocks": [
    {
      "id": "top-2",
      "type": "content",
      "region": "top",
      "order": 2,
      "content_json": { "format": "markdown", "value": "Top block order 2" }
    },
    {
      "id": "top-1",
      "type": "content",
      "region": "top",
      "order": 1,
      "content_json": { "format": "markdown", "value": "Top block order 1" }
    },
    {
      "id": "aux-note",
      "type": "content",
      "region": "auxiliary",
      "order": 1,
      "content_json": { "format": "markdown", "value": "Auxiliary region block" }
    },
    {
      "id": "hidden-one",
      "type": "content",
      "region": "footer",
      "order": 1,
      "visibility": "hidden_unmounted",
      "content_json": { "format": "markdown", "value": "Should not render" }
    }
  ],
  "metadata_json": {
    "story_id": "<story-id>",
    "description": "Region + hidden block validation"
  }
}
```

Expected browser result:
1. Story panel + chat panel visible.
2. Top region blocks render in order (`top-1` before `top-2`).
3. Auxiliary region block renders in side support area.
4. Hidden block does not render.
5. Demo room resolves with story association and runtime flow.

---

## Example 6: Hidden-Mounted + Runtime-Coupled Blocks (B/C Readiness)
Step 1 payload:
```json
{
  "slug": "qa-hidden-mounted-runtime-blocks",
  "title": "QA Hidden Mounted Runtime Blocks",
  "scope": "personal",
  "is_active": true,
  "default_auto_respond": true,
  "metadata_json": {}
}
```

Step 2 payload (replace `<story-id>`):
```json
{
  "schema_version": 1,
  "layout_mode": "panels",
  "runtime_policy": "auto",
  "persona_policy": "first_available",
  "chat_mode": "participant",
  "panels": [
    { "id": "story", "kind": "storyRuntime", "prominence": "primary", "order": 1, "title": "Story" },
    { "id": "chat", "kind": "chat", "prominence": "auxiliary", "order": 2, "title": "Chat" },
    { "id": "participants", "kind": "participantPanel", "prominence": "auxiliary", "order": 3, "title": "Participants" }
  ],
  "blocks": [
    {
      "id": "story-meta",
      "type": "storyMetadata",
      "region": "top",
      "order": 1,
      "title": "Story Metadata"
    },
    {
      "id": "orchestrator",
      "type": "orchestratorState",
      "region": "primary",
      "order": 1,
      "title": "Orchestrator State",
      "config_json": {
        "show_agent_list": true,
        "only_active_agents": false
      }
    },
    {
      "id": "feed-mounted",
      "type": "contributionFeed",
      "region": "auxiliary",
      "order": 1,
      "title": "Contribution Feed (Mounted Hidden)",
      "visibility": "hidden_mounted",
      "config_json": {
        "max_items": 8,
        "include_internal": true,
        "show_sender_type": true
      }
    },
    {
      "id": "feed-unmounted",
      "type": "contributionFeed",
      "region": "auxiliary",
      "order": 2,
      "title": "Contribution Feed (Unmounted Hidden)",
      "visibility": "hidden_unmounted"
    }
  ],
  "metadata_json": {
    "story_id": "<story-id>",
    "description": "Hidden mounted vs unmounted + runtime-coupled block validation"
  }
}
```

Expected browser result:
1. `storyMetadata` and `orchestratorState` blocks render with runtime-aware status.
2. `hidden_mounted` block stays in DOM but is visually hidden.
3. `hidden_unmounted` block is not rendered.
4. Story/chat/participants still behave normally while support blocks update.

---

## Quick UX/QA Checklist
1. Content payloads are rendered from authored JSON, not static demo examples.
2. Code format uses syntax highlighting path and shows code options.
3. Panel content and block content both work.
4. Region and order behavior is predictable.
5. Hidden modes are honored (`hidden_unmounted` and `hidden_mounted`).
6. Runtime-coupled blocks (`storyMetadata`, `orchestratorState`, `contributionFeed`) reflect live room/runtime context.
7. Demo URL composition works: `https://<frontend-host>/demo/<slug>`.
