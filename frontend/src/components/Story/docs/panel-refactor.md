  ---
  StoryPlayer Panel Refactor — Reference Card

  Decisions & Assumptions

  Architectural Decisions
  ┌───────────────────────────────────────┬───────────────────────────────────────────────────────────────────────────────────────────────┐
  │               Decision                │                                           Rationale                                           │
  ├───────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────┤
  │ StoryPlayer as primary Story panel    │ Distinct from StoryPreview (Room auxiliary) — different context, different evolution path     │
  ├───────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────┤
  │ StoryDebugPanel as separate auxiliary │ Decoupled for layout flexibility; can show/hide via panel config                              │
  ├───────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Context for runtime state             │ Panels configured via render() functions — context avoids prop drilling through layout system │
  ├───────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Reuse useStoryEditor for data         │ Existing hook already fetches story + nodes + choices; no new API patterns                    │
  ├───────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Provider at StoryShell level          │ Shell knows storyId; wrapping layout ensures all panels access context                        │
  ├───────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────┤
  │ Story-specific primitives             │ Use Story/primitives/ (PanelContainer, ActionBar) not Room primitives                         │
  └───────────────────────────────────────┴───────────────────────────────────────────────────────────────────────────────────────────────┘
  Assumptions
  ┌──────────────────────────────────────┬───────────────────────────────────────────────────────────────────────────┐
  │              Assumption              │                                Implication                                │
  ├──────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────┤
  │ StoryShell/StoryLayout already work  │ We're integrating into existing infrastructure, not building it           │
  ├──────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────┤
  │ useStoryEditor API is stable         │ We depend on its return shape { story, nodes, choices, isLoading, error } │
  ├──────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────┤
  │ CSS variable cascade works           │ We don't add hardcoded styles; use --foreground, --muted, etc.            │
  ├──────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────┤
  │ Content format handling is temporary │ Current renderContent() preserved; future refactor planned                │
  ├──────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────┤
  │ ActionBar actions are context-native │ Undo/Restart come from StoryPlayerContext, not new hooks                  │
  └──────────────────────────────────────┴───────────────────────────────────────────────────────────────────────────┘
  Constraints
  ┌────────────────────────────┬────────────────────────────────────────────────────────┐
  │         Constraint         │                      Enforcement                       │
  ├────────────────────────────┼────────────────────────────────────────────────────────┤
  │ No new hook patterns       │ Use existing hooks/stories/* or context-native actions │
  ├────────────────────────────┼────────────────────────────────────────────────────────┤
  │ Respect CSS cascade        │ PageTheme → CardsTheme → Panel → Content inheritance   │
  ├────────────────────────────┼────────────────────────────────────────────────────────┤
  │ Inline documentation       │ Comment "why" for architectural choices                │
  ├────────────────────────────┼────────────────────────────────────────────────────────┤
  │ Preserve existing behavior │ Content rendering logic unchanged                      │
  └────────────────────────────┴────────────────────────────────────────────────────────┘
  ---
  Component Specifications

  1. StoryPlayerProvider

  Location: frontend/src/components/Story/StoryPlayer/StoryPlayerProvider.tsx

  Purpose: Provides runtime player state and actions to all Story panels

  Dependencies:
  ├── useStoryEditor (from hooks/stories)
  ├── React.createContext
  ├── React.useState
  ├── React.useMemo
  └── State utilities (evaluateRequiresState, applySetsState from utils/stateConditions)

  Contract (Context Value):
  interface StoryPlayerContextValue {
    // Data (from useStoryEditor)
    story: StoryPublic | undefined
    nodes: StoryNodePublic[]
    choices: NodeChoicePublic[]
    isLoading: boolean
    error: Error | null

    // Runtime State
    currentNodeId: string | null
    currentNode: StoryNodePublic | undefined
    playerState: Record<string, unknown>
    history: HistoryEntry[]

    // Derived State
    availableChoices: NodeChoicePublic[]
    allChoicesForNode: NodeChoicePublic[]
    isEndNode: boolean

    // Actions
    handleChoice: (choice: NodeChoicePublic) => void
    handleUndo: () => void
    handleRestart: () => void
  }

  interface HistoryEntry {
    nodeId: string
    state: Record<string, unknown>
    choiceText?: string
  }

  Props:
  interface StoryPlayerProviderProps {
    storyId: string
    children: React.ReactNode
  }

  Control Flow:
  1. Receive storyId prop
  2. Call useStoryEditor({ storyId }) → { story, nodes, choices, isLoading, error }
  3. Initialize runtime state:
     - currentNodeId = startNode?.id ?? null
     - playerState = {}
     - history = []
  4. Compute derived state (useMemo):
     - currentNode = nodes.find(n => n.id === currentNodeId)
     - allChoicesForNode = choices.filter(c => c.from_node_id === currentNodeId)
     - availableChoices = allChoicesForNode.filter(evaluateRequiresState)
     - isEndNode = currentNode?.is_end_node || availableChoices.length === 0
  5. Define actions:
     - handleChoice: save to history, apply sets_state, navigate
     - handleUndo: restore previous node + state from history
     - handleRestart: reset to startNode, clear state + history
  6. Provide context value to children

  Call Hierarchy:
  StoryShell
  └── StoryPlayerProvider ← YOU ARE HERE
      ├── useStoryEditor(storyId)
      │   ├── useQuery (story)
      │   ├── useQuery (nodes)
      │   └── useQuery (choices)
      └── StoryLayout
          ├── StoryPlayerPanel (consumes context)
          └── StoryDebugPanel (consumes context)

  ---
  2. useStoryPlayerContext

  Location: frontend/src/components/Story/StoryPlayer/useStoryPlayerContext.ts

  Purpose: Hook to consume StoryPlayerContext with error boundary

  Dependencies:
  ├── React.useContext
  └── StoryPlayerContext (from StoryPlayerProvider)

  Contract:
  function useStoryPlayerContext(): StoryPlayerContextValue
  // Throws if used outside StoryPlayerProvider

  Implementation Pattern:
  export function useStoryPlayerContext(): StoryPlayerContextValue {
    const context = useContext(StoryPlayerContext)
    if (!context) {
      throw new Error(
        "useStoryPlayerContext must be used within StoryPlayerProvider"
      )
    }
    return context
  }

  ---
  3. StoryPlayerPanel

  Location: frontend/src/components/Story/panels/StoryPlayerPanel.tsx

  Purpose: Primary panel displaying story content and choices

  Dependencies:
  ├── useStoryPlayerContext (from StoryPlayer)
  ├── PanelContainer (from Story/primitives)
  ├── ActionBar (from Story/primitives)
  ├── StoryContent (from StoryPlayer)
  ├── Lucide icons (RotateCcw, Play, Loader2, AlertCircle)
  └── UI components (Button from ui)

  Contract (Props):
  // No props — all data from context
  interface StoryPlayerPanelProps {}

  Control Flow:
  1. Call useStoryPlayerContext()
  2. Extract: isLoading, error, story, handleUndo, handleRestart, history
  3. Build headerActions:
     - Undo action (disabled if history.length === 0)
     - Restart action
  4. Render decision tree:
     if (isLoading) → PanelContainer with Loader2 spinner
     if (error) → PanelContainer with AlertCircle + message
     else → PanelContainer with StoryContent

  Call Hierarchy:
  StoryLayout (via PanelConfig.render())
  └── StoryPlayerPanel ← YOU ARE HERE
      ├── useStoryPlayerContext()
      ├── PanelContainer
      │   ├── headerActions={ActionBar}
      │   └── children={StoryContent}
      └── StoryContent
          └── useStoryPlayerContext()

  ActionBar Actions:
  const actions: ActionItem[] = [
    {
      id: "undo",
      icon: RotateCcw,
      label: "Undo",
      onClick: handleUndo,
      disabled: history.length === 0,
    },
    {
      id: "restart",
      icon: Play,
      label: "Restart",
      onClick: handleRestart,
    },
  ]

  ---
  4. StoryContent

  Location: frontend/src/components/Story/StoryPlayer/StoryContent.tsx

  Purpose: Renders current node content, choices, and state-based UI

  Dependencies:
  ├── useStoryPlayerContext (from StoryPlayer)
  ├── DOMPurify (for HTML sanitization)
  ├── UI components (Card, CardHeader, CardContent, Badge, Separator, Button)
  └── Lucide icons (ChevronRight, Play)

  Contract (Props):
  // No props — all data from context
  interface StoryContentProps {}

  Control Flow:
  1. Call useStoryPlayerContext()
  2. Extract: currentNode, availableChoices, isEndNode, handleChoice, handleRestart, nodes (for startNode check)
  3. Render decision tree:
     if (!startNode) → "No start node found" message
     if (!currentNode) → "Node not found" + restart button
     else → Full content:
       - Card with node title + optional "The End" badge
       - renderContent(currentNode) — HTML/JSON/text
       - If not end: choice buttons
       - If end: "Play Again" button
       - If dead end: warning message

  renderContent Helper:
  function renderContent(node: StoryNodePublic): React.ReactNode {
    const format = node.content_format || "text"
    switch (format) {
      case "html":
        return <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(...) }} />
      case "json":
        return <pre>{JSON.stringify(parsed, null, 2)}</pre>
      default:
        return <p>{content}</p>
    }
  }

  ---
  5. StoryDebugPanel

  Location: frontend/src/components/Story/panels/StoryDebugPanel.tsx

  Purpose: Auxiliary panel showing player state, history, and choice details

  Dependencies:
  ├── useStoryPlayerContext (from StoryPlayer)
  ├── PanelContainer (from Story/primitives)
  ├── Collapsible components (from ui)
  ├── Lucide icons (Bug, ChevronUp, ChevronDown)
  └── UI components (Button, Badge)

  Contract (Props):
  // No props — all data from context
  interface StoryDebugPanelProps {}

  Control Flow:
  1. Call useStoryPlayerContext()
  2. Extract: playerState, history, availableChoices, allChoicesForNode, currentNode, isLoading
  3. Manage local UI state: expandedSections { state, history, choices }
  4. Render decision tree:
     if (isLoading) → PanelContainer with "Waiting..." spinner
     else → PanelContainer with three collapsible sections

  Sections:
  ┌─────────────────────────────────────┐
  │ 🐛 Debug                            │
  ├─────────────────────────────────────┤
  │ ▼ Player State (3)                  │
  │   hasKey: true                      │
  │   gold: 50                          │
  │   visited_cave: true                │
  ├─────────────────────────────────────┤
  │ ▼ Choice History (5)                │
  │   1. Open the door                  │
  │   2. Take the key                   │
  │   3. Enter the cave                 │
  ├─────────────────────────────────────┤
  │ ▼ Choices (2/4)                     │
  │   ✓ Go north                        │
  │   ✓ Go south                        │
  │   ✗ Use key [Blocked]               │
  │     Requires: {"hasKey": true}      │
  │   ✗ Pay 100 gold [Blocked]          │
  │     Requires: {"gold": {"gte": 100}}│
  ├─────────────────────────────────────┤
  │ Current Node: The Cave Entrance     │
  └─────────────────────────────────────┘

  ---
  Integration Points

  StoryShell Update

  Current:
  <div style={getCardThemeStyle(cardsTheme)} className="flex-1 min-h-0">
    <StoryLayout panels={panels} mode={layoutMode} />
  </div>

  Updated:
  <div style={getCardThemeStyle(cardsTheme)} className="flex-1 min-h-0">
    <StoryPlayerProvider storyId={storyId}>
      <StoryLayout panels={panels} mode={layoutMode} />
    </StoryPlayerProvider>
  </div>

  StoryShell Props Addition:
  interface StoryShellProps {
    // ... existing props
    storyId: string  // NEW: Required for StoryPlayerProvider
  }

  Panel Configuration (at route level)

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

  ---
  File Dependency Graph

  frontend/src/
  ├── components/Story/
  │   ├── StoryShell.tsx
  │   │   └── imports: StoryPlayerProvider, StoryLayout
  │   │
  │   ├── StoryPlayer/
  │   │   ├── index.ts
  │   │   │   └── exports: StoryPlayerProvider, useStoryPlayerContext, StoryContent
  │   │   ├── StoryPlayerProvider.tsx
  │   │   │   └── imports: useStoryEditor, stateConditions utils
  │   │   ├── useStoryPlayerContext.ts
  │   │   │   └── imports: StoryPlayerContext
  │   │   └── StoryContent.tsx
  │   │       └── imports: useStoryPlayerContext, DOMPurify, UI components
  │   │
  │   ├── panels/
  │   │   ├── index.ts
  │   │   │   └── exports: StoryPlayerPanel, StoryDebugPanel
  │   │   ├── StoryPlayerPanel.tsx
  │   │   │   └── imports: useStoryPlayerContext, PanelContainer, ActionBar, StoryContent
  │   │   └── StoryDebugPanel.tsx
  │   │       └── imports: useStoryPlayerContext, PanelContainer, Collapsible
  │   │
  │   └── primitives/
  │       ├── PanelContainer.tsx (existing)
  │       └── ActionBar.tsx (existing)
  │
  ├── hooks/stories/
  │   └── useStoryEditor.ts (existing, unchanged)
  │
  └── utils/
      └── stateConditions.ts (existing, unchanged)

  ---
  Testing Considerations
  ┌───────────────────────┬────────────────────────────────────────────────────────────────┐
  │       Component       │                           Test Focus                           │
  ├───────────────────────┼────────────────────────────────────────────────────────────────┤
  │ StoryPlayerProvider   │ State transitions, undo/restart behavior, choice filtering     │
  ├───────────────────────┼────────────────────────────────────────────────────────────────┤
  │ useStoryPlayerContext │ Error when used outside provider                               │
  ├───────────────────────┼────────────────────────────────────────────────────────────────┤
  │ StoryPlayerPanel      │ Loading/error states render correctly, actions wire to context │
  ├───────────────────────┼────────────────────────────────────────────────────────────────┤
  │ StoryContent          │ All content formats render, choices display, end states        │
  ├───────────────────────┼────────────────────────────────────────────────────────────────┤
  │ StoryDebugPanel       │ Collapsible sections, blocked choice display, history list     │
  └───────────────────────┴────────────────────────────────────────────────────────────────┘
  ---