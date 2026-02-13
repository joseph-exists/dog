/**
 * Story Player Page — Route Orchestrator
 *
 * Displays an interactive story player with debug panel.
 * Follows the orchestrator pattern: route owns state + panel registry,
 * shell owns structure + rendering.
 *
 * Theme state uses nullish coalescing for future user preference integration.
 */

import { useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { BookOpen } from "lucide-react"
import { useState } from "react"

import { StoriesService } from "@/client"
import {
  StoryShell,
  StoryPlayerPanel,
  StoryDebugPanel,
  type PanelConfig,
} from "@/components/Story"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"

export const Route = createFileRoute("/_layout/story/$storyId")({
  component: StoryPlayerPage,
  head: () => ({
    meta: [{ title: "Story Player" }],
  }),
})

function StoryPlayerPage() {
  const { storyId } = Route.useParams()
  const navigate = useNavigate()

  // Future: useUserPagePrefs("story-player") will provide saved preferences
  const savedPrefs = null as { pageTheme?: string; cardsTheme?: string } | null

  // Theme selection — nullish coalescing ready for future prefs integration
  const [pageThemeId, setPageThemeId] = useState(
    savedPrefs?.pageTheme ?? "default"
  )
  const [cardsThemeId, setCardsThemeId] = useState(
    savedPrefs?.cardsTheme ?? "default"
  )

  // Fetch story metadata for title
  const { data: story, isLoading, error } = useQuery({
    queryKey: ["stories", storyId],
    queryFn: () => StoriesService.readStory({ id: storyId }),
  })

  // Panel configurations
  const panels: PanelConfig[] = [
    {
      id: "player",
      kind: "storyPlayer",
      prominence: "primary",
      title: "Player",
      render: () => <StoryPlayerPanel />,
    },
    {
      id: "debug",
      kind: "storyDebug",
      prominence: "auxiliary",
      title: "Debug",
      render: () => <StoryDebugPanel />,
    },
  ]

  // Loading state
  if (isLoading) {
    return (
      <div className="flex flex-col h-full p-6 space-y-4">
        <Skeleton className="h-12 w-64" />
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

  // Error or not found
  if (error || !story) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-6">
        <div className="flex flex-col items-center gap-4 text-center max-w-md">
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-muted">
            <BookOpen className="h-10 w-10 text-muted-foreground" />
          </div>
          <h1 className="text-2xl font-bold">Story Not Found</h1>
          <p className="text-muted-foreground">
            This story doesn't exist or you don't have access to it.
          </p>
          <Button
            variant="outline"
            onClick={() => navigate({ to: "/story" })}
          >
            Back to Library
          </Button>
        </div>
      </div>
    )
  }

  return (
    <StoryShell
      storyId={storyId}
      title={story.title}
      type="play"
      canEdit={true} // TODO: check story.owner_id against current user
      panels={panels}
      pageThemeId={pageThemeId}
      cardsThemeId={cardsThemeId}
      onPageThemeChange={setPageThemeId}
      onCardsThemeChange={setCardsThemeId}
    />
  )
}
