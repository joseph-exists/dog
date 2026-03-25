import { useQuery } from "@tanstack/react-query"
import { ExternalLink, RefreshCw } from "lucide-react"
import { useEffect, useMemo, useState } from "react"
import { Link } from "@tanstack/react-router"
import type { RoomWorkspaceConnectionPurpose } from "@/client"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useWorkspaces } from "@/hooks/useWorkspaces"
import { cn } from "@/lib/utils"
import {
  RoomService,
  type RoomWorkspaceConnectionViewModel,
} from "@/services/roomService"
import type { WorkspaceListItemViewModel } from "@/services/workspaceService"
import { PanelContainer } from "../primitives"

interface WorkspaceConnectionsPanelProps {
  roomId: string
}

const PURPOSE_OPTIONS: Array<{
  value: RoomWorkspaceConnectionPurpose
  label: string
  description: string
}> = [
  {
    value: "service_connect",
    label: "Service Link",
    description: "Inspect browser-facing or API services discovered in the workspace.",
  },
  {
    value: "agent_runtime_connect",
    label: "Agent Runtime",
    description: "Inspect runtime endpoints for agent services such as codex or hermes.",
  },
]

function getStatusBadgeClass(status: RoomWorkspaceConnectionViewModel["status"]) {
  if (status === "available") {
    return "border-emerald-500/40 bg-emerald-500/10 text-emerald-700"
  }
  if (status === "pending") {
    return "border-amber-500/40 bg-amber-500/10 text-amber-700"
  }
  return "border-rose-500/40 bg-rose-500/10 text-rose-700"
}

function getWorkspaceOptionLabel(workspace: WorkspaceListItemViewModel) {
  const projectLabel = workspace.projectSummary?.name ?? "Unattached"
  return `${workspace.name} · ${workspace.status} · ${projectLabel}`
}

