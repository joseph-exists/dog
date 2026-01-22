/**
 * Room Runtime Service - Data Integration Layer
 *
 * Purpose: Provide a UI-friendly abstraction over room runtime APIs.
 * Transforms backend runtime projections into ViewModels for the StoryPanel.
 */

import {
  type ContentFormat,
  type NodeChoicePublic,
  type RoomRuntimePublic,
  RoomRuntimeService as RoomRuntimeApi,
  type RoomRuntimeAdvanceRequest,
  type RoomRuntimeRewindRequest,
  type RoomRuntimeResetRequest,
  type RoomRuntimeStartRequest,
  type StoryNodePublic,
} from "@/client"

// ============================================================================
// Type Definitions - ViewModels
// ============================================================================

export interface NodeViewModel {
  id: string
  title: string
  content: string
  contentFormat: ContentFormat | null
  isStartNode: boolean
  isEndNode: boolean
}

export interface ChoiceViewModel {
  id: string
  text: string
  toNodeId: string
  order: number
  requiresState: Record<string, unknown> | null
  setsState: Record<string, unknown> | null
  isAvailable: boolean
  unavailableReason: string | null
}

export interface RoomRuntimeViewModel {
  roomId: string
  storyId: string
  storyVersion: number
  revision: number
  headChoiceId: string | null

  currentNode: NodeViewModel | null
  nodeChain: NodeViewModel[]
  availableChoices: ChoiceViewModel[]
  storyState: Record<string, unknown> | null
  rewindTargets: null

  hasRuntime: boolean // derived: runtime exists for room
  isAtEndNode: boolean // derived: current node is flagged as end
  canRewind: boolean // derived: head choice exists for one-step rewind
  canReset: boolean // derived: reset is allowed when runtime exists
}

// ============================================================================
// Transformation Helpers
// ============================================================================

function toNodeViewModel(node: StoryNodePublic): NodeViewModel {
  return {
    id: node.id,
    title: node.title,
    content: node.content ?? "",
    contentFormat: node.content_format ?? null,
    isStartNode: node.is_start_node ?? false,
    isEndNode: node.is_end_node ?? false,
  }
}

function toChoiceViewModel(choice: NodeChoicePublic): ChoiceViewModel {
  return {
    id: choice.id,
    text: choice.text,
    toNodeId: choice.to_node_id,
    order: choice.order ?? 0,
    requiresState: choice.requires_state ?? null,
    setsState: choice.sets_state ?? null,
    isAvailable: true,
    unavailableReason: null,
  }
}

function sortChoices(choices: ChoiceViewModel[]): ChoiceViewModel[] {
  return [...choices].sort((a, b) => {
    if (a.order !== b.order) {
      return a.order - b.order
    }
    return a.id.localeCompare(b.id)
  })
}

function toViewModel(runtime: RoomRuntimePublic): RoomRuntimeViewModel {
  const currentNode =
    runtime.current_node ? toNodeViewModel(runtime.current_node) : null
  const nodeChain = runtime.node_chain
    ? runtime.node_chain.map(toNodeViewModel)
    : []
  const availableChoices = runtime.available_choices
    ? sortChoices(runtime.available_choices.map(toChoiceViewModel))
    : []

  const hasRuntime = Boolean(runtime.story_id)
  const isAtEndNode = currentNode?.isEndNode ?? false
  const canRewind = Boolean(runtime.head_choice_id)
  const canReset = hasRuntime

  return {
    roomId: runtime.room_id,
    storyId: runtime.story_id,
    storyVersion: runtime.story_version,
    revision: runtime.revision,
    headChoiceId: runtime.head_choice_id ?? null,
    currentNode,
    nodeChain,
    availableChoices,
    storyState: runtime.story_state ?? null,
    rewindTargets: null,
    hasRuntime,
    isAtEndNode,
    canRewind,
    canReset,
  }
}

// ============================================================================
// Service Functions
// ============================================================================

export const RoomRuntimeService = {
  /**
   * Fetch the room's runtime projection and transform to ViewModel.
   */
  async getRuntime(roomId: string): Promise<RoomRuntimeViewModel> {
    const runtime = await RoomRuntimeApi.readRoomRuntime({ roomId })
    return toViewModel(runtime)
  },

  /**
   * Start or replace the room runtime with a story/version.
   */
  async startRuntime(
    roomId: string,
    request: RoomRuntimeStartRequest,
  ): Promise<RoomRuntimeViewModel> {
    const runtime = await RoomRuntimeApi.putRoomRuntime({
      roomId,
      requestBody: request,
    })
    return toViewModel(runtime)
  },

  /**
   * Advance the runtime by selecting a choice.
   */
  async advance(
    roomId: string,
    request: RoomRuntimeAdvanceRequest,
  ): Promise<RoomRuntimeViewModel> {
    const runtime = await RoomRuntimeApi.advanceRoomRuntimeRoute({
      roomId,
      requestBody: request,
    })
    return toViewModel(runtime)
  },

  /**
   * Rewind the runtime to a prior choice.
   */
  async rewind(
    roomId: string,
    request: RoomRuntimeRewindRequest,
  ): Promise<RoomRuntimeViewModel> {
    const runtime = await RoomRuntimeApi.rewindRoomRuntimeRoute({
      roomId,
      requestBody: request,
    })
    return toViewModel(runtime)
  },

  /**
   * Reset the runtime to the story start node.
   */
  async reset(
    roomId: string,
    request: RoomRuntimeResetRequest,
  ): Promise<RoomRuntimeViewModel> {
    const runtime = await RoomRuntimeApi.resetRoomRuntimeRoute({
      roomId,
      requestBody: request,
    })
    return toViewModel(runtime)
  },
}
