/**
 * Room Service - Data Integration Layer
 *
 * Purpose: Provide a clean, type-safe abstraction over the OpenAPI client
 * for room-related operations. Transforms backend response models to
 * frontend ViewModels optimized for UI consumption.
 *
 * Architecture:
 * - Wraps OpenAPI client methods
 * - Transforms backend types to ViewModels
 * - Computes derived fields (e.g., is_own_message, participant_count)
 * - Centralizes API endpoint usage
 * - Provides type-safe interfaces
 *
 * Dependencies:
 * - OpenAPI auto-generated client (@/client)
 * - Current user context (passed as parameter)
 *
 *
 */

import {
  type ParticipantAddRequest,
  type RoomCreate,
  type RoomMessagePublic,
  type RoomMessageSend,
  type RoomMessagesPublic,
  type RoomParticipantPublic,
  type RoomParticipantsPublic,
  type RoomPublic,
  type RoomsPublic,
  RoomsService,
  type RoomUpdate,
  UsersService,
} from "@/client"
import { AgentService } from "./agentService"

// ============================================================================
// Type Definitions - ViewModels
// ============================================================================

/**
 * Room ViewModel - Optimized for UI display
 *
 * Transformations from backend RoomPublic:
 * - Parses ISO timestamps to Date objects
 * - Computes participant_count (requires additional query)
 * - Provides nullable unread_count for future enhancement
 */
export interface RoomViewModel {
  room_id: string
  title: string | null
  creator_id: string
  story_id: string | null
  created_at: Date
  last_activity: Date

  // Computed fields (not from backend)
  participant_count?: number
  unread_count?: number
}

/**
 * Message ViewModel - Enriched for UI consumption
 *
 * Transformations from backend RoomMessagePublic:
 * - Parses created_at timestamp to Date
 * - Computes sender_name from participant lookup or agent_name
 * - Adds is_own_message flag for visual distinction
 * - Normalizes sender_type to strict union type
 * - Phase 5: Includes message management fields (edited, pinned, active_for_context)
 */
export interface MessageViewModel {
  message_id: string
  room_id: string
  sender_type: "user" | "agent"
  sender_name: string
  sender_id: string | null
  agent_name: string | null
  content: string
  button_options?: Record<string, unknown> | null
  created_at: Date

  // Computed fields
  is_own_message: boolean

  // Phase 5: Message management fields
  edited_at?: string | null
  edited_by?: string | null
  is_pinned: boolean
  pinned_at?: string | null
  pinned_by?: string | null
  active_for_context: boolean

  // Backend-provided permission flags (eliminates client-side computation)
  can_edit: boolean
  can_delete: boolean
  can_pin: boolean
}

/**
 * Participant ViewModel - Unified user/agent representation
 *
 * Transformations from backend RoomParticipantPublic:
 * - Normalizes participant_type to strict union
 * - Provides display_name (user full_name or agent_name)
 * - Adds avatar_url placeholder for future user avatars
 * - Normalizes role to strict union type
 */
export interface ParticipantViewModel {
  participant_id: string
  participant_type: "user" | "agent"
  display_name: string
  role: "owner" | "member"
  avatar_url?: string
  is_active: boolean
  joined_at: Date
  left_at: Date | null
}

/**
 * Paginated messages response
 */
export interface PaginatedMessages {
  messages: MessageViewModel[]
  has_more: boolean
  total_count: number
  next_cursor?: string
}

/**
 * Room creation input
 */
export interface CreateRoomInput {
  title: string
  story_id?: string | null
}

/**
 * Room update input
 */
export interface UpdateRoomInput {
  title?: string | null
}

/**
 * Participant addition input
 */
export interface AddParticipantInput {
  participant_id: string
  participant_type: "user" | "agent"
  role?: "owner" | "member"
}

// ============================================================================
// Transformation Functions
// ============================================================================

/**
 * Transform backend RoomPublic to RoomViewModel
 */
function transformRoom(room: RoomPublic): RoomViewModel {
  return {
    room_id: room.room_id,
    title: room.title ?? null, // Convert undefined to null
    creator_id: room.creator_id,
    story_id: room.story_id ?? null, // Convert undefined to null
    created_at: new Date(room.created_at),
    last_activity: new Date(room.last_activity),
    // participant_count will be populated separately if needed
    participant_count: undefined,
    unread_count: undefined,
  }
}

