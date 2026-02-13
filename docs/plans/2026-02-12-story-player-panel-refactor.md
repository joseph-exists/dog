# StoryPlayer Panel Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform StoryPlayer into a composable primary panel for the Story shell, with a separate StoryDebugPanel auxiliary panel, sharing runtime state via React Context.

**Architecture:** StoryPlayerProvider wraps StoryLayout to provide runtime player state (currentNodeId, playerState, history) to all panels. StoryPlayerPanel and StoryDebugPanel consume this context. Data fetching uses existing useStoryEditor hook. Panels use Story primitives (PanelContainer, ActionBar).

**Tech Stack:** React, TypeScript, TanStack Query (via useStoryEditor), Story primitives, DOMPurify

---

## Reference Card Summary

See conversation for full reference card. Key decisions:
- StoryPlayer = primary Story panel (distinct from StoryPreview in Room)
- StoryDebugPanel = separate auxiliary panel (decoupled for layout flexibility)
- Context for runtime state (avoids prop drilling through layout system)
- Reuse useStoryEditor for data fetching
- Use Story/primitives (not Room primitives)
- Respect CSS variable cascade (no hardcoded styles)
- Document "why" with inline comments

---

## Task 1: Create StoryPlayerProvider Context

**Files:**
- Create: `frontend/src/components/Story/StoryPlayer/StoryPlayerProvider.tsx`
- Create: `frontend/src/components/Story/StoryPlayer/useStoryPlayerContext.ts`
- Modify: `frontend/src/components/Story/StoryPlayer/index.ts`

**Step 1: Create the context types and provider**

Create `frontend/src/components/Story/StoryPlayer/StoryPlayerProvider.tsx`:

