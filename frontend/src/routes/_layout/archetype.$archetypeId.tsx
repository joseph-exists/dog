// src/routes/_layout/archetype.$archetypeId.tsx

import { useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { Crown } from "lucide-react"
import { useEffect, useRef } from "react"

import { ArchetypesService } from "@/client"
import { PageShell } from "@/components/Page"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import useAuth from "@/hooks/useAuth"
import { usePageEditor } from "@/hooks/usePageEditor"

export const Route = createFileRoute("/_layout/archetype/$archetypeId")({
  component: ArchetypePage,
  head: () => ({
    meta: [{ title: "Archetype" }],
  }),
})

/**
 * ArchetypePage - Detail page for a single archetype
 *
 * Uses the auto-create + hydrate pattern: on first visit, creates a page
 * from the "archetype" template and hydrates blocks with archetype data.
 * Renders PageShell with entityType="archetype" for entity-type-aware blocks.
 */
function ArchetypePage() {
  const { archetypeId } = Route.useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const creatingRef = useRef(false)

  // Any authenticated user can edit archetype pages
  const isOwner = !!user

  const {
    isLoading: pageLoading,
    pageExists,
    createPage,
  } = usePageEditor("archetype", archetypeId)

  // Fetch archetype data for page hydration
  const { data: archetype, isLoading: archetypeLoading } = useQuery({
    queryKey: ["archetype", archetypeId],
    queryFn: () => ArchetypesService.readArchetype({ id: archetypeId }),
  })

  // Auto-create page with hydrated content when archetype is loaded but page doesn't exist
  useEffect(() => {
    if (
      pageLoading ||
      archetypeLoading ||
      pageExists ||
      !archetype ||
      !isOwner
    ) {
      return
    }
    if (creatingRef.current) return
    creatingRef.current = true

    createPage("archetype", {
      identity: {
        name: archetype.name,
        tagline: archetype.description ?? "",
      },
      bio: {
        text: archetype.description ?? "",
      },
    }).catch(() => {
      creatingRef.current = false
    })
  }, [
    pageLoading,
    archetypeLoading,
    pageExists,
    archetype,
    isOwner,
    createPage,
  ])

  const isLoading = pageLoading || archetypeLoading

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

  // Non-owner viewing an archetype with no page yet
  if (!pageExists && !isOwner) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-6">
        <div className="flex flex-col items-center gap-4 text-center max-w-md">
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-muted">
            <Crown className="h-10 w-10 text-muted-foreground" />
          </div>
          <h1 className="text-2xl font-bold">Page Not Found</h1>
          <p className="text-muted-foreground">
            This archetype doesn't have a profile page yet.
          </p>
          <Button
            variant="outline"
            onClick={() => navigate({ to: "/archetypes" })}
          >
            Back to Archetypes
          </Button>
        </div>
      </div>
    )
  }

  return (
    <PageShell
      entityType="archetype"
      entityId={archetypeId}
      isOwner={isOwner}
      onDelete={() => navigate({ to: "/archetypes" })}
    />
  )
}
