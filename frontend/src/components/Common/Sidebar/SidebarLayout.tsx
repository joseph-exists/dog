// src/components/Common/Sidebar/SidebarLayout.tsx

import {
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
} from "@/components/ui/sidebar"

import { NavMain } from "./NavMain"
import { NavUser } from "./NavUser"
import type { NavSection, SidebarUser } from "./types"

// ============================================================================
// SidebarLayout - Section Composer
// ============================================================================
//
// RESPONSIBILITIES:
//   - Arranges sections into Header / Content / Footer zones
//   - Routes sections to appropriate Nav components based on variant
//   - Renders user menu in footer
//
// SECTION VARIANTS:
//   - "main": Rendered in SidebarContent, fills available space
//   - "secondary": Rendered in SidebarContent with mt-auto (pins to bottom)
//   - "footer": Reserved for future use (custom footer sections)
//
// LAYOUT ZONES:
//   - SidebarHeader: Logo/branding (passed as children)
//   - SidebarContent: Navigation sections
//   - SidebarFooter: User menu
// ============================================================================

interface SidebarLayoutProps {
  /** Header content (logo, branding) */
  header: React.ReactNode
  /** Navigation sections to render */
  sections: NavSection[]
  /** Current user for footer */
  user: SidebarUser | null
  /** Logout handler */
  onLogout: () => void
}

export function SidebarLayout({
  header,
  sections,
  user,
  onLogout,
}: SidebarLayoutProps) {
  // Split sections by variant for layout placement
  const mainSections = sections.filter((s) => s.variant === "main")
  const secondarySections = sections.filter((s) => s.variant === "secondary")

  return (
    <>
      <SidebarHeader className="px-4 py-6 group-data-[collapsible=icon]:px-0 group-data-[collapsible=icon]:items-center">
        {header}
      </SidebarHeader>

      <SidebarContent>
        {/* Main sections fill available space */}
        {mainSections.map((section) => (
          <NavMain key={section.id} section={section} />
        ))}

        {/* Secondary sections pin to bottom */}
        {secondarySections.map((section, index) => (
          <div key={section.id} className={index === 0 ? "mt-auto" : ""}>
            <NavMain section={section} />
          </div>
        ))}
      </SidebarContent>

      <SidebarFooter>
        <NavUser user={user} onLogout={onLogout} />
      </SidebarFooter>
    </>
  )
}
