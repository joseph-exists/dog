/**
 * PresentableAgentCard
 *
 * A presentation-aware agent card that uses the REAL shadcn Card, Badge,
 * and other production components — but wraps them in a CSS variable
 * scoping container that applies the agent's visual identity.
 *
 * The key mechanism: setting CSS custom properties on a wrapper div.
 * Since shadcn's Card uses `bg-card` (→ var(--card)), `text-card-foreground`
 * (→ var(--card-foreground)), and `border` (→ var(--border)), overriding
 * those variables on an ancestor div causes all descendant components
 * to inherit the new values. No component rebuilds needed.
 *
 * Supports all three variants: full, compact, mini.
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

// import type { AgentScope, ParticipationMode } from "../Display/AgentBadge"
import {
  AgentModeBadge,
  AgentProviderBadge,
  AgentScopeBadge,
  AgentStatusBadge,
  parseProviderFromModelName,
} from "../Display/AgentBadge"

import PresentableAgentAvatar from "./PresentableAgentAvatar"
import type { AgentPresentation, AgentWithPresentation } from "./types"
// ^ AgentTypeKey
import {
  presentationToStyle,
  resolveAgentPresentation,
} from "./resolve"

interface PresentableAgentCardProps {
  agent: AgentWithPresentation
  variant?: "full" | "compact" | "mini"
  /** Whether to apply presentation-as-data styling */
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
    top: `absolute top-0 left-0 right-0 rounded-t-xl`,
    bottom: `absolute bottom-0 left-0 right-0`,
    left: `absolute top-0 bottom-0 left-0 rounded-l-xl`,
  }

  const dimensionStyle =
    position === "left"
      ? { width, height: "100%" }
      : { height: width, width: "100%" }

  return (
    <div
      className={cn("pointer-events-none transition-all", positionStyles[position])}
      style={{
        backgroundColor: color,
        ...dimensionStyle,
      }}
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

function DebugPanel({ agent, resolved }: { agent: AgentWithPresentation; resolved: AgentPresentation }) {
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

function PresentableCardFull({
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
  agent: AgentWithPresentation
  resolved: AgentPresentation
  presentationEnabled: boolean
} & Pick<
  PresentableAgentCardProps,
  "href" | "isSelected" | "onClick" | "action" | "className" | "debug"
>) {
  const providerType = parseProviderFromModelName(agent.modelName)
  const displayModel = agent.modelName
    ?.split(":")
    .pop()
    ?.replace(/-/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase())

  const decoClasses = presentationEnabled
    ? getDecorationClasses(resolved.decorationHint)
    : ""
  const titleDecoClasses = presentationEnabled
    ? getDecorationTitleClasses(resolved.decorationHint)
    : ""

  // CSS variable overrides — the core mechanism
  // Shadow and radius are applied directly on the Card element (not here)
  // because Tailwind's shadow-sm sets --tw-shadow on the Card itself,
  // overriding any inherited value from this wrapper.
  const wrapperStyle = presentationEnabled
    ? presentationToStyle(resolved.tokens)
    : undefined

  // Direct inline styles for the Card element — these beat Tailwind classes
  const cardInlineStyle: React.CSSProperties = {
    ...(presentationEnabled && resolved.tokens?.["--agent-card-radius"]
      ? { borderRadius: resolved.tokens["--agent-card-radius"] }
      : {}),
    ...(presentationEnabled && resolved.tokens?.["--agent-card-shadow"]
      ? { boxShadow: resolved.tokens["--agent-card-shadow"] }
      : {}),
  }

  const avatar = (
    <PresentableAgentAvatar
      name={agent.name}
      size="lg"
      presentation={presentationEnabled ? resolved.avatar : undefined}
    />
  )

  const title = (
    <CardTitle className={cn("truncate", titleDecoClasses)}>
      {agent.name}
    </CardTitle>
  )

  return (
    <div style={wrapperStyle} className={cn("transition-all duration-300", decoClasses)}>
      <Card
        className={cn(
          "transition-all relative overflow-hidden",
          onClick && "cursor-pointer hover:shadow-md hover:border-primary/50",
          isSelected && "ring-2 ring-primary",
          !agent.isEnabled && "opacity-60",
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
                <AgentStatusBadge isEnabled={agent.isEnabled ?? true} />
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
            {agent.scope && <AgentScopeBadge scope={agent.scope} />}
            {agent.participationMode && (
              <AgentModeBadge mode={agent.participationMode} />
            )}
            {agent.scope === "personal" && providerType && (
              <AgentProviderBadge providerType={providerType} />
            )}
            {displayModel && (
              <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
                {displayModel}
              </span>
            )}
            {agent.creator && agent.creator !== "System" && (
              <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded italic">
                by {agent.creator}
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

function PresentableCardCompact({
  agent,
  resolved,
  presentationEnabled,
  isSelected,
  onClick,
  action,
  className,
}: {
  agent: AgentWithPresentation
  resolved: AgentPresentation
  presentationEnabled: boolean
} & Pick<PresentableAgentCardProps, "isSelected" | "onClick" | "action" | "className">) {
  const providerType = parseProviderFromModelName(agent.modelName)
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
          !agent.isEnabled && "opacity-60",
          className,
        )}
        style={
          accentColor
            ? { borderLeftWidth: 3, borderLeftColor: accentColor }
            : undefined
        }
        onClick={onClick}
      >
        <PresentableAgentAvatar
          name={agent.name}
          size="md"
          presentation={presentationEnabled ? resolved.avatar : undefined}
        />

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className={cn("font-medium truncate", titleDecoClasses)}>
              {agent.name}
            </span>
            {agent.scope && (
              <AgentScopeBadge scope={agent.scope} className="scale-90" />
            )}
            {agent.scope === "personal" && providerType && (
              <AgentProviderBadge
                providerType={providerType}
                className="scale-90"
              />
            )}
          </div>
          {agent.description && (
            <p className="text-sm text-muted-foreground truncate">
              {agent.description}
            </p>
          )}
        </div>

        {agent.participationMode && (
          <AgentModeBadge
            mode={agent.participationMode}
            className="hidden sm:flex"
          />
        )}

        {action && (
          <div onClick={(e) => e.stopPropagation()}>{action}</div>
        )}
      </div>
    </div>
  )
}

// ── Mini Variant ──────────────────────────────────────────────────────────

function PresentableCardMini({
  agent,
  resolved,
  presentationEnabled,
  isSelected,
  onClick,
  className,
}: {
  agent: AgentWithPresentation
  resolved: AgentPresentation
  presentationEnabled: boolean
} & Pick<PresentableAgentCardProps, "isSelected" | "onClick" | "className">) {
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
      <PresentableAgentAvatar
        name={agent.name}
        size="sm"
        presentation={presentationEnabled ? resolved.avatar : undefined}
      />
      <span className="text-sm font-medium truncate text-card-foreground">{agent.name}</span>
    </div>
  )
}

// ── Main Component ────────────────────────────────────────────────────────

export default function PresentableAgentCard({
  agent,
  variant = "full",
  presentationEnabled = true,
  href,
  isSelected,
  onClick,
  action,
  className,
  debug = false,
}: PresentableAgentCardProps) {
  const resolved = resolveAgentPresentation(
    agent.agentType,
    presentationEnabled ? agent.presentation : null,
  )

  const shared = {
    agent,
    resolved,
    presentationEnabled,
    isSelected,
    onClick,
    action,
    className,
  }

  switch (variant) {
    case "mini":
      return <PresentableCardMini {...shared} />
    case "compact":
      return <PresentableCardCompact {...shared} />
    default:
      return <PresentableCardFull {...shared} href={href} debug={debug} />
  }
}
