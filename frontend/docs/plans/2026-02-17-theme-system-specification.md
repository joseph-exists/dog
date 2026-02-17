# Theme System Technical Specification

> **Status:** Draft
> **Author:** Claude + Josep
> **Date:** 2026-02-17
> **Domain:** Presentation Layer

---

## 1. Executive Summary

This specification defines a unified theme system supporting:
- Multi-origin themes (system, admin, user-created)
- Multi-category themes (page surfaces, card content, syntax highlighting, motion)
- Context-sensitive bindings (page, panel, authored content)
- Specificity-based resolution cascade

The system separates **theme definitions** (what exists) from **theme bindings** (where applied), enabling flexible composition without schema proliferation.

---

## 2. Domain Model

### 2.1 Theme Registry Aggregate

The Theme Registry is the authoritative source for all theme definitions.

#### Entity: Theme

| Attribute | Type | Description |
|-----------|------|-------------|
| id | UUID | Primary identifier |
| name | String | Human-readable name |
| description | String? | Optional description |
| category | ThemeCategory | Classification of theme purpose |
| scope | ThemeScope | Visibility and ownership rules |
| owner_id | UUID? | Creator reference (null for system) |
| is_system | Boolean | Immutable system-seeded flag |
| tokens | JSON | Category-specific token payload |
| created_at | Timestamp | Creation time |
| updated_at | Timestamp | Last modification time |

#### Value Object: ThemeCategory

Enumeration of theme purposes. Each category has distinct token schemas.

| Category | Purpose | Token Schema |
|----------|---------|--------------|
| `page` | Page surface theming | CSS variables including `--background` |
| `card` | Card/panel content areas | CSS variables excluding `--background` |
| `syntax` | Code syntax highlighting | Shiki theme name or syntax token colors |
| `motion` | Animation characteristics | Duration, easing, spring physics, reduced motion |

#### Value Object: ThemeScope

Enumeration of visibility and ownership rules.

| Scope | Owner | Visibility | Editable By |
|-------|-------|------------|-------------|
| `system` | None | All users | None (immutable) |
| `org` | Admin | All org users | Admins |
| `personal` | User | Owner only | Owner |
| `shared` | User | All org users | Owner |

#### Invariants

1. System themes (`is_system = true`) cannot be modified or deleted
2. A theme's `owner_id` must be null if `scope = system`
3. A theme's `owner_id` must be non-null if `scope ∈ {personal, shared}`
4. Token payload must conform to category-specific schema

---

### 2.2 Theme Binding Aggregate

Theme Bindings connect themes to specific contexts where they apply.

#### Entity: ThemeBinding

| Attribute | Type | Description |
|-----------|------|-------------|
| id | UUID | Primary identifier |
| binding_type | BindingType | Classification of binding ownership |
| owner_id | UUID | Reference to owner (user or entity) |
| context_key | String | Composite context path |
| slot | ThemeSlot | Which theme category this binds |
| theme_id | UUID | Foreign key to Theme |
| created_at | Timestamp | Creation time |
| updated_at | Timestamp | Last modification time |

#### Value Object: BindingType

| Type | Owner Semantics | Use Case |
|------|-----------------|----------|
| `user_pref` | owner_id = user_id | Viewer's personal preferences |
| `authored` | owner_id = entity_id | Creator's content theming |

#### Value Object: ThemeSlot

Matches ThemeCategory but represents the "slot" being filled:

| Slot | Filled By Category |
|------|--------------------|
| `page` | `page` themes |
| `cards` | `card` themes |
| `syntax` | `syntax` themes |
| `motion` | `motion` themes |

#### Value Object: ContextKey

A path-like string encoding the full context hierarchy.

**Grammar:**
```
context_key ::= segment ("/" segment)*
segment     ::= type ":" identifier
type        ::= "page" | "panel" | "story" | "room" | "node"
identifier  ::= slug | uuid | "*"
```

**Examples:**

| Context Key | Meaning |
|-------------|---------|
| `page:story` | Story listing page |
| `page:story/panel:debug` | Debug panel on story page |
| `page:agents/panel:debug` | Debug panel on agents page |
| `page:*/panel:*` | All panels on all pages (global default) |
| `story:{uuid}` | Specific story's base theme |
| `story:{uuid}/node:{uuid}` | Specific node within a story |
| `room:{uuid}` | Specific room |
| `room:{uuid}/panel:chat` | Chat panel in specific room |

