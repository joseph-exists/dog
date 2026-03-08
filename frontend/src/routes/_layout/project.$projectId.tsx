import { useEffect, useMemo, useRef, useState } from "react"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { Loader2, Trash2, Unplug, Users2 } from "lucide-react"
import { PageShell } from "@/components/Page"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
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
  useAttachableResources,
  useDeleteProject,
  useMyGroups,
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
  const { data: attachable } = useAttachableResources(canManageProject)

  const updateProject = useUpdateProject(projectId)
  const deleteProject = useDeleteProject()
  const addResource = useAddProjectResource(projectId)
  const removeResource = useRemoveProjectResource(projectId)
  const upsertGrant = useUpsertProjectGrant(projectId)
  const revokeGrant = useRevokeProjectGrant(projectId)

  const [nameDraft, setNameDraft] = useState("")
  const [descriptionDraft, setDescriptionDraft] = useState("")
  const [resourceType, setResourceType] = useState<AttachableResourceType>("story")
  const [resourceScope, setResourceScope] = useState<"owned" | "available">("owned")
  const [resourceId, setResourceId] = useState("")
  const [attachSelection, setAttachSelection] = useState("")
  const [grantSubjectType, setGrantSubjectType] = useState<"user" | "group">("group")
  const [grantRole, setGrantRole] = useState<"viewer" | "editor">("viewer")
  const [grantSubjectId, setGrantSubjectId] = useState("")

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
    if (grantSubjectType === "user") {
      setGrantSubjectId("")
    }
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
                  Grant viewer/editor access to users or groups for this project.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
                  <div className="space-y-1.5">
                    <Label>Subject type</Label>
                    <Select
                      value={grantSubjectType}
                      onValueChange={(value: "user" | "group") => setGrantSubjectType(value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
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
                    <Label>Subject ID</Label>
                    {grantSubjectType === "group" ? (
                      <Select value={grantSubjectId} onValueChange={setGrantSubjectId}>
                        <SelectTrigger>
                          <SelectValue placeholder="Choose one of your groups" />
                        </SelectTrigger>
                        <SelectContent>
                          {(groups ?? []).map((group) => (
                            <SelectItem key={group.id} value={group.id}>
                              {group.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    ) : (
                      <Input
                        value={grantSubjectId}
                        onChange={(event) => setGrantSubjectId(event.target.value)}
                        placeholder="User UUID"
                      />
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
                        <div
                          key={grant.id}
                          className="flex items-center justify-between rounded-lg border p-3"
                        >
                          <div className="text-sm">
                            <div className="font-medium">
                              {grant.subject_type}:{grant.subject_id}
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
                      ))
                    )}
                  </div>
                )}
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
