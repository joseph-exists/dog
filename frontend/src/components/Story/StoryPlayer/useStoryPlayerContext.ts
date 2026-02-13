/**
 * useStoryPlayerContext
 *
 * Hook to consume StoryPlayerContext with proper error boundary.
 *
 * USAGE: Call from any component inside StoryPlayerProvider.
 * Will throw if used outside provider (fail-fast for debugging).
 */
import { useContext } from "react"
import {
  StoryPlayerContext,
  type StoryPlayerContextValue,
} from "./StoryPlayerProvider"

export function useStoryPlayerContext(): StoryPlayerContextValue {
  const context = useContext(StoryPlayerContext)

  if (!context) {
    throw new Error(
      "useStoryPlayerContext must be used within a StoryPlayerProvider. " +
        "Ensure StoryPlayerProvider wraps your component tree."
    )
  }

  return context
}
