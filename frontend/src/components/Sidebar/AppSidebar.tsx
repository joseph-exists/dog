import {
  BookOpen,
  Bot,
  Briefcase,
  Home,
  MessageSquare,
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
  { icon: Briefcase, title: "Items", path: "/items" },
]

// Temporary dev items for testing old vs new room implementations
const devItems: Item[] = [
  { icon: MessageSquare, title: "Rooms (Old)", path: "/room-v2" },
]

export function AppSidebar() {
  const { user: currentUser } = useAuth()

  const items = currentUser?.is_superuser
    ? [
        ...baseItems,
        ...devItems,
        { icon: Users, title: "Admin", path: "/admin" },
      ]
    : [...baseItems, ...devItems]

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
