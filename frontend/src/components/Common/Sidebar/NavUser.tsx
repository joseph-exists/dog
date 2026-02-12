// src/components/Common/Sidebar/NavUser.tsx

import { Link as RouterLink } from "@tanstack/react-router"
import { ChevronsUpDown, LogOut, Settings } from "lucide-react"

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar"

import type { SidebarUser } from "./types"

// ============================================================================
// NavUser - User Menu Component
// ============================================================================
//
// RESPONSIBILITIES:
//   - Displays current user info in sidebar footer
//   - Provides dropdown with settings link and logout action
//   - Handles mobile sidebar close on navigation
//
// DOES NOT:
//   - Manage auth state (receives user + onLogout as props)
//   - Fetch user data
//
// NULL STATE:
//   - Returns null if user is not provided (logged out state)
// ============================================================================

interface NavUserProps {
  /** Current user data (null = logged out) */
  user: SidebarUser | null
  /** Logout handler - called when user clicks logout */
  onLogout: () => void
}

/** Extracts initials from full name for avatar fallback */
function getInitials(name: string): string {
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .toUpperCase()
    .slice(0, 2)
}

export function NavUser({ user, onLogout }: NavUserProps) {
  const { isMobile, setOpenMobile } = useSidebar()

  // Don't render if no user
  if (!user) return null

  const handleNavClick = () => {
    if (isMobile) {
      setOpenMobile(false)
    }
  }

  const handleLogout = () => {
    onLogout()
  }

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton
              size="lg"
              className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
              data-testid="user-menu"
            >
              <Avatar className="size-8 grayscale">
                {user.avatarUrl && (
                  <AvatarImage src={user.avatarUrl} alt={user.fullName} />
                )}
                <AvatarFallback className="bg-zinc-600 text-white">
                  {getInitials(user.fullName)}
                </AvatarFallback>
              </Avatar>
              <div className="grid flex-1 text-left text-sm leading-tight min-w-0">
                <span className="truncate font-medium">{user.fullName}</span>
                <span className="text-muted-foreground truncate text-xs">
                  {user.email}
                </span>
              </div>
              <ChevronsUpDown className="ml-auto size-4 text-muted-foreground" />
            </SidebarMenuButton>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            className="w-(--radix-dropdown-menu-trigger-width) min-w-56 rounded-lg"
            side={isMobile ? "bottom" : "right"}
            align="end"
            sideOffset={4}
          >
            <DropdownMenuLabel className="p-0 font-normal">
              <div className="flex items-center gap-2 px-1 py-1.5 text-left text-sm">
                <Avatar className="size-8">
                  {user.avatarUrl && (
                    <AvatarImage src={user.avatarUrl} alt={user.fullName} />
                  )}
                  <AvatarFallback>{getInitials(user.fullName)}</AvatarFallback>
                </Avatar>
                <div className="grid flex-1 text-left text-sm leading-tight">
                  <span className="truncate font-medium">{user.fullName}</span>
                  <span className="text-muted-foreground truncate text-xs">
                    {user.email}
                  </span>
                </div>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <RouterLink to="/settings" onClick={handleNavClick}>
              <DropdownMenuItem>
                <Settings className="mr-2 size-4" />
                Settings
              </DropdownMenuItem>
            </RouterLink>
            <DropdownMenuItem onClick={handleLogout}>
              <LogOut className="mr-2 size-4" />
              Log Out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  )
}
