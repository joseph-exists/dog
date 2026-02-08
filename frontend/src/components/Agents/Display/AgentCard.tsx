/**
 * AgentCard Component
 *
 * The single card implementation for displaying agents. Supports presentation-as-data
 * styling via CSS variable scoping on a wrapper div. When an agent carries presentation
 * data (or has a typed default), the card renders with that visual identity.
 * When it doesn't, the card renders with standard shadcn defaults.
 *
 * Supports three variants: full, compact, mini.
 *
 * See Presentation/REFERENCE.md for the complete architectural guide.
 */

import { Link } from "@tanstack/react-router"

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { cn } from "@/lib/utils"

import AgentAvatar from "./AgentAvatar"
import {
  AgentModeBadge,
  AgentProviderBadge,
  AgentScopeBadge,
  AgentStatusBadge,
} from "./AgentBadge"

import { useProviderTypeName } from "../hooks"

import type {
  AgentPresentation,
//  AgentTypeKey,
  UserAgentConfigData,
} from "../types"
import { isAgentScope, isAgentTypeKey, isParticipationMode } from "../types"
import { presentationToStyle, resolveAgentPresentation } from "../resolve"

// ── Props ─────────────────────────────────────────────────────────────────

interface AgentCardProps {
  agent: UserAgentConfigData
  variant?: "full" | "compact" | "mini"
  /** Override presentation behavior. Defaults to true when agent has presentation or agent_type. */
  presentationEnabled?: boolean
  href?: string
  isSelected?: boolean
  onClick?: () => void
  action?: React.ReactNode
  className?: string
  /** Show debug info about resolved presentation */
  debug?: boolean
}

// ── Accent Strip ──────────────────────────────────────────────────────────

function AccentStrip({
  presentation,
  enabled,
}: {
  presentation: AgentPresentation
  enabled: boolean
}) {
  if (!enabled) return null

  const position = presentation.tokens?.["--agent-accent-position"] ?? "top"
  const width = presentation.tokens?.["--agent-accent-width"] ?? "3px"
  const color = presentation.tokens?.["--agent-accent"]

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
      className={cn("pointer-events-none transition-all", positionStyles[position])}
      style={{ backgroundColor: color, ...dimensionStyle }}
    />
  )
}

// ── Decoration Hint Classes ───────────────────────────────────────────────

function getDecorationClasses(hint?: AgentPresentation["decorationHint"]): string {
  switch (hint) {
    case "brutalist":
      return "font-mono"
    case "ethereal":
      return "font-serif"
    default:
      return ""
  }
}

function getDecorationTitleClasses(hint?: AgentPresentation["decorationHint"]): string {
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
  agent,
  resolved,
}: {
  agent: UserAgentConfigData
  resolved: AgentPresentation
}) {
  const tokenCount = Object.keys(resolved.tokens || {}).length
  return (
    <div className="border-t border-dashed border-border px-4 py-2 text-[10px] font-mono text-muted-foreground bg-muted/30">
      <span className="font-bold">src:</span>{" "}
      {agent.presentation ? "instance" : "type default"}
      {" · "}
      <span className="font-bold">tokens:</span> {tokenCount}
      {" · "}
      <span className="font-bold">deco:</span> {resolved.decorationHint || "none"}
      {" · "}
      <span className="font-bold">accent:</span>{" "}
      {resolved.tokens?.["--agent-accent-position"] || "top"}
    </div>
  )
}

// ── Full Variant ──────────────────────────────────────────────────────────

function AgentCardFull({
  agent,
  resolved,
  presentationEnabled,
  href,
  isSelected,
  onClick,
  action,
  className,
  debug,
}: {
  agent: UserAgentConfigData
  resolved: AgentPresentation
  presentationEnabled: boolean
  debug: boolean
} & Pick<AgentCardProps, "href" | "isSelected" | "onClick" | "action" | "className">) {
  
  const providerTypeQuery = useProviderTypeName(agent.model_name)
  const providerType = providerTypeQuery.data

  const displayModel = agent.model_name


  const scope = isAgentScope(agent.scope) ? agent.scope : undefined
  const participationMode = isParticipationMode(agent.participation_mode)
    ? agent.participation_mode
    : undefined
  const isEnabled = agent.is_enabled ?? true

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
    ...(presentationEnabled && resolved.tokens?.["--agent-card-radius"]
      ? { borderRadius: resolved.tokens["--agent-card-radius"] }
      : {}),
    ...(presentationEnabled && resolved.tokens?.["--agent-card-shadow"]
      ? { boxShadow: resolved.tokens["--agent-card-shadow"] }
      : {}),
  }

  const avatar = (
    <AgentAvatar
      name={agent.name ?? "Agent"}
      size="lg"
      presentation={presentationEnabled ? resolved.avatar : undefined}
    />
  )

  const title = (
    <CardTitle className={cn("truncate", titleDecoClasses)}>
      {agent.name ?? "Agent"}
    </CardTitle>
  )

  return (
    <div style={wrapperStyle} className={cn("transition-all duration-300", decoClasses)}>
      <Card
        className={cn(
          "transition-all relative overflow-hidden",
          onClick && "cursor-pointer hover:shadow-md hover:border-primary/50",
          isSelected && "ring-2 ring-primary",
          !isEnabled && "opacity-60",
          className,
        )}
        onClick={onClick}
        style={Object.keys(cardInlineStyle).length > 0 ? cardInlineStyle : undefined}
      >
        <AccentStrip presentation={resolved} enabled={presentationEnabled} />

        <CardHeader className="pb-3">
          <div className="flex items-start gap-3">
            {href ? (
              <Link to={href} onClick={(e) => e.stopPropagation()}>
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
                    onClick={(e) => e.stopPropagation()}
                  >
                    {title}
                  </Link>
                ) : (
                  title
                )}
                <AgentStatusBadge isEnabled={isEnabled} />
              </div>

              {agent.slug && (
                <CardDescription className="font-mono text-xs">
                  @{agent.slug}
                </CardDescription>
              )}

              {agent.description && (
                <CardDescription
                  className={cn(
                    "mt-1 line-clamp-2",
                    resolved.decorationHint === "ethereal" && presentationEnabled && "italic",
                  )}
                >
                  {agent.description}
                </CardDescription>
              )}
            </div>

            {action && (
              <div onClick={(e) => e.stopPropagation()}>{action}</div>
            )}
          </div>
        </CardHeader>

        <CardContent className="pt-0">
          <div className="flex flex-wrap gap-2">
            {scope && <AgentScopeBadge scope={scope} />}
            {participationMode && (
              <AgentModeBadge mode={participationMode} />
            )}
            {scope === "personal" && providerType && (
              <AgentProviderBadge providerType={providerType} />
            )}
            {displayModel && (
              <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
                {displayModel}
              </span>
            )}
          </div>
        </CardContent>

        {debug && <DebugPanel agent={agent} resolved={resolved} />}
      </Card>
    </div>
  )
}