```tsx
/**
 * StoryPlayerProvider
 *
 * Provides runtime player state to all Story panels.
 *
 * ARCHITECTURE DECISION: We use React Context rather than props because:
 * 1. Panels are configured via PanelConfig.render() functions - prop drilling is awkward
 * 2. Multiple panels (Player, Debug) need access to the same runtime state
 * 3. Future panels can easily tap into player state without prop changes
 *
 * DATA FLOW:
 * - API data (story, nodes, choices) comes from useStoryEditor hook
 * - Runtime state (currentNodeId, playerState, history) is managed here
 * - Both are exposed via context for panel consumption
 */
import {
  createContext,
  useCallback,
  useMemo,
  useState,
  type ReactNode,
} from "react"
import type { NodeChoicePublic, StoryNodePublic, StoryPublic } from "@/client"
import { useStoryEditor } from "@/hooks/stories/useStoryEditor"
import {
  applySetsState,
  evaluateRequiresState,
  type StateConditions,
  type StateMutations,
} from "@/utils/stateConditions"

// === Types ===

export interface HistoryEntry {
  nodeId: string
  state: Record<string, unknown>
  choiceText?: string
}

export interface StoryPlayerContextValue {
  // Data from useStoryEditor
  story: StoryPublic | undefined
  nodes: StoryNodePublic[]
  choices: NodeChoicePublic[]
  isLoading: boolean
  error: Error | null

  // Runtime state
  currentNodeId: string | null
  currentNode: StoryNodePublic | undefined
  playerState: Record<string, unknown>
  history: HistoryEntry[]

  // Derived state
  startNode: StoryNodePublic | undefined
  availableChoices: NodeChoicePublic[]
  allChoicesForNode: NodeChoicePublic[]
  isEndNode: boolean

  // Actions
  handleChoice: (choice: NodeChoicePublic) => void
  handleUndo: () => void
  handleRestart: () => void
}

interface StoryPlayerProviderProps {
  storyId: string
  children: ReactNode
}

// === Context ===

export const StoryPlayerContext = createContext<StoryPlayerContextValue | null>(
  null
)

// === Provider ===

export function StoryPlayerProvider({
  storyId,
  children,
}: StoryPlayerProviderProps) {
  // Fetch story data using existing hook
  const { story, nodes, choices, isLoading, error } = useStoryEditor({
    storyId,
  })

  // Find start node
  const startNode = useMemo(
    () => nodes.find((n) => n.is_start_node),
    [nodes]
  )

  // Runtime state
  const [currentNodeId, setCurrentNodeId] = useState<string | null>(null)
  const [playerState, setPlayerState] = useState<Record<string, unknown>>({})
  const [history, setHistory] = useState<HistoryEntry[]>([])

  // Initialize currentNodeId when startNode becomes available
  // ARCHITECTURE DECISION: We initialize lazily rather than in useState
  // because startNode depends on async data from useStoryEditor
  useMemo(() => {
    if (startNode && currentNodeId === null) {
      setCurrentNodeId(startNode.id)
    }
  }, [startNode, currentNodeId])

  // Derived: current node
  const currentNode = useMemo(
    () => nodes.find((n) => n.id === currentNodeId),
    [nodes, currentNodeId]
  )

  // Derived: all choices for current node (unfiltered, for debug panel)
  const allChoicesForNode = useMemo(
    () => choices.filter((c) => c.from_node_id === currentNodeId),
    [choices, currentNodeId]
  )

  // Derived: available choices (filtered by requires_state conditions)
  const availableChoices = useMemo(
    () =>
      allChoicesForNode.filter((choice) =>
        evaluateRequiresState(
          choice.requires_state as StateConditions | null,
          playerState
        )
      ),
    [allChoicesForNode, playerState]
  )

  // Derived: is this an end node?
  const isEndNode = currentNode?.is_end_node || availableChoices.length === 0

  // Action: handle choice selection
  const handleChoice = useCallback(
    (choice: NodeChoicePublic) => {
      if (!currentNode || !choice.to_node_id) return

      // Save current state to history before transitioning
      setHistory((prev) => [
        ...prev,
        {
          nodeId: currentNode.id,
          state: { ...playerState },
          choiceText: choice.text,
        },
      ])

      // Apply state mutations if any
      if (choice.sets_state) {
        setPlayerState((prev) =>
          applySetsState(choice.sets_state as StateMutations, prev)
        )
      }

      // Navigate to next node
      setCurrentNodeId(choice.to_node_id)
    },
    [currentNode, playerState]
  )

  // Action: undo last choice (restores both node AND state)
  const handleUndo = useCallback(() => {
    if (history.length === 0) return

    const previous = history[history.length - 1]
    setCurrentNodeId(previous.nodeId)
    setPlayerState(previous.state)
    setHistory((prev) => prev.slice(0, -1))
  }, [history])

  // Action: restart from beginning
  const handleRestart = useCallback(() => {
    setHistory([])
    setPlayerState({})
    setCurrentNodeId(startNode?.id ?? null)
  }, [startNode])

  // Build context value
  const contextValue = useMemo<StoryPlayerContextValue>(
    () => ({
      // Data
      story,
      nodes,
      choices,
      isLoading,
      error: error as Error | null,

      // Runtime state
      currentNodeId,
      currentNode,
      playerState,
      history,

      // Derived
      startNode,
      availableChoices,
      allChoicesForNode,
      isEndNode,

      // Actions
      handleChoice,
      handleUndo,
      handleRestart,
    }),
    [
      story,
      nodes,
      choices,
      isLoading,
      error,
      currentNodeId,
      currentNode,
      playerState,
      history,
      startNode,
      availableChoices,
      allChoicesForNode,
      isEndNode,
      handleChoice,
      handleUndo,
      handleRestart,
    ]
  )

  return (
    <StoryPlayerContext.Provider value={contextValue}>
      {children}
    </StoryPlayerContext.Provider>
  )
}
```

**Step 2: Create the context hook**

Create `frontend/src/components/Story/StoryPlayer/useStoryPlayerContext.ts`:

