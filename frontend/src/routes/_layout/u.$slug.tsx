// src/routes/_layout/u.$slug.tsx

import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { Plus, User } from "lucide-react"
import { useState } from "react"

import { CreatePageDialog, PageShell } from "@/components/Page"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import useAuth from "@/hooks/useAuth"
import { useUserPageViewModel } from "@/hooks/useUserPageViewModel"

export const Route = createFileRoute("/_layout/u/$slug")({
  component: UserPage,
  head: ({ params }) => ({
    meta: [{ title: `${params.slug}'s Profile` }],
  }),
})

function UserPage() {
  const { slug } = Route.useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [isCreating, setIsCreating] = useState(false)

  // For now, treat slug as userId directly
  // TODO: review adding slug-to-userId resolution service
  // TODO: review adding coolname/regenerate for slug - if UserID is immutable, maybe slug can be ephemeral -
  // TODO: and maybe slug ephemerality presents affordances for privacy/persona system
  const userId = slug

  // Determine ownership
  const isOwner = user?.id === userId

  const { isLoading, pageExists, createPage, viewModel } =
    useUserPageViewModel(slug)

  const handleCreatePage = async (templateId: string) => {
    setIsCreating(true)
    try {
      await createPage(templateId, {
        identity: {
          name: user?.full_name || user?.email || slug,
          tagline: "A work-centered user surface shaped through personas.",
        },
        bio: {
          text:
            "This page organizes work, personas, audience views, and relations without collapsing them into a single static identity.",
        },
      })
      setShowCreateDialog(false)
    } finally {
      setIsCreating(false)
    }
  }

  const handleDelete = () => {
    // TODO: Implement page deletion
    navigate({ to: "/" })
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="flex flex-col h-full p-6 space-y-4">
        <div className="flex items-center gap-4">
          <Skeleton className="h-24 w-24 rounded-full" />
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

  // No page exists
  if (!pageExists) {
    // Owner can create a page
    if (isOwner) {
      return (
        <div className="flex flex-col items-center justify-center h-full p-6">
          <div className="flex flex-col items-center gap-4 text-center max-w-md">
            <div className="flex h-20 w-20 items-center justify-center rounded-full bg-muted">
              <User className="h-10 w-10 text-muted-foreground" />
            </div>
            <h1 className="text-2xl font-bold">Create Your Page</h1>
            <p className="text-muted-foreground">
              You don't have a profile page yet. Create one to share your
              information with others.
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
            entityType="user"
          />
        </div>
      )
    }

    // Non-owner sees not found
    return (
      <div className="flex flex-col items-center justify-center h-full p-6">
        <div className="flex flex-col items-center gap-4 text-center max-w-md">
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-muted">
            <User className="h-10 w-10 text-muted-foreground" />
          </div>
          <h1 className="text-2xl font-bold">Page Not Found</h1>
          <p className="text-muted-foreground">
            This user hasn't created their profile page yet.
          </p>
          <Button variant="outline" onClick={() => navigate({ to: "/" })}>
            Go Home
          </Button>
        </div>
      </div>
    )
  }

  // Page exists - render PageShell
  return (
    <PageShell
      entityType="user"
      entityId={userId}
      isOwner={isOwner}
      onDelete={handleDelete}
      entityNameOverride={
        isOwner ? user?.full_name || user?.email || slug : undefined
      }
      userPageViewModel={viewModel}
    />
  )
}
