import {
  createFileRoute,
  Outlet,
  redirect,
  useMatches,
} from "@tanstack/react-router"

import { Footer } from "@/components/Common/Footer"
import AppSidebar from "@/components/Sidebar/AppSidebar"
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
  "/": "Dashboard",
  "/stories": "Stories",
  "/rooms": "Rooms",
  "/agents": "Agents",
  "/items": "Items",
  "/admin": "Admin",
  "/settings": "Settings",
}

function Layout() {
  const matches = useMatches()
  const currentPath = matches[matches.length - 1]?.pathname || "/"

  // Get title from exact match or find parent route
  const pageTitle =
    routeTitles[currentPath] ||
    Object.entries(routeTitles).find(
      ([path]) => currentPath.startsWith(path) && path !== "/",
    )?.[1] ||
    "Dashboard"

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <header className="sticky top-0 z-10 flex h-16 shrink-0 items-center gap-2 border-b bg-background px-4">
          <SidebarTrigger className="-ml-1 text-muted-foreground" />
          <Separator orientation="vertical" className="mx-2 h-4" />
          <h1 className="text-base font-medium">{pageTitle}</h1>
        </header>
        <main className="flex-1 p-6 md:p-8">
          <div className="mx-auto max-w-7xl">
            <Outlet />
          </div>
        </main>
        <Footer />
      </SidebarInset>
    </SidebarProvider>
  )
}

export default Layout
