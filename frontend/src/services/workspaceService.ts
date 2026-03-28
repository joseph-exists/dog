import {
  OpenAPI,
  type WorkspaceAction,
  type WorkspaceBootstrapIntent,
  type WorkspaceBootstrapProgress,
  type WorkspaceConnectivitySummary,
  type WorkspaceCreate,
  type WorkspaceExternalUrlRepoSource,
  type WorkspaceFlavour,
  type WorkspaceFlavourHealthSummary,
  type WorkspaceInstallIntentAuto,
  type WorkspaceInstallIntentNone,
  type WorkspaceInstallIntentProfile,
  type WorkspaceProjectSummary,
  type WorkspacePublic,
  type WorkspaceReadinessSummary,
  type WorkspaceServiceSummary,
  type WorkspaceShadowRepoSource,
  type WorkspaceStartupIntentAgentService,
  type WorkspaceStartupIntentProfile,
  type WorkspaceStartupIntentTerminalOnly,
  type WorkspaceStatus,
  WorkspacesService,
  type WorkspaceTerminalStatus,
  type WorkspaceUserRepoSource,
  type WorkspaceVisibility,
} from "@/client"
import type { ApiRequestOptions } from "@/client/core/ApiRequestOptions"
import { request as __request } from "@/client/core/request"

export type BootstrapRepoSourceType =
  | "none"
  | "external_url"
  | "user_repo"
  | "shadow_repo"
export type BootstrapInstallMode = "none" | "auto" | "profile"
export type BootstrapStartupMode = "terminal_only" | "profile" | "agent_service"
export type BootstrapPhase =
  | "pending"
  | "resolving_source"
  | "materializing_repo"
  | "installing_dependencies"
  | "starting_services"
  | "running_readiness_checks"
  | "complete"
  | "failed"

export interface BootstrapRepoSourceViewModel {
  type: Exclude<BootstrapRepoSourceType, "none">
  label: string
  detail: string
  ref: string | null
}

export interface BootstrapIntentViewModel {
  repoSource: BootstrapRepoSourceViewModel | null
  workspacePath: string | null
  installMode: BootstrapInstallMode
  installProfile: string | null
  startupMode: BootstrapStartupMode
  startupProfile: string | null
  agentProfile: string | null
  envVars: Record<string, string>
  sshPubkey: string | null
}

export interface BootstrapProgressViewModel {
  phase: BootstrapPhase
  message: string | null
  stepCount: number | null
  completedSteps: number | null
  failureMessage: string | null
  completionRatio: number | null
}

export interface WorkspaceReadinessSummaryViewModel {
  terminalReady: boolean
  bootstrapComplete: boolean
  servicesReady: boolean
  serviceCount: number | null
  readyServiceCount: number | null
}

export interface WorkspaceDiscoveredServiceViewModel {
  id: string
  kind: string
  label: string
  status: "pending" | "ready" | "failed" | "unknown"
  protocol: string | null
  host: string | null
  port: number | null
  path: string | null
  url: string | null
  source: string | null
  readinessMessage: string | null
}

export interface WorkspaceConnectivitySummaryViewModel {
  terminalReady: boolean
  bootstrapComplete: boolean
  servicesReady: boolean
  serviceCount: number | null
  readyServiceCount: number | null
}

export interface WorkspaceFlavourHealthSummaryViewModel {
  flavour: string
  snapshotReady: boolean
  latestRebuildStatus: string | null
  latestRebuildJobId: string | null
}

export type WorkspaceAccessLevel = "view" | "use" | "manage"

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
  accessLevel: WorkspaceAccessLevel
  canUseWorkspace: boolean
  canManageRuntime: boolean
  canDiscoverServices: boolean
  canDestroy: boolean
  isProjectWorkspace: boolean
  hasTerminal: boolean
  bootstrapIntent: BootstrapIntentViewModel | null
  bootstrapProgress: BootstrapProgressViewModel | null
  readinessSummary: WorkspaceReadinessSummaryViewModel | null
  connectivitySummary: WorkspaceConnectivitySummaryViewModel | null
  services: WorkspaceDiscoveredServiceViewModel[]
  flavourHealth: WorkspaceFlavourHealthSummaryViewModel | null
  bootstrapWorkspacePath: string | null
  startedServices: string[]
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
  bootstrapPlanStepCount: number | null
  bootstrapStepResults: Array<Record<string, unknown>>
  platformServiceProjection: WorkspacePlatformServiceProjectionSummaryViewModel[]
}

