/**
 * NodeDisplay
 *
 * Presents the current story node with formatted content.
 * Uses ContentRenderer for all format rendering.
 */
import type { ReactNode } from "react";
import type { ContentFormat } from "@/client";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { NodeViewModel } from "@/services/roomRuntimeService";
import {
  ContentRenderer,
  toContent,
} from "@/components/Common/ContentRenderer";

interface NodeDisplayProps {
  node: NodeViewModel;
  onNodeClick?: (node: NodeViewModel) => void;
  actions?: ReactNode;
  /** @deprecated Custom renderers should use ContentRenderer directly */
  renderContent?: (content: string, format: ContentFormat | null) => ReactNode;
  className?: string;
}

/**
 * Default content renderer using ContentRenderer
 */
function defaultRenderContent(
  content: string,
  format: ContentFormat | null,
): ReactNode {
  return (
    <ContentRenderer
      content={toContent(content, format, "card")}
      safeMode={true}
    />
  );
}

export function NodeDisplay({
  node,
  onNodeClick,
  actions,
  renderContent,
  className,
}: NodeDisplayProps) {
  // Use custom renderer if provided, otherwise use ContentRenderer
  const contentRenderer = renderContent ?? defaultRenderContent;

  return (
    <div
      className={cn(
        "demo-node rounded-lg border bg-card p-4 shadow-sm space-y-3",
        onNodeClick && "cursor-pointer hover:border-primary/60",
        className,
      )}
      onClick={onNodeClick ? () => onNodeClick(node) : undefined}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="demo-node-title text-lg font-semibold">
            {node.title}
          </h3>
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
      <div className="demo-node-content text-sm text-foreground/90">
        {contentRenderer(node.content, node.contentFormat)}
      </div>
    </div>
  );
}
