import { useState, useMemo } from "react"
import DOMPurify from 'dompurify'
import {
  Box,
  Button,
  Card,
  Container,
  Flex,
  Heading,
  HStack,
  Text,
  VStack,
  Badge,
  Separator,
} from "@chakra-ui/react"
import { FaArrowLeft, FaArrowRight, FaUndo } from "react-icons/fa"

import type { StoryPublic, StoryNodePublic, NodeChoicePublic, ContentFormat } from "@/client"

interface StoryPreviewProps {
  story: StoryPublic
  nodes: StoryNodePublic[]
  choices: NodeChoicePublic[]
  onExit: () => void
}

interface HistoryEntry {
  nodeId: string
  state: Record<string, unknown>
  choiceText?: string
}

// Helper function to render content based on format
const renderContent = (node: StoryNodePublic) => {
  const format: ContentFormat = (node.content_format || "text") as ContentFormat
  const content = node.content || ""

  switch (format) {
    case "html":
      return (
        <Box
          className="story-content"
          dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(content) }}
          fontSize="lg"
          lineHeight="tall"
          css={{
            // Apply same styling as CSS for consistency
            '& p': { margin: '0.5em 0' },
            '& h1': { fontSize: '2em', fontWeight: 'bold', margin: '0.75em 0 0.5em' },
            '& h2': { fontSize: '1.5em', fontWeight: 'bold', margin: '0.75em 0 0.5em' },
            '& h3': { fontSize: '1.25em', fontWeight: 'bold', margin: '0.75em 0 0.5em' },
            '& ul, & ol': { paddingLeft: '1.5em', margin: '0.5em 0' },
            '& code': {
              backgroundColor: 'rgba(128, 128, 128, 0.1)',
              borderRadius: '3px',
              padding: '0.2em 0.4em',
              fontFamily: 'monospace',
            },
            '& pre': {
              backgroundColor: 'rgba(128, 128, 128, 0.1)',
              borderRadius: '5px',
              padding: '1em',
              overflow: 'auto',
            },
            '& blockquote': {
              borderLeft: '3px solid',
              borderLeftColor: 'var(--chakra-colors-border)',
              paddingLeft: '1em',
              fontStyle: 'italic',
              color: 'var(--chakra-colors-fg-muted)',
            },
            '& a': { color: 'var(--chakra-colors-blue-500)', textDecoration: 'underline' },
            '& img': { maxWidth: '100%', borderRadius: '5px' },
          }}
        />
      )

    case "json":
      try {
        const parsed = JSON.parse(content)
        return (
          <Box fontSize="lg" lineHeight="tall">
            <Text fontStyle="italic" color="fg.muted" fontSize="sm" mb={2}>
              [JSON Content - Rendering not yet implemented]
            </Text>
            <Text whiteSpace="pre-wrap" fontFamily="monospace" fontSize="sm">
              {JSON.stringify(parsed, null, 2)}
            </Text>
          </Box>
        )
      } catch {
        return (
          <Text whiteSpace="pre-wrap" fontSize="lg" lineHeight="tall" color="red.500">
            [Invalid JSON content]
          </Text>
        )
      }

    case "text":
    default:
      return (
        <Text whiteSpace="pre-wrap" fontSize="lg" lineHeight="tall">
          {content}
        </Text>
      )
  }
}

