import {
  type WorkspaceAction,
  type WorkspaceCreate,
  type WorkspaceFlavour,
  type WorkspaceProjectSummary,
  type WorkspacePublic,
  type WorkspaceStatus,
  type WorkspaceTerminalStatus,
  type WorkspaceVisibility,
  WorkspacesService,
} from "@/client"

export interface WorkspaceListItemViewModel {
  id: string
  name: string
  flavour: WorkspaceFlavour
  kind: string
  status: WorkspaceStatus
  createdAt: Date
  updatedAt: Date
  visibility: WorkspaceVisibility
  projectId: string | null
  projectSummary: WorkspaceProjectSummary | null
  failureMessage: string | null
  terminalStatus: WorkspaceTerminalStatus
  allowedActions: WorkspaceAction[]
  hasTerminal: boolean
}

export interface WorkspaceDetailViewModel extends WorkspaceListItemViewModel {
  ownerId: string
  kennelName: string | null
  kennelJob: string | null
  wsToken: string | null
  meta: Record<string, unknown>
  terminalUrl: string | null
  lastTransitionAt: Date | null
  requestedAt: Date | null
  startedAt: Date | null
  readyAt: Date | null
  stoppedAt: Date | null
  destroyedAt: Date | null
  isProvisioning: boolean
  isStarting: boolean
  isReady: boolean
  isFailed: boolean
  canOpenTerminal: boolean
  canStop: boolean
  canStart: boolean
  canDestroy: boolean
}

export interface WorkspaceTerminalDescriptor {
  terminalUrl: string
  protocol: string
  host: string
  isDirectConnection: boolean
}

export interface CreateWorkspaceInput {
  name: string
  flavour?: WorkspaceFlavour
  kind?: string
  repoUrl?: string | null
  sshPubkey?: string | null
  envVars?: Record<string, string>
}

function toWorkspaceDetailViewModel(workspace: WorkspacePublic): WorkspaceDetailViewModel {
  const status = workspace.status ?? "requested"
  const terminalUrl = workspace.terminal_url ?? null
  const allowedActions = workspace.allowed_actions ?? []
  const terminalStatus = workspace.terminal_status ?? "unavailable"

  return {
    id: workspace.id,
    ownerId: workspace.owner_id,
    name: workspace.name,
    flavour: workspace.flavour ?? "dev",
    kind: workspace.kind ?? "ephemeral",
    status,
    kennelName: workspace.kennel_name ?? null,
    kennelJob: workspace.kennel_job ?? null,
    wsToken: workspace.ws_token ?? null,
    failureMessage: workspace.failure_message ?? null,
    lastTransitionAt: workspace.last_transition_at ? new Date(workspace.last_transition_at) : null,
    requestedAt: workspace.requested_at ? new Date(workspace.requested_at) : null,
    startedAt: workspace.started_at ? new Date(workspace.started_at) : null,
    readyAt: workspace.ready_at ? new Date(workspace.ready_at) : null,
    stoppedAt: workspace.stopped_at ? new Date(workspace.stopped_at) : null,
    destroyedAt: workspace.destroyed_at ? new Date(workspace.destroyed_at) : null,
    meta: (workspace.meta ?? {}) as Record<string, unknown>,
    visibility: workspace.visibility ?? "private",
    projectId: workspace.project_id ?? null,
    projectSummary: workspace.project_summary ?? null,
    terminalStatus,
    allowedActions,
    createdAt: new Date(workspace.created_at),
    updatedAt: new Date(workspace.updated_at),
    terminalUrl,
    hasTerminal: terminalStatus === "available" || terminalStatus === "expired",
    isProvisioning: status === "requested" || status === "provisioning",
    isStarting: status === "starting",
    isReady: status === "ready",
    isFailed: status === "failed",
    canOpenTerminal: allowedActions.includes("request_terminal"),
    canStop: allowedActions.includes("stop"),
    canStart: allowedActions.includes("start"),
    canDestroy: allowedActions.includes("destroy"),
  }
}

function toWorkspaceListItemViewModel(workspace: WorkspacePublic): WorkspaceListItemViewModel {
  const detail = toWorkspaceDetailViewModel(workspace)
  return {
    id: detail.id,
    name: detail.name,
    flavour: detail.flavour,
    kind: detail.kind,
    status: detail.status,
    createdAt: detail.createdAt,
    updatedAt: detail.updatedAt,
    visibility: detail.visibility,
    projectId: detail.projectId,
    projectSummary: detail.projectSummary,
    failureMessage: detail.failureMessage,
    terminalStatus: detail.terminalStatus,
    allowedActions: detail.allowedActions,
    hasTerminal: detail.hasTerminal,
  }
}

function toWorkspaceTerminalDescriptor(data: Record<string, string>): WorkspaceTerminalDescriptor {
  const terminalUrl = data.terminal_url
  const parsed = new URL(terminalUrl)
  return {
    terminalUrl,
    protocol: parsed.protocol.replace(":", ""),
    host: parsed.host,
    isDirectConnection: true,
  }
}

export const WorkspaceService = {
  async listWorkspaces(): Promise<WorkspaceListItemViewModel[]> {
    const response = await WorkspacesService.listWorkspaces()
    return response.data.map(toWorkspaceListItemViewModel)
  },

  async getWorkspace(workspaceId: string): Promise<WorkspaceDetailViewModel> {
    const response = await WorkspacesService.getWorkspace({ workspaceId })
    return toWorkspaceDetailViewModel(response)
  },

  async createWorkspace(input: CreateWorkspaceInput): Promise<WorkspaceDetailViewModel> {
    const requestBody: WorkspaceCreate = {
      name: input.name,
      flavour: input.flavour,
      kind: input.kind,
      repo_url: input.repoUrl,
      ssh_pubkey: input.sshPubkey,
      env_vars: input.envVars,
    }
    const response = await WorkspacesService.createWorkspace({ requestBody })
    return toWorkspaceDetailViewModel(response)
  },

  async stopWorkspace(workspaceId: string): Promise<void> {
    await WorkspacesService.stopWorkspace({ workspaceId })
  },

  async startWorkspace(workspaceId: string): Promise<void> {
    await WorkspacesService.startWorkspace({ workspaceId })
  },

  async destroyWorkspace(workspaceId: string): Promise<void> {
    await WorkspacesService.destroyWorkspace({ workspaceId })
  },

  async getTerminalDescriptor(workspaceId: string): Promise<WorkspaceTerminalDescriptor> {
    const response = await WorkspacesService.getWorkspaceTerminal({ workspaceId })
    return toWorkspaceTerminalDescriptor(response as Record<string, string>)
  },
}
