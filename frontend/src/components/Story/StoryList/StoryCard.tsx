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

import { Link } from "@tanstack/react-router"
import React from "react"
import { cn } from "@/lib/utils"
// , resolveStoryPresentation ??
import { presentationToStyle, resolveStoryPresentation, STORY_TYPE_PRESENTATIONS } from "@/components/Common/Themes/resolve"
import type { StoryPresentation } from "@/components/Common/Themes/types"
import { isStoryTypeKey } from "@/components/Common/Themes/types"
import type { StoryPublic } from "@/client"
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
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


// ── Compact Variant ───────────────────────────────────────────────────────

function StoryCardCompact({
  story,
  resolved,
  presentationEnabled,
  isSelected,
  onClick,
  action,
  className,
}: {
  story: StoryPublic
  resolved: StoryPresentation
  presentationEnabled: boolean
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
          className,
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
            {/* {scope && <AgentScopeBadge scope={scope} className="scale-90" />}
            {scope === "personal" && providerType && (
              <AgentProviderBadge
                providerType={providerType}
                className="scale-90"
              /> 
            )}*/}
          </div>
          {story.description && (
            <p className="text-sm text-muted-foreground truncate">
              {story.description}
            </p>
          )}
        </div>

        {action && <div onClick={(e) => e.stopPropagation()}>{action}</div>}
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
        className,
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

export default function StoryCard({
  story,
  variant = "full",
  presentationEnabled,
  href,
  isSelected,
  onClick,
  action,
  className,
  debug = false,
}: StoryCardProps) {
  // Default: presentation is enabled when the agent has presentation data or a typed default
  const storyType = isStoryTypeKey(story.story_type)
    ? story.story_type
    : undefined
  const enabled = presentationEnabled ?? !!(story.presentation || storyType)

  const typeDefaults = storyType ? STORY_TYPE_PRESENTATIONS[storyType] : undefined
  const resolved = resolveStoryPresentation(
    typeDefaults,
    enabled ? story.presentation : null,
  )

  const shared = {
    story,
    resolved,
    presentationEnabled: enabled,
    isSelected,
    onClick,
    action,
    className,
  }
  switch (variant) {
    case "mini":
      return <StoryCardMini {...shared}/>
    case "compact":
      return <StoryCardCompact {...shared}/>
    default:
      return <StoryCardFull {...shared} href={href} debug={debug} />
  }
}

export { StoryCardFull, StoryCardCompact, StoryCardMini }
