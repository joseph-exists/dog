/**
 * Demo Presentation Resolver
 *
 * Resolves presentation_json configurations into React CSSProperties and frame
 * metadata for the demo presentation system. This module serves as the bridge
 * between declarative presentation_json schemas and runtime CSS application.
 *
 * ## Architecture
 *
 * The resolver follows a cascading inheritance model:
 * - Composition-level presentation_json provides defaults
 * - Panel-level presentation_json overrides composition settings
 * - Block-level presentation_json overrides panel settings
 *
 * Each level is resolved independently by DemoPresentationFrame, which applies
 * the styles to its content wrapper div.
 *
 * ## Supported Features
 *
 * | Category     | Fields                                           | Output               |
 * |--------------|--------------------------------------------------|----------------------|
 * | Motion       | panel_enter_ms, block_enter_ms, block_stagger_ms | transition + opacity |
 * | Typography   | size, line_height, heading_font, body_font       | fontSize, lineHeight, CSS vars |
 * | Backgrounds  | page_gradient, svg_overlay, card_pattern.css     | backgroundImage      |
 * | Effects      | card_glow.enable/css, message_row_highlight      | boxShadow            |
 * | Overlays     | panel_header.css, block_header.css               | header bar gradient  |
 * | CSS Vars     | tokens.*, theme_tokens.*, css_vars.*             | custom properties    |
 * | Callouts     | callouts.header, callouts.footer                 | CalloutConfig        |
 *
 * ## Font Resolution
 *
 * Font families are resolved into CSS custom properties:
 * - typography.heading_font → --font-heading
 * - typography.body_font → --font-body
 *
 * These properties are consumed by demo-themes.css rules and fall back to
 * var(--font-sans) when not specified. The actual font loading is handled
 * by DemoPresentationFrame's useFontLoader hook.
 *
 * ## Callout Resolution
 *
 * Callouts are decorative UI elements configured via presentation_json.callouts:
 * - callouts.header → CalloutConfig for top of container
 * - callouts.footer → CalloutConfig for bottom of container
 *
 * The resolved callout configs are passed to DemoPresentationFrame, which
 * renders CalloutBanner components at the appropriate positions.
 *
 * @see DemoPresentationFrame - Applies resolved styles, loads fonts, renders callouts
 * @see demoBuilderCapabilityRegistry - Defines available font/callout presets
 * @see Page/primitives/Callout - The CalloutBanner component
 */
import type React from "react"
import { getSvgOverlayUrl } from "@/components/Demo/svgOverlayRegistry"
import type {
  CalloutConfig,
  CalloutSlotMap,
} from "@/components/Page/primitives/Callout"
import type { ThemeViewModel } from "@/services/themeService"
import { themeTokensToStyle } from "@/services/themeService"

type TokenMap = Record<string, unknown>
type RecordValue = Record<string, unknown>

export type DemoPresentationScope = "composition" | "panel" | "block"

/**
 * Resolved presentation frame data ready for application by DemoPresentationFrame.
 *
 * @property style - CSS properties to apply to the frame wrapper
 * @property overlayCss - Optional CSS for the header overlay bar
 * @property motionMs - Optional enter animation duration in milliseconds
 * @property easing - Optional CSS easing function for animations
 * @property fontFamilies - Font family names that need to be loaded (non-system fonts)
 * @property callouts - Callout configurations by slot (header, footer)
 */
export interface ResolvedDemoPresentationFrame {
  style?: React.CSSProperties
  overlayCss?: string
  motionMs?: number
  easing?: string
  /** Font families that need dynamic loading (excludes "system") */
  fontFamilies?: string[]
  /** Callout configurations by slot position */
  callouts?: CalloutSlotMap
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value)
}

function getNestedString(
  source: unknown,
  ...path: string[]
): string | undefined {
  let cursor: unknown = source
  for (const segment of path) {
    if (!isRecord(cursor)) return undefined
    cursor = cursor[segment]
  }
  return typeof cursor === "string" && cursor.trim().length > 0
    ? cursor
    : undefined
}

