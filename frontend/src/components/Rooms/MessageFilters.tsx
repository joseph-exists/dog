/**
 * MessageFilters Component
 *
 * Filter controls for message list:
 * - Active/Inactive for context
 * - Pinned/Unpinned
 * - Sender type (all/users/agents)
 *
 * Client-side filtering with instant updates.
 */

import { X } from "lucide-react"
import { Button } from "@/components/ui/button"

export interface MessageFilters {
  /** null = show all, true = active only, false = inactive only */
  activeForContext: boolean | null
  /** null = show all, true = pinned only, false = unpinned only */
  isPinned: boolean | null
  /** Filter by sender type */
  senderType: "all" | "user" | "agent"
}

interface MessageFiltersProps {
  filters: MessageFilters
  onFilterChange: <K extends keyof MessageFilters>(
    key: K,
    value: MessageFilters[K],
  ) => void
  onClearFilters: () => void
}

const selectClassName =
  "h-8 rounded-md border border-input bg-transparent px-2 text-sm shadow-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"

export default function MessageFilters({
  filters,
  onFilterChange,
  onClearFilters,
}: MessageFiltersProps) {
  return (
    <div className="flex items-center gap-4 p-4 flex-wrap">
      <span className="font-medium text-sm">Filters:</span>

      {/* Active/Inactive Filter */}
      <select
        className={`${selectClassName} max-w-[200px]`}
        value={
          filters.activeForContext === null
            ? "all"
            : filters.activeForContext.toString()
        }
        onChange={(e) => {
          const val = e.target.value
          onFilterChange(
            "activeForContext",
            val === "all" ? null : val === "true",
          )
        }}
      >
        <option value="all">All Messages</option>
        <option value="true">Active for Context</option>
        <option value="false">Inactive for Context</option>
      </select>

      {/* Pinned Filter */}
      <select
        className={`${selectClassName} max-w-[180px]`}
        value={filters.isPinned === null ? "all" : filters.isPinned.toString()}
        onChange={(e) => {
          const val = e.target.value
          onFilterChange("isPinned", val === "all" ? null : val === "true")
        }}
      >
        <option value="all">All / Pinned</option>
        <option value="true">Pinned Only</option>
        <option value="false">Unpinned Only</option>
      </select>

      {/* Sender Type Filter */}
      <select
        className={`${selectClassName} max-w-[150px]`}
        value={filters.senderType}
        onChange={(e) =>
          onFilterChange(
            "senderType",
            e.target.value as "all" | "user" | "agent",
          )
        }
      >
        <option value="all">All Senders</option>
        <option value="user">Users Only</option>
        <option value="agent">Agents Only</option>
      </select>

      {/* Clear Filters Button */}
      <Button
        size="icon-sm"
        variant="ghost"
        onClick={onClearFilters}
        aria-label="Clear filters"
      >
        <X className="h-4 w-4" />
      </Button>
    </div>
  )
}
