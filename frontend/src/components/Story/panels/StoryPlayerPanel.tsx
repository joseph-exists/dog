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
import { ActionBar, type ActionItem } from "../primitives/ActionBar"
import { PanelContainer } from "../primitives/PanelContainer"
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
