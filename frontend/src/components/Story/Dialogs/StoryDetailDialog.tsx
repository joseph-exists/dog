/**
 * StoryDetailDialog
 *
 * View dialog for an existing story.
 * Displays story details in a larger panel with full content visible.
 *
 * Owns: open/close state, query fetching, toast feedback.
 */

import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { ExternalLinkIcon, EyeIcon, Loader2Icon } from "lucide-react"
import { useState } from "react"

import { StoriesService } from "@/client/sdk.gen"
import type { StoryPublic } from "@/client/types.gen"
import {
  resolveStoryPresentation,
  STORY_TYPE_PRESENTATIONS,
} from "@/components/Common/Themes/resolve"
import { isStoryTypeKey } from "@/components/Common/Themes/types"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import StoryAvatar from "../Display/StoryAvatar"

// ── View Mode ─────────────────────────────────────────────────────────────

function StoryViewContent({ story }: { story: StoryPublic }) {
  const storyType = isStoryTypeKey(story.story_type)
    ? story.story_type
    : undefined
  const typeDefaults = storyType
    ? STORY_TYPE_PRESENTATIONS[storyType]
    : undefined
  const resolved = resolveStoryPresentation(
    typeDefaults,
    story.presentation ?? null,
  )

  return (
    <div className="space-y-4">
      {/* Badges row */}
      <div className="flex flex-wrap gap-2">
        <Badge variant={story.is_published ? "default" : "outline"}>
          {story.is_published ? "Published" : "Draft"}
        </Badge>
        {story.is_published && story.published_version !== null && (
          <Badge variant="secondary">v{story.published_version}</Badge>
        )}
        {storyType && (
          <Badge variant="outline" className="capitalize">
            {storyType}
          </Badge>
        )}
        {resolved.decorationHint && (
          <Badge variant="outline" className="text-muted-foreground">
            {resolved.decorationHint}
          </Badge>
        )}
      </div>

      {/* Description */}
      {story.description && (
        <div className="space-y-1">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            Description
          </p>
          <p className="text-sm whitespace-pre-wrap">{story.description}</p>
        </div>
      )}

      {/* Story metadata */}
      <div className="space-y-1">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
          Version Info
        </p>
        <div className="text-sm text-muted-foreground space-y-0.5">
          <p>Current version: {story.current_version}</p>
          {story.published_version !== null && (
            <p>Published version: {story.published_version}</p>
          )}
        </div>
      </div>

      {/* Timestamps */}
      <div className="space-y-1">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
          Timestamps
        </p>
        <div className="text-sm text-muted-foreground space-y-0.5">
          <p>Created: {new Date(story.created_at).toLocaleString()}</p>
          <p>Updated: {new Date(story.updated_at).toLocaleString()}</p>
        </div>
      </div>

      {/* Presentation info */}
      {(resolved.avatar?.emoji || resolved.tokens) && (
        <div className="space-y-1">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            Presentation
          </p>
          <div className="text-sm text-muted-foreground space-y-0.5">
            {resolved.avatar?.emoji && <p>Avatar: {resolved.avatar.emoji}</p>}
            {resolved.tokens?.["--story-accent"] && (
              <p className="flex items-center gap-2">
                Accent:{" "}
                <span
                  className="inline-block w-4 h-4 rounded-sm border"
                  style={{
                    backgroundColor: resolved.tokens["--story-accent"],
                  }}
                />
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

// ── Main Dialog ───────────────────────────────────────────────────────────

interface StoryDetailDialogProps {
  storyId: string
  trigger?: React.ReactNode
  className?: string
}

export default function StoryDetailDialog({
  storyId,
  trigger,
  className,
}: StoryDetailDialogProps) {
  const [isOpen, setIsOpen] = useState(false)

  const { data: story, isLoading } = useQuery({
    queryKey: ["story", storyId],
    queryFn: () => StoriesService.readStory({ id: storyId }),
    enabled: isOpen,
  })

  const handleOpenChange = (open: boolean) => {
    setIsOpen(open)
  }

  const storyType =
    story && isStoryTypeKey(story.story_type) ? story.story_type : undefined
  const typeDefaults = storyType
    ? STORY_TYPE_PRESENTATIONS[storyType]
    : undefined
  const resolved = story
    ? resolveStoryPresentation(typeDefaults, story.presentation ?? null)
    : null

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        {trigger ?? (
          <Button variant="ghost" size="icon" className={className}>
            <EyeIcon className="size-4" />
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        {isLoading || !story ? (
          <div className="flex items-center justify-center py-8">
            <Loader2Icon className="size-6 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <StoryAvatar
                  name={story.title ?? "Story"}
                  size="sm"
                  presentation={resolved?.avatar}
                />
                <span className="truncate">{story.title ?? "Story"}</span>
              </DialogTitle>
              <DialogDescription>Story details and metadata.</DialogDescription>
            </DialogHeader>

            <StoryViewContent story={story} />

            <DialogFooter>
              <Button variant="outline" size="sm" asChild>
                <Link
                  to="/story/$storyId"
                  params={{ storyId }}
                  onClick={() => handleOpenChange(false)}
                >
                  <ExternalLinkIcon className="size-4 mr-1" />
                  Open Story
                </Link>
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => handleOpenChange(false)}
              >
                Close
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
