// src/routes/_layout/team.$slug.tsx
import { useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"

import { PageShell } from "@/components/Page"
import { PageService } from "@/services/pageService"

// TODO: Replace with actual service
const mockTeam = {
  id: "team-alpha",
  typeId: "team",
  name: "Alpha Team",
  slug: "alpha",
  avatarUrl: undefined,
  tagline: "Building the future of collaboration",
  bio: "We are a cross-functional team focused on creating tools that help people work together more effectively.",
  email: "alpha@example.com",
  phone: undefined,
  links: [
    {
      id: "1",
      type: "website" as const,
      url: "https://alpha.team",
      label: "Website",
    },
  ],
  relationships: [
    {
      id: "u1",
      typeId: "user",
      name: "Alice",
      relationshipTypeId: "has_member",
      badges: ["Lead"],
    },
    { id: "u2", typeId: "user", name: "Bob", relationshipTypeId: "has_member" },
    {
      id: "u3",
      typeId: "user",
      name: "Charlie",
      relationshipTypeId: "has_member",
    },
  ],
  activities: [],
  images: [],
  createdAt: new Date("2024-03-01"),
  updatedAt: new Date(),
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

  // TODO: Replace with actual query
  const team = { ...mockTeam, slug }

  const { data: layout } = useQuery({
    queryKey: ["pages", "team", slug],
    queryFn: () => PageService.getLayout("team", slug),
  })

  // TODO: Check actual ownership
  const isOwner = true

  const handleDelete = () => {
    navigate({ to: "/" })
  }

  return (
    <PageShell
      entity={team}
      isOwner={isOwner}
      blocks={layout?.layout}
      onDelete={handleDelete}
    />
  )
}
