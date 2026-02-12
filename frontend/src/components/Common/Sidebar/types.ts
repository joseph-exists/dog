// src/components/Common/Sidebar/types.ts

import type { LucideIcon } from "lucide-react"

/**
 * Single navigation item.
 * Path-based for router integration, icon for visual.
 */
export interface NavItem {
  /** Unique identifier */
  id: string
  /** Display label */
  title: string
  /** Route path (used with RouterLink) */
  path: string
  /** Icon component */
  icon: LucideIcon
  /** Optional badge text (e.g., "3" for notifications) */
  badge?: string
}

/**
 * Navigation section configuration.
 * Sections are rendered in order by SidebarLayout.
 */
export interface NavSection {
  /** Unique identifier */
  id: string
  /** Section label (optional - some sections are unlabeled) */
  label?: string
  /** Items in this section */
  items: NavItem[]
  /** Visual variant */
  variant: "main" | "secondary" | "footer"
}

/**
 * User data shape for NavUser.
 * Intentionally minimal - maps from auth user.
 */
export interface SidebarUser {
  id: string
  fullName: string
  email: string
  avatarUrl?: string
  isSuperuser?: boolean
}