// ── Compact Variant ───────────────────────────────────────────────────────

function AgentCardCompact({
  agent,
  resolved,
  presentationEnabled,
  isSelected,
  onClick,
  action,
  className,
}: {
  agent: UserAgentConfigData
  resolved: AgentPresentation
  presentationEnabled: boolean
} & Pick<AgentCardProps, "isSelected" | "onClick" | "action" | "className">) {
  const providerTypeQuery = useProviderTypeName(agent.model_name)
  const providerType = providerTypeQuery.data
  const scope = isAgentScope(agent.scope) ? agent.scope : undefined
  const participationMode = isParticipationMode(agent.participation_mode)
    ? agent.participation_mode
    : undefined
  const isEnabled = agent.is_enabled ?? true

  const wrapperStyle = presentationEnabled
    ? presentationToStyle(resolved.tokens)
    : undefined

  const accentColor = presentationEnabled
    ? resolved.tokens?.["--agent-accent"]
    : undefined

  const decoClasses = presentationEnabled
    ? getDecorationClasses(resolved.decorationHint)
    : ""
  const titleDecoClasses = presentationEnabled
    ? getDecorationTitleClasses(resolved.decorationHint)
    : ""

  return (
    <div style={wrapperStyle} className={cn("transition-all duration-300", decoClasses)}>
      <div
        className={cn(
          "flex items-center gap-3 p-3 rounded-lg border bg-card text-card-foreground transition-colors",
          onClick && "cursor-pointer hover:bg-accent/50",
          isSelected && "ring-2 ring-primary",
          !isEnabled && "opacity-60",
          className,
        )}
        style={
          accentColor
            ? { borderLeftWidth: 3, borderLeftColor: accentColor }
            : undefined
        }
        onClick={onClick}
      >
        <AgentAvatar
          name={agent.name ?? "Agent"}
          size="md"
          presentation={presentationEnabled ? resolved.avatar : undefined}
        />

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className={cn("font-medium truncate", titleDecoClasses)}>
              {agent.name ?? "Agent"}
            </span>
            {scope && (
              <AgentScopeBadge scope={scope} className="scale-90" />
            )}
            {scope === "personal" && providerType && (
              <AgentProviderBadge providerType={providerType} className="scale-90" />
            )}
          </div>
          {agent.description && (
            <p className="text-sm text-muted-foreground truncate">
              {agent.description}
            </p>
          )}
        </div>

        {participationMode && (
          <AgentModeBadge mode={participationMode} className="hidden sm:flex" />
        )}

        {action && (
          <div onClick={(e) => e.stopPropagation()}>{action}</div>
        )}
      </div>
    </div>
  )
}

// ── Mini Variant ──────────────────────────────────────────────────────────

function AgentCardMini({
  agent,
  resolved,
  presentationEnabled,
  isSelected,
  onClick,
  className,
}: {
  agent: UserAgentConfigData
  resolved: AgentPresentation
  presentationEnabled: boolean
} & Pick<AgentCardProps, "isSelected" | "onClick" | "className">) {
  const accentColor = presentationEnabled
    ? resolved.tokens?.["--agent-accent"]
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
      <AgentAvatar
        name={agent.name ?? "Agent"}
        size="sm"
        presentation={presentationEnabled ? resolved.avatar : undefined}
      />
      <span className="text-sm font-medium truncate text-card-foreground">
        {agent.name ?? "Agent"}
      </span>
    </div>
  )
}

// ── Main Component ────────────────────────────────────────────────────────

export default function AgentCard({
  agent,
  variant = "full",
  presentationEnabled,
  href,
  isSelected,
  onClick,
  action,
  className,
  debug = false,
}: AgentCardProps) {
  // Default: presentation is enabled when the agent has presentation data or a typed default
  const agentType = isAgentTypeKey(agent.agent_type) ? agent.agent_type : undefined
  const enabled = presentationEnabled ?? !!(agent.presentation || agentType)

  const resolved = resolveAgentPresentation(
    agentType,
    enabled ? agent.presentation : null,
  )

  const shared = {
    agent,
    resolved,
    presentationEnabled: enabled,
    isSelected,
    onClick,
    action,
    className,
  }

  switch (variant) {
    case "mini":
      return <AgentCardMini {...shared} />
    case "compact":
      return <AgentCardCompact {...shared} />
    default:
      return <AgentCardFull {...shared} href={href} debug={debug} />
  }
}

// Export variants for direct use if needed
export { AgentCardFull, AgentCardCompact, AgentCardMini }
