/**
 * StoryCard - Individual story display card
 *
 * Features:
 * - Status badge: Published (primary), Unpublished (secondary), Draft (outline)
 * - Editing badge when current_version > published_version
 * - Action buttons: Edit, Publish/Unpublish, Delete
 * - Linked rooms display with navigation
 * - Relative timestamp formatting
 */

import { useQuery } from "@tanstack/react-query"
import { Link, useNavigate } from "@tanstack/react-router"
import { Edit, MessageSquare, Plus, Trash2 } from "lucide-react"
import React, { useState } from "react"
import { cn } from "@/lib/utils"
// , resolveStoryPresentation ??
import { presentationToStyle } from "@/components/Common/Themes/resolve"
import type { StoryPresentation } from "@/components/Common/Themes/types"
import { RoomsService, type StoryPublic } from "@/client"
import AddRoom from "@/components/Room/Dialogs/AddRoom"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  useDeleteStory,
  usePublishStory,
  useUnpublishStory,
} from "@/hooks/stories/useStories"
import StoryAvatar from "../Display/StoryAvatar"
// use existing storybadges, migrate later 

interface StoryCardProps {
  story: StoryPublic
  variant?: "full" | "compact" | "mini"
  href?: string
  presentationEnabled?: boolean
  isSelected?: boolean
  onClick?: () => void
  action?: React.ReactNode
  className?: string
  debug? : boolean
}

// ── Accent Strip ──────────────────────────────────────────────────────────

function AccentStrip({
  presentation,
  enabled,
}: {
  presentation: StoryPresentation
  enabled: boolean
}) {
  if (!enabled) return null

  const position = presentation.tokens?.["--story-accent-position"] ?? "top"
  const width = presentation.tokens?.["--story-accent-width"] ?? "3px"
  const color = presentation.tokens?.["--story-accent"]

  if (position === "none" || !color) return null

  const positionStyles: Record<string, string> = {
    top: "absolute top-0 left-0 right-0 rounded-t-xl",
    bottom: "absolute bottom-0 left-0 right-0",
    left: "absolute top-0 bottom-0 left-0 rounded-l-xl",
  }

  const dimensionStyle =
    position === "left"
      ? { width, height: "100%" }
      : { height: width, width: "100%" }

  return (
    <div
      className={cn(
        "pointer-events-none transition-all",
        positionStyles[position],
      )}
      style={{ backgroundColor: color, ...dimensionStyle }}
    />
  )
}

// ── Decoration Hint Classes ───────────────────────────────────────────────

function getDecorationClasses(
  hint?: StoryPresentation["decorationHint"],
): string {
  switch (hint) {
    case "brutalist":
      return "font-mono"
    case "ethereal":
      return "font-serif"
    default:
      return ""
  }
}

function getDecorationTitleClasses(
  hint?: StoryPresentation["decorationHint"],
): string {
  switch (hint) {
    case "brutalist":
      return "uppercase tracking-wide text-[13px]"
    case "ethereal":
      return "italic font-normal text-[16px]"
    default:
      return ""
  }
}

// ── Debug Panel ───────────────────────────────────────────────────────────

function DebugPanel({
  story,
  resolved,
}: {
  story: StoryPublic
  resolved: StoryPresentation
}) {
  const tokenCount = Object.keys(resolved.tokens || {}).length
  return (
    <div className="border-t border-dashed border-border px-4 py-2 text-[10px] font-mono text-muted-foreground bg-muted/30">
      <span className="font-bold">src:</span>{" "}
      {story.presentation ? "instance" : "type default"}
      {" · "}
      <span className="font-bold">tokens:</span> {tokenCount}
      {" · "}
      <span className="font-bold">deco:</span>{" "}
      {resolved.decorationHint || "none"}
      {" · "}
      <span className="font-bold">accent:</span>{" "}
      {resolved.tokens?.["--story-accent-position"] || "top"}
    </div>
  )
}

// ── Full Variant ──────────────────────────────────────────────────────────

