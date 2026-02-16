/**
 * ImageRenderer - Image content with URL normalization
 *
 * URL normalization evolves during implementation (per spec).
 * Currently handles: external URLs, data URIs, relative paths.
 */
import type { ContentProps, ImageContentOptions } from "../types"

export function ImageRenderer({ content, variant, className }: ContentProps<"image">) {
  const src = typeof content.value === "string" ? content.value : ""
  const options = content.metadata?.options as ImageContentOptions | undefined

  const alt = options?.alt ?? "Image"
  const loading = options?.loading ?? "lazy"

  // Variant-specific styling
  const variantStyles: Record<string, string> = {
    inline: "inline max-h-6",
    thumbnail: "w-24 h-24 object-cover rounded",
    background: "absolute inset-0 w-full h-full object-cover",
    card: "w-full max-h-64 object-contain",
    page: "w-full max-h-96 object-contain",
    modal: "max-w-full max-h-[80vh] object-contain",
  }

  const style = variantStyles[variant ?? ""] ?? ""

  // Error handling: show placeholder if src is empty
  if (!src) {
    return (
      <div className={`bg-muted rounded flex items-center justify-center text-muted-foreground text-sm ${style} ${className ?? ""}`}>
        No image source
      </div>
    )
  }

  return (
    <img
      src={src}
      alt={alt}
      loading={loading}
      width={options?.width}
      height={options?.height}
      className={`${style} ${className ?? ""}`}
    />
  )
}