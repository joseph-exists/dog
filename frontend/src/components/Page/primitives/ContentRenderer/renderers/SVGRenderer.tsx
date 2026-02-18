/**
 * SVGRenderer - SVG as inline element or img wrapper
 *
 * inline: true → <svg> directly (scripts can run if trusted)
 * inline: false → <img src="data:..."> (safe, no scripts)
 *
 * Variant defaults:
 * - background → inline: true
 * - others → inline: false (safer)
 */
import DOMPurify from "dompurify"
import type { ContentProps, SVGContentOptions } from "../types"

export function SVGRenderer({
  content,
  variant,
  safeMode = true,
  className,
}: ContentProps<"svg">) {
  const svg = typeof content.value === "string" ? content.value : ""
  const options = content.metadata?.options as SVGContentOptions | undefined

  // Determine inline mode - background defaults to inline
  const shouldInline = options?.inline ?? variant === "background"

  // If safe mode, force img wrapper regardless of options
  if (safeMode && shouldInline) {
    // Sanitize and convert to data URL
    const sanitized = DOMPurify.sanitize(svg)
    const dataUrl = `data:image/svg+xml,${encodeURIComponent(sanitized)}`

    return (
      <img
        src={dataUrl}
        alt="SVG content"
        className={`${variant === "background" ? "absolute inset-0 w-full h-full object-cover" : ""} ${className ?? ""}`}
      />
    )
  }

  // Inline SVG rendering
  if (shouldInline) {
    const sanitized = safeMode ? DOMPurify.sanitize(svg) : svg

    return (
      <div
        className={`${variant === "background" ? "absolute inset-0 [&>svg]:w-full [&>svg]:h-full" : ""} ${className ?? ""}`}
        dangerouslySetInnerHTML={{ __html: sanitized }}
      />
    )
  }

  // Default: img wrapper
  const dataUrl = `data:image/svg+xml,${encodeURIComponent(svg)}`
  return <img src={dataUrl} alt="SVG content" className={className} />
}
