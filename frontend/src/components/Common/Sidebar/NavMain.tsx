// src/components/Common/Sidebar/NavMain.tsx

import { Link as RouterLink, useRouterState } from "@tanstack/react-router"

import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar"

import type { NavSection } from "./types"

// ============================================================================
// NavMain - Primary Navigation Renderer
// ============================================================================
//
// RESPONSIBILITIES:
//   - Renders a single NavSection as a list of router-linked menu items
//   - Determines active state by comparing item.path to current route
//   - Handles mobile sidebar close on navigation
//
// DOES NOT:
//   - Decide which items to show (that's AppSidebar's job)
//   - Fetch any data
//   - Know about authentication
//
// STYLING:
//   - Uses shadcn Sidebar primitives for consistent look
//   - Active state handled via SidebarMenuButton's isActive prop
// ============================================================================

interface NavMainProps {
  /** Section to render */
  section: NavSection
}

export function NavMain({ section }: NavMainProps) {
  const { isMobile, setOpenMobile } = useSidebar()
  const router = useRouterState()
  const currentPath = router.location.pathname

  /** Close mobile sidebar after navigation */
  const handleClick = () => {
    if (isMobile) {
      setOpenMobile(false)
    }
  }

  return (
    <SidebarGroup>
      {section.label && <SidebarGroupLabel>{section.label}</SidebarGroupLabel>}
      <SidebarGroupContent>
        <SidebarMenu>
          {section.items.map((item) => {
            // Exact match for root, startsWith for nested routes
            const isActive =
              item.path === "/"
                ? currentPath === "/"
                : currentPath.startsWith(item.path)

            return (
              <SidebarMenuItem key={item.id}>
                <SidebarMenuButton
                  tooltip={item.title}
                  isActive={isActive}
                  asChild
                >
                  <RouterLink to={item.path} onClick={handleClick}>
                    <item.icon />
                    <span>{item.title}</span>
                  </RouterLink>
                </SidebarMenuButton>
              </SidebarMenuItem>
            )
          })}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  )
}
