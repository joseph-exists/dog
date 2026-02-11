// src/routes/_layout/personas.tsx

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import {
  Globe,
  Loader2Icon,
  PlusIcon,
  Search,
  Smile,
  TrashIcon,
} from "lucide-react"
import { Suspense, useMemo, useState } from "react"

import type { PersonaPublic } from "@/client"
import { PersonasService, UserPersonasService } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import CreatePersonaDialog from "@/components/Persona/CreatePersonaDialog"
import PersonaDetailDialog from "@/components/Persona/PersonaDetailDialog"
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
import useAuth from "@/hooks/useAuth"
import { showSuccessToast, showErrorToast } from "@/hooks/useCustomToast"
import { PersonaLibraryService } from "@/services/personaLibraryService"

export const Route = createFileRoute("/_layout/personas")({
  component: PersonasPage,
  head: () => ({
    meta: [{ title: "Personas" }],
  }),
})

// ============================================================================
// Query Options
// ============================================================================

function getMyPersonasQueryOptions(userId: string) {
  return {
    queryKey: ["persona-library", userId],
    queryFn: () =>
      PersonaLibraryService.getLibrary({ type: "user", id: userId, name: "" }),
    enabled: !!userId,
  }
}

function getAllPersonasQueryOptions() {
  return {
    queryKey: ["personas", "all"],
    queryFn: () => PersonasService.readPersonas({ limit: 100 }),
  }
}

// ============================================================================
// Action Buttons
// ============================================================================

function AddToLibraryButton({ persona }: { persona: PersonaPublic }) {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  

  const mutation = useMutation({
    mutationFn: () =>
      UserPersonasService.createUserPersona({
        requestBody: { persona_id: persona.id },
      }),
    onSuccess: () => {
      showSuccessToast(`Added "${persona.name}" to library`)
    },
    onError: (err: ApiError) => {
      const message =
        (err.body as { detail?: string })?.detail ||
        "Failed to add persona to library"
      showErrorToast(message)
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: ["persona-library", user?.id],
      })
    },
  })

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => mutation.mutate()}
      disabled={mutation.isPending}
      className="text-muted-foreground hover:text-primary hover:bg-primary/10 shrink-0"
      title="Add to library"
    >
      {mutation.isPending ? (
        <Loader2Icon className="size-4 animate-spin" />
      ) : (
        <PlusIcon className="size-4" />
      )}
    </Button>
  )
}

function DeletePersonaButton({ persona }: { persona: PersonaPublic }) {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  
  const [isOpen, setIsOpen] = useState(false)

  const mutation = useMutation({
    mutationFn: () => PersonasService.deletePersona({ id: persona.id }),
    onSuccess: () => {
      showSuccessToast(`Deleted "${persona.name}"`)
      setIsOpen(false)
    },
    onError: (err: ApiError) => {
      const message =
        (err.body as { detail?: string })?.detail || "Failed to delete persona"
      showErrorToast(message)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["personas"] })
      queryClient.invalidateQueries({
        queryKey: ["persona-library", user?.id],
      })
    },
  })

  return (
    <AlertDialog open={isOpen} onOpenChange={setIsOpen}>
      <AlertDialogTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="text-muted-foreground hover:text-destructive hover:bg-destructive/10 shrink-0"
        >
          <TrashIcon className="size-4" />
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Persona</AlertDialogTitle>
          <AlertDialogDescription>
            Permanently delete &quot;{persona.name}&quot;? This will also remove
            it from all libraries. This action cannot be undone.
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
// Catalog Persona Card (with add/view/delete actions)
// ============================================================================

function CatalogPersonaCard({ persona }: { persona: PersonaPublic }) {
  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <div className="flex items-start gap-3">
          <Link
            to="/persona/$personaId"
            params={{ personaId: persona.id }}
            className="shrink-0"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-pink-100 dark:bg-pink-900/30 hover:ring-2 hover:ring-pink-300 transition-all">
              <Smile className="size-5 text-pink-600 dark:text-pink-300" />
            </div>
          </Link>
          <div className="flex-1 min-w-0">
            <Link
              to="/persona/$personaId"
              params={{ personaId: persona.id }}
              className="hover:underline"
            >
              <h3 className="font-medium truncate">{persona.name}</h3>
            </Link>
            {persona.description && (
              <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
                {persona.description}
              </p>
            )}
          </div>

          <div className="flex items-center gap-0.5 shrink-0">
            <PersonaDetailDialog personaId={persona.id} className="size-7" />
            <AddToLibraryButton persona={persona} />
            <DeletePersonaButton persona={persona} />
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="flex flex-wrap gap-1.5">
          {persona.general_domain && (
            <DomainTag label={persona.general_domain} />
          )}
          {persona.specific_domain && (
            <DomainTag label={persona.specific_domain} />
          )}
        </div>
      </CardContent>
    </Card>
  )
}

function DomainTag({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300">
      <Globe className="size-3" />
      {label}
    </span>
  )
}

// ============================================================================
// Library Persona Card (with remove action)
// ============================================================================

