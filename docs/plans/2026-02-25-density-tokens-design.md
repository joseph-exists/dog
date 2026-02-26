# Density Tokens Implementation Design

> Status: Approved
> Date: 2026-02-25
> Context: Priority item from presentation-customization-roadmap.md

## Overview

Implement consumption of density tokens (`feed_density`, `stack_density`, `matrix_density`) in Demo block/panel components. These tokens are already defined in the capability registry and pass through presentation_json - components just need to read and apply them.

## Scope

### Components Affected

| Component | Token | Current State |
|-----------|-------|---------------|
| `DemoChatPanel` | `feed_density` | Already has prop, applies padding only |
| `ContributionFeedBlock` | `feed_density` | Hardcoded spacing |
| `OrchestratorStateBlock` | `stack_density` | Hardcoded spacing |
| `ToolCapabilityBlock` | `matrix_density` | Hardcoded spacing |

### Density Values

- `feed_density` / `stack_density`: `"comfortable"` (default) | `"compact"`
- `matrix_density`: `"standard"` (default) | `"compact"`

## Design Decisions

### Preset-Only Approach

Density tokens act as bundled presets, not individual property overrides.

**Rationale:**
- YAGNI - No evidence users need per-property overrides yet
- Simpler mental model ("compact or comfortable" vs 6 spacing tokens)
- Extensible later without breaking existing configs
- Follows established pattern (typography fonts work similarly)

**Future extensibility:** If users request granular control, we can add override tokens (e.g., `feed_container_padding`) that take precedence over preset values. Inline comments will mark extension points.

## Class Mappings

### `feed_density` (DemoChatPanel, ContributionFeedBlock)

| Element | `comfortable` (default) | `compact` |
|---------|------------------------|-----------|
| Container padding | `p-4` | `p-2` |
| Section gaps | `space-y-4` | `space-y-2` |
| Card padding | `p-2.5` | `p-1.5` |
| Item gaps | `space-y-2` | `space-y-1` |

### `stack_density` (OrchestratorStateBlock)

| Element | `comfortable` (default) | `compact` |
|---------|------------------------|-----------|
| Container padding | `p-4` | `p-2` |
| Section gaps | `space-y-4` | `space-y-2` |
| Card padding | `p-3` | `p-2` |
| Agent row spacing | `space-y-2` | `space-y-1` |
| Badge gaps | `gap-2` | `gap-1` |

### `matrix_density` (ToolCapabilityBlock)

| Element | `standard` (default) | `compact` |
|---------|---------------------|-----------|
| Container padding | `p-4` | `p-2` |
| Section gaps | `space-y-4` | `space-y-2` |
| Card padding | `p-3` | `p-2` |
| Badge gaps | `gap-1.5` | `gap-1` |
| Agent section gaps | `space-y-2` | `space-y-1` |

## Data Flow

```
presentation_json
  { "tokens": { "feed_density": "compact" } }
                    │
                    ▼
rendererRegistry.tsx
  parse*Presentation() reads tokens, returns typed value
                    │
                    ▼
Panel/Block Renderers
  Pass density as prop to component
                    │
                    ▼
Component
  const classes = DENSITY_CLASSES[density]
  Apply in JSX
```

## Implementation Plan

### Files to Modify

| File | Changes |
|------|---------|
| `rendererRegistry.tsx` | Add density parsing to 3 parse functions |
| `ContributionFeedBlock.tsx` | Add `feedDensity` prop + class mapping |
| `OrchestratorStateBlock.tsx` | Add `stackDensity` prop + class mapping |
| `ToolCapabilityBlock.tsx` | Add `matrixDensity` prop + class mapping |

### Type Definitions

```typescript
type FeedDensity = "comfortable" | "compact"
type StackDensity = "comfortable" | "compact"
type MatrixDensity = "standard" | "compact"
```

### Implementation Pattern

Each component will use a density classes object:

```typescript
/**
 * Density class mappings for [component] layout.
 *
 * Controls spacing/padding based on presentation_json tokens.
 * Currently preset-based; if per-property overrides are needed,
 * add tokens like `tokens.[component]_container_padding` that
 * take precedence over these preset values.
 */
const DENSITY_CLASSES = {
  comfortable: {
    container: "p-4",
    sections: "space-y-4",
    card: "p-3",
    // ... component-specific
  },
  compact: {
    container: "p-2",
    sections: "space-y-2",
    card: "p-2",
    // ... component-specific
  },
} as const
```

## Testing

After implementation:
1. Verify default (no token) renders comfortable/standard spacing
2. Verify `compact` token applies tighter spacing
3. Test cascade: composition → panel → block precedence
4. Visual check in demo builder preview

## Usage

```json
{
  "presentation_json": {
    "tokens": {
      "feed_density": "compact",
      "stack_density": "compact",
      "matrix_density": "compact"
    }
  }
}
```
