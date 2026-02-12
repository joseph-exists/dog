/**
 * StoryPreview - Interactive story player for testing
 *
 * Features:
 * - State management (currentNodeId, playerState, history)
 * - Content rendering (HTML sanitized, Text plain, JSON formatted)
 * - Choice display filtered by requires_state conditions
 * - State mutations via sets_state on choice selection
 * - Navigation controls (undo with state restoration, restart)
 * - Collapsible debug panel (state, history, available choices)
 *
 * 
 */

import DOMPurify from "dompurify"
import {
  ArrowLeft,
  Bug,
  ChevronDown,
  ChevronRight,
  ChevronUp,
  Play,
  RotateCcw,
} from "lucide-react"
import { useMemo, useState } from "react"
import type { NodeChoicePublic, StoryNodePublic, StoryPublic } from "@/client"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { Separator } from "@/components/ui/separator"
import {
  applySetsState,
  evaluateRequiresState,
  type StateConditions,
  type StateMutations,
} from "@/utils/stateConditions"

interface StoryPreviewProps {
  story: StoryPublic
  nodes: StoryNodePublic[]
  choices: NodeChoicePublic[]
  onExit: () => void
}

interface HistoryEntry {
  nodeId: string
  state: Record<string, unknown>
  choiceText?: string
}

/**
 * Renders node content based on format with appropriate styling
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

const StoryPreview = ({ story, nodes, choices, onExit }: StoryPreviewProps) => {
  // Find the start node
  const startNode = useMemo(() => nodes.find((n) => n.is_start_node), [nodes])

  // Core state
  const [currentNodeId, setCurrentNodeId] = useState<string | null>(
    startNode?.id ?? null,
  )
  const [playerState, setPlayerState] = useState<Record<string, unknown>>({})
  const [history, setHistory] = useState<HistoryEntry[]>([])

  // Debug panel visibility
  const [showDebugPanel, setShowDebugPanel] = useState(true)
  const [expandedSections, setExpandedSections] = useState({
    state: true,
    history: true,
    choices: true,
  })

  // Get current node
  const currentNode = useMemo(
    () => nodes.find((n) => n.id === currentNodeId),
    [nodes, currentNodeId],
  )

  // Get all choices for current node
  const allChoicesForNode = useMemo(
    () => choices.filter((c) => c.from_node_id === currentNodeId),
    [choices, currentNodeId],
  )

  // Filter choices by requires_state conditions
  const availableChoices = useMemo(() => {
    return allChoicesForNode.filter((choice) =>
      evaluateRequiresState(
        choice.requires_state as StateConditions | null,
        playerState,
      ),
    )
  }, [allChoicesForNode, playerState])

  // Handle choice selection
  const handleChoice = (choice: NodeChoicePublic) => {
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
        applySetsState(choice.sets_state as StateMutations, prev),
      )
    }

    // Navigate to next node
    setCurrentNodeId(choice.to_node_id)
  }

  // Handle undo - restores both node AND state
  const handleUndo = () => {
    if (history.length === 0) return

    const previous = history[history.length - 1]
    setCurrentNodeId(previous.nodeId)
    setPlayerState(previous.state)
    setHistory((prev) => prev.slice(0, -1))
  }

  // Handle restart - resets everything
  const handleRestart = () => {
    setHistory([])
    setPlayerState({})
    setCurrentNodeId(startNode?.id ?? null)
  }

  // Toggle debug section
  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }))
  }

  // Determine if at end
  const isEndNode = currentNode?.is_end_node || availableChoices.length === 0

  return (
    <div className="flex h-screen flex-col bg-muted/30">
      {/* Header */}
      <header className="border-border bg-background flex items-center justify-between border-b px-4 py-3">
        <div className="flex items-center gap-4">
          <Button size="sm" variant="ghost" onClick={onExit}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Exit Preview
          </Button>
          <div>
            <h1 className="text-lg font-semibold">{story.title}</h1>
            <Badge variant="secondary" className="text-xs">
              Preview Mode
            </Badge>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={handleUndo}
            disabled={history.length === 0}
          >
            <RotateCcw className="mr-2 h-4 w-4" />
            Undo
          </Button>
          <Button size="sm" variant="outline" onClick={handleRestart}>
            <Play className="mr-2 h-4 w-4" />
            Restart
          </Button>
          <Button
            size="sm"
            variant={showDebugPanel ? "default" : "outline"}
            onClick={() => setShowDebugPanel(!showDebugPanel)}
          >
            <Bug className="h-4 w-4" />
          </Button>
        </div>
      </header>

      {/* Content Area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Main Story Content */}
        <main className="flex-1 overflow-y-auto p-8">
          <div className="mx-auto max-w-2xl">
            {!startNode ? (
              <Card>
                <CardContent className="py-8 text-center">
                  <p className="text-destructive font-medium">
                    No start node found
                  </p>
                  <p className="text-muted-foreground mt-2 text-sm">
                    Add a node marked as "Start" to begin the story
                  </p>
                </CardContent>
              </Card>
            ) : !currentNode ? (
              <Card>
                <CardContent className="py-8 text-center">
                  <p className="text-destructive font-medium">Node not found</p>
                  <Button className="mt-4" onClick={handleRestart}>
                    Restart
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-2xl">
                      {currentNode.title}
                    </CardTitle>
                    {isEndNode && (
                      <Badge className="bg-green-600">The End</Badge>
                    )}
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
                  {isEndNode && (
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
                  {!currentNode.is_end_node &&
                    availableChoices.length === 0 && (
                      <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg p-4 text-center">
                        <p className="text-amber-700 dark:text-amber-400 text-sm">
                          No choices available from this node (dead end or
                          conditions not met)
                        </p>
                      </div>
                    )}
                </CardContent>
              </Card>
            )}
          </div>
        </main>

        {/* Debug Panel */}
        {showDebugPanel && (
          <aside className="bg-background border-border w-80 overflow-y-auto border-l p-4 space-y-4">
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <Bug className="h-4 w-4" />
              Debug Panel
            </h3>

            {/* Player State */}
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
                    <span className="text-muted-foreground">
                      No state set yet
                    </span>
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

            {/* Choice History */}
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

            {/* Available Choices */}
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
                    Choices ({availableChoices.length}/
                    {allChoicesForNode.length})
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
              <p className="text-xs text-muted-foreground mb-1">
                Current Node:
              </p>
              <code className="text-xs bg-muted px-2 py-1 rounded block truncate">
                {currentNode?.title || "None"}
              </code>
            </div>
          </aside>
        )}
      </div>
    </div>
  )
}

export default StoryPreview
