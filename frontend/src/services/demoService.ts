/**
 * Demo Service
 *
 * Resolve payloads are now consumed directly from generated SDK types.
 */

import { DemosService, type ResolveDemoEntryPayload } from "@/client"

// ============================================================================
// ViewModel Types
// ============================================================================

export interface DemoConfigViewModel {
  id: string
  slug: string
  title: string
  description: string | null
  scope: "system" | "personal" | "shared"
  isActive: boolean
  defaultAutoRespond: boolean
  defaultPanelsJson: Array<{ [key: string]: unknown }>
  defaultLayoutJson: Array<{ [key: string]: unknown }>
  metadataJson: { [key: string]: unknown }
  ownerId: string | null
  createdAt: Date
  updatedAt: Date
}

export interface DemoSessionViewModel {
  id: string
  demoConfigId: string
  userId: string
  roomId: string
  autoRespond: boolean
  status: "active" | "archived" | "ended"
  pageEntityType: string
  pageEntityId: string
  createdAt: Date
  updatedAt: Date
  lastAccessedAt: Date
}

export type ResolvedDemoSessionViewModel = ResolveDemoEntryPayload

// ============================================================================
// Service API
// ============================================================================

export const DemoService = {
  /**
   * Resolve (get-or-create) the current user's demo session for a slug.
   * Backend guarantees per-user runtime isolation via DemoSession.
   */
  async resolveSessionForSlug(
    slug: string,
  ): Promise<ResolvedDemoSessionViewModel> {
    return DemosService.resolveDemoSessionForSlug({
      demoSlug: slug,
    })
  },
}
