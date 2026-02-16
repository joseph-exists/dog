/**
 * HTMLRenderer - HTML content with DOMPurify sanitization
 *
 * safeMode: true → aggressive sanitization
 * safeMode: false + trusted → minimal sanitization
 */
import DOMPurify from "dompurify"
import type { ContentProps, HTMLContentOptions } from "../types"

export function HTMLRenderer({
  content,
  variant,
  safeMode = true,
  className,
}: ContentProps<"html">) {
  const html = typeof content.value === "string" ? content.value : ""
  const options = content.metadata?.options as HTMLContentOptions | undefined

  // Determine sanitization level
  const shouldSanitize = safeMode || options?.sanitize !== false
  const sanitizedHtml = shouldSanitize
    ? DOMPurify.sanitize(html, options?.sanitizerConfig ?? {})
    : html

  // Variant-specific wrapper
  const variantClass = variant === "inline" ? "inline" : ""
  const proseClass = variant !== "inline" ? "prose prose-lg dark:prose-invert max-w-none" : ""

  return (
    <div
      className={`${proseClass} ${variantClass} ${className ?? ""}`}
      dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
    />
  )
}