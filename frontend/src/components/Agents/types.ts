type AgentScope = "system" | "personal"
type ParticipationMode = "always" | "on_mention" | "manual"


export interface AgentData {
  id: string
  name: string
  description?: string | null
  scope?: AgentScope
  participationMode?: ParticipationMode
  isEnabled?: boolean
  isCoordinator?: boolean
  modelName?: string
}