import { createFileRoute } from "@tanstack/react-router"
import StoryList from "@/components/Stories/StoryList/StoryList"

export const Route = createFileRoute("/_layout/stories/")({
  component: StoryList,
})
