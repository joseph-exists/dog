import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { ArrowLeft, LayoutPanelLeft, Plus, User } from "lucide-react"
import { useEffect, useMemo, useState } from "react"

import {
  AccessService,
  GroupsService,
  PersonaGroupsService,
  type AccessGrantPublic,
  type AccessGrantRole,
  type AccessGrantSubjectType,
} from "@/client"
import { CreatePageDialog } from "@/components/Page/Dialogs/CreatePageDialog"
import { BlockEditorSheet } from "@/components/Page/editor/BlockEditorSheet"
import { BlockPalette } from "@/components/Page/editor/BlockPalette"
import type { TemplateBlock } from "@/components/Page/registry"
import { getPageTemplate } from "@/components/Page/registry"
import { DiscoverUserPersonaCombobox } from "@/components/UserPage/DiscoverUserPersonaCombobox"
import {
  UserPageBuilderNavigator,
  UserPageAudiencePreviewPanel,
  UserPageBuilderPreview,
  UserPageBuilderSaveBar,
  UserPageBuilderSurfaceEditor,
  UserPageBuilderValidationPanel,
} from "@/components/UserPage/builder"
import {
  addUserPageBuilderDraftBlock,
  deleteUserPageBuilderDraftBlock,
  type UserPageBuilderDraft,
  hydrateUserPageBuilderDraft,
  moveUserPageBuilderDraftBlock,
  resetUserPageBuilderDraftBlock,
  serializeUserPageBuilderDraft,
  toggleUserPageBuilderDraftBlockVisibility,
  updateUserPageBuilderDraftBlockContent,
} from "@/components/UserPage/builder/userPageBuilderAdapter"
import {
  validateUserPageBuilderDraft,
  type UserPageBuilderSurface,
} from "@/components/UserPage/builder/userPageBuilderSchema"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { EntityCombobox, type EntityComboboxOption } from "@/components/ui/entity-combobox"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import useAuth from "@/hooks/useAuth"
import { buildUserPageViewModel } from "@/hooks/useUserPageViewModel"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import { PageService } from "@/services/pageService"
import { UserPersonaService } from "@/services/userPersonaService"

export const Route = createFileRoute("/_layout/u/$slug/compose")({
  component: UserPageComposerRoute,
  head: ({ params }) => ({
    meta: [{ title: `Compose ${params.slug}` }],
  }),
})

function instantiateTemplate(
  templateId: string,
  contentOverrides?: Record<string, Record<string, unknown>>,
): TemplateBlock[] {
  const template = getPageTemplate(templateId)
  if (!template) {
    throw new Error(`Template not found: ${templateId}`)
  }

  return template.defaultBlocks.map((block) => ({
    ...block,
    id: crypto.randomUUID(),
    visibility: block.visibility ?? "visible",
    content: {
      ...(block.content ?? {}),
      ...(contentOverrides?.[block.type] ?? {}),
    },
  }))
}

