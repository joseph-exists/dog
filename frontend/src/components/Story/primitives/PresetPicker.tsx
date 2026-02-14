/**
 * PresetPicker Primitive
 *
 * Dropdown/button group for selecting layout presets.
 * Shows mini-previews of each preset option.
 *
 * @example
 * ```tsx
 * <PresetPicker
 *   presets={systemPresets}
 *   currentPresetId="collaborate"
 *   onSelect={(id) => applyPreset(id)}
 * />
 * ```
 */

import { motion } from "framer-motion"
import { Check, ChevronDown, Layout } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  getTransition,
  springConfig,
  useReduceMotion,
} from "@/components/ui/motion"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"
import { MiniPreview, type MiniPreviewPanel } from "./MiniPreview"

// ============================================================================
// Types
// ============================================================================

export interface Preset {
  id: string
  name: string
  description?: string
  panels: MiniPreviewPanel[]
}

export interface PresetPickerProps {
  /** Available presets */
  presets: Preset[]
  /** Currently selected preset ID (null if custom) */
  currentPresetId: string | null
  /** Called when a preset is selected */
  onSelect: (presetId: string) => void
  /** Display variant */
  variant?: "dropdown" | "buttons"
  /** Additional className */
  className?: string
}

// ============================================================================
// PresetButton Component (for button variant)
// ============================================================================

interface PresetButtonProps {
  preset: Preset
  isSelected: boolean
  onSelect: () => void
}

function PresetButton({ preset, isSelected, onSelect }: PresetButtonProps) {
  const reduceMotion = useReduceMotion()

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <motion.button
          type="button"
          onClick={onSelect}
          className={cn(
            "relative flex flex-col items-center gap-2 p-2 rounded-lg border transition-colors",
            isSelected
              ? "border-primary bg-primary/5"
              : "border-transparent hover:border-border hover:bg-muted/50",
          )}
          whileHover={{ scale: reduceMotion ? 1 : 1.02 }}
          whileTap={{ scale: reduceMotion ? 1 : 0.98 }}
          transition={getTransition(springConfig.snappy, reduceMotion)}
        >
          <MiniPreview
            panels={preset.panels}
            width={80}
            height={50}
            showLabels={false}
          />
          <span className="text-xs font-medium">{preset.name}</span>
          {isSelected && (
            <Check className="h-3 w-3 text-primary absolute top-1 right-1" />
          )}
        </motion.button>
      </TooltipTrigger>
      <TooltipContent>
        <p>{preset.description || preset.name}</p>
      </TooltipContent>
    </Tooltip>
  )
}

// ============================================================================
// PresetPicker Component
// ============================================================================

export function PresetPicker({
  presets,
  currentPresetId,
  onSelect,
  variant = "dropdown",
  className,
}: PresetPickerProps) {
  const currentPreset = presets.find((p) => p.id === currentPresetId)

  if (variant === "buttons") {
    return (
      <div className={cn("flex flex-wrap gap-2", className)}>
        {presets.map((preset) => (
          <PresetButton
            key={preset.id}
            preset={preset}
            isSelected={preset.id === currentPresetId}
            onSelect={() => onSelect(preset.id)}
          />
        ))}
      </div>
    )
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" className={cn("gap-2", className)}>
          <Layout className="h-4 w-4" />
          <span>{currentPreset?.name || "Custom"}</span>
          <ChevronDown className="h-4 w-4 opacity-50" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-64">
        {presets.map((preset) => (
          <DropdownMenuItem
            key={preset.id}
            onClick={() => onSelect(preset.id)}
            className="flex items-center gap-3 p-3"
          >
            <MiniPreview
              panels={preset.panels}
              width={60}
              height={40}
              showLabels={false}
            />
            <div className="flex-1 min-w-0">
              <p className="font-medium text-sm">{preset.name}</p>
              {preset.description && (
                <p className="text-xs text-muted-foreground truncate">
                  {preset.description}
                </p>
              )}
            </div>
            {preset.id === currentPresetId && (
              <Check className="h-4 w-4 text-primary shrink-0" />
            )}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

// ============================================================================
// System Presets (constant data)
// ============================================================================

export const SYSTEM_PRESETS: Preset[] = [
  {
    id: "story",
    name: "focused story",
    description: "",
    panels: [{ id: "player", kind: "storyPlayer", prominence: "primary" }],
  },
  {
    id: "reviewer",
    name: "review mode",
    description: "story with debug sidebar",
    panels: [
      { id: "player", kind: "storyPlayer", prominence: "primary" },
      { id: "debug", kind: "storyDebug", prominence: "auxiliary" }]
  },
  {
    id: "collaborate",
    name: "Collaborate",
    description: "Chat with agents sidebar",
    panels: [
      { id: "chat", kind: "chat", prominence: "primary" },
      { id: "participants", kind: "participantPanel", prominence: "auxiliary" },
    ],
  },
  {
    id: "story_mode",
    name: "Story Mode",
    description: "Story editor with chat",
    panels: [
      { id: "story", kind: "storyEditor", prominence: "primary" },
      { id: "chat", kind: "chat", prominence: "primary" },
      { id: "participants", kind: "participantPanel", prominence: "auxiliary" },
    ],
  },
  {
    id: "story_runtime",
    name: "Story Runtime",
    description: "Playthrough with runtime controls",
    panels: [
      { id: "runtime", kind: "storyRuntime", prominence: "primary" },
      { id: "chat", kind: "chat", prominence: "primary" },
      { id: "participants", kind: "participantPanel", prominence: "auxiliary" },
    ],
  },
  {
    id: "debug",
    name: "Debug",
    description: "Chat with debug info",
    panels: [
      { id: "chat", kind: "chat", prominence: "primary" },
      { id: "debug", kind: "debug", prominence: "auxiliary" },
      { id: "participants", kind: "participantPanel", prominence: "auxiliary" },
    ],
  },
  {
    id: "canvas",
    name: "Canvas",
    description: "Canvas with chat",
    panels: [
      { id: "canvas", kind: "canvas", prominence: "primary" },
      { id: "chat", kind: "chat", prominence: "primary" },
      { id: "participants", kind: "participantPanel", prominence: "auxiliary" },
    ],
  },
]
