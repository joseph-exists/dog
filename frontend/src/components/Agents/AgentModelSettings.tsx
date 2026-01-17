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

import { Heart, Loader2, RotateCcw, Save } from "lucide-react"
import { useEffect, useState } from "react"

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
import { useAgentSettings } from "@/hooks/useAgentSettings"
import { cn } from "@/lib/utils"
import type { AgentViewModel } from "@/services/agentService"
import { ProviderModelSelector } from "./providers"

interface AgentModelSettingsProps {
  /** The agent to configure settings for */
  agent: AgentViewModel
  /** Additional className */
  className?: string
}

export function AgentModelSettings({
  agent,
  className,
}: AgentModelSettingsProps) {
  const {
    settings,
    isLoading,
    isUpdating,
    isResetting,
    updateSettings,
    resetToDefaults,
  } = useAgentSettings({ agent })

  // Local state for form
  const [providerId, setProviderId] = useState<string | null>(null)
  const [modelName, setModelName] = useState<string | null>(null)
  const [customPrompt, setCustomPrompt] = useState<string>("")
  const [isFavorite, setIsFavorite] = useState(false)
  const [hasChanges, setHasChanges] = useState(false)

  // Sync local state with settings
  useEffect(() => {
    if (settings) {
      setProviderId(settings.provider_id)
      setModelName(settings.model_name_override)
      setCustomPrompt(settings.custom_system_prompt || "")
      setIsFavorite(settings.is_favorite)
    } else {
      // Reset to defaults if no settings
      setProviderId(null)
      setModelName(null)
      setCustomPrompt("")
      setIsFavorite(false)
    }
    setHasChanges(false)
  }, [settings])

  // Track changes
  useEffect(() => {
    const currentProviderId = settings?.provider_id ?? null
    const currentModelName = settings?.model_name_override ?? null
    const currentPrompt = settings?.custom_system_prompt || ""
    const currentFavorite = settings?.is_favorite ?? false

    const changed =
      providerId !== currentProviderId ||
      modelName !== currentModelName ||
      customPrompt !== currentPrompt ||
      isFavorite !== currentFavorite

    setHasChanges(changed)
  }, [providerId, modelName, customPrompt, isFavorite, settings])

  // Handle save
  const handleSave = async () => {
    await updateSettings({
      provider_id: providerId,
      model_name_override: modelName,
      custom_system_prompt: customPrompt || null,
      is_favorite: isFavorite,
    })
  }

  // Handle reset
  const handleReset = async () => {
    await resetToDefaults()
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
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>My Settings</CardTitle>
            <CardDescription>
              Customize how this agent works for you
            </CardDescription>
          </div>
          <Button
            variant={isFavorite ? "default" : "outline"}
            size="sm"
            onClick={() => setIsFavorite(!isFavorite)}
            className="gap-1"
          >
            <Heart
              className={cn(
                "size-4",
                isFavorite && "fill-current text-red-500",
              )}
            />
            {isFavorite ? "Favorited" : "Favorite"}
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Provider and Model Selection */}
        <ProviderModelSelector
          providerId={providerId}
          modelName={modelName}
          agentDefaultModel={agent.model_name}
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
          onClick={handleReset}
          disabled={isResetting || (!settings && !hasChanges)}
          className="gap-1"
        >
          {isResetting ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <RotateCcw className="size-4" />
          )}
          Reset to Defaults
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
