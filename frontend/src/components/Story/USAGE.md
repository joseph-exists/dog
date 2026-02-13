# Story Panel System Usage

## Quick Start

```tsx
import {
  StoryShell,
  StoryPlayerPanel,
  StoryDebugPanel,
  type PanelConfig,
} from "@/components/Story"

function StoryPage({ storyId }: { storyId: string }) {
  const panels: PanelConfig[] = [
    {
      id: "player",
      kind: "storyPlayer",
      prominence: "primary",
      title: "Player",
      render: () => <StoryPlayerPanel />,
    },
    {
      id: "debug",
      kind: "storyDebug",
      prominence: "auxiliary",
      title: "Debug",
      render: () => <StoryDebugPanel />,
    },
  ]

  return (
    <StoryShell
      storyId={storyId}
      title="My Story"
      panels={panels}
      pageThemeId="default"
      cardsThemeId="default"
      onPageThemeChange={(id) => console.log("page theme:", id)}
      onCardsThemeChange={(id) => console.log("cards theme:", id)}
    />
  )
}
```

## Architecture

### Component Hierarchy

```
StoryShell
├── StoryHeader (title, theme controls, layout toggle)
└── StoryPlayerProvider (context for runtime state)
    └── StoryLayout (resizable panels / tabs)
        ├── StoryPlayerPanel (primary)
        │   └── StoryContent
        └── StoryDebugPanel (auxiliary)
```

### Data Flow

1. **API Data**: `useStoryEditor` fetches story, nodes, choices
2. **Runtime State**: `StoryPlayerProvider` manages currentNodeId, playerState, history
3. **Context**: Both panels consume via `useStoryPlayerContext()`

### Creating Custom Panels

Any panel can access player state:

```tsx
import { useStoryPlayerContext } from "@/components/Story"

function MyCustomPanel() {
  const { playerState, history, currentNode } = useStoryPlayerContext()

  return (
    <PanelContainer title="Custom">
      {/* Your custom UI */}
    </PanelContainer>
  )
}
```

## Panel Configurations

### Primary Panels
- `prominence: "primary"` - Side-by-side in main area
- Full height, resizable width

### Auxiliary Panels
- `prominence: "auxiliary"` - Stacked in right column
- Resizable, collapsible

### Layout Modes
- `"panels"` (desktop) - Resizable panel groups
- `"tabs"` (mobile) - Tab-based navigation
