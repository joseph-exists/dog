import {
  AccessService,
  AgentsService,
  DemosService,
  GroupsService,
  PersonaGroupsService,
  ProjectsService,
  RoomsService,
  StoriesService,
  UserPersonasService,
  UsersService,
  UserReposService,
  type AccessGrantPublic,
  type AccessGrantRevokeRequest,
  type AccessGrantRole,
  type AccessGrantSubjectType,
  type AccessGrantUpsertRequest,
  type ProjectCreate,
  type PersonaGroupCreate,
  type PersonaGroupMembershipCreate,
  type PersonaGroupMembershipPublic,
  type PersonaGroupPublic,
  type ProjectPublic,
  type ProjectResourceCreate,
  type ProjectResourcePublic,
  type ProjectUpdate,
  type UserGroupPublic,
  type UserPersonaPublic,
} from "@/client"
import { OpenAPI } from "@/client"
import type { ApiRequestOptions } from "@/client/core/ApiRequestOptions"
import { request as __request } from "@/client/core/request"

export type AttachableResourceType =
  | "agent"
  | "story"
  | "demo_session"
  | "room"
  | "user_repo"

export type AttachableResourceScope = "owned" | "available"

export interface AttachableResourceOption {
  resourceType: AttachableResourceType
  resourceId: string
  label: string
  subtitle?: string
  scope: AttachableResourceScope
}