/**
 * Transform backend RoomMessagePublic to MessageViewModel
 *
 * @param message - Backend message object
 * @param currentUserId - Current user's ID for computing is_own_message
 */
function transformMessage(
  message: RoomMessagePublic,
  currentUserId: string | null,
): MessageViewModel {
  // Determine sender name
  let sender_name: string
  if (message.sender_type === "agent") {
    sender_name = message.agent_name || "Unknown Agent"
  } else {
    // For user messages, we'll need to look up the user's name
    // For now, use a placeholder that indicates we need user data
    sender_name = message.sender_id || "Unknown User"
  }

  // Check if this is the current user's message
  const is_own_message =
    message.sender_type === "user" && message.sender_id === currentUserId

  // Cast to any to access Phase 5 fields from backend
  const msg = message as any

  return {
    message_id: message.message_id,
    room_id: message.room_id,
    sender_type: message.sender_type as "user" | "agent",
    sender_name,
    sender_id: message.sender_id,
    agent_name: message.agent_name,
    content: message.content,
    button_options: message.button_options,
    created_at: new Date(message.created_at),
    is_own_message,
    // Phase 5: Message management fields
    edited_at: msg.edited_at ?? null,
    edited_by: msg.edited_by ?? null,
    is_pinned: msg.is_pinned ?? false,
    pinned_at: msg.pinned_at ?? null,
    pinned_by: msg.pinned_by ?? null,
    active_for_context: msg.active_for_context ?? false,

    // Backend-provided permission flags
    can_edit: msg.can_edit ?? false,
    can_delete: msg.can_delete ?? false,
    can_pin: msg.can_pin ?? false,
  }
}

/**
 * Transform backend RoomParticipantPublic to ParticipantViewModel
 *
 * @param participant - Backend participant object
 */
function transformParticipant(
  participant: RoomParticipantPublic,
): ParticipantViewModel {
  // Determine display name
  // For users: participant_id is UUID, we'll need to lookup user details
  // For agents: participant_id is agent name (can be used directly)
  let display_name: string
  if (participant.participant_type === "agent") {
    display_name = participant.participant_id // Agent name
  } else {
    // For users, we'd ideally lookup from a user cache/store
    // For now, use participant_id as placeholder
    display_name = participant.participant_id
  }

  return {
    participant_id: participant.participant_id,
    participant_type: participant.participant_type as "user" | "agent",
    display_name,
    role: (participant.role || "member") as "owner" | "member",
    avatar_url: undefined, // Will be populated from user lookup in future
    is_active: participant.active,
    joined_at: new Date(participant.joined_at),
    left_at: participant.left_at ? new Date(participant.left_at) : null,
  }
}

// ============================================================================
// User Lookup and Caching
// ============================================================================

/**
 * In-memory cache for user details to prevent redundant API calls
 */
const userCache = new Map<string, { full_name: string | null; email: string }>()

/**
 * Fetch user details with caching
 *
 * @param userId - User UUID
 * @returns User details or null if not found
 */
async function getUserDetails(
  userId: string,
): Promise<{ full_name: string | null; email: string } | null> {
  // Check cache first
  if (userCache.has(userId)) {
    return userCache.get(userId)!
  }

  try {
    const user = await UsersService.readUserById({ userId })
    const details = {
      full_name: user.full_name ?? null,
      email: user.email,
    }
    userCache.set(userId, details)
    return details
  } catch {
    // User not found or error - don't cache failures
    return null
  }
}

/**
 * In-memory cache for agent details to prevent redundant API calls
 */
const agentCache = new Map<
  string,
  { name: string; description: string | null }
>()

/**
 * Fetch agent details with caching
 *
 * @param agentId - Agent UUID
 * @returns Agent details or null if not found
 */
async function getAgentDetails(
  agentId: string,
): Promise<{ name: string; description: string | null } | null> {
  // Check cache first
  if (agentCache.has(agentId)) {
    return agentCache.get(agentId)!
  }

  try {
    const agent = await AgentService.getAgent(agentId)
    const details = {
      name: agent.name,
      description: agent.description ?? null,
    }
    agentCache.set(agentId, details)
    return details
  } catch {
    // Agent not found or error - don't cache failures
    return null
  }
}

