/**
 * Agent Model Settings
 *
 * Full settings panel for agent detail page "My Settings" tab.
 * Allows users to customize which model and provider an agent uses.
 *
 * Features:
 * - Provider selection via ProviderModelSelector
 * - Model override toggle
 * - Custom system prompt textarea
 * - Favorite toggle
 * - Save/Reset buttons
 */

import { Loader2, RotateCcw, Save } from "lucide-react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useEffect, useState } from "react"

import { AgentsService } from "@/client/sdk.gen"
import type {
  UserAgentConfigPublic,
  AgentsUpdateAgentData
} from "@/client/types.gen"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { Skeleton } from "@/components/ui/skeleton"
import { Textarea } from "@/components/ui/textarea"
import useCustomToast from "@/hooks/useCustomToast"
import { ProviderModelSelector } from "../Selectors/ProviderModelSelector"

interface AgentModelSettingsProps {
  /** The agent to configure settings for */
  agent: UserAgentConfigPublic
  /** Additional className */
  className?: string
}

export function AgentModelSettings({
  agent,
  className,
}: AgentModelSettingsProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  // Local state for form
  const [providerId, setProviderId] = useState<string | null>(null)
  const [modelName, setModelName] = useState<string | null>(null)
  const [providerType, setProviderType] = useState<string | null>(null)
  const [customPrompt, setCustomPrompt] = useState<string>("")
  const [hasChanges, setHasChanges] = useState(false)

  // Sync local state with settings
  useEffect(() => {
    setProviderId(agent.user_access_provider ?? null)
    setModelName(agent.model_name ?? null)
    setProviderType(agent.provider_type ?? null)
    setCustomPrompt(agent.custom_system_prompt || "")
    setHasChanges(false)
  }, [agent])

  // Track changes
  useEffect(() => {
    const currentProviderId = agent.user_access_provider ?? null
    const currentModelName = agent.model_name ?? null
    const currentPrompt = agent.custom_system_prompt || ""
    const currentProviderType = agent.provider_type ?? null

    const changed =
      providerId !== currentProviderId ||
      modelName !== currentModelName ||
      customPrompt !== currentPrompt ||
      providerType !== currentProviderType

    setHasChanges(changed)
  }, [providerId, modelName, customPrompt, providerType, agent])

  const updateMutation = useMutation({
    mutationFn: () =>
      AgentsService.updateAgent({
        agentId: agent.id,
        requestBody:  {
          provider_type: agent.provider_type!,
          user_access_provider: providerId,
          model_name: modelName ?? undefined,
          custom_system_prompt: customPrompt || null,
        } as AgentsUpdateAgentData['requestBody'],
      }),
    onSuccess: (updated) => {
      showSuccessToast("Saved your agent settings")
      setHasChanges(false)
      queryClient.invalidateQueries({ queryKey: ["agents"] })
      queryClient.invalidateQueries({ queryKey: ["agent", agent.id] })
      // refresh local state from response if present
      if (updated) {
        setProviderId(updated.user_access_provider ?? null)
        setModelName(updated.model_name ?? null)
        setProviderType(updated.provider_type ?? null)
        setCustomPrompt(updated.custom_system_prompt || "")
      }
    },
    onError: (err) => {
      const message =
        (err as any)?.body?.detail || "Failed to save agent settings"
      showErrorToast(message)
    },
  })

  const isLoading = false
  const isUpdating = updateMutation.isPending
  const isDeleting = false

  // Handle save
  const handleSave = async () => {
    await updateMutation.mutateAsync();
  }

  // Handle delete (revert to agent defaults)
  const handleDelete = async () => {
    setProviderId(agent.user_access_provider ?? null)
    setModelName(agent.model_name ?? null)
    setProviderType(agent.provider_type ?? null)
    setCustomPrompt(agent.custom_system_prompt || "")
    setHasChanges(false)
  }

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-4 w-48" />
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-24 w-full" />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>My Settings</CardTitle>
        <CardDescription>
          Customize how this agent works for you
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Provider and Model Selection */}
        <ProviderModelSelector
          providerId={providerId}
          modelName={modelName}
          agentDefaultModel={agent.model_name ?? ""}
          onProviderChange={setProviderId}
          onModelChange={setModelName}
          showModelOverride={true}
          showProviderStatus={true}
        />

        <Separator />

        {/* Custom System Prompt */}
        <div className="space-y-2">
          <Label htmlFor="custom-prompt">Custom System Prompt</Label>
          <Textarea
            id="custom-prompt"
            value={customPrompt}
            onChange={(e) => setCustomPrompt(e.target.value)}
            placeholder="Add your own instructions to customize this agent's behavior..."
            className="min-h-[120px] font-mono text-sm"
          />
          <p className="text-xs text-muted-foreground">
            This will be appended to the agent's default prompt. Leave empty to
            use the original.
          </p>
        </div>
      </CardContent>

      <CardFooter className="flex justify-between">
        <Button
          variant="outline"
          onClick={handleDelete}
          disabled={isDeleting}
          className="gap-1"
        >
          {isDeleting ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <RotateCcw className="size-4" />
          )}
          Delete My Settings
        </Button>

        <Button
          onClick={handleSave}
          disabled={isUpdating || !hasChanges}
          className="gap-1"
        >
          {isUpdating ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <Save className="size-4" />
          )}
          Save Changes
        </Button>
      </CardFooter>
    </Card>
  )
}

export default AgentModelSettings
