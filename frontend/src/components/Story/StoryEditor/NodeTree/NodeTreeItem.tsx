/**
 * NodeTreeItem - Individual node in the tree view
 *
 * Features:
 * - Indentation based on tree level
 * - Expand/collapse toggle for nodes with children
 * - Icons based on node type (start/end/regular)
 * - Selection highlighting
 */

import { ChevronDown, ChevronRight, FileText, Flag, Trophy } from "lucide-react"
import type { StoryNodePublic } from "@/client"
import { cn } from "@/lib/utils"
import type { TreeNode } from "./treeUtils"

interface NodeTreeItemProps {
  treeNode: TreeNode
  isSelected: boolean
  onSelect: (nodeId: string) => void
  onToggle: (nodeId: string) => void
}

const NodeTreeItem = ({
  treeNode,
  isSelected,
  onSelect,
  onToggle,
}: NodeTreeItemProps) => {
  const { node, children, level, isExpanded } = treeNode
  const hasChildren = children.length > 0

  const getNodeIcon = (n: StoryNodePublic) => {
    if (n.is_start_node) return <Flag className="h-4 w-4 text-green-500" />
    if (n.is_end_node) return <Trophy className="h-4 w-4 text-blue-500" />
    return <FileText className="text-muted-foreground h-4 w-4" />
  }

  return (
    <div
      className={cn(
        "flex items-center gap-1 rounded-md px-2 py-1.5 text-sm transition-colors cursor-pointer",
        isSelected ? "bg-primary text-primary-foreground" : "hover:bg-muted",
      )}
      style={{ paddingLeft: `${8 + level * 16}px` }}
      onClick={() => onSelect(node.id)}
    >
      {/* Expand/Collapse Button */}
      {hasChildren ? (
        <button
          type="button"
          className="flex h-4 w-4 items-center justify-center rounded hover:bg-muted-foreground/20"
          onClick={(e) => {
            e.stopPropagation()
            onToggle(node.id)
          }}
        >
          {isExpanded ? (
            <ChevronDown className="h-3 w-3" />
          ) : (
            <ChevronRight className="h-3 w-3" />
          )}
        </button>
      ) : (
        <div className="w-4" /> // Spacer for alignment
      )}

      {/* Node Icon */}
      {getNodeIcon(node)}

      {/* Node Title */}
      <span className="truncate flex-1">{node.title || "Untitled"}</span>
    </div>
  )
}

export default NodeTreeItem
