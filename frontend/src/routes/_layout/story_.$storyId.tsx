/**
 * Story Player Page — Route Orchestrator
 *
 * Displays an interactive story player with debug panel.
 * Follows the orchestrator pattern: route owns state + panel registry,
 * shell owns structure + rendering.
 *
 * Theme state uses backend bindings via useUserThemeBindings hook.
 */

import { useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { BookOpen } from "lucide-react"

import { StoriesService } from "@/client"
import {
  type PanelConfig,
  StoryDebugPanel,
  StoryPlayerPanel,
  StoryShell,
} from "@/components/Story"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { usePageThemes } from "@/hooks/useThemeBinding"
import {
  useAvailableThemes,
  useUserThemeBindings,
} from "@/hooks/useThemeRegistry"

export const Route = createFileRoute("/_layout/story_/$storyId")({
  component: StoryPlayerPage,
  head: () => ({
    meta: [{ title: "Story Player" }],
  }),
})

function StoryPlayerPage() {
  const { storyId } = Route.useParams()
  const navigate = useNavigate()

  // Context path for this specific story player page
  const contextPath = [`page:story-player`, `story:${storyId}`]

  // Resolve current themes
  const { themes, isLoading: isResolvingThemes } = usePageThemes(contextPath)

  // User binding management
  const { setBinding } = useUserThemeBindings("page:story-player")

  // Available themes for pickers
  const { themes: availablePageThemes } = useAvailableThemes("page")
  const { themes: availableCardThemes } = useAvailableThemes("card")

  // Theme change handlers
  const handlePageThemeChange = (themeId: string) => {
    setBinding({
      contextKey: "page:story-player",
      slot: "page",
      themeId,
    })
  }

  const handleCardsThemeChange = (themeId: string) => {
    setBinding({
      contextKey: "page:story-player",
      slot: "cards",
      themeId,
    })
  }

  // Fetch story metadata for title
  const {
    data: story,
    isLoading,
    error,
  } = useQuery({
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
          <Button variant="outline" onClick={() => navigate({ to: "/story" })}>
            Back to Library
          </Button>
        </div>
      </div>
    )
  }

  // Extract resolved theme data
  const pageTheme = themes.page?.theme ?? null
  const cardsTheme = themes.cards?.theme ?? null

  return (
    <StoryShell
      storyId={storyId}
      title={story.title}
      type="play"
      canEdit={true} // TODO: check story.owner_id against current user
      panels={panels}
      pageTheme={pageTheme}
      cardsTheme={cardsTheme}
      availablePageThemes={availablePageThemes}
      availableCardThemes={availableCardThemes}
      onPageThemeChange={handlePageThemeChange}
      onCardsThemeChange={handleCardsThemeChange}
      isLoadingThemes={isResolvingThemes}
    />
  )
}
