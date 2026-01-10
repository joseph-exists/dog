import { useState, useMemo } from "react"
import { Box, EmptyState, Flex, Heading, VStack, IconButton, Text } from "@chakra-ui/react"
import { FiFileText, FiChevronDown, FiChevronRight } from "react-icons/fi"
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core"
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable"

import type { StoryNodePublic, NodeChoicePublic } from "@/client"
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
  const [tree, setTree] = useState<TreeNode | null>(null)

  // Build the tree structure whenever nodes or choices change
  useMemo(() => {
    const newTree = buildNodeTree(nodes, choices)
    setTree(newTree)
  }, [nodes, choices])

  // Get the flattened tree for rendering
  const flatNodes = useMemo(() => flattenTree(tree), [tree])

  // Get orphaned nodes (not connected to start node)
  const orphanedNodes = useMemo(() => getOrphanedNodes(nodes, tree), [nodes, tree])

  const hasStartNode = nodes.some((n) => n.is_start_node)

  // Drag and drop sensors
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event

    if (over && active.id !== over.id) {
      const oldIndex = flatNodes.findIndex((n) => n.node.id === active.id)
      const newIndex = flatNodes.findIndex((n) => n.node.id === over.id)

      if (oldIndex !== -1 && newIndex !== -1) {
        // For now, just reorder in the flat list
        // In the future, you could update the backend with new order
        const reordered = arrayMove(flatNodes, oldIndex, newIndex)
        console.log("Reordered nodes:", reordered.map((n) => n.node.title))
      }
    }
  }

  const handleToggleExpand = (nodeId: string) => {
    setTree(toggleNodeExpansion(tree, nodeId))
  }

  if (nodes.length === 0) {
    return (
      <Box p={4}>
        <EmptyState.Root size="sm">
          <EmptyState.Content>
            <EmptyState.Indicator>
              <FiFileText />
            </EmptyState.Indicator>
            <VStack textAlign="center">
              <EmptyState.Title fontSize="md">No Nodes Yet</EmptyState.Title>
              <EmptyState.Description fontSize="sm">
                Create your first node to start building your story
              </EmptyState.Description>
            </VStack>
          </EmptyState.Content>
        </EmptyState.Root>
        <Box mt={4}>
          <CreateNodeModal
            storyId={storyId}
            storyVersion={storyVersion}
            onSuccess={onSelectNode}
            existingStartNode={hasStartNode}
          />
        </Box>
      </Box>
    )
  }

  return (
    <Box p={4}>
      <Flex justify="space-between" align="center" mb={4}>
        <Heading size="sm">Story Flow</Heading>
        <CreateNodeModal
          storyId={storyId}
          storyVersion={storyVersion}
          onSuccess={onSelectNode}
          existingStartNode={hasStartNode}
        />
      </Flex>

      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <VStack align="stretch" gap={1}>
          {/* Hierarchical Tree */}
          {tree && (
            <>
              <Text fontSize="xs" fontWeight="bold" color="fg.muted" mb={2}>
                Story Tree
              </Text>
              <SortableContext
                items={flatNodes.map((n) => n.node.id)}
                strategy={verticalListSortingStrategy}
              >
                {flatNodes.map((treeNode) => (
                  <Box key={treeNode.node.id}>
                    <Flex align="center" gap={0}>
                      {/* Indentation */}
                      <Box width={`${treeNode.level * 20}px`} flexShrink={0}>
                        {treeNode.level > 0 && (
                          <Box
                            ml={`${(treeNode.level - 1) * 20 + 10}px`}
                            width="10px"
                            height="20px"
                            borderLeft="1px solid"
                            borderBottom="1px solid"
                            borderColor="border"
                          />
                        )}
                      </Box>

                      {/* Expand/Collapse Button */}
                      {treeNode.children.length > 0 ? (
                        <IconButton
                          aria-label="Toggle expand"
                          size="xs"
                          variant="ghost"
                          onClick={() => handleToggleExpand(treeNode.node.id)}
                          mr={1}
                        >
                          {treeNode.isExpanded ? <FiChevronDown /> : <FiChevronRight />}
                        </IconButton>
                      ) : (
                        <Box width="24px" flexShrink={0} />
                      )}

                      {/* Node Item */}
                      <Box flex={1}>
                        <NodeTreeItem
                          node={treeNode.node}
                          isSelected={selectedNodeId === treeNode.node.id}
                          onClick={() => onSelectNode(treeNode.node.id)}
                          level={treeNode.level}
                        />
                      </Box>
                    </Flex>
                  </Box>
                ))}
              </SortableContext>
            </>
          )}

          {/* Orphaned Nodes Section */}
          {orphanedNodes.length > 0 && (
            <>
              <Text fontSize="xs" fontWeight="bold" color="orange.500" mt={4} mb={2}>
                Orphaned Nodes ({orphanedNodes.length})
              </Text>
              <Text fontSize="2xs" color="fg.muted" mb={2}>
                These nodes are not connected to the story flow
              </Text>
              {orphanedNodes.map((node) => (
                <NodeTreeItem
                  key={node.id}
                  node={node}
                  isSelected={selectedNodeId === node.id}
                  onClick={() => onSelectNode(node.id)}
                  level={0}
                />
              ))}
            </>
          )}
        </VStack>
      </DndContext>
    </Box>
  )
}

export default NodeTree