```tsx
/**
 * useStoryPlayerContext
 *
 * Hook to consume StoryPlayerContext with proper error boundary.
 *
 * USAGE: Call from any component inside StoryPlayerProvider.
 * Will throw if used outside provider (fail-fast for debugging).
 */
import { useContext } from "react"
import {
  StoryPlayerContext,
  type StoryPlayerContextValue,
} from "./StoryPlayerProvider"

export function useStoryPlayerContext(): StoryPlayerContextValue {
  const context = useContext(StoryPlayerContext)

  if (!context) {
    throw new Error(
      "useStoryPlayerContext must be used within a StoryPlayerProvider. " +
        "Ensure StoryPlayerProvider wraps your component tree."
    )
  }

  return context
}
```

**Step 3: Update the index exports**

Modify `frontend/src/components/Story/StoryPlayer/index.ts`:

```tsx
// StoryPlayer module exports
//
// Components for the Story player panel system.
// StoryPlayerProvider should wrap StoryLayout to share state across panels.

export { StoryPlayerProvider } from "./StoryPlayerProvider"
export { useStoryPlayerContext } from "./useStoryPlayerContext"
export type {
  StoryPlayerContextValue,
  HistoryEntry,
} from "./StoryPlayerProvider"
```

**Step 4: Verify TypeScript compilation**

Run: `cd /home/josep/dog/frontend && npx tsc --noEmit 2>&1 | head -30`

Expected: No errors related to StoryPlayer files (or only pre-existing errors)

**Step 5: Commit**

```bash
git add frontend/src/components/Story/StoryPlayer/
git commit -m "feat(story): add StoryPlayerProvider context for runtime state

- Create StoryPlayerProvider with runtime state management
- Add useStoryPlayerContext hook with error boundary
- Exposes story data (via useStoryEditor) + runtime state + actions
- Enables multiple panels to share player state"
```

---

## Task 2: Create StoryContent Component

**Files:**
- Create: `frontend/src/components/Story/StoryPlayer/StoryContent.tsx`
- Modify: `frontend/src/components/Story/StoryPlayer/index.ts`

**Step 1: Create StoryContent component**

Create `frontend/src/components/Story/StoryPlayer/StoryContent.tsx`:

