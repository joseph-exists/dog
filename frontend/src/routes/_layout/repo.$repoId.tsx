import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import {
  AlertCircleIcon,
  ArrowLeftIcon,
  ExternalLinkIcon,
  GitBranchIcon,
  LockIcon,
  MoreVerticalIcon,
  PanelsTopLeftIcon,
  RefreshCwIcon,
  SaveIcon,
  Trash2Icon,
  UnlockIcon,
} from "lucide-react"
import { useEffect, useMemo, useState } from "react"
import type { ApiError } from "@/client/core/ApiError"
import {
  buildRepoUserLayoutPresetId,
  createUserRepoLayoutPreset,
  getSystemRepoLayoutPresets,
  getUserRepoQueryOptions,
  RepoLayout,
  type RepoLayoutPreset,
  type RepoPanelConfig,
  RepoPanelLayoutDialog,
  renderRepoPanel,
  repoQueryKeys,
  SaveRepoLayoutPresetDialog,
} from "@/components/Repo"
import { RepoLayoutEditorDialog } from "@/components/Repo/Dialogs/RepoLayoutEditorDialog"
import { RepoStatusBadge } from "@/components/Repo/Display/RepoStatusBadge"
import {
  readRepoLayoutWorkspaceState,
  readUserRepoLayoutPresets,
  resolveRepoLayoutPreset,
  writeRepoLayoutWorkspaceState,
  writeUserRepoLayoutPresets,
} from "@/components/Repo/panels/repoLayoutPresets"
import {
  applyRepoPanelLayoutItems,
  type RepoPanelLayoutItem,
  repoPanelLayoutItemsEqual,
} from "@/components/Repo/panels/repoPanelLayoutCustomization"
import { formatRepoDate } from "@/components/Repo/utils"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import useAuth from "@/hooks/useAuth"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import { UserRepoAppService } from "@/services/userRepoService"
import { handleError } from "@/utils"

export const Route = createFileRoute("/_layout/repo/$repoId")({
  component: RepoDetailPage,
  head: () => ({
    meta: [{ title: "Repository Details" }],
  }),
})

function RepoDetailSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-6 w-48" />
      <div className="space-y-3">
        <Skeleton className="h-9 w-64" />
        <Skeleton className="h-4 w-80" />
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Skeleton className="h-32 rounded-xl" />
        <Skeleton className="h-32 rounded-xl" />
        <Skeleton className="h-32 rounded-xl" />
        <Skeleton className="h-32 rounded-xl" />
      </div>
      <Skeleton className="h-64 rounded-xl" />
    </div>
  )
}

