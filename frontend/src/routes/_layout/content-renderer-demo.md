import { createFileRoute } from "@tanstack/react-router"
import { ContentRendererDemo } from "@/components/Demo/ContentRendererDemo"

export const Route = createFileRoute("/_layout/content-renderer-demo/")({
  component: ContentRendererDemo,
})