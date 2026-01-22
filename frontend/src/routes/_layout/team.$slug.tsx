// src/routes/_layout/team.$slug.tsx
import { createFileRoute, useNavigate } from "@tanstack/react-router"

import { PageShell } from "@/components/Page"

// TODO: Replace with actual service to fetch team ID from slug
const mockTeamIdBySlug: Record<string, string> = {
  alpha: "team-alpha",
  beta: "team-beta",
}

export const Route = createFileRoute("/_layout/team/$slug")({
  component: TeamPage,
  head: () => ({
    meta: [{ title: "Team Profile" }],
  }),
})

function TeamPage() {
  const { slug } = Route.useParams()
  const navigate = useNavigate()

  // TODO: Replace with actual query to get team ID from slug
  const teamId = mockTeamIdBySlug[slug] ?? slug

  // TODO: Check actual ownership
  const isOwner = true

  const handleDelete = () => {
    navigate({ to: "/" })
  }

  return (
    <PageShell
      entityType="team"
      entityId={teamId}
      isOwner={isOwner}
      onDelete={handleDelete}
    />
  )
}
