import {
  type WorkspaceCreate,
  type WorkspaceFlavour,
  type WorkspacePublic,
  type WorkspaceStatus,
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
  hasTerminal: boolean
}

export interface WorkspaceDetailViewModel extends WorkspaceListItemViewModel {
  ownerId: string
  kennelName: string | null
  kennelJob: string | null
  wsToken: string | null
  meta: Record<string, unknown>
  terminalUrl: string | null
  isProvisioning: boolean
  isReady: boolean
  canOpenTerminal: boolean
  canStop: boolean
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
  const status = workspace.status ?? "provisioning"
  const terminalUrl = workspace.terminal_url ?? null

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
    meta: (workspace.meta ?? {}) as Record<string, unknown>,
    createdAt: new Date(workspace.created_at),
    updatedAt: new Date(workspace.updated_at),
    terminalUrl,
    hasTerminal: status === "ready",
    isProvisioning: status === "provisioning",
    isReady: status === "ready",
    canOpenTerminal: status === "ready",
    canStop: status === "ready" || status === "provisioning",
    canDestroy: status !== "destroyed",
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

  async destroyWorkspace(workspaceId: string): Promise<void> {
    await WorkspacesService.destroyWorkspace({ workspaceId })
  },

  async getTerminalDescriptor(workspaceId: string): Promise<WorkspaceTerminalDescriptor> {
    const response = await WorkspacesService.getWorkspaceTerminal({ workspaceId })
    return toWorkspaceTerminalDescriptor(response as Record<string, string>)
  },
}
