// src/routes/_layout/qualities.tsx

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { Gem, Loader2Icon, Search, TrashIcon } from "lucide-react"
import { Suspense, useMemo, useState } from "react"

import type { QualityPublic } from "@/client"
import { QualitiesService } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import CreateQualityDialog from "@/components/Quality/CreateQualityDialog"
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
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"

export const Route = createFileRoute("/_layout/qualities")({
  component: QualitiesPage,
  head: () => ({
    meta: [{ title: "Qualities" }],
  }),
})

// ============================================================================
// Query Options
// ============================================================================

function getAllQualitiesQueryOptions() {
  return {
    queryKey: ["qualities", "all"],
    queryFn: () => QualitiesService.readQualities({ limit: 100 }),
  }
}

// ============================================================================
// Delete Button
// ============================================================================

function DeleteQualityButton({ quality }: { quality: QualityPublic }) {
  const queryClient = useQueryClient()

  const [isOpen, setIsOpen] = useState(false)

  const mutation = useMutation({
    mutationFn: () => QualitiesService.deleteQuality({ id: quality.id }),
    onSuccess: () => {
      showSuccessToast(`Deleted "${quality.name}"`)
      setIsOpen(false)
    },
    onError: (err: ApiError) => {
      const message =
        (err.body as { detail?: string })?.detail || "Failed to delete quality"
      showErrorToast(message)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["qualities"] })
    },
  })

  return (
    <AlertDialog open={isOpen} onOpenChange={setIsOpen}>
      <AlertDialogTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="text-muted-foreground hover:text-destructive hover:bg-destructive/10 shrink-0"
          title="Delete quality"
        >
          <TrashIcon className="size-4" />
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Quality</AlertDialogTitle>
          <AlertDialogDescription>
            Permanently delete &quot;{quality.name}&quot;? Archetypes and
            personas using this quality will lose the reference. This action
            cannot be undone.
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

// ============================================================================
// Quality Card
// ============================================================================

function QualityCard({ quality }: { quality: QualityPublic }) {
  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <div className="flex items-start gap-3">
          <Link
            to="/quality/$qualityId"
            params={{ qualityId: quality.id }}
            className="shrink-0"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-violet-100 dark:bg-violet-900/30 hover:ring-2 hover:ring-violet-300 transition-all">
              <Gem className="size-5 text-violet-600 dark:text-violet-300" />
            </div>
          </Link>
          <div className="flex-1 min-w-0">
            <Link
              to="/quality/$qualityId"
              params={{ qualityId: quality.id }}
              className="hover:underline"
            >
              <h3 className="font-medium truncate">{quality.name}</h3>
            </Link>
            {quality.description && (
              <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
                {quality.description}
              </p>
            )}
          </div>

          <div className="flex items-center gap-0.5 shrink-0">
            <DeleteQualityButton quality={quality} />
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <p className="text-xs text-muted-foreground">
          Created {new Date(quality.created_at).toLocaleDateString()}
        </p>
      </CardContent>
    </Card>
  )
}

// ============================================================================
// Skeletons
// ============================================================================

function QualityCardSkeleton() {
  return (
    <Card>
      <CardHeader className="flex flex-row items-start gap-3">
        <Skeleton className="size-10 rounded-full" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-4 w-48" />
        </div>
      </CardHeader>
      <CardContent>
        <Skeleton className="h-4 w-24" />
      </CardContent>
    </Card>
  )
}

function PendingQualities() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <QualityCardSkeleton />
      <QualityCardSkeleton />
      <QualityCardSkeleton />
    </div>
  )
}

// ============================================================================
// Content
// ============================================================================

function QualitiesListContent({ searchQuery }: { searchQuery: string }) {
  const { data, isLoading } = useQuery(getAllQualitiesQueryOptions())

  const qualities = data?.data ?? []

  const filtered = useMemo(() => {
    if (!searchQuery) return qualities
    const q = searchQuery.toLowerCase()
    return qualities.filter(
      (item) =>
        item.name.toLowerCase().includes(q) ||
        item.description?.toLowerCase().includes(q),
    )
  }, [qualities, searchQuery])

  if (isLoading) {
    return <PendingQualities />
  }

  if (filtered.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-muted p-4 mb-4">
          <Gem className="size-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">No qualities yet</h3>
        <p className="text-muted-foreground mb-4">
          {searchQuery
            ? "No qualities match your search"
            : "Create your first quality to define personality attributes"}
        </p>
      </div>
    )
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {filtered.map((quality) => (
        <QualityCard key={quality.id} quality={quality} />
      ))}
    </div>
  )
}

// ============================================================================
// Main Page
// ============================================================================

function QualitiesPage() {
  const [searchQuery, setSearchQuery] = useState("")

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Qualities</h1>
          <p className="text-muted-foreground">
            Define personality attributes that can be linked to traits
          </p>
        </div>
        <CreateQualityDialog />
      </div>

      {/* Search */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
        <Input
          placeholder="Search qualities..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-9"
        />
      </div>

      <Suspense fallback={<PendingQualities />}>
        <QualitiesListContent searchQuery={searchQuery} />
      </Suspense>
    </div>
  )
}
