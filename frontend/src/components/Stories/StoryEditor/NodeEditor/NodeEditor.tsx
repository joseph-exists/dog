import { useState } from "react"
import {
  Badge,
  Box,
  Button,
  Card,
  EmptyState,
  Flex,
  Heading,
  HStack,
  IconButton,
  Separator,
  Text,
  VStack,
} from "@chakra-ui/react"
import { FiFileText } from "react-icons/fi"
import { FaEdit, FaPlus, FaTrash } from "react-icons/fa"
import { useQuery } from "@tanstack/react-query"

import { StorynodesService, type StoryNodePublic } from "@/client"
import { useChoicesForNode, useDeleteChoice } from "@/hooks/stories/useNodeChoices"
import ChoiceEditor from "./ChoiceEditor"
import NodeEditorForm from "./NodeEditorForm"
import {
  DialogActionTrigger,
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"

interface NodeEditorProps {
  nodeId: string | null
  storyId: string
  storyVersion: number
  availableNodes: StoryNodePublic[]
}

const NodeEditor = ({ nodeId, storyId, availableNodes }: NodeEditorProps) => {
  const [deleteChoiceId, setDeleteChoiceId] = useState<string | null>(null)

  // Fetch the selected node
  const { data: node, isLoading } = useQuery({
    queryKey: ["nodes", nodeId],
    queryFn: () => StorynodesService.readStorynode({ id: nodeId! }),
    enabled: !!nodeId,
  })

  // Fetch choices for this node
  const { data: choicesData, isLoading: choicesLoading } = useChoicesForNode(nodeId)
  const choices = choicesData?.data || []

  const deleteMutation = useDeleteChoice(nodeId)

  if (!nodeId) {
    return (
      <Box p={8}>
        <EmptyState.Root>
          <EmptyState.Content>
            <EmptyState.Indicator>
              <FiFileText />
            </EmptyState.Indicator>
            <VStack textAlign="center">
              <EmptyState.Title>No Node Selected</EmptyState.Title>
              <EmptyState.Description>
                Select a node from the tree to view and edit its content
              </EmptyState.Description>
            </VStack>
          </EmptyState.Content>
        </EmptyState.Root>
      </Box>
    )
  }

  if (isLoading) {
    return (
      <Box p={8}>
        <Text>Loading node...</Text>
      </Box>
    )
  }

  if (!node) {
    return (
      <Box p={8}>
        <Text color="red.500">Error loading node</Text>
      </Box>
    )
  }

  return (
    <Box p={8}>
      <VStack align="stretch" gap={6}>
        {/* Node Edit Form */}
        <NodeEditorForm node={node} storyId={storyId} />

        <Separator />

        {/* Choices Section */}
        <Box>
          <Flex justify="space-between" align="center" mb={3}>
            <Heading size="md">Choices from this node</Heading>
            <ChoiceEditor
              fromNodeId={nodeId}
              availableNodes={availableNodes}
              trigger={
                <Button size="sm" colorPalette="blue">
                  <FaPlus fontSize="10px" />
                  Add Choice
                </Button>
              }
            />
          </Flex>

          {choicesLoading ? (
            <Text fontSize="sm">
              Loading choices...
            </Text>
          ) : choices.length === 0 ? (
            <EmptyState.Root size="sm">
              <EmptyState.Content>
                <EmptyState.Indicator>
                  <FiFileText />
                </EmptyState.Indicator>
                <VStack textAlign="center">
                  <EmptyState.Title fontSize="sm">No Choices Yet</EmptyState.Title>
                  <EmptyState.Description fontSize="xs">
                    Add choices to create branching paths in your story
                  </EmptyState.Description>
                </VStack>
              </EmptyState.Content>
            </EmptyState.Root>
          ) : (
            <VStack align="stretch" gap={3}>
              {choices
                .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
                .map((choice) => {
                  const targetNode = availableNodes.find((n) => n.id === choice.to_node_id)
                  return (
                    <Card.Root key={choice.id} size="sm">
                      <Card.Body>
                        <VStack align="stretch" gap={2}>
                          <Flex justify="space-between" align="start">
                            <Box flex={1}>
                              <Text fontWeight="bold" fontSize="sm">
                                {choice.text}
                              </Text>
                              <Text fontSize="xs">
                                → {targetNode?.title || "Unknown node"}
                              </Text>
                            </Box>
                            <HStack gap={1}>
                              <Badge size="sm" colorPalette="gray">
                                Order: {choice.order}
                              </Badge>
                              {choice.requires_state && (
                                <Badge size="sm" colorPalette="orange">
                                  Conditional
                                </Badge>
                              )}
                              {choice.sets_state && (
                                <Badge size="sm" colorPalette="blue">
                                  Sets State
                                </Badge>
                              )}
                            </HStack>
                          </Flex>

                          <HStack gap={2} justify="flex-end">
                            <ChoiceEditor
                              fromNodeId={nodeId}
                              availableNodes={availableNodes}
                              choice={choice}
                              trigger={
                                <IconButton
                                  size="xs"
                                  variant="ghost"
                                  aria-label="Edit choice"
                                >
                                  <FaEdit />
                                </IconButton>
                              }
                            />
                            <DialogRoot
                              open={deleteChoiceId === choice.id}
                              onOpenChange={({ open }) => setDeleteChoiceId(open ? choice.id : null)}
                            >
                              <DialogTrigger asChild>
                                <IconButton
                                  size="xs"
                                  variant="ghost"
                                  colorPalette="red"
                                  aria-label="Delete choice"
                                >
                                  <FaTrash />
                                </IconButton>
                              </DialogTrigger>
                              <DialogContent>
                                <DialogHeader>
                                  <DialogTitle>Delete Choice</DialogTitle>
                                </DialogHeader>
                                <DialogBody>
                                  <Text>
                                    Are you sure you want to delete this choice? This action cannot
                                    be undone.
                                  </Text>
                                </DialogBody>
                                <DialogFooter gap={2}>
                                  <DialogActionTrigger asChild>
                                    <Button variant="subtle" colorPalette="gray">
                                      Cancel
                                    </Button>
                                  </DialogActionTrigger>
                                  <Button
                                    colorPalette="red"
                                    onClick={() => {
                                      deleteMutation.mutate(choice.id)
                                      setDeleteChoiceId(null)
                                    }}
                                    loading={deleteMutation.isPending}
                                  >
                                    Delete
                                  </Button>
                                </DialogFooter>
                                <DialogCloseTrigger />
                              </DialogContent>
                            </DialogRoot>
                          </HStack>
                        </VStack>
                      </Card.Body>
                    </Card.Root>
                  )
                })}
            </VStack>
          )}
        </Box>
      </VStack>
    </Box>
  )
}

export default NodeEditor
