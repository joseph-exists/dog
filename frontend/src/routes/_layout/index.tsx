import { createFileRoute } from "@tanstack/react-router"
import useAuth from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
  head: () => ({
    meta: [
      {
        title: "silly beans",
      },
    ],
  }),
})

function Dashboard() {
  const { user: currentUser } = useAuth()

  return (
    <div>
      <div>
        <h1 className="text-2xl truncate max-w-sm">
          Hi, {currentUser?.full_name || currentUser?.email} 👋
        </h1>
        <p className="text-muted-foreground"></p>
        <div>
          <h1 className="text-2xl truncate max-w-sm">
            Fast and Easy: Talk to a System Agent Still Fast, Still Easy: Roll
            your own Agent Even Faster and Easier: Provider/Model Selection
          </h1>
          <p className="text-muted-foreground" />
        </div>
      </div>
    </div>
  )
}