const StoryPreview = ({ story, nodes, choices, onExit }: StoryPreviewProps) => {
  // Find the start node
  const startNode = nodes.find((n) => n.is_start_node)

  // Initialize state
  const [currentNodeId, setCurrentNodeId] = useState<string | null>(startNode?.id || null)
  const [playerState, setPlayerState] = useState<Record<string, unknown>>({})
  const [history, setHistory] = useState<HistoryEntry[]>([])

  // Get current node
  const currentNode = nodes.find((n) => n.id === currentNodeId)

  // Get available choices for current node
  const availableChoices = useMemo(() => {
    if (!currentNodeId) return []

    const nodeChoices = choices.filter((c) => c.from_node_id === currentNodeId)

    // Filter by requires_state
    return nodeChoices.filter((choice) => {
      if (!choice.requires_state) return true

      // Check if all required state conditions are met
      return Object.entries(choice.requires_state).every(([key, value]) => {
        return playerState[key] === value
      })
    })
  }, [currentNodeId, choices, playerState])

  const handleChoiceClick = (choice: NodeChoicePublic) => {
    if (!currentNode) return

    // Save to history
    setHistory((prev) => [
      ...prev,
      {
        nodeId: currentNode.id,
        state: { ...playerState },
        choiceText: choice.text,
      },
    ])

    // Apply state changes
    if (choice.sets_state) {
      setPlayerState((prev) => ({
        ...prev,
        ...choice.sets_state,
      }))
    }

    // Navigate to next node
    setCurrentNodeId(choice.to_node_id)
  }

  const handleUndo = () => {
    if (history.length === 0) return

    const previous = history[history.length - 1]
    setCurrentNodeId(previous.nodeId)
    setPlayerState(previous.state)
    setHistory((prev) => prev.slice(0, -1))
  }

  const handleRestart = () => {
    setCurrentNodeId(startNode?.id || null)
    setPlayerState({})
    setHistory([])
  }

  if (!startNode) {
    return (
      <Container maxW="container.md" py={8}>
        <Card.Root>
          <Card.Body>
            <VStack gap={4}>
              <Text color="red.500">No start node found. Please set a start node to preview.</Text>
              <Button onClick={onExit}>
                <FaArrowLeft />
                Back to Editor
              </Button>
            </VStack>
          </Card.Body>
        </Card.Root>
      </Container>
    )
  }

  if (!currentNode) {
    return (
      <Container maxW="container.md" py={8}>
        <Card.Root>
          <Card.Body>
            <VStack gap={4}>
              <Text color="red.500">Node not found.</Text>
              <Button onClick={handleRestart}>Restart</Button>
            </VStack>
          </Card.Body>
        </Card.Root>
      </Container>
    )
  }

  const isEndNode = currentNode.is_end_node || availableChoices.length === 0

  return (
    <Box minH="100vh" bg="bg.subtle">
      {/* Header */}
      <Box borderBottomWidth="1px" borderColor="border" bg="bg">
        <Container maxW="container.xl" py={4}>
          <Flex justify="space-between" align="center">
            <HStack gap={4}>
              <Badge colorPalette="blue">Preview Mode</Badge>
              <Heading size="md">{story.title}</Heading>
            </HStack>
            <HStack gap={2}>
              <Button size="sm" variant="ghost" onClick={handleUndo} disabled={history.length === 0}>
                <FaUndo />
                Undo
              </Button>
              <Button size="sm" variant="ghost" onClick={handleRestart}>
                Restart
              </Button>
              <Button size="sm" onClick={onExit}>
                <FaArrowLeft />
                Exit Preview
              </Button>
            </HStack>
          </Flex>
        </Container>
      </Box>

      <Container maxW="container.xl" py={8}>
        <Flex gap={6} direction={{ base: "column", lg: "row" }}>
          {/* Main Story Panel */}
          <Box flex="1">
            <Card.Root>
              <Card.Header>
                <Flex justify="space-between" align="center">
                  <Heading size="lg">{currentNode.title}</Heading>
                  {isEndNode && (
                    <Badge colorPalette="green" size="lg">
                      The End
                    </Badge>
                  )}
                </Flex>
              </Card.Header>
              <Card.Body>
                <VStack align="stretch" gap={6}>
                  {/* Node Content */}
                  {renderContent(currentNode)}

                  {/* Choices */}
                  {!isEndNode && availableChoices.length > 0 && (
                    <>
                      <Separator />
                      <Box>
                        <Text fontSize="sm" fontWeight="bold" color="fg.muted" mb={3}>
                          What do you do?
                        </Text>
                        <VStack align="stretch" gap={3}>
                          {availableChoices
                            .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
                            .map((choice) => (
                              <Button
                                key={choice.id}
                                onClick={() => handleChoiceClick(choice)}
                                size="lg"
                                variant="outline"
                                justifyContent="space-between"
                                h="auto"
                                py={4}
                                px={6}
                              >
                                <Text textAlign="left" flex="1">
                                  {choice.text}
                                </Text>
                                <FaArrowRight />
                              </Button>
                            ))}
                        </VStack>
                      </Box>
                    </>
                  )}

                  {/* End State */}
                  {isEndNode && (
                    <>
                      <Separator />
                      <VStack gap={3}>
                        <Text fontSize="lg" fontWeight="bold" color="fg.muted">
                          You've reached an ending!
                        </Text>
                        <Button onClick={handleRestart} colorPalette="blue">
                          Play Again
                        </Button>
                      </VStack>
                    </>
                  )}
                </VStack>
              </Card.Body>
            </Card.Root>
          </Box>

          {/* Debug Panel */}
          <Box width={{ base: "full", lg: "300px" }}>
            <VStack align="stretch" gap={4}>
              {/* Player State */}
              <Card.Root size="sm">
                <Card.Header>
                  <Heading size="sm">Player State</Heading>
                </Card.Header>
                <Card.Body>
                  {Object.keys(playerState).length === 0 ? (
                    <Text fontSize="xs" color="fg.muted">
                      No state set yet
                    </Text>
                  ) : (
                    <VStack align="stretch" gap={2}>
                      {Object.entries(playerState).map(([key, value]) => (
                        <Box key={key}>
                          <Text fontSize="xs" fontWeight="bold">
                            {key}:
                          </Text>
                          <Text fontSize="xs" color="fg.muted">
                            {JSON.stringify(value)}
                          </Text>
                        </Box>
                      ))}
                    </VStack>
                  )}
                </Card.Body>
              </Card.Root>

              {/* Choice History */}
              <Card.Root size="sm">
                <Card.Header>
                  <Heading size="sm">Choice History</Heading>
                </Card.Header>
                <Card.Body>
                  {history.length === 0 ? (
                    <Text fontSize="xs" color="fg.muted">
                      No choices made yet
                    </Text>
                  ) : (
                    <VStack align="stretch" gap={2}>
                      {history.map((entry, index) => (
                        <Box key={index}>
                          <Text fontSize="xs" fontWeight="bold">
                            {index + 1}. {entry.choiceText}
                          </Text>
                        </Box>
                      ))}
                    </VStack>
                  )}
                </Card.Body>
              </Card.Root>

              {/* Available Choices Debug */}
              <Card.Root size="sm">
                <Card.Header>
                  <Heading size="sm">Available Choices</Heading>
                </Card.Header>
                <Card.Body>
                  <VStack align="stretch" gap={2}>
                    <Text fontSize="xs" color="fg.muted">
                      {availableChoices.length} choice{availableChoices.length !== 1 ? "s" : ""}{" "}
                      available
                    </Text>
                    {availableChoices.map((choice) => (
                      <Box key={choice.id}>
                        <Text fontSize="xs">{choice.text}</Text>
                        {choice.requires_state && (
                          <Text fontSize="2xs" color="orange.500">
                            Requires: {JSON.stringify(choice.requires_state)}
                          </Text>
                        )}
                        {choice.sets_state && (
                          <Text fontSize="2xs" color="blue.500">
                            Sets: {JSON.stringify(choice.sets_state)}
                          </Text>
                        )}
                      </Box>
                    ))}
                  </VStack>
                </Card.Body>
              </Card.Root>
            </VStack>
          </Box>
        </Flex>
      </Container>
    </Box>
  )
}

export default StoryPreview
