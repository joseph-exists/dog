/**
 * Legacy Room Route - Redirects to unified route
 * @deprecated Use /r/:roomId instead
 */

import { createFileRoute, redirect } from "@tanstack/react-router"

export const Route = createFileRoute("/_layout/room/$roomId")({
  beforeLoad: ({ params }) => {
    throw redirect({
      to: "/r/$roomId",
      params: { roomId: params.roomId },
      replace: true,
    })
  },
  component: () => null,
})