function getNestedNumber(
  source: unknown,
  ...path: string[]
): number | undefined {
  let cursor: unknown = source
  for (const segment of path) {
    if (!isRecord(cursor)) return undefined
    cursor = cursor[segment]
  }
  return typeof cursor === "number" && Number.isFinite(cursor) && cursor > 0
    ? cursor
    : undefined
}

function getNestedBoolean(
  source: unknown,
  ...path: string[]
): boolean | undefined {
  let cursor: unknown = source
  for (const segment of path) {
    if (!isRecord(cursor)) return undefined
    cursor = cursor[segment]
  }
  return typeof cursor === "boolean" ? cursor : undefined
}

function toCustomPropTokenMap(value: unknown): TokenMap {
  if (!isRecord(value)) return {}
  const tokens: TokenMap = {}
  for (const [key, tokenValue] of Object.entries(value)) {
    if (!key.startsWith("--")) continue
    if (typeof tokenValue !== "string") continue
    tokens[key] = tokenValue
  }
  return tokens
}

export function extractPresentationTokens(presentationJson: unknown): TokenMap {
  if (!isRecord(presentationJson)) return {}
  const nestedTokens = toCustomPropTokenMap(presentationJson.tokens)
  const nestedThemeTokens = toCustomPropTokenMap(presentationJson.theme_tokens)
  const nestedCssVars = toCustomPropTokenMap(presentationJson.css_vars)
  const rootTokens = toCustomPropTokenMap(presentationJson)
  return {
    ...nestedTokens,
    ...nestedThemeTokens,
    ...nestedCssVars,
    ...rootTokens,
  }
}

export function buildDemoThemeIndex(
  ...themeGroups: ThemeViewModel[][]
): Map<string, ThemeViewModel> {
  const index = new Map<string, ThemeViewModel>()
  for (const group of themeGroups) {
    for (const theme of group) {
      if (!index.has(theme.id)) {
        index.set(theme.id, theme)
      }
    }
  }
  return index
}

export function resolveDemoPresentationStyle({
  themeId,
  presentationJson,
  themeIndex,
}: {
  themeId: string | null | undefined
  presentationJson: unknown
  themeIndex: Map<string, ThemeViewModel>
}): React.CSSProperties | undefined {
  const themedTokens =
    typeof themeId === "string" && themeId.trim().length > 0
      ? (themeIndex.get(themeId)?.tokens ?? {})
      : {}
  const presentationTokens = extractPresentationTokens(presentationJson)
  return themeTokensToStyle({
    ...themedTokens,
    ...presentationTokens,
  })
}

/**
 * Font family result containing style properties and font names to load.
 *
 * Separates the CSS custom property assignment from the font loading concern
 * to keep responsibilities clear between resolver and loader.
 */
interface FontResolutionResult {
  style: React.CSSProperties
  /** Non-system font families that need to be loaded via Google Fonts */
  fontFamilies: string[]
}

/**
 * Resolves typography.heading_font and typography.body_font into CSS custom properties.
 *
 * ## How It Works
 *
 * 1. Reads font values from presentation_json.typography
 * 2. Skips "system" values (use default font stack)
 * 3. Outputs CSS custom properties with fallback chain
 * 4. Collects non-system font names for dynamic loading
 *
 * ## CSS Custom Property Format
 *
 * The output follows this pattern:
 * ```css
 * --font-heading: "Space Grotesk", var(--font-sans);
 * --font-body: "Inter", var(--font-sans);
 * ```
 *
 * This ensures graceful fallback if the custom font fails to load.
 *
 * @param presentationJson - The presentation_json object to extract fonts from
 * @returns Object containing style properties and font families to load
 */
