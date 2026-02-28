/**
 * SoloStoryPlayerPanel
 *
 * Solo/local story player for page panels. Fetches the attached story and lets
 * the player navigate through nodes and choices entirely client-side.
 */

import DOMPurify from "dompurify"
import {
  AlertCircle,
  BookOpen,
  ChevronDown,
  ChevronRight,
  ChevronUp,
  Loader2,
  Play,
  RotateCcw,
  Undo2,
} from "lucide-react"
import { useMemo, useState } from "react"
import type { NodeChoicePublic, StoryNodePublic } from "@/client"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { Separator } from "@/components/ui/separator"
import { useStoryEditor } from "@/hooks/stories/useStoryEditor"
import {
  applySetsState,
  evaluateRequiresState,
  type StateConditions,
  type StateMutations,
} from "@/utils/stateConditions"
import { PanelContainer } from "../primitives/PanelContainer"
import { PlaceholderContent } from "../primitives/PlaceholderContent"

// ============================================================================
// Types
// ============================================================================

export interface StoryProgressEvent {
  type:
    | "choice_made"
    | "story_started"
    | "story_ended"
    | "story_restarted"
    | "story_rewound"
  nodeTitle: string
  choiceText?: string
  isEndNode?: boolean
}

interface SoloStoryPlayerPanelProps {
  storyId: string
  onStoryEvent?: (event: StoryProgressEvent) => void
  runtimeNotice?: string | null
}

interface HistoryEntry {
  nodeId: string
  state: Record<string, unknown>
  choiceText?: string
}

// ============================================================================
// Content Renderer
// ============================================================================

function renderContent(node: StoryNodePublic) {
  const format = node.content_format || "text"
  const content = node.content || ""

  switch (format) {
    case "html":
      return (
        <div
          className="prose prose-sm dark:prose-invert max-w-none"
          dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(content) }}
        />
      )
    case "json":
      try {
        const parsed = JSON.parse(content)
        return (
          <pre className="bg-muted p-3 rounded-md overflow-auto text-xs font-mono">
            {JSON.stringify(parsed, null, 2)}
          </pre>
        )
      } catch {
        return (
          <p className="text-destructive text-sm">[Invalid JSON content]</p>
        )
      }
    default:
      return (
        <p className="text-sm leading-relaxed whitespace-pre-wrap">
          {content || "(No content)"}
        </p>
      )
  }
}

// ============================================================================
// Component
// ============================================================================

