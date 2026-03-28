import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import {
  ExternalLinkIcon,
  EyeIcon,
  LayoutTemplate,
  Loader2Icon,
  PencilIcon,
  PlayIcon,
  SearchIcon,
  TrashIcon,
  UserIcon,
} from "lucide-react"
import { useMemo, useState } from "react"

import { type DemoConfigPublic, DemosService } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { Textarea } from "@/components/ui/textarea"
import useAuth from "@/hooks/useAuth"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import { cn } from "@/lib/utils"

const DEMO_LIBRARY_QUERY_KEY = ["demo-library", "all-visible"] as const

type ScopeFilter = "all" | "personal" | "shared" | "system"
type StatusFilter = "all" | "active" | "inactive"
type OwnershipFilter = "all" | "mine"

function getDemoLibraryQueryOptions() {
  return {
    queryKey: DEMO_LIBRARY_QUERY_KEY,
    queryFn: () =>
      DemosService.listAllDemoConfigs({
        includeInactive: true,
        includeSystem: true,
        limit: 200,
      }),
  }
}

function getScopeLabel(scope?: DemoConfigPublic["scope"]) {
  switch (scope) {
    case "personal":
      return "Personal"
    case "shared":
      return "Shared"
    case "system":
      return "System"
    default:
      return "Unknown"
  }
}

function isDemoOwner(demo: DemoConfigPublic, userId?: string | null) {
  return Boolean(userId && demo.owner_id === userId)
}

function getDemoSearchText(demo: DemoConfigPublic) {
  return [demo.title, demo.slug, demo.description ?? ""].join(" ").toLowerCase()
}

function ScopeBadge({ scope }: { scope?: DemoConfigPublic["scope"] }) {
  const className =
    scope === "personal"
      ? "bg-blue-100 text-blue-800 hover:bg-blue-100 dark:bg-blue-900/30 dark:text-blue-300"
      : scope === "shared"
        ? "bg-emerald-100 text-emerald-800 hover:bg-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-300"
        : "bg-amber-100 text-amber-800 hover:bg-amber-100 dark:bg-amber-900/30 dark:text-amber-300"

  return (
    <Badge className={className}>
      <LayoutTemplate className="size-3" />
      {getScopeLabel(scope)}
    </Badge>
  )
}

function StatusBadge({ isActive }: { isActive?: boolean }) {
  return (
    <Badge variant={isActive ? "default" : "outline"}>
      {isActive ? "Active" : "Inactive"}
    </Badge>
  )
}

function OwnershipBadge({
  demo,
  isOwner,
}: {
  demo: DemoConfigPublic
  isOwner: boolean
}) {
  if (isOwner) {
    return (
      <Badge variant="secondary">
        <UserIcon className="size-3" />
        Mine
      </Badge>
    )
  }

  if (demo.owner_id) {
    return (
      <Badge variant="outline">
        <UserIcon className="size-3" />
        Shared Access
      </Badge>
    )
  }

  return (
    <Badge variant="outline">
      <UserIcon className="size-3" />
      System
    </Badge>
  )
}

