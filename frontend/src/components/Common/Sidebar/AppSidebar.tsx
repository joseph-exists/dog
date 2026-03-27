// src/components/Common/Sidebar/AppSidebar.tsx

import { useRouterState } from "@tanstack/react-router"
import {
  BirdhouseIcon,
  BookHeart,
  BookOpen,
  Bot,
  CircuitBoard,
  Crown,
  FolderGit2,
  FolderKanban,
  Gem,
  GrapeIcon,
  Home,
  Images,
  MessageSquare,
  MonitorPlay,
  MoonStar,
  Smile,
  Sparkles,
  User2,
  Users,
} from "lucide-react"
import { Logo } from "@/components/Common/Logo"
import { Sidebar } from "@/components/ui/sidebar"
import useAuth from "@/hooks/useAuth"
import { SidebarLayout } from "./SidebarLayout"
import type { NavItem, NavSection, SidebarUser } from "./types"

// ============================================================================
// NAVIGATION REGISTRY
// ============================================================================
//
// All navigation configuration lives here. This is the single source of truth.
//
// STRUCTURE:
//   1. MAIN_NAV_ITEMS     - Always visible, core app features
//   2. Domain sections    - Contextual nav shown for specific routes
//   3. buildUserItems()   - Dynamic items based on auth state
//   4. buildSections()    - Registry that computes final sections from route
//
// ============================================================================

// ============================================================================
// MAIN NAVIGATION
// ============================================================================
//
// ADD:    Insert a NavItem object in desired position
// REMOVE: Delete the NavItem object
// EDIT:   Modify title/path/icon, keep id stable
// ============================================================================

const MAIN_NAV_ITEMS: NavItem[] = [
  { id: "dashboard", title: "Dashboard", path: "/", icon: Home },
  { id: "stories", title: "Story Desk", path: "/stories", icon: BookOpen },
  { id: "story", title: "Library", path: "/story", icon: BookHeart },
  { id: "rooms", title: "Rooms", path: "/rooms", icon: MessageSquare },
  { id: "agents", title: "Agents", path: "/agents", icon: Bot },
  { id: "projects", title: "Projects", path: "/projects", icon: FolderKanban },
  { id: "workspaces", title: "Workspaces", path: "/workspaces", icon: MonitorPlay },
  { id: "repos", title: "Repo Library", path: "/repos", icon: FolderGit2 },
  { id: "svgs", title: "SVG Library", path: "/svgs", icon: Images },
  { id: "personas", title: "Identity Manager", path: "/personas", icon: Smile },
  // { id: "items", title: "Items", path: "/items", icon: Briefcase },
  {
    id: "chatster",
    title: "Debug-Chatster",
    path: "/chatster",
    icon: BirdhouseIcon,
  },
  {
    id: "prompt-builder",
    icon: GrapeIcon,
    title: "prompt builder",
    path: "/prompt-builder",
  },
  {
    id: "demo-builder",
    icon: CircuitBoard,
    title: "demo builder",
    path: "/demo-builder",
  },
  { id: "demo-library", icon: MoonStar, title: "demo library", path: "/demos" },
]

// ============================================================================
// DOMAIN-SPECIFIC SECTIONS
// ============================================================================
//
// Each domain that needs contextual navigation defines its items here.
// The buildSections() registry determines when each is visible.
//
// TO ADD A NEW DOMAIN SECTION:
//   1. Define a new NavItem[] array below (e.g., AGENTS_NAV_ITEMS)
//   2. Add visibility logic in buildSections() using route matching
//   3. Import any new icons at top of file
// ============================================================================

/** Persona domain - tools for managing persona components */
const PERSONA_NAV_ITEMS: NavItem[] = [
  { id: "archetypes", title: "Archetypes", path: "/archetypes", icon: Crown },
  { id: "qualities", title: "Qualities", path: "/qualities", icon: Gem },
  { id: "traits", title: "Traits", path: "/traits", icon: Sparkles },
]

// const STORY_NAV_ITEMS: NavItem[] = [
//   { id: }
// Future domains can be added here:
// const AGENTS_NAV_ITEMS: NavItem[] = [...]
// const ROOMS_NAV_ITEMS: NavItem[] = [...]

// ============================================================================
// DYNAMIC USER ITEMS
// ============================================================================

function buildUserItems(userId?: string, isSuperuser?: boolean): NavItem[] {
  const items: NavItem[] = []

  if (userId) {
    items.push({
      id: "my-page",
      title: "My Page",
      path: `/u/${userId}`,
      icon: User2,
    })
  }

  if (isSuperuser) {
    items.push({
      id: "admin",
      title: "Admin",
      path: "/admin",
      icon: Users,
    })
  }

  return items
}

// ============================================================================
// SECTION REGISTRY
// ============================================================================
//
// This function is the REGISTRY. It determines which sections appear based
// on the current route.
//
// VISIBILITY RULES:
//   - Main section: ALWAYS visible
//   - Persona tools: When path starts with "/personas" or is a persona sub-route
//
// TO ADD CONTEXTUAL NAVIGATION FOR A NEW DOMAIN:
//   1. Define the domain's NavItem[] above
//   2. Add a route check below (e.g., currentPath.startsWith("/agents"))
//   3. Push a new NavSection with variant: "secondary"
// ============================================================================

function buildSections(
  currentPath: string,
  userId?: string,
  isSuperuser?: boolean,
): NavSection[] {
  const sections: NavSection[] = []

  // ─────────────────────────────────────────────────────────────────────────
  // Main navigation - always visible
  // ─────────────────────────────────────────────────────────────────────────
  sections.push({
    id: "main",
    items: [...MAIN_NAV_ITEMS, ...buildUserItems(userId, isSuperuser)],
    variant: "main",
  })

  // ─────────────────────────────────────────────────────────────────────────
  // Persona tools - contextual
  // Visible when: /personas, /archetypes, /qualities, /traits
  // ─────────────────────────────────────────────────────────────────────────
  const personaRoutes = ["/personas", "/archetypes", "/qualities", "/traits"]
  const isPersonaContext = personaRoutes.some(
    (route) => currentPath === route || currentPath.startsWith(`${route}/`),
  )

  if (isPersonaContext) {
    sections.push({
      id: "persona-tools",
      label: "Persona Tools",
      items: PERSONA_NAV_ITEMS,
      variant: "secondary",
    })
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Future domain sections go here
  // ─────────────────────────────────────────────────────────────────────────
  // Example:
  // const isAgentsContext = currentPath.startsWith("/agents")
  // if (isAgentsContext) {
  //   sections.push({
  //     id: "agent-tools",
  //     label: "Agent Tools",
  //     items: AGENTS_NAV_ITEMS,
  //     variant: "secondary",
  //   })
  // }

  return sections
}

// ============================================================================
// SIDEBAR SHELL
// ============================================================================

export function AppSidebar() {
  const router = useRouterState()
  const currentPath = router.location.pathname
  const { user: authUser, logout } = useAuth()

  // Map auth user to sidebar user shape
  const user: SidebarUser | null = authUser
    ? {
        id: authUser.id,
        fullName: authUser.full_name || "User",
        email: authUser.email,
        avatarUrl: undefined, // Add if available on auth user
        isSuperuser: authUser.is_superuser,
      }
    : null

  // Compute sections from registry
  const sections = buildSections(currentPath, user?.id, user?.isSuperuser)

  return (
    <Sidebar collapsible="icon">
      <SidebarLayout
        header={<Logo variant="responsive" />}
        sections={sections}
        user={user}
        onLogout={logout}
      />
    </Sidebar>
  )
}

export default AppSidebar