// ============================================================================
// Room Service - Public API
// ============================================================================

/**
 * Room Service
 *
 * Provides all room-related data operations with clean, type-safe interfaces.
 * All methods return ViewModels optimized for UI consumption.
 *
 * Error Handling:
 * - All methods can throw ApiError from the OpenAPI client
 * - Callers should handle errors appropriately (see handleError utility)
 *
 * Authentication:
 * - All methods require valid JWT token (handled by OpenAPI client)
 * - 401 errors indicate authentication failure
 * - 403 errors indicate authorization failure (not a room participant)
 */
export const RoomService = {
  // ==========================================================================
  // Room Operations
  // ==========================================================================

  /**
   * List all rooms accessible to the current user
   *
   * Returns rooms ordered by last_activity (most recent first).
   * Only includes rooms where user is an active participant.
   *
   * @param options - Pagination options
   * @returns Array of RoomViewModel objects
   * @throws ApiError on network or server errors
   */
  async listRooms(options?: {
    skip?: number
    limit?: number
  }): Promise<RoomViewModel[]> {
    const response: RoomsPublic = await RoomsService.listUserRooms({
      skip: options?.skip,
      limit: options?.limit,
    })

    return response.data.map(transformRoom)
  },

  /**
   * Get a single room by ID
   *
   * @param roomId - Room UUID
   * @returns RoomViewModel
   * @throws ApiError - 404 if room not found, 403 if not a participant
   */
  async getRoom(roomId: string): Promise<RoomViewModel> {
    const room: RoomPublic = await RoomsService.getRoom({ roomId })
    return transformRoom(room)
  },

  /**
   * Create a new room
   *
   * Current user becomes the room owner and is automatically added as
   * a participant.
   *
   * @param data - Room creation parameters
   * @returns Newly created RoomViewModel
   * @throws ApiError on validation or server errors
   */
  async createRoom(data: CreateRoomInput): Promise<RoomViewModel> {
    const createData: RoomCreate = {
      title: data.title,
      story_id: data.story_id,
    }

    const room: RoomPublic = await RoomsService.createNewRoom({
      requestBody: createData,
    })

    return transformRoom(room)
  },

  /**
   * Update room metadata (owner-only)
   *
   * @param roomId - Room UUID
   * @param data - Fields to update
   * @returns Updated RoomViewModel
   * @throws ApiError - 403 if not room owner, 404 if room not found
   */
  async updateRoom(
    roomId: string,
    data: UpdateRoomInput,
  ): Promise<RoomViewModel> {
    const updateData: RoomUpdate = {
      title: data.title,
    }

    const room: RoomPublic = await RoomsService.updateRoom({
      roomId,
      requestBody: updateData,
    })

    return transformRoom(room)
  },

  // ==========================================================================
  // Message Operations
  // ==========================================================================

  /**
   * Get messages for a room with cursor-based pagination
   *
   * Messages are returned in chronological order (oldest first).
   * Use the `before` cursor to load older messages.
   *
   * @param roomId - Room UUID
   * @param options - Pagination options
   * @param currentUserId - Current user's ID for computing is_own_message
   * @returns Paginated messages response
   * @throws ApiError - 403 if not a room participant, 404 if room not found
   */
  async getMessages(
    roomId: string,
    options?: { limit?: number; before?: string },
    currentUserId?: string | null,
  ): Promise<PaginatedMessages> {
    const response: RoomMessagesPublic = await RoomsService.listMessages({
      roomId,
      limit: options?.limit,
      before: options?.before,
    })

    // Transform messages first (without user enrichment)
    const messages = response.data.map((msg) =>
      transformMessage(msg, currentUserId || null),
    )

    // Collect unique user IDs from messages
    const userIds = new Set<string>()
    messages.forEach((msg) => {
      if (msg.sender_type === "user" && msg.sender_id) {
        userIds.add(msg.sender_id)
      }
    })

    // Fetch all user details in parallel
    const userMap = new Map<
      string,
      { full_name: string | null; email: string }
    >()
    await Promise.all(
      Array.from(userIds).map(async (userId) => {
        const details = await getUserDetails(userId)
        if (details) {
          userMap.set(userId, details)
        }
      }),
    )

    // Use the existing utility function to enrich messages
    const enrichedMessages = enrichMessagesWithUserNames(messages, userMap)

    // Pagination logic (unchanged)
    const limit = options?.limit || 50
    const has_more = response.data.length === limit
    const next_cursor =
      has_more && enrichedMessages.length > 0
        ? enrichedMessages[0].created_at.toISOString()
        : undefined

    return {
      messages: enrichedMessages,
      has_more,
      total_count: response.count,
      next_cursor,
    }
  },

  /**
   * Send a message to a room
   *
   * After the user message is persisted, the backend automatically
   * triggers any active agents in the room. Agent responses will
   * be available via subsequent getMessages() calls.
   *
   * @param roomId - Room UUID
   * @param content - Message text content
   * @param currentUserId - Current user's ID for optimistic update
   * @returns The created message as MessageViewModel
   * @throws ApiError - 403 if not a participant, 422 if validation fails
   */
  async sendMessage(
    roomId: string,
    content: string,
    currentUserId?: string | null,
  ): Promise<MessageViewModel> {
    const messageData: RoomMessageSend = {
      content,
    }

    const message: RoomMessagePublic = await RoomsService.sendMessage({
      roomId,
      requestBody: messageData,
    })

    return transformMessage(message, currentUserId || null)
  },

  // ==========================================================================
  // Phase 5: Message Management Operations
  // ==========================================================================

  /**
   * Edit a message's content
   *
   * Authorization: Message author OR room owner can edit user messages.
   * Only room owner can edit agent messages.
   * Does NOT change active_for_context status.
   *
   * @param roomId - Room UUID
   * @param messageId - Message UUID
   * @param content - New message content
   * @param currentUserId - Current user's ID
   * @returns The updated message as MessageViewModel
   * @throws ApiError - 403 if not authorized, 404 if message not found
   */
  async editMessage(
    roomId: string,
    messageId: string,
    content: string,
    currentUserId?: string | null,
  ): Promise<MessageViewModel> {
    const message: RoomMessagePublic = await RoomsService.editMessageEndpoint({
      roomId,
      messageId,
      requestBody: { content },
    })

    return transformMessage(message, currentUserId || null)
  },

  /**
   * Pin a message (room owner only)
   *
   * Pinning automatically marks the message as active_for_context.
   *
   * @param roomId - Room UUID
   * @param messageId - Message UUID
   * @param currentUserId - Current user's ID
   * @returns The updated message as MessageViewModel
   * @throws ApiError - 403 if not room owner, 404 if message not found
   */
  async pinMessage(
    roomId: string,
    messageId: string,
    currentUserId?: string | null,
  ): Promise<MessageViewModel> {
    const message: RoomMessagePublic = await RoomsService.pinMessageEndpoint({
      roomId,
      messageId,
    })

    return transformMessage(message, currentUserId || null)
  },

  /**
   * Unpin a message (room owner only)
   *
   * Unpinning does NOT change active_for_context status.
   *
   * @param roomId - Room UUID
   * @param messageId - Message UUID
   * @param currentUserId - Current user's ID
   * @returns The updated message as MessageViewModel
   * @throws ApiError - 403 if not room owner, 404 if message not found
   */
  async unpinMessage(
    roomId: string,
    messageId: string,
    currentUserId?: string | null,
  ): Promise<MessageViewModel> {
    const message: RoomMessagePublic = await RoomsService.unpinMessageEndpoint({
      roomId,
      messageId,
    })

    return transformMessage(message, currentUserId || null)
  },

  /**
   * Toggle message active_for_context status
   *
   * Any active participant can toggle context inclusion.
   *
   * @param roomId - Room UUID
   * @param messageId - Message UUID
   * @param active - New active_for_context value
   * @param currentUserId - Current user's ID
   * @returns The updated message as MessageViewModel
   * @throws ApiError - 403 if not a participant, 404 if message not found
   */
  async toggleMessageContext(
    roomId: string,
    messageId: string,
    active: boolean,
    currentUserId?: string | null,
  ): Promise<MessageViewModel> {
    const message: RoomMessagePublic =
      await RoomsService.toggleMessageContextEndpoint({
        roomId,
        messageId,
        requestBody: { active_for_context: active },
      })

    return transformMessage(message, currentUserId || null)
  },

  /**
   * Delete a message (room owner only, soft delete)
   *
   * Message is removed from API responses but preserved in event log.
   *
   * @param roomId - Room UUID
   * @param messageId - Message UUID
   * @param _currentUserId - Current user's ID (unused, for consistency)
   * @returns Promise that resolves when deletion is complete
   * @throws ApiError - 403 if not room owner, 404 if message not found
   */
  async deleteMessage(
    roomId: string,
    messageId: string,
    _currentUserId?: string | null,
  ): Promise<void> {
    await RoomsService.deleteMessageEndpoint({
      roomId,
      messageId,
    })
  },

  /**
   * Delete a room (owner-only, hard delete)
   *
   * @param roomId - Room UUID
   * @returns Promise that resolves when deletion is complete
   * @throws ApiError - 403 if not room owner, 404 if room not found
   */
  async deleteRoom(_roomId: string): Promise<void> {
    throw new Error(
      "Room deletion not yet supported. Backend endpoint needs to be created.",
    )
    // uncomment once we figure out this endpoint
    // await RoomsService.deleteRoom({ roomId: _roomId });
  },

  // ==========================================================================
  // Participant Operations
  // ==========================================================================

  /**
   * Get all participants in a room
   *
   * Returns both user and agent participants.
   * Only includes active participants (left_at is null).
   *
   * @param roomId - Room UUID
   * @returns Array of ParticipantViewModel objects
   * @throws ApiError - 403 if not a room participant, 404 if room not found
   */
  async getParticipants(roomId: string): Promise<ParticipantViewModel[]> {
    const response: RoomParticipantsPublic =
      await RoomsService.listRoomParticipants({ roomId })

    // Transform participants first
    const participants = response.data
      .filter((p) => p.active) // Only active participants
      .map(transformParticipant)

    // Collect unique user IDs and agent IDs from participants
    const userIds = new Set<string>()
    const agentIds = new Set<string>()
    participants.forEach((p) => {
      if (p.participant_type === "user") {
        userIds.add(p.participant_id)
      } else if (p.participant_type === "agent") {
        agentIds.add(p.participant_id)
      }
    })

    // Fetch all user and agent details in parallel
    const userMap = new Map<
      string,
      { full_name: string | null; email: string }
    >()
    const agentMap = new Map<
      string,
      { name: string; description: string | null }
    >()

    await Promise.all([
      // Fetch user details
      ...Array.from(userIds).map(async (userId) => {
        const details = await getUserDetails(userId)
        if (details) {
          userMap.set(userId, details)
        }
      }),
      // Fetch agent details
      ...Array.from(agentIds).map(async (agentId) => {
        const details = await getAgentDetails(agentId)
        if (details) {
          agentMap.set(agentId, details)
        }
      }),
    ])

    // Enrich participants with both user and agent profiles
    return enrichParticipantsWithProfiles(participants, userMap, agentMap)
  },

  /**
   * Add a participant to a room (owner-only)
   *
   * Supports adding both users and agents.
   * Operation is idempotent: re-adding an inactive participant reactivates them.
   *
   * For users: participant_id is the user's UUID
   * For agents: participant_id is the agent's name (e.g., "StoryAdvisor")
   *
   * @param roomId - Room UUID
   * @param data - Participant details
   * @returns The added participant as ParticipantViewModel
   * @throws ApiError - 403 if not room owner, 404 if participant not found
   */
  async addParticipant(
    roomId: string,
    data: AddParticipantInput,
  ): Promise<ParticipantViewModel> {
    const participantData: ParticipantAddRequest = {
      participant_id: data.participant_id,
      participant_type: data.participant_type,
      role: data.role,
    }

    const participant: RoomParticipantPublic =
      await RoomsService.addRoomParticipant({
        roomId,
        requestBody: participantData,
      })

    return transformParticipant(participant)
  },

  /**
   * Remove a participant from a room (owner-only, soft delete)
   *
   * Sets the participant's active status to false.
   * Historical events and messages are preserved.
   *
   * For users: participantId is the user's UUID
   * For agents: participantId is the agent's name
   *
   * @param roomId - Room UUID
   * @param participantId - Participant identifier
   * @returns Promise that resolves when removal is complete
   * @throws ApiError - 403 if not room owner, 404 if participant not found
   */
  async removeParticipant(
    roomId: string,
    participantId: string,
  ): Promise<void> {
    await RoomsService.removeRoomParticipant({
      roomId,
      participantId,
    })
  },

  /**
   * Change a participant's role (owner-only)
   *
   * @param roomId - Room UUID
   * @param participantId - Participant identifier
   * @param newRole - New role ('owner' or 'member')
   * @returns Updated participant
   * @throws ApiError - 403 if not room owner
   */
  async changeParticipantRole(
    roomId: string,
    participantId: string,
    newRole: "owner" | "member",
  ): Promise<ParticipantViewModel> {
    const participant: RoomParticipantPublic =
      await RoomsService.changeRoomParticipantRole({
        roomId,
        participantId,
        requestBody: { new_role: newRole },
      })

    return transformParticipant(participant)
  },
}