export interface WorkspaceTerminalDescriptor {
  terminalUrl: string
  protocol: string
  host: string
  isDirectConnection: boolean
}

export type WorkspacePlatformServiceConsumerKind =
  | "workspace_runtime"
  | "agent_runtime"

export interface WorkspacePlatformServiceGrantViewModel {
  grantId: string
  serviceId: string
  transport: string
  url: string
  authMode: string
  requireApproval: string
  description: string | null
  scopes: string[]
  tags: string[]
  scope: Record<string, string>
  issuedAt: Date
  expiresAt: Date | null
}

export interface WorkspacePlatformServiceAccessGrantViewModel {
  workspaceId: string
  consumerKind: WorkspacePlatformServiceConsumerKind
  issuedAt: Date
  expiresAt: Date | null
  services: WorkspacePlatformServiceGrantViewModel[]
}

export interface WorkspacePlatformServiceProjectionSummaryViewModel {
  consumerKind: WorkspacePlatformServiceConsumerKind
  serviceIds: string[]
  issuedAt: Date | null
  expiresAt: Date | null
  refreshedAt: Date | null
  runtimeFilePaths: string[]
  injectErrors: string[]
}

export interface IssueWorkspacePlatformServiceAccessInput {
  consumerKind?: WorkspacePlatformServiceConsumerKind
  serviceIds?: string[]
}

