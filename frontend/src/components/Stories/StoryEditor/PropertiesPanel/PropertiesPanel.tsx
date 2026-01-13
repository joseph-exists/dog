import {
  Badge,
  Box,
  Button,
  HStack,
  Heading,
  Separator,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useState } from "react"
import { FaCheck, FaExclamationTriangle } from "react-icons/fa"

import type { StoryNodePublic, StoryPublic } from "@/client"
import {
  useCreateNewVersion,
  useUnpublishStory,
} from "@/hooks/stories/useStories"
import {
  useStateSchema,
  useValidateStateSchema,
} from "@/hooks/stories/useStateSchema"
import PublishModal from "../../PublishWorkflow/PublishModal"
import { StateSchemaDrawer } from "../StateSchema"

interface PropertiesPanelProps {
  story: StoryPublic
  nodes: StoryNodePublic[]
  validation: {
    isValid: boolean
    errors: string[]
    warnings: string[]
  }
}

const PropertiesPanel = ({
  story,
  nodes,
  validation,
}: PropertiesPanelProps) => {
  const [isPublishModalOpen, setIsPublishModalOpen] = useState(false)
  const [isSchemaDrawerOpen, setIsSchemaDrawerOpen] = useState(false)
  const createNewVersionMutation = useCreateNewVersion()
  const unpublishMutation = useUnpublishStory()

  // State schema data
  const { data: schemaData } = useStateSchema(story.id, story.current_version)
  const { data: schemaValidation } = useValidateStateSchema(
    story.id,
    story.current_version,
  )

  const isPublishedVersion =
    story.published_version === story.current_version && story.is_published

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  const startNodeCount = nodes.filter((n) => n.is_start_node).length
  const endNodeCount = nodes.filter((n) => n.is_end_node).length

  const handleCreateNewVersion = () => {
    if (
      window.confirm(
        `This will create a new version (v${
          story.current_version + 1
        }) that you can edit without affecting the published version. Continue?`,
      )
    ) {
      createNewVersionMutation.mutate(story.id)
    }
  }

  const handleUnpublish = () => {
    if (
      window.confirm(
        "This will hide your story from the catalog. Existing players will keep their progress. Continue?",
      )
    ) {
      unpublishMutation.mutate(story.id)
    }
  }

  return (
    <Box p={4}>
      <VStack align="stretch" gap={6}>
        {/* Story Info */}
        <Box>
          <Heading size="sm" mb={3}>
            Story Info
          </Heading>
          <VStack align="stretch" gap={2} fontSize="sm">
            <Box>
              <Text fontWeight="bold" color="fg.muted">
                Title
              </Text>
              <Text>{story.title}</Text>
            </Box>
            {story.description && (
              <Box>
                <Text fontWeight="bold" color="fg.muted">
                  Description
                </Text>
                <Text fontSize="xs" color="fg.muted">
                  {story.description}
                </Text>
              </Box>
            )}
            <Box>
              <Text fontWeight="bold" color="fg.muted">
                Created
              </Text>
              <Text fontSize="xs">{formatDate(story.created_at)}</Text>
            </Box>
            <Box>
              <Text fontWeight="bold" color="fg.muted">
                Last Updated
              </Text>
              <Text fontSize="xs">{formatDate(story.updated_at)}</Text>
            </Box>
          </VStack>
        </Box>

        <Separator />

        {/* Version Status */}
        <Box>
          <Heading size="sm" mb={3}>
            Version Status
          </Heading>
          <VStack align="stretch" gap={2}>
            <HStack>
              <Text fontSize="sm" color="fg.muted">
                Current Version:
              </Text>
              <Badge colorPalette="blue">v{story.current_version}</Badge>
            </HStack>
            {story.published_version && (
              <HStack>
                <Text fontSize="sm" color="fg.muted">
                  Published Version:
                </Text>
                <Badge colorPalette="green">v{story.published_version}</Badge>
              </HStack>
            )}
            <HStack>
              <Text fontSize="sm" color="fg.muted">
                Status:
              </Text>
              <Badge colorPalette={story.is_published ? "green" : "gray"}>
                {story.is_published ? "Published" : "Draft"}
              </Badge>
            </HStack>
          </VStack>
        </Box>

        <Separator />

        {/* Node Statistics */}
        <Box>
          <Heading size="sm" mb={3}>
            Node Statistics
          </Heading>
          <VStack align="stretch" gap={2} fontSize="sm">
            <HStack justify="space-between">
              <Text color="fg.muted">Total Nodes:</Text>
              <Text fontWeight="bold">{nodes.length}</Text>
            </HStack>
            <HStack justify="space-between">
              <Text color="fg.muted">Start Nodes:</Text>
              <HStack gap={1}>
                <Text fontWeight="bold">{startNodeCount}</Text>
                {startNodeCount !== 1 && (
                  <FaExclamationTriangle color="orange" size={12} />
                )}
                {startNodeCount === 1 && <FaCheck color="green" size={12} />}
              </HStack>
            </HStack>
            <HStack justify="space-between">
              <Text color="fg.muted">End Nodes:</Text>
              <HStack gap={1}>
                <Text fontWeight="bold">{endNodeCount}</Text>
                {endNodeCount === 0 && (
                  <FaExclamationTriangle color="orange" size={12} />
                )}
                {endNodeCount > 0 && <FaCheck color="green" size={12} />}
              </HStack>
            </HStack>
          </VStack>
        </Box>

        <Separator />

        {/* State Variables */}
        <Box>
          <Heading size="sm" mb={3}>
            State Variables
          </Heading>
          <VStack align="stretch" gap={2} fontSize="sm">
            <HStack justify="space-between">
              <Text color="fg.muted">Defined:</Text>
              <Text fontWeight="bold">{schemaData?.count ?? 0}</Text>
            </HStack>
            {schemaValidation && !schemaValidation.is_valid && (
              <HStack fontSize="xs" color="orange.600">
                <FaExclamationTriangle />
                <Text>
                  {schemaValidation.undefined_variables.length} undefined in
                  choices
                </Text>
              </HStack>
            )}
            <Button
              size="sm"
              variant="outline"
              onClick={() => setIsSchemaDrawerOpen(true)}
            >
              Manage Variables
            </Button>
          </VStack>
        </Box>

        <Separator />

        {/* Validation Warnings */}
        {(validation.errors.length > 0 || validation.warnings.length > 0) && (
          <Box>
            <Heading size="sm" mb={3} color="orange.600">
              Validation Issues
            </Heading>
            <VStack align="stretch" gap={1}>
              {validation.errors.map((error, idx) => (
                <HStack key={idx} fontSize="xs" color="red.600">
                  <FaExclamationTriangle />
                  <Text>{error}</Text>
                </HStack>
              ))}
              {validation.warnings.map((warning, idx) => (
                <HStack key={idx} fontSize="xs" color="orange.600">
                  <FaExclamationTriangle />
                  <Text>{warning}</Text>
                </HStack>
              ))}
            </VStack>
          </Box>
        )}

        <Separator />

        {/* Actions */}
        <Box>
          <Heading size="sm" mb={3}>
            Actions
          </Heading>
          <VStack align="stretch" gap={2}>
            <Button
              size="sm"
              colorPalette={validation.isValid ? "green" : "gray"}
              onClick={() => setIsPublishModalOpen(true)}
            >
              {story.is_published ? "Republish Story" : "Publish Story"}
            </Button>
            {story.published_version &&
              story.current_version === story.published_version && (
                <Button
                  size="sm"
                  colorPalette="blue"
                  variant="outline"
                  onClick={handleCreateNewVersion}
                  loading={createNewVersionMutation.isPending}
                >
                  Create New Version
                </Button>
              )}
            {story.is_published && (
              <Button
                size="sm"
                colorPalette="red"
                variant="outline"
                onClick={handleUnpublish}
                loading={unpublishMutation.isPending}
              >
                Unpublish
              </Button>
            )}
          </VStack>
        </Box>
      </VStack>

      {/* Publish Modal */}
      <PublishModal
        storyId={story.id}
        isOpen={isPublishModalOpen}
        onClose={() => setIsPublishModalOpen(false)}
      />

      {/* State Schema Drawer */}
      <StateSchemaDrawer
        storyId={story.id}
        version={story.current_version}
        isOpen={isSchemaDrawerOpen}
        onClose={() => setIsSchemaDrawerOpen(false)}
        isReadOnly={isPublishedVersion}
      />
    </Box>
  )
}

export default PropertiesPanel
