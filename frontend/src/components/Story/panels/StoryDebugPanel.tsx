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

import { Bug, ChevronDown, ChevronUp, Loader2 } from "lucide-react"
import { useState } from "react"
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
