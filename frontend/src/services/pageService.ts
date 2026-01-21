/**
 * Page Service - Data Integration Layer
 *
 * Provides a ViewModel-based interface for persisted page layouts.
 * Uses the OpenAPI client request helper for new endpoints.
 */

import { OpenAPI } from "@/client"
import type { ApiRequestOptions } from "@/client/core/ApiRequestOptions"
import { request as __request } from "@/client/core/request"
import type { TemplateBlock } from "@/components/Page/registry"

// ============================================================================
// Type Definitions - ViewModels
// ============================================================================

export interface PageLayoutViewModel {
  id: string
  entityType: string
  entityId: string
  ownerId: string
  layoutVersion: number
  layout: TemplateBlock[]
  createdAt: Date
  updatedAt: Date
}

export interface SavePageLayoutInput {
  entityType: string
  entityId: string
  layout: TemplateBlock[]
  layoutVersion?: number
}

// ============================================================================
// API Types (local mirror)
// ============================================================================

interface PagePublicResponse {
  id: string
  entity_type: string
  entity_id: string
  owner_id: string
  layout_version: number
  layout_json: TemplateBlock[]
  created_at: string
  updated_at: string
}

interface PageLayoutPayload {
  layout_json: TemplateBlock[]
  layout_version?: number
}

// ============================================================================
// Transformation Functions
// ============================================================================

function transformPage(page: PagePublicResponse): PageLayoutViewModel {
  return {
    id: page.id,
    entityType: page.entity_type,
    entityId: page.entity_id,
    ownerId: page.owner_id,
    layoutVersion: page.layout_version,
    layout: page.layout_json,
    createdAt: new Date(page.created_at),
    updatedAt: new Date(page.updated_at),
  }
}

// ============================================================================
// Service
// ============================================================================

export const PageService = {
  /**
   * Fetch persisted layout for an entity.
   */
  async getLayout(
    entityType: string,
    entityId: string,
  ): Promise<PageLayoutViewModel | null> {
    const options: ApiRequestOptions<PagePublicResponse | null> = {
      method: "GET",
      url: `/api/v1/pages/${entityType}/${entityId}`,
    }

    const response = await __request<PagePublicResponse | null>(
      OpenAPI,
      options,
    )
    return response ? transformPage(response) : null
  },

  /**
   * Create or overwrite a layout for an entity.
   */
  async saveLayout(input: SavePageLayoutInput): Promise<PageLayoutViewModel> {
    const payload: PageLayoutPayload = {
      layout_json: input.layout,
      layout_version: input.layoutVersion,
    }

    const options: ApiRequestOptions<PagePublicResponse> = {
      method: "POST",
      url: `/api/v1/pages/${input.entityType}/${input.entityId}/layout`,
      body: payload,
      mediaType: "application/json",
    }

    const response = await __request<PagePublicResponse>(OpenAPI, options)
    return transformPage(response)
  },

  /**
   * Update a layout by page ID.
   */
  async updateLayout(
    pageId: string,
    payload: PageLayoutPayload,
  ): Promise<PageLayoutViewModel> {
    const options: ApiRequestOptions<PagePublicResponse> = {
      method: "PUT",
      url: `/api/v1/pages/${pageId}`,
      body: payload,
      mediaType: "application/json",
    }

    const response = await __request<PagePublicResponse>(OpenAPI, options)
    return transformPage(response)
  },
}
