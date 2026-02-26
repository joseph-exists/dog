import { useMemo, useState } from "react"
import {
  ParticipantStack,
  PresetPicker,
  SYSTEM_PRESETS,
} from "@/components/Page/primitives"
import type { ParticipantViewModel } from "@/services/roomService"

export interface DemoAgentRosterAgent {
  id: string
  name: string
  description: string | null
  participation_mode: string
  scope: string
  is_coordinator: boolean
  is_enabled: boolean
}

interface AgentRosterBlockProps {
  title?: string | null
  config: unknown
  activeUsers: ParticipantViewModel[]
  roomAgents: DemoAgentRosterAgent[]
}

interface AgentRosterBlockConfig {
  show_participant_stack: boolean
  participant_stack_max_visible: number
  show_preset_picker: boolean
  preset_picker_variant: "dropdown" | "buttons"
}

function toAgentRosterConfig(value: unknown): AgentRosterBlockConfig {
  const raw =
    value && typeof value === "object" ? (value as Record<string, unknown>) : {}

  const maxVisibleRaw = raw.participant_stack_max_visible
  const maxVisible =
    typeof maxVisibleRaw === "number" &&
    Number.isFinite(maxVisibleRaw) &&
    maxVisibleRaw > 0
      ? Math.floor(maxVisibleRaw)
      : 5

  const variant =
    raw.preset_picker_variant === "buttons" ||
    raw.preset_picker_variant === "dropdown"
      ? raw.preset_picker_variant
      : "dropdown"

  return {
    show_participant_stack: raw.show_participant_stack !== false,
    participant_stack_max_visible: maxVisible,
    show_preset_picker: raw.show_preset_picker === true,
    preset_picker_variant: variant,
  }
}

export function AgentRosterBlock({
  title,
  config,
  activeUsers,
  roomAgents,
}: AgentRosterBlockProps) {
  const parsedConfig = toAgentRosterConfig(config)
  const [selectedPresetId, setSelectedPresetId] = useState<string | null>(null)

  const participants = useMemo(
    () => [
      ...activeUsers.map((user) => ({
        id: user.participant_id,
        name: user.display_name,
        type: "user" as const,
        role: user.role,
      })),
      ...roomAgents.map((agent) => ({
        id: agent.id,
        name: agent.name,
        type: "agent" as const,
        badges: [agent.participation_mode],
        isActive: agent.is_enabled,
      })),
    ],
    [activeUsers, roomAgents],
  )

  return (
    <div className="p-4 space-y-4">
      <div className="space-y-1">
        <div className="text-sm font-medium">{title ?? "Agent Roster"}</div>
        <div className="text-xs text-muted-foreground">
          {activeUsers.length} user{activeUsers.length === 1 ? "" : "s"},{" "}
          {roomAgents.length} agent{roomAgents.length === 1 ? "" : "s"}
        </div>
      </div>

      {parsedConfig.show_participant_stack && participants.length > 0 && (
        <div className="flex items-center justify-between gap-2 rounded-md border bg-muted/20 p-2">
          <span className="text-xs text-muted-foreground">
            Participant stack
          </span>
          <ParticipantStack
            participants={participants}
            maxVisible={parsedConfig.participant_stack_max_visible}
          />
        </div>
      )}

      {parsedConfig.show_preset_picker && (
        <div className="space-y-2 rounded-md border bg-muted/20 p-3">
          <div className="text-xs text-muted-foreground">
            Layout preset preview
          </div>
          <PresetPicker
            presets={SYSTEM_PRESETS}
            currentPresetId={selectedPresetId}
            onSelect={setSelectedPresetId}
            variant={parsedConfig.preset_picker_variant}
          />
        </div>
      )}

      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-md border bg-muted/20 p-3">
          <div className="mb-2 text-xs font-medium text-muted-foreground">
            Users
          </div>
          {activeUsers.length === 0 ? (
            <div className="text-xs text-muted-foreground">
              No users in room.
            </div>
          ) : (
            <div className="space-y-1.5">
              {activeUsers.map((user) => (
                <div key={user.participant_id} className="text-sm">
                  {user.display_name}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="rounded-md border bg-muted/20 p-3">
          <div className="mb-2 text-xs font-medium text-muted-foreground">
            Agents
          </div>
          {roomAgents.length === 0 ? (
            <div className="text-xs text-muted-foreground">
              No agents in room.
            </div>
          ) : (
            <div className="space-y-2">
              {roomAgents.map((agent) => (
                <div key={agent.id} className="space-y-0.5">
                  <div className="text-sm font-medium">{agent.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {agent.participation_mode}
                    {agent.is_coordinator ? " • coordinator" : ""}
                    {!agent.is_enabled ? " • inactive" : ""}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