```tsx
/**
 * StoryContent
 *
 * Renders the current node's content and available choices.
 * Consumes StoryPlayerContext for all data.
 *
 * CONTENT FORMATS:
 * - html: Sanitized via DOMPurify, rendered with prose styling
 * - json: Formatted as preformatted code block
 * - text: Plain text with whitespace preserved
 *
 * NOTE: Content format handling is preserved from original StoryPlayer.
 * This is a future refactor target for cleaner rich-text/markdown pipeline.
 */
import DOMPurify from "dompurify"
import { ChevronRight, Play } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import type { StoryNodePublic } from "@/client"
import { useStoryPlayerContext } from "./useStoryPlayerContext"

/**
 * Renders node content based on format.
 *
 * ARCHITECTURE DECISION: This is extracted as a helper function rather than
 * a component because it's tightly coupled to node data structure and
 * doesn't need its own lifecycle or state.
 */
function renderContent(node: StoryNodePublic) {
  const format = node.content_format || "text"
  const content = node.content || ""

  switch (format) {
    case "html":
      return (
        <div
          className="prose prose-lg dark:prose-invert max-w-none"
          dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(content) }}
        />
      )

    case "json":
      try {
        const parsed = JSON.parse(content)
        return (
          <div>
            <p className="text-sm text-muted-foreground italic mb-2">
              [JSON Content]
            </p>
            <pre className="bg-muted p-4 rounded-md overflow-auto text-sm font-mono">
              {JSON.stringify(parsed, null, 2)}
            </pre>
          </div>
        )
      } catch {
        return (
          <p className="text-destructive whitespace-pre-wrap">
            [Invalid JSON content]
          </p>
        )
      }

    default:
      return (
        <p className="text-lg leading-relaxed whitespace-pre-wrap">
          {content || "(No content)"}
        </p>
      )
  }
}

export function StoryContent() {
  const {
    startNode,
    currentNode,
    availableChoices,
    isEndNode,
    handleChoice,
    handleRestart,
  } = useStoryPlayerContext()

  // No start node configured
  if (!startNode) {
    return (
      <div className="flex items-center justify-center h-full p-8">
        <Card className="max-w-md">
          <CardContent className="py-8 text-center">
            <p className="text-destructive font-medium">No start node found</p>
            <p className="text-muted-foreground mt-2 text-sm">
              Add a node marked as "Start" to begin the story
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Current node not found (edge case)
  if (!currentNode) {
    return (
      <div className="flex items-center justify-center h-full p-8">
        <Card className="max-w-md">
          <CardContent className="py-8 text-center">
            <p className="text-destructive font-medium">Node not found</p>
            <Button className="mt-4" onClick={handleRestart}>
              Restart
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Normal content rendering
  return (
    <div className="p-8">
      <div className="mx-auto max-w-2xl">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-2xl">{currentNode.title}</CardTitle>
              {isEndNode && <Badge className="bg-green-600">The End</Badge>}
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Node Content */}
            {renderContent(currentNode)}

            {/* Choices Section */}
            {!isEndNode && availableChoices.length > 0 && (
              <>
                <Separator />
                <div>
                  <h3 className="text-muted-foreground text-sm font-medium uppercase mb-3">
                    What do you do?
                  </h3>
                  <div className="space-y-3">
                    {availableChoices
                      .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
                      .map((choice) => (
                        <button
                          key={choice.id}
                          type="button"
                          onClick={() => handleChoice(choice)}
                          className="hover:bg-muted border-border bg-background flex w-full items-center justify-between rounded-lg border p-4 text-left transition-colors"
                        >
                          <span>{choice.text}</span>
                          <ChevronRight className="text-muted-foreground h-5 w-5 shrink-0" />
                        </button>
                      ))}
                  </div>
                </div>
              </>
            )}

            {/* End State */}
            {isEndNode && currentNode.is_end_node && (
              <>
                <Separator />
                <div className="text-center space-y-3">
                  <p className="text-lg font-medium text-muted-foreground">
                    You've reached an ending!
                  </p>
                  <Button onClick={handleRestart}>
                    <Play className="mr-2 h-4 w-4" />
                    Play Again
                  </Button>
                </div>
              </>
            )}

            {/* Dead End Warning */}
            {!currentNode.is_end_node && availableChoices.length === 0 && (
              <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg p-4 text-center">
                <p className="text-amber-700 dark:text-amber-400 text-sm">
                  No choices available from this node (dead end or conditions
                  not met). Use Undo or Restart to continue.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
```

**Step 2: Update index exports**

Modify `frontend/src/components/Story/StoryPlayer/index.ts`:

```tsx
// StoryPlayer module exports
//
// Components for the Story player panel system.
// StoryPlayerProvider should wrap StoryLayout to share state across panels.

export { StoryPlayerProvider } from "./StoryPlayerProvider"
export { useStoryPlayerContext } from "./useStoryPlayerContext"
export { StoryContent } from "./StoryContent"
export type {
  StoryPlayerContextValue,
  HistoryEntry,
} from "./StoryPlayerProvider"
```

**Step 3: Verify TypeScript compilation**

Run: `cd /home/josep/dog/frontend && npx tsc --noEmit 2>&1 | head -30`

Expected: No new errors

**Step 4: Commit**

```bash
git add frontend/src/components/Story/StoryPlayer/
git commit -m "feat(story): add StoryContent component for node rendering

- Extract content rendering from StoryPlayer
- Handles HTML/JSON/text formats
- Shows choices, end state, dead-end warnings
- Consumes context via useStoryPlayerContext"
```

---

## Task 3: Create StoryPlayerPanel

**Files:**
- Create: `frontend/src/components/Story/panels/StoryPlayerPanel.tsx`
- Create: `frontend/src/components/Story/panels/index.ts`

**Step 1: Create StoryPlayerPanel**

Create `frontend/src/components/Story/panels/StoryPlayerPanel.tsx`:

