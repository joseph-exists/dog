/**
 * Demo Service
 *
 * Resolve payloads are now consumed directly from generated SDK types.
 */

import { DemosService, type ResolveDemoEntryPayload } from "@/client"
import { OpenAPI } from "@/client"
import type { ApiRequestOptions } from "@/client/core/ApiRequestOptions"
import { request as __request } from "@/client/core/request"

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

export interface DemoCanvasRenderRequest {
  panel_id?: string | null
  script_name?: string
  script_input?: Record<string, unknown>
  title?: string
  subtitle?: string | null
  persist_to_composition?: boolean
  commit_to_shadow_repo?: boolean
}

export interface DemoCanvasRenderResponse {
  demo_config_id: string
  panel_id: string
  request_id?: string | null
  status: string
  svg: string
  persisted: boolean
  shadow_commit_sha?: string | null
}

export interface TesserScript {
  name: string
  description: string
  input_schema: Record<string, unknown>
  help_text?: string | null
  kind?: string | null
  source_path?: string | null
}

export interface TesserScriptsResponse {
  data: TesserScript[]
  count: number
}

export interface TesserScriptRunRequest {
  script_input?: Record<string, unknown>
  room_id?: string | null
  timeout_seconds?: number
}

export interface TesserScriptRunResponse {
  request_id?: string | null
  script_name: string
  status: string
  render?: Record<string, unknown> | null
  error?: string | null
  completed_at?: string | null
  worker_id?: string | null
}

export interface TesserScriptHelpResponse {
  script_name: string
  help_text?: string | null
  description?: string | null
  input_schema: Record<string, unknown>
}

export interface TesserExamplesIndexResponse {
  path: string
  content: string
}

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

  async renderCanvasPanel(
    demoConfigId: string,
    payload: DemoCanvasRenderRequest,
  ): Promise<DemoCanvasRenderResponse> {
    const requestOptions: ApiRequestOptions<DemoCanvasRenderResponse> = {
      method: "POST",
      url: `/api/v1/demos/configs/${demoConfigId}/canvas/render`,
      body: payload,
      mediaType: "application/json",
    }
    return __request(OpenAPI, requestOptions)
  },

  async listTesserScripts(): Promise<TesserScriptsResponse> {
    const requestOptions: ApiRequestOptions<TesserScriptsResponse> = {
      method: "GET",
      url: "/api/v1/tesser/scripts",
    }
    return __request(OpenAPI, requestOptions)
  },

  async runTesserScript(
    scriptName: string,
    payload: TesserScriptRunRequest,
  ): Promise<TesserScriptRunResponse> {
    const requestOptions: ApiRequestOptions<TesserScriptRunResponse> = {
      method: "POST",
      url: `/api/v1/tesser/scripts/${encodeURIComponent(scriptName)}/run`,
      body: payload,
      mediaType: "application/json",
    }
    return __request(OpenAPI, requestOptions)
  },

  async getTesserScriptHelp(
    scriptName: string,
  ): Promise<TesserScriptHelpResponse> {
    const requestOptions: ApiRequestOptions<TesserScriptHelpResponse> = {
      method: "GET",
      url: `/api/v1/tesser/scripts/${encodeURIComponent(scriptName)}/help`,
    }
    return __request(OpenAPI, requestOptions)
  },

  async getTesserExamplesIndex(): Promise<TesserExamplesIndexResponse> {
    const requestOptions: ApiRequestOptions<TesserExamplesIndexResponse> = {
      method: "GET",
      url: "/api/v1/tesser/examples/index",
    }
    return __request(OpenAPI, requestOptions)
  },
}
