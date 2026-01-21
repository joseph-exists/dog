/**
 * Legacy Room V2 Route - Redirects to unified route
 * @deprecated Use /r/:roomId instead
 */

import { createFileRoute, redirect } from "@tanstack/react-router"

export const Route = createFileRoute("/_layout/room-v2/$roomId")({
  beforeLoad: ({ params }) => {
    throw redirect({
      to: "/r/$roomId",
      params: { roomId: params.roomId },
      replace: true,
    })
  },
  component: () => null,
})