export const ProjectsAppService = {
  async listProjects(skip = 0, limit = 100): Promise<ProjectPublic[]> {
    const response = await ProjectsService.listProjects({ skip, limit })
    return response.data
  },

  async getProject(projectId: string): Promise<ProjectPublic> {
    return ProjectsService.getProject({ projectId })
  },

  async createProject(input: ProjectCreate): Promise<ProjectPublic> {
    return ProjectsService.createNewProject({ requestBody: input })
  },

  async updateProject(
    projectId: string,
    input: ProjectUpdate,
  ): Promise<ProjectPublic> {
    return ProjectsService.patchProject({ projectId, requestBody: input })
  },

  async deleteProject(projectId: string): Promise<void> {
    await ProjectsService.deleteProjectRoute({ projectId })
  },

  async listProjectResources(projectId: string): Promise<ProjectResourcePublic[]> {
    const response = await ProjectsService.getProjectResources({ projectId })
    return response.data
  },

  async addProjectResource(
    projectId: string,
    input: ProjectResourceCreate,
  ): Promise<ProjectResourcePublic> {
    return ProjectsService.addProjectResource({ projectId, requestBody: input })
  },

  async removeProjectResource(
    projectId: string,
    input: ProjectResourceCreate,
  ): Promise<void> {
    await ProjectsService.removeProjectResource({ projectId, requestBody: input })
  },

  async listProjectAccessGrants(projectId: string): Promise<AccessGrantPublic[]> {
    const response = await AccessService.listResourceAccessGrants({
      resourceType: "project",
      resourceId: projectId,
    })
    return response.data
  },

  async upsertProjectAccessGrant(
    projectId: string,
    input: AccessGrantUpsertRequest,
  ): Promise<AccessGrantPublic> {
    return AccessService.upsertResourceAccessGrant({
      resourceType: "project",
      resourceId: projectId,
      requestBody: input,
    })
  },

  async revokeProjectAccessGrant(
    projectId: string,
    input: AccessGrantRevokeRequest,
  ): Promise<void> {
    await AccessService.revokeResourceAccessGrant({
      resourceType: "project",
      resourceId: projectId,
      requestBody: input,
    })
  },

  async getMyEffectiveProjectRole(
    projectId: string,
  ): Promise<ProjectGrantRole | null> {
    const options: ApiRequestOptions<{ role: AccessGrantRole | null }> = {
      method: "GET",
      url: `/api/v1/access/project/${projectId}/me`,
    }
    const response = await __request<{ role: AccessGrantRole | null }>(
      OpenAPI,
      options,
    )
    return response.role ?? null
  },

  async listMyGroups(): Promise<UserGroupPublic[]> {
    const response = await GroupsService.listUserGroups()
    return response.data
  },

  async listMyUserPersonas(): Promise<UserPersonaPublic[]> {
    const response = await UserPersonasService.readUserPersonas({ skip: 0, limit: 100 })
    return response.data
  },

  async listMyPersonaGroups(): Promise<PersonaGroupPublic[]> {
    const response = await PersonaGroupsService.listPersonaGroups({ skip: 0, limit: 100 })
    return response.data
  },

  async createPersonaGroup(input: PersonaGroupCreate): Promise<PersonaGroupPublic> {
    return PersonaGroupsService.createNewPersonaGroup({ requestBody: input })
  },

  async listPersonaGroupMembers(
    groupId: string,
  ): Promise<PersonaGroupMembershipPublic[]> {
    const response = await PersonaGroupsService.listPersonaGroupMembers({ groupId })
    return response.data
  },

  async addPersonaGroupMember(
    groupId: string,
    input: PersonaGroupMembershipCreate,
  ): Promise<PersonaGroupMembershipPublic> {
    return PersonaGroupsService.addPersonaGroupMember({
      groupId,
      requestBody: input,
    })
  },

  async listAttachableResourceOptions(): Promise<AttachableResourceOption[]> {
    const [currentUser, stories, sessions, repos, rooms, agents] = await Promise.all([
      UsersService.readUserMe(),
      StoriesService.readStories({ skip: 0, limit: 100 }),
      DemosService.listMyDemoSessions({ skip: 0, limit: 100 }),
      UserReposService.listUserRepos(),
      RoomsService.listUserRooms({ skip: 0, limit: 100 }),
      AgentsService.listAvailableAgents({ skip: 0, limit: 100 }),
    ])

    const storyOptions: AttachableResourceOption[] = stories.data.map((story) => ({
      resourceType: "story",
      resourceId: story.id,
      label: story.title,
      subtitle: story.description ?? "Story",
      scope: story.owner_id === currentUser.id ? "owned" : "available",
    }))

    const sessionOptions: AttachableResourceOption[] = sessions.data.map(
      (session) => ({
        resourceType: "demo_session",
        resourceId: session.id,
        label: `Demo Session ${session.id.slice(0, 8)}`,
        subtitle: `Room ${session.room_id.slice(0, 8)}`,
        scope: session.user_id === currentUser.id ? "owned" : "available",
      }),
    )

    const repoOptions: AttachableResourceOption[] = repos.data.map((repo) => ({
      resourceType: "user_repo",
      resourceId: repo.id,
      label: repo.display_name,
      subtitle: repo.import_status,
      scope: repo.owner_user_id === currentUser.id ? "owned" : "available",
    }))

    const roomOptions: AttachableResourceOption[] = rooms.data.map((room) => ({
      resourceType: "room",
      resourceId: room.room_id,
      label: room.title ?? `Room ${room.room_id.slice(0, 8)}`,
      subtitle: room.story_id ? `Story ${room.story_id.slice(0, 8)}` : "No story",
      scope: room.creator_id === currentUser.id ? "owned" : "available",
    }))

    const agentOptions: AttachableResourceOption[] = agents.data.map((agent) => ({
      resourceType: "agent",
      resourceId: agent.id,
      label: agent.name ?? agent.slug ?? `Agent ${agent.id.slice(0, 8)}`,
      subtitle: agent.description ?? agent.model_name ?? agent.scope ?? "Agent",
      scope: agent.owner_id === currentUser.id ? "owned" : "available",
    }))

    return [...storyOptions, ...sessionOptions, ...repoOptions, ...roomOptions, ...agentOptions]
  },
}

export type ProjectGrantRole = AccessGrantRole
export type ProjectGrantSubjectType = AccessGrantSubjectType
