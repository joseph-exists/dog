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
