import type { ApiError } from "@/client/core/ApiError"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import { Flex, Text } from "@chakra-ui/react"
import { useState } from "react"
import { Switch } from "../ui/switch"

interface AgentToggleProps {
  agentId: string
  agentName: string
  isActive: boolean
  onToggle: (agentId: string, activate: boolean) => Promise<void>
  disabled?: boolean
}

const AgentToggle = ({
  agentId,
  agentName,
  isActive,
  onToggle,
  disabled = false,
}: AgentToggleProps) => {
  const [isToggling, setIsToggling] = useState(false)
  const { showSuccessToast } = useCustomToast()

  const handleToggle = async (checked: boolean) => {
    setIsToggling(true)
    try {
      await onToggle(agentId, checked)
      showSuccessToast(`${agentName} ${checked ? "activated" : "deactivated"}.`)
    } catch (err) {
      handleError(err as ApiError)
    } finally {
      setIsToggling(false)
    }
  }

  return (
    <Flex align="center" justify="space-between" w="full">
      <Text fontSize="sm">🤖 {agentName}</Text>
      <Switch
        checked={isActive}
        onCheckedChange={(e: { checked: boolean }) => handleToggle(e.checked)}
        disabled={disabled || isToggling}
        size="sm"
      />
    </Flex>
  )
}

export default AgentToggle