#### Uniqueness Constraint

The tuple `(binding_type, owner_id, context_key, slot)` must be unique.

#### Invariants

1. `theme_id` must reference a Theme with matching category for the slot
2. For `binding_type = user_pref`, `owner_id` must be a valid user
3. For `binding_type = authored`, `owner_id` must be a valid entity of the type implied by context_key

---

### 2.3 Resolution Domain Service

The Resolution Service computes the effective theme for a given context.

#### Input: ResolutionRequest

| Field | Type | Description |
|-------|------|-------------|
| user_id | UUID | Requesting user |
| context_path | String[] | Ordered path segments |
| slot | ThemeSlot | Which theme category to resolve |
| entity_context | EntityContext? | Optional authored content context |

#### Output: ResolvedTheme

| Field | Type | Description |
|-------|------|-------------|
| theme | Theme? | Resolved theme or null |
| source | ResolutionSource | How the theme was resolved |
| context_key_matched | String? | Which binding matched |

#### Value Object: ResolutionSource

| Source | Meaning |
|--------|---------|
| `authored` | Matched an authored binding |
| `user_pref` | Matched a user preference binding |
| `system_default` | No binding found, using system default |
| `none` | No theme available |

#### Resolution Algorithm (Pseudocode)

```
function resolve(request):
    candidates = build_specificity_cascade(request.context_path)

    # Phase 1: Check authored bindings (if entity context provided)
    if request.entity_context:
        for key in candidates:
            binding = find_authored_binding(request.entity_context, key, request.slot)
            if binding:
                return ResolvedTheme(binding.theme, "authored", key)

    # Phase 2: Check user preference bindings
    for key in candidates:
        binding = find_user_pref_binding(request.user_id, key, request.slot)
        if binding:
            return ResolvedTheme(binding.theme, "user_pref", key)

    # Phase 3: System default
    default = find_system_default(request.slot)
    if default:
        return ResolvedTheme(default, "system_default", null)

    return ResolvedTheme(null, "none", null)

function build_specificity_cascade(path):
    # Most specific to least specific
    # ["page:story", "panel:debug"] produces:
    #   "page:story/panel:debug"
    #   "page:story/panel:*"
    #   "page:story"
    #   "page:*"
    #   "*"
    ...
```

---

## 3. Operations

### 3.1 Theme Registry Operations

#### Commands

| Command | Input | Output | Authorization |
|---------|-------|--------|---------------|
| CreateTheme | ThemeCreate | Theme | User (personal/shared), Admin (org) |
| UpdateTheme | theme_id, ThemeUpdate | Theme | Owner or Admin |
| DeleteTheme | theme_id | void | Owner or Admin, not system |
| SeedSystemThemes | ThemeCreate[] | Theme[] | System only (migration) |

#### Queries

| Query | Input | Output | Authorization |
|-------|-------|--------|---------------|
| GetTheme | theme_id | Theme | Visible to requester |
| ListThemes | filters (category, scope) | Theme[] | Filtered by visibility |
| ListAvailableThemes | user_id, category | Theme[] | All themes user can use |

### 3.2 Theme Binding Operations

#### Commands

| Command | Input | Output | Authorization |
|---------|-------|--------|---------------|
| SetUserPrefBinding | context_key, slot, theme_id | ThemeBinding | Authenticated user |
| ClearUserPrefBinding | context_key, slot | void | Authenticated user |
| SetAuthoredBinding | entity_ref, context_key, slot, theme_id | ThemeBinding | Entity owner |
| ClearAuthoredBinding | entity_ref, context_key, slot | void | Entity owner |

#### Queries

| Query | Input | Output | Authorization |
|-------|-------|--------|---------------|
| GetUserBindings | user_id, context_prefix? | ThemeBinding[] | Owner or Admin |
| GetAuthoredBindings | entity_ref | ThemeBinding[] | Entity viewer |
| ResolveTheme | ResolutionRequest | ResolvedTheme | Authenticated user |
| BatchResolveThemes | ResolutionRequest[] | ResolvedTheme[] | Authenticated user |

