import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import type { ApiError, WorkspaceFlavour } from "@/client"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import {
  type CreateWorkspaceInput,
  WorkspaceService,
} from "@/services/workspaceService"

export const workspaceKeys = {
  all: ["workspaces"] as const,
  list: () => [...workspaceKeys.all, "list"] as const,
  detail: (workspaceId: string) => [...workspaceKeys.all, "detail", workspaceId] as const,
  terminal: (workspaceId: string) => [...workspaceKeys.all, "terminal", workspaceId] as const,
}

export interface CreateWorkspaceFormInput {
  name: string
  flavour?: WorkspaceFlavour
  kind?: string
  repoUrl?: string
  sshPubkey?: string
  envVarsText?: string
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

function toCreateWorkspaceInput(input: CreateWorkspaceFormInput): CreateWorkspaceInput {
  return {
    name: input.name.trim(),
    flavour: input.flavour ?? "dev",
    kind: input.kind ?? "ephemeral",
    repoUrl: input.repoUrl?.trim() || null,
    sshPubkey: input.sshPubkey?.trim() || null,
    envVars: parseEnvVars(input.envVarsText),
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
    mutationFn: (workspaceId: string) => WorkspaceService.stopWorkspace(workspaceId),
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
    mutationFn: (workspaceId: string) => WorkspaceService.startWorkspace(workspaceId),
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
    mutationFn: (workspaceId: string) => WorkspaceService.destroyWorkspace(workspaceId),
    onSuccess: () => {
      showSuccessToast("Workspace destroyed.")
      queryClient.invalidateQueries({ queryKey: workspaceKeys.all })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err)
    },
  })
}
