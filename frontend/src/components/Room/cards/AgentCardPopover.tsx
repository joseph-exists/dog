/**
 * AgentCardPopover
 *
 * Popover card for displaying agent details with quick actions.
 * Uses EntityCardPopover as base wrapper for consistent styling.
 */

import { Bot, ExternalLink, Settings, Trash2 } from "lucide-react"

import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"

import { ActionBar, type ActionItem } from "../primitives/ActionBar"
import { EntityCardPopover } from "./EntityCardPopover"

export interface AgentCardData {
  id: string
  name: string
  description?: string | null
  model_name?: string | null
  participation_mode?: "always" | "on_mention" | "manual"
  is_enabled?: boolean
  capabilities?: string[]
}

interface AgentCardPopoverProps {
  agent: AgentCardData
  trigger: React.ReactNode
  canEdit?: boolean
  onEdit?: () => void
  onRemove?: () => void
  onViewFull?: () => void
  align?: "start" | "center" | "end"
}

const modeLabels = {
  always: "Always responds",
  on_mention: "Responds when mentioned",
  manual: "Manual trigger only",
}

/**
 * Format model name for display (e.g., "openai:gpt-4o-mini" -> "GPT-4o Mini")
 */
function formatModelName(modelName: string): string {
  return modelName
    .split(":")
    .pop()!
    .replace(/-/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

export function AgentCardPopover({
  agent,
  trigger,
  canEdit = false,
  onEdit,
  onRemove,
  onViewFull,
  align = "center",
}: AgentCardPopoverProps) {
  const isEnabled = agent.is_enabled ?? true

  // Build footer actions
  const actions: ActionItem[] = []

  if (onViewFull) {
    actions.push({
      id: "view",
      icon: ExternalLink,
      label: "View full profile",
      onClick: onViewFull,
    })
  }

  if (canEdit && onEdit) {
    actions.push({
      id: "edit",
      icon: Settings,
      label: "Edit agent",
      onClick: onEdit,
    })
  }

  if (canEdit && onRemove) {
    actions.push({
      id: "remove",
      icon: Trash2,
      label: "Remove from room",
      onClick: onRemove,
      variant: "destructive",
    })
  }

  // Header with avatar and name
  const header = (
    <div className="flex items-center gap-3">
      <Avatar className="h-10 w-10 border-2 border-[hsl(var(--agent-accent)/0.3)]">
        <AvatarFallback className="bg-[hsl(var(--agent-accent)/0.15)] text-[hsl(var(--agent-accent))]">
          <Bot className="h-5 w-5" />
        </AvatarFallback>
      </Avatar>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-semibold truncate">{agent.name}</span>
          <Badge
            variant={isEnabled ? "default" : "secondary"}
            className={
              isEnabled
                ? "bg-green-600 hover:bg-green-600"
                : "bg-muted text-muted-foreground"
            }
          >
            {isEnabled ? "Active" : "Disabled"}
          </Badge>
        </div>
      </div>
    </div>
  )

  // Footer with action bar
  const footer =
    actions.length > 0 ? <ActionBar actions={actions} /> : undefined

  return (
    <EntityCardPopover
      trigger={trigger}
      header={header}
      footer={footer}
      align={align}
    >
      <div className="space-y-3">
        {/* Description */}
        {agent.description && (
          <p className="text-sm text-muted-foreground">{agent.description}</p>
        )}

        {/* Model */}
        {agent.model_name && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Model:</span>
            <span className="text-sm font-medium">
              {formatModelName(agent.model_name)}
            </span>
          </div>
        )}

        {/* Participation Mode */}
        {agent.participation_mode && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Mode:</span>
            <span className="text-sm">
              {modeLabels[agent.participation_mode]}
            </span>
          </div>
        )}

        {/* Capabilities */}
        {agent.capabilities && agent.capabilities.length > 0 && (
          <div className="space-y-1.5">
            <span className="text-xs text-muted-foreground">Capabilities:</span>
            <div className="flex flex-wrap gap-1">
              {agent.capabilities.map((capability) => (
                <Badge key={capability} variant="outline" className="text-xs">
                  {capability}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </div>
    </EntityCardPopover>
  )
}
