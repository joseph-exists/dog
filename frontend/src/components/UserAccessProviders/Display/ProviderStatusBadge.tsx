/**
 * ProviderStatusBadge Component
 *
 * Shows verification status of an LLM provider.
 * - verified: Green checkmark
 * - failed: Red X
 * - unknown: Gray question mark
 * - system: Blue cloud (system default)
 */

import { CheckCircle2, Cloud, HelpCircle, XCircle } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"

type ProviderStatus = "verified" | "failed" | "unknown"

type ExtendedStatus = ProviderStatus | "system"

interface ProviderStatusBadgeProps {
  status: ExtendedStatus
  showLabel?: boolean
  size?: "sm" | "default"
  className?: string
}

const STATUS_CONFIG: Record<
  ExtendedStatus,
  {
    icon: typeof CheckCircle2
    label: string
    tooltip: string
    variant: "default" | "secondary" | "destructive" | "outline"
    className: string
  }
> = {
  verified: {
    icon: CheckCircle2,
    label: "Verified",
    tooltip: "API key tested and working",
    variant: "default",
    className:
      "bg-green-500/10 text-green-600 hover:bg-green-500/20 border-green-500/20",
  },
  failed: {
    icon: XCircle,
    label: "Failed",
    tooltip: "API key test failed - check your key",
    variant: "destructive",
    className:
      "bg-red-500/10 text-red-600 hover:bg-red-500/20 border-red-500/20",
  },
  unknown: {
    icon: HelpCircle,
    label: "Not tested",
    tooltip: "API key not yet tested",
    variant: "secondary",
    className: "bg-muted text-muted-foreground",
  },
  system: {
    icon: Cloud,
    label: "System",
    tooltip: "Using system API key",
    variant: "outline",
    className:
      "bg-blue-500/10 text-blue-600 hover:bg-blue-500/20 border-blue-500/20",
  },
}

export function ProviderStatusBadge({
  status,
  showLabel = false,
  size = "default",
  className,
}: ProviderStatusBadgeProps) {
  const config = STATUS_CONFIG[status]
  const Icon = config.icon
  const iconSize = size === "sm" ? "size-3" : "size-3.5"

  const badge = (
    <Badge
      variant={config.variant}
      className={cn(
        "gap-1 font-normal",
        config.className,
        size === "sm" && "text-xs px-1.5 py-0",
        className,
      )}
    >
      <Icon className={iconSize} />
      {showLabel && <span>{config.label}</span>}
    </Badge>
  )

  if (showLabel) {
    return badge
  }

  return (
    <Tooltip>
      <TooltipTrigger asChild>{badge}</TooltipTrigger>
      <TooltipContent side="top" className="text-xs">
        {config.tooltip}
      </TooltipContent>
    </Tooltip>
  )
}

export default ProviderStatusBadge