// ============================================================================
// Utility Functions (for future enhancements)
// ============================================================================

/**
 * Enrich messages with user display names
 *
 * This function will be implemented when user lookup functionality is added.
 * For now, it's a placeholder for the planned enhancement.
 *
 * @param messages - Array of messages to enrich
 * @param users - Map of user_id to UserPublic
 * @returns Messages with updated sender_name for user messages
 */
export function enrichMessagesWithUserNames(
  messages: MessageViewModel[],
  users: Map<string, { full_name: string | null; email: string }>,
): MessageViewModel[] {
  return messages.map((msg) => {
    if (msg.sender_type === "user" && msg.sender_id) {
      const user = users.get(msg.sender_id)
      if (user) {
        return {
          ...msg,
          sender_name: user.full_name || user.email,
        }
      }
    }
    return msg
  })
}

/**
 * Enrich participants with user display names and avatars
 *
 * This function will be implemented when user profile lookup is added.
 *
 * @param participants - Array of participants to enrich
 * @param users - Map of user_id to UserPublic with profile data
 * @returns Participants with updated display_name and avatar_url
 */
export function enrichParticipantsWithUserProfiles(
  participants: ParticipantViewModel[],
  users: Map<
    string,
    { full_name: string | null; email: string; avatar_url?: string }
  >,
): ParticipantViewModel[] {
  return participants.map((p) => {
    if (p.participant_type === "user") {
      const user = users.get(p.participant_id)
      if (user) {
        return {
          ...p,
          display_name: user.full_name || user.email,
          avatar_url: user.avatar_url,
        }
      }
    }
    return p
  })
}

