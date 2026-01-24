// src/routes/_layout/archetypes.tsx

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { Crown, Loader2Icon, Search, TrashIcon } from "lucide-react"
import { Suspense, useMemo, useState } from "react"

import type { ArchetypePublic } from "@/client"
import { ArchetypesService } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import CreateArchetypeDialog from "@/components/Archetype/CreateArchetypeDialog"
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
import useCustomToast from "@/hooks/useCustomToast"

export const Route = createFileRoute("/_layout/archetypes")({
  component: ArchetypesPage,
  head: () => ({
    meta: [{ title: "Archetypes" }],
  }),
})

// ============================================================================
// Query Options
// ============================================================================

function getAllArchetypesQueryOptions() {
  return {
    queryKey: ["archetypes", "all"],
    queryFn: () => ArchetypesService.readArchetypes({ limit: 100 }),
  }
}

// ============================================================================
// Delete Button
// ============================================================================

function DeleteArchetypeButton({ archetype }: { archetype: ArchetypePublic }) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [isOpen, setIsOpen] = useState(false)

  const mutation = useMutation({
    mutationFn: () => ArchetypesService.deleteArchetype({ id: archetype.id }),
    onSuccess: () => {
      showSuccessToast(`Deleted "${archetype.name}"`)
      setIsOpen(false)
    },
    onError: (err: ApiError) => {
      const message =
        (err.body as { detail?: string })?.detail ||
        "Failed to delete archetype"
      showErrorToast(message)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["archetypes"] })
    },
  })

  return (
    <AlertDialog open={isOpen} onOpenChange={setIsOpen}>
      <AlertDialogTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="text-muted-foreground hover:text-destructive hover:bg-destructive/10 shrink-0"
          title="Delete archetype"
        >
          <TrashIcon className="size-4" />
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Archetype</AlertDialogTitle>
          <AlertDialogDescription>
            Permanently delete &quot;{archetype.name}&quot;? Personas using this
            archetype will keep their inherited traits but lose the archetype
            reference. This action cannot be undone.
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
// Archetype Card
// ============================================================================

function ArchetypeCard({ archetype }: { archetype: ArchetypePublic }) {
  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <div className="flex items-start gap-3">
          <Link
            to="/archetype/$archetypeId"
            params={{ archetypeId: archetype.id }}
            className="shrink-0"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-amber-100 dark:bg-amber-900/30 hover:ring-2 hover:ring-amber-300 transition-all">
              <Crown className="size-5 text-amber-600 dark:text-amber-300" />
            </div>
          </Link>
          <div className="flex-1 min-w-0">
            <Link
              to="/archetype/$archetypeId"
              params={{ archetypeId: archetype.id }}
              className="hover:underline"
            >
              <h3 className="font-medium truncate">{archetype.name}</h3>
            </Link>
            {archetype.description && (
              <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
                {archetype.description}
              </p>
            )}
          </div>

          <div className="flex items-center gap-0.5 shrink-0">
            <DeleteArchetypeButton archetype={archetype} />
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <p className="text-xs text-muted-foreground">
          Created {new Date(archetype.created_at).toLocaleDateString()}
        </p>
      </CardContent>
    </Card>
  )
}

// ============================================================================
// Skeletons
// ============================================================================

function ArchetypeCardSkeleton() {
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

function PendingArchetypes() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <ArchetypeCardSkeleton />
      <ArchetypeCardSkeleton />
      <ArchetypeCardSkeleton />
    </div>
  )
}

// ============================================================================
// Content
// ============================================================================

function ArchetypesListContent({ searchQuery }: { searchQuery: string }) {
  const { data, isLoading } = useQuery(getAllArchetypesQueryOptions())

  const archetypes = data?.data ?? []

  // Filter by search query
  const filtered = useMemo(() => {
    if (!searchQuery) return archetypes
    const q = searchQuery.toLowerCase()
    return archetypes.filter(
      (a) =>
        a.name.toLowerCase().includes(q) ||
        a.description?.toLowerCase().includes(q),
    )
  }, [archetypes, searchQuery])

  if (isLoading) {
    return <PendingArchetypes />
  }

  if (filtered.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-muted p-4 mb-4">
          <Crown className="size-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">No archetypes yet</h3>
        <p className="text-muted-foreground mb-4">
          {searchQuery
            ? "No archetypes match your search"
            : "Create your first archetype to define reusable trait sets"}
        </p>
      </div>
    )
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {filtered.map((archetype) => (
        <ArchetypeCard key={archetype.id} archetype={archetype} />
      ))}
    </div>
  )
}

// ============================================================================
// Main Page
// ============================================================================

function ArchetypesPage() {
  const [searchQuery, setSearchQuery] = useState("")

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Archetypes</h1>
          <p className="text-muted-foreground">
            Define reusable trait and quality sets for personas
          </p>
        </div>
        <CreateArchetypeDialog />
      </div>

      {/* Search */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
        <Input
          placeholder="Search archetypes..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-9"
        />
      </div>

      <Suspense fallback={<PendingArchetypes />}>
        <ArchetypesListContent searchQuery={searchQuery} />
      </Suspense>
    </div>
  )
}
