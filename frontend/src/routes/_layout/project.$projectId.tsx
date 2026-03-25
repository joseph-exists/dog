import { useEffect, useMemo, useRef, useState } from "react"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { Loader2, Trash2, Unplug, Users2 } from "lucide-react"
import { PageShell } from "@/components/Page"
import { DiscoverUserPersonaCombobox } from "@/components/UserPage/DiscoverUserPersonaCombobox"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import type { EntityComboboxOption } from "@/components/ui/entity-combobox"
import { EntityCombobox } from "@/components/ui/entity-combobox"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import useAuth from "@/hooks/useAuth"
import { usePageEditor } from "@/hooks/usePageEditor"
import {
  useAddProjectResource,
  useAddPersonaGroupMember,
  useAttachableResources,
  useCreatePersonaGroup,
  useDeleteProject,
  useMyGroups,
  useMyPersonaGroups,
  useMyUserPersonas,
  usePersonaGroupMembers,
  useProject,
  useProjectAccessGrants,
  useProjectMyRole,
  useProjectResources,
  useRemoveProjectResource,
  useRevokeProjectGrant,
  useUpdateProject,
  useUpsertProjectGrant,
} from "@/hooks/useProjects"
import type { AttachableResourceType } from "@/services/projectsService"

const resourceTypeLabels: Record<AttachableResourceType, string> = {
  agent: "Agent",
  story: "Story",
  demo_session: "Demo",
  room: "Room",
  workspace: "Workspace",
  user_repo: "Repo",
}

export const Route = createFileRoute("/_layout/project/$projectId")({
  component: ProjectDetailPage,
  head: () => ({
    meta: [{ title: "Project Workspace" }],
  }),
})

