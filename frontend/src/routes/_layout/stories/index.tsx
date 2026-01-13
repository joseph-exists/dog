import StoryList from "@/components/Stories/StoryList/StoryList"
import { createFileRoute } from "@tanstack/react-router"

export const Route = createFileRoute("/_layout/stories/")({
  component: StoryList,
})
