import StoryEditor from "@/components/Stories/StoryEditor/StoryEditor"
import { createFileRoute } from "@tanstack/react-router"

export const Route = createFileRoute("/_layout/stories/$storyId/edit")({
  component: StoryEditorPage,
})

function StoryEditorPage() {
  const { storyId } = Route.useParams()
  return <StoryEditor storyId={storyId} />
}