```tsx
/**
 * StoryPlayerPanel
 *
 * Primary panel for the Story shell that displays interactive story content.
 *
 * ARCHITECTURE DECISION: This panel has no props - all data comes from
 * StoryPlayerContext. This keeps PanelConfig.render() functions clean:
 *   render: () => <StoryPlayerPanel />
 *
 * RESPONSIBILITIES:
 * - Wraps content in PanelContainer (consistent panel structure)
 * - Provides ActionBar with Undo/Restart actions
 * - Delegates content rendering to StoryContent
 * - Handles loading/error states
 */
import { AlertCircle, Loader2, Play, RotateCcw } from "lucide-react"
import { PanelContainer } from "../primitives/PanelContainer"
import { ActionBar, type ActionItem } from "../primitives/ActionBar"
import { StoryContent, useStoryPlayerContext } from "../StoryPlayer"

export function StoryPlayerPanel() {
  const { story, isLoading, error, history, handleUndo, handleRestart } =
    useStoryPlayerContext()

  // Build header actions
  // ARCHITECTURE DECISION: Actions come from context (native to player),
  // not from external hooks. This keeps the panel self-contained.
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

  // Loading state
  if (isLoading) {
    return (
      <PanelContainer title="Player">
        <div className="flex items-center justify-center h-full">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </PanelContainer>
    )
  }

  // Error state
  if (error) {
    return (
      <PanelContainer title="Player">
        <div className="flex flex-col items-center justify-center h-full text-center p-6">
          <AlertCircle className="h-8 w-8 text-destructive mb-4" />
          <p className="text-sm text-muted-foreground">
            {error.message || "Failed to load story"}
          </p>
        </div>
      </PanelContainer>
    )
  }

  // Normal rendering
  return (
    <PanelContainer
      title={story?.title || "Player"}
      headerActions={<ActionBar actions={actions} />}
      scrollable={true}
    >
      <StoryContent />
    </PanelContainer>
  )
}
```

**Step 2: Create panels index**

Create `frontend/src/components/Story/panels/index.ts`:

```tsx
// Story panels exports
//
// Panels for use within StoryLayout.
// All panels consume StoryPlayerContext for shared state.

export { StoryPlayerPanel } from "./StoryPlayerPanel"
```

**Step 3: Verify TypeScript compilation**

Run: `cd /home/josep/dog/frontend && npx tsc --noEmit 2>&1 | head -30`

Expected: No new errors

**Step 4: Commit**

```bash
git add frontend/src/components/Story/panels/
git commit -m "feat(story): add StoryPlayerPanel as primary Story panel

- Uses PanelContainer + ActionBar from Story primitives
- Provides Undo/Restart actions in header
- Delegates content to StoryContent
- Handles loading/error states inline"
```

---

## Task 4: Create StoryDebugPanel

**Files:**
- Create: `frontend/src/components/Story/panels/StoryDebugPanel.tsx`
- Modify: `frontend/src/components/Story/panels/index.ts`

**Step 1: Create StoryDebugPanel**

Create `frontend/src/components/Story/panels/StoryDebugPanel.tsx`:

