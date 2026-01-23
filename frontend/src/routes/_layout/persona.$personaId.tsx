// src/routes/_layout/persona.$personaId.tsx

import { useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { Smile } from "lucide-react"
import { useEffect, useRef } from "react"

import { PersonasService } from "@/client"
import { PageShell } from "@/components/Page"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import useAuth from "@/hooks/useAuth"
import { usePageEditor } from "@/hooks/usePageEditor"

export const Route = createFileRoute("/_layout/persona/$personaId")({
  component: PersonaPage,
  head: () => ({
    meta: [{ title: "Persona" }],
  }),
})

function PersonaPage() {
  const { personaId } = Route.useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const creatingRef = useRef(false)

  // Any authenticated user can edit persona pages
  const isOwner = !!user

  const {
    isLoading: pageLoading,
    pageExists,
    createPage,
  } = usePageEditor("persona", personaId)

  // Fetch persona data for page hydration
  const { data: persona, isLoading: personaLoading } = useQuery({
    queryKey: ["persona", personaId],
    queryFn: () => PersonasService.readPersona({ id: personaId }),
  })

  // Auto-create page with hydrated content when persona is loaded but page doesn't exist
  useEffect(() => {
    if (pageLoading || personaLoading || pageExists || !persona || !isOwner) {
      return
    }
    if (creatingRef.current) return
    creatingRef.current = true

    createPage("persona", {
      identity: {
        name: persona.name,
        tagline: persona.description ?? "",
      },
      bio: {
        text: persona.long_description ?? persona.description ?? "",
      },
      domains: {
        generalDomain: persona.general_domain ?? "",
        specificDomain: persona.specific_domain ?? "",
        generalDomainHigh: persona.general_domain_high ?? "",
        specificDomainHigh: persona.specific_domain_high ?? "",
      },
    }).catch(() => {
      creatingRef.current = false
    })
  }, [pageLoading, personaLoading, pageExists, persona, isOwner, createPage])

  const isLoading = pageLoading || personaLoading

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

  // Non-owner viewing a persona with no page yet
  if (!pageExists && !isOwner) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-6">
        <div className="flex flex-col items-center gap-4 text-center max-w-md">
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-muted">
            <Smile className="h-10 w-10 text-muted-foreground" />
          </div>
          <h1 className="text-2xl font-bold">Page Not Found</h1>
          <p className="text-muted-foreground">
            This persona doesn't have a profile page yet.
          </p>
          <Button
            variant="outline"
            onClick={() => navigate({ to: "/personas" })}
          >
            Back to Personas
          </Button>
        </div>
      </div>
    )
  }

  return (
    <PageShell
      entityType="persona"
      entityId={personaId}
      isOwner={isOwner}
      onDelete={() => navigate({ to: "/personas" })}
    />
  )
}
