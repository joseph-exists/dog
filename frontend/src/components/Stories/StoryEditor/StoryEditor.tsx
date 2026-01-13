import {
  Box,
  Button,
  Container,
  Flex,
  Grid,
  HStack,
  Heading,
  Spinner,
} from "@chakra-ui/react"
import { useNavigate } from "@tanstack/react-router"
import { useState } from "react"
import { FaArrowLeft, FaEye } from "react-icons/fa"

import { useStoryEditor } from "@/hooks/stories/useStoryEditor"
import StoryPreview from "../StoryPlayer/StoryPreview"
import NodeEditor from "./NodeEditor/NodeEditor"
import NodeTree from "./NodeTree/NodeTree"
import PropertiesPanel from "./PropertiesPanel/PropertiesPanel"

interface StoryEditorProps {
  storyId: string
}

const StoryEditor = ({ storyId }: StoryEditorProps) => {
  const navigate = useNavigate()
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [isPreviewMode, setIsPreviewMode] = useState(false)

  const { story, nodes, choices, isLoading, error, validateForPublish } =
    useStoryEditor({ storyId })

  const validation =
    story && nodes
      ? validateForPublish()
      : {
          isValid: false,
          errors: [],
          warnings: [],
        }

  if (isLoading) {
    return (
      <Container maxW="container.xl" py={8}>
        <Flex justify="center" align="center" minH="400px">
          <Spinner size="xl" colorPalette="blue" />
        </Flex>
      </Container>
    )
  }

  if (error || !story) {
    return (
      <Container maxW="container.xl" py={8}>
        <Heading size="lg" color="red.500">
          Error loading story
        </Heading>
      </Container>
    )
  }

  // Preview Mode
  if (isPreviewMode) {
    return (
      <StoryPreview
        story={story}
        nodes={nodes}
        choices={choices}
        onExit={() => setIsPreviewMode(false)}
      />
    )
  }

  // Editor Mode
  return (
    <Box>
      {/* Header */}
      <Box borderBottomWidth="1px" borderColor="border">
        <Container maxW="full" py={4}>
          <Flex justify="space-between" align="center">
            <HStack gap={4}>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => navigate({ to: "/stories" })}
              >
                <FaArrowLeft />
                Back to Stories
              </Button>
              <Box>
                <Heading size="md">{story.title}</Heading>
                <HStack fontSize="sm" color="fg.muted" gap={2}>
                  <span>v{story.current_version}</span>
                  {story.published_version &&
                    story.current_version > story.published_version && (
                      <span>(Draft)</span>
                    )}
                </HStack>
              </Box>
            </HStack>
            <HStack gap={2}>
              <Button
                size="sm"
                colorPalette="blue"
                variant="outline"
                onClick={() => setIsPreviewMode(true)}
              >
                <FaEye />
                Preview
              </Button>
              <Button
                size="sm"
                colorPalette={validation.isValid ? "green" : "gray"}
                disabled={!validation.isValid}
              >
                Publish
              </Button>
            </HStack>
          </Flex>
        </Container>
      </Box>

      {/* Three-Panel Layout */}
      <Grid
        templateColumns={{ base: "1fr", lg: "250px 1fr 300px" }}
        gap={0}
        h="calc(100vh - 200px)"
      >
        {/* Left Panel: Node Tree */}
        <Box
          overflowY="auto"
          borderRightWidth="1px"
          borderColor="border"
          bg="bg.subtle"
        >
          <NodeTree
            nodes={nodes}
            choices={choices}
            selectedNodeId={selectedNodeId}
            onSelectNode={setSelectedNodeId}
            storyId={storyId}
            storyVersion={story.current_version}
          />
        </Box>

        {/* Center Panel: Node Editor */}
        <Box overflowY="auto">
          <NodeEditor
            nodeId={selectedNodeId}
            storyId={storyId}
            storyVersion={story.current_version}
            availableNodes={nodes}
          />
        </Box>

        {/* Right Panel: Properties */}
        <Box
          overflowY="auto"
          borderLeftWidth="1px"
          borderColor="border"
          bg="bg.subtle"
        >
          <PropertiesPanel
            story={story}
            nodes={nodes}
            validation={validation}
          />
        </Box>
      </Grid>
    </Box>
  )
}

export default StoryEditor
