/**
 * Callout Style Presets
 *
 * Defines the visual treatment for each CalloutStylePreset. Each preset is
 * a combination of Tailwind classes that create a distinct visual style.
 *
 * ## Design Philosophy
 *
 * Presets are designed to be:
 * - **Self-contained**: Each preset provides complete styling
 * - **Composable**: Can be combined with customStyle for fine-tuning
 * - **Consistent**: Follow the demo theme system's visual language
 * - **Accessible**: Maintain sufficient contrast and readability
 *
 * ## Adding New Presets
 *
 * To add a new preset:
 * 1. Add the preset name to CalloutStylePreset type in types.ts
 * 2. Add the class string to CALLOUT_STYLE_PRESETS below
 * 3. Document the visual character and use case
 *
 * ## Preset Categories
 *
 * **Glassmorphism** (frosted, glass-pill)
 * - Semi-transparent backgrounds with backdrop blur
 * - Subtle borders for depth
 * - Best on dark or gradient backgrounds
 *
 * **High Contrast** (neon-frame, runtime-banner)
 * - Bold colors and/or glowing effects
 * - Commands attention
 * - Use sparingly to maintain hierarchy
 *
 * **Structural** (framed-note, status-pill)
 * - Defined borders and padding
 * - Clear visual boundaries
 * - Good for information callouts
 */
import type { CalloutStylePreset } from "./types"

/**
 * Tailwind class strings for each callout style preset.
 *
 * These classes are applied to the outer container of CalloutBanner.
 * The component adds additional base classes for layout (flex, items-center, etc.).
 */
export const CALLOUT_STYLE_PRESETS: Record<CalloutStylePreset, string> = {
  /**
   * Frosted glassmorphism style.
   *
   * Visual: Semi-transparent white background with backdrop blur,
   * subtle white border, rounded corners.
   *
   * Use for: General notices, preview indicators, non-critical info.
   * Best on: Dark backgrounds, gradients, images.
   */
  frosted: [
    "bg-white/10",
    "backdrop-blur-md",
    "border",
    "border-white/20",
    "rounded-lg",
    "text-white/90",
    "shadow-sm",
  ].join(" "),

  /**
   * Neon frame with glow effect.
   *
   * Visual: Cyan/teal border with outer glow, dark background,
   * high contrast text.
   *
   * Use for: Tech contexts, cyber themes, attention-grabbing notices.
   * Best on: Dark backgrounds, terminal/hacker aesthetics.
   */
  "neon-frame": [
    "bg-slate-900/80",
    "border-2",
    "border-cyan-400/60",
    "rounded-md",
    "text-cyan-100",
    "shadow-[0_0_15px_rgba(34,211,238,0.25)]",
  ].join(" "),

  /**
   * Frosted glass pill shape.
   *
   * Visual: Compact pill with glassmorphism, fully rounded ends.
   *
   * Use for: Compact status indicators, inline notices.
   * Best on: Any background, works as floating element.
   */
  "glass-pill": [
    "bg-white/15",
    "backdrop-blur-sm",
    "border",
    "border-white/25",
    "rounded-full",
    "text-white/90",
    "text-sm",
    "px-4",
    "py-1",
  ].join(" "),

  /**
   * Framed note card style.
   *
   * Visual: Solid background with left accent border, card-like appearance.
   *
   * Use for: Important information, documentation-style callouts.
   * Best on: Light or neutral backgrounds.
   */
  "framed-note": [
    "bg-slate-100",
    "dark:bg-slate-800",
    "border-l-4",
    "border-l-blue-500",
    "border",
    "border-slate-200",
    "dark:border-slate-700",
    "rounded-r-md",
    "text-slate-700",
    "dark:text-slate-200",
  ].join(" "),

  /**
   * Minimal status pill.
   *
   * Visual: Small, badge-like appearance with subtle background.
   *
   * Use for: Status indicators, labels, metadata display.
   * Best on: Any context where space is limited.
   */
  "status-pill": [
    "bg-slate-200/80",
    "dark:bg-slate-700/80",
    "rounded-full",
    "text-slate-600",
    "dark:text-slate-300",
    "text-xs",
    "font-medium",
    "px-3",
    "py-0.5",
  ].join(" "),

  /**
   * Full-width runtime banner.
   *
   * Visual: Prominent banner for system-level status messages,
   * gradient background, full width.
   *
   * Use for: Loading states, runtime notices, system messages.
   * Best on: Top of containers, should span full width.
   */
  "runtime-banner": [
    "bg-gradient-to-r",
    "from-indigo-500/90",
    "to-purple-500/90",
    "text-white",
    "font-medium",
    "rounded-md",
    "shadow-md",
    "shadow-indigo-500/20",
  ].join(" "),
}

/**
 * Default padding classes for callout presets.
 *
 * Some presets (glass-pill, status-pill) define their own padding.
 * This provides fallback padding for presets that don't.
 */
export const CALLOUT_DEFAULT_PADDING = "px-4 py-2"

/**
 * Presets that define their own padding and should skip default.
 */
export const CALLOUT_PRESETS_WITH_CUSTOM_PADDING: Set<CalloutStylePreset> =
  new Set(["glass-pill", "status-pill"])

/**
 * Gets the complete class string for a callout preset, including default padding.
 *
 * @param preset - The style preset name
 * @returns Combined class string with preset classes and appropriate padding
 */
export function getCalloutPresetClasses(preset: CalloutStylePreset): string {
  const presetClasses = CALLOUT_STYLE_PRESETS[preset]
  const needsDefaultPadding = !CALLOUT_PRESETS_WITH_CUSTOM_PADDING.has(preset)

  return needsDefaultPadding
    ? `${presetClasses} ${CALLOUT_DEFAULT_PADDING}`
    : presetClasses
}