function LibraryPersonaCard({
  persona,
  entryId,
}: {
  persona: PersonaPublic
  entryId: string
}) {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  
  const [isOpen, setIsOpen] = useState(false)

  const removeMutation = useMutation({
    mutationFn: () => UserPersonasService.deleteUserPersona({ id: entryId }),
    onSuccess: () => {
      showSuccessToast(`Removed "${persona.name}" from library`)
      setIsOpen(false)
    },
    onError: (err: ApiError) => {
      const message =
        (err.body as { detail?: string })?.detail || "Failed to remove persona"
      showErrorToast(message)
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: ["persona-library", user?.id],
      })
    },
  })

  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <div className="flex items-start gap-3">
          <Link
            to="/persona/$personaId"
            params={{ personaId: persona.id }}
            className="shrink-0"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-pink-100 dark:bg-pink-900/30 hover:ring-2 hover:ring-pink-300 transition-all">
              <Smile className="size-5 text-pink-600 dark:text-pink-300" />
            </div>
          </Link>
          <div className="flex-1 min-w-0">
            <Link
              to="/persona/$personaId"
              params={{ personaId: persona.id }}
              className="hover:underline"
            >
              <h3 className="font-medium truncate">{persona.name}</h3>
            </Link>
            {persona.description && (
              <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
                {persona.description}
              </p>
            )}
          </div>

          <div className="flex items-center gap-0.5 shrink-0">
            <PersonaDetailDialog personaId={persona.id} className="size-7" />
            <AlertDialog open={isOpen} onOpenChange={setIsOpen}>
              <AlertDialogTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                >
                  <TrashIcon className="size-4" />
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Remove Persona</AlertDialogTitle>
                  <AlertDialogDescription>
                    Remove &quot;{persona.name}&quot; from your library? The
                    persona will still exist in the catalog.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel disabled={removeMutation.isPending}>
                    Cancel
                  </AlertDialogCancel>
                  <AlertDialogAction
                    onClick={() => removeMutation.mutate()}
                    disabled={removeMutation.isPending}
                    className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                  >
                    {removeMutation.isPending && (
                      <Loader2Icon className="size-4 animate-spin" />
                    )}
                    Remove
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="flex flex-wrap gap-1.5">
          {persona.general_domain && (
            <DomainTag label={persona.general_domain} />
          )}
          {persona.specific_domain && (
            <DomainTag label={persona.specific_domain} />
          )}
        </div>
      </CardContent>
    </Card>
  )
}

// ============================================================================
// Skeletons
// ============================================================================

function PersonaCardSkeleton() {
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

function PendingPersonas() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <PersonaCardSkeleton />
      <PersonaCardSkeleton />
      <PersonaCardSkeleton />
    </div>
  )
}

// ============================================================================
// Content Sections
// ============================================================================

function PersonasListContent({ searchQuery }: { searchQuery: string }) {
  const { user } = useAuth()

  const { data: libraryData, isLoading: libraryLoading } = useQuery(
    getMyPersonasQueryOptions(user?.id ?? ""),
  )

  const { data: allData, isLoading: allLoading } = useQuery(
    getAllPersonasQueryOptions(),
  )

  // Build a map of persona ID → persona for library entries
  const allPersonas = allData?.data ?? []
  const personaMap = useMemo(() => {
    const map = new Map<string, PersonaPublic>()
    for (const p of allPersonas) {
      map.set(p.id, p)
    }
    return map
  }, [allPersonas])

  // Filter all personas by search
  const filteredAll = useMemo(() => {
    if (!searchQuery) return allPersonas
    const q = searchQuery.toLowerCase()
    return allPersonas.filter(
      (p) =>
        p.name.toLowerCase().includes(q) ||
        p.description?.toLowerCase().includes(q) ||
        p.general_domain?.toLowerCase().includes(q) ||
        p.specific_domain?.toLowerCase().includes(q),
    )
  }, [allPersonas, searchQuery])

  // Library persona IDs for the "in library" indicator
  const libraryPersonaIds = useMemo(
    () => new Set((libraryData ?? []).map((lp) => lp.personaId)),
    [libraryData],
  )

  // Filter catalog to exclude library personas
  const catalogPersonas = useMemo(
    () => filteredAll.filter((p) => !libraryPersonaIds.has(p.id)),
    [filteredAll, libraryPersonaIds],
  )

  if (libraryLoading || allLoading) {
    return <PendingPersonas />
  }

  const hasLibrary = (libraryData ?? []).length > 0
  const hasCatalog = catalogPersonas.length > 0

  if (!hasLibrary && !hasCatalog) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-muted p-4 mb-4">
          <Smile className="size-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">No personas yet</h3>
        <p className="text-muted-foreground mb-4">
          {searchQuery
            ? "No personas match your search"
            : "Create your first persona to get started"}
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* My Library */}
      {hasLibrary && (
        <section>
          <h2 className="text-lg font-semibold mb-4">My Library</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {(libraryData ?? []).map((lp) => {
              const persona = personaMap.get(lp.personaId)
              if (!persona) return null
              return (
                <LibraryPersonaCard
                  key={lp.libraryEntryId}
                  persona={persona}
                  entryId={lp.libraryEntryId}
                />
              )
            })}
          </div>
        </section>
      )}

      {/* All Personas (catalog) */}
      {hasCatalog && (
        <section>
          <h2 className="text-lg font-semibold mb-4 text-muted-foreground">
            All Personas
          </h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {catalogPersonas.map((persona) => (
              <CatalogPersonaCard key={persona.id} persona={persona} />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}

// ============================================================================
// Main Page
// ============================================================================

function PersonasPage() {
  const [searchQuery, setSearchQuery] = useState("")

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Personas</h1>
          <p className="text-muted-foreground">
            Browse and manage your persona library
          </p>
        </div>
        <CreatePersonaDialog />
      </div>

      {/* Search */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
        <Input
          placeholder="Search personas..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-9"
        />
      </div>

      <Suspense fallback={<PendingPersonas />}>
        <PersonasListContent searchQuery={searchQuery} />
      </Suspense>
    </div>
  )
}
