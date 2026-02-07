import { createFileRoute } from "@tanstack/react-router"
import PresentationDemo from "@/components/Agents/Presentation/PresentationDemo"

export const Route = createFileRoute("/_layout/presentation-poc")({
  component: PresentationDemo,
})
