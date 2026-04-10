import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { AlertCircle, ExternalLink, LoaderCircle, RefreshCw } from "lucide-react"
import { useEffect, useState } from "react"
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
import { useRoomWorkspaceConnection } from "@/hooks/useRoomWorkspaceConnection"
import { cn } from "@/lib/utils"
import {
  RoomService,
  type RoomWorkspaceCandidateViewModel,
  type RoomWorkspaceConnectionViewModel,
  RoomWorkspaceRuntimeInvokeError,
  type RoomWorkspaceRuntimeInvokeResponseViewModel,
} from "@/services/roomService"
import { Textarea } from "@/components/ui/textarea"
import { PanelContainer } from "../primitives"

interface WorkspaceConnectionsPanelProps {
  roomId: string
}

interface RuntimeInvokeErrorState {
  message: string
  errorCategory: string | null
  errorPhase: string | null
}

const PURPOSE_OPTIONS: Array<{
  value: RoomWorkspaceConnectionPurpose
  label: string
  description: string
}> = [
  {
    value: "service_connect",
    label: "Service Link",
    description:
      "Inspect browser-facing or API services discovered in the workspace for direct links.",
  },
  {
    value: "agent_runtime_connect",
    label: "Agent Runtime",
    description:
      "Use backend-routed runtime endpoints for room-managed execution (codex, hermes, and similar runtimes).",
  },
]

function getStatusBadgeClass(
  status: RoomWorkspaceConnectionViewModel["status"],
) {
  if (status === "available") {
    return "border-emerald-500/40 bg-emerald-500/10 text-emerald-700"
  }
  if (status === "pending") {
    return "border-amber-500/40 bg-amber-500/10 text-amber-700"
  }
  return "border-rose-500/40 bg-rose-500/10 text-rose-700"
}

function getCurrentConnectionStateClass(state: "active" | "unavailable") {
  if (state === "active") {
    return "border-emerald-500/40 bg-emerald-500/10 text-emerald-700"
  }
  return "border-rose-500/40 bg-rose-500/10 text-rose-700"
}

function getFreshnessLabel(expiresAt: Date | null) {
  if (!expiresAt) return "No expiry recorded"
  const remaining = expiresAt.getTime() - Date.now()
  if (remaining <= 0) return "Expired"
  if (remaining <= 2 * 60 * 1000) return "Expiring soon"
  return "Fresh"
}

function getFreshnessClass(expiresAt: Date | null) {
  if (!expiresAt) return "border-border bg-muted/40 text-muted-foreground"
  const remaining = expiresAt.getTime() - Date.now()
  if (remaining <= 0) return "border-rose-500/40 bg-rose-500/10 text-rose-700"
  if (remaining <= 2 * 60 * 1000)
    return "border-amber-500/40 bg-amber-500/10 text-amber-700"
  return "border-emerald-500/40 bg-emerald-500/10 text-emerald-700"
}

function getWorkspaceOptionLabel(workspace: RoomWorkspaceCandidateViewModel) {
  const projectLabel = workspace.project_summary?.name ?? "Private"
  return `${workspace.workspace_name} · ${workspace.workspace_status} · ${projectLabel}`
}

function getEndpointKindLabel(
  endpoint: RoomWorkspaceConnectionViewModel["endpoints"][number],
) {
  if (endpoint.kind === "agent-runtime") {
    return "backend-routed runtime endpoint"
  }
  return endpoint.kind
}

function relationshipLabel(
  relationship: RoomWorkspaceCandidateViewModel["relationship"],
) {
  return relationship === "shared_project" ? "Shared Project" : "Owner Private"
}

function accessLabel(
  accessLevel: RoomWorkspaceCandidateViewModel["access_level"],
) {
  if (accessLevel === "manage") return "Manage"
  if (accessLevel === "use") return "Use"
  return "View"
}

function getRuntimeInvokeStateLabel(
  isInvokingRuntime: boolean,
  runtimeInvokeResult: RoomWorkspaceRuntimeInvokeResponseViewModel | null,
  runtimeInvokeError: RuntimeInvokeErrorState | null,
) {
  if (isInvokingRuntime) return "Invoking runtime"
  if (runtimeInvokeError) return "Invocation failed"
  if (runtimeInvokeResult) return "Invocation completed"
  return "Ready"
}

