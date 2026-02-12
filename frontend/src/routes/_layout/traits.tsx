// src/routes/_layout/traits.tsx

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { Loader2Icon, Search, Sparkles, TrashIcon } from "lucide-react"
import { Suspense, useMemo, useState } from "react"

import type { TraitPublic } from "@/client"
import { TraitsService } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import CreateTraitDialog from "@/components/Trait/CreateTraitDialog"
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

export const Route = createFileRoute("/_layout/traits")({
  component: TraitsPage,
  head: () => ({
    meta: [{ title: "Traits" }],
  }),
})

// ============================================================================
// Query Options
// ============================================================================

function getAllTraitsQueryOptions() {
  return {
    queryKey: ["traits", "all"],
    queryFn: () => TraitsService.readTraits({ limit: 100 }),
  }
}

// ============================================================================
// Delete Button
// ============================================================================

function DeleteTraitButton({ trait }: { trait: TraitPublic }) {
  const queryClient = useQueryClient()

  const [isOpen, setIsOpen] = useState(false)

  const mutation = useMutation({
    mutationFn: () => TraitsService.deleteTrait({ id: trait.id }),
    onSuccess: () => {
      showSuccessToast(`Deleted "${trait.name}"`)
      setIsOpen(false)
    },
    onError: (err: ApiError) => {
      const message =
        (err.body as { detail?: string })?.detail || "Failed to delete trait"
      showErrorToast(message)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["traits"] })
    },
  })

  return (
    <AlertDialog open={isOpen} onOpenChange={setIsOpen}>
      <AlertDialogTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="text-muted-foreground hover:text-destructive hover:bg-destructive/10 shrink-0"
          title="Delete trait"
        >
          <TrashIcon className="size-4" />
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Trait</AlertDialogTitle>
          <AlertDialogDescription>
            Permanently delete &quot;{trait.name}&quot;? Archetypes and personas
            using this trait will lose the reference. This action cannot be
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

// ============================================================================
// Trait Card
// ============================================================================

function TraitCard({ trait }: { trait: TraitPublic }) {
  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <div className="flex items-start gap-3">
          <Link
            to="/trait/$traitId"
            params={{ traitId: trait.id }}
            className="shrink-0"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-rose-100 dark:bg-rose-900/30 hover:ring-2 hover:ring-rose-300 transition-all">
              <Sparkles className="size-5 text-rose-600 dark:text-rose-300" />
            </div>
          </Link>
          <div className="flex-1 min-w-0">
            <Link
              to="/trait/$traitId"
              params={{ traitId: trait.id }}
              className="hover:underline"
            >
              <h3 className="font-medium truncate">{trait.name}</h3>
            </Link>
            {trait.description && (
              <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
                {trait.description}
              </p>
            )}
          </div>

          <div className="flex items-center gap-0.5 shrink-0">
            <DeleteTraitButton trait={trait} />
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <p className="text-xs text-muted-foreground">
          Created {new Date(trait.created_at).toLocaleDateString()}
        </p>
      </CardContent>
    </Card>
  )
}

// ============================================================================
// Skeletons
// ============================================================================

function TraitCardSkeleton() {
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

function PendingTraits() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <TraitCardSkeleton />
      <TraitCardSkeleton />
      <TraitCardSkeleton />
    </div>
  )
}

// ============================================================================
// Content
// ============================================================================

function TraitsListContent({ searchQuery }: { searchQuery: string }) {
  const { data, isLoading } = useQuery(getAllTraitsQueryOptions())

  const traits = data?.data ?? []

  const filtered = useMemo(() => {
    if (!searchQuery) return traits
    const q = searchQuery.toLowerCase()
    return traits.filter(
      (item) =>
        item.name.toLowerCase().includes(q) ||
        item.description?.toLowerCase().includes(q),
    )
  }, [traits, searchQuery])

  if (isLoading) {
    return <PendingTraits />
  }

  if (filtered.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-muted p-4 mb-4">
          <Sparkles className="size-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">No traits yet</h3>
        <p className="text-muted-foreground mb-4">
          {searchQuery
            ? "No traits match your search"
            : "Create your first trait to define personality characteristics"}
        </p>
      </div>
    )
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {filtered.map((trait) => (
        <TraitCard key={trait.id} trait={trait} />
      ))}
    </div>
  )
}

// ============================================================================
// Main Page
// ============================================================================

function TraitsPage() {
  const [searchQuery, setSearchQuery] = useState("")

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Traits</h1>
          <p className="text-muted-foreground">
            Define personality characteristics that can be linked to qualities
          </p>
        </div>
        <CreateTraitDialog />
      </div>

      {/* Search */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
        <Input
          placeholder="Search traits..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-9"
        />
      </div>

      <Suspense fallback={<PendingTraits />}>
        <TraitsListContent searchQuery={searchQuery} />
      </Suspense>
    </div>
  )
}
