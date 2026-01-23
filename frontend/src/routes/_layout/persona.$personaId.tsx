// src/routes/_layout/persona.$personaId.tsx

import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { Plus, Smile } from "lucide-react"
import { useState } from "react"

import { CreatePageDialog, PageShell } from "@/components/Page"
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
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [isCreating, setIsCreating] = useState(false)

  // Any authenticated user can edit persona pages
  const isOwner = !!user

  const { isLoading, pageExists, createPage } = usePageEditor(
    "persona",
    personaId,
  )

  const handleCreatePage = async (templateId: string) => {
    setIsCreating(true)
    try {
      await createPage(templateId)
      setShowCreateDialog(false)
    } finally {
      setIsCreating(false)
    }
  }

  const handleDelete = () => {
    navigate({ to: "/personas" })
  }

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

  if (!pageExists) {
    if (isOwner) {
      return (
        <div className="flex flex-col items-center justify-center h-full p-6">
          <div className="flex flex-col items-center gap-4 text-center max-w-md">
            <div className="flex h-20 w-20 items-center justify-center rounded-full bg-muted">
              <Smile className="h-10 w-10 text-muted-foreground" />
            </div>
            <h1 className="text-2xl font-bold">Create Persona Page</h1>
            <p className="text-muted-foreground">
              This persona doesn't have a profile page yet. Create one to
              display its identity, domains, and traits.
            </p>
            <Button onClick={() => setShowCreateDialog(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Create Page
            </Button>
          </div>

          <CreatePageDialog
            open={showCreateDialog}
            onOpenChange={setShowCreateDialog}
            onCreatePage={handleCreatePage}
            isCreating={isCreating}
            entityType="persona"
          />
        </div>
      )
    }

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
      onDelete={handleDelete}
    />
  )
}