function getRuntimeInvokeStateClass(
  isInvokingRuntime: boolean,
  runtimeInvokeResult: RoomWorkspaceRuntimeInvokeResponseViewModel | null,
  runtimeInvokeError: RuntimeInvokeErrorState | null,
) {
  if (isInvokingRuntime) {
    return "border-amber-500/40 bg-amber-500/10 text-amber-700"
  }
  if (runtimeInvokeError) {
    return "border-rose-500/40 bg-rose-500/10 text-rose-700"
  }
  if (runtimeInvokeResult) {
    return "border-emerald-500/40 bg-emerald-500/10 text-emerald-700"
  }
  return "border-border bg-muted/40 text-muted-foreground"
}

export function WorkspaceConnectionsPanel({
  roomId,
}: WorkspaceConnectionsPanelProps) {
  const {
    currentConnection,
    setCurrentConnection,
    clearCurrentConnection,
    refetchCurrentConnection,
  } = useRoomWorkspaceConnection(roomId)
  const {
    data: workspaceOptions = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: ["rooms", roomId, "workspace-candidates"],
    queryFn: () => RoomService.listWorkspaceCandidates(roomId),
    staleTime: 5_000,
  })
  const [workspaceId, setWorkspaceId] = useState<string>("")
  const [purpose, setPurpose] =
    useState<RoomWorkspaceConnectionPurpose>("service_connect")
  const [runtimeInput, setRuntimeInput] = useState("")
  const [runtimeInvokeResult, setRuntimeInvokeResult] =
    useState<RoomWorkspaceRuntimeInvokeResponseViewModel | null>(null)
  const [runtimeInvokeError, setRuntimeInvokeError] =
    useState<RuntimeInvokeErrorState | null>(null)
  const [isInvokingRuntime, setIsInvokingRuntime] = useState(false)

  useEffect(() => {
    if (!workspaceOptions.length) {
      setWorkspaceId("")
      return
    }

    const stillPresent = workspaceOptions.some(
      (workspace) => workspace.workspace_id === workspaceId,
    )
    if (stillPresent) return

    const preferredWorkspace =
      workspaceOptions.find(
        (workspace) =>
          workspace.supports_service_connect ||
          workspace.supports_agent_runtime_connect,
      ) ?? workspaceOptions[0]

    setWorkspaceId(preferredWorkspace.workspace_id)
  }, [workspaceId, workspaceOptions])

  const selectedWorkspace =
    workspaceOptions.find(
      (workspace) => workspace.workspace_id === workspaceId,
    ) ?? null

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

  const selectedPurpose = PURPOSE_OPTIONS.find(
    (option) => option.value === purpose,
  )
  const isCurrentSelection =
    currentConnection?.workspaceId === selectedWorkspace?.workspace_id &&
    currentConnection?.purpose === purpose
  const currentConnectionIsFresh =
    !currentConnection?.descriptorExpiresAt ||
    new Date(currentConnection.descriptorExpiresAt).getTime() > Date.now()
  const canInvokeCurrentRuntime =
    currentConnection?.purpose === "agent_runtime_connect" &&
    currentConnection.state === "active" &&
    currentConnection.descriptorStatus === "available" &&
    currentConnectionIsFresh

  async function handleInvokeRuntime() {
    const normalizedInput = runtimeInput.trim()
    if (!normalizedInput || !canInvokeCurrentRuntime) return

    setIsInvokingRuntime(true)
    setRuntimeInvokeError(null)
    setRuntimeInvokeResult(null)

    try {
      const result = await RoomService.invokeWorkspaceRuntime(roomId, {
        input: normalizedInput,
      })
      setRuntimeInvokeResult(result)
      setRuntimeInput("")
    } catch (error) {
      if (error instanceof RoomWorkspaceRuntimeInvokeError) {
        setRuntimeInvokeError({
          message: error.message,
          errorCategory: error.errorCategory,
          errorPhase: error.errorPhase,
        })
      } else {
        setRuntimeInvokeError({
          message:
            error instanceof Error
              ? error.message
              : "Unable to invoke the connected runtime.",
          errorCategory: null,
          errorPhase: null,
        })
      }
    } finally {
      setIsInvokingRuntime(false)
    }
  }

  const connectedRuntimeLabel =
    currentConnection?.endpoints.find((endpoint) => endpoint.kind === "agent-runtime")
      ?.label ?? "Connected Runtime"

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
            className={cn(
              "h-4 w-4",
              descriptorQuery.isFetching && "animate-spin",
            )}
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

        {currentConnection ? (
          <div className="space-y-3 rounded-lg border bg-muted/20 p-3">
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-1">
                <div className="text-sm font-medium">
                  Current room connection
                </div>
                <div className="text-xs text-muted-foreground">
                  {currentConnection.workspaceName} ·{" "}
                  {currentConnection.purpose === "agent_runtime_connect"
                    ? "Agent Runtime"
                    : "Service Link"}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge
                  variant="outline"
                  className={getCurrentConnectionStateClass(
                    currentConnection.state,
                  )}
                >
                  {currentConnection.state}
                </Badge>
                <Badge
                  variant="outline"
                  className={getFreshnessClass(
                    currentConnection.descriptorExpiresAt
                      ? new Date(currentConnection.descriptorExpiresAt)
                      : null,
                  )}
                >
                  {getFreshnessLabel(
                    currentConnection.descriptorExpiresAt
                      ? new Date(currentConnection.descriptorExpiresAt)
                      : null,
                  )}
                </Badge>
                <Badge
                  variant="outline"
                  className={getStatusBadgeClass(
                    currentConnection.descriptorStatus,
                  )}
                >
                  {currentConnection.descriptorStatus}
                </Badge>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => void refetchCurrentConnection()}
                >
                  Refresh
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => void clearCurrentConnection()}
                >
                  Clear
                </Button>
              </div>
            </div>

            <div className="flex flex-wrap gap-2 text-xs">
              <span className="rounded-full border bg-background px-2 py-0.5 text-muted-foreground">
                {relationshipLabel(currentConnection.relationship)}
              </span>
              <span className="rounded-full border bg-background px-2 py-0.5 text-muted-foreground">
                Access: {accessLabel(currentConnection.accessLevel)}
              </span>
              <span className="rounded-full border bg-background px-2 py-0.5 text-muted-foreground">
                {currentConnection.readyServiceCount}/
                {currentConnection.serviceCount} services ready
              </span>
            </div>

            <div className="text-xs text-muted-foreground">
              {currentConnection.state === "unavailable"
                ? (currentConnection.stateReason ??
                  currentConnection.reason ??
                  "This room-held connection now points at a workspace that is no longer available.")
                : currentConnection.descriptorExpiresAt &&
                    new Date(currentConnection.descriptorExpiresAt).getTime() <=
                      Date.now()
                  ? "The held descriptor has aged out. Refresh to rebuild it from current backend state."
                  : (currentConnection.reason ??
                    "Descriptor-backed room connection is active.")}
            </div>

            {currentConnection.state === "unavailable" ? (
              <div className="rounded-md border bg-background/70 p-3 text-xs text-muted-foreground">
                The room is retaining this connection as historical session
                state. You can clear it and choose a new workspace candidate
                when you are ready.
              </div>
            ) : null}

            <div className="text-[11px] text-muted-foreground">
              Descriptor {currentConnection.descriptorId}
              {currentConnection.descriptorExpiresAt
                ? ` · Expires ${new Date(currentConnection.descriptorExpiresAt).toLocaleString()}`
                : ""}
            </div>

            <div className="space-y-2">
              <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Current Endpoints
              </div>
              {currentConnection.endpoints.length > 0 ? (
                <div className="space-y-2">
                  {currentConnection.endpoints.map((endpoint) => (
                    <div
                      key={endpoint.id}
                      className="rounded-md border bg-background/70 p-3"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div className="min-w-0">
                          <div className="text-sm font-medium">
                            {endpoint.label}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {getEndpointKindLabel(endpoint)} · {endpoint.protocol}
                            {endpoint.auth_mode
                              ? ` · ${endpoint.auth_mode}`
                              : ""}
                          </div>
                          {endpoint.scope ? (
                            <div className="mt-1 text-[11px] text-muted-foreground">
                              Scope:{" "}
                              {Object.entries(endpoint.scope)
                                .map(([key, value]) => `${key}=${value}`)
                                .join(" · ")}
                            </div>
                          ) : null}
                        </div>
                        {endpoint.url && endpoint.kind !== "agent-runtime" ? (
                          <a
                            href={endpoint.url}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
                          >
                            Open
                            <ExternalLink className="h-3.5 w-3.5" />
                          </a>
                        ) : endpoint.url ? (
                          <div className="flex items-center gap-2">
                            <Badge variant="outline">Backend-routed invoke</Badge>
                            <a
                              href={endpoint.url}
                              target="_blank"
                              rel="noreferrer"
                              className="inline-flex items-center gap-1 text-[11px] text-muted-foreground hover:underline"
                            >
                              Direct Open (diagnostic)
                              <ExternalLink className="h-3.5 w-3.5" />
                            </a>
                          </div>
                        ) : (
                          <Badge variant="outline">No URL yet</Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-muted-foreground">
                  No endpoints have been issued for the current connection yet.
                </div>
              )}
            </div>

            <div className="text-[11px] text-muted-foreground">
              Selected {new Date(currentConnection.selectedAt).toLocaleString()}
            </div>

            {currentConnection.purpose === "agent_runtime_connect" ? (
              <div className="space-y-3 rounded-lg border border-dashed p-3">
                <div className="space-y-1">
                  <div className="flex items-center justify-between gap-3">
                    <div className="text-sm font-medium">
                      Send To Connected Runtime
                    </div>
                    <Badge
                      variant="outline"
                      className={getRuntimeInvokeStateClass(
                        isInvokingRuntime,
                        runtimeInvokeResult,
                        runtimeInvokeError,
                      )}
                    >
                      {getRuntimeInvokeStateLabel(
                        isInvokingRuntime,
                        runtimeInvokeResult,
                        runtimeInvokeError,
                      )}
                    </Badge>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Send a room-scoped message through the backend execution
                    path instead of opening the runtime endpoint manually.
                  </div>
                  <div className="text-[11px] text-muted-foreground">
                    Runtime: {runtimeInvokeResult?.runtime_label ?? connectedRuntimeLabel}
                    {runtimeInvokeResult?.runtime_profile
                      ? ` · Profile ${runtimeInvokeResult.runtime_profile}`
                      : ""}
                  </div>
                </div>

                <Textarea
                  value={runtimeInput}
                  onChange={(event) => setRuntimeInput(event.target.value)}
                  placeholder="Ask the connected runtime to inspect code, summarize state, or perform a task."
                  disabled={!canInvokeCurrentRuntime || isInvokingRuntime}
                />

                <div className="flex items-center justify-between gap-3">
                  <div className="text-[11px] text-muted-foreground">
                    {canInvokeCurrentRuntime
                      ? "The response will be written back into room history as a runtime message."
                      : "Runtime invocation is available only for an active, fresh, available agent-runtime connection."}
                  </div>
                  <Button
                    size="sm"
                    onClick={() => void handleInvokeRuntime()}
                    disabled={
                      !canInvokeCurrentRuntime ||
                      !runtimeInput.trim() ||
                      isInvokingRuntime
                    }
                  >
                    {isInvokingRuntime ? "Invoking..." : "Send To Runtime"}
                  </Button>
                </div>

                {runtimeInvokeError ? (
                  <div className="rounded-md border border-destructive/40 bg-destructive/5 px-3 py-3 text-sm text-destructive">
                    <div className="flex items-start gap-2">
                      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                      <div className="space-y-1">
                        <div>{runtimeInvokeError.message}</div>
                        <div className="text-[11px] text-destructive/80">
                          {runtimeInvokeError.errorPhase
                            ? `Phase ${runtimeInvokeError.errorPhase}`
                            : "Phase unavailable"}
                          {runtimeInvokeError.errorCategory
                            ? ` · ${runtimeInvokeError.errorCategory}`
                            : ""}
                        </div>
                      </div>
                    </div>
                  </div>
                ) : null}

                {isInvokingRuntime ? (
                  <div className="rounded-md border border-amber-500/40 bg-amber-500/5 px-3 py-3 text-sm text-amber-700">
                    <div className="flex items-center gap-2">
                      <LoaderCircle className="h-4 w-4 animate-spin" />
                      Waiting for the connected runtime to return a response.
                    </div>
                  </div>
                ) : null}

                {runtimeInvokeResult ? (
                  <div className="rounded-md border bg-background/70 p-3">
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-sm font-medium">
                        {runtimeInvokeResult.runtime_label}
                      </div>
                      <Badge
                        variant="outline"
                        className={
                          runtimeInvokeResult.success
                            ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-700"
                            : "border-rose-500/40 bg-rose-500/10 text-rose-700"
                        }
                      >
                        {runtimeInvokeResult.success ? "success" : "failed"}
                      </Badge>
                    </div>
                    <div className="mt-2 whitespace-pre-wrap text-sm text-foreground">
                      {runtimeInvokeResult.output_text}
                    </div>
                    <div className="mt-2 text-[11px] text-muted-foreground">
                      Invocation {runtimeInvokeResult.invocation_id} · Request{" "}
                      {runtimeInvokeResult.request_id} · Endpoint{" "}
                      {runtimeInvokeResult.endpoint_id}
                    </div>
                  </div>
                ) : null}
              </div>
            ) : null}
          </div>
        ) : null}

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
                      <SelectItem
                        key={workspace.workspace_id}
                        value={workspace.workspace_id}
                      >
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
                <p className="text-[11px] text-muted-foreground">
                  {purpose === "agent_runtime_connect"
                    ? "Agent Runtime connections are invoked by backend orchestration. Room websocket clients observe room events, but do not own runtime transport."
                    : "Service Link is for direct service endpoint inspection and browser/API navigation."}
                </p>
              </div>
            </div>

            {selectedWorkspace ? (
              <div className="rounded-lg border bg-muted/30 p-3">
                <div className="flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <div className="font-medium text-sm">
                      {selectedWorkspace.workspace_name}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {selectedWorkspace.project_summary?.name ??
                        "No project attachment"}
                    </div>
                    <div className="mt-1 flex flex-wrap gap-2 text-xs">
                      <span className="rounded-full border bg-background px-2 py-0.5 text-muted-foreground">
                        {relationshipLabel(selectedWorkspace.relationship)}
                      </span>
                      <span className="rounded-full border bg-background px-2 py-0.5 text-muted-foreground">
                        Access: {accessLabel(selectedWorkspace.access_level)}
                      </span>
                      {selectedWorkspace.supports_service_connect ? (
                        <span className="rounded-full border bg-background px-2 py-0.5 text-muted-foreground">
                          service connect
                        </span>
                      ) : null}
                      {selectedWorkspace.supports_agent_runtime_connect ? (
                        <span className="rounded-full border bg-background px-2 py-0.5 text-muted-foreground">
                          agent runtime
                        </span>
                      ) : null}
                    </div>
                    <div className="mt-2 text-xs text-muted-foreground">
                      {selectedWorkspace.match_reason}
                      {selectedWorkspace.service_count > 0
                        ? ` · ${selectedWorkspace.ready_service_count}/${selectedWorkspace.service_count} services ready`
                        : ""}
                    </div>
                  </div>
                  <Link
                    to="/workspace/$workspaceId"
                    params={{ workspaceId: selectedWorkspace.workspace_id }}
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
                    {descriptorQuery.data.status === "pending" &&
                    purpose === "agent_runtime_connect" ? (
                      <div className="text-[11px] text-muted-foreground">
                        Pending usually means the runtime process is present but
                        the websocket listener is not yet ready on port `4319`.
                      </div>
                    ) : null}
                    <div className="text-[11px] text-muted-foreground">
                      Descriptor {descriptorQuery.data.descriptor_id}
                      {descriptorQuery.data.expires_at
                        ? ` · Expires ${descriptorQuery.data.expires_at.toLocaleString()}`
                        : ""}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge
                      variant="outline"
                      className={getFreshnessClass(
                        descriptorQuery.data.expires_at,
                      )}
                    >
                      {getFreshnessLabel(descriptorQuery.data.expires_at)}
                    </Badge>
                    <Badge
                      variant="outline"
                      className={getStatusBadgeClass(
                        descriptorQuery.data.status,
                      )}
                    >
                      {descriptorQuery.data.status}
                    </Badge>
                  </div>
                </div>

                {selectedWorkspace ? (
                  <div className="flex items-center justify-between gap-3 rounded-lg border border-dashed p-3">
                    <div className="space-y-1">
                      <div className="text-sm font-medium">
                        Room-side connection state
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Hold this descriptor as the room&apos;s current
                        workspace connection for the active session.
                      </div>
                    </div>
                    <Button
                      size="sm"
                      onClick={() =>
                        void setCurrentConnection({
                          candidate: selectedWorkspace,
                          purpose,
                        })
                      }
                      disabled={
                        descriptorQuery.data.status === "denied" ||
                        isCurrentSelection
                      }
                    >
                      {isCurrentSelection
                        ? "Current Connection"
                        : "Set Current"}
                    </Button>
                  </div>
                ) : null}

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
                                {getEndpointKindLabel(endpoint)} · {endpoint.protocol}
                                {endpoint.auth_mode
                                  ? ` · ${endpoint.auth_mode}`
                                  : ""}
                              </div>
                            </div>
                            {endpoint.url && endpoint.kind !== "agent-runtime" ? (
                              <a
                                href={endpoint.url}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
                              >
                                Open
                                <ExternalLink className="h-3.5 w-3.5" />
                              </a>
                            ) : endpoint.url ? (
                              <div className="flex items-center gap-2">
                                <Badge variant="outline">Backend-routed invoke</Badge>
                                <a
                                  href={endpoint.url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="inline-flex items-center gap-1 text-[11px] text-muted-foreground hover:underline"
                                >
                                  Direct Open (diagnostic)
                                  <ExternalLink className="h-3.5 w-3.5" />
                                </a>
                              </div>
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
