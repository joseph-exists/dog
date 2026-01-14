/**
 * ParticipantList Component
 *
 * Displays active participants:
 * - Users section with count
 * - Agents section with count
 * - Visual distinction (agent icon)
 * - Loading state handling
 *
 * Phase 3 Alpha - Task 18
 */

import { Box, Flex, Spinner, Text, VStack } from "@chakra-ui/react"

import type { ParticipantViewModel } from "@/services/roomService"

import AgentToggle from "./AgentToggle"
import RemoveParticipantButton from "./RemoveParticipantButton"

interface ParticipantListProps {
  activeUsers: ParticipantViewModel[]
  activeAgents: ParticipantViewModel[]
  isLoading?: boolean
  currentUserRole: "owner" | "member" | null
  onRemoveParticipant?: (participantId: string) => Promise<void>
  onToggleAgent?: (agentId: string, activate: boolean) => Promise<void>
}

const ParticipantList = ({
  activeUsers,
  activeAgents,
  isLoading = false,
  currentUserRole,
  onRemoveParticipant,
  onToggleAgent,
}: ParticipantListProps) => {
  // Loading state
  if (isLoading) {
    return (
      <Box
        p={4}
        borderTopWidth={1}
        borderColor="gray.200"
        _dark={{ borderColor: "gray.700" }}
      >
        <Spinner size="sm" />
      </Box>
    )
  }

  return (
    <Box
      p={4}
      borderTopWidth={1}
      borderColor="gray.200"
      bg="white"
      _dark={{ borderColor: "gray.700", bg: "gray.900" }}
    >
      <Text fontSize="sm" fontWeight="bold" mb={2}>
        Participants
      </Text>

      <VStack align="start" gap={2} fontSize="sm">
        {/* Users section */}
        {activeUsers.length > 0 && (
          <>
            <Text fontSize="xs" color="gray.600" _dark={{ color: "gray.400" }}>
              Users ({activeUsers.length})
            </Text>
            {activeUsers.map((p) => (
              <Flex
                key={p.participant_id}
                justify="space-between"
                w="full"
                align="center"
              >
                <Text>{p.display_name}</Text>
                {currentUserRole === "owner" && onRemoveParticipant && (
                  <RemoveParticipantButton
                    participantId={p.participant_id}
                    participantName={p.display_name}
                    participantType="user"
                    onRemove={onRemoveParticipant}
                  />
                )}
              </Flex>
            ))}
          </>
        )}

        {/* Agents section */}
        {activeAgents.length > 0 && (
          <>
            <Text
              fontSize="xs"
              color="gray.600"
              _dark={{ color: "gray.400" }}
              mt={2}
            >
              Agents ({activeAgents.length})
            </Text>
            {activeAgents.map((p) =>
              currentUserRole === "owner" && onToggleAgent ? (
                <AgentToggle
                  key={p.participant_id}
                  agentId={p.participant_id}
                  agentName={p.display_name}
                  isActive={p.is_active}
                  onToggle={onToggleAgent}
                />
              ) : (
                <Text key={p.participant_id} fontSize="sm">
                  🤖 {p.display_name}
                </Text>
              ),
            )}
          </>
        )}

        {/* Empty state */}
        {activeUsers.length === 0 && activeAgents.length === 0 && (
          <Text fontSize="xs" color="gray.500" _dark={{ color: "gray.500" }}>
            No active participants
          </Text>
        )}
      </VStack>
    </Box>
  )
}

export default ParticipantList
