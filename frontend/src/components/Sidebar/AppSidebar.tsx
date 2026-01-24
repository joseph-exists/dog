import {
  BookOpen,
  Bot,
  Briefcase,
  Crown,
  Home,
  MessageSquare,
  Smile,
  User2,
  Users,
} from "lucide-react"

import { SidebarAppearance } from "@/components/Common/Appearance"
import { Logo } from "@/components/Common/Logo"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
} from "@/components/ui/sidebar"
import useAuth from "@/hooks/useAuth"
import { type Item, Main } from "./Main"
import { User } from "./User"

const baseItems: Item[] = [
  { icon: Home, title: "Dashboard", path: "/" },
  { icon: BookOpen, title: "Stories", path: "/stories" },
  { icon: MessageSquare, title: "Rooms", path: "/rooms" },
  { icon: Bot, title: "Agents", path: "/agents" },
  { icon: Smile, title: "Personas", path: "/personas" },
  { icon: Crown, title: "Archetypes", path: "/archetypes" },
  { icon: Briefcase, title: "Items", path: "/items" },
  { icon: BookOpen, title: "debug-chatster", path: "/chatster" },
]

export function AppSidebar() {
  const { user: currentUser } = useAuth()

  // Build items list based on user state
  const items: Item[] = [...baseItems]

  // Add "My Page" only for authenticated users
  if (currentUser?.id) {
    items.push({ icon: User2, title: "My Page", path: `/u/${currentUser.id}` })
  }

  // Add Admin for superusers
  if (currentUser?.is_superuser) {
    items.push({ icon: Users, title: "Admin", path: "/admin" })
  }

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="px-4 py-6 group-data-[collapsible=icon]:px-0 group-data-[collapsible=icon]:items-center">
        <Logo variant="responsive" />
      </SidebarHeader>
      <SidebarContent>
        <Main items={items} />
      </SidebarContent>
      <SidebarFooter>
        <SidebarAppearance />
        <User user={currentUser} />
      </SidebarFooter>
    </Sidebar>
  )
}

export default AppSidebar
