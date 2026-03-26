import { OpenAPI } from "@/client"
import type { ApiRequestOptions } from "@/client/core/ApiRequestOptions"
import { request as __request } from "@/client/core/request"

export interface TesserScript {
  name: string
  description: string
  supported_formats: string[]
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

export interface TesserRenderPayload {
  format?: string | null
  svg?: string | null
  artifacts?: Array<Record<string, unknown>>
  manifest_path?: string | null
  runtime_profile?: string | null
  resolved_capabilities?: string[]
  [key: string]: unknown
}

export interface TesserScriptRunResponse {
  request_id?: string | null
  script_name: string
  status: string
  render?: TesserRenderPayload | null
  error?: string | null
  completed_at?: string | null
  worker_id?: string | null
}

export interface TesserScriptEnqueueRequest {
  script_input?: Record<string, unknown>
  room_id?: string | null
}

export interface TesserScriptEnqueueResponse {
  request_id: string
  job_id: string
  script_name: string
  status: string
  runtime_profile?: string | null
  resolved_capabilities?: string[]
  queued_at?: string | null
  completed_at?: string | null
  render?: TesserRenderPayload | null
  error?: string | null
  worker_id?: string | null
}

export interface TesserJobStatusResponse {
  request_id: string
  job_id: string
  status: string
  script_name?: string | null
  room_id?: string | null
  runtime_profile?: string | null
  resolved_capabilities?: string[]
  queued_at?: string | null
  completed_at?: string | null
  render?: TesserRenderPayload | null
  error?: string | null
  worker_id?: string | null
}

export interface TesserScriptHelpResponse {
  script_name: string
  help_text?: string | null
  description?: string | null
  supported_formats: string[]
  input_schema: Record<string, unknown>
}

export interface TesserExamplesIndexResponse {
  path: string
  content: string
}

export const TesserService = {
  async listScripts(input?: {
    format?: string
  }): Promise<TesserScriptsResponse> {
    const query = input?.format
      ? `?format=${encodeURIComponent(input.format)}`
      : ""
    const requestOptions: ApiRequestOptions<TesserScriptsResponse> = {
      method: "GET",
      url: `/api/v1/tesser/scripts${query}`,
    }
    return __request(OpenAPI, requestOptions)
  },

  async runScript(
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

  async enqueueScript(
    scriptName: string,
    payload: TesserScriptEnqueueRequest,
  ): Promise<TesserScriptEnqueueResponse> {
    const requestOptions: ApiRequestOptions<TesserScriptEnqueueResponse> = {
      method: "POST",
      url: `/api/v1/tesser/scripts/${encodeURIComponent(scriptName)}/enqueue`,
      body: payload,
      mediaType: "application/json",
    }
    return __request(OpenAPI, requestOptions)
  },

  async getScriptHelp(scriptName: string): Promise<TesserScriptHelpResponse> {
    const requestOptions: ApiRequestOptions<TesserScriptHelpResponse> = {
      method: "GET",
      url: `/api/v1/tesser/scripts/${encodeURIComponent(scriptName)}/help`,
    }
    return __request(OpenAPI, requestOptions)
  },

  async getExamplesIndex(): Promise<TesserExamplesIndexResponse> {
    const requestOptions: ApiRequestOptions<TesserExamplesIndexResponse> = {
      method: "GET",
      url: "/api/v1/tesser/examples/index",
    }
    return __request(OpenAPI, requestOptions)
  },

  async getJobStatus(jobId: string): Promise<TesserJobStatusResponse> {
    const requestOptions: ApiRequestOptions<TesserJobStatusResponse> = {
      method: "GET",
      url: `/api/v1/tesser/jobs/${encodeURIComponent(jobId)}`,
    }
    return __request(OpenAPI, requestOptions)
  },

  getSvgMarkupFromRender(render?: TesserRenderPayload | null): string | null {
    if (!render || render.format !== "svg") return null
    return typeof render.svg === "string" && render.svg.trim().length > 0
      ? render.svg
      : null
  },
}
