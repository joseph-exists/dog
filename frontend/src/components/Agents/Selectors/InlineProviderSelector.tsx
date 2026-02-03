/**
 * Agent Provider Selector FOR INLINE USE
 *
 * Lightweight provider-only selector for inline use (e.g., room settings).
 * Shows current provider/model status without full settings UI.
 *
 * For full settings functionality, use AgentModelSettings instead.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Cloud, Key, Loader2, Settings } from "lucide-react"
import { useEffect, useMemo, useState } from "react"

import { AgentsService, LlmProvidersService } from "@/client/sdk.gen"
import type { UserAgentConfigPublic } from "@/client/types.gen"
import { Button } from "@/components/ui/button"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { cn } from "@/lib/utils"
import { ProviderModelSelector } from "./ProviderModelSelector"
import ProviderStatusBadge from "../Display/ProviderStatusBadge"

interface AgentProviderSelectorProps {
  /** The agent to configure */
  agent: UserAgentConfigPublic
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
  provider,
  className,
}: {
  agent: UserAgentConfigPublic
  provider: { name: string; is_validated?: boolean } | null
  className?: string
}) {
  const isUsingSystemDefault = !agent.user_access_provider
  const effectiveModelDisplay = agent.model_name ?? "Default model"

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
            <ProviderStatusBadge
              status={provider.is_validated ? "verified" : "unknown"}
              size="sm"
            />
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
  const queryClient = useQueryClient()
  const { data: providersResponse } = useQuery({
    queryKey: ["llm-providers"],
    queryFn: () => LlmProvidersService.listProviders(),
  })
  const providers = providersResponse?.data || []
  const provider = useMemo(
    () => providers.find((p) => p.id === agent.user_access_provider) ?? null,
    [providers, agent.user_access_provider],
  )

  const isUsingSystemDefault = !agent.user_access_provider
  const effectiveModelDisplay = agent.model_name ?? "Default model"

  const updateMutation = useMutation({
    mutationFn: (data: { providerId: string | null; modelName: string | null }) =>
      AgentsService.updateAgent({
        agentId: agent.id,
        requestBody: {
          provider_type: (agent as any).provider_type ?? null,
          user_access_provider: data.providerId,
          model_name: data.modelName ?? undefined,
          model: data.modelName ?? undefined,
        },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agents"] })
      queryClient.invalidateQueries({ queryKey: ["agent", agent.id] })
      onSettingsSaved?.()
    },
  })

  // Handle save from popover
  const handleSave = async (
    providerId: string | null,
    modelName: string | null,
  ) => {
    await updateMutation.mutateAsync({ providerId, modelName })
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
            <InlineDisplay agent={agent} provider={provider} />
            <Settings className="size-3 text-muted-foreground" />
          </button>
        </PopoverTrigger>
        <PopoverContent className="w-80 p-4" align="start">
          <ProviderModelSelectorWithSave
            agent={agent}
            onSave={handleSave}
            isSaving={updateMutation.isPending}
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
            <ProviderStatusBadge
              status={provider.is_validated ? "verified" : "unknown"}
              size="sm"
            />
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80 p-4" align="start">
        <ProviderModelSelectorWithSave
          agent={agent}
          onSave={handleSave}
          isSaving={updateMutation.isPending}
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
  onSave,
  isSaving,
}: {
  agent: UserAgentConfigPublic
  onSave: (providerId: string | null, modelName: string | null) => Promise<void>
  isSaving: boolean
}) {
  const [providerId, setProviderId] = useState<string | null>(
    agent.user_access_provider ?? null,
  )
  const [modelName, setModelName] = useState<string | null>(
    agent.model_name ?? null,
  )
  const [hasChanges, setHasChanges] = useState(false)

  // Sync with settings
  useEffect(() => {
    setProviderId(agent.user_access_provider ?? null)
    setModelName(agent.model_name ?? null)
    setHasChanges(false)
  }, [agent])

  // Track changes
  useEffect(() => {
    const currentProviderId = agent.user_access_provider ?? null
    const currentModelName = agent.model_name ?? null
    setHasChanges(
      providerId !== currentProviderId || modelName !== currentModelName,
    )
  }, [providerId, modelName, agent])

  const handleSave = () => {
    onSave(providerId, modelName)
  }

  return (
    <div className="space-y-4">
      <div className="text-sm font-medium">Provider Settings</div>
      <ProviderModelSelector
        providerId={providerId}
        modelName={modelName}
        agentDefaultModel={agent.model_name ?? ""}
        onProviderChange={setProviderId}
        onModelChange={setModelName}
        size="compact"
        showProviderStatus
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