function DemoCard({
  demo,
  isOwner,
  variant = "grid",
  onOpen,
}: {
  demo: DemoConfigPublic
  isOwner: boolean
  variant?: "grid" | "detail"
  onOpen?: () => void
}) {
  const updatedAt = new Date(demo.updated_at).toLocaleString()
  const createdAt = new Date(demo.created_at).toLocaleString()
  const interactive = variant === "grid" && onOpen

  return (
    <Card
      className={cn(
        "h-full transition-all",
        interactive && "cursor-pointer hover:border-primary/50 hover:shadow-md",
      )}
      onClick={interactive ? onOpen : undefined}
      onKeyDown={
        interactive
          ? (event) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault()
                onOpen()
              }
            }
          : undefined
      }
      role={interactive ? "button" : undefined}
      tabIndex={interactive ? 0 : undefined}
    >
      <CardHeader className={cn("gap-3", variant === "detail" && "pb-4")}>
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 space-y-1">
            <CardTitle className="truncate text-lg">{demo.title}</CardTitle>
            <p className="font-mono text-xs text-muted-foreground">
              /demo/{demo.slug}
            </p>
          </div>

          {variant === "grid" && (
            <Button
              variant="ghost"
              size="icon"
              className="shrink-0"
              onClick={(event) => {
                event.stopPropagation()
                onOpen?.()
              }}
            >
              <EyeIcon className="size-4" />
            </Button>
          )}
        </div>

        <div className="flex flex-wrap gap-2">
          <ScopeBadge scope={demo.scope} />
          <StatusBadge isActive={demo.is_active} />
          <OwnershipBadge demo={demo} isOwner={isOwner} />
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <p
          className={cn(
            "text-sm text-muted-foreground",
            variant === "grid"
              ? "line-clamp-3 min-h-[3.75rem]"
              : "whitespace-pre-wrap",
          )}
        >
          {demo.description?.trim() || "No description provided."}
        </p>

        <div className="grid gap-2 text-sm">
          <div className="flex items-center justify-between gap-3">
            <span className="text-muted-foreground">Updated</span>
            <span className="text-right">{updatedAt}</span>
          </div>
          <div className="flex items-center justify-between gap-3">
            <span className="text-muted-foreground">Created</span>
            <span className="text-right">{createdAt}</span>
          </div>
          <div className="flex items-center justify-between gap-3">
            <span className="text-muted-foreground">Owner</span>
            <span className="text-right">
              {isOwner ? "You" : demo.owner_id ? "Visible to you" : "System"}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function DemoCardSkeleton() {
  return (
    <Card>
      <CardHeader className="space-y-3">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1 space-y-2">
            <Skeleton className="h-5 w-40" />
            <Skeleton className="h-4 w-32" />
          </div>
          <Skeleton className="size-8 rounded-md" />
        </div>
        <div className="flex gap-2">
          <Skeleton className="h-5 w-20 rounded-full" />
          <Skeleton className="h-5 w-16 rounded-full" />
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-5/6" />
        <Skeleton className="h-4 w-2/3" />
      </CardContent>
    </Card>
  )
}

function PendingDemos() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      <DemoCardSkeleton />
      <DemoCardSkeleton />
      <DemoCardSkeleton />
      <DemoCardSkeleton />
      <DemoCardSkeleton />
      <DemoCardSkeleton />
    </div>
  )
}

function DeleteDemoButton({
  demo,
  onDeleted,
}: {
  demo: DemoConfigPublic
  onDeleted?: () => void
}) {
  const queryClient = useQueryClient()
  const [isOpen, setIsOpen] = useState(false)

  const mutation = useMutation({
    mutationFn: () =>
      DemosService.deleteExistingDemoConfig({ demoConfigId: demo.id }),
    onSuccess: () => {
      showSuccessToast(`Deleted "${demo.title}"`)
      setIsOpen(false)
      onDeleted?.()
    },
    onError: (error: ApiError) => {
      const message =
        (error.body as { detail?: string })?.detail || "Failed to delete demo"
      showErrorToast(message)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: DEMO_LIBRARY_QUERY_KEY })
    },
  })

  return (
    <AlertDialog open={isOpen} onOpenChange={setIsOpen}>
      <AlertDialogTrigger asChild>
        <Button variant="destructive" size="sm">
          <TrashIcon className="size-4" />
          Delete
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Demo</AlertDialogTitle>
          <AlertDialogDescription>
            Permanently delete &ldquo;{demo.title}&rdquo;? This action cannot be
            undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={mutation.isPending}>
            Cancel
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {mutation.isPending && (
              <Loader2Icon className="size-4 animate-spin" />
            )}
            Delete
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}