```tsx
/**
 * StoryDebugPanel
 *
 * Auxiliary panel showing player state, choice history, and available choices.
 *
 * ARCHITECTURE DECISION: This is a separate panel (not embedded in StoryPlayerPanel)
 * so it can be:
 * 1. Shown/hidden via layout configuration
 * 2. Positioned independently (auxiliary column)
 * 3. Evolved separately from the player UI
 *
 * SECTIONS:
 * - Player State: Current key-value pairs in playerState
 * - Choice History: List of choices made with index
 * - Available Choices: All choices for node, showing blocked status + conditions
 */
import { useState } from "react"
import { Bug, ChevronDown, ChevronUp, Loader2 } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { PanelContainer } from "../primitives/PanelContainer"
import { useStoryPlayerContext } from "../StoryPlayer"

export function StoryDebugPanel() {
  const {
    isLoading,
    playerState,
    history,
    availableChoices,
    allChoicesForNode,
    currentNode,
  } = useStoryPlayerContext()

  // Local UI state for collapsible sections
  const [expandedSections, setExpandedSections] = useState({
    state: true,
    history: true,
    choices: true,
  })

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }))
  }

  // Loading state
  if (isLoading) {
    return (
      <PanelContainer title="Debug">
        <div className="flex items-center justify-center h-full">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      </PanelContainer>
    )
  }

  return (
    <PanelContainer title="Debug" scrollable={true}>
      <div className="p-4 space-y-4">
        {/* Header */}
        <h3 className="text-sm font-semibold flex items-center gap-2">
          <Bug className="h-4 w-4" />
          Debug Panel
        </h3>

        {/* Player State Section */}
        <Collapsible
          open={expandedSections.state}
          onOpenChange={() => toggleSection("state")}
        >
          <CollapsibleTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="w-full justify-between"
            >
              <span>Player State ({Object.keys(playerState).length})</span>
              {expandedSections.state ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </Button>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <div className="bg-muted rounded-md p-3 mt-2 text-xs">
              {Object.keys(playerState).length === 0 ? (
                <span className="text-muted-foreground">No state set yet</span>
              ) : (
                <div className="space-y-2">
                  {Object.entries(playerState).map(([key, value]) => (
                    <div key={key}>
                      <span className="font-semibold">{key}:</span>{" "}
                      <span className="text-muted-foreground">
                        {JSON.stringify(value)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </CollapsibleContent>
        </Collapsible>

        {/* Choice History Section */}
        <Collapsible
          open={expandedSections.history}
          onOpenChange={() => toggleSection("history")}
        >
          <CollapsibleTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="w-full justify-between"
            >
              <span>Choice History ({history.length})</span>
              {expandedSections.history ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </Button>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <div className="bg-muted rounded-md p-3 mt-2 text-xs max-h-40 overflow-y-auto">
              {history.length === 0 ? (
                <span className="text-muted-foreground">
                  No choices made yet
                </span>
              ) : (
                <div className="space-y-1">
                  {history.map((entry, index) => (
                    <div key={index} className="truncate">
                      <span className="text-muted-foreground">
                        {index + 1}.
                      </span>{" "}
                      {entry.choiceText}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </CollapsibleContent>
        </Collapsible>

        {/* Available Choices Section */}
        <Collapsible
          open={expandedSections.choices}
          onOpenChange={() => toggleSection("choices")}
        >
          <CollapsibleTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="w-full justify-between"
            >
              <span>
                Choices ({availableChoices.length}/{allChoicesForNode.length})
              </span>
              {expandedSections.choices ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </Button>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <div className="bg-muted rounded-md p-3 mt-2 text-xs max-h-60 overflow-y-auto space-y-3">
              {allChoicesForNode.length === 0 ? (
                <span className="text-muted-foreground">
                  No choices from this node
                </span>
              ) : (
                allChoicesForNode.map((choice) => {
                  const isAvailable = availableChoices.includes(choice)
                  return (
                    <div
                      key={choice.id}
                      className={`space-y-1 ${!isAvailable ? "opacity-50" : ""}`}
                    >
                      <div className="flex items-start gap-2">
                        <span className={isAvailable ? "" : "line-through"}>
                          {choice.text}
                        </span>
                        {!isAvailable && (
                          <Badge
                            variant="outline"
                            className="text-[10px] shrink-0"
                          >
                            Blocked
                          </Badge>
                        )}
                      </div>
                      {choice.requires_state && (
                        <div className="text-amber-600 dark:text-amber-400 break-all">
                          <span className="font-semibold">Requires:</span>{" "}
                          {JSON.stringify(choice.requires_state)}
                        </div>
                      )}
                      {choice.sets_state && (
                        <div className="text-blue-600 dark:text-blue-400 break-all">
                          <span className="font-semibold">Sets:</span>{" "}
                          {JSON.stringify(choice.sets_state)}
                        </div>
                      )}
                    </div>
                  )
                })
              )}
            </div>
          </CollapsibleContent>
        </Collapsible>

        {/* Current Node Info */}
        <div className="border-t pt-4">
          <p className="text-xs text-muted-foreground mb-1">Current Node:</p>
          <code className="text-xs bg-muted px-2 py-1 rounded block truncate">
            {currentNode?.title || "None"}
          </code>
        </div>
      </div>
    </PanelContainer>
  )
}
```

