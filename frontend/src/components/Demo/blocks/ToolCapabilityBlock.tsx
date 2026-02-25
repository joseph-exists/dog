import { Wrench } from "lucide-react"
import type { UserAgentConfigPublic } from "@/client/types.gen"
import { Badge } from "@/components/ui/badge"
import type { DemoRoomAgentData } from "@/components/Demo/rendererRegistry"

interface ToolCapabilityBlockProps {
  title?: string | null
  config: unknown
  roomAgents: DemoRoomAgentData[]
  availableAgents: UserAgentConfigPublic[]
  calloutLabel?: string | null
}

interface ToolCapabilityConfig {
  only_active_agents: boolean
  show_agent_matrix: boolean
  show_config_json: boolean
}

function toConfig(value: unknown): ToolCapabilityConfig {
  const raw = value && typeof value === "object" ? (value as Record<string, unknown>) : {}
  return {
    only_active_agents: raw.only_active_agents !== false,
    show_agent_matrix: raw.show_agent_matrix !== false,
    show_config_json: raw.show_config_json === true,
  }
}

function findAgentConfig(
  roomAgent: DemoRoomAgentData,
  availableAgents: UserAgentConfigPublic[],
): UserAgentConfigPublic | undefined {
  return availableAgents.find((agent) => (
    agent.id === roomAgent.id
      || agent.name === roomAgent.id
      || agent.slug === roomAgent.id
      || agent.name === roomAgent.name
  ))
}

export function ToolCapabilityBlock({
  title,
  config,
  roomAgents,
  availableAgents,
  calloutLabel,
}: ToolCapabilityBlockProps) {
  const parsedConfig = toConfig(config)
  const scopedAgents = parsedConfig.only_active_agents
    ? roomAgents.filter((agent) => agent.is_enabled)
    : roomAgents

  const agentCapabilities = scopedAgents.map((agent) => {
    const configAgent = findAgentConfig(agent, availableAgents)
    const capabilities = (configAgent?.capabilities ?? []).filter((value): value is string => typeof value === "string" && value.length > 0)

    return {
      agent,
      capabilities,
    }
  })

  const capabilityCountByName = new Map<string, number>()
  for (const item of agentCapabilities) {
    for (const capability of item.capabilities) {
      capabilityCountByName.set(capability, (capabilityCountByName.get(capability) ?? 0) + 1)
    }
  }

  const sortedCapabilities = Array.from(capabilityCountByName.entries()).sort((a, b) => {
    if (b[1] !== a[1]) return b[1] - a[1]
    return a[0].localeCompare(b[0])
  })

  return (
    <div className="p-4 space-y-4">
      <div className="space-y-1">
        <div className="text-sm font-medium">{title ?? "Tool Capability"}</div>
        <div className="text-xs text-muted-foreground">Capabilities available from agents currently scoped into this demo.</div>
      </div>
      {calloutLabel && (
        <div className="rounded border bg-muted/30 px-2 py-1 text-xs text-muted-foreground">
          {calloutLabel}
        </div>
      )}

      <div className="grid gap-2 md:grid-cols-3">
        <div className="rounded-md border bg-muted/20 p-3">
          <div className="text-xs text-muted-foreground">Scoped agents</div>
          <div className="mt-1 text-lg font-semibold">{scopedAgents.length}</div>
        </div>
        <div className="rounded-md border bg-muted/20 p-3">
          <div className="text-xs text-muted-foreground">Unique capabilities</div>
          <div className="mt-1 text-lg font-semibold">{sortedCapabilities.length}</div>
        </div>
        <div className="rounded-md border bg-muted/20 p-3">
          <div className="text-xs text-muted-foreground">Capability assignments</div>
          <div className="mt-1 text-lg font-semibold">
            {agentCapabilities.reduce((sum, item) => sum + item.capabilities.length, 0)}
          </div>
        </div>
      </div>

      <div className="rounded-md border bg-muted/20 p-3 space-y-2">
        <div className="text-xs text-muted-foreground">Capability index</div>
        {sortedCapabilities.length === 0 ? (
          <div className="text-xs text-muted-foreground">No capabilities are declared for scoped agents.</div>
        ) : (
          <div className="flex flex-wrap gap-1.5">
            {sortedCapabilities.map(([capability, count]) => (
              <Badge key={capability} variant="outline" className="text-[10px] gap-1">
                <Wrench className="h-3 w-3" />
                {capability}
                <span className="text-muted-foreground">({count})</span>
              </Badge>
            ))}
          </div>
        )}
      </div>

      {parsedConfig.show_agent_matrix && (
        <div className="rounded-md border bg-muted/20 p-3">
          <div className="mb-2 text-xs text-muted-foreground">Agent capability matrix</div>
          {agentCapabilities.length === 0 ? (
            <div className="text-xs text-muted-foreground">No agents in scope.</div>
          ) : (
            <div className="space-y-2">
              {agentCapabilities.map(({ agent, capabilities }) => (
                <div key={agent.id} className="space-y-1">
                  <div className="text-sm font-medium">{agent.name}</div>
                  {capabilities.length === 0 ? (
                    <div className="text-xs text-muted-foreground">No declared capabilities.</div>
                  ) : (
                    <div className="flex flex-wrap gap-1.5">
                      {capabilities.map((capability) => (
                        <Badge key={`${agent.id}-${capability}`} variant="secondary" className="text-[10px]">
                          {capability}
                        </Badge>
                      ))}
                    </div>
                  )}
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
