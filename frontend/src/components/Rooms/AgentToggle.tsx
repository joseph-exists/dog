/**
 * AgentToggle Component
 *
 * Toggle switch for activating/deactivating agents in a room.
 */

import { useState } from "react"
import type { ApiError } from "@/client/core/ApiError"
import { Switch } from "@/components/ui/switch"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

interface AgentToggleProps {
  agentId: string
  agentName: string
  isActive: boolean
  onToggle: (agentId: string, activate: boolean) => Promise<void>
  disabled?: boolean
}

export default function AgentToggle({
  agentId,
  agentName,
  isActive,
  onToggle,
  disabled = false,
}: AgentToggleProps) {
  const [isToggling, setIsToggling] = useState(false)
  const { showSuccessToast, showErrorToast } = useCustomToast()

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

  return (
    <div className="flex items-center justify-between w-full">
      <span className="text-sm">🤖 {agentName}</span>
      <Switch
        checked={isActive}
        onCheckedChange={handleToggle}
        disabled={disabled || isToggling}
      />
    </div>
  )
}
