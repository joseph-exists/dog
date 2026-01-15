/**
 * StoryList - Main container for displaying user's stories
 *
 * Features:
 * - Responsive grid layout (1-3 columns based on viewport)
 * - Empty state when no stories exist
 * - Loading and error states
 * - "Create Story" button in header
 */

import { AlertCircle, BookOpen, Loader2 } from "lucide-react"

import { useStories } from "@/hooks/stories/useStories"
import CreateStoryModal from "./CreateStoryModal"
import StoryCard from "./StoryCard"

const StoryList = () => {
  const { data, isLoading, error } = useStories()

  const stories = data?.data ?? []

  // Loading state
  if (isLoading) {
    return (
      <div className="container mx-auto max-w-7xl py-8">
        <div className="flex min-h-[400px] items-center justify-center">
          <Loader2 className="text-muted-foreground h-8 w-8 animate-spin" />
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="container mx-auto max-w-7xl py-8">
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="bg-destructive/10 mb-4 rounded-full p-4">
            <AlertCircle className="text-destructive h-8 w-8" />
          </div>
          <h3 className="text-lg font-semibold">Error Loading Stories</h3>
          <p className="text-muted-foreground">
            {error.message || "Something went wrong. Please try again."}
          </p>
        </div>
      </div>
    )
  }

  // Empty state
  if (stories.length === 0) {
    return (
      <div className="container mx-auto max-w-7xl py-8">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-bold">My Stories</h1>
          <CreateStoryModal />
        </div>
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="bg-muted mb-4 rounded-full p-4">
            <BookOpen className="text-muted-foreground h-8 w-8" />
          </div>
          <h3 className="text-lg font-semibold">No Stories Yet</h3>
          <p className="text-muted-foreground max-w-md">
            Create your first interactive story and start crafting branching
            adventures!
          </p>
        </div>
      </div>
    )
  }

  // Stories grid
  return (
    <div className="container mx-auto max-w-7xl py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">My Stories</h1>
        <CreateStoryModal />
      </div>
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        {stories.map((story) => (
          <StoryCard key={story.id} story={story} />
        ))}
      </div>
    </div>
  )
}

export default StoryList
