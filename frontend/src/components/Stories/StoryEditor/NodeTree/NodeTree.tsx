/**
 * NodeTree - Hierarchical tree view of story nodes
 *
 * Features:
 * - Tree structure built from nodes/choices using adjacency map
 * - Expandable/collapsible nodes
 * - "Orphaned Nodes" section for unreachable nodes
 * - "Create Node" button
 * - Selection highlighting
 */

import { useState, useMemo } from "react"
import { Plus, FileText, AlertTriangle } from "lucide-react"
import type { NodeChoicePublic, StoryNodePublic } from "@/client"
import { Button } from "@/components/ui/button"
import NodeTreeItem from "./NodeTreeItem"
import CreateNodeModal from "../NodeEditor/CreateNodeModal"
import {
  buildNodeTree,
  flattenTree,
  toggleNodeExpansion,
  getOrphanedNodes,
  type TreeNode,
} from "./treeUtils"

interface NodeTreeProps {
  nodes: StoryNodePublic[]
  choices: NodeChoicePublic[]
  selectedNodeId: string | null
  onSelectNode: (nodeId: string) => void
  storyId: string
  storyVersion: number
}

const NodeTree = ({
  nodes,
  choices,
  selectedNodeId,
  onSelectNode,
  storyId,
  storyVersion,
}: NodeTreeProps) => {
  const [showCreateModal, setShowCreateModal] = useState(false)

  // Build initial tree from nodes and choices
  const initialTree = useMemo(
    () => buildNodeTree(nodes, choices),
    [nodes, choices]
  )

  // Manage tree state for expand/collapse
  const [tree, setTree] = useState<TreeNode | null>(initialTree)

  // Update tree when nodes/choices change
  useMemo(() => {
    setTree(buildNodeTree(nodes, choices))
  }, [nodes, choices])

  // Flatten tree for rendering
  const flatNodes = useMemo(() => flattenTree(tree), [tree])

  // Find orphaned nodes
  const orphanedNodes = useMemo(
    () => getOrphanedNodes(nodes, tree),
    [nodes, tree]
  )

  const handleToggle = (nodeId: string) => {
    setTree((prev) => toggleNodeExpansion(prev, nodeId))
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-border flex items-center justify-between border-b p-3">
        <h2 className="text-sm font-semibold">Nodes</h2>
        <Button
          size="sm"
          variant="ghost"
          className="h-7 w-7 p-0"
          onClick={() => setShowCreateModal(true)}
        >
          <Plus className="h-4 w-4" />
        </Button>
      </div>

      {/* Node List */}
      <div className="flex-1 overflow-y-auto p-2">
        {nodes.length === 0 ? (
          <div className="text-muted-foreground py-8 text-center text-sm">
            <FileText className="mx-auto mb-2 h-8 w-8 opacity-50" />
            <p>No nodes yet</p>
            <p className="text-xs">Create your first node to begin</p>
          </div>
        ) : (
          <div className="space-y-0.5">
            {/* Tree Nodes */}
            {flatNodes.map((treeNode) => (
              <NodeTreeItem
                key={treeNode.node.id}
                treeNode={treeNode}
                isSelected={selectedNodeId === treeNode.node.id}
                onSelect={onSelectNode}
                onToggle={handleToggle}
              />
            ))}

            {/* Orphaned Nodes Section */}
            {orphanedNodes.length > 0 && (
              <div className="mt-4 pt-4 border-t border-border">
                <div className="flex items-center gap-2 px-2 py-1 text-xs text-muted-foreground">
                  <AlertTriangle className="h-3 w-3" />
                  <span>Orphaned Nodes ({orphanedNodes.length})</span>
                </div>
                {orphanedNodes.map((node) => (
                  <button
                    type="button"
                    key={node.id}
                    className={`flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm transition-colors ${
                      selectedNodeId === node.id
                        ? "bg-primary text-primary-foreground"
                        : "hover:bg-muted text-muted-foreground"
                    }`}
                    onClick={() => onSelectNode(node.id)}
                  >
                    <div className="w-4" />
                    <FileText className="h-4 w-4 opacity-50" />
                    <span className="truncate">{node.title || "Untitled"}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Create Node Modal */}
      <CreateNodeModal
        open={showCreateModal}
        onOpenChange={setShowCreateModal}
        storyId={storyId}
        storyVersion={storyVersion}
        hasStartNode={nodes.some((n) => n.is_start_node)}
      />
    </div>
  )
}

export default NodeTree
