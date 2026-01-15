/**
 * StoryEditor - Main editor layout for interactive stories
 *
 * Features:
 * - Two-panel layout: NodeTree (left, 280px) | NodeEditor (right, flex)
 * - Header with: back button, story title, preview toggle, publish button
 * - Preview mode toggle (renders StoryPreview when active)
 * - Publish workflow integration with validation status
 *
 * @see STORIES_MIGRATION_TASKS.md Phase 2
 */

import { useNavigate } from "@tanstack/react-router"
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle,
  Copy,
  Eye,
  Loader2,
} from "lucide-react"
import { useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { usePublishWorkflow } from "@/hooks/stories/usePublishWorkflow"
import { useCloneStory } from "@/hooks/stories/useStories"
import { useStoryEditor } from "@/hooks/stories/useStoryEditor"
import { PublishModal } from "../PublishWorkflow"
import StoryPreview from "../StoryPlayer/StoryPreview"
import NodeEditor from "./NodeEditor/NodeEditor"
// Story components
import NodeTree from "./NodeTree/NodeTree"
import { StateSchemaSheet } from "./StateSchema"

interface StoryEditorProps {
  storyId: string
}

const StoryEditor = ({ storyId }: StoryEditorProps) => {
  const navigate = useNavigate()
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [isPreviewMode, setIsPreviewMode] = useState(false)
  const [showPublishDialog, setShowPublishDialog] = useState(false)

  const { story, nodes, choices, isLoading, error, validateForPublish } =
    useStoryEditor({ storyId })

  // Publish workflow hook for unpublish action (publish is handled by PublishModal)
  const { unpublish, isUnpublishing } = usePublishWorkflow({ storyId })

  // Clone story mutation
  const cloneMutation = useCloneStory()

  const handleClone = async () => {
    if (!story) return
    const clonedStory = await cloneMutation.mutateAsync({
      title: story.title,
      description: story.description,
    })
    // Navigate to the cloned story's editor
    navigate({
      to: "/stories/$storyId/edit",
      params: { storyId: clonedStory.id },
    })
  }

  // Run validation when story and nodes are loaded
  const validation =
    story && nodes
      ? validateForPublish()
      : { isValid: false, errors: [], warnings: [] }

  // Loading state
  if (isLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="text-muted-foreground h-8 w-8 animate-spin" />
      </div>
    )
  }

  // Error state
  if (error || !story) {
    return (
      <div className="container mx-auto max-w-7xl py-8">
        <div className="text-destructive text-lg font-semibold">
          Error loading story
        </div>
        <p className="text-muted-foreground mt-2">
          {error?.message || "Story not found"}
        </p>
        <Button
          variant="outline"
          className="mt-4"
          onClick={() => navigate({ to: "/stories" })}
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Stories
        </Button>
      </div>
    )
  }

  // Preview Mode
  if (isPreviewMode) {
    return (
      <StoryPreview
        story={story}
        nodes={nodes}
        choices={choices}
        onExit={() => setIsPreviewMode(false)}
      />
    )
  }

  // Determine if story needs publishing
  const needsPublish =
    !story.is_published ||
    (story.published_version !== null &&
      story.current_version > story.published_version)

  // Editor Mode
  return (
    <div className="flex h-screen flex-col">
      {/* Header */}
      <header className="border-border flex-shrink-0 border-b">
        <div className="flex items-center justify-between px-4 py-3">
          {/* Left: Back button + Story info */}
          <div className="flex items-center gap-4">
            <Button
              size="sm"
              variant="ghost"
              onClick={() => navigate({ to: "/stories" })}
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>

            <div>
              <h1 className="text-lg font-semibold">{story.title}</h1>
              <div className="text-muted-foreground flex items-center gap-2 text-sm">
                <span>v{story.current_version}</span>
                {story.published_version !== null &&
                  story.current_version > story.published_version && (
                    <Badge variant="secondary" className="text-xs">
                      Draft
                    </Badge>
                  )}
                {story.is_published && (
                  <Badge variant="default" className="text-xs">
                    Published v{story.published_version}
                  </Badge>
                )}
              </div>
            </div>
          </div>

          {/* Right: Clone + State Schema + Preview + Validation + Publish */}
          <div className="flex items-center gap-2">
            {/* Clone Story */}
            <Button
              size="sm"
              variant="outline"
              onClick={handleClone}
              disabled={cloneMutation.isPending}
              title="Create a copy of this story"
            >
              {cloneMutation.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Copy className="mr-2 h-4 w-4" />
              )}
              Clone
            </Button>

            {/* State Schema */}
            <StateSchemaSheet
              storyId={storyId}
              version={story.current_version}
              isPublished={story.is_published}
              publishedVersion={story.published_version}
            />

            {/* Preview Toggle */}
            <Button
              size="sm"
              variant="outline"
              onClick={() => setIsPreviewMode(true)}
            >
              <Eye className="mr-2 h-4 w-4" />
              Preview
            </Button>

            {/* Validation Status Indicator */}
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="flex items-center">
                    {validation.isValid ? (
                      <CheckCircle className="h-5 w-5 text-green-500" />
                    ) : (
                      <AlertTriangle className="h-5 w-5 text-yellow-500" />
                    )}
                  </div>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="max-w-xs">
                  {validation.isValid ? (
                    <p>Story is valid and ready to publish</p>
                  ) : (
                    <div className="space-y-1">
                      {validation.errors.map((err, i) => (
                        <p key={i} className="text-destructive text-sm">
                          {err}
                        </p>
                      ))}
                      {validation.warnings.map((warn, i) => (
                        <p key={i} className="text-sm text-yellow-600">
                          {warn}
                        </p>
                      ))}
                    </div>
                  )}
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>

            {/* Publish/Unpublish Button */}
            {needsPublish ? (
              <>
                <Button size="sm" onClick={() => setShowPublishDialog(true)}>
                  Publish
                </Button>
                <PublishModal
                  storyId={storyId}
                  isOpen={showPublishDialog}
                  onClose={() => setShowPublishDialog(false)}
                />
              </>
            ) : story.is_published ? (
              <Button
                size="sm"
                variant="outline"
                onClick={unpublish}
                disabled={isUnpublishing}
              >
                {isUnpublishing ? "..." : "Unpublish"}
              </Button>
            ) : null}
          </div>
        </div>
      </header>

      {/* Two-Panel Layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Panel: Node Tree (280px) */}
        <aside className="bg-muted/30 border-border w-[280px] flex-shrink-0 overflow-y-auto border-r">
          <NodeTree
            nodes={nodes}
            choices={choices}
            selectedNodeId={selectedNodeId}
            onSelectNode={setSelectedNodeId}
            storyId={storyId}
            storyVersion={story.current_version}
          />
        </aside>

        {/* Right Panel: Node Editor (flex) */}
        <main className="flex-1 overflow-y-auto">
          <NodeEditor
            nodeId={selectedNodeId}
            storyId={storyId}
            storyVersion={story.current_version}
            availableNodes={nodes}
          />
        </main>
      </div>
    </div>
  )
}

export default StoryEditor
