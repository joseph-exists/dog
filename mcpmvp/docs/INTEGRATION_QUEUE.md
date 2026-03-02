# MCP Server Integration Queue

Quick reference for upcoming MCP server migrations/creations.

## Status

| System | Status | Primary Use Case |
|--------|--------|------------------|
| Affordances | ✅ Complete | Agent introspection of what's possible |
| Story | 📋 Planned | Story navigation & branching for agents |
| Tesser | 📋 Planned | Semantic search & embedding queries |
| Canvas | 📋 Planned | Composition rendering & validation |

---

## 1. Story System

### Why MCP?

Agents need to:
- Navigate story structures
- Understand available choices
- Preview consequences of choices
- Track narrative state

### Current Backend Location

```
backend/app/api/routes/
├── stories.py          # Story CRUD
├── storynodes.py       # Node management
├── node_choices.py     # Choice handling
└── user_story_progress.py  # Progress tracking

backend/app/models.py
├── Story, StoryNode, StoryChoice
└── UserStoryProgress
```

### Proposed MCP Tools

```python
# Navigation
story_current_node(story_id, user_id) → Current node + available choices
story_preview_choice(node_id, choice_id) → What happens if this choice is made
story_available_paths(node_id) → All reachable nodes from here

# Structure
story_map(story_id) → Full graph structure
story_node_details(node_id) → Node content + metadata

# Progress (if stateless possible)
story_progress_summary(story_id, user_id) → Where user is, what they've done
```

### Migration Considerations

**Challenge:** Story progress is database-backed (UserStoryProgress).

**Options:**
1. **Hybrid** - MCP for read-only navigation, backend for mutations
2. **Stateless** - MCP provides structure, caller tracks state
3. **Cache-based** - MCP caches story structure, delegates writes

**Recommendation:** Start with read-only structure navigation (option 2), add stateful operations later if needed.

### Files to Extract

- Story structure definitions (if in YAML/JSON)
- Navigation logic (path finding, choice evaluation)
- Story validation rules

---

## 2. Tesser System

### Why MCP?

Agents need to:
- Query semantic similarity
- Find related content
- Generate embeddings for comparison
- Search across knowledge bases

### Current Backend Location

```
backend/app/api/routes/tesser.py
tesser/                    # Separate package
├── pyproject.toml
├── tesser/
│   ├── embedder.py
│   └── ...
```

### Proposed MCP Tools

```python
# Search
tesser_search(query, collection, limit) → Similar items
tesser_compare(text_a, text_b) → Similarity score

# Embedding
tesser_embed(text) → Vector representation
tesser_batch_embed(texts) → Multiple vectors

# Collections
tesser_collections() → Available collections
tesser_collection_stats(collection) → Size, dimensions, etc.
```

### Migration Considerations

**Challenge:** Tesser may call external APIs (OpenAI, etc.) for embeddings.

**Options:**
1. **Keep API calls in MCP** - MCP server handles external calls
2. **Proxy through backend** - MCP calls backend which calls APIs
3. **Local-only** - Only expose local vector operations

**Recommendation:** Option 1 - MCP server can handle async HTTP calls to embedding APIs. Keep it self-contained.

### Files to Extract

- Embedding logic from tesser package
- Collection configuration
- Search/similarity algorithms

---

## 3. Canvas System

### Why MCP?

Agents need to:
- Understand composition structure
- Validate panel/block configurations
- Preview rendered layouts
- Generate valid presentation_json

### Current Backend Location

```
backend/app/api/routes/demos.py  # Has composition endpoints
frontend/docs/
├── color-tests.json     # Valid styling reference
└── color-tests.md       # Styling documentation
```

### Proposed MCP Tools

```python
# Validation
canvas_validate_composition(composition_json) → Errors/warnings
canvas_validate_panel(panel_spec) → Panel-specific validation
canvas_validate_presentation(presentation_json) → Styling validation

# Schema
canvas_panel_schema(panel_kind) → Valid options for panel type
canvas_block_schema(block_type) → Valid options for block type
canvas_supported_styles() → What presentation_json fields work

# Generation
canvas_generate_preset(theme_name) → Valid presentation_json
canvas_suggest_layout(requirements) → Composition suggestions
```

### Migration Considerations

**Challenge:** Canvas validation needs to stay in sync with frontend renderer.

**Options:**
1. **Schema-driven** - Load schemas from shared location
2. **Frontend-sourced** - Pull validation rules from frontend docs
3. **Manual sync** - Keep MCP rules updated manually

**Recommendation:** Option 2 - Parse `color-tests.json` and `color-tests.md` to build validation rules. Single source of truth.

### Files to Create

- Schema definitions for panels/blocks
- Validation logic
- Preset generation (like we did in demos.py CLI)

---

## Integration Order

Suggested sequence based on complexity and dependencies:

1. **Canvas** (simplest - mostly validation/generation, no DB)
2. **Tesser** (self-contained, external API calls manageable)
3. **Story** (most complex - database dependencies)

---

## Template: Starting a New Integration

```bash


# X. Update Typer CLI
# Edit backend/app/test_scripts/typer/commands/{domain}.py


```

---