/**
 * Enrich participants with both user and agent display names
 *
 * Handles lookups for both user participants (by UUID) and agent participants
 * (by agent config ID). This fixes the issue where agent UUIDs were being
 * displayed instead of their configured names.
 *
 * @param participants - Array of participants to enrich
 * @param users - Map of user_id to user profile data
 * @param agents - Map of agent_id to agent config data
 * @returns Participants with updated display_name and avatar_url
 */
export function enrichParticipantsWithProfiles(
  participants: ParticipantViewModel[],
  users: Map<
    string,
    { full_name: string | null; email: string; avatar_url?: string }
  >,
  agents: Map<string, { name: string; description: string | null }>,
): ParticipantViewModel[] {
  return participants.map((p) => {
    if (p.participant_type === "user") {
      const user = users.get(p.participant_id)
      if (user) {
        return {
          ...p,
          display_name: user.full_name || user.email,
          avatar_url: user.avatar_url,
        }
      }
    } else if (p.participant_type === "agent") {
      const agent = agents.get(p.participant_id)
      if (agent) {
        return {
          ...p,
          display_name: agent.name,
        }
      }
    }
    return p
  })
}

//   /** COPIED FROM exported client sdk
//    * Get Rooms For Story
//    * Get rooms for a story where user is creator or active participant.
//    * @param data The data for the request.
//    * @param data.storyId
//    * @param data.skip
//    * @param data.limit
//    * @returns RoomsPublic Successful Response
//    * @throws ApiError
//    */
//   public static getRoomsForStory(data: RoomsGetRoomsForStoryData): CancelablePromise<RoomsGetRoomsForStoryResponse> {
//     return __request(OpenAPI, {
//         method: 'GET',
//         url: '/api/v1/rooms/story/{story_id}',
//         path: {
//             story_id: data.storyId
//         },
//         query: {
//             skip: data.skip,
//             limit: data.limit
//         },
//         errors: {
//             422: 'Validation Error'
//         }
//     });
// }
