/**
 * FallbackRenderer - Handles unsupported content formats
 *
 * Shows format type and raw value preview for debugging.
 */
import type { FallbackRendererProps } from "../types"

export function FallbackRenderer({ content }: FallbackRendererProps) {
  const valuePreview =
    typeof content.value === "string"
      ? content.value.slice(0, 200)
      : JSON.stringify(content.value).slice(0, 200)

  return (
    <div className="border border-amber-300 dark:border-amber-700 rounded-lg p-4 bg-amber-50 dark:bg-amber-950/30">
      <p className="text-sm text-amber-700 dark:text-amber-400 font-medium mb-2">
        Unsupported format: {content.format}
      </p>
      <pre className="text-xs text-muted-foreground overflow-auto max-h-32">
        {valuePreview}
        {valuePreview.length >= 200 && "..."}
      </pre>
    </div>
  )
}