export function WorkspaceConnectionsPanel({
  roomId,
}: WorkspaceConnectionsPanelProps) {
  const { data: workspaces = [], isLoading, error } = useWorkspaces()
  const [workspaceId, setWorkspaceId] = useState<string>("")
  const [purpose, setPurpose] =
    useState<RoomWorkspaceConnectionPurpose>("service_connect")

  const workspaceOptions = useMemo(
    () => [...workspaces].sort((a, b) => a.name.localeCompare(b.name)),
    [workspaces],
  )

  useEffect(() => {
    if (!workspaceOptions.length) {
      setWorkspaceId("")
      return
    }

    const stillPresent = workspaceOptions.some(
      (workspace) => workspace.id === workspaceId,
    )
    if (stillPresent) return

    const preferredWorkspace =
      workspaceOptions.find(
        (workspace) =>
          workspace.connectivitySummary?.serviceCount ||
          workspace.services.length > 0,
      ) ?? workspaceOptions[0]

    setWorkspaceId(preferredWorkspace.id)
  }, [workspaceId, workspaceOptions])

  const selectedWorkspace =
    workspaceOptions.find((workspace) => workspace.id === workspaceId) ?? null

  const descriptorQuery = useQuery({
    queryKey: ["rooms", roomId, "workspace-connections", workspaceId, purpose],
    queryFn: () =>
      RoomService.createWorkspaceConnection(roomId, {
        workspace_id: workspaceId,
        purpose,
      }),
    enabled: Boolean(workspaceId),
    staleTime: 1_000,
    refetchInterval: (query) => {
      const descriptor = query.state.data
      if (!descriptor) return 3_000
      return descriptor.status === "pending" ? 3_000 : false
    },
  })

  const selectedPurpose = PURPOSE_OPTIONS.find((option) => option.value === purpose)

  return (
    <PanelContainer
      title="Workspace Links"
      headerActions={
        <Button
          size="sm"
          variant="ghost"
          onClick={() => void descriptorQuery.refetch()}
          disabled={!workspaceId || descriptorQuery.isFetching}
        >
          <RefreshCw
            className={cn("h-4 w-4", descriptorQuery.isFetching && "animate-spin")}
          />
        </Button>
      }
    >
      <div className="space-y-4 p-4">
        <div className="space-y-2">
          <p className="text-sm text-muted-foreground">
            Inspect backend-evaluated workspace connectivity for this room.
          </p>
          <p className="text-xs text-muted-foreground">
            Descriptors reflect shared-project or owner-private access plus the
            latest discovered runtime surfaces.
          </p>
        </div>

        {isLoading ? (
          <div className="rounded-md border border-dashed px-3 py-4 text-sm text-muted-foreground">
            Loading available workspaces...
          </div>
        ) : null}

        {!isLoading && error ? (
          <div className="rounded-md border border-destructive/40 bg-destructive/5 px-3 py-4 text-sm text-destructive">
            Unable to load workspaces for descriptor inspection.
          </div>
        ) : null}

        {!isLoading && !error && workspaceOptions.length === 0 ? (
          <div className="rounded-md border border-dashed px-3 py-4 text-sm text-muted-foreground">
            No accessible workspaces are available yet.
          </div>
        ) : null}

        {workspaceOptions.length > 0 ? (
          <>
            <div className="space-y-3">
              <div className="space-y-1">
                <label className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Workspace
                </label>
                <Select value={workspaceId} onValueChange={setWorkspaceId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a workspace" />
                  </SelectTrigger>
                  <SelectContent>
                    {workspaceOptions.map((workspace) => (
                      <SelectItem key={workspace.id} value={workspace.id}>
                        {getWorkspaceOptionLabel(workspace)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Purpose
                </label>
                <Select
                  value={purpose}
                  onValueChange={(value) =>
                    setPurpose(value as RoomWorkspaceConnectionPurpose)
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {PURPOSE_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {selectedPurpose ? (
                  <p className="text-xs text-muted-foreground">
                    {selectedPurpose.description}
                  </p>
                ) : null}
              </div>
            </div>

            {selectedWorkspace ? (
              <div className="rounded-lg border bg-muted/30 p-3">
                <div className="flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <div className="font-medium text-sm">{selectedWorkspace.name}</div>
                    <div className="text-xs text-muted-foreground">
                      {selectedWorkspace.projectSummary?.name ??
                        "No project attachment"}
                    </div>
                  </div>
                  <Link
                    to="/workspace/$workspaceId"
                    params={{ workspaceId: selectedWorkspace.id }}
                    className="text-xs text-primary hover:underline"
                  >
                    Open workspace
                  </Link>
                </div>
              </div>
            ) : null}

            {descriptorQuery.isLoading ? (
              <div className="rounded-md border border-dashed px-3 py-4 text-sm text-muted-foreground">
                Requesting live descriptor...
              </div>
            ) : null}

            {descriptorQuery.error ? (
              <div className="rounded-md border border-destructive/40 bg-destructive/5 px-3 py-4 text-sm text-destructive">
                Unable to evaluate this room/workspace connection right now.
              </div>
            ) : null}

            {descriptorQuery.data ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between gap-3 rounded-lg border p-3">
                  <div className="space-y-1">
                    <div className="text-sm font-medium">Descriptor status</div>
                    <div className="text-xs text-muted-foreground">
                      {descriptorQuery.data.reason ??
                        "Descriptor issued successfully."}
                    </div>
                  </div>
                  <Badge
                    variant="outline"
                    className={getStatusBadgeClass(descriptorQuery.data.status)}
                  >
                    {descriptorQuery.data.status}
                  </Badge>
                </div>

                <div className="space-y-2 rounded-lg border p-3">
                  <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Capabilities
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {descriptorQuery.data.capabilities.length > 0 ? (
                      descriptorQuery.data.capabilities.map((capability) => (
                        <Badge key={capability} variant="secondary">
                          {capability}
                        </Badge>
                      ))
                    ) : (
                      <span className="text-sm text-muted-foreground">
                        No capability grants were returned for this request.
                      </span>
                    )}
                  </div>
                </div>

                <div className="space-y-2 rounded-lg border p-3">
                  <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Endpoints
                  </div>
                  {descriptorQuery.data.endpoints.length > 0 ? (
                    <div className="space-y-2">
                      {descriptorQuery.data.endpoints.map((endpoint) => (
                        <div
                          key={endpoint.id}
                          className="rounded-md border bg-muted/20 p-3"
                        >
                          <div className="flex items-center justify-between gap-3">
                            <div className="min-w-0">
                              <div className="text-sm font-medium">
                                {endpoint.label}
                              </div>
                              <div className="text-xs text-muted-foreground">
                                {endpoint.kind} · {endpoint.protocol}
                                {endpoint.auth_mode ? ` · ${endpoint.auth_mode}` : ""}
                              </div>
                            </div>
                            {endpoint.url ? (
                              <a
                                href={endpoint.url}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
                              >
                                Open
                                <ExternalLink className="h-3.5 w-3.5" />
                              </a>
                            ) : (
                              <Badge variant="outline">No URL yet</Badge>
                            )}
                          </div>
                          {endpoint.expires_at ? (
                            <div className="mt-2 text-xs text-muted-foreground">
                              Expires {endpoint.expires_at.toLocaleString()}
                            </div>
                          ) : null}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-sm text-muted-foreground">
                      No endpoints are available for this purpose yet.
                    </div>
                  )}
                </div>
              </div>
            ) : null}
          </>
        ) : null}
      </div>
    </PanelContainer>
  )
}
