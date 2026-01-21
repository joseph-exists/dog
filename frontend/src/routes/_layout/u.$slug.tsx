// src/routes/_layout/u.$slug.tsx
import { useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"

import { PageShell } from "@/components/Page"
import { PageService } from "@/services/pageService"

// TODO: Replace with actual service
const mockUser = {
  id: "1",
  typeId: "user",
  name: "Alice Example",
  slug: "alice",
  avatarUrl: undefined,
  tagline: "Software Engineer & Open Source Enthusiast",
  bio: "I build things with code. Currently working on distributed systems and developer tools.",
  email: "alice@example.com",
  phone: undefined,
  links: [
    {
      id: "1",
      type: "github" as const,
      url: "https://github.com/alice",
      label: "GitHub",
    },
    {
      id: "2",
      type: "twitter" as const,
      url: "https://twitter.com/alice",
      label: "@alice",
    },
    {
      id: "3",
      type: "website" as const,
      url: "https://alice.dev",
      label: "Blog",
    },
  ],
  relationships: [
    {
      id: "t1",
      typeId: "team",
      name: "Alpha Team",
      relationshipTypeId: "member",
    },
    {
      id: "a1",
      typeId: "agent",
      name: "Claude",
      avatarUrl: undefined,
      badges: ["GPT-4"],
      relationshipTypeId: "creator",
    },
  ],
  activities: [],
  images: [],
  createdAt: new Date("2024-01-15"),
  updatedAt: new Date(),
}

export const Route = createFileRoute("/_layout/u/$slug")({
  component: UserPage,
  head: () => ({
    meta: [{ title: "User Profile" }],
  }),
})

function UserPage() {
  const { slug } = Route.useParams()
  const navigate = useNavigate()

  // TODO: Replace with actual query
  // const { data: user } = useSuspenseQuery({
  //   queryKey: ["users", slug],
  //   queryFn: () => UserService.getBySlug(slug),
  // })

  const user = { ...mockUser, slug }

  const { data: layout } = useQuery({
    queryKey: ["pages", "user", slug],
    queryFn: () => PageService.getLayout("user", slug),
  })

  // TODO: Check actual ownership
  const isOwner = true

  const handleDelete = () => {
    // TODO: Implement delete
    navigate({ to: "/" })
  }

  return (
    <PageShell
      entity={user}
      isOwner={isOwner}
      blocks={layout?.layout}
      onDelete={handleDelete}
    />
  )
}