---

## 4. Contracts

### 4.1 API Contract: Theme Registry

#### Endpoints

| Method | Path | Operation |
|--------|------|-----------|
| GET | `/api/v1/themes` | ListThemes |
| GET | `/api/v1/themes/available` | ListAvailableThemes |
| GET | `/api/v1/themes/{id}` | GetTheme |
| POST | `/api/v1/themes` | CreateTheme |
| PATCH | `/api/v1/themes/{id}` | UpdateTheme |
| DELETE | `/api/v1/themes/{id}` | DeleteTheme |

#### Request/Response Schemas

**ThemeCreate:**
- name: string (required)
- description: string (optional)
- category: ThemeCategory (required)
- scope: ThemeScope (required, default: personal)
- tokens: object (required, validated per category)

**ThemeUpdate:**
- name: string (optional)
- description: string (optional)
- tokens: object (optional)
- scope: ThemeScope (optional, cannot change to/from system)

**ThemePublic:**
- id, name, description, category, scope, is_system, tokens, created_at, updated_at
- owner: UserPublicMinimal? (if not system)

### 4.2 API Contract: Theme Bindings

#### Endpoints

| Method | Path | Operation |
|--------|------|-----------|
| GET | `/api/v1/theme-bindings/user` | GetUserBindings |
| PUT | `/api/v1/theme-bindings/user` | SetUserPrefBinding |
| DELETE | `/api/v1/theme-bindings/user` | ClearUserPrefBinding |
| GET | `/api/v1/theme-bindings/resolve` | ResolveTheme |
| POST | `/api/v1/theme-bindings/resolve/batch` | BatchResolveThemes |

**Note:** Authored bindings are managed through entity-specific endpoints (story nodes, rooms, etc.) rather than a separate binding API.

#### Request/Response Schemas

**SetUserPrefBindingRequest:**
- context_key: string (required)
- slot: ThemeSlot (required)
- theme_id: UUID (required)

**ResolveThemeRequest:**
- context_path: string[] (required)
- slot: ThemeSlot (required)
- entity_context: EntityContext? (optional)

**ResolvedThemeResponse:**
- theme: ThemePublic?
- source: ResolutionSource
- context_key_matched: string?

### 4.3 Frontend Contract: Resolution Hook

**Interface:**
```
useThemeBinding(slot: ThemeSlot, contextOverride?: string[])
  → { theme: Theme | null, source: ResolutionSource, isLoading: boolean }
```

**Behavior:**
1. Derives context from current route and panel context
2. Applies contextOverride if provided
3. Queries resolution endpoint (with caching)
4. Returns resolved theme and metadata

---

## 5. Token Schemas by Category

### 5.1 Page Theme Tokens

Surface tokens that include background. Applied to page-level wrapper.

| Token | Required | Description |
|-------|----------|-------------|
| `--background` | Yes | Page surface color |
| `--foreground` | Yes | Primary text color |
| `--card` | Yes | Card surface color |
| `--card-foreground` | Yes | Card text color |
| `--border` | Yes | Border color |
| `--muted` | Yes | Muted surface color |
| `--muted-foreground` | Yes | Muted text color |
| `--secondary` | Yes | Secondary surface color |
| `--secondary-foreground` | Yes | Secondary text color |
| `--accent` | Yes | Accent/hover color |
| `--accent-foreground` | Yes | Accent text color |

### 5.2 Card Theme Tokens

Content area tokens excluding background. Applied to cards wrapper.

| Token | Required | Description |
|-------|----------|-------------|
| `--card` | Yes | Card surface color |
| `--card-foreground` | Yes | Card text color |
| `--border` | Yes | Border color |
| `--muted` | Yes | Muted surface color |
| `--muted-foreground` | Yes | Muted text color |
| `--secondary` | Yes | Secondary surface color |
| `--secondary-foreground` | Yes | Secondary text color |
| `--accent` | Yes | Accent/hover color |
| `--accent-foreground` | Yes | Accent text color |
| `--agent-accent` | No | Agent-specific accent |
| `--story-accent` | No | Story-specific accent |

