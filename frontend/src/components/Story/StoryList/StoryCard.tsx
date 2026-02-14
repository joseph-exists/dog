/**
 * StoryCard - Individual story display card
 *
 * Features:
 * - Three variants: full, compact, mini
 * - Presentation theming system (tokens, accent strips, decoration hints)
 * - Status badge: Published (primary), Unpublished (secondary), Draft (outline)
 * - Editing badge when current_version > published_version
 * - Optional action buttons: Edit, Publish/Unpublish, Delete
 * - Linked rooms display with navigation
 * - Relative timestamp formatting
 */

import { useQuery } from "@tanstack/react-query"
import { Link, useNavigate } from "@tanstack/react-router"
import { Edit, MessageSquare, Plus, Trash2 } from "lucide-react"
import React, { useState } from "react"

import { RoomsService, type StoryPublic } from "@/client"
import AddRoom from "@/components/Room/Dialogs/AddRoom"
import {
  presentationToStyle,
  resolveStoryPresentation,
  STORY_TYPE_PRESENTATIONS,
} from "@/components/Common/Themes/resolve"
import type { StoryPresentation } from "@/components/Common/Themes/types"
import { isStoryTypeKey } from "@/components/Common/Themes/types"
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
import { cn } from "@/lib/utils"
import StoryAvatar from "../Display/StoryAvatar"

// ============================================================================
// Types
// ============================================================================

interface StoryCardProps {
  story: StoryPublic
  variant?: "full" | "compact" | "mini"
  href?: string
  presentationEnabled?: boolean
  isSelected?: boolean
  onClick?: () => void
  /** Custom action slot (used when showActions is false) */
  action?: React.ReactNode
  /** Show standard CRUD actions (Edit, Publish, Delete) */
  showActions?: boolean
  /** Show linked rooms section */
  showLinkedRooms?: boolean
  /** Show version info */
  showVersionInfo?: boolean
  className?: string
  debug?: boolean
}

// ============================================================================
// Helper Functions
// ============================================================================

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffInDays = Math.floor(
    (now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24)
  )

  if (diffInDays === 0) return "Today"
  if (diffInDays === 1) return "Yesterday"
  if (diffInDays < 7) return `${diffInDays} days ago`
  if (diffInDays < 30) return `${Math.floor(diffInDays / 7)} weeks ago`
  return date.toLocaleDateString()
}

// ============================================================================
// Sub-components
// ============================================================================

// ── Status Badges ─────────────────────────────────────────────────────────

function StoryStatusBadge({ story }: { story: StoryPublic }) {
  if (story.is_published && story.published_version !== null) {
    return <Badge variant="default">Published v{story.published_version}</Badge>
  }
  if (!story.is_published && story.published_version !== null) {
    return <Badge variant="secondary">Unpublished</Badge>
  }
  return <Badge variant="outline">Draft v{story.current_version}</Badge>
}

function StoryEditingBadge({ story }: { story: StoryPublic }) {
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
        positionStyles[position]
      )}
      style={{ backgroundColor: color, ...dimensionStyle }}
    />
  )
}

// ── Decoration Hint Classes ───────────────────────────────────────────────

function getDecorationClasses(
  hint?: StoryPresentation["decorationHint"]
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
  hint?: StoryPresentation["decorationHint"]
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

// ── Linked Rooms ──────────────────────────────────────────────────────────

function LinkedRoomsSection({ storyId }: { storyId: string }) {
  const { data: roomsData } = useQuery({
    queryKey: ["rooms", "story", storyId],
    queryFn: () => RoomsService.getRoomsForStory({ storyId }),
  })

  const linkedRooms = roomsData?.data ?? []

  if (linkedRooms.length === 0) return null

  return (
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
            onClick={(e: React.MouseEvent) => e.stopPropagation()}
          >
            <Badge variant="secondary" className="cursor-pointer hover:opacity-80">
              {room.title || "Untitled Room"}
            </Badge>
          </Link>
        ))}
      </div>
    </div>
  )
}

