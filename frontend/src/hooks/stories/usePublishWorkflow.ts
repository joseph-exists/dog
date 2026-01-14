import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useMemo } from "react"
import {
  type NodeChoicePublic,
  StoriesService,
  type StoryNodePublic,
  StorynodesService,
  type StoryPublic,
} from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import {
  type ValidationResult,
  validateStoryForPublish,
} from "./storyValidation"

interface UsePublishWorkflowOptions {
  storyId: string
}

const { showErrorToast } = useCustomToast()

interface PublishWorkflowReturn {
  story: StoryPublic | undefined
  nodes: StoryNodePublic[]
  choices: NodeChoicePublic[]
  // ValidationResult and validateStoryForPublish were imported from legacy hook on frontend.
  // validation should use the correct API validation - we can use a hook to call it but not process on the frontend
  validation: ValidationResult
  isReady: boolean
  isLoading: boolean
  publish: () => void
  publishAsync: () => Promise<StoryPublic>
  unpublish: () => void
  isPublishing: boolean
  isUnpublishing: boolean
}

export function usePublishWorkflow({
  storyId,
}: UsePublishWorkflowOptions): PublishWorkflowReturn {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  // Fetch story
  const { data: story, isLoading: storyLoading } = useQuery({
    queryKey: ["stories", storyId],
    queryFn: () => StoriesService.readStory({ id: storyId }),
  })

  // Fetch nodes for current version
  const { data: nodesData, isLoading: nodesLoading } = useQuery({
    queryKey: ["stories", storyId, "nodes"],
    queryFn: async () => {
      const result = await StorynodesService.readStorynodes({
        skip: 0,
        limit: 1000,
      })
      if (!story) return []
      return result.data.filter(
        (node) =>
          node.story_id === storyId &&
          node.story_version === story.current_version,
      )
    },
    enabled: !!story,
  })

  const nodes = nodesData || []

  // Fetch all choices for all nodes
  const { data: choicesData, isLoading: choicesLoading } = useQuery({
    queryKey: ["stories", storyId, "choices"],
    queryFn: async () => {
      const allChoices: NodeChoicePublic[] = []

      // Fetch choices for each node
      for (const node of nodes) {
        const result = await StorynodesService.readNodeChoices({
          nodeId: node.id,
          skip: 0,
          limit: 100,
        })
        allChoices.push(...result.data)
      }

      return allChoices
    },
    enabled: nodes.length > 0,
  })

  const choices = choicesData || []

  // Run validation
  const validation = useMemo(() => {
    if (!story || nodes.length === 0) {
      return {
        isValid: false,
        errors: ["Story data not loaded"],
        warnings: [],
      }
    }
    return validateStoryForPublish(nodes, choices)
  }, [story, nodes, choices])

  const isReady = validation.isValid
  const isLoading = storyLoading || nodesLoading || choicesLoading

  // Publish mutation
  const publishMutation = useMutation({
    mutationFn: () => StoriesService.publishStory({ id: storyId }),
    onSuccess: (updatedStory) => {
      showSuccessToast(
        `Story published as v${updatedStory.published_version}! Now visible in catalog.`,
      )
      queryClient.invalidateQueries({ queryKey: ["stories"] })
      queryClient.invalidateQueries({ queryKey: ["stories", storyId] })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })

  // Unpublish mutation
  const unpublishMutation = useMutation({
    mutationFn: () => StoriesService.unpublishStory({ id: storyId }),
    onSuccess: () => {
      showSuccessToast(
        "Story unpublished. It is no longer visible in the catalog.",
      )
      queryClient.invalidateQueries({ queryKey: ["stories"] })
      queryClient.invalidateQueries({ queryKey: ["stories", storyId] })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })

  return {
    story,
    nodes,
    choices,
    validation,
    isReady,
    isLoading,
    publish: () => publishMutation.mutate(),
    publishAsync: () => publishMutation.mutateAsync(),
    unpublish: () => unpublishMutation.mutate(),
    isPublishing: publishMutation.isPending,
    isUnpublishing: unpublishMutation.isPending,
  }
}
