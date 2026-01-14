import {
  Container,
  EmptyState,
  Flex,
  Grid,
  Heading,
  Spinner,
  VStack,
} from "@chakra-ui/react"
import { FiBook } from "react-icons/fi"

import { useStories } from "@/hooks/stories/useStories"
import CreateStoryModal from "./CreateStoryModal"
import StoryCard from "./StoryCard"

const StoryList = () => {
  const { data, isLoading, error } = useStories()

  const stories = data?.data ?? []

  if (isLoading) {
    return (
      <Container maxW="container.xl" py={8}>
        <Flex justify="center" align="center" minH="400px">
          <Spinner size="xl" colorPalette="blue" />
        </Flex>
      </Container>
    )
  }

  if (error) {
    return (
      <Container maxW="container.xl" py={8}>
        <EmptyState.Root>
          <EmptyState.Content>
            <EmptyState.Indicator>
              <FiBook />
            </EmptyState.Indicator>
            <VStack textAlign="center">
              <EmptyState.Title>Error Loading Stories</EmptyState.Title>
              <EmptyState.Description>
                {error.message || "Something went wrong. Please try again."}
              </EmptyState.Description>
            </VStack>
          </EmptyState.Content>
        </EmptyState.Root>
      </Container>
    )
  }

  if (stories.length === 0) {
    return (
      <Container maxW="container.xl" py={8}>
        <Flex justify="space-between" align="center" mb={6}>
          <Heading size="lg">My Stories</Heading>
          <CreateStoryModal />
        </Flex>
        <EmptyState.Root>
          <EmptyState.Content>
            <EmptyState.Indicator>
              <FiBook />
            </EmptyState.Indicator>
            <VStack textAlign="center">
              <EmptyState.Title>No Stories Yet</EmptyState.Title>
              <EmptyState.Description>
                Create your first interactive story and start crafting branching
                adventures!
              </EmptyState.Description>
            </VStack>
          </EmptyState.Content>
        </EmptyState.Root>
      </Container>
    )
  }

  return (
    <Container maxW="container.xl" py={8}>
      <Flex justify="space-between" align="center" mb={6}>
        <Heading size="lg">My Stories</Heading>
        <CreateStoryModal />
      </Flex>
      <Grid
        templateColumns={{
          base: "1fr",
          md: "repeat(2, 1fr)",
          lg: "repeat(3, 1fr)",
        }}
        gap={6}
      >
        {stories.map((story) => (
          <StoryCard key={story.id} story={story} />
        ))}
      </Grid>
    </Container>
  )
}

export default StoryList