export interface CreateWorkspaceInput {
  name: string
  flavour?: WorkspaceFlavour
  kind?: string
  repoSourceType?: BootstrapRepoSourceType
  repoUrl?: string | null
  userRepoId?: string | null
  shadowRepoEntityType?: string | null
  shadowRepoEntityId?: string | null
  repoRef?: string | null
  workspacePath?: string | null
  installMode?: BootstrapInstallMode
  installProfile?: string | null
  startupMode?: BootstrapStartupMode
  startupProfile?: string | null
  agentProfile?: string | null
  sshPubkey?: string | null
  envVars?: Record<string, string>
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function toBootstrapRepoSourceViewModel(
  repoSource:
    | WorkspaceExternalUrlRepoSource
    | WorkspaceUserRepoSource
    | WorkspaceShadowRepoSource
    | null
    | undefined,
): BootstrapRepoSourceViewModel | null {
  if (!repoSource?.type) return null

  if (repoSource.type === "external_url") {
    return {
      type: "external_url",
      label: "External Repository",
      detail: repoSource.repo_url,
      ref: repoSource.ref ?? null,
    }
  }

  if (repoSource.type === "user_repo") {
    return {
      type: "user_repo",
      label: "User Repo",
      detail: repoSource.repo_id,
      ref: repoSource.ref ?? null,
    }
  }

  if (repoSource.type === "shadow_repo") {
    return {
      type: "shadow_repo",
      label: "Shadow Repo",
      detail: `${repoSource.entity_type}:${repoSource.entity_id}`,
      ref: repoSource.ref ?? null,
    }
  }

  return null
}

function toBootstrapIntentViewModel(
  value: WorkspaceBootstrapIntent | null | undefined,
): BootstrapIntentViewModel | null {
  if (!value) return null

  const installIntent = value.install_intent
  const startupIntent = value.startup_intent
  const envVars = value.env_vars ?? {}

  return {
    repoSource: toBootstrapRepoSourceViewModel(value.repo_source ?? null),
    workspacePath: value.workspace_path ?? null,
    installMode:
      installIntent?.mode === "auto" || installIntent?.mode === "profile"
        ? installIntent.mode
        : "none",
    installProfile:
      installIntent?.mode === "profile" ? installIntent.profile : null,
    startupMode:
      startupIntent?.mode === "profile" ||
      startupIntent?.mode === "agent_service" ||
      startupIntent?.mode === "terminal_only"
        ? startupIntent.mode
        : "terminal_only",
    startupProfile:
      startupIntent?.mode === "profile" ? startupIntent.profile : null,
    agentProfile:
      startupIntent?.mode === "agent_service"
        ? startupIntent.agent_profile
        : null,
    envVars,
    sshPubkey: value.ssh_pubkey ?? null,
  }
}

function toBootstrapProgressViewModel(
  value: WorkspaceBootstrapProgress | null | undefined,
): BootstrapProgressViewModel | null {
  if (!value?.phase) return null

  const completedSteps =
    typeof value.completed_steps === "number" ? value.completed_steps : null
  const stepCount =
    typeof value.step_count === "number" ? value.step_count : null
  const completionRatio =
    completedSteps !== null && stepCount !== null && stepCount > 0
      ? Math.max(0, Math.min(1, completedSteps / stepCount))
      : null

  return {
    phase: value.phase as BootstrapPhase,
    message: value.message ?? null,
    stepCount,
    completedSteps,
    failureMessage: value.failure_message ?? null,
    completionRatio,
  }
}

function toReadinessSummaryViewModel(
  value: WorkspaceReadinessSummary | null | undefined,
): WorkspaceReadinessSummaryViewModel | null {
  if (!value) return null
  return {
    terminalReady: value.terminal_ready === true,
    bootstrapComplete: value.bootstrap_complete === true,
    servicesReady: value.services_ready === true,
    serviceCount:
      typeof value.service_count === "number" ? value.service_count : null,
    readyServiceCount:
      typeof value.ready_service_count === "number"
        ? value.ready_service_count
        : null,
  }
}

function toConnectivitySummaryViewModel(
  value: WorkspaceConnectivitySummary | null | undefined,
): WorkspaceConnectivitySummaryViewModel | null {
  if (!value) return null
  return {
    terminalReady: value.terminal_ready === true,
    bootstrapComplete: value.bootstrap_complete === true,
    servicesReady: value.services_ready === true,
    serviceCount:
      typeof value.service_count === "number" ? value.service_count : null,
    readyServiceCount:
      typeof value.ready_service_count === "number"
        ? value.ready_service_count
        : null,
  }
}

function toWorkspaceDiscoveredServiceViewModel(
  value: WorkspaceServiceSummary,
): WorkspaceDiscoveredServiceViewModel {
  return {
    id: value.id,
    kind: value.kind,
    label: value.label,
    status: value.status ?? "unknown",
    protocol: value.protocol ?? null,
    host: value.host ?? null,
    port: typeof value.port === "number" ? value.port : null,
    path: value.path ?? null,
    url: value.url ?? null,
    source: value.source ?? null,
    readinessMessage: value.readiness_message ?? null,
  }
}

function toWorkspaceFlavourHealthViewModel(
  value: WorkspaceFlavourHealthSummary | null | undefined,
): WorkspaceFlavourHealthSummaryViewModel | null {
  if (!value?.flavour) return null
  return {
    flavour: value.flavour,
    snapshotReady: value.snapshot_ready === true,
    latestRebuildStatus: value.latest_rebuild_status ?? null,
    latestRebuildJobId: value.latest_rebuild_job_id ?? null,
  }
}

function toWorkspaceDetailViewModel(
  workspace: WorkspacePublic,
): WorkspaceDetailViewModel {
  const status = workspace.status ?? "requested"
  const terminalUrl = workspace.terminal_url ?? null
  const allowedActions = workspace.allowed_actions ?? []
  const terminalStatus = workspace.terminal_status ?? "unavailable"
  const meta = isRecord(workspace.meta) ? workspace.meta : {}
  const bootstrapIntent = toBootstrapIntentViewModel(
    workspace.bootstrap?.intent,
  )
  const bootstrapProgress = toBootstrapProgressViewModel(
    workspace.bootstrap?.progress,
  )
  const readinessSummary = toReadinessSummaryViewModel(
    workspace.readiness_summary,
  )
  const connectivitySummary = toConnectivitySummaryViewModel(
    workspace.connectivity_summary,
  )
  const services = Array.isArray(workspace.services)
    ? workspace.services.map(toWorkspaceDiscoveredServiceViewModel)
    : []
  const flavourHealth = toWorkspaceFlavourHealthViewModel(
    workspace.flavour_health,
  )
  const bootstrapStepResults = Array.isArray(meta.bootstrap_step_results)
    ? meta.bootstrap_step_results.filter(isRecord)
    : []
  const bootstrapPlan = isRecord(meta.bootstrap_plan)
    ? meta.bootstrap_plan
    : null
  const startedServices = Array.isArray(meta.bootstrap_started_services)
    ? meta.bootstrap_started_services.filter(
        (value): value is string => typeof value === "string",
      )
    : []
  const platformServiceProjection = Array.isArray(
    meta.platform_service_projection,
  )
    ? meta.platform_service_projection
        .map(toWorkspacePlatformServiceProjectionSummaryViewModel)
        .filter(
          (
            value,
          ): value is WorkspacePlatformServiceProjectionSummaryViewModel =>
            value !== null,
        )
    : []
  const canOpenTerminal = allowedActions.includes("request_terminal")
  const canDiscoverServices = allowedActions.includes("discover_services")
  const canStart = allowedActions.includes("start")
  const canStop = allowedActions.includes("stop")
  const canDestroy = allowedActions.includes("destroy")
  const canManageRuntime = canStart || canStop || canDestroy
  const canUseWorkspace =
    canOpenTerminal || canDiscoverServices || canManageRuntime
  const accessLevel: WorkspaceAccessLevel = canManageRuntime
    ? "manage"
    : canUseWorkspace
      ? "use"
      : "view"

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
    lastTransitionAt: workspace.last_transition_at
      ? new Date(workspace.last_transition_at)
      : null,
    requestedAt: workspace.requested_at
      ? new Date(workspace.requested_at)
      : null,
    startedAt: workspace.started_at ? new Date(workspace.started_at) : null,
    readyAt: workspace.ready_at ? new Date(workspace.ready_at) : null,
    stoppedAt: workspace.stopped_at ? new Date(workspace.stopped_at) : null,
    destroyedAt: workspace.destroyed_at
      ? new Date(workspace.destroyed_at)
      : null,
    meta,
    visibility: workspace.visibility ?? "private",
    projectId: workspace.project_id ?? null,
    projectSummary: workspace.project_summary ?? null,
    terminalStatus,
    allowedActions,
    accessLevel,
    canUseWorkspace,
    canManageRuntime,
    canDiscoverServices,
    isProjectWorkspace: (workspace.visibility ?? "private") === "project",
    createdAt: new Date(workspace.created_at),
    updatedAt: new Date(workspace.updated_at),
    terminalUrl,
    hasTerminal:
      (terminalStatus === "available" || terminalStatus === "expired") &&
      canOpenTerminal,
    isProvisioning: status === "requested" || status === "provisioning",
    isStarting: status === "starting",
    isReady: status === "ready",
    isFailed: status === "failed",
    canOpenTerminal,
    canStop,
    canStart,
    canDestroy,
    bootstrapIntent,
    bootstrapProgress,
    readinessSummary,
    connectivitySummary,
    services,
    flavourHealth,
    bootstrapWorkspacePath:
      typeof meta.bootstrap_workspace_path === "string"
        ? meta.bootstrap_workspace_path
        : (bootstrapIntent?.workspacePath ?? null),
    startedServices,
    bootstrapPlanStepCount:
      bootstrapProgress?.stepCount ??
      (bootstrapPlan && Array.isArray(bootstrapPlan.steps)
        ? bootstrapPlan.steps.length
        : null),
    bootstrapStepResults,
    platformServiceProjection,
  }
}

