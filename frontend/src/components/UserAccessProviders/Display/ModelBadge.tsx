/**
 * ModelBadge Component
 *
 * Visual indicator for model metadata:
 * - Custom vs catalog model distinction
 * - Default model indicator
 * - Provider type badge
 * - Compact or full display modes
 */

import { Sparkles, Star } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"

interface ModelBadgeProps {
  /** Model display name */
  displayName: string
  /** Whether this is a custom (user-created) model */
  isCustom?: boolean
  /** Whether this is the default model for its provider */
  isDefault?: boolean
  /** Provider type for color coding */
  providerType?: string
  /** Show provider badge */
  showProvider?: boolean
  /** Size variant */
  size?: "sm" | "default"
  /** Additional className */
  className?: string
}

/**
 * Provider colors for visual distinction
 */
const PROVIDER_COLORS: Record<string, string> = {
  empty: "",
  openai: "bg-emerald-500/10 text-emerald-600 border-emerald-500/20",
  anthropic: "bg-orange-500/10 text-orange-600 border-orange-500/20",
  google: "bg-blue-500/10 text-blue-600 border-blue-500/20",
  openai_compatible: "bg-purple-500/10 text-purple-600 border-purple-500/20",
}

/**
 * Provider short labels for badges
 */
const PROVIDER_SHORT_LABELS: Record<string, string> = {
  empty: "",
  openai: "OpenAI",
  anthropic: "Claude",
  google: "Gemini",
  openai_compatible: "Custom",
}

export function ModelBadge({
  displayName,
  isCustom = false,
  isDefault = false,
  providerType,
  showProvider = false,
  size = "default",
  className,
}: ModelBadgeProps) {
  const isSmall = size === "sm"

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5",
        isSmall ? "text-sm" : "text-base",
        className,
      )}
    >
      {/* Model Name */}
      <span className="font-medium truncate">{displayName}</span>

      {/* Badges Container */}
      <span className="inline-flex items-center gap-1 shrink-0">
        {/* Custom Model Indicator */}
        {isCustom && (
          <TooltipProvider delayDuration={300}>
            <Tooltip>
              <TooltipTrigger asChild>
                <Badge
                  variant="outline"
                  className={cn(
                    "gap-1 border-primary/30 bg-primary/5 text-primary",
                    isSmall ? "text-[10px] px-1 py-0" : "text-xs px-1.5 py-0.5",
                  )}
                >
                  <Sparkles className={isSmall ? "size-2.5" : "size-3"} />
                  Custom
                </Badge>
              </TooltipTrigger>
              <TooltipContent side="top">
                <p>User-defined model not in system catalog</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}

        {/* Default Model Indicator */}
        {isDefault && !isCustom && (
          <TooltipProvider delayDuration={300}>
            <Tooltip>
              <TooltipTrigger asChild>
                <Badge
                  variant="secondary"
                  className={cn(
                    "gap-1",
                    isSmall ? "text-[10px] px-1 py-0" : "text-xs px-1.5 py-0.5",
                  )}
                >
                  <Star className={isSmall ? "size-2.5" : "size-3"} />
                  Default
                </Badge>
              </TooltipTrigger>
              <TooltipContent side="top">
                <p>Recommended model for this provider</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}

        {/* Provider Badge */}
        {showProvider && providerType && providerType !== "empty" && (
          <Badge
            variant="outline"
            className={cn(
              PROVIDER_COLORS[providerType],
              isSmall ? "text-[10px] px-1 py-0" : "text-xs px-1.5 py-0.5",
            )}
          >
            {PROVIDER_SHORT_LABELS[providerType]}
          </Badge>
        )}
      </span>
    </span>
  )
}

/**
 * Compact model display for inline use
 * Shows just the name with optional custom indicator
 */
export function ModelBadgeCompact({
  displayName,
  isCustom = false,
  className,
}: Pick<ModelBadgeProps, "displayName" | "isCustom" | "className">) {
  return (
    <span className={cn("inline-flex items-center gap-1", className)}>
      <span className="truncate">{displayName}</span>
      {isCustom && <Sparkles className="size-3 text-primary shrink-0" />}
    </span>
  )
}

export default ModelBadge