function RenameDemoButton({ demo }: { demo: DemoConfigPublic }) {
  const queryClient = useQueryClient()
  const [isOpen, setIsOpen] = useState(false)
  const [titleDraft, setTitleDraft] = useState(demo.title)
  const [descriptionDraft, setDescriptionDraft] = useState(
    demo.description ?? "",
  )

  const nextTitle = titleDraft.trim()
  const nextDescription = descriptionDraft.trim()
  const isUnchanged = nextTitle === demo.title
  const originalDescription = (demo.description ?? "").trim()
  const isDescriptionUnchanged = nextDescription === originalDescription

  const mutation = useMutation({
    mutationFn: () =>
      DemosService.updateExistingDemoConfig({
        demoConfigId: demo.id,
        requestBody: {
          title: nextTitle,
          description: nextDescription || null,
        },
      }),
    onSuccess: (updated) => {
      showSuccessToast(`Updated "${updated.title}"`)
      setIsOpen(false)
    },
    onError: (error: ApiError) => {
      const message =
        (error.body as { detail?: string })?.detail ||
        "Failed to update demo details"
      showErrorToast(message)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: DEMO_LIBRARY_QUERY_KEY })
    },
  })

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => {
        setIsOpen(open)
        if (open) {
          setTitleDraft(demo.title)
          setDescriptionDraft(demo.description ?? "")
        }
      }}
    >
      <Button variant="outline" size="sm" onClick={() => setIsOpen(true)}>
        <PencilIcon className="size-4" />
        Edit Details
      </Button>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Edit Demo Details</DialogTitle>
          <DialogDescription>
            Update the title and description shown in Demo Library and Builder.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <label
              htmlFor={`rename-demo-${demo.id}`}
              className="text-sm font-medium"
            >
              Demo name
            </label>
            <Input
              id={`rename-demo-${demo.id}`}
              value={titleDraft}
              onChange={(event) => setTitleDraft(event.target.value)}
              placeholder="Enter a demo name"
              maxLength={120}
            />
          </div>

          <div className="space-y-2">
            <label
              htmlFor={`demo-description-${demo.id}`}
              className="text-sm font-medium"
            >
              Description
            </label>
            <Textarea
              id={`demo-description-${demo.id}`}
              value={descriptionDraft}
              onChange={(event) => setDescriptionDraft(event.target.value)}
              placeholder="Add a short description for this demo"
              rows={5}
            />
          </div>

          <p className="text-xs text-muted-foreground">
            Slug stays unchanged: {demo.slug}
          </p>
        </div>

        <DialogFooter>
          <Button
            variant="secondary"
            onClick={() => setIsOpen(false)}
            disabled={mutation.isPending}
          >
            Cancel
          </Button>
          <Button
            onClick={() => mutation.mutate()}
            disabled={
              mutation.isPending ||
              !nextTitle ||
              (isUnchanged && isDescriptionUnchanged)
            }
          >
            {mutation.isPending && (
              <Loader2Icon className="size-4 animate-spin" />
            )}
            Save
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function DemoDetailDialog({
  demo,
  isOwner,
  open,
  onOpenChange,
}: {
  demo: DemoConfigPublic | null
  isOwner: boolean
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        {!demo ? null : (
          <>
            <DialogHeader>
              <DialogTitle>{demo.title}</DialogTitle>
              <DialogDescription>
                Review details, launch the demo, or manage it if you own it.
              </DialogDescription>
            </DialogHeader>

            <DemoCard demo={demo} isOwner={isOwner} variant="detail" />

            <DialogFooter className="sm:justify-between">
              <div className="flex flex-col-reverse gap-2 sm:flex-row">
                {isOwner && <RenameDemoButton demo={demo} />}
                {isOwner && (
                  <Button variant="outline" size="sm" asChild>
                    <Link
                      to="/demo-builder"
                      search={{ demoConfigId: demo.id }}
                      onClick={() => onOpenChange(false)}
                    >
                      <PencilIcon className="size-4" />
                      Edit In Builder
                    </Link>
                  </Button>
                )}
                {isOwner && (
                  <DeleteDemoButton
                    demo={demo}
                    onDeleted={() => onOpenChange(false)}
                  />
                )}
              </div>

              <div className="flex flex-col-reverse gap-2 sm:flex-row">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => onOpenChange(false)}
                >
                  Close
                </Button>
                <Button size="sm" asChild>
                  <Link
                    to="/demo/$slug"
                    params={{ slug: demo.slug }}
                    onClick={() => onOpenChange(false)}
                  >
                    <PlayIcon className="size-4" />
                    Start Demo
                  </Link>
                </Button>
              </div>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}

export function DemoLibraryPage() {
  const { user } = useAuth()
  const [searchQuery, setSearchQuery] = useState("")
  const [scopeFilter, setScopeFilter] = useState<ScopeFilter>("all")
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all")
  const [ownershipFilter, setOwnershipFilter] = useState<OwnershipFilter>("all")
  const [selectedDemoId, setSelectedDemoId] = useState<string | null>(null)

  const { data, isLoading } = useQuery(getDemoLibraryQueryOptions())
  const demos = data?.data ?? []

  const filteredDemos = useMemo(() => {
    const normalizedSearch = searchQuery.trim().toLowerCase()

    return [...demos]
      .filter((demo) => {
        if (scopeFilter !== "all" && demo.scope !== scopeFilter) {
          return false
        }

        if (statusFilter === "active" && !demo.is_active) {
          return false
        }

        if (statusFilter === "inactive" && demo.is_active !== false) {
          return false
        }

        if (
          ownershipFilter === "mine" &&
          !isDemoOwner(demo, user?.id ?? null)
        ) {
          return false
        }

        if (!normalizedSearch) {
          return true
        }

        return getDemoSearchText(demo).includes(normalizedSearch)
      })
      .sort(
        (left, right) =>
          new Date(right.updated_at).getTime() -
          new Date(left.updated_at).getTime(),
      )
  }, [demos, ownershipFilter, scopeFilter, searchQuery, statusFilter, user?.id])

  const selectedDemo = useMemo(
    () => demos.find((demo) => demo.id === selectedDemoId) ?? null,
    [demos, selectedDemoId],
  )

  const selectedDemoOwner = selectedDemo
    ? isDemoOwner(selectedDemo, user?.id ?? null)
    : false

  const hasAnyDemos = demos.length > 0

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Demo Library</h1>
          <p className="text-muted-foreground">
            Browse every demo you can access, then launch or manage it from a
            single place.
          </p>
        </div>

        <Button variant="outline" size="sm" asChild>
          <Link to="/demo-builder">
            <ExternalLinkIcon className="size-4" />
            Open Demo Builder
          </Link>
        </Button>
      </div>

      <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_180px_180px_180px]">
        <div className="relative">
          <SearchIcon className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="Search demos by title, slug, or description..."
            className="pl-9"
          />
        </div>

        <Select
          value={scopeFilter}
          onValueChange={(value) => setScopeFilter(value as ScopeFilter)}
        >
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Scope" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All scopes</SelectItem>
            <SelectItem value="personal">Personal</SelectItem>
            <SelectItem value="shared">Shared</SelectItem>
            <SelectItem value="system">System</SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={statusFilter}
          onValueChange={(value) => setStatusFilter(value as StatusFilter)}
        >
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="inactive">Inactive</SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={ownershipFilter}
          onValueChange={(value) =>
            setOwnershipFilter(value as OwnershipFilter)
          }
        >
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Ownership" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All visible</SelectItem>
            <SelectItem value="mine">Mine</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="flex items-center justify-between gap-3 text-sm text-muted-foreground">
        <span>
          {filteredDemos.length} {filteredDemos.length === 1 ? "demo" : "demos"}
        </span>
        {(searchQuery ||
          scopeFilter !== "all" ||
          statusFilter !== "all" ||
          ownershipFilter !== "all") && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setSearchQuery("")
              setScopeFilter("all")
              setStatusFilter("all")
              setOwnershipFilter("all")
            }}
          >
            Clear filters
          </Button>
        )}
      </div>

      {isLoading ? (
        <PendingDemos />
      ) : !hasAnyDemos ? (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-16 text-center">
          <div className="mb-4 rounded-full bg-muted p-4">
            <LayoutTemplate className="size-8 text-muted-foreground" />
          </div>
          <h2 className="text-lg font-semibold">No demos available</h2>
          <p className="mt-2 max-w-md text-sm text-muted-foreground">
            Once demos are created or shared with you, they will appear here.
          </p>
        </div>
      ) : filteredDemos.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-16 text-center">
          <div className="mb-4 rounded-full bg-muted p-4">
            <SearchIcon className="size-8 text-muted-foreground" />
          </div>
          <h2 className="text-lg font-semibold">
            No demos match these filters
          </h2>
          <p className="mt-2 max-w-md text-sm text-muted-foreground">
            Adjust the search or filter controls to broaden the results.
          </p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {filteredDemos.map((demo) => (
            <DemoCard
              key={demo.id}
              demo={demo}
              isOwner={isDemoOwner(demo, user?.id ?? null)}
              onOpen={() => setSelectedDemoId(demo.id)}
            />
          ))}
        </div>
      )}

      <DemoDetailDialog
        demo={selectedDemo}
        isOwner={selectedDemoOwner}
        open={Boolean(selectedDemo)}
        onOpenChange={(open) => {
          if (!open) {
            setSelectedDemoId(null)
          }
        }}
      />
    </div>
  )
}