function toWorkspaceListItemViewModel(
  workspace: WorkspacePublic,
): WorkspaceListItemViewModel {
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
    accessLevel: detail.accessLevel,
    canUseWorkspace: detail.canUseWorkspace,
    canManageRuntime: detail.canManageRuntime,
    canDiscoverServices: detail.canDiscoverServices,
    canDestroy: detail.canDestroy,
    isProjectWorkspace: detail.isProjectWorkspace,
    hasTerminal: detail.hasTerminal,
    bootstrapIntent: detail.bootstrapIntent,
    bootstrapProgress: detail.bootstrapProgress,
    readinessSummary: detail.readinessSummary,
    connectivitySummary: detail.connectivitySummary,
    services: detail.services,
    flavourHealth: detail.flavourHealth,
    bootstrapWorkspacePath: detail.bootstrapWorkspacePath,
    startedServices: detail.startedServices,
  }
}

function toWorkspaceTerminalDescriptor(
  data: Record<string, string>,
): WorkspaceTerminalDescriptor {
  const terminalUrl = data.terminal_url
  const parsed = new URL(terminalUrl)
  return {
    terminalUrl,
    protocol: parsed.protocol.replace(":", ""),
    host: parsed.host,
    isDirectConnection: true,
  }
}

function toWorkspacePlatformServiceAccessGrantViewModel(value: {
  workspace_id: string
  consumer_kind: WorkspacePlatformServiceConsumerKind
  issued_at: string
  expires_at?: string | null
  services?: Array<{
    grant_id: string
    service_id: string
    transport: string
    url: string
    auth_mode?: string
    require_approval?: string
    description?: string | null
    scopes?: string[]
    tags?: string[]
    scope?: Record<string, string>
    issued_at: string
    expires_at?: string | null
  }>
}): WorkspacePlatformServiceAccessGrantViewModel {
  return {
    workspaceId: value.workspace_id,
    consumerKind: value.consumer_kind,
    issuedAt: new Date(value.issued_at),
    expiresAt: value.expires_at ? new Date(value.expires_at) : null,
    services: Array.isArray(value.services)
      ? value.services.map((service) => ({
          grantId: service.grant_id,
          serviceId: service.service_id,
          transport: service.transport,
          url: service.url,
          authMode: service.auth_mode ?? "none",
          requireApproval: service.require_approval ?? "never",
          description: service.description ?? null,
          scopes: Array.isArray(service.scopes) ? service.scopes : [],
          tags: Array.isArray(service.tags) ? service.tags : [],
          scope: isRecord(service.scope)
            ? Object.fromEntries(
                Object.entries(service.scope).map(([key, entry]) => [
                  key,
                  String(entry),
                ]),
              )
            : {},
          issuedAt: new Date(service.issued_at),
          expiresAt: service.expires_at ? new Date(service.expires_at) : null,
        }))
      : [],
  }
}

