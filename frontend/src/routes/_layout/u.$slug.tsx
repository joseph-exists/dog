import { createFileRoute, Outlet } from "@tanstack/react-router"

export const Route = createFileRoute("/_layout/u/$slug")({
  component: UserPageLayoutRoute,
})

function UserPageLayoutRoute() {
  return <Outlet />
}