**Step 2: Update panels index**

Modify `frontend/src/components/Story/panels/index.ts`:

```tsx
// Story panels exports
//
// Panels for use within StoryLayout.
// All panels consume StoryPlayerContext for shared state.

export { StoryPlayerPanel } from "./StoryPlayerPanel"
export { StoryDebugPanel } from "./StoryDebugPanel"
```

**Step 3: Verify TypeScript compilation**

Run: `cd /home/josep/dog/frontend && npx tsc --noEmit 2>&1 | head -30`

Expected: No new errors

**Step 4: Commit**

```bash
git add frontend/src/components/Story/panels/
git commit -m "feat(story): add StoryDebugPanel as auxiliary panel

- Shows player state, choice history, available choices
- Collapsible sections for compact view
- Displays blocked choices with conditions
- Decoupled from StoryPlayerPanel for layout flexibility"
```

---

## Task 5: Integrate Provider into StoryShell

**Files:**
- Modify: `frontend/src/components/Story/StoryShell.tsx`

**Step 1: Update StoryShell to accept storyId and wrap with provider**

Modify `frontend/src/components/Story/StoryShell.tsx`:

```tsx
// src/components/Story/StoryShell.tsx
/**
 * StoryShell - Main container that orchestrates the Story page layout
 *
 * ARCHITECTURE DECISION: StoryPlayerProvider wraps StoryLayout so that
 * all panels can access shared player state via context. The shell knows
 * the storyId (from route params) and passes it to the provider.
 *
 * THEMING: Uses two-layer theme cascade:
 * 1. Page theme (outer) - affects header and overall page
 * 2. Cards theme (inner) - affects panel content areas
 */
import * as React from "react"
import { cn } from "@/lib/utils"
import { StoryHeader } from "./StoryHeader"
import { StoryLayout, type PanelConfig } from "./StoryLayout"
import {
  getPageThemeById,
  getPageThemeStyle,
} from "@/components/Common/Themes/page_themes"
import {
  getCardThemeById,
  getCardThemeStyle,
} from "@/components/Common/Themes/card_themes"
import { StoryPlayerProvider } from "./StoryPlayer"

export interface StoryShellProps {
  /** Story ID for data fetching */
  storyId: string
  /** Page title */
  title: string
  /** Panel configurations */
  panels: PanelConfig[]
  /** Currently selected page theme ID */
  pageThemeId: string
  /** Currently selected cards theme ID */
  cardsThemeId: string
  /** Page theme change callback */
  onPageThemeChange: (themeId: string) => void
  /** Cards theme change callback */
  onCardsThemeChange: (themeId: string) => void
  /** Additional className */
  className?: string
}

export function StoryShell({
  storyId,
  title,
  panels,
  pageThemeId,
  cardsThemeId,
  onPageThemeChange,
  onCardsThemeChange,
  className,
}: StoryShellProps) {
  const [layoutMode, setLayoutMode] = React.useState<"panels" | "tabs">("panels")

  const pageTheme = getPageThemeById(pageThemeId)
  const cardsTheme = getCardThemeById(cardsThemeId)

  return (
    // Outermost: page theme scope (affects header and content)
    // Transparent wrapper - only sets CSS variables, does not render a surface
    <div
      style={getPageThemeStyle(pageTheme)}
      className={cn("flex flex-col h-full", className)}
    >
      <StoryHeader
        title={title}
        pageThemeId={pageThemeId}
        cardsThemeId={cardsThemeId}
        onPageThemeChange={onPageThemeChange}
        onCardsThemeChange={onCardsThemeChange}
        layoutMode={layoutMode}
        onLayoutModeChange={setLayoutMode}
      />

      {/* Inner: Cards theme scope (overrides page theme for card areas) */}
      {/* Transparent wrapper - only sets CSS variables, does not render a surface */}
      <div style={getCardThemeStyle(cardsTheme)} className="flex-1 min-h-0">
        {/*
          ARCHITECTURE DECISION: Provider wraps layout so all panels
          can access shared player state without prop drilling.
          See StoryPlayerProvider for context shape.
        */}
        <StoryPlayerProvider storyId={storyId}>
          <StoryLayout panels={panels} mode={layoutMode} />
        </StoryPlayerProvider>
      </div>
    </div>
  )
}
```

