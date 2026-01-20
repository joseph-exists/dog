/**
 * StoryEditorPanel
 *
 * Panel for collaborative story editing within a room.
 * Simplified version of StoryEditor for room context.
 *
 * Features:
 * - Resizable two-panel layout: NodeTree (30%) | NodeEditor (70%)
 * - Header with story title, version badge, publish status
 * - Loading and error states via PlaceholderContent
 */

import { BookOpen, Loader2 } from "lucide-react"
import { useState } from "react"
import NodeEditor from "@/components/Stories/StoryEditor/NodeEditor/NodeEditor"
import NodeTree from "@/components/Stories/StoryEditor/NodeTree/NodeTree"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable"
import { useStoryEditor } from "@/hooks/stories/useStoryEditor"
import { cn } from "@/lib/utils"
import { PanelContainer } from "../primitives/PanelContainer"
import { PlaceholderContent } from "../primitives/PlaceholderContent"

interface StoryEditorPanelProps {
  /** Story ID to edit */
  storyId: string
  /** Hide panel header (when page provides its own) */
  hideHeader?: boolean
  /** Additional className */
  className?: string
  /** Callback when user wants to navigate to stories list */
  onNavigateToStories?: () => void
}

export function StoryEditorPanel({
  storyId,
  hideHeader = false,
  className,
  onNavigateToStories,
}: StoryEditorPanelProps) {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)

  const { story, nodes, choices, isLoading, error } = useStoryEditor({
    storyId,
  })

  // Loading state
  if (isLoading) {
    return (
      <div className={cn("flex h-full flex-col", className)}>
        <PlaceholderContent
          icon={Loader2}
          title="Loading Story"
          description="Please wait while the story is loading..."
          className="[&_svg]:animate-spin"
        />
      </div>
    )
  }

  // Error state
  if (error || !story) {
    return (
      <div className={cn("flex h-full flex-col", className)}>
        <PlaceholderContent
          icon={BookOpen}
          title="Story Not Found"
          description={error?.message || "Unable to load the story."}
          action={
            onNavigateToStories ? (
              <Button variant="outline" size="sm" onClick={onNavigateToStories}>
                Back to Stories
              </Button>
            ) : undefined
          }
        />
      </div>
    )
  }

  // Build header actions with version and publish status badges
  const headerActions = (
    <div className="flex items-center gap-2">
      <Badge variant="secondary" className="text-xs">
        v{story.current_version}
      </Badge>
      {story.is_published ? (
        <Badge variant="default" className="text-xs">
          Published
        </Badge>
      ) : (
        <Badge variant="outline" className="text-xs">
          Draft
        </Badge>
      )}
    </div>
  )

  // Editor content with resizable panels
  const editorContent = (
    <ResizablePanelGroup direction="horizontal" className="h-full">
      {/* Left Panel: Node Tree (30%) */}
      <ResizablePanel defaultSize={30} minSize={20} maxSize={50}>
        <NodeTree
          nodes={nodes}
          choices={choices}
          selectedNodeId={selectedNodeId}
          onSelectNode={setSelectedNodeId}
          storyId={storyId}
          storyVersion={story.current_version}
        />
      </ResizablePanel>

      <ResizableHandle withHandle />

      {/* Right Panel: Node Editor (70%) */}
      <ResizablePanel defaultSize={70} minSize={40}>
        <NodeEditor
          nodeId={selectedNodeId}
          storyId={storyId}
          storyVersion={story.current_version}
          availableNodes={nodes}
        />
      </ResizablePanel>
    </ResizablePanelGroup>
  )

  // Render with or without PanelContainer based on hideHeader
  if (hideHeader) {
    return (
      <div className={cn("flex h-full flex-col", className)}>
        {editorContent}
      </div>
    )
  }

  return (
    <PanelContainer
      title={story.title}
      headerActions={headerActions}
      className={className}
      scrollable={false}
    >
      {editorContent}
    </PanelContainer>
  )
}
