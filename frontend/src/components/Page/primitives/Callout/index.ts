/**
 * Callout Primitive
 *
 * A composable callout/banner system for displaying notices, status messages,
 * and contextual information. Designed for integration with the demo
 * presentation system but usable independently.
 *
 * ## Quick Start
 *
 * ```tsx
 * import { CalloutBanner, type CalloutConfig } from "@/components/Page/primitives/Callout"
 *
 * const config: CalloutConfig = {
 *   style: "frosted",
 *   text: "Preview Mode",
 *   icon: "eye",
 * }
 *
 * <CalloutBanner config={config} />
 * ```
 *
 * ## Available Presets
 *
 * - `frosted` - Glassmorphism style, good for dark backgrounds
 * - `neon-frame` - Glowing cyan border, cyber/tech aesthetic
 * - `glass-pill` - Compact frosted pill shape
 * - `framed-note` - Card-like with left accent border
 * - `status-pill` - Minimal badge style
 * - `runtime-banner` - Full-width gradient banner
 *
 * ## Integration with Demo System
 *
 * The callout system integrates with presentation_json through:
 * 1. demoPresentationResolver extracts callout configs
 * 2. DemoPresentationFrame renders CalloutBanner at appropriate slots
 *
 * @see CalloutBanner - The main rendering component
 * @see calloutStylePresets - Style definitions
 * @see types - TypeScript interfaces
 */

// Component exports
export { CalloutBanner, shouldRenderCallout } from "./CalloutBanner"

// Style preset exports
export {
  CALLOUT_DEFAULT_PADDING,
  CALLOUT_PRESETS_WITH_CUSTOM_PADDING,
  CALLOUT_STYLE_PRESETS,
  getCalloutPresetClasses,
} from "./calloutStylePresets"

// Type exports
export type {
  CalloutBannerProps,
  CalloutConfig,
  CalloutSlot,
  CalloutSlotMap,
  CalloutStylePreset,
} from "./types"
