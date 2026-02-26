/**
 * Demo Presentation Frame
 *
 * A wrapper component that applies resolved presentation styles to demo content.
 * Handles CSS property application, enter animations, overlay bars, dynamic
 * font loading, and callout rendering.
 *
 * ## Key Responsibilities
 *
 * 1. **Style Application**: Applies resolved CSS properties from demoPresentationResolver
 * 2. **Enter Animation**: Fade-in + slide-up animation controlled by motionMs
 * 3. **Overlay Bar**: Optional header gradient bar for visual hierarchy
 * 4. **Font Loading**: Dynamically loads Google Fonts when custom fonts are specified
 * 5. **Callout Rendering**: Displays CalloutBanner components at header/footer slots
 *
 * ## Font Loading Strategy
 *
 * When frame.fontFamilies contains font names, the useFontLoader hook injects
 * Google Fonts <link> tags into document.head. Key characteristics:
 *
 * - **Deduplication**: Fonts are only loaded once per page, tracked via data attributes
 * - **Lazy Loading**: Fonts load on-demand when first used in a frame
 * - **Cleanup**: Font links persist for the page lifetime (no cleanup on unmount)
 *   to avoid re-fetching when components remount
 * - **Fallback**: CSS uses var(--font-sans) fallback during load (font-display: swap)
 *
 * ## Callout Rendering
 *
 * When frame.callouts contains configurations, CalloutBanner components are
 * rendered at the appropriate slots:
 *
 * - **header**: Rendered before the main content
 * - **footer**: Rendered after the main content
 *
 * Callouts are configured via presentation_json.callouts and resolved by
 * demoPresentationResolver. The CalloutBanner component from Page/primitives
 * handles the actual rendering with style presets.
 *
 * ## Usage
 *
 * ```tsx
 * const frame = resolveDemoPresentationFrame({
 *   scope: "panel",
 *   themeId: panel.theme_id,
 *   presentationJson: panel.presentation_json,
 *   themeIndex,
 * })
 *
 * <DemoPresentationFrame frame={frame} className="h-full">
 *   <PanelContent />
 * </DemoPresentationFrame>
 * ```
 *
 * @see resolveDemoPresentationFrame - Creates frame configuration
 * @see demo-themes.css - Consumes --font-heading and --font-body variables
 * @see Page/primitives/Callout - CalloutBanner component
 */

import type React from "react"
import { useEffect, useMemo, useState } from "react"
import type { ResolvedDemoPresentationFrame } from "@/components/Demo/demoPresentationResolver"
import {
  CalloutBanner,
  shouldRenderCallout,
} from "@/components/Page/primitives/Callout"
import { cn } from "@/lib/utils"

// ============================================================================
// FONT LOADING SYSTEM
// ============================================================================
//
// The font loader dynamically injects Google Fonts CSS when custom fonts are
// used in presentation_json. This approach was chosen over:
//
// 1. Pre-loading all fonts in index.html
//    - Pros: No FOUT, faster subsequent loads
//    - Cons: Loads unused fonts, larger initial bundle
//
// 2. Using @font-face with local files
//    - Pros: Full control, no external dependency
//    - Cons: Requires bundling fonts, license complexity
//
// 3. CSS @import in stylesheets
//    - Pros: Simple, declarative
//    - Cons: Blocks rendering, can't be conditional
//
// The dynamic approach balances flexibility (any Google Font) with efficiency
// (only load what's used) while accepting a brief FOUT on first use.
//
// ============================================================================

/**
 * Formats a font family name for Google Fonts URL.
 *
 * Google Fonts expects spaces to be replaced with '+' in URLs.
 * Example: "Space Grotesk" → "Space+Grotesk"
 *
 * @param fontFamily - The font family name as specified in presentation_json
 * @returns URL-encoded font family name for Google Fonts API
 */
function formatGoogleFontFamily(fontFamily: string): string {
  return fontFamily.trim().replace(/\s+/g, "+")
}

/**
 * Generates a Google Fonts CSS URL for a given font family.
 *
 * Uses CSS2 API with display=swap for optimal loading behavior:
 * - Text renders immediately with fallback font
 * - Custom font swaps in when loaded
 * - Prevents invisible text during load
 *
 * @param fontFamily - The font family name
 * @returns Complete Google Fonts CSS URL
 */
function buildGoogleFontsUrl(fontFamily: string): string {
  const encodedFamily = formatGoogleFontFamily(fontFamily)
  // Include common weights: 400 (regular), 500 (medium), 600 (semibold), 700 (bold)
  // This covers typical heading and body text needs
  return `https://fonts.googleapis.com/css2?family=${encodedFamily}:wght@400;500;600;700&display=swap`
}

