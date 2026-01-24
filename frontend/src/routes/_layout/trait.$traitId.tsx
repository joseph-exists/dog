// src/routes/_layout/trait.$traitId.tsx

import { useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { Sparkles } from "lucide-react"
import { useEffect, useRef } from "react"

import { TraitsService } from "@/client"
import { PageShell } from "@/components/Page"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import useAuth from "@/hooks/useAuth"
import { usePageEditor } from "@/hooks/usePageEditor"

export const Route = createFileRoute("/_layout/trait/$traitId")({
  component: TraitPage,
  head: () => ({
    meta: [{ title: "Trait" }],
  }),
})

/**
 * TraitPage - Detail page for a single trait
 *
 * Uses the auto-create + hydrate pattern: on first visit, creates a page
 * from the "trait" template and hydrates blocks with trait data.
 * Renders PageShell with entityType="trait" for entity-type-aware blocks.
 */
function TraitPage() {
  const { traitId } = Route.useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const creatingRef = useRef(false)

  const isOwner = !!user

  const {
    isLoading: pageLoading,
    pageExists,
    createPage,
  } = usePageEditor("trait", traitId)

  // Fetch trait data for page hydration
  const { data: trait, isLoading: traitLoading } = useQuery({
    queryKey: ["trait", traitId],
    queryFn: () => TraitsService.readTrait({ id: traitId }),
  })

  // Auto-create page with hydrated content when trait is loaded but page doesn't exist
  useEffect(() => {
    if (
      pageLoading ||
      traitLoading ||
      pageExists ||
      !trait ||
      !isOwner
    ) {
      return
    }
    if (creatingRef.current) return
    creatingRef.current = true

    createPage("trait", {
      identity: {
        name: trait.name,
        tagline: trait.description ?? "",
      },
      bio: {
        text: trait.description ?? "",
      },
    }).catch(() => {
      creatingRef.current = false
    })
  }, [
    pageLoading,
    traitLoading,
    pageExists,
    trait,
    isOwner,
    createPage,
  ])

  const isLoading = pageLoading || traitLoading

  if (isLoading) {
    return (
      <div className="flex flex-col h-full p-6 space-y-4">
        <div className="flex items-center gap-4">
          <Skeleton className="h-20 w-20 rounded-full" />
          <div className="space-y-2">
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-4 w-32" />
          </div>
        </div>
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-24 w-full" />
      </div>
    )
  }

  if (!pageExists && !isOwner) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-6">
        <div className="flex flex-col items-center gap-4 text-center max-w-md">
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-muted">
            <Sparkles className="h-10 w-10 text-muted-foreground" />
          </div>
          <h1 className="text-2xl font-bold">Page Not Found</h1>
          <p className="text-muted-foreground">
            This trait doesn't have a profile page yet.
          </p>
          <Button
            variant="outline"
            onClick={() => navigate({ to: "/traits" })}
          >
            Back to Traits
          </Button>
        </div>
      </div>
    )
  }

  return (
    <PageShell
      entityType="trait"
      entityId={traitId}
      isOwner={isOwner}
      onDelete={() => navigate({ to: "/traits" })}
    />
  )
}