function StoryCardFull({
  story,
  resolved,
  presentationEnabled,
  href,
  isSelected,
  onClick,
  action,
  className,
  debug,
} : {
  story: StoryPublic
  resolved: StoryPresentation
  presentationEnabled: boolean
  debug:boolean
} & Pick<
  StoryCardProps,
  "href" | "isSelected" | "onClick" | "action" | "className"
>) {
  const decoClasses = presentationEnabled
    ? getDecorationClasses(resolved.decorationHint)
    : "" 
  const titleDecoClasses = presentationEnabled
    ? getDecorationTitleClasses(resolved.decorationHint)
    : ""

  // CSS variable overrides on wrapper div — the core presentation mechanism
  const wrapperStyle = presentationEnabled
    ? presentationToStyle(resolved.tokens)
    : undefined

  // Shadow and radius applied directly on Card element because Tailwind's
  // shadow-sm sets --tw-shadow on the element itself, overriding inherited values.
  const cardInlineStyle: React.CSSProperties = {
    ...(presentationEnabled && resolved.tokens?.["--story-card-radius"]
      ? { borderRadius: resolved.tokens["--story-card-radius"] }
      : {}),
    ...(presentationEnabled && resolved.tokens?.["--story-card-shadow"]
      ? { boxShadow: resolved.tokens["--story-card-shadow"] }
      : {}),
  }

  const avatar = (
    <StoryAvatar
      name={story.title ?? "Story"}
      size="lg"
      presentation={presentationEnabled ? resolved.avatar : undefined}
    />
  )

  const title = (
    <CardTitle className={cn("truncate", titleDecoClasses)}>
      {story.title ?? "Story"}
    </CardTitle>
  )
  return (
    <div
      style={wrapperStyle}
      className={cn("transition-all duration-300", decoClasses)}
    >
      <Card
        className={cn(
          "transition-all relative overflow-hidden",
          onClick && "cursor-pointer hover:shadow-md hover:border-primary/50",
          isSelected && "ring-2 ring-primary",
          className,
        )}
        onClick={onClick}
        style={
          Object.keys(cardInlineStyle).length > 0 ? cardInlineStyle : undefined
        }
      >
        <AccentStrip presentation={resolved} enabled={presentationEnabled} />

        <CardHeader className="pb-3">
          <div className="flex items-start gap-3">
            {href ? (
              <Link
                to={href}
                onClick={(e: { stopPropagation: () => any }) =>
                  e.stopPropagation()
                }
              >
                {avatar}
              </Link>
            ) : (
              avatar
            )}

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                {href ? (
                  <Link
                    to={href}
                    className="hover:underline"
                    onClick={(e: React.MouseEvent<HTMLAnchorElement>) =>
                      e.stopPropagation()
                    }
                  >
                    {title}
                  </Link>
                ) : (
                  title
                )}
                {/* <StoryStatusBadge isPublished={isPublished} /> */}
              </div>

              {/* {story.slug && ( TODO: add back once Story has slug references?
                <CardDescription className="font-mono text-xs">
                  @{story.slug}
                </CardDescription>
              )} */}

              {story.description && (
                <CardDescription
                  className={cn(
                    "mt-1 line-clamp-2",
                    resolved.decorationHint === "ethereal" &&
                      presentationEnabled &&
                      "italic",
                  )}
                >
                  {story.description}
                </CardDescription>
              )}
            </div>

            {action && <div onClick={(e) => e.stopPropagation()}>{action}</div>}
          </div>
        </CardHeader>

        {/* <CardContent className="pt-0">
          <div className="flex flex-wrap gap-2">
            {scope && <StoryPublishedBadge scope={scope} />}
            {participationMode && <StoryModeBadge mode={participationMode} />}
            {scope === "personal" && providerType && (
              <AgentProviderBadge providerType={providerType} />
            )}
            {displayModel && (
              <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
                {displayModel}
              </span>
            )}
          </div>
        </CardContent> */}

        {debug && <DebugPanel story={story} resolved={resolved} />}
      </Card>
    </div>
  )
}


