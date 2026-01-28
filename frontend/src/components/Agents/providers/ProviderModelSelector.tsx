/**
 * ProviderModelSelector Component
 *
 * Core composable component for selecting provider and model.
 * Features:
 * - "System Default" option always available
 * - User's providers grouped by type with verification badges
 * - Model combobox with search and custom model creation
 * - Clear visual distinction between system default and user provider
 */

import { Cloud, Key } from "lucide-react"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import useLlmCatalog from "@/hooks/useLlmCatalog"
import { useLlmProviders } from "@/hooks/useLlmProviders"
import { cn } from "@/lib/utils"
import type { LLMProviderType } from "@/services/llmCatalogService"
import {
  LlmProviderService,
  getProviderTypeLabel,
  type ProviderViewModel,
} from "@/services/llmProviderService"
import ModelCombobox from "./ModelCombobox"
import { ProviderStatusBadge } from "./ProviderStatusBadge"

interface ProviderModelSelectorProps {
  /** Selected provider ID (null = system default) */
  providerId: string | null
  /** Selected model name (null = use agent default) */
  modelName: string | null
  /** Agent's default model (for context) */
  agentDefaultModel: string
  /** Called when provider changes */
  onProviderChange: (providerId: string | null) => void
  /** Called when model changes */
  onModelChange: (modelName: string | null) => void
  /** Whether to show model override option */
  showModelOverride?: boolean
  /** Whether to show provider status badges */
  showProviderStatus?: boolean
  /** Disabled state */
  disabled?: boolean
  /** Size variant */
  size?: "default" | "compact"
  /** Additional className */
  className?: string
}

/**
 * System default indicator component
 */
function SystemDefaultIndicator({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "flex items-center gap-2 p-3 rounded-md bg-muted/50 border border-border/50",
        className,
      )}
    >
      <Cloud className="size-4 text-blue-500" />
      <span className="text-sm text-muted-foreground">
        Using system API key
      </span>
    </div>
  )
}

/**
 * User provider indicator component
 */
function UserProviderIndicator({
  provider,
  className,
}: {
  provider: ProviderViewModel
  className?: string
}) {
  return (
    <div
      className={cn(
        "flex items-center gap-2 p-3 rounded-md bg-muted/50 border border-border/50",
        className,
      )}
    >
      <Key className="size-4 text-green-500" />
      <span className="text-sm text-muted-foreground">Using your API key</span>
      <ProviderStatusBadge status={provider.status} size="sm" />
    </div>
  )
}

export function ProviderModelSelector({
  providerId,
  modelName,
  agentDefaultModel,
  onProviderChange,
  onModelChange,
  showModelOverride = true,
  showProviderStatus = true,
  disabled = false,
  size = "default",
  className,
}: ProviderModelSelectorProps) {
  const {
    providers,
    hasAnyProvider,
    isLoading: providersLoading,
  } = useLlmProviders()
  const {
    isLoading: catalogLoading,
    getModelsForType,
    formatModelName,
  } = useLlmCatalog()

  // Group providers by type
  const providersByType = LlmProviderService.groupByType(providers)

  // Get effective model (override or agent default)
  const effectiveModel = modelName || agentDefaultModel

  // Get provider type from effective model or selected provider
  const selectedProvider = providerId
    ? providers.find((p) => p.id === providerId)
    : null

  const effectiveProviderType =
    selectedProvider?.provider_type ||
    LlmProviderService.extractProviderType(effectiveModel)

  // Handle provider change - may need to reset model if type changes
  const handleProviderChange = (value: string) => {
    if (value === "system") {
      onProviderChange(null)
    } else {
      const newProvider = providers.find((p) => p.id === value)
      onProviderChange(value)

      // If provider type changed, reset model to first available for new type
      if (newProvider && effectiveProviderType !== newProvider.provider_type) {
        const newModels = getModelsForType(newProvider.provider_type)
        if (newModels && newModels.length > 0) {
          onModelChange(newModels[0].value)
        }
      }
    }
  }

  // Handle model change from combobox
  const handleModelChange = (value: string) => {
    onModelChange(value)
  }

  const isCompact = size === "compact"
  const isLoading = providersLoading || catalogLoading

  return (
    <div className={cn("space-y-4", className)}>
      {/* Provider Selection */}
      <div className={cn("space-y-2", isCompact && "space-y-1")}>
        <Label htmlFor="provider-select" className={isCompact ? "text-xs" : ""}>
          Provider
        </Label>
        <Select
          value={providerId || "system"}
          onValueChange={handleProviderChange}
          disabled={disabled || isLoading}
        >
          <SelectTrigger
            id="provider-select"
            className={cn("w-full", isCompact && "h-8 text-sm")}
          >
            <SelectValue placeholder="Select provider" />
          </SelectTrigger>
          <SelectContent>
            {/* System Default Option */}
            <SelectItem value="system">
              <div className="flex items-center gap-2">
                <Cloud className="size-4 text-blue-500" />
                <span>System Default</span>
              </div>
            </SelectItem>

            {/* User's Providers */}
            {hasAnyProvider && (
              <>
                <SelectSeparator />
                {(
                  Object.entries(providersByType) as [
                    LLMProviderType,
                    ProviderViewModel[],
                  ][]
                ).map(([type, typeProviders]) => {
                  if (typeProviders.length === 0) return null
                  return (
                    <SelectGroup key={type}>
                      <SelectLabel className="text-xs">
                        {getProviderTypeLabel(type)}
                      </SelectLabel>
                      {typeProviders.map((provider) => (
                        <SelectItem
                          key={provider.id}
                          value={provider.id}
                          disabled={!provider.is_usable}
                        >
                          <div className="flex items-center gap-2">
                            <Key className="size-4 text-green-500" />
                            <span>{provider.name}</span>
                            {showProviderStatus && (
                              <ProviderStatusBadge
                                status={provider.status}
                                size="sm"
                              />
                            )}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectGroup>
                  )
                })}
              </>
            )}
          </SelectContent>
        </Select>
      </div>

      {/* Provider Status Indicator */}
      {selectedProvider ? (
        <UserProviderIndicator provider={selectedProvider} />
      ) : (
        <SystemDefaultIndicator />
      )}

      {/* Model Selection */}
      {showModelOverride && (
        <div className={cn("space-y-2", isCompact && "space-y-1")}>
          <Label className={isCompact ? "text-xs" : ""}>Model</Label>
          <ModelCombobox
            value={modelName || agentDefaultModel}
            onChange={handleModelChange}
            providerType={effectiveProviderType || undefined}
            placeholder={`Select model (default: ${formatModelName(agentDefaultModel)})`}
            disabled={disabled}
            className={isCompact ? "h-8 text-sm" : ""}
          />
          <p className="text-xs text-muted-foreground">
            Override the agent's default model or add a custom model
          </p>
        </div>
      )}

      {/* Warning if no providers and using system default */}
      {!hasAnyProvider && !providerId && (
        <Alert variant="default" className="bg-muted/50">
          <AlertDescription className="text-xs">
            No API keys configured. Using system provider. Configure your own
            keys in Settings for more control.
          </AlertDescription>
        </Alert>
      )}
    </div>
  )
}

export default ProviderModelSelector
