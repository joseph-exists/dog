// src/routes/_layout/quality.$qualityId.tsx

import { useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { Gem } from "lucide-react"
import { useEffect, useRef } from "react"

import { QualitiesService } from "@/client"
import { PageShell } from "@/components/Page"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import useAuth from "@/hooks/useAuth"
import { usePageEditor } from "@/hooks/usePageEditor"

export const Route = createFileRoute("/_layout/quality/$qualityId")({
  component: QualityPage,
  head: () => ({
    meta: [{ title: "Quality" }],
  }),
})

/**
 * QualityPage - Detail page for a single quality
 *
 * Uses the auto-create + hydrate pattern: on first visit, creates a page
 * from the "quality" template and hydrates blocks with quality data.
 * Renders PageShell with entityType="quality" for entity-type-aware blocks.
 */
function QualityPage() {
  const { qualityId } = Route.useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const creatingRef = useRef(false)

  const isOwner = !!user

  const {
    isLoading: pageLoading,
    pageExists,
    createPage,
  } = usePageEditor("quality", qualityId)

  // Fetch quality data for page hydration
  const { data: quality, isLoading: qualityLoading } = useQuery({
    queryKey: ["quality", qualityId],
    queryFn: () => QualitiesService.readQuality({ id: qualityId }),
  })

  // Auto-create page with hydrated content when quality is loaded but page doesn't exist
  useEffect(() => {
    if (
      pageLoading ||
      qualityLoading ||
      pageExists ||
      !quality ||
      !isOwner
    ) {
      return
    }
    if (creatingRef.current) return
    creatingRef.current = true

    createPage("quality", {
      identity: {
        name: quality.name,
        tagline: quality.description ?? "",
      },
      bio: {
        text: quality.description ?? "",
      },
    }).catch(() => {
      creatingRef.current = false
    })
  }, [
    pageLoading,
    qualityLoading,
    pageExists,
    quality,
    isOwner,
    createPage,
  ])

  const isLoading = pageLoading || qualityLoading

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
            <Gem className="h-10 w-10 text-muted-foreground" />
          </div>
          <h1 className="text-2xl font-bold">Page Not Found</h1>
          <p className="text-muted-foreground">
            This quality doesn't have a profile page yet.
          </p>
          <Button
            variant="outline"
            onClick={() => navigate({ to: "/qualities" })}
          >
            Back to Qualities
          </Button>
        </div>
      </div>
    )
  }

  return (
    <PageShell
      entityType="quality"
      entityId={qualityId}
      isOwner={isOwner}
      onDelete={() => navigate({ to: "/qualities" })}
    />
  )
}
