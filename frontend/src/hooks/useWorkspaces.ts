import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import type { ApiError, WorkspaceFlavour } from "@/client"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import {
  type BootstrapInstallMode,
  type BootstrapRepoSourceType,
  type BootstrapStartupMode,
  type CreateWorkspaceInput,
  type IssueWorkspacePlatformServiceAccessInput,
  WorkspaceService,
} from "@/services/workspaceService"
import { handleError } from "@/utils"

export const workspaceKeys = {
  all: ["workspaces"] as const,
  list: () => [...workspaceKeys.all, "list"] as const,
  detail: (workspaceId: string) =>
    [...workspaceKeys.all, "detail", workspaceId] as const,
  terminal: (workspaceId: string) =>
    [...workspaceKeys.all, "terminal", workspaceId] as const,
}

export interface CreateWorkspaceFormInput {
  name: string
  flavour?: WorkspaceFlavour
  runtimePreset?: string
  kind?: string
  repoSourceType?: BootstrapRepoSourceType
  repoUrl?: string
  userRepoId?: string
  shadowRepoEntityType?: string
  shadowRepoEntityId?: string
  repoRef?: string
  workspacePath?: string
  installMode?: BootstrapInstallMode
  installProfile?: string
  startupMode?: BootstrapStartupMode
  startupProfile?: string
  agentProfile?: string
  sshPubkey?: string
  envVarsText?: string
  bootstrapProfile?: string
  runtimeFiles?: Array<{
    path: string
    content: string
  }>
}

function parseEnvVars(text: string | undefined): Record<string, string> {
  if (!text) return {}
  const result: Record<string, string> = {}
  for (const line of text.split("\n")) {
    const trimmed = line.trim()
    if (!trimmed || trimmed.startsWith("#")) continue
    const equalsIndex = trimmed.indexOf("=")
    if (equalsIndex <= 0) continue
    const key = trimmed.slice(0, equalsIndex).trim()
    const value = trimmed.slice(equalsIndex + 1).trim()
    if (key) result[key] = value
  }
  return result
}

function toRuntimeFiles(
  entries: CreateWorkspaceFormInput["runtimeFiles"],
): Record<string, string> {
  const result: Record<string, string> = {}
  for (const entry of entries ?? []) {
    const path = entry.path.trim()
    if (!path) continue
    result[path] = entry.content
  }
  return result
}

function toCreateWorkspaceInput(
  input: CreateWorkspaceFormInput,
): CreateWorkspaceInput {
  const runtimeFiles = toRuntimeFiles(input.runtimeFiles)
  return {
    name: input.name.trim(),
    flavour: input.flavour ?? "dev",
    runtimePreset: input.runtimePreset?.trim() || null,
    kind: input.kind ?? "ephemeral",
    repoSourceType: input.repoSourceType ?? "none",
    repoUrl: input.repoUrl?.trim() || null,
    userRepoId: input.userRepoId?.trim() || null,
    shadowRepoEntityType: input.shadowRepoEntityType?.trim() || null,
    shadowRepoEntityId: input.shadowRepoEntityId?.trim() || null,
    repoRef: input.repoRef?.trim() || null,
    workspacePath: input.workspacePath?.trim() || null,
    installMode: input.installMode ?? "none",
    installProfile: input.installProfile?.trim() || null,
    startupMode: input.startupMode ?? "terminal_only",
    startupProfile: input.startupProfile?.trim() || null,
    agentProfile: input.agentProfile?.trim() || null,
    sshPubkey: input.sshPubkey?.trim() || null,
    envVars: parseEnvVars(input.envVarsText),
    bootstrapProfile: input.bootstrapProfile?.trim() || null,
    runtimeFiles,
  }
}

export function useWorkspaces() {
  return useQuery({
    queryKey: workspaceKeys.list(),
    queryFn: () => WorkspaceService.listWorkspaces(),
    staleTime: 5_000,
  })
}

export function useCreateWorkspace() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (input: CreateWorkspaceFormInput) =>
      WorkspaceService.createWorkspace(toCreateWorkspaceInput(input)),
    onSuccess: (workspace) => {
      showSuccessToast(`Workspace "${workspace.name}" is provisioning.`)
      queryClient.invalidateQueries({ queryKey: workspaceKeys.all })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err)
    },
  })
}

export function useStopWorkspace() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (workspaceId: string) =>
      WorkspaceService.stopWorkspace(workspaceId),
    onSuccess: () => {
      showSuccessToast("Workspace stop requested.")
      queryClient.invalidateQueries({ queryKey: workspaceKeys.all })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err)
    },
  })
}

export function useStartWorkspace() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (workspaceId: string) =>
      WorkspaceService.startWorkspace(workspaceId),
    onSuccess: () => {
      showSuccessToast("Workspace start requested.")
      queryClient.invalidateQueries({ queryKey: workspaceKeys.all })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err)
    },
  })
}

export function useDestroyWorkspace() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (workspaceId: string) =>
      WorkspaceService.destroyWorkspace(workspaceId),
    onSuccess: () => {
      showSuccessToast("Workspace destroyed.")
      queryClient.invalidateQueries({ queryKey: workspaceKeys.all })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err)
    },
  })
}

export function useIssueWorkspacePlatformServiceAccess(workspaceId: string) {
  return useMutation({
    mutationFn: (input: IssueWorkspacePlatformServiceAccessInput) =>
      WorkspaceService.issuePlatformServiceAccess(workspaceId, input),
    onSuccess: (grant) => {
      showSuccessToast(
        `Issued ${grant.services.length} platform service grant${grant.services.length === 1 ? "" : "s"} for ${grant.consumerKind.replaceAll("_", " ")}.`,
      )
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err)
    },
  })
}

export function useWorkspacePlatformRuntimeConfig(workspaceId: string) {
  return useMutation({
    mutationFn: (input: IssueWorkspacePlatformServiceAccessInput) =>
      WorkspaceService.getPlatformRuntimeConfig(workspaceId, input),
    onSuccess: (config) => {
      showSuccessToast(
        `Resolved runtime config with ${config.services.length} platform service${config.services.length === 1 ? "" : "s"} for ${config.consumerKind.replaceAll("_", " ")}.`,
      )
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err)
    },
  })
}

export function useRefreshWorkspacePlatformRuntimeProjection(
  workspaceId: string,
) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (input: IssueWorkspacePlatformServiceAccessInput) =>
      WorkspaceService.refreshPlatformRuntimeProjection(workspaceId, input),
    onSuccess: (config) => {
      showSuccessToast(
        `Refreshed runtime projection for ${config.consumerKind.replaceAll("_", " ")}.`,
      )
      queryClient.invalidateQueries({
        queryKey: workspaceKeys.detail(workspaceId),
      })
      queryClient.invalidateQueries({ queryKey: workspaceKeys.list() })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err)
    },
  })
}
