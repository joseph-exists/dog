/**
 * StoryGridPanel
 *
 * Primary panel for the story listing page. Renders the story card collection
 * in a responsive grid.
 *
 * Owns its own data query (useSuspenseQuery). Wrapped in PanelContainer
 * for consistent header/scroll/footer structure.
 *
 * Mirrors AgentsGridPanel pattern for cascade consistency.
 */

import {
  useMutation,
  useQueryClient,
  useSuspenseQuery,
} from "@tanstack/react-query"
import { BookOpen, Loader2Icon, Plus, TrashIcon } from "lucide-react"
import { Suspense, useState } from "react"

import type { ApiError } from "@/client/core/ApiError"
import { StoriesService } from "@/client/sdk.gen"
import type { StoryPublic } from "@/client/types.gen"
import { PanelContainer } from "@/components/Page/primitives"
import AddRoom from "@/components/Room/Dialogs/AddRoom"
import StoryDetailDialog from "@/components/Story/Dialogs/StoryDetailDialog"
import CreateStoryModal from "@/components/Story/Display/CreateStoryModal"
import StoryCard from "@/components/Story/StoryList/StoryCard"

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
import { Skeleton } from "@/components/ui/skeleton"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"

// ── Query ─────────────────────────────────────────────────────────────────

function getStoriesQueryOptions() {
  return {
    queryFn: () => StoriesService.readStories({}),
    queryKey: ["stories"],
  }
}

// ── Loading States ────────────────────────────────────────────────────────

function StoryCardSkeleton() {
  return (
    <Card className="h-96">
      <CardHeader className="flex flex-row items-start gap-4">
        <div className="flex-1 space-y-2">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-4 w-48" />
        </div>
      </CardHeader>
      <CardContent>
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4 mt-2" />
      </CardContent>
    </Card>
  )
}

function PendingStories() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 p-4">
      <StoryCardSkeleton />
      <StoryCardSkeleton />
      <StoryCardSkeleton />
    </div>
  )
}

// ── Delete Action ─────────────────────────────────────────────────────────

function DeleteStoryButton({ story }: { story: StoryPublic }) {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: () => StoriesService.deleteStory({ id: story.id }),
    onSuccess: () => {
      showSuccessToast(`Story "${story.title}" deleted successfully.`)
      setIsOpen(false)
    },
    onError: (err: ApiError) => {
      const message =
        (err.body as { detail?: string })?.detail || "Failed to delete story"
      showErrorToast(message)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["stories"] })
    },
  })

  return (
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
          <AlertDialogTitle>Delete Story</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to delete &ldquo;{story.title}&rdquo;? This
            action cannot be undone.
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

// ── Card Item (with href + actions) ───────────────────────────────────────

function StoryCardItem({ story }: { story: StoryPublic }) {
  return (
    <StoryCard
      story={story}
      href={`/story/${story.id}`}
      showLinkedRooms
      showVersionInfo
      action={
        <div className="flex items-center gap-2">
          <StoryDetailDialog storyId={story.id} className="size-7" />
          {story.is_published && (
            <AddRoom
              defaultStoryId={story.id}
              trigger={
                <Button size="sm" variant="outline">
                  <Plus className="mr-1 h-4 w-4" />
                  Room
                </Button>
              }
            />
          )}
          <DeleteStoryButton story={story} />
        </div>
      }
    />
  )
}

// ── Grid Content ──────────────────────────────────────────────────────────

function StoryGridContent() {
  const { data } = useSuspenseQuery(getStoriesQueryOptions())
  const allStories: StoryPublic[] = data.data || []

  // Split by published status
  const publishedStories = allStories.filter((s) => s.is_published)
  const draftStories = allStories.filter((s) => !s.is_published)

  if (allStories.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-muted p-4 mb-4">
          <BookOpen className="size-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">No stories yet</h3>
        <p className="text-muted-foreground mb-4">
          Create your first story to get started.
        </p>
        <CreateStoryModal />
      </div>
    )
  }

  return (
    <div className="space-y-8 p-4">
      {publishedStories.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-4">Published Stories</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {publishedStories.map((story) => (
              <StoryCardItem key={story.id} story={story} />
            ))}
          </div>
        </section>
      )}

      {draftStories.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-4 text-muted-foreground">
            Drafts
          </h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {draftStories.map((story) => (
              <StoryCardItem key={story.id} story={story} />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}

// ── Panel Export ───────────────────────────────────────────────────────────

export function StoryGridPanel() {
  return (
    <PanelContainer title="Library" scrollable>
      <Suspense fallback={<PendingStories />}>
        <StoryGridContent />
      </Suspense>
    </PanelContainer>
  )
}
