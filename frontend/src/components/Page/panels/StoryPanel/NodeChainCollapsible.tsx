/**
 * NodeChainCollapsible
 *
 * Collapsible list of node chain entries for operator context.
 */

import { ChevronDown, ChevronUp } from "lucide-react"
import { useMemo, useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { useIsMobile } from "@/hooks/use-mobile"
import { cn } from "@/lib/utils"
import type { NodeViewModel } from "@/services/roomRuntimeService"

interface NodeChainCollapsibleProps {
  nodes: NodeViewModel[]
  currentNodeId?: string | null
  onNodeClick?: (node: NodeViewModel) => void
}

export function NodeChainCollapsible({
  nodes,
  currentNodeId,
  onNodeClick,
}: NodeChainCollapsibleProps) {
  const isMobile = useIsMobile()
  const [open, setOpen] = useState(false)

  const visibleNodes = useMemo(() => {
    const limit = isMobile ? 5 : 12
    return nodes.slice(-limit)
  }, [nodes, isMobile])

  return (
    <Collapsible open={open} onOpenChange={setOpen} className="space-y-2">
      <CollapsibleTrigger asChild>
        <Button variant="ghost" className="w-full justify-between px-0">
          <span className="text-sm font-medium">
            Node Chain ({nodes.length})
          </span>
          {open ? (
            <ChevronUp className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
        </Button>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="demo-chain space-y-1 rounded-md border bg-muted/30 p-2">
          {visibleNodes.length === 0 ? (
            <p className="text-xs text-muted-foreground">
              No node history available.
            </p>
          ) : (
            visibleNodes.map((node) => (
              <button
                key={node.id}
                type="button"
                onClick={onNodeClick ? () => onNodeClick(node) : undefined}
                className={cn(
                  "w-full rounded-md px-2 py-1 text-left text-xs transition-colors",
                  node.id === currentNodeId
                    ? "demo-chain-active bg-primary/10 text-primary"
                    : "hover:bg-muted",
                  onNodeClick ? "cursor-pointer" : "cursor-default",
                )}
              >
                {node.title}
              </button>
            ))
          )}
        </div>
      </CollapsibleContent>
    </Collapsible>
  )
}