export function SoloStoryPlayerPanel({
  storyId,
  onStoryEvent,
  runtimeNotice = null,
}: SoloStoryPlayerPanelProps) {
  const { story, nodes, choices, isLoading, error } = useStoryEditor({
    storyId,
  })

  // Find the start node
  const startNode = useMemo(() => nodes.find((n) => n.is_start_node), [nodes])

  // Core game state
  const [currentNodeId, setCurrentNodeId] = useState<string | null>(null)
  const [playerState, setPlayerState] = useState<Record<string, unknown>>({})
  const [history, setHistory] = useState<HistoryEntry[]>([])
  const [hasStarted, setHasStarted] = useState(false)

  // Debug sections
  const [expandedSections, setExpandedSections] = useState({
    state: false,
    history: false,
  })

  // Current node
  const currentNode = useMemo(
    () => nodes.find((n) => n.id === currentNodeId),
    [nodes, currentNodeId],
  )

  // Choices for current node, filtered by state conditions
  const allChoicesForNode = useMemo(
    () => choices.filter((c) => c.from_node_id === currentNodeId),
    [choices, currentNodeId],
  )

  const availableChoices = useMemo(
    () =>
      allChoicesForNode.filter((choice) =>
        evaluateRequiresState(
          choice.requires_state as StateConditions | null,
          playerState,
        ),
      ),
    [allChoicesForNode, playerState],
  )

  const isEndNode = currentNode?.is_end_node || availableChoices.length === 0

  // ──────────────────────────────────────────────────────────────────────────
  // Handlers
  // ──────────────────────────────────────────────────────────────────────────

  const handleStart = () => {
    if (!startNode) return
    setCurrentNodeId(startNode.id)
    setHasStarted(true)
    setPlayerState({})
    setHistory([])
    onStoryEvent?.({
      type: "story_started",
      nodeTitle: startNode.title,
    })
  }

  const handleChoice = (choice: NodeChoicePublic) => {
    if (!currentNode || !choice.to_node_id) return

    // Save to history
    setHistory((prev) => [
      ...prev,
      {
        nodeId: currentNode.id,
        state: { ...playerState },
        choiceText: choice.text,
      },
    ])

    // Apply state mutations
    if (choice.sets_state) {
      setPlayerState((prev) =>
        applySetsState(choice.sets_state as StateMutations, prev),
      )
    }

    // Navigate
    setCurrentNodeId(choice.to_node_id)

    // Emit event
    const targetNode = nodes.find((n) => n.id === choice.to_node_id)
    onStoryEvent?.({
      type: targetNode?.is_end_node ? "story_ended" : "choice_made",
      nodeTitle: targetNode?.title ?? "Unknown",
      choiceText: choice.text,
      isEndNode: targetNode?.is_end_node ?? false,
    })
  }

  const handleUndo = () => {
    if (history.length === 0) return
    const previous = history[history.length - 1]
    setCurrentNodeId(previous.nodeId)
    setPlayerState(previous.state)
    setHistory((prev) => prev.slice(0, -1))

    const prevNode = nodes.find((n) => n.id === previous.nodeId)
    onStoryEvent?.({
      type: "story_rewound",
      nodeTitle: prevNode?.title ?? "Unknown",
    })
  }

  const handleRestart = () => {
    if (!startNode) return
    setHistory([])
    setPlayerState({})
    setCurrentNodeId(startNode.id)
    onStoryEvent?.({
      type: "story_restarted",
      nodeTitle: startNode.title,
    })
  }

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }))
  }

  // ──────────────────────────────────────────────────────────────────────────
  // Loading / Error / Empty states
  // ──────────────────────────────────────────────────────────────────────────

  if (!storyId) {
    return (
      <PanelContainer title="Solo Story Player">
        <PlaceholderContent
          icon={BookOpen}
          title="No Story Attached"
          description="This panel doesn't have a story attached yet."
        />
      </PanelContainer>
    )
  }

  if (isLoading) {
    return (
      <PanelContainer title="Solo Story Player">
        <PlaceholderContent
          icon={Loader2}
          title="Loading Story"
          description="Fetching story data..."
          className="[&_svg]:animate-spin"
        />
      </PanelContainer>
    )
  }

  if (error) {
    return (
      <PanelContainer title="Solo Story Player">
        <PlaceholderContent
          icon={AlertCircle}
          title="Failed to Load Story"
          description={error.message || "Please try again."}
        />
      </PanelContainer>
    )
  }

  if (!story || nodes.length === 0) {
    return (
      <PanelContainer title="Solo Story Player">
        <PlaceholderContent
          icon={BookOpen}
          title="Story Not Ready"
          description="This story has no nodes yet."
        />
      </PanelContainer>
    )
  }

  // ──────────────────────────────────────────────────────────────────────────
  // Pre-start state
  // ──────────────────────────────────────────────────────────────────────────

  if (!hasStarted || !currentNode) {
    return (
      <PanelContainer title="Solo Story Player">
        <div className="flex flex-col items-center justify-center gap-4 p-6 text-center h-full">
          <BookOpen className="h-10 w-10 text-muted-foreground" />
          <div>
            <h3 className="font-semibold text-lg">{story.title}</h3>
            {story.description && (
              <p className="text-sm text-muted-foreground mt-1">
                {story.description}
              </p>
            )}
          </div>
          <Badge variant="secondary" className="text-xs">
            {nodes.length} nodes · {choices.length} choices
          </Badge>
          {runtimeNotice ? (
            <div className="max-w-md rounded-lg border border-amber-300/70 bg-amber-50 px-3 py-2 text-xs text-amber-900 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-200">
              {runtimeNotice}
            </div>
          ) : null}
          <Button onClick={handleStart} disabled={!startNode}>
            <Play className="mr-2 h-4 w-4" />
            Begin Story
          </Button>
          {!startNode && (
            <p className="text-xs text-destructive">No start node found</p>
          )}
        </div>
      </PanelContainer>
    )
  }

  // ──────────────────────────────────────────────────────────────────────────
  // Active play state
  // ──────────────────────────────────────────────────────────────────────────

  const headerActions = (
    <div className="flex items-center gap-1">
      <Button
        size="icon"
        variant="ghost"
        className="h-7 w-7"
        onClick={handleUndo}
        disabled={history.length === 0}
        title="Undo"
      >
        <Undo2 className="h-3.5 w-3.5" />
      </Button>
      <Button
        size="icon"
        variant="ghost"
        className="h-7 w-7"
        onClick={handleRestart}
        title="Restart"
      >
        <RotateCcw className="h-3.5 w-3.5" />
      </Button>
    </div>
  )

  return (
    <PanelContainer title="Solo Story Player" headerActions={headerActions}>
      <div className="flex flex-col gap-4 p-4">
        {runtimeNotice ? (
          <div className="rounded-lg border border-amber-300/70 bg-amber-50 px-3 py-2 text-xs text-amber-900 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-200">
            {runtimeNotice}
          </div>
        ) : null}
        {/* Node Title */}
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">{currentNode.title}</h3>
          {isEndNode && (
            <Badge variant="default" className="text-xs bg-green-600">
              The End
            </Badge>
          )}
        </div>

        {/* Node Content */}
        {renderContent(currentNode)}

        {/* Choices */}
        {!isEndNode && availableChoices.length > 0 && (
          <>
            <Separator />
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase mb-2">
                What do you do?
              </p>
              <div className="space-y-2">
                {availableChoices
                  .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
                  .map((choice) => (
                    <button
                      key={choice.id}
                      type="button"
                      onClick={() => handleChoice(choice)}
                      className="hover:bg-muted border-border bg-background flex w-full items-center justify-between rounded-lg border p-3 text-left text-sm transition-colors"
                    >
                      <span>{choice.text}</span>
                      <ChevronRight className="text-muted-foreground h-4 w-4 shrink-0" />
                    </button>
                  ))}
              </div>
            </div>
          </>
        )}

        {/* End State */}
        {isEndNode && (
          <>
            <Separator />
            <div className="text-center space-y-3">
              <p className="text-sm font-medium text-muted-foreground">
                You've reached an ending!
              </p>
              <Button size="sm" onClick={handleRestart}>
                <Play className="mr-2 h-3.5 w-3.5" />
                Play Again
              </Button>
            </div>
          </>
        )}

        {/* Dead End Warning */}
        {!currentNode.is_end_node && availableChoices.length === 0 && (
          <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg p-3 text-center">
            <p className="text-amber-700 dark:text-amber-400 text-xs">
              No choices available (dead end or conditions not met)
            </p>
          </div>
        )}

        {/* Debug Sections */}
        <Separator className="mt-2" />

        {/* Player State */}
        <Collapsible
          open={expandedSections.state}
          onOpenChange={() => toggleSection("state")}
        >
          <CollapsibleTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="w-full justify-between h-7 text-xs"
            >
              <span>State ({Object.keys(playerState).length})</span>
              {expandedSections.state ? (
                <ChevronUp className="h-3 w-3" />
              ) : (
                <ChevronDown className="h-3 w-3" />
              )}
            </Button>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <div className="bg-muted rounded-md p-2 mt-1 text-xs">
              {Object.keys(playerState).length === 0 ? (
                <span className="text-muted-foreground">No state set</span>
              ) : (
                <div className="space-y-1">
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

        {/* History */}
        <Collapsible
          open={expandedSections.history}
          onOpenChange={() => toggleSection("history")}
        >
          <CollapsibleTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="w-full justify-between h-7 text-xs"
            >
              <span>History ({history.length})</span>
              {expandedSections.history ? (
                <ChevronUp className="h-3 w-3" />
              ) : (
                <ChevronDown className="h-3 w-3" />
              )}
            </Button>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <div className="bg-muted rounded-md p-2 mt-1 text-xs max-h-32 overflow-y-auto">
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
      </div>
    </PanelContainer>
  )
}