**Step 2: Verify TypeScript compilation**

Run: `cd /home/josep/dog/frontend && npx tsc --noEmit 2>&1 | head -30`

Expected: May show errors in files that use StoryShell without storyId - this is expected and will be fixed in Task 6

**Step 3: Commit**

```bash
git add frontend/src/components/Story/StoryShell.tsx
git commit -m "feat(story): integrate StoryPlayerProvider into StoryShell

- Add storyId prop to StoryShell
- Wrap StoryLayout with StoryPlayerProvider
- Enables all panels to access shared player state"
```

---

## Task 6: Update Story Index Exports

**Files:**
- Modify: `frontend/src/components/Story/index.ts`

**Step 1: Update Story index to export panels**

Modify `frontend/src/components/Story/index.ts`:

```tsx
// Story component exports
//
// Main exports for the Story feature.
// Use StoryShell as the main container, configure with panel configs.

// Shell and Layout
export { StoryShell, type StoryShellProps } from "./StoryShell"
export { StoryLayout, type PanelConfig } from "./StoryLayout"

// Panels (for use in PanelConfig.render())
export { StoryPlayerPanel, StoryDebugPanel } from "./panels"

// Context (for custom panels that need player state)
export {
  StoryPlayerProvider,
  useStoryPlayerContext,
  type StoryPlayerContextValue,
  type HistoryEntry,
} from "./StoryPlayer"
```

**Step 2: Verify TypeScript compilation**

Run: `cd /home/josep/dog/frontend && npx tsc --noEmit 2>&1 | head -30`

Expected: No new errors from Story module

**Step 3: Commit**

```bash
git add frontend/src/components/Story/index.ts
git commit -m "feat(story): export panels and context from Story module

- Export StoryPlayerPanel and StoryDebugPanel
- Export StoryPlayerProvider and useStoryPlayerContext
- Enables consumers to build Story pages with panels"
```

---

## Task 7: Create Example Usage (Documentation)

**Files:**
- Create: `frontend/src/components/Story/USAGE.md`

**Step 1: Create usage documentation**

Create `frontend/src/components/Story/USAGE.md`:

```markdown
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
```

**Step 2: Commit**

```bash
git add frontend/src/components/Story/USAGE.md
git commit -m "docs(story): add usage documentation for panel system

- Quick start example
- Architecture overview
- Custom panel creation guide"
```

---

## Task 8: Final Verification

**Step 1: Run full TypeScript check**

Run: `cd /home/josep/dog/frontend && npx tsc --noEmit`

Expected: No errors (or only pre-existing unrelated errors)

**Step 2: Run linter**

Run: `cd /home/josep/dog/frontend && npm run lint`

Expected: No new lint errors in Story components

**Step 3: Start dev server and verify no runtime errors**

Run: `cd /home/josep/dog/frontend && npm run dev`

Expected: Dev server starts without errors

**Step 4: Final commit (if any fixes needed)**

```bash
git add -A
git commit -m "fix(story): address any lint/type issues from panel refactor"
```

---

## Summary

| Task | Component | Purpose |
|------|-----------|---------|
| 1 | StoryPlayerProvider | Context for runtime state |
| 2 | StoryContent | Node content rendering |
| 3 | StoryPlayerPanel | Primary panel wrapper |
| 4 | StoryDebugPanel | Auxiliary debug panel |
| 5 | StoryShell update | Provider integration |
| 6 | Index exports | Module API |
| 7 | USAGE.md | Documentation |
| 8 | Verification | Type/lint checks |

Total estimated time: 45-60 minutes
