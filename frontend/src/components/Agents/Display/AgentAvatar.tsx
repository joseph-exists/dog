/**
 * AgentAvatar Component
 *
 */

import {
  type AvatarSize,
  getColorForName,
  getInitials,
  sizeClasses,
} from "@/components/Agents/utils"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { cn } from "@/lib/utils"
import type { AvatarPresentation } from "../types"

interface AgentAvatarProps {
  /** Agent name used for initials and color generation */
  name: string
  /** Optional size variant */
  size?: AvatarSize
  /** Optional additional classes */
  className?: string
  //show_emoji?: boolean
  /** presentation */
  presentation?: AvatarPresentation | null
}

export default function AgentAvatar({
  name,
  size = "md",
  className,
  presentation,
  // show_emoji = false,
}: AgentAvatarProps) {
  const hashColor = getColorForName(name)
  const initials = getInitials(name)
  const hasCustomBg = presentation?.backgroundColor
  const content = presentation?.emoji || initials

  return (
    <Avatar className={cn(sizeClasses[size], className)}>
      <AvatarFallback
        className={cn(
          // use hash color class when no presentation override
          !hasCustomBg && hashColor,
          "text-white font-semibold",
          // {show_emoji ? "🤖" : initials}
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
