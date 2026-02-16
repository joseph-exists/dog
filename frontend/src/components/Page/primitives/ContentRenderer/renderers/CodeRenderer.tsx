/**
 * CodeRenderer - Standalone code blocks with Shiki highlighting
 *
 * Full options: language, lineNumbers, highlightLines, startLine,
 * filename, copyable, theme
 */
import { CodeHighlight } from "../components/CodeHighlight"
import { useThemeResolution } from "../hooks/useThemeResolution"
import type { ContentProps, CodeContentOptions } from "../types"

export function CodeRenderer({ content, variant, className }: ContentProps<"code">) {
  const code = typeof content.value === "string" ? content.value : ""
  const options = content.metadata?.options as CodeContentOptions | undefined
  const { codeTheme } = useThemeResolution({ content })

  // Derive options with defaults
  const language = options?.language ?? "text"
  const copyable = options?.copyable ?? true
  const filename = options?.filename
  const lineNumbers = options?.lineNumbers ?? false
  const highlightLines = options?.highlightLines
  const startLine = options?.startLine


  // Background variant: code as decorative layer
  if (variant === "background") {
    return (
      <div
        className={`absolute inset-0 overflow-hidden opacity-10 pointer-events-none ${className ?? ""}`}
      >
        <CodeHighlight
          options={{ language, theme: codeTheme, forceBlock: true }}
        >
          {code}
        </CodeHighlight>
      </div>
    )
  }

  return (
    <div className={`relative ${className ?? ""}`}>
      {filename && (
        <div className="text-xs text-muted-foreground bg-muted px-3 py-1 rounded-t border-b border-border">
          {filename}
        </div>
      )}
      <CodeHighlight
        options={{
          language,
          theme: codeTheme,
          forceBlock: true,
          copyable,
          lineNumbers,
          highlightLines,
          startLine,
        }}
      >
        {code}
      </CodeHighlight>
    </div>
  )
}