const StoryCard = ({ story }: StoryCardProps) => {
  const navigate = useNavigate()
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)

  const publishMutation = usePublishStory()
  const unpublishMutation = useUnpublishStory()
  const deleteMutation = useDeleteStory()

  // Fetch linked rooms for this story
  const { data: roomsData } = useQuery({
    queryKey: ["rooms", "story", story.id],
    queryFn: () => RoomsService.getRoomsForStory({ storyId: story.id }),
  })

  // Determine story lifecycle state for badge
  const getStatusBadge = () => {
    if (story.is_published && story.published_version !== null) {
      return (
        <Badge variant="default">Published v{story.published_version}</Badge>
      )
    }
    if (!story.is_published && story.published_version !== null) {
      return <Badge variant="secondary">Unpublished</Badge>
    }
    return <Badge variant="outline">Draft v{story.current_version}</Badge>
  }

  // Show editing badge if current version > published version
  const getEditingBadge = () => {
    if (
      story.published_version &&
      story.current_version > story.published_version
    ) {
      return (
        <Badge
          variant="secondary"
          className="bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
        >
          Draft v{story.current_version}
        </Badge>
      )
    }
    return null
  }

  const handleEdit = () => {
    navigate({ to: "/stories/$storyId/edit", params: { storyId: story.id } })
  }

  const handleTogglePublish = () => {
    if (story.is_published) {
      unpublishMutation.mutate(story.id)
    } else {
      publishMutation.mutate(story.id)
    }
  }

  const handleDelete = () => {
    deleteMutation.mutate(story.id)
    setShowDeleteDialog(false)
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInDays = Math.floor(
      (now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24),
    )

    if (diffInDays === 0) return "Today"
    if (diffInDays === 1) return "Yesterday"
    if (diffInDays < 7) return `${diffInDays} days ago`
    if (diffInDays < 30) return `${Math.floor(diffInDays / 7)} weeks ago`
    return date.toLocaleDateString()
  }

  const linkedRooms = roomsData?.data ?? []

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-xl">{story.title}</CardTitle>
          <div className="flex gap-2">
            {getStatusBadge()}
            {getEditingBadge()}
          </div>
        </div>
        <CardDescription className="min-h-[40px]">
          {story.description || "No description"}
        </CardDescription>
      </CardHeader>

      <CardContent className="flex flex-col gap-3">
        {/* Version Info */}
        <div className="text-muted-foreground flex gap-4 text-xs">
          <span>Current: v{story.current_version}</span>
          {story.published_version && (
            <span>Published: v{story.published_version}</span>
          )}
        </div>

        {/* Timestamp */}
        <p className="text-muted-foreground text-xs">
          Updated {formatDate(story.updated_at)}
        </p>

        {/* Linked Rooms */}
        {linkedRooms.length > 0 && (
          <div className="flex flex-col gap-2 pt-2">
            <div className="text-muted-foreground flex items-center gap-1 text-xs">
              <MessageSquare className="h-3 w-3" />
              <span>Linked Rooms:</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {linkedRooms.map((room) => (
                <Link
                  key={room.room_id}
                  to="/r/$roomId"
                  params={{ roomId: room.room_id }}
                >
                  <Badge
                    variant="secondary"
                    className="cursor-pointer hover:opacity-80"
                  >
                    {room.title || "Untitled Room"}
                  </Badge>
                </Link>
              ))}
            </div>
          </div>
        )}
      </CardContent>

      <CardFooter className="flex-wrap gap-2">
        {/* Edit Button */}
        <Button size="sm" onClick={handleEdit}>
          <Edit className="mr-1 h-4 w-4" />
          Edit
        </Button>

        {/* Create Room Button - only for published stories */}
        {story.is_published && (
          <AddRoom
            defaultStoryId={story.id}
            trigger={
              <Button size="sm" variant="outline">
                <Plus className="mr-1 h-4 w-4" />
                Room
              </Button>
            }
          />
        )}

        {/* Publish/Unpublish Button */}
        <Button
          size="sm"
          variant="outline"
          onClick={handleTogglePublish}
          disabled={publishMutation.isPending || unpublishMutation.isPending}
        >
          {publishMutation.isPending || unpublishMutation.isPending
            ? "..."
            : story.is_published
              ? "Unpublish"
              : "Publish"}
        </Button>

        {/* Delete Button with Confirmation Dialog */}
        <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
          <DialogTrigger asChild>
            <Button
              size="sm"
              variant="ghost"
              className="text-destructive hover:text-destructive"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Delete Story</DialogTitle>
              <DialogDescription>
                Are you sure you want to delete "{story.title}"? This action
                cannot be undone.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <DialogClose asChild>
                <Button variant="outline">Cancel</Button>
              </DialogClose>
              <Button
                variant="destructive"
                onClick={handleDelete}
                disabled={deleteMutation.isPending}
              >
                {deleteMutation.isPending ? "Deleting..." : "Delete"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </CardFooter>
    </Card>
  )
}

export default StoryCard