function resolveFontStyle(presentationJson: unknown): FontResolutionResult {
  const style: React.CSSProperties = {}
  const fontFamilies: string[] = []

  const headingFont = getNestedString(
    presentationJson,
    "typography",
    "heading_font",
  )
  const bodyFont = getNestedString(presentationJson, "typography", "body_font")

  // Heading font: applied to h1, h2, h3 via demo-themes.css
  if (headingFont && headingFont !== "system") {
    // Use CSS custom property for cascading inheritance
    // The font name is quoted to handle multi-word names like "Space Grotesk"
    // Fallback chain ensures text remains visible during font loading
    ;(style as Record<string, string>)["--font-heading"] =
      `"${headingFont}", var(--font-sans)`
    fontFamilies.push(headingFont)
  }

  // Body font: applied to p, span, li via demo-themes.css
  if (bodyFont && bodyFont !== "system") {
    ;(style as Record<string, string>)["--font-body"] =
      `"${bodyFont}", var(--font-sans)`
    // Avoid duplicate font loading if heading and body use same font
    if (!fontFamilies.includes(bodyFont)) {
      fontFamilies.push(bodyFont)
    }
  }

  return { style, fontFamilies }
}

/**
 * Resolves typography size and line height into CSS properties.
 *
 * Maps semantic size tokens (xs, sm, base, lg) to rem values and line height
 * tokens (tight, normal, relaxed) to numeric values.
 *
 * @param presentationJson - The presentation_json object to extract typography from
 * @returns CSS properties for fontSize and lineHeight
 */
function resolveTypographySizeStyle(
  presentationJson: unknown,
): React.CSSProperties {
  const typographySize = getNestedString(presentationJson, "typography", "size")
  const lineHeight = getNestedString(
    presentationJson,
    "typography",
    "line_height",
  )

  const style: React.CSSProperties = {}

  // Size tokens map to standard rem scale
  if (typographySize === "xs") style.fontSize = "0.75rem"
  if (typographySize === "sm") style.fontSize = "0.875rem"
  if (typographySize === "base") style.fontSize = "1rem"
  if (typographySize === "lg") style.fontSize = "1.125rem"

  // Line height tokens for readability control
  if (lineHeight === "tight") style.lineHeight = "1.25"
  if (lineHeight === "normal") style.lineHeight = "1.5"
  if (lineHeight === "relaxed") style.lineHeight = "1.65"

  return style
}

/**
 * Combined typography resolution (size + line height).
 *
 * @deprecated Prefer using resolveTypographySizeStyle and resolveFontStyle separately
 * for clearer separation of concerns. This function is maintained for backward
 * compatibility with existing code that calls resolveTypographyStyle directly.
 */
export function resolveTypographyStyle(
  presentationJson: unknown,
): React.CSSProperties {
  return resolveTypographySizeStyle(presentationJson)
}

function resolveEffectStyle(presentationJson: unknown): React.CSSProperties {
  const style: React.CSSProperties = {}
  const cardPatternCss = getNestedString(
    presentationJson,
    "backgrounds",
    "card_pattern",
    "css",
  )
  const pageGradientCss = getNestedString(
    presentationJson,
    "backgrounds",
    "page_gradient",
  )
  const svgOverlayPreset = getNestedString(
    presentationJson,
    "backgrounds",
    "svg_overlay",
  )
  const glowEnabled = getNestedBoolean(
    presentationJson,
    "effects",
    "card_glow",
    "enable",
  )
  const glowCss = getNestedString(
    presentationJson,
    "effects",
    "card_glow",
    "css",
  )

  // Resolve SVG overlay URL from preset name
  // Returns undefined for invalid/unknown presets (graceful fallback)
  const svgOverlayUrl = svgOverlayPreset
    ? getSvgOverlayUrl(svgOverlayPreset)
    : undefined

  // Build background layers in visual stacking order:
  // 1. page_gradient (top - most visible, typically solid colors/gradients)
  // 2. svg_overlay (middle - subtle texture patterns)
  // 3. card_pattern (bottom - base pattern layer)
  if (pageGradientCss || svgOverlayUrl || cardPatternCss) {
    const layers: string[] = []
    if (pageGradientCss) layers.push(pageGradientCss)
    if (svgOverlayUrl) layers.push(svgOverlayUrl)
    if (cardPatternCss) layers.push(cardPatternCss)
    style.backgroundImage = layers.join(", ")
  }
  if (glowCss) {
    style.boxShadow = glowCss
  } else if (glowEnabled) {
    style.boxShadow = "0 10px 28px rgba(15, 23, 42, 0.24)"
  }
  return style
}

