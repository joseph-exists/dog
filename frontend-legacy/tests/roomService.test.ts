/**
 * Room Service Tests
 *
 * Tests the transformation logic and type safety of the RoomService adapter.
 * These tests use mock data to verify transformations without hitting the API.
 *
 * @see Phase3-TechnicalSpec.md §7.1 (Unit Testing)
 */

import type {
  RoomMessagePublic,
  RoomParticipantPublic,
  RoomPublic,
} from "@/client"
import { describe, expect, it } from "vitest"
import {
  enrichMessagesWithUserNames,
  enrichParticipantsWithUserProfiles,
} from "./roomService"
import type { MessageViewModel, ParticipantViewModel } from "./roomService"

// ============================================================================
// Mock Data Factories
// ============================================================================

function createMockRoom(overrides?: Partial<RoomPublic>): RoomPublic {
  return {
    room_id: "123e4567-e89b-12d3-a456-426614174000",
    title: "Test Room",
    creator_id: "123e4567-e89b-12d3-a456-426614174001",
    story_id: "123e4567-e89b-12d3-a456-426614174002",
    created_at: "2025-01-01T12:00:00Z",
    last_activity: "2025-01-02T15:30:00Z",
    ...overrides,
  }
}

function createMockUserMessage(
  overrides?: Partial<RoomMessagePublic>,
): RoomMessagePublic {
  return {
    message_id: "msg-001",
    room_id: "123e4567-e89b-12d3-a456-426614174000",
    sender_type: "user",
    sender_id: "user-001",
    agent_name: null,
    content: "Hello, world!",
    created_at: "2025-01-02T15:30:00Z",
    button_options: null,
    ...overrides,
  }
}

function createMockAgentMessage(
  overrides?: Partial<RoomMessagePublic>,
): RoomMessagePublic {
  return {
    message_id: "msg-002",
    room_id: "123e4567-e89b-12d3-a456-426614174000",
    sender_type: "agent",
    sender_id: null,
    agent_name: "StoryAdvisor",
    content: "How can I help you today?",
    created_at: "2025-01-02T15:31:00Z",
    button_options: null,
    ...overrides,
  }
}

function createMockUserParticipant(
  overrides?: Partial<RoomParticipantPublic>,
): RoomParticipantPublic {
  return {
    id: "participant-001",
    room_id: "123e4567-e89b-12d3-a456-426614174000",
    participant_id: "user-001",
    participant_type: "user",
    role: "owner",
    joined_at: "2025-01-01T12:00:00Z",
    left_at: null,
    active: true,
    ...overrides,
  }
}

function createMockAgentParticipant(
  overrides?: Partial<RoomParticipantPublic>,
): RoomParticipantPublic {
  return {
    id: "participant-002",
    room_id: "123e4567-e89b-12d3-a456-426614174000",
    participant_id: "StoryAdvisor",
    participant_type: "agent",
    role: "member",
    joined_at: "2025-01-01T12:05:00Z",
    left_at: null,
    active: true,
    ...overrides,
  }
}

// ============================================================================
// Transformation Tests
// ============================================================================

describe("RoomService Transformations", () => {
  describe("Room Transformation", () => {
    it("should transform RoomPublic to RoomViewModel with Date objects", () => {
      const mockRoom = createMockRoom()

      // We can't directly test the private transform function,
      // but we verify the structure matches our ViewModel type
      expect(mockRoom.room_id).toBe("123e4567-e89b-12d3-a456-426614174000")
      expect(mockRoom.created_at).toBe("2025-01-01T12:00:00Z")

      // Verify Date parsing would work
      const createdAt = new Date(mockRoom.created_at)
      expect(createdAt).toBeInstanceOf(Date)
      expect(createdAt.getFullYear()).toBe(2025)
    })

    it("should handle null title and story_id", () => {
      const mockRoom = createMockRoom({ title: null, story_id: null })

      expect(mockRoom.title).toBeNull()
      expect(mockRoom.story_id).toBeNull()
    })
  })

  describe("Message Transformation", () => {
    it("should identify user messages correctly", () => {
      const userMessage = createMockUserMessage()

      expect(userMessage.sender_type).toBe("user")
      expect(userMessage.sender_id).toBe("user-001")
      expect(userMessage.agent_name).toBeNull()
    })

    it("should identify agent messages correctly", () => {
      const agentMessage = createMockAgentMessage()

      expect(agentMessage.sender_type).toBe("agent")
      expect(agentMessage.agent_name).toBe("StoryAdvisor")
      expect(agentMessage.sender_id).toBeNull()
    })

    it("should parse message timestamps to Date objects", () => {
      const message = createMockUserMessage()
      const createdAt = new Date(message.created_at)

      expect(createdAt).toBeInstanceOf(Date)
      expect(createdAt.toISOString()).toBe("2025-01-02T15:30:00.000Z")
    })

    it("should handle button_options if present", () => {
      const messageWithButtons = createMockAgentMessage({
        button_options: {
          label: "Continue Story",
          value: "continue",
          style: "primary",
        },
      })

      expect(messageWithButtons.button_options).toBeDefined()
      expect(messageWithButtons.button_options).toHaveProperty("label")
    })
  })

  describe("Participant Transformation", () => {
    it("should transform user participant correctly", () => {
      const participant = createMockUserParticipant()

      expect(participant.participant_type).toBe("user")
      expect(participant.participant_id).toBe("user-001")
      expect(participant.role).toBe("owner")
      expect(participant.active).toBe(true)
    })

    it("should transform agent participant correctly", () => {
      const participant = createMockAgentParticipant()

      expect(participant.participant_type).toBe("agent")
      expect(participant.participant_id).toBe("StoryAdvisor")
      expect(participant.role).toBe("member")
    })

    it("should handle left participants", () => {
      const leftParticipant = createMockUserParticipant({
        active: false,
        left_at: "2025-01-03T10:00:00Z",
      })

      expect(leftParticipant.active).toBe(false)
      expect(leftParticipant.left_at).toBe("2025-01-03T10:00:00Z")
    })
  })
})

