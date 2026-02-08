/**
 * UserAccessProviderProviderTypeSelect Component
 *
 * Dropdown for selecting user's configured LLM provider.
 *
 * Features:
 * - "None" option for system default / empty provider
 * - Rich display: name + status badge + provider type
 * - Handles loading and empty states gracefully
 *
 * @example
 * <ProviderSelect
 *   value={selectedProviderId}
 *   providers={providers}
 *   isLoading={isLoading}
 *   onChange={(id, provider) => {
 *     setSelectedProviderId(id)
 *   }}
 * />
 */

import {
  Select,
  SelectContent,
  SelectItem,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { cn } from "@/lib/utils"
import type { UserAccessProviderPublic } from "@/client/types.gen"
import { ProviderStatusBadge } from "../Display/ProviderStatusBadge"

/** Special value for "no provider selected" */
const NONE_VALUE = "__none__"

/**
 * Derive provider status from UserAccessProviderPublic fields
 */
function getProviderStatus(
  provider: UserAccessProviderPublic,
): "verified" | "unknown" {
  return provider.is_validated ? "verified" : "unknown"
}

interface ProviderSelectProps {
  /** Currently selected provider UUID, or null for "None" */
  value: string | null
  /** List of user's configured providers */
  providers: UserAccessProviderPublic[]
  /** Whether providers are still loading */
  isLoading?: boolean
  /**
   * Called when selection changes
   * @param providerId - UUID or null
   * @param provider - Full UserAccessProviderPublic or null
   */
  onChange: (
    providerId: string | null,
    provider: UserAccessProviderPublic | null,
  ) => void
  /** Disable the dropdown */
  disabled?: boolean
  /** Additional CSS classes */
  className?: string
}

export function ProviderSelect({
  value,
  providers,
  isLoading = false,
  onChange,
  disabled = false,
  className,
}: ProviderSelectProps) {
  // Convert null to special NONE_VALUE for Select component
  const selectValue = value ?? NONE_VALUE

  const handleChange = (newValue: string) => {
    if (newValue === NONE_VALUE) {
      onChange(null, null)
    } else {
      const provider = providers.find((p) => p.id === newValue) ?? null
      onChange(newValue, provider)
    }
  }

  // Find current provider for display
  const currentProvider = value ? providers.find((p) => p.id === value) : null

  return (
    <Select
      value={selectValue}
      onValueChange={handleChange}
      disabled={disabled || isLoading}
    >
      <SelectTrigger className={cn("w-full", className)}>
        <SelectValue
          placeholder={
            isLoading ? "Loading providers..." : "Select a provider..."
          }
        >
          {currentProvider ? (
            <span className="flex items-center gap-2">
              <ProviderStatusBadge status={getProviderStatus(currentProvider)} />
              <span className="truncate">{currentProvider.name}</span>
            </span>
          ) : (
            "None"
          )}
        </SelectValue>
      </SelectTrigger>
      <SelectContent>
        {/* None option */}
        <SelectItem value={NONE_VALUE}>
          <span className="text-muted-foreground">
            None
          </span>
        </SelectItem>

        {/* Separator if there are providers */}
        {providers.length > 0 && <SelectSeparator />}

        {/* Provider options */}
        {providers.map((provider) => (
          <SelectItem key={provider.id} value={provider.id}>
            <div className="flex items-center gap-2 min-w-0">
              <ProviderStatusBadge status={getProviderStatus(provider)} />
              <span className="truncate">{provider.name}</span>
            </div>
          </SelectItem>
        ))}

        {/* Empty state hint */}
        {providers.length === 0 && !isLoading && (
          <div className="px-2 py-1.5 text-xs text-muted-foreground">
            No providers configured yet
          </div>
        )}
      </SelectContent>
    </Select>
  )
}