**Constraint:** `--background` must NOT be present in card themes.

### 5.3 Syntax Theme Tokens

Code highlighting configuration. Two modes supported.

**Mode A: Built-in Shiki Theme**

| Token | Required | Description |
|-------|----------|-------------|
| `shikiTheme` | Yes | Shiki theme name string |

**Mode B: Custom Token Colors**

| Token | Required | Description |
|-------|----------|-------------|
| `--syntax-background` | Yes | Code block background |
| `--syntax-foreground` | Yes | Default text color |
| `--syntax-keyword` | Yes | Keywords (if, else, return) |
| `--syntax-string` | Yes | String literals |
| `--syntax-number` | Yes | Numeric literals |
| `--syntax-comment` | Yes | Comments |
| `--syntax-function` | Yes | Function names |
| `--syntax-variable` | Yes | Variable names |
| `--syntax-operator` | Yes | Operators |
| `--syntax-punctuation` | Yes | Punctuation |

### 5.4 Motion Theme Tokens

Animation and transition configuration.

| Token | Required | Default | Description |
|-------|----------|---------|-------------|
| `reducedMotion` | No | false | Respect prefers-reduced-motion |
| `transitionDuration` | No | "0.2s" | Default transition duration |
| `easingFunction` | No | "ease-out" | Default easing |
| `springStiffness` | No | 100 | Spring animation stiffness |
| `springDamping` | No | 10 | Spring animation damping |
| `springMass` | No | 1 | Spring animation mass |

---

## 6. System Theme Seed Data

The following themes ship with the system and are immutable.

### 6.1 Page Themes (category: page)

| ID | Name | Description |
|----|------|-------------|
| `default` | Default | Application theme (empty tokens, falls through to :root) |
| `midnight` | Midnight | Deep blue dark theme |
| `warm-sand` | Warm Sand | Warm light theme |
| `forest` | Forest | Green-tinted dark theme |

### 6.2 Card Themes (category: card)

| ID | Name | Description |
|----|------|-------------|
| `default` | Default | Inherit from page theme (empty tokens) |
| `oracle` | Oracle | Purple-tinted card surfaces |
| `ember` | Ember | Warm amber card surfaces |
| `arctic` | Arctic | Cool blue-gray card surfaces |

### 6.3 Syntax Themes (category: syntax)

| ID | Name | Description |
|----|------|-------------|
| `github-dark` | GitHub Dark | Shiki built-in |
| `github-light` | GitHub Light | Shiki built-in |
| `one-dark-pro` | One Dark Pro | Shiki built-in |
| `dracula` | Dracula | Shiki built-in |

### 6.4 Motion Themes (category: motion)

| ID | Name | Description |
|----|------|-------------|
| `default` | Default | Standard animations |
| `snappy` | Snappy | Fast, crisp transitions |
| `smooth` | Smooth | Slower, flowing transitions |
| `reduced` | Reduced | Minimal motion for accessibility |

---

## 7. Frontend Integration Points

### 7.1 Files Requiring Modification

#### Theme Definition Migration

| Current File | Action | Notes |
|--------------|--------|-------|
| `Common/Themes/page_themes.ts` | Convert to seed data | Export format changes to match API |
| `Common/Themes/card_themes.ts` | Convert to seed data | Export format changes to match API |
| `Common/Themes/types.ts` | Extend types | Add ThemeCategory, ThemeScope, ThemeSlot |
| `Common/Themes/resolve.ts` | Update resolution | Use new resolution service |

#### New Files Required

| File | Purpose |
|------|---------|
| `hooks/useThemeBinding.ts` | Resolution hook with caching |
| `hooks/useThemeRegistry.ts` | Theme CRUD operations |
| `services/themeService.ts` | API client for theme endpoints |
| `contexts/ThemeResolutionContext.tsx` | Context for resolution caching |

#### Shell Component Updates

| File | Changes |
|------|---------|
| `Story/StoryShell.tsx` | Use useThemeBinding for page/cards slots |
| `Agents/AgentsShell.tsx` | Use useThemeBinding for page/cards slots |
| `Room/RoomShell.tsx` | Use useThemeBinding for page/cards slots |

#### Route Updates

