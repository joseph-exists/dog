import {
  Badge,
  Button,
  Card,
  Flex,
  HStack,
  Text,
  VStack,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { Link, useNavigate } from "@tanstack/react-router"
import { useState } from "react"
import { FaComments, FaEdit, FaTrash } from "react-icons/fa"

import { RoomsService, type StoryPublic } from "@/client"
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
import {
  useDeleteStory,
  usePublishStory,
  useUnpublishStory,
} from "@/hooks/stories/useStories"

interface StoryCardProps {
  story: StoryPublic
}

const StoryCard = ({ story }: StoryCardProps) => {
  const navigate = useNavigate()
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)

  const publishMutation = usePublishStory()
  const unpublishMutation = useUnpublishStory()
  const deleteMutation = useDeleteStory()

  const { data: roomsData } = useQuery({
    queryKey: ["rooms", "story", story.id],
    queryFn: () => RoomsService.getRoomsForStory({ storyId: story.id }),
  })

  // Determine story lifecycle state for badge
  const getStatusBadge = () => {
    if (story.is_published && story.published_version !== null) {
      return (
        <Badge colorPalette="blue" size="sm">
          Published v{story.published_version}
        </Badge>
      )
    }
    if (!story.is_published && story.published_version !== null) {
      return (
        <Badge colorPalette="orange" size="sm">
          Unpublished
        </Badge>
      )
    }
    return (
      <Badge colorPalette="gray" size="sm">
        Draft v{story.current_version}
      </Badge>
    )
  }

  // Show editing badge if current version > published version
  const getEditingBadge = () => {
    if (
      story.published_version &&
      story.current_version > story.published_version
    ) {
      return (
        <Badge colorPalette="yellow" size="sm">
          Draft v{story.current_version}
        </Badge>
      )
    }
    return null
  }

  const handleEdit = () => {
    navigate({ to: `/stories/${story.id}/edit` })
  }

  const handleTogglePublish = () => {
    if (story.is_published) {
      unpublishMutation.mutate(story.id)
    } else {
      publishMutation.mutate(story.id)
    }
  }

  const handleDelete = () => {
    deleteMutation.mutate(story.id)
    setShowDeleteDialog(false)
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInDays = Math.floor(
      (now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24),
    )

    if (diffInDays === 0) return "Today"
    if (diffInDays === 1) return "Yesterday"
    if (diffInDays < 7) return `${diffInDays} days ago`
    if (diffInDays < 30) return `${Math.floor(diffInDays / 7)} weeks ago`
    return date.toLocaleDateString()
  }

  return (
    <Card.Root>
      <Card.Body>
        <VStack align="stretch" gap={3}>
          {/* Title and Badges */}
          <Flex justify="space-between" align="start">
            <Text fontSize="xl" fontWeight="bold">
              {story.title}
            </Text>
            <HStack gap={2}>
              {getStatusBadge()}
              {getEditingBadge()}
            </HStack>
          </Flex>

          {/* Description */}
          <Text fontSize="sm" color="fg.muted" minH="40px">
            {story.description || "No description"}
          </Text>

          {/* Version Info */}
          <HStack fontSize="xs" color="fg.muted" gap={4}>
            <Text>Current: v{story.current_version}</Text>
            {story.published_version && (
              <Text>Published: v{story.published_version}</Text>
            )}
          </HStack>

          {/* Timestamp */}
          <Text fontSize="xs" color="fg.subtle">
            Updated {formatDate(story.updated_at)}
          </Text>

          {/* Actions */}
          <Flex gap={2} mt={2}>
            <Button size="sm" onClick={handleEdit} colorPalette="blue" flex={1}>
              <FaEdit />
              Edit
            </Button>
            <Button
              size="sm"
              onClick={handleTogglePublish}
              colorPalette={story.is_published ? "orange" : "green"}
              variant="outline"
              loading={publishMutation.isPending || unpublishMutation.isPending}
              flex={1}
            >
              {story.is_published ? "Unpublish" : "Publish"}
            </Button>
            <DialogRoot
              open={showDeleteDialog}
              onOpenChange={({ open }) => setShowDeleteDialog(open)}
            >
              <DialogTrigger asChild>
                <Button size="sm" colorPalette="red" variant="ghost">
                  <FaTrash />
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Delete Story</DialogTitle>
                </DialogHeader>
                <DialogBody>
                  <Text>
                    Are you sure you want to delete "{story.title}"? This action
                    cannot be undone.
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
                    onClick={handleDelete}
                    loading={deleteMutation.isPending}
                  >
                    Delete
                  </Button>
                </DialogFooter>
                <DialogCloseTrigger />
              </DialogContent>
            </DialogRoot>
          </Flex>

          {/* Linked Rooms */}
          {roomsData && roomsData.data.length > 0 && (
            <VStack align="stretch" gap={1} mt={2}>
              <HStack fontSize="xs" color="fg.muted">
                <FaComments />
                <Text>Linked Rooms:</Text>
              </HStack>
              <HStack gap={2} flexWrap="wrap">
                {roomsData.data.map((room) => (
                  <Link
                    key={room.room_id}
                    to="/room/$roomId"
                    params={{ roomId: room.room_id }}
                  >
                    <Badge
                      colorPalette="purple"
                      size="sm"
                      cursor="pointer"
                      _hover={{ opacity: 0.8 }}
                    >
                      {room.title || "Untitled Room"}
                    </Badge>
                  </Link>
                ))}
              </HStack>
            </VStack>
          )}
        </VStack>
      </Card.Body>
    </Card.Root>
  )
}

export default StoryCard
