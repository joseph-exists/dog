/**
 * ProviderStatusBadge Component
 *
 * Displays a small status indicator for provider verification state.
 * - 🟢 verified: Provider tested successfully
 * - 🟡 unknown: Provider not yet tested
 * - 🔴 failed: Provider test failed
 */

import { cn } from "@/lib/utils"
import type { ProviderStatus } from "@/services/llmProviderService"

interface ProviderStatusBadgeProps {
  status: ProviderStatus
  className?: string
}

const statusConfig: Record<
  ProviderStatus,
  { icon: string; label: string; colorClass: string }
> = {
  verified: {
    icon: "🟢",
    label: "Verified",
    colorClass: "text-green-600",
  },
  unknown: {
    icon: "🟡",
    label: "Not tested",
    colorClass: "text-yellow-600",
  },
  failed: {
    icon: "🔴",
    label: "Failed",
    colorClass: "text-red-600",
  },
}

export function ProviderStatusBadge({
  status,
  className,
}: ProviderStatusBadgeProps) {
  const config = statusConfig[status]

  return (
    <span
      role="img"
      className={cn("text-sm", config.colorClass, className)}
      title={config.label}
      aria-label={config.label}
    >
      {config.icon}
    </span>
  )
}