function toWorkspacePlatformServiceProjectionSummaryViewModel(
  value: unknown,
): WorkspacePlatformServiceProjectionSummaryViewModel | null {
  if (!isRecord(value)) return null

  const consumerKind =
    value.consumer_kind === "workspace_runtime"
      ? "workspace_runtime"
      : value.consumer_kind === "agent_runtime"
        ? "agent_runtime"
        : null
  if (!consumerKind) return null

  return {
    consumerKind,
    serviceIds: Array.isArray(value.service_ids)
      ? value.service_ids.filter(
          (entry): entry is string => typeof entry === "string",
        )
      : [],
    issuedAt:
      typeof value.issued_at === "string" ? new Date(value.issued_at) : null,
    expiresAt:
      typeof value.expires_at === "string" ? new Date(value.expires_at) : null,
    refreshedAt:
      typeof value.refreshed_at === "string"
        ? new Date(value.refreshed_at)
        : null,
    runtimeFilePaths: Array.isArray(value.runtime_file_paths)
      ? value.runtime_file_paths.filter(
          (entry): entry is string => typeof entry === "string",
        )
      : [],
    injectErrors: Array.isArray(value.inject_errors)
      ? value.inject_errors.filter(
          (entry): entry is string => typeof entry === "string",
        )
      : [],
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

  async issuePlatformServiceAccess(
    workspaceId: string,
    input: IssueWorkspacePlatformServiceAccessInput = {},
  ): Promise<WorkspacePlatformServiceAccessGrantViewModel> {
    const requestOptions: ApiRequestOptions = {
      method: "POST",
      url: `/api/v1/workspaces/${workspaceId}/platform-service-access`,
      body: {
        consumer_kind: input.consumerKind ?? "workspace_runtime",
        service_ids: input.serviceIds ?? [],
      },
      mediaType: "application/json",
    }
    const response = (await __request(OpenAPI, requestOptions)) as {
      workspace_id: string
      consumer_kind: WorkspacePlatformServiceConsumerKind
      issued_at: string
      expires_at?: string | null
      services?: Array<{
        grant_id: string
        service_id: string
        transport: string
        url: string
        auth_mode?: string
        require_approval?: string
        description?: string | null
        scopes?: string[]
        tags?: string[]
        scope?: Record<string, string>
        issued_at: string
        expires_at?: string | null
      }>
    }
    return toWorkspacePlatformServiceAccessGrantViewModel(response)
  },

  async getPlatformRuntimeConfig(
    workspaceId: string,
    input: IssueWorkspacePlatformServiceAccessInput = {},
  ): Promise<WorkspacePlatformServiceAccessGrantViewModel> {
    const requestOptions: ApiRequestOptions = {
      method: "POST",
      url: `/api/v1/workspaces/${workspaceId}/platform-runtime-config`,
      body: {
        consumer_kind: input.consumerKind ?? "workspace_runtime",
        service_ids: input.serviceIds ?? [],
      },
      mediaType: "application/json",
    }
    const response = (await __request(OpenAPI, requestOptions)) as {
      workspace_id: string
      consumer_kind: WorkspacePlatformServiceConsumerKind
      issued_at: string
      expires_at?: string | null
      services?: Array<{
        grant_id: string
        service_id: string
        transport: string
        url: string
        auth_mode?: string
        require_approval?: string
        description?: string | null
        scopes?: string[]
        tags?: string[]
        scope?: Record<string, string>
        issued_at: string
        expires_at?: string | null
      }>
    }
    return toWorkspacePlatformServiceAccessGrantViewModel(response)
  },

  async refreshPlatformRuntimeProjection(
    workspaceId: string,
    input: IssueWorkspacePlatformServiceAccessInput = {},
  ): Promise<WorkspacePlatformServiceAccessGrantViewModel> {
    const requestOptions: ApiRequestOptions = {
      method: "POST",
      url: `/api/v1/workspaces/${workspaceId}/platform-runtime-projection/refresh`,
      body: {
        consumer_kind: input.consumerKind ?? "workspace_runtime",
        service_ids: input.serviceIds ?? [],
      },
      mediaType: "application/json",
    }
    const response = (await __request(OpenAPI, requestOptions)) as {
      workspace_id: string
      consumer_kind: WorkspacePlatformServiceConsumerKind
      issued_at: string
      expires_at?: string | null
      services?: Array<{
        grant_id: string
        service_id: string
        transport: string
        url: string
        auth_mode?: string
        require_approval?: string
        description?: string | null
        scopes?: string[]
        tags?: string[]
        scope?: Record<string, string>
        issued_at: string
        expires_at?: string | null
      }>
    }
    return toWorkspacePlatformServiceAccessGrantViewModel(response)
  },

  async createWorkspace(
    input: CreateWorkspaceInput,
  ): Promise<WorkspaceDetailViewModel> {
    const repoSource =
      input.repoSourceType === "external_url" && input.repoUrl
        ? ({
            type: "external_url" as const,
            repo_url: input.repoUrl,
            ref: input.repoRef ?? undefined,
          } satisfies WorkspaceExternalUrlRepoSource)
        : input.repoSourceType === "user_repo" && input.userRepoId
          ? ({
              type: "user_repo" as const,
              repo_id: input.userRepoId,
              ref: input.repoRef ?? undefined,
            } satisfies WorkspaceUserRepoSource)
          : input.repoSourceType === "shadow_repo" &&
              input.shadowRepoEntityType &&
              input.shadowRepoEntityId
            ? ({
                type: "shadow_repo" as const,
                entity_type: input.shadowRepoEntityType,
                entity_id: input.shadowRepoEntityId,
                ref: input.repoRef ?? undefined,
              } satisfies WorkspaceShadowRepoSource)
            : null

    const bootstrap =
      repoSource ||
      input.workspacePath ||
      input.installMode !== undefined ||
      input.startupMode !== undefined ||
      input.sshPubkey ||
      (input.envVars && Object.keys(input.envVars).length > 0)
        ? ({
            repo_source: repoSource ?? undefined,
            workspace_path: input.workspacePath ?? undefined,
            install_intent:
              input.installMode === "auto"
                ? ({
                    mode: "auto" as const,
                  } satisfies WorkspaceInstallIntentAuto)
                : input.installMode === "profile" && input.installProfile
                  ? ({
                      mode: "profile" as const,
                      profile: input.installProfile,
                    } satisfies WorkspaceInstallIntentProfile)
                  : ({
                      mode: "none" as const,
                    } satisfies WorkspaceInstallIntentNone),
            startup_intent:
              input.startupMode === "profile" && input.startupProfile
                ? ({
                    mode: "profile" as const,
                    profile: input.startupProfile,
                  } satisfies WorkspaceStartupIntentProfile)
                : input.startupMode === "agent_service" && input.agentProfile
                  ? ({
                      mode: "agent_service" as const,
                      agent_profile: input.agentProfile,
                    } satisfies WorkspaceStartupIntentAgentService)
                  : ({
                      mode: "terminal_only" as const,
                    } satisfies WorkspaceStartupIntentTerminalOnly),
            ssh_pubkey: input.sshPubkey ?? undefined,
            env_vars: input.envVars ?? {},
          } satisfies WorkspaceBootstrapIntent)
        : undefined

    const requestBody: WorkspaceCreate = {
      name: input.name,
      flavour: input.flavour,
      kind: input.kind,
      repo_url:
        input.repoSourceType === "external_url" ? input.repoUrl : undefined,
      ssh_pubkey: input.sshPubkey,
      env_vars: input.envVars,
      bootstrap,
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

  async getTerminalDescriptor(
    workspaceId: string,
  ): Promise<WorkspaceTerminalDescriptor> {
    const response = await WorkspacesService.getWorkspaceTerminal({
      workspaceId,
    })
    return toWorkspaceTerminalDescriptor(response as Record<string, string>)
  },
}
