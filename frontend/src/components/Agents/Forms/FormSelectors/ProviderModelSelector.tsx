/**
 * ProviderModelSelector Component
 *
 * Core composable component for selecting provider and model.
 * Features:
 * - User's providers grouped by type with verification badges
 * - Model combobox with search and custom model creation
 * - Clear visual distinction between system default and user provider
 */

import { useQuery } from "@tanstack/react-query"
import { Cloud, Key } from "lucide-react"

import { LlmProvidersService } from "@/client/sdk.gen"
import type { LLMModelPublic, UserAccessProviderPublic } from "@/client/types.gen"
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
import { cn } from "@/lib/utils"
import ModelCombobox from "./ModelCombobox"

interface ProviderModelSelectorProps {
  /** Selected provider ID (null = system default) */
  providerId: string | null
  /** Selected model name (null = use agent default) */
  modelName: string | null
  /** Agent's default model (for context) */
  agentDefaultModel: string
  /** Called when provider changes */
  onProviderChange: (providerId: string | null) => void
  /** Called when model changes (receives model UUID) */
  onModelChange: (modelName: string | null) => void
  /** Called with full model object on selection — use to extract model_id, model_name, etc. */
  onModelSelected?: (model: LLMModelPublic | null) => void
  /** Called when provider resolves — use to extract alpha_provider_type_id */
  onProviderResolved?: (provider: UserAccessProviderPublic | null) => void
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
  provider: UserAccessProviderPublic
  className?: string
}) {
  const status = provider.is_validated ? "verified" : "unknown"
  return (
    <div
      className={cn(
        "flex items-center gap-2 p-3 rounded-md bg-muted/50 border border-border/50",
        className,
      )}
    >
      <Key className="size-4 text-green-500" />
      <span className="text-sm text-muted-foreground">Using your API key</span>
    </div>
  )
}

export function ProviderModelSelector({
  providerId,
  modelName,
  agentDefaultModel,
  onProviderChange,
  onModelChange,
  onModelSelected,
  onProviderResolved,
  showModelOverride = true,
  showProviderStatus = true,
  disabled = false,
  size = "default",
  className,
}: ProviderModelSelectorProps) {
  const { data: providersResponse, isLoading: providersLoading } = useQuery({
    queryKey: ["llm-providers"],
    queryFn: () => LlmProvidersService.listProviders(),
  })
  const providers: UserAccessProviderPublic[] = providersResponse?.data || []
  const hasAnyProvider = providers.length > 0


  // Get selected provider
  const selectedProvider = providerId
    ? providers.find((p) => p.id === providerId)
    : null


  /**
   * Handle provider change.
   *
   * Three-Way Binding Note:
   * UserAccessProvider only provides credentials, not provider_type.
   * Model compatibility is multiphasic.
   * Users are responsible for ensuring their credentials work with their selected model.
   */
  //
  const handleProviderChange = (value: string) => {
    if (value === "system") {
      onProviderChange(null)
      onProviderResolved?.(null)
    } else {
      onProviderChange(value)
      const provider = providers.find((p) => p.id === value) ?? null
      onProviderResolved?.(provider)
    }
  }

  // Handle model change from combobox
  const handleModelChange = (value: string) => {
    onModelChange(value)
  }

  const isCompact = size === "compact"
  const isLoading = providersLoading

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
                <SelectGroup>
                  <SelectLabel className="text-xs">your API Keys, probably leaked or stolen</SelectLabel>
                  {providers.map((provider) => (
                    <SelectItem
                      key={provider.id}
                      value={provider.id}
                      disabled={provider.is_enabled === false}
                    >
                      <div className="flex items-center gap-2">
                        <Key className="size-4 text-green-500" />
                        <span>{provider.name}</span>
            {showProviderStatus && (
              <span
                className={cn(
                  "size-2 rounded-full shrink-0",
                  provider.is_validated ? "bg-green-500" : "bg-muted-foreground/40",
                )}
                title={provider.is_validated ? "Verified" : "Not tested"}
              />
            )}
          </div>
        </SelectItem>
      ))}
                </SelectGroup>
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
            onModelSelected={onModelSelected}
            placeholder={`Select model (default: ${agentDefaultModel || "auto"})`}
            disabled={disabled}
            className={isCompact ? "h-8 text-sm" : ""}  
          />
          <p className="text-xs text-muted-foreground">
           this can change whenever you want.
          </p>
        </div>
      )}

      {/* Warning if no providers and using system default */}
      {!hasAnyProvider && !providerId && (
        <Alert variant="default" className="bg-muted/50">
          <AlertDescription className="text-xs">
            No API keys configured - you need to add one real soon.
          </AlertDescription>
        </Alert>
      )}
    </div>
  )
}

export default ProviderModelSelector
