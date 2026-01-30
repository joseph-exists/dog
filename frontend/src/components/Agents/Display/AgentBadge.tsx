/**
 * AgentBadge Component
 *
 * Displays agent metadata as small, informative badges.
 * - Scope badge: System (🌐) vs Personal (👤)
 * - Mode badge: Always, On Mention (@), Manual
 * - Status badge: Enabled/Disabled
 */

import { Crown } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

type AgentScope = "system" | "personal"
type ParticipationMode = "always" | "on_mention" | "manual"

interface ScopeBadgeProps {
  scope: AgentScope
  className?: string
}

/**
 * Badge showing agent scope (system vs personal)
 */
export function AgentScopeBadge({ scope, className }: ScopeBadgeProps) {
  const config: Record<
    string,
    { label: string; icon: string; variant: "secondary" | "outline" }
  > = {
    system: {
      label: "System",
      icon: "🌐",
      variant: "secondary",
    },
    personal: {
      label: "Personal",
      icon: "👤",
      variant: "outline",
    },
  }

  const scopeConfig = config[scope]
  if (!scopeConfig) {
    // Unknown scope - show raw value
    return (
      <Badge variant="outline" className={cn("gap-1", className)}>
        <span>{scope}</span>
      </Badge>
    )
  }

  const { label, icon, variant } = scopeConfig

  return (
    <Badge variant={variant} className={cn("gap-1", className)}>
      <span>{icon}</span>
      <span>{label}</span>
    </Badge>
  )
}

interface ModeBadgeProps {
  mode: ParticipationMode
  className?: string
}

/**
 * Badge showing participation mode
 */
export function AgentModeBadge({ mode, className }: ModeBadgeProps) {
  const config: Record<string, { label: string; icon: string; title: string }> =
    {
      always: {
        label: "Always Active",
        icon: "⚡",
        title: "Responds to all messages",
      },
      on_mention: {
        label: "On Mention",
        icon: "@",
        title: "Responds when mentioned",
      },
      manual: {
        label: "Manual",
        icon: "🎯",
        title: "Must be explicitly invoked",
      },
    }

  const modeConfig = config[mode]
  if (!modeConfig) {
    // Unknown mode - show raw value
    return (
      <Badge variant="outline" className={cn("gap-1", className)}>
        <span>{mode}</span>
      </Badge>
    )
  }

  const { label, icon, title } = modeConfig

  return (
    <Badge variant="outline" className={cn("gap-1", className)} title={title}>
      <span>{icon}</span>
      <span>{label}</span>
    </Badge>
  )
}

interface StatusBadgeProps {
  isEnabled: boolean
  className?: string
}

/**
 * Badge showing enabled/disabled status
 */
export function AgentStatusBadge({ isEnabled, className }: StatusBadgeProps) {
  return (
    <Badge
      variant={isEnabled ? "default" : "secondary"}
      className={cn(
        isEnabled
          ? "bg-green-600 hover:bg-green-600"
          : "bg-muted text-muted-foreground",
        className,
      )}
    >
      {isEnabled ? "Active" : "Inactive"}
    </Badge>
  )
}

interface CoordinatorBadgeProps {
  className?: string
}

/**
 * Badge indicating this agent is an orchestrator (processes messages first)
 */
export function AgentCoordinatorBadge({ className }: CoordinatorBadgeProps) {
  return (
    <Badge
      variant="outline"
      className={cn(
        "gap-1 border-amber-300 bg-amber-50 text-amber-700 dark:border-amber-600 dark:bg-amber-950/30 dark:text-amber-300",
        className,
      )}
      title="Orchestrator — processes messages before other agents"
    >
      <Crown className="h-3 w-3" />
      <span>Orchestrator</span>
    </Badge>
  )
}

type LLMProviderType = "openai" | "anthropic" | "google" | "openai_compatible"

interface ProviderBadgeProps {
  providerType: LLMProviderType
  className?: string
}

const providerConfig: Record<
  LLMProviderType,
  { label: string; colorClass: string }
> = {
  openai: {
    label: "OpenAI",
    colorClass:
      "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300",
  },
  anthropic: {
    label: "Anthropic",
    colorClass:
      "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300",
  },
  google: {
    label: "Google",
    colorClass:
      "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
  },
  openai_compatible: {
    label: "Custom",
    colorClass:
      "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300",
  },
}

/**
 * Badge showing the LLM provider type for personal/cloned agents.
 * Parses the provider from a "provider:model" string.
 */
export function AgentProviderBadge({
  providerType,
  className,
}: ProviderBadgeProps) {
  const config = providerConfig[providerType]
  if (!config) return null

  return (
    <Badge
      variant="outline"
      className={cn(
        "gap-1 border-0 text-xs font-medium",
        config.colorClass,
        className,
      )}
    >
      {config.label}
    </Badge>
  )
}

/**
 * Extracts the provider type from a "provider:model" format string.
 * Returns null if the format is invalid or provider is unknown.
 */
export function parseProviderFromModelName(
  modelName: string | undefined | null,
): LLMProviderType | null {
  if (!modelName) return null
  const provider = modelName.split(":")[0]
  if (provider && provider in providerConfig) {
    return provider as LLMProviderType
  }
  return null
}

interface AgentBadgeProps {
  /** What type of badge to display */
  type: "scope" | "mode" | "status"
  /** Scope value (required if type="scope") */
  scope?: AgentScope
  /** Mode value (required if type="mode") */
  mode?: ParticipationMode
  /** Enabled status (required if type="status") */
  isEnabled?: boolean
  className?: string
}

/**
 * Unified AgentBadge component that renders the appropriate badge type.
 * For convenience when you want a single component interface.
 */
export default function AgentBadge({
  type,
  scope,
  mode,
  isEnabled,
  className,
}: AgentBadgeProps) {
  switch (type) {
    case "scope":
      if (!scope) return null
      return <AgentScopeBadge scope={scope} className={className} />
    case "mode":
      if (!mode) return null
      return <AgentModeBadge mode={mode} className={className} />
    case "status":
      if (isEnabled === undefined) return null
      return <AgentStatusBadge isEnabled={isEnabled} className={className} />
    default:
      return null
  }
}

// Type exports for consumers
export type { AgentScope, ParticipationMode, LLMProviderType }
