/**
 * NodeDisplay
 *
 * Presents the current story node with formatted content.
 * Allows optional action slot and content renderer override.
 */

import DOMPurify from "dompurify"
import type { ReactNode } from "react"
import ReactMarkdown from "react-markdown"
import type { ContentFormat } from "@/client"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import type { NodeViewModel } from "@/services/roomRuntimeService"

interface NodeDisplayProps {
  node: NodeViewModel
  onNodeClick?: (node: NodeViewModel) => void
  actions?: ReactNode
  renderContent?: (content: string, format: ContentFormat | null) => ReactNode
  className?: string
}

function renderNodeContent(
  content: string,
  format: ContentFormat | null,
): ReactNode {
  switch (format) {
    case "html":
      return (
        <div
          className="prose max-w-none"
          dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(content) }}
        />
      )
    case "json":
      try {
        const parsed = content ? JSON.parse(content) : {}
        return (
          <pre className="rounded-md bg-muted px-3 py-2 text-xs font-mono whitespace-pre-wrap">
            {JSON.stringify(parsed, null, 2)}
          </pre>
        )
      } catch {
        return (
          <pre className="rounded-md bg-muted px-3 py-2 text-xs font-mono whitespace-pre-wrap text-destructive">
            Invalid JSON content
          </pre>
        )
      }
    case "markdown":
      return (
        <div className="prose max-w-none">
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
      )
    default:
      return <p className="whitespace-pre-wrap">{content}</p>
  }
}

export function NodeDisplay({
  node,
  onNodeClick,
  actions,
  renderContent,
  className,
}: NodeDisplayProps) {
  const contentRenderer = renderContent ?? renderNodeContent

  return (
    <div
      className={cn(
        "rounded-lg border bg-card p-4 shadow-sm space-y-3",
        onNodeClick && "cursor-pointer hover:border-primary/60",
        className,
      )}
      onClick={onNodeClick ? () => onNodeClick(node) : undefined}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold">{node.title}</h3>
          <div className="mt-1 flex flex-wrap items-center gap-2">
            {node.isStartNode && (
              <Badge variant="secondary" className="text-xs">
                Start
              </Badge>
            )}
            {node.isEndNode && (
              <Badge variant="default" className="text-xs">
                End
              </Badge>
            )}
          </div>
        </div>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>
      <div className="text-sm text-foreground/90">
        {contentRenderer(node.content, node.contentFormat)}
      </div>
    </div>
  )
}
