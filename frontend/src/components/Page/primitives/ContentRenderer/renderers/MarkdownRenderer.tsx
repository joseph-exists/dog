/**
 * MarkdownRenderer - Markdown with Shiki code highlighting
 *
 * Uses react-markdown with custom code component for Shiki integration.
 */
import ReactMarkdown from "react-markdown"
import { CodeHighlight } from "../components/CodeHighlight"
import { useThemeResolution } from "../hooks/useThemeResolution"
import type { ContentProps, MarkdownContentOptions } from "../types"

export function MarkdownRenderer({
  content,
  variant,
  className,
}: ContentProps<"markdown">) {
  const markdown = typeof content.value === "string" ? content.value : ""
  const { codeTheme, prose } = useThemeResolution({ content })
  // Options reserved for future use (e.g., readonly mode)
  const _options = content.metadata?.options as MarkdownContentOptions | undefined
  void _options // Suppress unused warning until implemented

  // Prose class based on variant and theme resolution
  const proseClass = prose && variant !== "inline"
    ? "prose prose-lg dark:prose-invert max-w-none"
    : ""

  return (
    <div className={`${proseClass} ${className ?? ""}`}>
      <ReactMarkdown
        components={{
          code({ className: codeClassName, children }) {
            // check if this is a code block with language class vs inline code
            const isBlock = codeClassName?.includes("language-")
            
            return (
              <CodeHighlight
                className={codeClassName}
                options={{ 
                  theme: codeTheme,
                  forceBlock: isBlock,
                  // enable line numbers for blocks by default in page variant
                  lineNumbers: isBlock && variant == "page",
                }}
              >
                {children}
              </CodeHighlight>
            )
          },
        }}
      >
        {markdown}
      </ReactMarkdown>
    </div>
  )
}