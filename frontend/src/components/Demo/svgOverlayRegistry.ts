/**
 * SVG Overlay Registry
 *
 * Provides a registry of SVG background patterns for demo presentation customization.
 * Patterns are stored as inline data URIs for zero-latency loading and offline support.
 *
 * ## Architecture Overview
 *
 * 1. **Registry** (this file)
 *    - Defines available SVG overlay presets
 *    - Stores SVG patterns as encoded data URIs
 *    - Provides lookup function for resolver integration
 *
 * 2. **Presentation Resolver** (demoPresentationResolver.ts)
 *    - Reads `backgrounds.svg_overlay` from presentation_json
 *    - Calls getSvgOverlayUrl() to get the data URI
 *    - Layers with page_gradient and card_pattern in backgroundImage
 *
 * 3. **Capability Registry** (demoBuilderCapabilityRegistry.ts)
 *    - Exposes svg_overlay as an enum field for demo builder UI
 *
 * ## Adding New Patterns
 *
 * 1. Create your SVG (keep it simple, tileable, low opacity)
 * 2. Add the raw SVG string as a constant below
 * 3. Add the preset name to SVG_OVERLAY_PRESETS
 * 4. Add the encoded URL to SVG_OVERLAY_REGISTRY
 * 5. Update capability registry enum values
 *
 * ## Design Guidelines
 *
 * - Use `currentColor` for strokes/fills so patterns adapt to themes
 * - Keep opacity low (6-12%) for subtle background texture
 * - Design for seamless tiling (edges should connect)
 * - Keep SVG simple to minimize bundle size (<1KB each)
 *
 * @see demoPresentationResolver.ts - Consumes this registry
 * @see demoBuilderCapabilityRegistry.ts - Exposes presets in builder UI
 */

// ============================================================================
// SVG PATTERN DEFINITIONS
// ============================================================================
//
// Each pattern is designed to be:
// - Subtle (low opacity)
// - Tileable (seamless repeating)
// - Theme-adaptive (uses currentColor)
// - Lightweight (simple paths)
//
// ============================================================================

/**
 * Grid Wave Pattern (v1)
 *
 * Horizontal wavy lines creating a subtle undulating grid effect.
 * Works well for tech/modern aesthetics.
 *
 * - Tile size: 60x30px
 * - Stroke opacity: 8%
 */
const GRID_WAVE_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="60" height="30" viewBox="0 0 60 30">
  <path d="M0 15 Q15 5 30 15 T60 15" fill="none" stroke="currentColor" stroke-opacity="0.08" stroke-width="1"/>
  <path d="M0 30 Q15 20 30 30 T60 30" fill="none" stroke="currentColor" stroke-opacity="0.05" stroke-width="0.5"/>
</svg>`

/**
 * Rings Grid Pattern (v2)
 *
 * Evenly spaced concentric circles creating a calm, organized feel.
 * Good for professional/clean designs.
 *
 * - Tile size: 40x40px
 * - Stroke opacity: 6%
 */
const RINGS_GRID_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 40 40">
  <circle cx="20" cy="20" r="12" fill="none" stroke="currentColor" stroke-opacity="0.06" stroke-width="1"/>
  <circle cx="20" cy="20" r="6" fill="none" stroke="currentColor" stroke-opacity="0.04" stroke-width="0.5"/>
</svg>`

/**
 * Constellation Dots Pattern (v1)
 *
 * Scattered dots with varying sizes and opacities, creating a starfield effect.
 * Great for dark backgrounds and space/tech themes.
 *
 * - Tile size: 80x80px
 * - Fill opacity: 6-10%
 */
const CONSTELLATION_DOTS_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80">
  <circle cx="10" cy="10" r="1.5" fill="currentColor" fill-opacity="0.1"/>
  <circle cx="50" cy="8" r="1" fill="currentColor" fill-opacity="0.06"/>
  <circle cx="75" cy="25" r="1.5" fill="currentColor" fill-opacity="0.08"/>
  <circle cx="25" cy="35" r="1" fill="currentColor" fill-opacity="0.06"/>
  <circle cx="60" cy="45" r="2" fill="currentColor" fill-opacity="0.1"/>
  <circle cx="5" cy="55" r="1" fill="currentColor" fill-opacity="0.06"/>
  <circle cx="40" cy="65" r="1.5" fill="currentColor" fill-opacity="0.08"/>
  <circle cx="70" cy="75" r="1" fill="currentColor" fill-opacity="0.06"/>
  <circle cx="20" cy="72" r="1.5" fill="currentColor" fill-opacity="0.08"/>
</svg>`

// ============================================================================
// REGISTRY EXPORTS
// ============================================================================

/**
 * Available SVG overlay preset names.
 *
 * Use these values in presentation_json.backgrounds.svg_overlay
 */
export const SVG_OVERLAY_PRESETS = [
  "grid-wave-v1",
  "rings-grid-v2",
  "constellation-dots-v1",
] as const

export type SvgOverlayPreset = (typeof SVG_OVERLAY_PRESETS)[number]

/**
 * Encodes an SVG string as a CSS url() data URI.
 *
 * Uses encodeURIComponent for safe embedding in CSS backgroundImage.
 *
 * @param svg - Raw SVG markup string
 * @returns CSS url() value with encoded data URI
 */
function encodeSvgAsUrl(svg: string): string {
  return `url("data:image/svg+xml,${encodeURIComponent(svg)}")`
}

/**
 * Registry mapping preset names to encoded CSS url() values.
 *
 * The URLs are pre-encoded at module load time for performance.
 */
const SVG_OVERLAY_REGISTRY: Record<SvgOverlayPreset, string> = {
  "grid-wave-v1": encodeSvgAsUrl(GRID_WAVE_SVG),
  "rings-grid-v2": encodeSvgAsUrl(RINGS_GRID_SVG),
  "constellation-dots-v1": encodeSvgAsUrl(CONSTELLATION_DOTS_SVG),
}

/**
 * Retrieves the CSS url() value for an SVG overlay preset.
 *
 * Returns undefined for unknown presets, allowing graceful fallback.
 *
 * @param preset - The preset name from presentation_json
 * @returns CSS url() value for backgroundImage, or undefined if not found
 *
 * @example
 * ```typescript
 * const url = getSvgOverlayUrl("grid-wave-v1")
 * // Returns: url("data:image/svg+xml,%3Csvg...")
 *
 * const unknown = getSvgOverlayUrl("invalid-preset")
 * // Returns: undefined
 * ```
 */
export function getSvgOverlayUrl(preset: string): string | undefined {
  return SVG_OVERLAY_REGISTRY[preset as SvgOverlayPreset]
}

/**
 * Checks if a string is a valid SVG overlay preset name.
 *
 * Useful for validation in presentation_json parsing.
 *
 * @param value - The value to check
 * @returns true if the value is a valid preset name
 */
export function isValidSvgOverlayPreset(
  value: unknown,
): value is SvgOverlayPreset {
  return (
    typeof value === "string" &&
    SVG_OVERLAY_PRESETS.includes(value as SvgOverlayPreset)
  )
}