function ProjectDetailPage() {
  const { projectId } = Route.useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const creatingRef = useRef(false)

  const { data: project, isLoading: isProjectLoading, error } = useProject(projectId)
  const isOwnerOrSuperuser = !!user && (
    user.id === project?.owner_id || Boolean(user.is_superuser)
  )
  const { data: myProjectRole } = useProjectMyRole(projectId, Boolean(project))
  const canManageProject = Boolean(project) && isOwnerOrSuperuser
  const canEditProjectLayout = Boolean(project) && (
    isOwnerOrSuperuser || myProjectRole === "editor" || myProjectRole === "manager"
  )

  const {
    isLoading: isPageLoading,
    pageExists,
    createPage,
  } = usePageEditor("project", projectId)

  const { data: resources, isLoading: isResourcesLoading } = useProjectResources(projectId)
  const { data: grants, isLoading: isGrantsLoading } = useProjectAccessGrants(
    projectId,
    canManageProject,
  )
  const { data: groups } = useMyGroups(canManageProject)
  const { data: userPersonas } = useMyUserPersonas(canManageProject)
  const { data: personaGroups } = useMyPersonaGroups(canManageProject)
  const { data: attachable } = useAttachableResources(canManageProject)

  const updateProject = useUpdateProject(projectId)
  const deleteProject = useDeleteProject()
  const addResource = useAddProjectResource(projectId)
  const removeResource = useRemoveProjectResource(projectId)
  const upsertGrant = useUpsertProjectGrant(projectId)
  const revokeGrant = useRevokeProjectGrant(projectId)
  const createPersonaGroup = useCreatePersonaGroup()

  const [nameDraft, setNameDraft] = useState("")
  const [descriptionDraft, setDescriptionDraft] = useState("")
  const [resourceType, setResourceType] = useState<AttachableResourceType>("story")
  const [resourceScope, setResourceScope] = useState<"owned" | "available">("owned")
  const [resourceId, setResourceId] = useState("")
  const [attachSelection, setAttachSelection] = useState("")
  const [grantSubjectType, setGrantSubjectType] = useState<
    "user" | "group" | "user_persona" | "persona_group"
  >("persona_group")
  const [grantRole, setGrantRole] = useState<"viewer" | "editor">("viewer")
  const [grantSubjectId, setGrantSubjectId] = useState("")
  const [newPersonaGroupName, setNewPersonaGroupName] = useState("")
  const [newPersonaGroupOwnerId, setNewPersonaGroupOwnerId] = useState("")
  const [selectedPersonaGroupId, setSelectedPersonaGroupId] = useState("")
  const [personaGroupMemberId, setPersonaGroupMemberId] = useState("")

  const { data: personaGroupMembers } = usePersonaGroupMembers(
    selectedPersonaGroupId,
    canManageProject,
  )
  const addPersonaGroupMember = useAddPersonaGroupMember(selectedPersonaGroupId)

  const ownedPersonaOptions = useMemo<EntityComboboxOption[]>(
    () =>
      (userPersonas ?? []).map((persona) => ({
        value: persona.id,
        label: persona.nickname?.trim() || `Persona ${persona.id.slice(0, 8)}`,
        subtitle: persona.description?.trim() || persona.persona_id,
        keywords: [persona.persona_id, persona.id, persona.nickname ?? ""],
      })),
    [userPersonas],
  )

  const personaGroupOptions = useMemo<EntityComboboxOption[]>(
    () =>
      (personaGroups ?? []).map((group) => {
        const ownerPersona = ownedPersonaOptions.find(
          (persona) => persona.value === group.owner_user_persona_id,
        )
        return {
          value: group.id,
          label: group.name,
          subtitle: ownerPersona
            ? `Owned by ${ownerPersona.label}`
            : group.group_type ?? "persona group",
          keywords: [group.id, group.name, group.owner_user_persona_id],
        }
      }),
    [ownedPersonaOptions, personaGroups],
  )

  const groupOptions = useMemo<EntityComboboxOption[]>(
    () =>
      (groups ?? []).map((group) => ({
        value: group.id,
        label: group.name,
        subtitle: group.id,
        keywords: [group.id, group.name],
      })),
    [groups],
  )

  const personaOptionById = useMemo(
    () => new Map(ownedPersonaOptions.map((option) => [option.value, option])),
    [ownedPersonaOptions],
  )
  const personaGroupOptionById = useMemo(
    () => new Map(personaGroupOptions.map((option) => [option.value, option])),
    [personaGroupOptions],
  )
  const groupOptionById = useMemo(
    () => new Map(groupOptions.map((option) => [option.value, option])),
    [groupOptions],
  )

  const selectedPersonaGroupOption = personaGroupOptionById.get(selectedPersonaGroupId)

  const selectedAttachOption = useMemo(
    () =>
      (attachable ?? []).find(
        (item) => `${item.resourceType}:${item.resourceId}` === attachSelection,
      ),
    [attachSelection, attachable],
  )

  const filteredAttachableOptions = useMemo(
    () =>
      (attachable ?? []).filter(
        (item) =>
          item.resourceType === resourceType &&
          (resourceScope === "available" || item.scope === "owned"),
      ),
    [attachable, resourceScope, resourceType],
  )

  useEffect(() => {
    if (
      isPageLoading ||
      pageExists ||
      !project ||
      !canEditProjectLayout ||
      creatingRef.current
    ) {
      return
    }
    creatingRef.current = true

    createPage("standard", {
      identity: {
        name: project.name,
        tagline: project.description ?? "",
      },
      bio: {
        text: project.description ?? "",
      },
    }).catch(() => {
      creatingRef.current = false
    })
  }, [isPageLoading, pageExists, project, canEditProjectLayout, createPage])

  if (isProjectLoading) {
    return (
      <div className="container mx-auto max-w-7xl py-8 space-y-4">
        <Skeleton className="h-10 w-72" />
        <Skeleton className="h-56 rounded-xl" />
        <Skeleton className="h-72 rounded-xl" />
      </div>
    )
  }

  if (error || !project) {
    return (
      <div className="container mx-auto max-w-5xl py-8">
        <Card>
          <CardHeader>
            <CardTitle>Project unavailable</CardTitle>
            <CardDescription>
              {error?.message ?? "The project was not found or you do not have access."}
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    )
  }

  const onSaveProject = async () => {
    await updateProject.mutateAsync({
      name: (nameDraft || project.name).trim(),
      description: (descriptionDraft || project.description || "").trim() || null,
    })
    setNameDraft("")
    setDescriptionDraft("")
  }

  const onDeleteProject = async () => {
    const confirmed = window.confirm(
      "Delete this project? This removes project associations and grants.",
    )
    if (!confirmed) return
    await deleteProject.mutateAsync(projectId)
    navigate({ to: "/projects" })
  }

  const onAttachResource = async () => {
    const effectiveType = selectedAttachOption?.resourceType ?? resourceType
    const effectiveId = selectedAttachOption?.resourceId ?? resourceId.trim()
    if (!effectiveId) return

    await addResource.mutateAsync({
      resource_type: effectiveType,
      resource_id: effectiveId,
    })
    setResourceId("")
    setAttachSelection("")
  }

  const onGrantAccess = async () => {
    const subjectId = grantSubjectId.trim()
    if (!subjectId) return
    await upsertGrant.mutateAsync({
      subject_type: grantSubjectType,
      subject_id: subjectId,
      role: grantRole,
    })
    if (grantSubjectType === "user" || grantSubjectType === "user_persona") {
      setGrantSubjectId("")
    }
  }

  const grantSubjectDescriptor =
    grantSubjectType === "persona_group"
      ? "Persona group"
      : grantSubjectType === "user_persona"
        ? "User persona"
        : grantSubjectType === "group"
          ? "Legacy user group"
          : "User account"

  const describeGrantSubject = (subjectType: typeof grantSubjectType, subjectId: string) => {
    if (subjectType === "persona_group") {
      return (
        personaGroupOptionById.get(subjectId) ?? {
          value: subjectId,
          label: "Persona group",
          subtitle: subjectId,
        }
      )
    }
    if (subjectType === "user_persona") {
      return (
        personaOptionById.get(subjectId) ?? {
          value: subjectId,
          label: "User persona",
          subtitle: subjectId,
        }
      )
    }
    if (subjectType === "group") {
      return (
        groupOptionById.get(subjectId) ?? {
          value: subjectId,
          label: "Legacy user group",
          subtitle: subjectId,
        }
      )
    }
    return {
      value: subjectId,
      label: "User account",
      subtitle: subjectId,
    }
  }

  const onCreatePersonaGroup = async () => {
    if (!newPersonaGroupName.trim() || !newPersonaGroupOwnerId) return
    const group = await createPersonaGroup.mutateAsync({
      name: newPersonaGroupName.trim(),
      owner_user_persona_id: newPersonaGroupOwnerId,
      group_type: "workspace",
      is_active: true,
    })
    setNewPersonaGroupName("")
    setSelectedPersonaGroupId(group.id)
  }

  const onAddPersonaGroupMember = async () => {
    if (!selectedPersonaGroupId || !personaGroupMemberId.trim()) return
    await addPersonaGroupMember.mutateAsync({
      user_persona_id: personaGroupMemberId.trim(),
      is_active: true,
      role: "member",
    })
    setPersonaGroupMemberId("")
  }

  return (
    <div className="container mx-auto max-w-7xl py-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{project.name}</h1>
        <p className="text-sm text-muted-foreground">
          {canManageProject
            ? "Workspace layout, access controls, and resource associations."
            : "Read-only project workspace and resource associations."}
        </p>
      </div>

      <Tabs defaultValue="workspace" className="space-y-4">
        <TabsList>
          <TabsTrigger value="workspace">Workspace</TabsTrigger>
          <TabsTrigger value="resources">Resources</TabsTrigger>
          {canManageProject ? (
            <>
              <TabsTrigger value="access">Access</TabsTrigger>
              <TabsTrigger value="settings">Settings</TabsTrigger>
            </>
          ) : null}
        </TabsList>

        <TabsContent value="workspace" className="space-y-4">
          {isPageLoading ? (
            <Skeleton className="h-[68vh] rounded-xl" />
          ) : !pageExists && !canEditProjectLayout ? (
            <Card>
              <CardHeader>
                <CardTitle>Workspace not initialized</CardTitle>
                <CardDescription>
                  A project owner can initialize and customize the workspace layout.
                </CardDescription>
              </CardHeader>
            </Card>
          ) : (
            <div className="h-[68vh] rounded-xl border overflow-hidden">
              <PageShell
                entityType="project"
                entityId={projectId}
                isOwner={canEditProjectLayout}
                ownerCanEdit={canEditProjectLayout}
                entityNameOverride={project.name}
              />
            </div>
          )}
        </TabsContent>

        <TabsContent value="resources">
          <Card>
            <CardHeader>
              <CardTitle>Resource Associations</CardTitle>
              <CardDescription>
                {canManageProject
                  ? "Attach stories, demos, rooms, or repos to this project."
                  : "Resources currently associated with this project."}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {canManageProject ? (
                <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                  <div className="space-y-1.5 md:col-span-2">
                    <Label>Quick pick</Label>
                    <Select value={attachSelection} onValueChange={setAttachSelection}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select a resource from the filtered set" />
                      </SelectTrigger>
                      <SelectContent>
                        {filteredAttachableOptions.map((option) => (
                          <SelectItem
                            key={`${option.resourceType}:${option.resourceId}`}
                            value={`${option.resourceType}:${option.resourceId}`}
                          >
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1.5">
                    <Label>Type</Label>
                    <Select
                      value={selectedAttachOption?.resourceType ?? resourceType}
                      onValueChange={(value: AttachableResourceType) => {
                        setResourceType(value)
                        setAttachSelection("")
                        setResourceId("")
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {Object.entries(resourceTypeLabels).map(([value, label]) => (
                          <SelectItem key={value} value={value}>
                            {label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1.5">
                    <Label>Visibility</Label>
                    <Select
                      value={resourceScope}
                      onValueChange={(value: "owned" | "available") => {
                        setResourceScope(value)
                        setAttachSelection("")
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="owned">Owned</SelectItem>
                        <SelectItem value="available">Available</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1.5 md:col-span-2">
                    <Label>Resource ID</Label>
                    <Input
                      value={selectedAttachOption?.resourceId ?? resourceId}
                      onChange={(event) => setResourceId(event.target.value)}
                      placeholder="UUID"
                    />
                  </div>
                  <div className="flex items-end">
                    <Button onClick={onAttachResource} disabled={addResource.isPending}>
                      Attach Resource
                    </Button>
                  </div>
                </div>
              ) : null}

              {canManageProject && filteredAttachableOptions.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No {resourceTypeLabels[resourceType].toLowerCase()} resources in the current filter.
                </p>
              ) : null}

              {isResourcesLoading ? (
                <Skeleton className="h-20 rounded-xl" />
              ) : (
                <div className="space-y-2">
                  {(resources ?? []).length === 0 ? (
                    <p className="text-sm text-muted-foreground">No resources attached yet.</p>
                  ) : (
                    (resources ?? []).map((item) => (
                      <div
                        key={item.id}
                        className="flex items-center justify-between rounded-lg border p-3"
                      >
                        <div className="text-sm">
                          <div className="font-medium">{item.resource_type}</div>
                          <div className="text-muted-foreground">{item.resource_id}</div>
                        </div>
                        {canManageProject ? (
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={removeResource.isPending}
                            onClick={() =>
                              removeResource.mutate({
                                resource_type: item.resource_type,
                                resource_id: item.resource_id,
                              })
                            }
                          >
                            <Unplug className="mr-2 h-4 w-4" />
                            Detach
                          </Button>
                        ) : null}
                      </div>
                    ))
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {canManageProject ? (
          <TabsContent value="access" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Project Access</CardTitle>
                <CardDescription>
                  Persona groups are the preferred workspace path. Direct persona, user,
                  and legacy group grants remain available during coexistence.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
                  <div className="space-y-1.5">
                    <Label>Subject type</Label>
                    <Select
                      value={grantSubjectType}
                      onValueChange={(
                        value: "user" | "group" | "user_persona" | "persona_group",
                      ) => {
                        setGrantSubjectType(value)
                        setGrantSubjectId("")
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="persona_group">persona_group</SelectItem>
                        <SelectItem value="user_persona">user_persona</SelectItem>
                        <SelectItem value="group">group</SelectItem>
                        <SelectItem value="user">user</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1.5">
                    <Label>Role</Label>
                    <Select
                      value={grantRole}
                      onValueChange={(value: "viewer" | "editor") => setGrantRole(value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="viewer">viewer</SelectItem>
                        <SelectItem value="editor">editor</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1.5 md:col-span-2">
                    <Label>{grantSubjectDescriptor}</Label>
                    {grantSubjectType === "group" ? (
                      <EntityCombobox
                        value={grantSubjectId}
                        onChange={setGrantSubjectId}
                        options={groupOptions}
                        placeholder="Choose one of your groups"
                        searchPlaceholder="Search groups..."
                        emptyMessage="No groups available."
                      />
                    ) : grantSubjectType === "persona_group" ? (
                      <EntityCombobox
                        value={grantSubjectId}
                        onChange={setGrantSubjectId}
                        options={personaGroupOptions}
                        placeholder="Choose one of your persona groups"
                        searchPlaceholder="Search persona groups..."
                        emptyMessage="No persona groups available."
                      />
                    ) : grantSubjectType === "user_persona" ? (
                      <div className="space-y-2">
                        <EntityCombobox
                          value={personaOptionById.has(grantSubjectId) ? grantSubjectId : ""}
                          onChange={setGrantSubjectId}
                          options={ownedPersonaOptions}
                          placeholder="Quick pick one of your personas"
                          searchPlaceholder="Search your personas..."
                          emptyMessage="No personas available."
                        />
                        <DiscoverUserPersonaCombobox
                          value={personaOptionById.has(grantSubjectId) ? "" : grantSubjectId}
                          onChange={setGrantSubjectId}
                          placeholder="Search published collaborator personas"
                        />
                        <Input
                          value={grantSubjectId}
                          onChange={(event) => setGrantSubjectId(event.target.value)}
                          placeholder="Or paste a collaborator UserPersona UUID"
                        />
                        <p className="text-xs text-muted-foreground">
                          Use quick pick for one of your personas, or paste another
                          collaborator persona ID when sharing across users.
                        </p>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        <Input
                          value={grantSubjectId}
                          onChange={(event) => setGrantSubjectId(event.target.value)}
                          placeholder="User UUID"
                        />
                        <p className="text-xs text-muted-foreground">
                          Direct user grants remain available, but persona-mediated grants
                          are preferred for workspace collaboration.
                        </p>
                      </div>
                    )}
                  </div>
                </div>
                <Button onClick={onGrantAccess} disabled={upsertGrant.isPending || !grantSubjectId}>
                  <Users2 className="mr-2 h-4 w-4" />
                  Grant Access
                </Button>

                {isGrantsLoading ? (
                  <Skeleton className="h-20 rounded-xl" />
                ) : (
                  <div className="space-y-2">
                    {(grants ?? []).length === 0 ? (
                      <p className="text-sm text-muted-foreground">No explicit grants yet.</p>
                    ) : (
                      (grants ?? []).map((grant) => (
                        (() => {
                          const subject = describeGrantSubject(
                            grant.subject_type,
                            grant.subject_id,
                          )
                          return (
                        <div
                          key={grant.id}
                          className="flex items-center justify-between rounded-lg border p-3"
                        >
                          <div className="text-sm">
                            <div className="font-medium">{subject.label}</div>
                            <div className="text-muted-foreground">
                              {grant.subject_type}
                              {subject.subtitle ? ` · ${subject.subtitle}` : ""}
                            </div>
                            <div className="text-muted-foreground">role: {grant.role}</div>
                          </div>
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={revokeGrant.isPending}
                            onClick={() =>
                              revokeGrant.mutate({
                                subject_type: grant.subject_type,
                                subject_id: grant.subject_id,
                              })
                            }
                          >
                            Revoke
                          </Button>
                        </div>
                          )
                        })()
                      ))
                    )}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Persona Collaboration Groups</CardTitle>
                <CardDescription>
                  Create persona-owned groups for workspace and project access.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                  <div className="space-y-1.5">
                    <Label>Group name</Label>
                    <Input
                      value={newPersonaGroupName}
                      onChange={(event) => setNewPersonaGroupName(event.target.value)}
                      placeholder="Design collaborators"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label>Owner persona</Label>
                    <EntityCombobox
                      value={newPersonaGroupOwnerId}
                      onChange={setNewPersonaGroupOwnerId}
                      options={ownedPersonaOptions}
                      placeholder="Select one of your personas"
                      searchPlaceholder="Search your personas..."
                      emptyMessage="No personas available."
                    />
                  </div>
                  <div className="flex items-end">
                    <Button
                      onClick={onCreatePersonaGroup}
                      disabled={
                        createPersonaGroup.isPending ||
                        !newPersonaGroupName.trim() ||
                        !newPersonaGroupOwnerId
                      }
                    >
                      Create Persona Group
                    </Button>
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                  <div className="space-y-1.5">
                    <Label>Manage group</Label>
                    <EntityCombobox
                      value={selectedPersonaGroupId}
                      onChange={setSelectedPersonaGroupId}
                      options={personaGroupOptions}
                      placeholder="Select persona group"
                      searchPlaceholder="Search persona groups..."
                      emptyMessage="No persona groups available."
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label>Add persona member</Label>
                    <div className="space-y-2">
                      <EntityCombobox
                        value={personaOptionById.has(personaGroupMemberId) ? personaGroupMemberId : ""}
                        onChange={setPersonaGroupMemberId}
                        options={ownedPersonaOptions}
                        placeholder="Quick pick one of your personas"
                        searchPlaceholder="Search your personas..."
                        emptyMessage="No personas available."
                        disabled={!selectedPersonaGroupId}
                      />
                      <DiscoverUserPersonaCombobox
                        value={
                          personaOptionById.has(personaGroupMemberId)
                            ? ""
                            : personaGroupMemberId
                        }
                        onChange={setPersonaGroupMemberId}
                        placeholder="Search published collaborator personas"
                        disabled={!selectedPersonaGroupId}
                      />
                      <Input
                        value={personaGroupMemberId}
                        onChange={(event) => setPersonaGroupMemberId(event.target.value)}
                        placeholder="Or paste another user's UserPersona UUID"
                        disabled={!selectedPersonaGroupId}
                      />
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Workspace groups can include your personas and collaborator personas.
                    </p>
                  </div>
                  <div className="flex items-end">
                    <Button
                      variant="outline"
                      onClick={onAddPersonaGroupMember}
                      disabled={
                        addPersonaGroupMember.isPending ||
                        !selectedPersonaGroupId ||
                        !personaGroupMemberId.trim()
                      }
                    >
                      Add Persona
                    </Button>
                  </div>
                </div>

                {selectedPersonaGroupId ? (
                  <div className="space-y-2 rounded-lg border p-3">
                    <div>
                      <div className="text-sm font-medium">
                        {selectedPersonaGroupOption?.label ?? "Group members"}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {selectedPersonaGroupOption?.subtitle ??
                          "Persona-mediated collaboration members"}
                      </div>
                    </div>
                    {(personaGroupMembers ?? []).length === 0 ? (
                      <p className="text-sm text-muted-foreground">
                        No persona members yet.
                      </p>
                    ) : (
                      (personaGroupMembers ?? []).map((member) => (
                        (() => {
                          const persona = personaOptionById.get(member.user_persona_id)
                          return (
                        <div
                          key={member.id}
                          className="flex items-center justify-between rounded border p-2 text-sm"
                        >
                          <div>
                            <div className="font-medium">
                              {persona?.label ?? "User persona"}
                            </div>
                            <div className="text-muted-foreground">
                              {persona?.subtitle ?? member.user_persona_id}
                            </div>
                            <div className="text-muted-foreground">
                              role: {member.role ?? "member"}
                            </div>
                          </div>
                        </div>
                          )
                        })()
                      ))
                    )}
                  </div>
                ) : null}
              </CardContent>
            </Card>
          </TabsContent>
        ) : null}

        {canManageProject ? (
          <TabsContent value="settings">
            <Card>
              <CardHeader>
                <CardTitle>Project Settings</CardTitle>
                <CardDescription>
                  Update name/description or delete the project.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                  <div className="space-y-1.5">
                    <Label>Name</Label>
                    <Input
                      value={nameDraft}
                      onChange={(event) => setNameDraft(event.target.value)}
                      placeholder={project.name}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label>Description</Label>
                    <Textarea
                      value={descriptionDraft}
                      onChange={(event) => setDescriptionDraft(event.target.value)}
                      placeholder={project.description ?? "No description"}
                    />
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button onClick={onSaveProject} disabled={updateProject.isPending}>
                    Save
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={onDeleteProject}
                    disabled={deleteProject.isPending}
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete Project
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        ) : null}
      </Tabs>

      {(addResource.isPending ||
        removeResource.isPending ||
        upsertGrant.isPending ||
        revokeGrant.isPending ||
        updateProject.isPending ||
        deleteProject.isPending) ? (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          Saving changes...
        </div>
      ) : null}
    </div>
  )
}
