/**
 * Callout Type Definitions
 *
 * Types for the Callout primitive component system. Callouts are decorative
 * UI elements used to draw attention to information, display status messages,
 * or provide contextual notices within demo compositions.
 *
 * ## Architecture Overview
 *
 * Callouts integrate with the demo presentation system through three layers:
 *
 * 1. **Types (this file)** - Define the shape of callout configurations
 * 2. **Style Presets** - Map preset names to CSS classes/styles
 * 3. **CalloutBanner Component** - Renders the actual UI
 *
 * ## Usage Contexts
 *
 * Callouts can appear in two main contexts:
 *
 * 1. **Static Decorative** - Fixed notices like "This is a preview"
 * 2. **Runtime Informational** - Dynamic status like "Agent is thinking..."
 *
 * ## Integration with presentation_json
 *
 * Callouts are configured via presentation_json at composition, panel, or
 * block level:
 *
 * ```json
 * {
 *   "callouts": {
 *     "header": { "style": "frosted", "text": "Preview Mode", "icon": "eye" }
 *   }
 * }
 * ```
 *
 * The demoPresentationResolver extracts these configs and passes them to
 * DemoPresentationFrame, which renders CalloutBanner components.
 *
 * @see calloutStylePresets.ts - Style definitions for each preset
 * @see CalloutBanner.tsx - The rendering component
 * @see demoPresentationResolver.ts - Extracts callout config from presentation_json
 */

/**
 * Available callout style presets.
 *
 * Each preset maps to a distinct visual treatment defined in calloutStylePresets.ts.
 * Choose based on the callout's purpose and the surrounding visual context.
 *
 * | Preset | Use Case | Visual Character |
 * |--------|----------|------------------|
 * | frosted | General notices | Glassmorphism, subtle |
 * | neon-frame | Tech/cyber contexts | Glowing border, high contrast |
 * | glass-pill | Compact status | Rounded pill, frosted |
 * | framed-note | Important info | Card-like, structured |
 * | status-pill | Inline status | Minimal, badge-like |
 * | runtime-banner | System status | Full-width, prominent |
 */
export type CalloutStylePreset =
  | "frosted"
  | "neon-frame"
  | "glass-pill"
  | "framed-note"
  | "status-pill"
  | "runtime-banner"

/**
 * Available callout placement slots.
 *
 * Slots determine where the callout renders relative to its parent container
 * (panel or block). The DemoPresentationFrame component handles positioning
 * based on the slot value.
 *
 * @remarks
 * The "overlay" slot is reserved for future floating callout support and is
 * not yet implemented in DemoPresentationFrame.
 */
export type CalloutSlot =
  | "header" // Top of the container, before content
  | "footer" // Bottom of the container, after content
  | "overlay" // Floating over content (future implementation)

/**
 * Configuration for a single callout instance.
 *
 * This is the shape of callout data in presentation_json. The style field
 * is required; all others are optional with sensible defaults.
 *
 * @example
 * ```typescript
 * const previewCallout: CalloutConfig = {
 *   style: "frosted",
 *   text: "Preview Mode",
 *   icon: "eye",
 *   visible: true,
 * }
 * ```
 */
export interface CalloutConfig {
  /**
   * Visual style preset to apply.
   * Maps to CSS classes defined in calloutStylePresets.ts.
   */
  style: CalloutStylePreset

  /**
   * Text content to display in the callout.
   * If omitted, the callout renders with icon only (if provided).
   */
  text?: string

  /**
   * Lucide icon name to display before the text.
   * Must be a valid icon from the lucide-react package.
   *
   * @example "eye", "info", "alert-triangle", "sparkles"
   */
  icon?: string

  /**
   * Whether the callout is visible.
   * Defaults to true. Set to false for conditional display.
   *
   * @remarks
   * This enables runtime toggling without removing the config entirely.
   * Useful for callouts that appear/disappear based on state.
   */
  visible?: boolean
}

/**
 * Map of slot names to callout configurations.
 *
 * Used in presentation_json to specify callouts for multiple slots:
 *
 * ```json
 * {
 *   "callouts": {
 *     "header": { "style": "frosted", "text": "Preview" },
 *     "footer": { "style": "status-pill", "text": "Saved" }
 *   }
 * }
 * ```
 */
export type CalloutSlotMap = Partial<Record<CalloutSlot, CalloutConfig>>

/**
 * Props for the CalloutBanner component.
 *
 * @see CalloutBanner.tsx
 */
export interface CalloutBannerProps {
  /**
   * Callout configuration determining style, text, icon, and visibility.
   */
  config: CalloutConfig

  /**
   * Additional CSS classes to apply to the callout container.
   * Merged with preset classes via cn() utility.
   */
  className?: string

  /**
   * Inline styles to apply, typically from presentation_json tokens.
   * These override preset styles for fine-grained customization.
   *
   * @remarks
   * Use sparingly; prefer style presets for consistency.
   * This is primarily for presentation_json.callouts.*.css overrides.
   */
  customStyle?: React.CSSProperties
}
