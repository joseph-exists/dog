/**
 * JSONRenderer - JSON with text or tree view modes
 *
 * viewMode: "text" → formatted JSON string
 * viewMode: "tree" → interactive collapsible tree (Phase 2: use library)
 */
// TODO: review existing JSON renderer for jsontree.

// import { useState } from "react"

import type { ContentProps, JSONContentOptions } from "../types"

export function JSONRenderer({
  content,
  variant,
  className,
}: ContentProps<"json">) {
  const options = content.metadata?.options as JSONContentOptions | undefined
  const viewMode = options?.viewMode ?? "text"

  // Parse JSON value
  let parsed: unknown
  let parseError: string | null = null

  try {
    parsed =
      typeof content.value === "string"
        ? JSON.parse(content.value)
        : content.value
  } catch (e) {
    parseError = e instanceof Error ? e.message : "Invalid JSON"
  }

  if (parseError) {
    return (
      <div className={`text-destructive ${className ?? ""}`}>
        <p className="font-medium">Invalid JSON</p>
        <p className="text-sm">{parseError}</p>
      </div>
    )
  }

  // Text mode: formatted JSON
  if (viewMode === "text") {
    return (
      <div className={className}>
        {variant !== "inline" && (
          <p className="text-sm text-muted-foreground italic mb-2">[JSON]</p>
        )}
        <pre className="bg-muted p-4 rounded-md overflow-auto text-sm font-mono">
          {JSON.stringify(parsed, null, 2)}
        </pre>
      </div>
    )
  }

  // Tree mode: collapsible (basic implementation)
  // TODO: Replace with json-tree library in Phase 2 for full interactivity
  return (
    <div className={className}>
      <p className="text-sm text-muted-foreground italic mb-2">
        [JSON Tree - Interactive mode coming soon]
      </p>
      <pre className="bg-muted p-4 rounded-md overflow-auto text-sm font-mono">
        {JSON.stringify(parsed, null, 2)}
      </pre>
    </div>
  )
}
