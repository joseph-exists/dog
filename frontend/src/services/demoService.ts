/**
 * Demo Service
 *
 * Resolve payloads are now consumed directly from generated SDK types.
 */

import { DemosService, type ResolveDemoEntryPayload } from "@/client"
import { OpenAPI } from "@/client"
import type { ApiRequestOptions } from "@/client/core/ApiRequestOptions"
import { request as __request } from "@/client/core/request"
import {
  TesserService,
  type TesserExamplesIndexResponse,
  type TesserScriptHelpResponse,
  type TesserScriptRunRequest,
  type TesserScriptRunResponse,
  type TesserScriptsResponse,
} from "./tesserService"

export type {
  TesserExamplesIndexResponse,
  TesserScript,
  TesserScriptHelpResponse,
  TesserScriptRunRequest,
  TesserScriptRunResponse,
  TesserScriptsResponse,
} from "./tesserService"

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

export interface DemoCanvasRenderJobResponse {
  demo_config_id: string
  panel_id: string
  job_id: string
  request_id?: string | null
  script_name?: string | null
  status: string
  runtime_profile?: string | null
  resolved_capabilities?: string[]
  queued_at?: string | null
  completed_at?: string | null
  svg?: string | null
  persisted: boolean
  shadow_commit_sha?: string | null
  error?: string | null
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

  async enqueueCanvasPanelRender(
    demoConfigId: string,
    payload: DemoCanvasRenderRequest,
  ): Promise<DemoCanvasRenderJobResponse> {
    const requestOptions: ApiRequestOptions<DemoCanvasRenderJobResponse> = {
      method: "POST",
      url: `/api/v1/demos/configs/${demoConfigId}/canvas/render/enqueue`,
      body: payload,
      mediaType: "application/json",
    }
    return __request(OpenAPI, requestOptions)
  },

  async getCanvasRenderJobStatus(
    demoConfigId: string,
    jobId: string,
  ): Promise<DemoCanvasRenderJobResponse> {
    const requestOptions: ApiRequestOptions<DemoCanvasRenderJobResponse> = {
      method: "GET",
      url: `/api/v1/demos/configs/${demoConfigId}/canvas/render/jobs/${encodeURIComponent(jobId)}`,
    }
    return __request(OpenAPI, requestOptions)
  },

  async listTesserScripts(): Promise<TesserScriptsResponse> {
    return TesserService.listScripts()
  },

  async runTesserScript(
    scriptName: string,
    payload: TesserScriptRunRequest,
  ): Promise<TesserScriptRunResponse> {
    return TesserService.runScript(scriptName, payload)
  },

  async getTesserScriptHelp(
    scriptName: string,
  ): Promise<TesserScriptHelpResponse> {
    return TesserService.getScriptHelp(scriptName)
  },

  async getTesserExamplesIndex(): Promise<TesserExamplesIndexResponse> {
    return TesserService.getExamplesIndex()
  },
}