function UserPageComposerRoute() {
  const { slug } = Route.useParams()
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const userId = slug
  const isOwner = user?.id === userId
  const [paletteOpen, setPaletteOpen] = useState(true)
  const [selectedBlockId, setSelectedBlockId] = useState<string | null>(null)
  const [selectedSurface, setSelectedSurface] =
    useState<UserPageBuilderSurface>("overview")
  const [draft, setDraft] = useState<UserPageBuilderDraft | null>(null)
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [grantSubjectType, setGrantSubjectType] =
    useState<AccessGrantSubjectType>("persona_group")
  const [grantRole, setGrantRole] = useState<AccessGrantRole>("viewer")
  const [grantSubjectId, setGrantSubjectId] = useState("")

  const pageQuery = useQuery({
    queryKey: ["pages", "user", userId],
    queryFn: () => PageService.getLayout("user", userId),
    enabled: isOwner,
  })

  const authoringBundleQuery = useQuery({
    queryKey: ["user-persona-authoring-bundle", userId],
    queryFn: () => UserPersonaService.getUserPageAuthoringBundle(),
    enabled: isOwner,
  })

  const legacyGroupsQuery = useQuery({
    queryKey: ["groups", "mine"],
    queryFn: async () => (await GroupsService.listUserGroups()).data,
    enabled: isOwner,
  })

  const personaGroupsQuery = useQuery({
    queryKey: ["persona-groups", "mine"],
    queryFn: async () => (await PersonaGroupsService.listPersonaGroups({ skip: 0, limit: 100 })).data,
    enabled: isOwner,
  })

  const pageAccessQuery = useQuery({
    queryKey: ["access", "page", pageQuery.data?.id],
    queryFn: async () =>
      pageQuery.data
        ? (await AccessService.listResourceAccessGrants({
            resourceType: "page",
            resourceId: pageQuery.data.id,
          })).data
        : [],
    enabled: isOwner && Boolean(pageQuery.data?.id),
  })

  useEffect(() => {
    if (!pageQuery.data?.layout) return
    setDraft(
      hydrateUserPageBuilderDraft({
        userId,
        slug,
        blocks: pageQuery.data.layout,
      }),
    )
  }, [pageQuery.data?.layout, userId, slug])

  const saveMutation = useMutation({
    mutationFn: async (layout: TemplateBlock[]) =>
      PageService.saveLayout({
        entityType: "user",
        entityId: userId,
        layout: UserPersonaService.buildPublishedSnapshot(
          layout,
          authoringBundleQuery.data ?? {
            personas: [],
            presentations: [],
            userPersonas: [],
            personaPresentations: [],
          },
        ),
        layoutVersion: pageQuery.data?.layoutVersion,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["pages", "user", userId] })
      showSuccessToast("Saved user page composition")
    },
    onError: () => {
      showErrorToast("Failed to save user page composition")
    },
  })

  const upsertPageGrantMutation = useMutation({
    mutationFn: async () => {
      if (!pageQuery.data?.id) {
        throw new Error("Create and save the page before managing audience access.")
      }
      return AccessService.upsertResourceAccessGrant({
        resourceType: "page",
        resourceId: pageQuery.data.id,
        requestBody: {
          subject_type: grantSubjectType,
          subject_id: grantSubjectId.trim(),
          role: grantRole,
        },
      })
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["access", "page", pageQuery.data?.id],
      })
      showSuccessToast("Updated page audience access")
      if (grantSubjectType === "user" || grantSubjectType === "user_persona") {
        setGrantSubjectId("")
      }
    },
    onError: () => {
      showErrorToast("Failed to update page audience access")
    },
  })

  const revokePageGrantMutation = useMutation({
    mutationFn: async (grant: AccessGrantPublic) => {
      if (!pageQuery.data?.id) {
        throw new Error("Create and save the page before managing audience access.")
      }
      await AccessService.revokeResourceAccessGrant({
        resourceType: "page",
        resourceId: pageQuery.data.id,
        requestBody: {
          subject_type: grant.subject_type,
          subject_id: grant.subject_id,
        },
      })
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["access", "page", pageQuery.data?.id],
      })
      showSuccessToast("Removed page audience access")
    },
    onError: () => {
      showErrorToast("Failed to remove page audience access")
    },
  })

  const builderDraft = useMemo(() => {
    if (draft) return { ...draft, selectedSurface }
    return hydrateUserPageBuilderDraft({
      userId,
      slug,
      blocks: pageQuery.data?.layout ?? [],
      selectedSurface,
    })
  }, [draft, selectedSurface, userId, slug, pageQuery.data?.layout])

  const serializedBlocks = useMemo(
    () => serializeUserPageBuilderDraft(builderDraft),
    [builderDraft],
  )

  const viewModel = useMemo(
    () =>
      buildUserPageViewModel({
        slug,
        userId,
        isOwner: true,
        pageExists: Boolean(pageQuery.data),
        blocks: serializedBlocks,
        libraryPersonas: [],
        ownerPersonas: authoringBundleQuery.data?.personas ?? [],
        ownerPresentations: authoringBundleQuery.data?.presentations ?? [],
      }),
    [slug, userId, pageQuery.data, serializedBlocks, authoringBundleQuery.data],
  )

  const issues = useMemo(() => validateUserPageBuilderDraft(builderDraft), [builderDraft])

  const ownedPersonaOptions = useMemo<EntityComboboxOption[]>(
    () =>
      (authoringBundleQuery.data?.userPersonas ?? []).map((persona) => ({
        value: persona.id,
        label: persona.nickname?.trim() || `Persona ${persona.id.slice(0, 8)}`,
        subtitle: persona.description?.trim() || persona.persona_id,
        keywords: [persona.id, persona.persona_id, persona.nickname ?? ""],
      })),
    [authoringBundleQuery.data?.userPersonas],
  )

  const personaGroupOptions = useMemo<EntityComboboxOption[]>(
    () =>
      (personaGroupsQuery.data ?? []).map((group) => ({
        value: group.id,
        label: group.name,
        subtitle: group.group_type ?? "persona group",
        keywords: [group.id, group.name, group.owner_user_persona_id],
      })),
    [personaGroupsQuery.data],
  )

  const legacyGroupOptions = useMemo<EntityComboboxOption[]>(
    () =>
      (legacyGroupsQuery.data ?? []).map((group) => ({
        value: group.id,
        label: group.name,
        subtitle: group.id,
        keywords: [group.id, group.name],
      })),
    [legacyGroupsQuery.data],
  )

  const personaOptionById = useMemo(
    () => new Map(ownedPersonaOptions.map((option) => [option.value, option])),
    [ownedPersonaOptions],
  )
  const personaGroupOptionById = useMemo(
    () => new Map(personaGroupOptions.map((option) => [option.value, option])),
    [personaGroupOptions],
  )
  const legacyGroupOptionById = useMemo(
    () => new Map(legacyGroupOptions.map((option) => [option.value, option])),
    [legacyGroupOptions],
  )

  const isDirty = useMemo(() => {
    return (
      JSON.stringify(serializedBlocks) !==
      JSON.stringify(pageQuery.data?.layout ?? [])
    )
  }, [serializedBlocks, pageQuery.data?.layout])

  const selectedBlock = useMemo(
    () => serializedBlocks.find((block) => block.id === selectedBlockId) ?? null,
    [serializedBlocks, selectedBlockId],
  )

  const describeGrantSubject = (
    subjectType: AccessGrantSubjectType,
    subjectId: string,
  ) => {
    if (subjectType === "user_persona") {
      return (
        personaOptionById.get(subjectId) ?? {
          value: subjectId,
          label: "User persona",
          subtitle: subjectId,
        }
      )
    }
    if (subjectType === "persona_group") {
      return (
        personaGroupOptionById.get(subjectId) ?? {
          value: subjectId,
          label: "Persona group",
          subtitle: subjectId,
        }
      )
    }
    if (subjectType === "group") {
      return (
        legacyGroupOptionById.get(subjectId) ?? {
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

  const handleUpdateBlockContent = (
    blockId: string,
    content: Record<string, unknown>,
  ) => {
    setDraft((current) =>
      current
        ? updateUserPageBuilderDraftBlockContent(current, blockId, content)
        : current,
    )
  }

  const handleAddBlock = (type: TemplateBlock["type"]) => {
    setDraft((current) => {
      if (!current) return current
      return addUserPageBuilderDraftBlock(current, { type, column: "primary" })
    })
  }

  const handleMoveBlock = (blockId: string, direction: "up" | "down") => {
    setDraft((current) => {
      if (!current) return current
      return moveUserPageBuilderDraftBlock(current, blockId, direction)
    })
  }

  const handleToggleVisibility = (blockId: string) => {
    setDraft((current) =>
      current
        ? toggleUserPageBuilderDraftBlockVisibility(current, blockId)
        : current,
    )
  }

  const handleDeleteBlock = (blockId: string) => {
    setDraft((current) =>
      current ? deleteUserPageBuilderDraftBlock(current, blockId) : current,
    )
    if (selectedBlockId === blockId) {
      setSelectedBlockId(null)
    }
  }

  const handleResetBlock = (blockId: string) => {
    setDraft((current) =>
      current ? resetUserPageBuilderDraftBlock(current, blockId) : current,
    )
  }

  const handleCreatePage = async (templateId: string) => {
    const layout = instantiateTemplate(templateId, {
      identity: {
        name: user?.full_name || user?.email || slug,
        tagline: "A work-centered user surface shaped through personas.",
      },
      bio: {
        text:
          "This page organizes work, personas, audience views, and relations without collapsing them into a single static identity.",
      },
    })
    const nextDraft = hydrateUserPageBuilderDraft({
      userId,
      slug,
      blocks: layout,
      selectedSurface,
    })
    setDraft(nextDraft)
    await saveMutation.mutateAsync(serializeUserPageBuilderDraft(nextDraft))
    setShowCreateDialog(false)
  }

  if (pageQuery.isLoading || authoringBundleQuery.isLoading) {
    return (
      <div className="flex h-full flex-col p-6 space-y-4">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-80 w-full" />
      </div>
    )
  }

  if (!isOwner) {
    return (
      <div className="flex h-full items-center justify-center p-6">
        <div className="max-w-md text-center space-y-4">
          <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-muted">
            <User className="h-10 w-10 text-muted-foreground" />
          </div>
          <h1 className="text-2xl font-bold">Composer Unavailable</h1>
          <p className="text-muted-foreground">
            Only the owner can compose this user page.
          </p>
          <Button asChild variant="outline">
            <Link to="/u/$slug" params={{ slug }}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back To Page
            </Link>
          </Button>
        </div>
      </div>
    )
  }

  if (!pageQuery.data && serializedBlocks.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-6">
        <div className="max-w-md text-center space-y-4">
          <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-muted">
            <LayoutPanelLeft className="h-10 w-10 text-muted-foreground" />
          </div>
          <h1 className="text-2xl font-bold">Create Your User Page</h1>
          <p className="text-muted-foreground">
            Start with the user template, then open the dedicated compositor to
            shape work, personas, audience views, and relations.
          </p>
          <Button onClick={() => setShowCreateDialog(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Create Page
          </Button>
          <CreatePageDialog
            open={showCreateDialog}
            onOpenChange={setShowCreateDialog}
            onCreatePage={handleCreatePage}
            isCreating={saveMutation.isPending}
            entityType="user"
          />
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-full">
      <BlockPalette
        onAddBlock={(type) => handleAddBlock(type)}
        targetColumn="primary"
        openClassName="w-60"
        isOpen={paletteOpen}
        onToggle={() => setPaletteOpen((current) => !current)}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <div className="border-b px-6 py-4">
          <div className="flex items-center justify-between gap-4">
            <div>
              <div className="text-sm uppercase tracking-wide text-muted-foreground">
                User Page Composer
              </div>
              <h1 className="text-2xl font-semibold">
                {user?.full_name || user?.email || slug}
              </h1>
              <p className="text-sm text-muted-foreground">
                Authoring workspace for layout, work, personas, audiences, and
                relations.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button asChild variant="outline">
                <Link to="/u/$slug" params={{ slug }}>
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Runtime Page
                </Link>
              </Button>
            </div>
          </div>
        </div>

        <div className="flex min-h-0 flex-1 flex-col p-4">
          <div className="mb-4">
            <Card>
              <CardHeader>
                <CardTitle>Audience Access</CardTitle>
                <CardDescription>
                  `trusted` audience views resolve from direct user or persona grants.
                  `collaborators` resolve from legacy groups and persona groups.
                  `custom` views can target a specific id through an audience key.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {!pageQuery.data ? (
                  <p className="text-sm text-muted-foreground">
                    Save the page once before configuring visitor audience access.
                  </p>
                ) : (
                  <>
                    <div className="grid gap-3 md:grid-cols-4">
                      <div className="space-y-1.5">
                        <Label>Subject type</Label>
                        <Select
                          value={grantSubjectType}
                          onValueChange={(value: AccessGrantSubjectType) => {
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
                          onValueChange={(value: AccessGrantRole) => setGrantRole(value)}
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
                        <Label>Audience target</Label>
                        {grantSubjectType === "persona_group" ? (
                          <EntityCombobox
                            value={grantSubjectId}
                            onChange={setGrantSubjectId}
                            options={personaGroupOptions}
                            placeholder="Choose one of your persona groups"
                            searchPlaceholder="Search persona groups..."
                            emptyMessage="No persona groups available."
                          />
                        ) : grantSubjectType === "group" ? (
                          <EntityCombobox
                            value={grantSubjectId}
                            onChange={setGrantSubjectId}
                            options={legacyGroupOptions}
                            placeholder="Choose one of your groups"
                            searchPlaceholder="Search groups..."
                            emptyMessage="No groups available."
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
                              placeholder="Search published visitor personas"
                            />
                            <Input
                              value={grantSubjectId}
                              onChange={(event) => setGrantSubjectId(event.target.value)}
                              placeholder="Or paste another visitor UserPersona UUID"
                            />
                          </div>
                        ) : (
                          <Input
                            value={grantSubjectId}
                            onChange={(event) => setGrantSubjectId(event.target.value)}
                            placeholder="User UUID"
                          />
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <Button
                        onClick={() => upsertPageGrantMutation.mutate()}
                        disabled={
                          upsertPageGrantMutation.isPending ||
                          grantSubjectId.trim().length === 0
                        }
                      >
                        Add Audience Grant
                      </Button>
                      <p className="text-xs text-muted-foreground">
                        Use the same ids in `custom` audience views when you need a
                        presentation to target one specific subject.
                      </p>
                    </div>

                    <div className="space-y-2">
                      {(pageAccessQuery.data ?? []).length === 0 ? (
                        <p className="text-sm text-muted-foreground">
                          No explicit page audience grants yet. Visitors without a
                          matching grant will resolve to `public`.
                        </p>
                      ) : (
                        (pageAccessQuery.data ?? []).map((grant) => {
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
                                <div className="text-muted-foreground">
                                  role: {grant.role}
                                </div>
                              </div>
                              <Button
                                variant="outline"
                                size="sm"
                                disabled={revokePageGrantMutation.isPending}
                                onClick={() => revokePageGrantMutation.mutate(grant)}
                              >
                                Remove
                              </Button>
                            </div>
                          )
                        })
                      )}
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </div>

          <div className="mb-4">
            <UserPageAudiencePreviewPanel
              userId={userId}
              slug={slug}
              blocks={serializedBlocks}
              authoringBundle={
                authoringBundleQuery.data ?? {
                  personas: [],
                  presentations: [],
                  userPersonas: [],
                  personaPresentations: [],
                }
              }
              pageGrants={pageAccessQuery.data ?? []}
            />
          </div>

          <ResizablePanelGroup direction="horizontal" className="min-h-0 flex-1">
            <ResizablePanel defaultSize={24} minSize={20}>
              <div className="h-full overflow-auto pr-2 space-y-4">
                <UserPageBuilderNavigator
                  blocks={serializedBlocks}
                  selectedSurface={selectedSurface}
                  issues={issues}
                  onSurfaceSelect={setSelectedSurface}
                  onEditBlock={setSelectedBlockId}
                />
                <UserPageBuilderValidationPanel issues={issues} />
              </div>
            </ResizablePanel>
            <ResizableHandle withHandle />
            <ResizablePanel defaultSize={30} minSize={24}>
              <div className="h-full overflow-auto px-2">
              <UserPageBuilderSurfaceEditor
                selectedSurface={selectedSurface}
                blocks={serializedBlocks}
                viewModel={viewModel}
                selectedBlockId={selectedBlockId}
                onSelectBlock={setSelectedBlockId}
                onMoveBlock={handleMoveBlock}
                onToggleVisibility={handleToggleVisibility}
                onResetBlock={handleResetBlock}
                onDeleteBlock={handleDeleteBlock}
              />
              </div>
            </ResizablePanel>
            <ResizableHandle withHandle />
            <ResizablePanel defaultSize={46} minSize={32}>
              <div className="h-full overflow-hidden pl-2">
                <UserPageBuilderPreview
                  blocks={serializedBlocks}
                  entityId={userId}
                  viewModel={viewModel}
                />
              </div>
            </ResizablePanel>
          </ResizablePanelGroup>
        </div>

        <div className="px-4 pb-4">
          <UserPageBuilderSaveBar
            label={`/${slug}/compose`}
            isDirty={isDirty}
            isSaving={saveMutation.isPending}
            canSave={issues.every((issue) => issue.severity !== "error")}
            statusNote="Persona and audience-view edits save immediately. Use this action to publish the page layout and visitor snapshot."
            onSave={() => saveMutation.mutate(serializedBlocks)}
          />
        </div>
      </div>

      <BlockEditorSheet
        block={selectedBlock}
        entityType="user"
        entityId={userId}
        onSave={handleUpdateBlockContent}
        onClose={() => setSelectedBlockId(null)}
      />
    </div>
  )
}
