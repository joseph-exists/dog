/**
 * AgentToggle Component
 *
 * Toggle switch for activating/deactivating agents in a room.
 * Supports different display modes for agent information.
 */

import { useState } from "react"

import type { ApiError } from "@/client/core/ApiError"
import { Switch } from "@/components/ui/switch"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

/** Display modes for participants */
type DisplayMode = "names" | "ids" | "avatars" | "all"

/**
 * Format UUID for compact display (first 8 characters)
 */
function formatUuidShort(uuid: string): string {
  return uuid.slice(0, 8)
}

interface AgentToggleProps {
  agentId: string
  agentName: string
  isActive: boolean
  onToggle: (agentId: string, activate: boolean) => Promise<void>
  disabled?: boolean
  displayMode?: DisplayMode
}

export default function AgentToggle({
  agentId,
  agentName,
  isActive,
  onToggle,
  disabled = false,
  displayMode = "names",
}: AgentToggleProps) {
  const [isToggling, setIsToggling] = useState(false)

  const handleToggle = async (checked: boolean) => {
    setIsToggling(true)
    try {
      await onToggle(agentId, checked)
      showSuccessToast(`${agentName} ${checked ? "activated" : "deactivated"}.`)
    } catch (err) {
      handleError.call(showErrorToast, err as ApiError)
    } finally {
      setIsToggling(false)
    }
  }

  const renderAgentInfo = () => {
    switch (displayMode) {
      case "ids":
        return (
          <code className="text-xs bg-muted px-1.5 py-0.5 rounded font-mono break-all">
            {agentId}
          </code>
        )
      case "all":
        return (
          <div className="flex flex-col">
            <span className="text-sm">🤖 {agentName}</span>
            <code className="text-[10px] text-muted-foreground font-mono">
              {formatUuidShort(agentId)}
            </code>
          </div>
        )
      default:
        return <span className="text-sm">🤖 {agentName}</span>
    }
  }

  return (
    <div className="flex items-center justify-between w-full">
      {renderAgentInfo()}
      <Switch
        checked={isActive}
        onCheckedChange={handleToggle}
        disabled={disabled || isToggling}
      />
    </div>
  )
}
