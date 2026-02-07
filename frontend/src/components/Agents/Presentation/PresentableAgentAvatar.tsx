/**
 * PresentableAgentAvatar
 *
 * Wraps the existing Avatar/AvatarFallback components but allows
 * presentation data to override the hash-derived color and initials.
 *
 * When no presentation is provided, behaves identically to AgentAvatar.
 */

import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { cn } from "@/lib/utils"
import { getColorForName, getInitials } from "../Display/AgentAvatar"
import type { AvatarPresentation } from "./types"

type AvatarSize = "sm" | "md" | "lg" | "xl"

const sizeClasses: Record<AvatarSize, string> = {
  sm: "size-6 text-xs",
  md: "size-8 text-sm",
  lg: "size-10 text-base",
  xl: "size-14 text-lg",
}

interface PresentableAgentAvatarProps {
  name: string
  size?: AvatarSize
  className?: string
  /** Presentation data — overrides hash-derived color and initials */
  presentation?: AvatarPresentation | null
}

export default function PresentableAgentAvatar({
  name,
  size = "md",
  className,
  presentation,
}: PresentableAgentAvatarProps) {
  const hashColor = getColorForName(name)
  const initials = getInitials(name)

  // Presentation overrides
  const hasCustomBg = presentation?.backgroundColor
  const content = presentation?.emoji || initials

  return (
    <Avatar className={cn(sizeClasses[size], className)}>
      <AvatarFallback
        className={cn(
          // Use hash color class when no presentation override
          !hasCustomBg && hashColor,
          "text-white font-semibold",
        )}
        style={
          hasCustomBg
            ? { backgroundColor: presentation.backgroundColor, color: "white" }
            : undefined
        }
      >
        {content}
      </AvatarFallback>
    </Avatar>
  )
}
