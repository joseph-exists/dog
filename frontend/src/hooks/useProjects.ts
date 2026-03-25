import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import type {
  ApiError,
  AccessGrantRevokeRequest,
  AccessGrantUpsertRequest,
  PersonaGroupCreate,
  PersonaGroupMembershipCreate,
  ProjectCreate,
  ProjectResourceCreate,
  ProjectUpdate,
} from "@/client"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import { ProjectsAppService } from "@/services/projectsService"
import { handleError } from "@/utils"

export const projectsQueryKeys = {
  all: ["projects"] as const,
  detail: (projectId: string) => [...projectsQueryKeys.all, projectId] as const,
  resources: (projectId: string) =>
    [...projectsQueryKeys.detail(projectId), "resources"] as const,
  grants: (projectId: string) =>
    [...projectsQueryKeys.detail(projectId), "grants"] as const,
  myRole: (projectId: string) =>
    [...projectsQueryKeys.detail(projectId), "my-role"] as const,
  groups: () => ["groups", "mine"] as const,
  userPersonas: () => ["user-personas", "mine"] as const,
  personaGroups: () => ["persona-groups", "mine"] as const,
  personaGroupMembers: (groupId: string) =>
    [...projectsQueryKeys.personaGroups(), groupId, "members"] as const,
  attachable: () => ["projects", "attachable"] as const,
}

export function useProjectsList() {
  return useQuery({
    queryKey: projectsQueryKeys.all,
    queryFn: () => ProjectsAppService.listProjects(),
  })
}

export function useProject(projectId: string) {
  return useQuery({
    queryKey: projectsQueryKeys.detail(projectId),
    queryFn: () => ProjectsAppService.getProject(projectId),
    enabled: Boolean(projectId),
  })
}

export function useProjectResources(projectId: string, enabled = true) {
  return useQuery({
    queryKey: projectsQueryKeys.resources(projectId),
    queryFn: () => ProjectsAppService.listProjectResources(projectId),
    enabled: Boolean(projectId) && enabled,
  })
}

export function useProjectAccessGrants(projectId: string, enabled = true) {
  return useQuery({
    queryKey: projectsQueryKeys.grants(projectId),
    queryFn: () => ProjectsAppService.listProjectAccessGrants(projectId),
    enabled: Boolean(projectId) && enabled,
  })
}

export function useProjectMyRole(projectId: string, enabled = true) {
  return useQuery({
    queryKey: projectsQueryKeys.myRole(projectId),
    queryFn: () => ProjectsAppService.getMyEffectiveProjectRole(projectId),
    enabled: Boolean(projectId) && enabled,
  })
}

export function useMyGroups(enabled = true) {
  return useQuery({
    queryKey: projectsQueryKeys.groups(),
    queryFn: () => ProjectsAppService.listMyGroups(),
    enabled,
  })
}

export function useMyUserPersonas(enabled = true) {
  return useQuery({
    queryKey: projectsQueryKeys.userPersonas(),
    queryFn: () => ProjectsAppService.listMyUserPersonas(),
    enabled,
  })
}

export function useMyPersonaGroups(enabled = true) {
  return useQuery({
    queryKey: projectsQueryKeys.personaGroups(),
    queryFn: () => ProjectsAppService.listMyPersonaGroups(),
    enabled,
  })
}

export function usePersonaGroupMembers(groupId: string, enabled = true) {
  return useQuery({
    queryKey: projectsQueryKeys.personaGroupMembers(groupId),
    queryFn: () => ProjectsAppService.listPersonaGroupMembers(groupId),
    enabled: Boolean(groupId) && enabled,
  })
}

export function useAttachableResources(enabled = true) {
  return useQuery({
    queryKey: projectsQueryKeys.attachable(),
    queryFn: () => ProjectsAppService.listAttachableResourceOptions(),
    enabled,
  })
}

export function useCreatePersonaGroup() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: PersonaGroupCreate) => ProjectsAppService.createPersonaGroup(input),
    onSuccess: () => {
      showSuccessToast("Persona group created")
      queryClient.invalidateQueries({ queryKey: projectsQueryKeys.personaGroups() })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })
}

export function useAddPersonaGroupMember(groupId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: PersonaGroupMembershipCreate) =>
      ProjectsAppService.addPersonaGroupMember(groupId, input),
    onSuccess: () => {
      showSuccessToast("Persona added to group")
      queryClient.invalidateQueries({
        queryKey: projectsQueryKeys.personaGroupMembers(groupId),
      })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })
}

export function useCreateProject() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: ProjectCreate) => ProjectsAppService.createProject(input),
    onSuccess: () => {
      showSuccessToast("Project created")
      queryClient.invalidateQueries({ queryKey: projectsQueryKeys.all })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })
}

export function useUpdateProject(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: ProjectUpdate) =>
      ProjectsAppService.updateProject(projectId, input),
    onSuccess: () => {
      showSuccessToast("Project updated")
      queryClient.invalidateQueries({ queryKey: projectsQueryKeys.all })
      queryClient.invalidateQueries({
        queryKey: projectsQueryKeys.detail(projectId),
      })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })
}

export function useDeleteProject() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (projectId: string) => ProjectsAppService.deleteProject(projectId),
    onSuccess: () => {
      showSuccessToast("Project deleted")
      queryClient.invalidateQueries({ queryKey: projectsQueryKeys.all })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })
}

export function useAddProjectResource(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: ProjectResourceCreate) =>
      ProjectsAppService.addProjectResource(projectId, input),
    onSuccess: () => {
      showSuccessToast("Resource attached")
      queryClient.invalidateQueries({
        queryKey: projectsQueryKeys.resources(projectId),
      })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })
}

export function useRemoveProjectResource(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: ProjectResourceCreate) =>
      ProjectsAppService.removeProjectResource(projectId, input),
    onSuccess: () => {
      showSuccessToast("Resource detached")
      queryClient.invalidateQueries({
        queryKey: projectsQueryKeys.resources(projectId),
      })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })
}

export function useAttachProjectResource() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      projectId,
      input,
    }: {
      projectId: string
      input: ProjectResourceCreate
    }) => ProjectsAppService.addProjectResource(projectId, input),
    onSuccess: (_result, variables) => {
      showSuccessToast("Resource attached")
      queryClient.invalidateQueries({
        queryKey: projectsQueryKeys.resources(variables.projectId),
      })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })
}

export function useDetachProjectResource() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      projectId,
      input,
    }: {
      projectId: string
      input: ProjectResourceCreate
    }) => ProjectsAppService.removeProjectResource(projectId, input),
    onSuccess: (_result, variables) => {
      showSuccessToast("Resource detached")
      queryClient.invalidateQueries({
        queryKey: projectsQueryKeys.resources(variables.projectId),
      })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })
}

export function useUpsertProjectGrant(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: AccessGrantUpsertRequest) =>
      ProjectsAppService.upsertProjectAccessGrant(projectId, input),
    onSuccess: () => {
      showSuccessToast("Access updated")
      queryClient.invalidateQueries({ queryKey: projectsQueryKeys.grants(projectId) })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })
}

export function useRevokeProjectGrant(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: AccessGrantRevokeRequest) =>
      ProjectsAppService.revokeProjectAccessGrant(projectId, input),
    onSuccess: () => {
      showSuccessToast("Access revoked")
      queryClient.invalidateQueries({ queryKey: projectsQueryKeys.grants(projectId) })
    },
    onError: (err: ApiError) => {
      handleError.call(showErrorToast, err as ApiError)
    },
  })
}
