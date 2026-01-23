import { useMemo } from "react"
import type { UIComponent } from "@/components/AgentUI/types"
import type { MessageViewModel } from "@/services/roomService"

export interface AgentUIEntry {
  component: UIComponent
  agentName: string
  messageId: string
  timestamp: string
}

interface UseAgentUIOptions {
  messages: MessageViewModel[]
}

interface UseAgentUIResult {
  /** All UI components from all agent messages, in chronological order */
  entries: AgentUIEntry[]
  /** UI components grouped by agent name */
  byAgent: Map<string, AgentUIEntry[]>
  /** Whether there are any UI components */
  hasComponents: boolean
  /** Total number of UI components */
  count: number
}

/**
 * Extracts and aggregates UI components from room messages.
 * Provides a flat chronological list and agent-grouped view.
 */
export function useAgentUI({ messages }: UseAgentUIOptions): UseAgentUIResult {
  const entries = useMemo(() => {
    const result: AgentUIEntry[] = []

    for (const msg of messages) {
      if (msg.sender_type !== "user" && msg.ui_components) {
        for (const component of msg.ui_components) {
          result.push({
            component,
            agentName: msg.sender_name,
            messageId: msg.message_id,
            timestamp:
              msg.created_at instanceof Date
                ? msg.created_at.toISOString()
                : String(msg.created_at ?? ""),
          })
        }
      }
    }

    return result
  }, [messages])

  const byAgent = useMemo(() => {
    const map = new Map<string, AgentUIEntry[]>()
    for (const entry of entries) {
      const existing = map.get(entry.agentName) ?? []
      existing.push(entry)
      map.set(entry.agentName, existing)
    }
    return map
  }, [entries])

  return {
    entries,
    byAgent,
    hasComponents: entries.length > 0,
    count: entries.length,
  }
}
