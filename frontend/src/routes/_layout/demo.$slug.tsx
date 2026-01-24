import { createFileRoute } from "@tanstack/react-router"
import { DemoPage } from "@/components/Demo/DemoPage"
import { getDemoConfig } from "@/config/demos"

export const Route = createFileRoute("/_layout/demo/$slug")({
  component: DemoRoute,
})

function DemoRoute() {
  const { slug } = Route.useParams()
  const config = getDemoConfig(slug)

  if (!config) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-muted-foreground">
          Demo &ldquo;{slug}&rdquo; not found.
        </p>
      </div>
    )
  }

  return <DemoPage config={config} />
}
