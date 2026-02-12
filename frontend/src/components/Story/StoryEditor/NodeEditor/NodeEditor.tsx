/**
 * NodeEditor - Editor panel for selected story node
 *
 * Features:
 * - Node header with title and type badges
 * - NodeEditorForm with title, content format, content editor
 * - Choices section with CRUD
 * - Delete node functionality
 */

import { ChevronRight, Edit, FileText, Plus, Trash2 } from "lucide-react"
import { useState } from "react"
import type { StoryNodePublic } from "@/client"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useChoicesForNode } from "@/hooks/stories/useNodeChoices"
import { useDeleteNode } from "@/hooks/stories/useStoryNodes"
import ChoiceEditor from "./ChoiceEditor"
import NodeEditorForm from "./NodeEditorForm"

interface NodeEditorProps {
  nodeId: string | null
  storyId: string
  storyVersion: number
  availableNodes: StoryNodePublic[]
}

const NodeEditor = ({ nodeId, storyId, availableNodes }: NodeEditorProps) => {
  const [editingChoiceId, setEditingChoiceId] = useState<string | null>(null)
  const [showCreateChoice, setShowCreateChoice] = useState(false)

  // Find the selected node
  const selectedNode = nodeId
    ? availableNodes.find((n) => n.id === nodeId)
    : null

  // Fetch choices for the selected node
  const { data: choicesData } = useChoicesForNode(nodeId)
  const choices = choicesData?.data ?? []

  // Delete mutation
  const deleteNode = useDeleteNode(storyId)

  // Empty state - no node selected
  if (!selectedNode) {
    return (
      <div className="flex h-full flex-col items-center justify-center text-center">
        <FileText className="text-muted-foreground mb-4 h-12 w-12 opacity-50" />
        <h3 className="text-lg font-medium">Select a Node</h3>
        <p className="text-muted-foreground mt-1 text-sm">
          Choose a node from the tree to edit its content
        </p>
      </div>
    )
  }

  const handleDelete = () => {
    deleteNode.mutate(selectedNode.id)
  }

  return (
    <div className="flex h-full flex-col">
      {/* Node Header */}
      <div className="border-border flex items-start justify-between border-b p-4">
        <div>
          <h2 className="text-xl font-semibold">
            {selectedNode.title || "Untitled Node"}
          </h2>
          <div className="mt-1 flex gap-2">
            {selectedNode.is_start_node && (
              <Badge variant="default" className="bg-green-500">
                Start
              </Badge>
            )}
            {selectedNode.is_end_node && (
              <Badge variant="default" className="bg-blue-500">
                End
              </Badge>
            )}
            <Badge variant="outline">
              {selectedNode.content_format || "text"}
            </Badge>
          </div>
        </div>

        {/* Delete Button */}
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button size="sm" variant="ghost" className="text-destructive">
              <Trash2 className="h-4 w-4" />
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete Node</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to delete "{selectedNode.title}"? This
                will also delete all choices connected to this node. This action
                cannot be undone.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={handleDelete}
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              >
                Delete
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>

      {/* Node Content */}
      <div className="flex-1 overflow-y-auto p-4">
        <NodeEditorForm node={selectedNode} storyId={storyId} />

        {/* Choices Section */}
        {!selectedNode.is_end_node && (
          <div className="mt-8 border-t border-border pt-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold">Choices</h3>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setShowCreateChoice(true)}
              >
                <Plus className="mr-2 h-4 w-4" />
                Add Choice
              </Button>
            </div>

            {choices.length === 0 ? (
              <div className="bg-muted/50 rounded-lg border border-dashed p-4 text-center">
                <p className="text-muted-foreground text-sm">
                  No choices yet. Add a choice to connect this node to another.
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {choices.map((choice) => {
                  const targetNode = availableNodes.find(
                    (n) => n.id === choice.to_node_id,
                  )
                  return (
                    <div
                      key={choice.id}
                      className="flex items-center justify-between rounded-lg border border-border p-3"
                    >
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        <ChevronRight className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                        <div className="min-w-0 flex-1">
                          <p className="font-medium truncate">{choice.text}</p>
                          <p className="text-xs text-muted-foreground">
                            → {targetNode?.title || "No target"}
                          </p>
                        </div>
                      </div>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => setEditingChoiceId(choice.id)}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Choice Editor Modal - Create */}
      {showCreateChoice && (
        <ChoiceEditor
          open={showCreateChoice}
          onOpenChange={setShowCreateChoice}
          fromNodeId={selectedNode.id}
          availableNodes={availableNodes}
          storyId={storyId}
        />
      )}

      {/* Choice Editor Modal - Edit */}
      {editingChoiceId && (
        <ChoiceEditor
          open={!!editingChoiceId}
          onOpenChange={(open) => !open && setEditingChoiceId(null)}
          fromNodeId={selectedNode.id}
          choiceId={editingChoiceId}
          choice={choices.find((c) => c.id === editingChoiceId)}
          availableNodes={availableNodes}
          storyId={storyId}
        />
      )}
    </div>
  )
}

export default NodeEditor
