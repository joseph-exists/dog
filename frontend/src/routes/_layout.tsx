import {
  createFileRoute,
  Outlet,
  redirect,
  useMatches,
} from "@tanstack/react-router"
import { useEffect, useState } from "react"

import { Footer } from "@/components/Common/Footer"
import { AppSidebar } from "@/components/Common/Sidebar"
import { Separator } from "@/components/ui/separator"
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import { isLoggedIn } from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout")({
  component: Layout,
  beforeLoad: async () => {
    if (!isLoggedIn()) {
      throw redirect({
        to: "/login",
      })
    }
  },
})

/** Map route paths to display titles */
const routeTitles: Record<string, string> = {
  "/": "Das Bord",
  "/stories": "Stories Authoring",
  "/rooms": "Rooms Looking At",
  "/agents": "Agents Reviewing",
  "/repos": "Repositories",
  "/story": "Story Reading",
  "/personas": "Personas Managing",
  "/persona": "Persona",
  "/items": "Items",
  "/u": "Profile",
  "/admin": "Admin",
  "/settings": "Settings",
  "/demos": "Demos Pagings",
  "/demo-builder": "DEMOS BILDERDAMMERUNG",
  "/prompt-builder": "PARTI PROMPTINGS",
  "/content-renderer-demo": "Content Demo",
}

/** Routes that need full-bleed layout (no max-width or padding) */
const fullBleedRoutes = [
  "/agents",
  "/repos",
  "/story",
  "/r/",
  "/room/",
  "/room-v2/",
  "/u/",
  "/persona/",
  "/demo/",
]

function Layout() {
  const matches = useMatches()
  const currentPath = matches[matches.length - 1]?.pathname || "/"
  const [sidebarOpen, setSidebarOpen] = useState(true)

  // Get title from exact match or find parent route
  const pageTitle =
    routeTitles[currentPath] ||
    Object.entries(routeTitles).find(
      ([path]) => currentPath.startsWith(path) && path !== "/",
    )?.[1] ||
    "Flamingo"

  // Check if this route needs full-bleed layout
  const isFullBleed = fullBleedRoutes.some((route) =>
    currentPath.startsWith(route),
  )

  // Demo pages should open with the app sidebar minimized to keep focus on content.
  useEffect(() => {
    if (currentPath.startsWith("/demo/")) {
      setSidebarOpen(false)
    }
  }, [currentPath])

  return (
    <SidebarProvider open={sidebarOpen} onOpenChange={setSidebarOpen}>
      <AppSidebar />
      <SidebarInset className="flex flex-col h-screen">
        {isFullBleed ? (
          <main className="flex-1 min-h-0 overflow-hidden">
            <Outlet />
          </main>
        ) : (
          <>
            <header className="sticky top-0 z-10 flex h-16 shrink-0 items-center gap-2 border-b bg-background px-4">
              <SidebarTrigger className="-ml-1 text-muted-foreground" />
              <Separator orientation="vertical" className="mx-2 h-4" />
              <h1 className="text-base font-medium">{pageTitle}</h1>
            </header>
            <main className="flex-1 p-6 md:p-8 overflow-auto">
              <div className="mx-auto max-w-7xl">
                <Outlet />
              </div>
            </main>
            <Footer />
          </>
        )}
      </SidebarInset>
    </SidebarProvider>
  )
}

export default Layout
