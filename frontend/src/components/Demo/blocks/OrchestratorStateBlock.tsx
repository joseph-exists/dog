import { Activity, Bot, Crown, Radio } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import type { DemoRoomAgentData } from "@/components/Demo/rendererRegistry"

interface OrchestratorStateBlockProps {
  title?: string | null
  config: unknown
  isConnected: boolean
  autoRespond: boolean
  runtimePolicy: "auto" | "manual" | "owner_only"
  runtimeHasRuntime: boolean
  roomAgents: DemoRoomAgentData[]
  calloutLabel?: string | null
}

export interface OrchestratorStateConfig {
  show_agent_list: boolean
  only_active_agents: boolean
  show_config_json: boolean
}

interface OrchestratorStateSummary {
  filteredAgents: DemoRoomAgentData[]
  orchestrators: DemoRoomAgentData[]
  activeAgents: DemoRoomAgentData[]
}

export function parseOrchestratorStateConfig(value: unknown): OrchestratorStateConfig {
  const raw = value && typeof value === "object" ? (value as Record<string, unknown>) : {}
  return {
    show_agent_list: raw.show_agent_list !== false,
    only_active_agents: raw.only_active_agents !== false,
    show_config_json: raw.show_config_json === true,
  }
}

export function summarizeOrchestratorState({
  config,
  roomAgents,
}: {
  config: OrchestratorStateConfig
  roomAgents: DemoRoomAgentData[]
}): OrchestratorStateSummary {
  const filteredAgents = config.only_active_agents
    ? roomAgents.filter((agent) => agent.is_enabled)
    : roomAgents
  const orchestrators = filteredAgents.filter((agent) => agent.is_coordinator)
  const activeAgents = roomAgents.filter((agent) => agent.is_enabled)
  return {
    filteredAgents,
    orchestrators,
    activeAgents,
  }
}

export function OrchestratorStateBlock({
  title,
  config,
  isConnected,
  autoRespond,
  runtimePolicy,
  runtimeHasRuntime,
  roomAgents,
  calloutLabel,
}: OrchestratorStateBlockProps) {
  const parsedConfig = parseOrchestratorStateConfig(config)
  const summary = summarizeOrchestratorState({ config: parsedConfig, roomAgents })

  return (
    <div className="p-4 space-y-4">
      <div className="space-y-1">
        <div className="text-sm font-medium">{title ?? "Orchestrator State"}</div>
        <div className="text-xs text-muted-foreground">Runtime and orchestrator health snapshot for this demo room.</div>
      </div>
      {calloutLabel && (
        <div className="rounded border bg-muted/30 px-2 py-1 text-xs text-muted-foreground">
          {calloutLabel}
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        <Badge variant={isConnected ? "default" : "secondary"} className="gap-1">
          <Radio className="h-3 w-3" />
          Socket {isConnected ? "connected" : "disconnected"}
        </Badge>
        <Badge variant={runtimeHasRuntime ? "default" : "outline"} className="gap-1">
          <Activity className="h-3 w-3" />
          Runtime {runtimeHasRuntime ? "running" : "idle"}
        </Badge>
        <Badge variant={autoRespond ? "default" : "outline"}>Auto-respond {autoRespond ? "on" : "off"}</Badge>
        <Badge variant="outline">Policy: {runtimePolicy}</Badge>
      </div>

      <div className="grid gap-2 md:grid-cols-3">
        <div className="rounded-md border bg-muted/20 p-3">
          <div className="text-xs text-muted-foreground">Agents in room</div>
          <div className="mt-1 text-lg font-semibold">{roomAgents.length}</div>
        </div>
        <div className="rounded-md border bg-muted/20 p-3">
          <div className="text-xs text-muted-foreground">Active agents</div>
          <div className="mt-1 text-lg font-semibold">{summary.activeAgents.length}</div>
        </div>
        <div className="rounded-md border bg-muted/20 p-3">
          <div className="text-xs text-muted-foreground">Orchestrators</div>
          <div className="mt-1 text-lg font-semibold">{summary.orchestrators.length}</div>
        </div>
      </div>

      {parsedConfig.show_agent_list && (
        <div className="rounded-md border bg-muted/20 p-3">
          <div className="mb-2 text-xs text-muted-foreground">Orchestration agents</div>
          {summary.filteredAgents.length === 0 ? (
            <div className="text-xs text-muted-foreground">No agents available for orchestration summary.</div>
          ) : (
            <div className="space-y-2">
              {summary.filteredAgents.map((agent) => (
                <div key={agent.id} className="flex items-center justify-between gap-2 text-sm">
                  <div className="min-w-0 flex items-center gap-2">
                    {agent.is_coordinator ? (
                      <Crown className="h-4 w-4 text-amber-600" />
                    ) : (
                      <Bot className="h-4 w-4 text-muted-foreground" />
                    )}
                    <span className="truncate">{agent.name}</span>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <Badge variant="outline" className="text-[10px]">
                      {agent.participation_mode}
                    </Badge>
                    {!agent.is_enabled && (
                      <Badge variant="secondary" className="text-[10px]">
                        inactive
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {parsedConfig.show_config_json && (
        <pre className="max-h-64 overflow-auto rounded border bg-muted/40 p-3 text-xs">
          {JSON.stringify(config ?? {}, null, 2)}
        </pre>
      )}
    </div>
  )
}
