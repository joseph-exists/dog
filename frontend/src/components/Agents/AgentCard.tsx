/**
 * AgentCard Component
 *
 * A versatile card for displaying agent information.
 * Supports multiple variants:
 * - "full": Complete card with all details (for agent lists, management)
 * - "compact": Smaller inline display (for room sidebars, selection)
 * - "mini": Minimal display with just avatar and name (for tight spaces)
 *
 * Full feature set (from agents page usage):
 * - slug: Display @slug under name
 * - href: Link avatar/name to detail page
 * - description, scope/mode/provider/model badges
 * - action slot: Edit/Delete buttons, view dialog, etc.
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
import type { AgentScope, ParticipationMode } from "./AgentBadge"
import {
  AgentModeBadge,
  AgentProviderBadge,
  AgentScopeBadge,
  AgentStatusBadge,
  parseProviderFromModelName,
} from "./AgentBadge"

interface AgentCardProps {
  /** Agent unique identifier */
  id: string
  /** Display name */
  name: string
  /** Agent slug (displays as @slug under name) */
  slug?: string
  /** Link destination for avatar/name (enables client-side navigation) */
  href?: string
  /** Short description */
  description?: string | null
  /** Agent scope */
  scope?: AgentScope
  /** Participation mode */
  participationMode?: ParticipationMode
  /** Whether agent is enabled */
  isEnabled?: boolean
  /** Model being used (e.g., "openai:gpt-4o-mini") */
  modelName?: string
  /** Card variant */
  variant?: "full" | "compact" | "mini"
  /** Whether this agent is currently selected/active */
  isSelected?: boolean
  /** Click handler */
  onClick?: () => void
  /** Optional action slot (buttons, toggles, etc.) */
  action?: React.ReactNode
  /** Additional classes */
  className?: string
}

/**
 * Mini variant: Just avatar and name in a row
 */
function AgentCardMini({
  name,
  scope,
  modelName,
  isSelected,
  onClick,
  className,
}: Pick<
  AgentCardProps,
  "name" | "scope" | "modelName" | "isSelected" | "onClick" | "className"
>) {
  const providerType = parseProviderFromModelName(modelName)

  return (
    <div
      className={cn(
        "flex items-center gap-2 p-2 rounded-md transition-colors",
        onClick && "cursor-pointer hover:bg-accent",
        isSelected && "bg-accent",
        className,
      )}
      onClick={onClick}
    >
      <AgentAvatar name={name} size="sm" />
      <span className="text-sm font-medium truncate">{name}</span>
      {scope === "personal" && providerType && (
        <AgentProviderBadge providerType={providerType} className="scale-75" />
      )}
    </div>
  )
}

/**
 * Compact variant: Avatar, name, description in a horizontal layout
 */
function AgentCardCompact({
  name,
  description,
  scope,
  participationMode,
  isEnabled = true,
  modelName,
  isSelected,
  onClick,
  action,
  className,
}: Omit<AgentCardProps, "variant" | "id">) {
  const providerType = parseProviderFromModelName(modelName)
  return (
    <div
      className={cn(
        "flex items-center gap-3 p-3 rounded-lg border bg-card transition-colors",
        onClick && "cursor-pointer hover:bg-accent/50",
        isSelected && "ring-2 ring-primary",
        !isEnabled && "opacity-60",
        className,
      )}
      onClick={onClick}
    >
      <AgentAvatar name={name} size="md" />

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium truncate">{name}</span>
          {scope && <AgentScopeBadge scope={scope} className="scale-90" />}
          {scope === "personal" && providerType && (
            <AgentProviderBadge
              providerType={providerType}
              className="scale-90"
            />
          )}
        </div>
        {description && (
          <p className="text-sm text-muted-foreground truncate">
            {description}
          </p>
        )}
      </div>

      {participationMode && (
        <AgentModeBadge mode={participationMode} className="hidden sm:flex" />
      )}

      {action && <div onClick={(e) => e.stopPropagation()}>{action}</div>}
    </div>
  )
}

/**
 * Full variant: Complete card with all details
 */
function AgentCardFull({
  name,
  slug,
  href,
  description,
  scope,
  participationMode,
  isEnabled = true,
  modelName,
  isSelected,
  onClick,
  action,
  className,
}: Omit<AgentCardProps, "variant" | "id">) {
  // Extract provider type and model display name from "provider:model" format
  const providerType = parseProviderFromModelName(modelName)
 
  // TODO PRI A: as soon as we touch this file again, this needs to be refactored.
  // this is awfully unnecessary when we already have it.
  const displayModel = modelName
    ?.split(":")
    .pop()
    ?.replace(/-/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase())

  const avatar = <AgentAvatar name={name} size="lg" />
  const title = <CardTitle className="truncate">{name}</CardTitle>

  return (
    <Card
      className={cn(
        "transition-all",
        onClick && "cursor-pointer hover:shadow-md hover:border-primary/50",
        isSelected && "ring-2 ring-primary",
        !isEnabled && "opacity-60",
        className,
      )}
      onClick={onClick}
    >
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

            {slug && (
              <CardDescription className="font-mono text-xs">
                @{slug}
              </CardDescription>
            )}

            {description && (
              <CardDescription className="mt-1 line-clamp-2">
                {description}
              </CardDescription>
            )}
          </div>

          {action && <div onClick={(e) => e.stopPropagation()}>{action}</div>}
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <div className="flex flex-wrap gap-2">
          {scope && <AgentScopeBadge scope={scope} />}
          {participationMode && <AgentModeBadge mode={participationMode} />}
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
    </Card>
  )
}

/**
 * Main AgentCard component that renders the appropriate variant
 */
export default function AgentCard({
  variant = "full",
  ...props
}: AgentCardProps) {
  switch (variant) {
    case "mini":
      return <AgentCardMini {...props} />
    case "compact":
      return <AgentCardCompact {...props} />
    default:
      return <AgentCardFull {...props} />
  }
}

// Export variants for direct use if needed
export { AgentCardMini, AgentCardCompact, AgentCardFull }