function resolveOverlayCss(
  scope: DemoPresentationScope,
  presentationJson: unknown,
): string | undefined {
  if (scope === "panel") {
    return (
      getNestedString(presentationJson, "overlays", "panel_header", "css") ??
      getNestedString(presentationJson, "overlays", "header", "css")
    )
  }
  if (scope === "block") {
    return (
      getNestedString(presentationJson, "overlays", "block_header", "css") ??
      getNestedString(presentationJson, "overlays", "header", "css")
    )
  }
  return undefined
}

function resolveMotionMs(
  scope: DemoPresentationScope,
  presentationJson: unknown,
): number | undefined {
  if (scope === "panel") {
    return (
      getNestedNumber(presentationJson, "motion", "panel_enter_ms") ??
      getNestedNumber(presentationJson, "motion", "enter_ms")
    )
  }
  if (scope === "block") {
    return (
      getNestedNumber(presentationJson, "motion", "block_enter_ms") ??
      getNestedNumber(presentationJson, "motion", "block_stagger_ms") ??
      getNestedNumber(presentationJson, "motion", "enter_ms")
    )
  }
  return getNestedNumber(presentationJson, "motion", "panel_enter_ms")
}

// ============================================================================
// CALLOUT RESOLUTION
// ============================================================================

/**
 * Valid style preset names for callouts.
 *
 * Must match CalloutStylePreset type in Page/primitives/Callout/types.ts.
 * Used for validation during resolution.
 */
const VALID_CALLOUT_STYLES = new Set([
  "frosted",
  "neon-frame",
  "glass-pill",
  "framed-note",
  "status-pill",
  "runtime-banner",
])

/**
 * Valid slot names for callouts.
 *
 * Must match CalloutSlot type. The "overlay" slot is parsed but may not
 * be rendered by all frame implementations.
 */
const VALID_CALLOUT_SLOTS = new Set(["header", "footer", "overlay"])

/**
 * Type guard for CalloutConfig objects.
 *
 * Validates that a value conforms to the CalloutConfig shape:
 * - Must be an object
 * - Must have a valid style preset
 * - Optional text must be string if present
 * - Optional icon must be string if present
 * - Optional visible must be boolean if present
 *
 * @param value - The value to check
 * @returns true if value is a valid CalloutConfig
 */
function isValidCalloutConfig(value: unknown): value is CalloutConfig {
  if (!isRecord(value)) return false

  // Style is required and must be a valid preset
  const style = value.style
  if (typeof style !== "string" || !VALID_CALLOUT_STYLES.has(style)) {
    return false
  }

  // Optional fields must be correct type if present
  if (value.text !== undefined && typeof value.text !== "string") return false
  if (value.icon !== undefined && typeof value.icon !== "string") return false
  if (value.visible !== undefined && typeof value.visible !== "boolean")
    return false

  return true
}

/**
 * Resolves callout configurations from presentation_json.
 *
 * Extracts and validates callout configs from the callouts object:
 *
 * ```json
 * {
 *   "callouts": {
 *     "header": { "style": "frosted", "text": "Preview Mode", "icon": "eye" },
 *     "footer": { "style": "status-pill", "text": "Saved" }
 *   }
 * }
 * ```
 *
 * Invalid or malformed callout configs are silently skipped to prevent
 * rendering errors from bad data.
 *
 * @param presentationJson - The presentation_json object to extract callouts from
 * @returns CalloutSlotMap with validated callout configs, or undefined if none
 *
 * @example
 * ```typescript
 * const callouts = resolveCalloutConfigs(presentation_json)
 * // => { header: { style: "frosted", text: "Preview" } }
 * ```
 */
