import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { ArrowLeft, LayoutPanelLeft, Plus, User } from "lucide-react"
import { useEffect, useMemo, useState } from "react"

import { CreatePageDialog } from "@/components/Page/Dialogs/CreatePageDialog"
import { BlockEditorSheet } from "@/components/Page/editor/BlockEditorSheet"
import { BlockPalette } from "@/components/Page/editor/BlockPalette"
import type { TemplateBlock } from "@/components/Page/registry"
import { getPageTemplate } from "@/components/Page/registry"
import {
  UserPageBuilderNavigator,
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
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable"
import { Skeleton } from "@/components/ui/skeleton"
import useAuth from "@/hooks/useAuth"
import { buildUserPageViewModel } from "@/hooks/useUserPageViewModel"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import { PageService } from "@/services/pageService"
import { PersonaLibraryService } from "@/services/personaLibraryService"

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

  const pageQuery = useQuery({
    queryKey: ["pages", "user", userId],
    queryFn: () => PageService.getLayout("user", userId),
    enabled: isOwner,
  })

  const personaLibraryQuery = useQuery({
    queryKey: ["persona-library", "user", userId],
    queryFn: () =>
      PersonaLibraryService.getLibrary({ type: "user", id: userId, name: "" }),
    enabled: isOwner,
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
        layout,
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
        libraryPersonas: personaLibraryQuery.data ?? [],
      }),
    [slug, userId, pageQuery.data, serializedBlocks, personaLibraryQuery.data],
  )

  const issues = useMemo(() => validateUserPageBuilderDraft(builderDraft), [builderDraft])

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

  if (pageQuery.isLoading || personaLibraryQuery.isLoading) {
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

        <div className="min-h-0 flex-1 p-4">
          <ResizablePanelGroup direction="horizontal" className="h-full">
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
