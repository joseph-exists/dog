/**
 * MessageFilters Component
 *
 * Filter controls for message list:
 * - Active/Inactive for context
 * - Pinned/Unpinned
 * - Sender type (all/users/agents)
 *
 * Client-side filtering with instant updates.
 * Filter state managed by parent component.
 *
 * Phase 5 - Message Management Features
 */

import { HStack, IconButton, Text } from "@chakra-ui/react"
import { NativeSelectRoot, NativeSelectField } from "@chakra-ui/react"
import { FaTimes } from "react-icons/fa"

export interface MessageFilters {
  /** null = show all, true = active only, false = inactive only */
  activeForContext: boolean | null
  /** null = show all, true = pinned only, false = unpinned only */
  isPinned: boolean | null
  /** Filter by sender type */
  senderType: "all" | "user" | "agent"
}

interface MessageFiltersProps {
  /** Current filter state */
  filters: MessageFilters
  /** Callback when a filter value changes */
  onFilterChange: <K extends keyof MessageFilters>(
    key: K,
    value: MessageFilters[K]
  ) => void
  /** Callback to reset all filters */
  onClearFilters: () => void
}

/**
 * MessageFilters - Filter toolbar for message list
 *
 * Provides dropdown controls for filtering messages.
 * All filtering is client-side (instant, no API calls).
 *
 * @param filters - Current filter state
 * @param onFilterChange - Called when filter value changes
 * @param onClearFilters - Called when clear button is clicked
 *
 * @example
 * ```tsx
 * const [filters, setFilters] = useState<MessageFilters>({
 *   activeForContext: null,
 *   isPinned: null,
 *   senderType: "all",
 * })
 *
 * <MessageFilters
 *   filters={filters}
 *   onFilterChange={(key, value) => setFilters(prev => ({ ...prev, [key]: value }))}
 *   onClearFilters={() => setFilters({ activeForContext: null, isPinned: null, senderType: "all" })}
 * />
 * ```
 */
const MessageFilters = ({
  filters,
  onFilterChange,
  onClearFilters,
}: MessageFiltersProps) => {
  return (
    <HStack gap={4} p={4} borderRadius="md" flexWrap="wrap">
      <Text fontWeight="medium" fontSize="sm">
        Filters:
      </Text>

      {/* Active/Inactive Filter */}
      <NativeSelectRoot size="sm" maxW="200px">
        <NativeSelectField
          value={
            filters.activeForContext === null
              ? "all"
              : filters.activeForContext.toString()
          }
          onChange={(e: React.ChangeEvent<HTMLSelectElement>) => {
            const val = e.target.value
            onFilterChange(
              "activeForContext",
              val === "all" ? null : val === "true"
            )
          }}
        >
          <option value="all">All Messages</option>
          <option value="true">Active for Context</option>
          <option value="false">Inactive for Context</option>
        </NativeSelectField>
      </NativeSelectRoot>

      {/* Pinned Filter */}
      <NativeSelectRoot size="sm" maxW="180px">
        <NativeSelectField
          value={
            filters.isPinned === null ? "all" : filters.isPinned.toString()
          }
          onChange={(e: React.ChangeEvent<HTMLSelectElement>) => {
            const val = e.target.value
            onFilterChange("isPinned", val === "all" ? null : val === "true")
          }}
        >
          <option value="all">All / Pinned</option>
          <option value="true">Pinned Only</option>
          <option value="false">Unpinned Only</option>
        </NativeSelectField>
      </NativeSelectRoot>

      {/* Sender Type Filter */}
      <NativeSelectRoot size="sm" maxW="150px">
        <NativeSelectField
          value={filters.senderType}
          onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
            onFilterChange("senderType", e.target.value as "all" | "user" | "agent")
          }
        >
          <option value="all">All Senders</option>
          <option value="user">Users Only</option>
          <option value="agent">Agents Only</option>
        </NativeSelectField>
      </NativeSelectRoot>

      {/* Clear Filters Button */}
      <IconButton
        size="sm"
        aria-label="Clear filters"
        onClick={onClearFilters}
        variant="ghost"
      >
        <FaTimes />
      </IconButton>
    </HStack>
  )
}

export default MessageFilters