/**
 * Hook to dynamically load Google Fonts.
 *
 * Injects <link> elements for each font family, with deduplication to prevent
 * multiple loads of the same font. Uses data attributes for tracking.
 *
 * ## Implementation Notes
 *
 * - Links are injected into document.head
 * - Data attribute `data-demo-font="FontName"` prevents duplicates
 * - Links persist after unmount to cache fonts across navigation
 * - No error handling: browser handles 404s gracefully
 *
 * @param fontFamilies - Array of font family names to load (excludes "system")
 *
 * @example
 * ```tsx
 * useFontLoader(["Space Grotesk", "Inter"])
 * // Injects:
 * // <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap" data-demo-font="Space Grotesk" />
 * // <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" data-demo-font="Inter" />
 * ```
 */
function useFontLoader(fontFamilies: string[] | undefined): void {
  useEffect(() => {
    if (!fontFamilies || fontFamilies.length === 0) return

    for (const fontFamily of fontFamilies) {
      // Skip if already loaded (check by data attribute)
      const existingLink = document.querySelector(
        `link[data-demo-font="${fontFamily}"]`,
      )
      if (existingLink) continue

      // Create and inject the stylesheet link
      const link = document.createElement("link")
      link.rel = "stylesheet"
      link.href = buildGoogleFontsUrl(fontFamily)
      link.dataset.demoFont = fontFamily

      // Add to head (appending ensures it doesn't block initial render)
      document.head.appendChild(link)

      // Optional: Log in development for debugging font issues
      if (process.env.NODE_ENV === "development") {
        console.debug(`[DemoPresentationFrame] Loading font: ${fontFamily}`)
      }
    }

    // No cleanup: fonts persist to avoid re-fetching on remount
    // This is intentional - fonts are a page-level resource
  }, [fontFamilies])
}

interface DemoPresentationFrameProps {
  /** Resolved presentation configuration from demoPresentationResolver */
  frame: ResolvedDemoPresentationFrame
  /** Additional classes for the outer wrapper div */
  className?: string
  /** Additional classes for the content container div */
  contentClassName?: string
  /** Content to render within the presentation frame */
  children: React.ReactNode
}

/**
 * Presentation frame component that applies resolved styles and handles animations.
 *
 * Wraps content in two divs:
 * 1. Outer div: Receives all resolved styles (backgrounds, fonts, effects, animation)
 * 2. Inner div: Contains actual content with z-index layering for overlay bar
 *
 * The overlay bar (when present) renders as a thin gradient strip at the top of
 * the frame, useful for visual hierarchy indicators.
 */
export function DemoPresentationFrame({
  frame,
  className,
  contentClassName,
  children,
}: DemoPresentationFrameProps) {
  // Animation state: starts false when motionMs is defined, triggers enter animation
  const [entered, setEntered] = useState(frame.motionMs === undefined)

  // Load fonts when frame specifies custom font families
  useFontLoader(frame.fontFamilies)

  // Trigger enter animation when frame configuration changes
  useEffect(() => {
    if (frame.motionMs === undefined) return
    setEntered(false)
    // Use requestAnimationFrame to ensure DOM has painted before animating
    const id = window.requestAnimationFrame(() => setEntered(true))
    return () => window.cancelAnimationFrame(id)
  }, [frame.motionMs])

  // Compute final style with animation properties when applicable
  const animatedStyle = useMemo(() => {
    const style: React.CSSProperties = {
      ...(frame.style ?? {}),
    }

    // Apply enter animation when motionMs is specified
    if (frame.motionMs !== undefined) {
      const easing = frame.easing ?? "ease-out"
      style.transition = `opacity ${frame.motionMs}ms ${easing}, transform ${frame.motionMs}ms ${easing}`
      style.opacity = entered ? 1 : 0
      style.transform = entered ? "translateY(0)" : "translateY(4px)"
    }

    return Object.keys(style).length > 0 ? style : undefined
  }, [entered, frame.easing, frame.motionMs, frame.style])

  return (
    <div className={cn("relative", className)} style={animatedStyle}>
      {/* Overlay bar: decorative header gradient when specified */}
      {frame.overlayCss && (
        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 top-0 z-10 h-1.5"
          style={{ background: frame.overlayCss }}
        />
      )}

      {/* Header callout: rendered before main content when configured */}
      {shouldRenderCallout(frame.callouts?.header) && (
        <CalloutBanner config={frame.callouts.header} className="mb-2" />
      )}

      {/* Content container: z-20 ensures content renders above overlay bar */}
      <div className={cn("relative z-20", contentClassName)}>{children}</div>

      {/* Footer callout: rendered after main content when configured */}
      {shouldRenderCallout(frame.callouts?.footer) && (
        <CalloutBanner config={frame.callouts.footer} className="mt-2" />
      )}
    </div>
  )
}
