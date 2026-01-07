import { useQuery } from "@tanstack/react-query"
import { StoriesService, StorynodesService, type StoryNodePublic, type StoryPublic } from "@/client"

interface UseStoryEditorOptions {
  storyId: string
}

export const useStoryEditor = ({ storyId }: UseStoryEditorOptions) => {
  // Fetch the story details
  const storyQuery = useQuery({
    queryKey: ["stories", storyId],
    queryFn: () => StoriesService.readStory({ id: storyId }),
  })

  const story = storyQuery.data

  // Fetch nodes for the story's current version
  const nodesQuery = useQuery({
    queryKey: ["stories", storyId, "nodes"],
    queryFn: async () => {
      const result = await StorynodesService.readStorynodes({ skip: 0, limit: 1000 })
      // Filter for nodes belonging to this story and its current version
      if (!story) return []
      return result.data.filter(
        (node) => node.story_id === storyId && node.story_version === story.current_version
      )
    },
    enabled: !!story, // Only fetch nodes after story is loaded
  })

  const nodes = nodesQuery.data ?? []

  // Helper: Get the start node
  const getStartNode = (): StoryNodePublic | undefined => {
    return nodes.find((node) => node.is_start_node === true)
  }

  // Helper: Get all end nodes
  const getEndNodes = (): StoryNodePublic[] => {
    return nodes.filter((node) => node.is_end_node === true)
  }

  // Helper: Basic validation check
  const validateForPublish = () => {
    const errors: string[] = []
    const warnings: string[] = []

    // Check for exactly one start node
    const startNodes = nodes.filter((node) => node.is_start_node === true)
    if (startNodes.length === 0) {
      errors.push("Story must have exactly one start node")
    } else if (startNodes.length > 1) {
      errors.push(`Story has ${startNodes.length} start nodes, but must have exactly one`)
    }

    // Check for at least one end node
    const endNodes = getEndNodes()
    if (endNodes.length === 0) {
      warnings.push("Story should have at least one end node")
    }

    // Check if story has nodes
    if (nodes.length === 0) {
      errors.push("Story must have at least one node")
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
    }
  }

  return {
    story,
    nodes,
    isLoading: storyQuery.isLoading || nodesQuery.isLoading,
    error: storyQuery.error || nodesQuery.error,
    getStartNode,
    getEndNodes,
    validateForPublish,
  }
}