| File | Changes |
|------|---------|
| `routes/_layout/story.tsx` | Remove localStorage, use bindings API |
| `routes/_layout/agents.tsx` | Remove localStorage, use bindings API |
| `routes/_layout/r.$roomId.tsx` | Integrate theme bindings |

#### Header Components

| File | Changes |
|------|---------|
| `Story/StoryHeader.tsx` | Theme selectors call SetUserPrefBinding |
| `Agents/AgentsHeader.tsx` | Theme selectors call SetUserPrefBinding |

#### Panel System

| File | Changes |
|------|---------|
| `Page/primitives/PanelContainer.tsx` | Accept optional theme binding context |
| Panel configs in routes | Include context_key for panel-level resolution |

#### Code Display (Shiki Integration)

| File | Changes |
|------|---------|
| Components using Shiki | Use useThemeBinding("syntax") |
| Shiki configuration | Support css-variables mode |

#### Animation (Framer Motion Integration)

| File | Changes |
|------|---------|
| `hooks/useMotionConfig.ts` | New hook wrapping useThemeBinding("motion") |
| Components with motion | Use motion config hook |

### 7.2 Migration Strategy

**Phase 1: Backend Foundation**
1. Create Theme and ThemeBinding models
2. Create API routes for registry and bindings
3. Create migration to seed system themes
4. Verify API contract with manual testing

**Phase 2: Frontend Services**
1. Create themeService.ts API client
2. Create useThemeBinding hook with local caching
3. Create useThemeRegistry hook for CRUD

**Phase 3: Shell Migration**
1. Update StoryShell to use new hooks
2. Update AgentsShell to use new hooks
3. Remove localStorage persistence from routes
4. Verify existing functionality preserved

**Phase 4: Extended Integration**
1. Add panel-level context support
2. Integrate Shiki syntax theming
3. Integrate Framer Motion theming
4. Add theme management UI

---

## 8. Open Questions

### 8.1 Deferred Decisions

1. **Theme Inheritance:** Should user-created themes be able to extend system themes (partial override)?  : deferred pending further exploration/iteration

2. **Theme Versioning:** When a theme is updated, should existing bindings see the update immediately or be pinned? : deferred pending further exploration/iteration/user feedback

3. **Cross-Entity Authored Themes:** Can a story author reference a theme from another story, or must they copy it? : copied - no theme cloning/reference at this time

4. **Panel Type Registry:** Should panel types (debug, chat, grid) be formally registered, or remain stringly-typed? : current panel types *should* be registered (see Story/registry/panelTypes.ts) - however, some code paths or components may not be migrated to the panel registry pattern.  We should make TODO comments in these files when we come across this.

5. **Bulk Operations:** Should batch binding updates be transactional?  help me understand?

### 8.2 Future Considerations

1. **Theme Marketplace:** User-shared themes discoverable by others
2. **Theme Preview:** Try before applying
3. **Theme Export/Import:** JSON export for backup/sharing
4. **Conditional Themes:** Time-of-day or system preference triggers

---

## 9. Appendix: Context Key Examples

### User Preference Bindings

| User Intent | context_key | slot |
|-------------|-------------|------|
| "My story page should use Midnight" | `page:story` | `page` |
| "My story cards should use Oracle" | `page:story` | `cards` |
| "All my debug panels should use dark syntax" | `page:*/panel:debug` | `syntax` |
| "Debug panel on story page specifically" | `page:story/panel:debug` | `syntax` |
| "I want snappy animations everywhere" | `*` | `motion` |

### Authored Bindings

| Author Intent | context_key | slot |
|---------------|-------------|------|
| "This story uses ethereal theme" | `story:{uuid}` | `cards` |
| "This specific node is highlighted" | `story:{uuid}/node:{uuid}` | `cards` |
| "Code in this story uses Dracula" | `story:{uuid}` | `syntax` |
| "This room has warm theme" | `room:{uuid}` | `cards` |

---

## 10. References

- `CASCADING-THEMES.md` — Runtime cascade documentation
- `Presentation/REFERENCE.md` — Presentation-as-data architecture
- `THEME-CASCADE-REFERENCE.md` — Migration guide (needs update)
- `types.ts` — Current TypeScript interfaces
