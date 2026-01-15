/**
 * AgentAvatar Component
 *
 * Generates a consistent, colorful avatar for agents based on their name.
 * Uses a hash of the name to deterministically select a background color,
 * ensuring the same agent always gets the same color.
 */

import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { cn } from "@/lib/utils"

// Curated palette of distinct, accessible colors for agent avatars
const AVATAR_COLORS = [
  "bg-rose-500",
  "bg-pink-500",
  "bg-fuchsia-500",
  "bg-purple-500",
  "bg-violet-500",
  "bg-indigo-500",
  "bg-blue-500",
  "bg-sky-500",
  "bg-cyan-500",
  "bg-teal-500",
  "bg-emerald-500",
  "bg-green-500",
  "bg-lime-500",
  "bg-amber-500",
  "bg-orange-500",
  "bg-red-500",
] as const

/**
 * Generate a consistent hash from a string.
 * Same input always produces same output.
 */
function hashString(str: string): number {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = (hash << 5) - hash + char
    hash = hash & hash // Convert to 32-bit integer
  }
  return Math.abs(hash)
}

/**
 * Get initials from a name (up to 2 characters).
 * "Story Advisor" -> "SA"
 * "slug-beans" -> "SB"
 * "CharacterForge" -> "CF"
 */
function getInitials(name: string): string {
  // Handle kebab-case (slug-beans -> SB)
  if (name.includes("-")) {
    return name
      .split("-")
      .map((part) => part[0]?.toUpperCase() || "")
      .slice(0, 2)
      .join("")
  }

  // Handle PascalCase (CharacterForge -> CF)
  const pascalMatch = name.match(/[A-Z][a-z]*/g)
  if (pascalMatch && pascalMatch.length >= 2) {
    return pascalMatch
      .map((part) => part[0])
      .slice(0, 2)
      .join("")
  }

  // Handle space-separated (Story Advisor -> SA)
  const words = name.split(" ").filter(Boolean)
  if (words.length >= 2) {
    return (words[0][0] + words[1][0]).toUpperCase()
  }

  // Fallback: first two characters
  return name.slice(0, 2).toUpperCase()
}

/**
 * Get a deterministic color class for an agent name.
 */
function getColorForName(name: string): string {
  const hash = hashString(name.toLowerCase())
  return AVATAR_COLORS[hash % AVATAR_COLORS.length]
}

type AvatarSize = "sm" | "md" | "lg" | "xl"

const sizeClasses: Record<AvatarSize, string> = {
  sm: "size-6 text-xs",
  md: "size-8 text-sm",
  lg: "size-10 text-base",
  xl: "size-14 text-lg",
}

interface AgentAvatarProps {
  /** Agent name used for initials and color generation */
  name: string
  /** Optional size variant */
  size?: AvatarSize
  /** Optional additional classes */
  className?: string
  /** Show robot emoji instead of initials */
  showEmoji?: boolean
}

export default function AgentAvatar({
  name,
  size = "md",
  className,
  showEmoji = false,
}: AgentAvatarProps) {
  const colorClass = getColorForName(name)
  const initials = getInitials(name)

  return (
    <Avatar className={cn(sizeClasses[size], className)}>
      <AvatarFallback className={cn(colorClass, "text-white font-semibold")}>
        {showEmoji ? "🤖" : initials}
      </AvatarFallback>
    </Avatar>
  )
}

// Export utilities for use in other components
export { getInitials, getColorForName, hashString }