function RepoDetailPage() {
  const { repoId } = Route.useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const [layoutMode, setLayoutMode] = useState<"panels" | "tabs">("panels")
  const [isQuickLayoutDialogOpen, setIsQuickLayoutDialogOpen] = useState(false)
  const [isLayoutEditorOpen, setIsLayoutEditorOpen] = useState(false)
  const [isSavePresetOpen, setIsSavePresetOpen] = useState(false)
  const [panelSelections, setPanelSelections] = useState<
    Record<string, string | null>
  >({})
  const systemPresets = useMemo(() => getSystemRepoLayoutPresets(), [])
  const [userPresets, setUserPresets] = useState<RepoLayoutPreset[]>([])
  const [activePresetId, setActivePresetId] = useState<string>(
    systemPresets[0]?.id ?? "system-default",
  )
  const [panelLayoutItems, setPanelLayoutItems] = useState<
    RepoPanelLayoutItem[]
  >(systemPresets[0]?.items ?? [])
  const {
    data: repo,
    isLoading,
    error,
    refetch,
    isFetching,
  } = useQuery(getUserRepoQueryOptions(repoId))
  const capabilities = useMemo(
    () => ({
      // Backend capability fields are returned in snake_case on UserRepoPublic.
      // This route keeps a small normalization layer so the existing repo panel
      // registry can continue using its established camelCase requirement names.
      hasRepoIdentity: true,
      hasFileTree: repo?.capabilities?.has_file_tree === true,
      hasBlobContent: repo?.capabilities?.has_blob_content === true,
      hasCommitHistory: repo?.capabilities?.has_commit_history === true,
      hasSearch: repo?.capabilities?.has_search === true,
      // Manage-access is still a frontend product concept rather than a backend
      // capability on UserRepoPublic; keep it conservative until repo sharing/edit
      // controls have their own explicit API contract.
      hasManageAccess: true,
    }),
    [repo],
  )
  const defaultBranch =
    repo?.default_branch ||
    repo?.capabilities?.default_branch ||
    repo?.source_branch ||
    "main"
  const isViewerReady =
    capabilities.hasFileTree === true && capabilities.hasBlobContent === true
  const layoutPresets = useMemo(
    () => [...systemPresets, ...userPresets],
    [systemPresets, userPresets],
  )
  const activePreset = useMemo(
    () => resolveRepoLayoutPreset(layoutPresets, activePresetId),
    [activePresetId, layoutPresets],
  )

  useEffect(() => {
    if (!repo || typeof window === "undefined") return
    const storedUserPresets = readUserRepoLayoutPresets(window.localStorage)
    const allPresets = [...systemPresets, ...storedUserPresets]
    const workspaceState = readRepoLayoutWorkspaceState(
      window.localStorage,
      repo.id,
    )
    const nextActivePreset = resolveRepoLayoutPreset(
      allPresets,
      workspaceState?.activePresetId ?? systemPresets[0]?.id,
    )

    setUserPresets(storedUserPresets)
    setActivePresetId(nextActivePreset.id)
    setPanelLayoutItems(
      workspaceState?.items && workspaceState.items.length > 0
        ? applyRepoPanelLayoutItems(
            nextActivePreset.items,
            workspaceState.items,
          )
        : nextActivePreset.items,
    )
  }, [repo, systemPresets])

  useEffect(() => {
    if (!repo || typeof window === "undefined") return
    writeRepoLayoutWorkspaceState(window.localStorage, repo.id, {
      activePresetId,
      items: panelLayoutItems,
    })
  }, [activePresetId, panelLayoutItems, repo])

  const panelContext = useMemo(
    () =>
      repo
        ? {
            repo,
            capabilities,
            panelSelections,
            setPanelSelection: (selectionKey: string, path: string | null) => {
              setPanelSelections((current) => ({
                ...current,
                [selectionKey]: path,
              }))
            },
          }
        : null,
    [capabilities, panelSelections, repo],
  )
  const effectivePanels = useMemo(
    () => applyRepoPanelLayoutItems(activePreset.items, panelLayoutItems),
    [activePreset.items, panelLayoutItems],
  )

  const panels = useMemo<RepoPanelConfig[]>(
    () =>
      panelContext
        ? effectivePanels.map((panel) => ({
            ...panel,
            title: panel.title ?? panel.kind,
            render: () => renderRepoPanel(panel, panelContext),
          }))
        : [],
    [effectivePanels, panelContext],
  )
  const hasCustomizedPanelLayout = useMemo(
    () => !repoPanelLayoutItemsEqual(panelLayoutItems, activePreset.items),
    [activePreset.items, panelLayoutItems],
  )
  const canDeleteActivePreset = activePreset.source === "user"
  const canManageRepo = Boolean(
    user && repo && (user.is_superuser || user.id === repo.owner_user_id),
  )
  const canCancelImport = repo?.import_status !== "ready"
  const cancelImportMutation = useMutation({
    mutationFn: async () => UserRepoAppService.cancelUserRepoImport(repoId),
    onSuccess: async () => {
      showSuccessToast(
        `Import canceled for ${repo?.display_name ?? "repository"}.`,
      )
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: repoQueryKeys.all }),
        queryClient.invalidateQueries({
          queryKey: repoQueryKeys.detail(repoId),
        }),
      ])
    },
    onError: (error: ApiError) => {
      handleError.call(showErrorToast, error)
    },
  })
  const deleteRepoMutation = useMutation({
    mutationFn: async () => UserRepoAppService.deleteUserRepo(repoId),
    onSuccess: async () => {
      showSuccessToast(`Deleted ${repo?.display_name ?? "repository"}.`)
      await queryClient.invalidateQueries({ queryKey: repoQueryKeys.all })
      navigate({ to: "/repos" })
    },
    onError: (error: ApiError) => {
      handleError.call(showErrorToast, error)
    },
  })

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null
      if (
        target &&
        (target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.isContentEditable)
      ) {
        return
      }

      const hasMod = event.metaKey || event.ctrlKey
      if (hasMod && event.shiftKey && event.key.toLowerCase() === "l") {
        event.preventDefault()
        setIsQuickLayoutDialogOpen(true)
        return
      }

      if (hasMod && event.altKey && event.key.toLowerCase() === "l") {
        event.preventDefault()
        setIsLayoutEditorOpen(true)
      }
    }

    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [])

  const handleApplyPanelLayout = (items: RepoPanelLayoutItem[]) => {
    setPanelLayoutItems(items)
    showSuccessToast("Repository panel layout updated.")
  }

  const handleApplyQuickPanelLayout = (
    items: RepoPanelLayoutItem[],
    presetId: string | null,
  ) => {
    if (presetId) {
      setActivePresetId(presetId)
    }
    setPanelLayoutItems(items)
    showSuccessToast("Repository panel layout updated.")
  }

  const handleResetPanelLayout = () => {
    setPanelLayoutItems(activePreset.items)
    showSuccessToast("Repository panel layout reset to preset.")
  }

  const handleSwitchPreset = (presetId: string) => {
    const nextPreset = resolveRepoLayoutPreset(layoutPresets, presetId)
    setActivePresetId(nextPreset.id)
    setPanelLayoutItems(nextPreset.items)
    showSuccessToast(`Preset switched to ${nextPreset.label}.`)
  }

  const handleSavePreset = (input: { label: string; description: string }) => {
    if (typeof window === "undefined") return

    const nextUserPresets =
      activePreset.source === "user"
        ? userPresets.map((preset) =>
            preset.id === activePreset.id
              ? {
                  ...preset,
                  label: input.label,
                  description: input.description,
                  items: panelLayoutItems,
                }
              : preset,
          )
        : [
            ...userPresets,
            createUserRepoLayoutPreset({
              id: buildRepoUserLayoutPresetId(
                input.label,
                [...systemPresets, ...userPresets].map((preset) => preset.id),
              ),
              label: input.label,
              description: input.description,
              items: panelLayoutItems,
            }),
          ]

    setUserPresets(nextUserPresets)
    writeUserRepoLayoutPresets(window.localStorage, nextUserPresets)

    const nextActivePreset =
      activePreset.source === "user"
        ? (nextUserPresets.find((preset) => preset.id === activePreset.id) ??
          nextUserPresets[0])
        : nextUserPresets[nextUserPresets.length - 1]

    if (nextActivePreset) {
      setActivePresetId(nextActivePreset.id)
    }

    setIsSavePresetOpen(false)
    showSuccessToast(
      activePreset.source === "user"
        ? "Layout preset updated."
        : "Layout preset saved.",
    )
  }

  const handleDeleteActivePreset = () => {
    if (
      !repo ||
      typeof window === "undefined" ||
      activePreset.source !== "user"
    )
      return

    const nextUserPresets = userPresets.filter(
      (preset) => preset.id !== activePreset.id,
    )
    const fallbackPreset = resolveRepoLayoutPreset(
      [...systemPresets, ...nextUserPresets],
      systemPresets[0]?.id,
    )

    setUserPresets(nextUserPresets)
    writeUserRepoLayoutPresets(window.localStorage, nextUserPresets)
    setActivePresetId(fallbackPreset.id)
    setPanelLayoutItems(fallbackPreset.items)
    showSuccessToast(`Preset ${activePreset.label} deleted.`)
  }

  const openAdvancedLayoutEditor = (items: RepoPanelLayoutItem[]) => {
    setPanelLayoutItems(items)
    setIsQuickLayoutDialogOpen(false)
    setIsLayoutEditorOpen(true)
  }

  if (isLoading) {
    return <RepoDetailSkeleton />
  }

  if (error || !repo) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="mb-4 rounded-full bg-destructive/10 p-4">
          <AlertCircleIcon className="size-8 text-destructive" />
        </div>
        <h3 className="text-lg font-semibold">Repository not found</h3>
        <p className="mb-4 text-muted-foreground">
          This repository does not exist or you do not have access to it.
        </p>
        <Button variant="outline" onClick={() => navigate({ to: "/repos" })}>
          <ArrowLeftIcon className="size-4" />
          Back to Repositories
        </Button>
      </div>
    )
  }

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 p-6">
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink asChild>
              <Link to="/repos">Repositories</Link>
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>{repo.display_name}</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      <div className="flex flex-col gap-4 rounded-3xl border bg-gradient-to-br from-background via-background to-muted/30 p-6 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-3xl font-semibold tracking-tight">
              {repo.display_name}
            </h1>
            <RepoStatusBadge repo={repo} className="text-sm" />
          </div>
          <div className="font-mono text-sm text-muted-foreground">
            {repo.slug}
          </div>
          <p className="max-w-3xl text-sm text-muted-foreground">
            {repo.description || "Managed repository import record."}
          </p>
          <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
            <span className="inline-flex items-center gap-2">
              <GitBranchIcon className="size-4" />
              Branch {defaultBranch}
            </span>
            <span className="inline-flex items-center gap-2">
              {repo.is_private ? (
                <LockIcon className="size-4" />
              ) : (
                <UnlockIcon className="size-4" />
              )}
              {repo.is_private ? "Private" : "Public"}
            </span>
            <span className="inline-flex items-center gap-2">
              {isViewerReady ? "Viewer ready" : "Viewer partial"}
            </span>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <Select value={activePreset.id} onValueChange={handleSwitchPreset}>
            <SelectTrigger className="w-[220px]">
              <SelectValue placeholder="Select layout preset" />
            </SelectTrigger>
            <SelectContent>
              {layoutPresets.map((preset) => (
                <SelectItem key={preset.id} value={preset.id}>
                  {preset.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <div className="inline-flex rounded-xl border bg-muted/30 p-1">
            <Button
              variant="ghost"
              size="sm"
              className={
                layoutMode === "panels" ? "bg-background shadow-sm" : ""
              }
              onClick={() => setLayoutMode("panels")}
            >
              Panels
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className={layoutMode === "tabs" ? "bg-background shadow-sm" : ""}
              onClick={() => setLayoutMode("tabs")}
            >
              Tabs
            </Button>
          </div>
          <Button variant="outline" onClick={() => refetch()}>
            <RefreshCwIcon
              className={isFetching ? "size-4 animate-spin" : "size-4"}
            />
            Refresh
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="outline"
                size="icon"
                aria-label="Repository layout actions"
              >
                <MoreVerticalIcon className="size-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={() => setIsQuickLayoutDialogOpen(true)}
              >
                <PanelsTopLeftIcon className="mr-2 size-4" />
                Panel Layout
                <span className="ml-auto text-xs text-muted-foreground">
                  Ctrl+Shift+L
                </span>
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setIsLayoutEditorOpen(true)}>
                <PanelsTopLeftIcon className="mr-2 size-4" />
                Advanced Layout Editor
                <span className="ml-auto text-xs text-muted-foreground">
                  Ctrl+Alt+L
                </span>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => setIsSavePresetOpen(true)}>
                <SaveIcon className="mr-2 size-4" />
                {activePreset.source === "user"
                  ? "Update Preset"
                  : "Save Preset"}
              </DropdownMenuItem>
              {canDeleteActivePreset ? (
                <DropdownMenuItem onClick={handleDeleteActivePreset}>
                  <Trash2Icon className="mr-2 size-4" />
                  Delete Preset
                </DropdownMenuItem>
              ) : null}
              {hasCustomizedPanelLayout ? (
                <DropdownMenuItem onClick={handleResetPanelLayout}>
                  <RefreshCwIcon className="mr-2 size-4" />
                  Reset to Preset
                </DropdownMenuItem>
              ) : null}
              {canManageRepo ? <DropdownMenuSeparator /> : null}
              {canManageRepo && canCancelImport ? (
                <DropdownMenuItem
                  disabled={
                    cancelImportMutation.isPending ||
                    deleteRepoMutation.isPending
                  }
                  onClick={() => {
                    if (
                      !window.confirm(
                        `Cancel import for "${repo.display_name}"? Any queued retries will be stopped.`,
                      )
                    ) {
                      return
                    }
                    cancelImportMutation.mutate()
                  }}
                >
                  <RefreshCwIcon className="mr-2 size-4" />
                  {cancelImportMutation.isPending
                    ? "Canceling Import..."
                    : "Cancel Import"}
                </DropdownMenuItem>
              ) : null}
              {canManageRepo ? (
                <DropdownMenuItem
                  disabled={
                    deleteRepoMutation.isPending ||
                    cancelImportMutation.isPending
                  }
                  className="text-destructive focus:text-destructive"
                  onClick={() => {
                    if (
                      !window.confirm(
                        `Delete "${repo.display_name}"? This removes the platform repo record and attempts to delete the managed forge repository.`,
                      )
                    ) {
                      return
                    }
                    deleteRepoMutation.mutate()
                  }}
                >
                  <Trash2Icon className="mr-2 size-4" />
                  {deleteRepoMutation.isPending
                    ? "Deleting..."
                    : "Delete Repository"}
                </DropdownMenuItem>
              ) : null}
            </DropdownMenuContent>
          </DropdownMenu>
          <Button asChild variant="outline">
            <Link to="/repos">
              <ArrowLeftIcon className="size-4" />
              Back
            </Link>
          </Button>
          {repo.gogs_html_url && (
            <Button asChild variant="outline">
              <a href={repo.gogs_html_url} target="_blank" rel="noreferrer">
                Internal Forge
                <ExternalLinkIcon className="size-4" />
              </a>
            </Button>
          )}
        </div>
      </div>

      <div className="rounded-2xl border bg-muted/20 px-4 py-3 text-sm text-muted-foreground">
        <span className="font-medium text-foreground">
          {activePreset.label}
        </span>
        {` · ${activePreset.description || "Custom repository workspace preset."}`}
        {hasCustomizedPanelLayout ? " · Modified for this repository." : ""}
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Created</CardDescription>
            <CardTitle className="text-base">
              {formatRepoDate(repo.created_at)}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Updated</CardDescription>
            <CardTitle className="text-base">
              {formatRepoDate(repo.updated_at)}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Default Branch</CardDescription>
            <CardTitle className="text-base">{defaultBranch}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Viewer</CardDescription>
            <CardTitle className="text-base">
              {isViewerReady ? "Enabled" : "Limited"}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Imported</CardDescription>
            <CardTitle className="text-base">
              {formatRepoDate(repo.imported_at)}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Owner User ID</CardDescription>
            <CardTitle className="truncate font-mono text-sm">
              {repo.owner_user_id}
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      <div className="min-h-[720px] overflow-hidden rounded-3xl border bg-background">
        <RepoLayout panels={panels} mode={layoutMode} />
      </div>

      <RepoPanelLayoutDialog
        open={isQuickLayoutDialogOpen}
        onOpenChange={setIsQuickLayoutDialogOpen}
        repoName={repo.display_name}
        presets={layoutPresets}
        activePresetId={activePreset.id}
        panels={panelLayoutItems}
        canReset={hasCustomizedPanelLayout}
        onApply={handleApplyQuickPanelLayout}
        onReset={handleResetPanelLayout}
        onOpenAdvanced={openAdvancedLayoutEditor}
      />
      <RepoLayoutEditorDialog
        open={isLayoutEditorOpen}
        onOpenChange={setIsLayoutEditorOpen}
        repoName={repo.display_name}
        panels={panelLayoutItems}
        capabilities={capabilities}
        onApply={handleApplyPanelLayout}
        onReset={handleResetPanelLayout}
        canReset={hasCustomizedPanelLayout}
      />
      <SaveRepoLayoutPresetDialog
        open={isSavePresetOpen}
        onOpenChange={setIsSavePresetOpen}
        title={
          activePreset.source === "user"
            ? "Update Layout Preset"
            : "Save Layout Preset"
        }
        description="Store this panel arrangement as a selectable repository workspace preset."
        initialLabel={activePreset.source === "user" ? activePreset.label : ""}
        initialDescription={
          activePreset.source === "user" ? activePreset.description : ""
        }
        confirmLabel={
          activePreset.source === "user" ? "Update Preset" : "Save Preset"
        }
        onConfirm={handleSavePreset}
      />
    </div>
  )
}
