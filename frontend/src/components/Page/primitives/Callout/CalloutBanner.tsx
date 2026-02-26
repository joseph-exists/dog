/**
 * CalloutBanner Component
 *
 * A versatile callout/banner component for displaying notices, status messages,
 * and contextual information within demo compositions.
 *
 * ## Features
 *
 * - **Style Presets**: Six built-in visual styles (frosted, neon-frame, etc.)
 * - **Icon Support**: Optional Lucide icon display
 * - **Visibility Control**: Conditional rendering via config.visible
 * - **Custom Styling**: Override styles via customStyle prop
 * - **Accessible**: Proper ARIA attributes for decorative content
 *
 * ## Usage
 *
 * ```tsx
 * import { CalloutBanner } from "@/components/Page/primitives/Callout"
 *
 * // Basic usage
 * <CalloutBanner
 *   config={{ style: "frosted", text: "Preview Mode", icon: "eye" }}
 * />
 *
 * // With custom styling
 * <CalloutBanner
 *   config={{ style: "neon-frame", text: "Connected" }}
 *   customStyle={{ borderColor: "rgba(0, 255, 136, 0.5)" }}
 * />
 * ```
 *
 * ## Integration with Presentation System
 *
 * CalloutBanner is typically rendered by DemoPresentationFrame based on
 * callout configurations extracted from presentation_json:
 *
 * ```tsx
 * // In DemoPresentationFrame
 * {frame.callouts?.header && (
 *   <CalloutBanner config={frame.callouts.header} />
 * )}
 * ```
 *
 * @see types.ts - Type definitions
 * @see calloutStylePresets.ts - Style preset definitions
 * @see DemoPresentationFrame.tsx - Primary consumer
 */

import * as LucideIcons from "lucide-react"
import { useMemo } from "react"
import { cn } from "@/lib/utils"
import { getCalloutPresetClasses } from "./calloutStylePresets"
import type { CalloutBannerProps } from "./types"

/**
 * Maps icon name strings to Lucide icon components.
 *
 * Lucide exports icons in PascalCase (e.g., "AlertTriangle"), but users may
 * provide kebab-case or lowercase names in configs. This function handles
 * the normalization.
 *
 * @param iconName - Icon name from config (e.g., "eye", "alert-triangle", "Eye")
 * @returns The Lucide icon component, or undefined if not found
 */
function getLucideIcon(
  iconName: string,
): React.ComponentType<{ className?: string }> | undefined {
  // Normalize: "alert-triangle" -> "AlertTriangle"
  const pascalCase = iconName
    .split("-")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join("")

  // Also try exact match (user might provide "AlertTriangle" directly)
  // Cast through unknown to handle Lucide's complex ForwardRefExoticComponent type
  const icons = LucideIcons as unknown as Record<
    string,
    React.ComponentType<{ className?: string }>
  >

  return icons[pascalCase] ?? icons[iconName]
}

/**
 * Renders a callout banner with the specified configuration.
 *
 * The component applies style presets from calloutStylePresets.ts and renders
 * optional icon and text content. Visibility is controlled by config.visible.
 *
 * ## Styling Cascade
 *
 * Styles are applied in this order (later overrides earlier):
 * 1. Base layout classes (flex, items-center, gap)
 * 2. Preset classes from CALLOUT_STYLE_PRESETS
 * 3. className prop (for container context)
 * 4. customStyle prop (for presentation_json overrides)
 *
 * @param props - Component props including config, className, and customStyle
 * @returns The rendered callout banner, or null if config.visible is false
 */
export function CalloutBanner({
  config,
  className,
  customStyle,
}: CalloutBannerProps) {
  // Early return for hidden callouts
  if (config.visible === false) {
    return null
  }

  // Resolve icon component if specified
  const IconComponent = useMemo(() => {
    if (!config.icon) return null
    return getLucideIcon(config.icon)
  }, [config.icon])

  // Get preset classes (includes padding handling)
  const presetClasses = getCalloutPresetClasses(config.style)

  // Base layout classes for flex alignment
  const baseClasses = "flex items-center gap-2"

  return (
    <div
      className={cn(baseClasses, presetClasses, className)}
      style={customStyle}
      // Callouts are typically decorative/supplementary; mark appropriately
      role="status"
      aria-live="polite"
    >
      {/* Icon rendering */}
      {IconComponent && (
        <IconComponent className="h-4 w-4 flex-shrink-0" aria-hidden="true" />
      )}

      {/* Text content */}
      {config.text && <span className="truncate">{config.text}</span>}
    </div>
  )
}

/**
 * Utility to check if a callout config should render.
 *
 * Useful for conditional rendering logic outside of CalloutBanner itself.
 *
 * @param config - The callout config to check, or undefined/null
 * @returns true if the callout should render (config exists and visible !== false)
 *
 * @example
 * ```tsx
 * {shouldRenderCallout(frame.callouts?.header) && (
 *   <CalloutBanner config={frame.callouts.header} />
 * )}
 * ```
 */
export function shouldRenderCallout(
  config: CalloutBannerProps["config"] | undefined | null,
): config is CalloutBannerProps["config"] {
  if (!config) return false
  return config.visible !== false
}
