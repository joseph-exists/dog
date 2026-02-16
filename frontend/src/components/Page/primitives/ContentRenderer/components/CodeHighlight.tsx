/**
 * CodeHighlight - Shiki-powered syntax highlighting
 *
 * Integration points:
 * - CodeRenderer: Direct code format
 * - MarkdownRenderer: Fenced code blocks via components.code
 * - MDXRenderer: Same pattern
 *  *
 * Supports:
 * - Line numbers (lineNumbers: true)
 * - Line highlighting (highlightLines: [1, 3, 5])
 * - Start line offset (startLine: 10)
 * - Custom transformers from @shikijs/transformers
 *
 * react-shiki's ShikiHighlighter accepts `transformers` prop via
 * CodeToHastOptions → TransformerOptions inheritance.
 */
import { ShikiHighlighter } from "react-shiki"
import { useMemo } from "react"
import type { CodeHighlightProps } from "../types"
import {
  transformerCompactLineOptions,
  type TransformerCompactLineOption,
} from "@shikijs/transformers"
import type { ShikiTransformer } from "@shikijs/types"


// Extract language from className like "language-typescript"
function extractLanguage(className?: string): string | undefined {
  if (!className) return undefined
  const match = className.match(/language-(\w+)/)
  return match?.[1]
}


/**
 * Create line numbers transformer
 * Adds data-line attribute for CSS-based line numbers
 */
function createLineNumbersTransformer(startLine: number = 1): ShikiTransformer {
  return {
    name: "line-numbers",
    line(node, line) {
      // Add line number as data attribute (1-indexed, adjusted for startLine)
      const lineNum = line + startLine - 1
      node.properties = node.properties || {}
      node.properties["data-line"] = lineNum
    },
    pre(node) {
      // Add class for CSS line numbers styling
      node.properties = node.properties || {}
      node.properties.className = node.properties.className || []
      if (Array.isArray(node.properties.className)) {
        node.properties.className.push("shiki-line-numbers")
      }
    },
  }
}

/**
 * Create line highlight transformer using @shikijs/transformers
 */
function createHighlightLinesTransformer(
  lines: number[]
): ShikiTransformer {
  const lineOptions: TransformerCompactLineOption[] = lines.map((line) => ({
    line,
    classes: ["shiki-highlighted"],
  }))
  return transformerCompactLineOptions(lineOptions)
}


export function CodeHighlight({
  className,
  children,
  options = {},
}: CodeHighlightProps) {
  const language = options.language ?? extractLanguage(className) ?? "text"
  const theme = options.theme ?? "github-dark"

  // Get code content as string
  const code =
    typeof children === "string"
      ? children
      : children?.toString?.() ?? ""

  // Inline detection: single line without explicit forceBlock
  const isInline = !options.forceBlock && !code.includes("\n")

  // Build transformers array
  const transformers = useMemo(() => {
    const result: ShikiTransformer[] = []

    // Add line numbers if requested
    if (options.lineNumbers) {
      result.push(createLineNumbersTransformer(options.startLine))
    }

    // Add line highlighting if requested (using @shikijs/transformers)
    if (options.highlightLines?.length) {
      result.push(createHighlightLinesTransformer(options.highlightLines))
    }

    // Add custom transformers
    if (options.transformers?.length) {
      result.push(...options.transformers)
    }

    return result
  }, [options.lineNumbers, options.startLine, options.highlightLines, options.transformers])

  if (isInline) {
    // Inline code: simple styled span
    return (
      <code className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono">
        {code}
      </code>
    )
  }

  // Block code: full Shiki highlighting with transformers
  return (
    <div className="relative group">
      <ShikiHighlighter
        language={language}
        theme={theme}
        transformers={transformers.length > 0 ? transformers : undefined}
      >
        {code.trim()}
      </ShikiHighlighter>
      {options.copyable && (
        <button
          type="button"
          className="absolute top-2 right-2 opacity-0 group-hover:opacity-100
                     transition-opacity text-xs bg-muted px-2 py-1 rounded"
          onClick={() => navigator.clipboard.writeText(code)}
        >
          Copy
        </button>
      )}
    </div>
  )
}