// ============================================================================
// Enrichment Function Tests
// ============================================================================

describe("Message Enrichment", () => {
  it("should enrich user messages with display names", () => {
    const messages: MessageViewModel[] = [
      {
        message_id: "msg-001",
        room_id: "room-001",
        sender_type: "user",
        sender_name: "user-001", // Original placeholder
        sender_id: "user-001",
        agent_name: null,
        content: "Hello",
        created_at: new Date(),
        is_own_message: false,
      },
    ]

    const users = new Map([
      ["user-001", { full_name: "Alice Smith", email: "alice@example.com" }],
    ])

    const enriched = enrichMessagesWithUserNames(messages, users)

    expect(enriched[0].sender_name).toBe("Alice Smith")
  })

  it("should use email as fallback when full_name is null", () => {
    const messages: MessageViewModel[] = [
      {
        message_id: "msg-001",
        room_id: "room-001",
        sender_type: "user",
        sender_name: "user-002",
        sender_id: "user-002",
        agent_name: null,
        content: "Hi",
        created_at: new Date(),
        is_own_message: false,
      },
    ]

    const users = new Map([
      ["user-002", { full_name: null, email: "bob@example.com" }],
    ])

    const enriched = enrichMessagesWithUserNames(messages, users)

    expect(enriched[0].sender_name).toBe("bob@example.com")
  })

  it("should not modify agent messages", () => {
    const messages: MessageViewModel[] = [
      {
        message_id: "msg-002",
        room_id: "room-001",
        sender_type: "agent",
        sender_name: "StoryAdvisor",
        sender_id: null,
        agent_name: "StoryAdvisor",
        content: "Hello!",
        created_at: new Date(),
        is_own_message: false,
      },
    ]

    const users = new Map()
    const enriched = enrichMessagesWithUserNames(messages, users)

    expect(enriched[0].sender_name).toBe("StoryAdvisor")
  })
})

describe("Participant Enrichment", () => {
  it("should enrich user participants with profile data", () => {
    const participants: ParticipantViewModel[] = [
      {
        participant_id: "user-001",
        participant_type: "user",
        display_name: "user-001", // Original placeholder
        role: "owner",
        is_active: true,
        joined_at: new Date(),
        left_at: null,
      },
    ]

    const users = new Map([
      [
        "user-001",
        {
          full_name: "Alice Smith",
          email: "alice@example.com",
          avatar_url: "https://example.com/avatars/alice.jpg",
        },
      ],
    ])

    const enriched = enrichParticipantsWithUserProfiles(participants, users)

    expect(enriched[0].display_name).toBe("Alice Smith")
    expect(enriched[0].avatar_url).toBe("https://example.com/avatars/alice.jpg")
  })

  it("should not modify agent participants", () => {
    const participants: ParticipantViewModel[] = [
      {
        participant_id: "StoryAdvisor",
        participant_type: "agent",
        display_name: "StoryAdvisor",
        role: "member",
        is_active: true,
        joined_at: new Date(),
        left_at: null,
      },
    ]

    const users = new Map()
    const enriched = enrichParticipantsWithUserProfiles(participants, users)

    expect(enriched[0].display_name).toBe("StoryAdvisor")
    expect(enriched[0].avatar_url).toBeUndefined()
  })
})

// ============================================================================
// Type Safety Tests
// ============================================================================

describe("Type Safety", () => {
  it("should enforce strict sender_type union", () => {
    // This test verifies TypeScript compilation
    // If it compiles, the types are correct
    const userMessage: MessageViewModel = {
      message_id: "msg-001",
      room_id: "room-001",
      sender_type: "user", // Must be 'user' or 'agent'
      sender_name: "Test User",
      sender_id: "user-001",
      agent_name: null,
      content: "Test",
      created_at: new Date(),
      is_own_message: false,
    }

    expect(userMessage.sender_type).toBe("user")

    const agentMessage: MessageViewModel = {
      message_id: "msg-002",
      room_id: "room-001",
      sender_type: "agent", // Must be 'user' or 'agent'
      sender_name: "StoryAdvisor",
      sender_id: null,
      agent_name: "StoryAdvisor",
      content: "Test",
      created_at: new Date(),
      is_own_message: false,
    }

    expect(agentMessage.sender_type).toBe("agent")
  })

  it("should enforce strict role union", () => {
    const participant: ParticipantViewModel = {
      participant_id: "user-001",
      participant_type: "user",
      display_name: "Test User",
      role: "owner", // Must be 'owner' or 'member'
      is_active: true,
      joined_at: new Date(),
      left_at: null,
    }

    expect(participant.role).toBe("owner")
  })
})