// ── Action Buttons ────────────────────────────────────────────────────────

function StoryActions({ story }: { story: StoryPublic }) {
  const navigate = useNavigate()
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)

  const publishMutation = usePublishStory()
  const unpublishMutation = useUnpublishStory()
  const deleteMutation = useDeleteStory()

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation()
    navigate({ to: "/stories/$storyId/edit", params: { storyId: story.id } })
  }

  const handleTogglePublish = (e: React.MouseEvent) => {
    e.stopPropagation()
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

  return (
    <div className="flex flex-wrap gap-2" onClick={(e) => e.stopPropagation()}>
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
    </div>
  )
}

// ============================================================================
// Variant Components
// ============================================================================

// ── Full Variant ──────────────────────────────────────────────────────────

function StoryCardFull({
  story,
  resolved,
  presentationEnabled,
  href,
  isSelected,
  onClick,
  action,
  showActions,
  showLinkedRooms,
  showVersionInfo,
  className,
  debug,
}: {
  story: StoryPublic
  resolved: StoryPresentation
  presentationEnabled: boolean
  debug: boolean
  showActions: boolean
  showLinkedRooms: boolean
  showVersionInfo: boolean
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

  const wrapperStyle = presentationEnabled
    ? presentationToStyle(resolved.tokens)
    : undefined

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
          className
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
                onClick={(e: { stopPropagation: () => void }) =>
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
                <StoryStatusBadge story={story} />
                <StoryEditingBadge story={story} />
              </div>

              {story.description && (
                <CardDescription
                  className={cn(
                    "mt-1 line-clamp-2",
                    resolved.decorationHint === "ethereal" &&
                      presentationEnabled &&
                      "italic"
                  )}
                >
                  {story.description}
                </CardDescription>
              )}
            </div>

            {action && !showActions && (
              <div onClick={(e) => e.stopPropagation()}>{action}</div>
            )}
          </div>
        </CardHeader>

        {(showVersionInfo || showLinkedRooms) && (
          <CardContent className="pt-0 flex flex-col gap-3">
            {/* Version Info */}
            {showVersionInfo && (
              <>
                <div className="text-muted-foreground flex gap-4 text-xs">
                  <span>Current: v{story.current_version}</span>
                  {story.published_version && (
                    <span>Published: v{story.published_version}</span>
                  )}
                </div>
                <p className="text-muted-foreground text-xs">
                  Updated {formatDate(story.updated_at)}
                </p>
              </>
            )}

            {/* Linked Rooms */}
            {showLinkedRooms && <LinkedRoomsSection storyId={story.id} />}
          </CardContent>
        )}

        {showActions && (
          <CardFooter>
            <StoryActions story={story} />
          </CardFooter>
        )}

        {debug && <DebugPanel story={story} resolved={resolved} />}
      </Card>
    </div>
  )
}

// ── Compact Variant ───────────────────────────────────────────────────────

function StoryCardCompact({
  story,
  resolved,
  presentationEnabled,
  isSelected,
  onClick,
  action,
  showActions,
  className,
}: {
  story: StoryPublic
  resolved: StoryPresentation
  presentationEnabled: boolean
  showActions: boolean
} & Pick<StoryCardProps, "isSelected" | "onClick" | "action" | "className">) {
  const wrapperStyle = presentationEnabled
    ? presentationToStyle(resolved.tokens)
    : undefined

  const accentColor = presentationEnabled
    ? resolved.tokens?.["--story-accent"]
    : undefined

  const decoClasses = presentationEnabled
    ? getDecorationClasses(resolved.decorationHint)
    : ""
  const titleDecoClasses = presentationEnabled
    ? getDecorationTitleClasses(resolved.decorationHint)
    : ""

  return (
    <div
      style={wrapperStyle}
      className={cn("transition-all duration-300", decoClasses)}
    >
      <div
        className={cn(
          "flex items-center gap-3 p-3 rounded-lg border bg-card text-card-foreground transition-colors",
          onClick && "cursor-pointer hover:bg-accent/50",
          isSelected && "ring-2 ring-primary",
          className
        )}
        style={
          accentColor
            ? { borderLeftWidth: 3, borderLeftColor: accentColor }
            : undefined
        }
        onClick={onClick}
      >
        <StoryAvatar
          name={story.title ?? "Story"}
          size="md"
          presentation={presentationEnabled ? resolved.avatar : undefined}
        />

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className={cn("font-medium truncate", titleDecoClasses)}>
              {story.title ?? "Story"}
            </span>
            <StoryStatusBadge story={story} />
          </div>
          {story.description && (
            <p className="text-sm text-muted-foreground truncate">
              {story.description}
            </p>
          )}
        </div>

        {action && !showActions && (
          <div onClick={(e) => e.stopPropagation()}>{action}</div>
        )}
        {showActions && (
          <div onClick={(e) => e.stopPropagation()}>
            <StoryActions story={story} />
          </div>
        )}
      </div>
    </div>
  )
}

// ── Mini Variant ──────────────────────────────────────────────────────────

function StoryCardMini({
  story,
  resolved,
  presentationEnabled,
  isSelected,
  onClick,
  className,
}: {
  story: StoryPublic
  resolved: StoryPresentation
  presentationEnabled: boolean
} & Pick<StoryCardProps, "isSelected" | "onClick" | "className">) {
  const accentColor = presentationEnabled
    ? resolved.tokens?.["--story-accent"]
    : undefined

  return (
    <div
      className={cn(
        "flex items-center gap-2 p-2 rounded-md transition-colors",
        onClick && "cursor-pointer hover:bg-accent",
        isSelected && "bg-accent",
        className
      )}
      style={
        isSelected && accentColor
          ? {
              backgroundColor: `color-mix(in oklch, ${accentColor} 10%, transparent)`,
              outline: `1.5px solid color-mix(in oklch, ${accentColor} 30%, transparent)`,
              outlineOffset: "-1.5px",
            }
          : undefined
      }
      onClick={onClick}
    >
      <StoryAvatar
        name={story.title ?? "Story"}
        size="sm"
        presentation={presentationEnabled ? resolved.avatar : undefined}
      />
      <span className="text-sm font-medium truncate text-card-foreground">
        {story.title ?? "Story"}
      </span>
    </div>
  )
}

// ============================================================================
// Main Component
// ============================================================================

export default function StoryCard({
  story,
  variant = "full",
  presentationEnabled,
  href,
  isSelected,
  onClick,
  action,
  showActions = false,
  showLinkedRooms = false,
  showVersionInfo = false,
  className,
  debug = false,
}: StoryCardProps) {
  // Default: presentation is enabled when the story has presentation data or a typed default
  const storyType = isStoryTypeKey(story.story_type)
    ? story.story_type
    : undefined
  const enabled = presentationEnabled ?? !!(story.presentation || storyType)

  const typeDefaults = storyType
    ? STORY_TYPE_PRESENTATIONS[storyType]
    : undefined
  const resolved = resolveStoryPresentation(
    typeDefaults,
    enabled ? story.presentation : null
  )

  const shared = {
    story,
    resolved,
    presentationEnabled: enabled,
    isSelected,
    onClick,
    action,
    showActions,
    className,
  }

  switch (variant) {
    case "mini":
      return <StoryCardMini {...shared} />
    case "compact":
      return <StoryCardCompact {...shared} />
    default:
      return (
        <StoryCardFull
          {...shared}
          href={href}
          debug={debug}
          showLinkedRooms={showLinkedRooms}
          showVersionInfo={showVersionInfo}
        />
      )
  }
}

export { StoryCardFull, StoryCardCompact, StoryCardMini }
