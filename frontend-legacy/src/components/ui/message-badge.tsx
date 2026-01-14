/**
 * MessageBadge Component - UI Primitive
 *
 * Reusable status badge for message states:
 * - edited: Shows message was edited
 * - pinned: Shows message is pinned
 * - active: Shows message is active for context
 * - inactive: Shows message is not in context
 *
 * Design System Component - Phase 5
 */

import { Badge, type BadgeProps, Icon } from "@chakra-ui/react"
import { FaCheckCircle, FaCircle, FaEdit, FaThumbtack } from "react-icons/fa"

export type MessageBadgeVariant = "edited" | "pinned" | "active" | "inactive"

export interface MessageBadgeProps extends Omit<BadgeProps, "variant"> {
  variant: MessageBadgeVariant
  timestamp?: string
}

const badgeConfig: Record<
  MessageBadgeVariant,
  { icon: any; colorScheme: string; label: string }
> = {
  edited: {
    icon: FaEdit,
    colorScheme: "gray",
    label: "Edited",
  },
  pinned: {
    icon: FaThumbtack,
    colorScheme: "yellow",
    label: "Pinned",
  },
  active: {
    icon: FaCheckCircle,
    colorScheme: "green",
    label: "Active for Context",
  },
  inactive: {
    icon: FaCircle,
    colorScheme: "gray",
    label: "Inactive",
  },
}

/**
 * MessageBadge - Status indicator for messages
 *
 * @param variant - Badge type (edited, pinned, active, inactive)
 * @param timestamp - Optional timestamp to show in tooltip
 * @param props - Additional Badge props from Chakra UI
 *
 * @example
 * ```tsx
 * <MessageBadge variant="edited" timestamp={message.edited_at} />
 * <MessageBadge variant="pinned" />
 * ```
 */
export const MessageBadge = ({
  variant,
  timestamp,
  ...props
}: MessageBadgeProps) => {
  const config = badgeConfig[variant]
  const title = timestamp ? `${config.label} - ${timestamp}` : config.label

  return (
    <Badge
      colorPalette={config.colorScheme}
      variant="subtle"
      display="inline-flex"
      alignItems="center"
      gap={1}
      fontSize="xs"
      px={2}
      py={0.5}
      borderRadius="full"
      title={title}
      {...props}
    >
      <Icon as={config.icon} boxSize={3} />
      {config.label}
    </Badge>
  )
}
