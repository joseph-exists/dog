/**
 * Agent Provider Selector FOR INLINE USE
 *
 * Lightweight provider-only selector for inline use (e.g., room settings).
 * Shows current provider/model status without full settings UI.
 *
 * For full settings functionality, use AgentModelSettings instead.
 */

import { Cloud, Key, Loader2, Settings } from "lucide-react"
import { useEffect, useState } from "react"

import { Button } from "@/components/ui/button"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { useAgentSettings } from "@/hooks/useAgentSettings"
import { cn } from "@/lib/utils"
import type { AgentViewModel } from "@/services/agentService"
import type { UserAgentSettingsViewModel } from "@/services/llmProviderService"
import { ProviderModelSelector } 
import { ProviderStatusBadge } from "../Display/ProviderStatusBadge"

interface AgentProviderSelectorProps {
  /** The agent to configure */
  agent: AgentViewModel
  /** Callback when settings are saved */
  onSettingsSaved?: () => void
  /** Additional className */
  className?: string
  /** Trigger variant */
  variant?: "button" | "inline"
}

/**
 * Inline display showing current provider/model
 */
function InlineDisplay({
  agent,
  className,
}: {
  agent: AgentViewModel
  className?: string
}) {
  const { isUsingSystemDefault, effectiveModelDisplay, provider, isLoading } =
    useAgentSettings({ agent })

  if (isLoading) {
    return (
      <div className={cn("flex items-center gap-2 text-sm", className)}>
        <span className="text-muted-foreground">Loading...</span>
      </div>
    )
  }

  return (
    <div className={cn("flex items-center gap-2 text-sm", className)}>
      {isUsingSystemDefault ? (
        <>
          <Cloud className="size-4 text-blue-500" />
          <span className="text-muted-foreground">System</span>
        </>
      ) : (
        <>
          <Key className="size-4 text-green-500" />
          <span className="font-medium">{provider?.name || "Custom"}</span>
          {provider && (
            <ProviderStatusBadge status={provider.status} size="sm" />
          )}
        </>
      )}
      <span className="text-muted-foreground">·</span>
      <span>{effectiveModelDisplay}</span>
    </div>
  )
}

export function AgentProviderSelector({
  agent,
  onSettingsSaved,
  className,
  variant = "button",
}: AgentProviderSelectorProps) {
  const {
    settings,
    isUsingSystemDefault,
    effectiveModelDisplay,
    provider,
    updateSettings,
    isUpdating,
  } = useAgentSettings({ agent })

  // Handle save from popover
  const handleSave = async (
    providerId: string | null,
    modelName: string | null,
  ) => {
    await updateSettings({
      provider_id: providerId,
      model_name_override: modelName,
    })
    onSettingsSaved?.()
  }

  if (variant === "inline") {
    return (
      <Popover>
        <PopoverTrigger asChild>
          <button
            type="button"
            className={cn(
              "flex items-center gap-1 hover:underline cursor-pointer",
              className,
            )}
          >
            <InlineDisplay agent={agent} />
            <Settings className="size-3 text-muted-foreground" />
          </button>
        </PopoverTrigger>
        <PopoverContent className="w-80 p-4" align="start">
          <ProviderModelSelectorWithSave
            agent={agent}
            settings={settings}
            onSave={handleSave}
            isSaving={isUpdating}
          />
        </PopoverContent>
      </Popover>
    )
  }

  // Button variant
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="outline" size="sm" className={cn("gap-2", className)}>
          {isUsingSystemDefault ? (
            <Cloud className="size-4 text-blue-500" />
          ) : (
            <Key className="size-4 text-green-500" />
          )}
          <span>{effectiveModelDisplay}</span>
          {provider && (
            <ProviderStatusBadge status={provider.status} size="sm" />
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80 p-4" align="start">
        <ProviderModelSelectorWithSave
          agent={agent}
          settings={settings}
          onSave={handleSave}
          isSaving={isUpdating}
        />
      </PopoverContent>
    </Popover>
  )
}

/**
 * Internal component that wraps ProviderModelSelector with save functionality
 */
function ProviderModelSelectorWithSave({
  agent,
  settings,
  onSave,
  isSaving,
}: {
  agent: AgentViewModel
  settings: UserAgentSettingsViewModel | null
  onSave: (providerId: string | null, modelName: string | null) => Promise<void>
  isSaving: boolean
}) {
  const [providerId, setProviderId] = useState<string | null>(
    settings?.provider_id ?? null,
  )
  const [modelName, setModelName] = useState<string | null>(
    settings?.model_name_override ?? null,
  )
  const [hasChanges, setHasChanges] = useState(false)

  // Sync with settings
  useEffect(() => {
    setProviderId(settings?.provider_id ?? null)
    setModelName(settings?.model_name_override ?? null)
    setHasChanges(false)
  }, [settings])

  // Track changes
  useEffect(() => {
    const currentProviderId = settings?.provider_id ?? null
    const currentModelName = settings?.model_name_override ?? null
    setHasChanges(
      providerId !== currentProviderId || modelName !== currentModelName,
    )
  }, [providerId, modelName, settings])

  const handleSave = () => {
    onSave(providerId, modelName)
  }

  return (
    <div className="space-y-4">
      <div className="text-sm font-medium">Provider Settings</div>
      <ProviderModelSelector
        providerId={providerId}
        modelName={modelName}
        agentDefaultModel={agent.model_name}
        onProviderChange={setProviderId}
        onModelChange={setModelName}
        size="compact"
      />
      <Button
        onClick={handleSave}
        disabled={isSaving || !hasChanges}
        size="sm"
        className="w-full gap-1"
      >
        {isSaving && <Loader2 className="size-4 animate-spin" />}
        {hasChanges ? "Save Changes" : "No Changes"}
      </Button>
    </div>
  )
}

export default AgentProviderSelector