export function resolveCalloutConfigs(
  presentationJson: unknown,
): CalloutSlotMap | undefined {
  if (!isRecord(presentationJson)) return undefined

  const calloutsRaw = presentationJson.callouts
  if (!isRecord(calloutsRaw)) return undefined

  const resolved: CalloutSlotMap = {}
  let hasValidCallout = false

  // Iterate over known slots and extract valid configs
  for (const slot of VALID_CALLOUT_SLOTS) {
    const slotConfig = calloutsRaw[slot]
    if (isValidCalloutConfig(slotConfig)) {
      resolved[slot as keyof CalloutSlotMap] = slotConfig
      hasValidCallout = true
    }
  }

  // Return undefined if no valid callouts found (keeps frame object clean)
  return hasValidCallout ? resolved : undefined
}

/**
 * Resolves presentation_json into a complete frame configuration.
 *
 * This is the main entry point for presentation resolution. It combines:
 * - Theme-based tokens (from themeId lookup)
 * - Typography size and line height
 * - Font family CSS custom properties
 * - Background gradients and patterns
 * - Visual effects (glow, shadows)
 * - Motion/animation configuration
 * - Overlay bar styling
 * - Callout configurations for header/footer slots
 *
 * ## Usage
 *
 * ```typescript
 * const frame = resolveDemoPresentationFrame({
 *   scope: "panel",
 *   themeId: panel.theme_id,
 *   presentationJson: panel.presentation_json,
 *   themeIndex,
 * })
 *
 * // Apply via DemoPresentationFrame component
 * <DemoPresentationFrame frame={frame}>
 *   {children}
 * </DemoPresentationFrame>
 * ```
 *
 * @param scope - The hierarchy level: "composition", "panel", or "block"
 * @param themeId - Optional theme ID for token lookup
 * @param presentationJson - The presentation_json object to resolve
 * @param themeIndex - Map of theme IDs to ThemeViewModel for token lookup
 * @returns Resolved frame configuration ready for DemoPresentationFrame
 */
export function resolveDemoPresentationFrame({
  scope,
  themeId,
  presentationJson,
  themeIndex,
}: {
  scope: DemoPresentationScope
  themeId: string | null | undefined
  presentationJson: unknown
  themeIndex: Map<string, ThemeViewModel>
}): ResolvedDemoPresentationFrame {
  // Resolve theme tokens from themeId lookup
  const tokenStyle = resolveDemoPresentationStyle({
    themeId,
    presentationJson,
    themeIndex,
  })

  // Resolve typography: size, line height, and font families
  const typographySizeStyle = resolveTypographySizeStyle(presentationJson)
  const fontResolution = resolveFontStyle(presentationJson)

  // Resolve visual effects: backgrounds, shadows, glows
  const effectStyle = resolveEffectStyle(presentationJson)

  // Resolve callout configurations
  const callouts = resolveCalloutConfigs(presentationJson)

  // Merge all style sources (later sources override earlier)
  const style: RecordValue = {
    ...(tokenStyle ?? {}),
    ...typographySizeStyle,
    ...fontResolution.style,
    ...effectStyle,
  }

  return {
    style:
      Object.keys(style).length > 0
        ? (style as unknown as React.CSSProperties)
        : undefined,
    overlayCss: resolveOverlayCss(scope, presentationJson),
    motionMs: resolveMotionMs(scope, presentationJson),
    easing: getNestedString(presentationJson, "motion", "easing"),
    // Include font families for dynamic loading by DemoPresentationFrame
    fontFamilies:
      fontResolution.fontFamilies.length > 0
        ? fontResolution.fontFamilies
        : undefined,
    // Include callout configs for rendering by DemoPresentationFrame
    callouts,
  }
}
