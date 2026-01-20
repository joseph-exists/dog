/**
 * LayoutSourceSelector Component
 *
 * Radio group for selecting layout source (room default, user default, custom).
 * Shows current source and allows switching.
 *
 * @example
 * ```tsx
 * <LayoutSourceSelector
 *   currentSource="user_defaults"
 *   onSourceChange={(source) => handleSourceChange(source)}
 *   isRoomOwner={false}
 * />
 * ```
 */

import { Link } from "@tanstack/react-router"
import { ExternalLink } from "lucide-react"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { cn } from "@/lib/utils"

// ============================================================================
// Types
// ============================================================================

export type LayoutSource =
  | "room_override"
  | "room_defaults"
  | "user_defaults"
  | "system_defaults"
  | "custom"

export interface LayoutSourceSelectorProps {
  /** Current source of the layout */
  currentSource: LayoutSource
  /** Called when source selection changes */
  onSourceChange: (source: LayoutSource) => void
  /** Whether the current user is the room owner */
  isRoomOwner: boolean
  /** Whether room has custom defaults set */
  hasRoomDefaults: boolean
  /** Additional className */
  className?: string
}

// ============================================================================
// Source Labels
// ============================================================================

const sourceLabels: Record<LayoutSource, string> = {
  room_override: "Custom for this room",
  room_defaults: "Room default",
  user_defaults: "My default",
  system_defaults: "System default",
  custom: "Custom for this room",
}

const sourceDescriptions: Record<LayoutSource, string> = {
  room_override: "Your personal layout for this room",
  room_defaults: "Layout set by the room owner",
  user_defaults: "Your default layout for all rooms",
  system_defaults: "Standard layout",
  custom: "Your personal layout for this room",
}

// ============================================================================
// Component
// ============================================================================

export function LayoutSourceSelector({
  currentSource,
  onSourceChange,
  hasRoomDefaults,
  className,
}: LayoutSourceSelectorProps) {
  // Normalize source for radio selection
  const selectedValue =
    currentSource === "room_override" ? "custom" : currentSource

  const handleChange = (value: string) => {
    onSourceChange(value as LayoutSource)
  }

  return (
    <div className={cn("space-y-3", className)}>
      {/* Current source indicator */}
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">Currently using:</span>
        <span className="font-medium">{sourceLabels[currentSource]}</span>
      </div>

      {/* Source selector */}
      <RadioGroup
        value={selectedValue}
        onValueChange={handleChange}
        className="grid gap-2"
      >
        {/* Room default option */}
        {hasRoomDefaults && (
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="room_defaults" id="source-room" />
            <Label htmlFor="source-room" className="flex-1 cursor-pointer">
              <span>{sourceLabels.room_defaults}</span>
              <span className="text-xs text-muted-foreground ml-2">
                {sourceDescriptions.room_defaults}
              </span>
            </Label>
          </div>
        )}

        {/* User default option */}
        <div className="flex items-center space-x-2">
          <RadioGroupItem value="user_defaults" id="source-user" />
          <Label htmlFor="source-user" className="flex-1 cursor-pointer">
            <span>{sourceLabels.user_defaults}</span>
            <span className="text-xs text-muted-foreground ml-2">
              {sourceDescriptions.user_defaults}
            </span>
          </Label>
          <Link
            to="/settings"
            className="text-xs text-primary hover:underline flex items-center gap-1"
          >
            Edit <ExternalLink className="h-3 w-3" />
          </Link>
        </div>

        {/* Custom option */}
        <div className="flex items-center space-x-2">
          <RadioGroupItem value="custom" id="source-custom" />
          <Label htmlFor="source-custom" className="flex-1 cursor-pointer">
            <span>{sourceLabels.custom}</span>
            <span className="text-xs text-muted-foreground ml-2">
              {sourceDescriptions.custom}
            </span>
          </Label>
        </div>
      </RadioGroup>
    </div>
  )
}
