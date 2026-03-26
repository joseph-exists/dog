import type { SvgAssetCreatePrivate } from "@/client"
import {
  type TesserJobStatusResponse,
  type TesserRenderPayload,
  TesserService,
} from "@/services/tesserService"

function slugifyScriptName(scriptName: string): string {
  return scriptName
    .replace(/[^a-zA-Z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .toLowerCase()
}

export function buildTimestampedScriptAssetName(scriptName: string): string {
  const safeScriptName = slugifyScriptName(scriptName) || "tesser"
  const stamp = new Date().toISOString().replace(/[:.]/g, "-")
  return `${safeScriptName}-${stamp}`
}

export function buildTesserSvgAssetPayload(input: {
  scriptName: string
  job: TesserJobStatusResponse
  render: TesserRenderPayload
  scriptInput: Record<string, unknown>
  name?: string
  description?: string | null
  metadataJson?: Record<string, unknown>
}): SvgAssetCreatePrivate | null {
  const svgMarkup = TesserService.getSvgMarkupFromRender(input.render)
  if (!svgMarkup) return null

  return {
    visibility: "private",
    name: input.name ?? buildTimestampedScriptAssetName(input.scriptName),
    description:
      input.description ??
      `Generated from Tesser script "${input.scriptName}"`,
    svg_markup: svgMarkup,
    metadata_json: {
      source: "tesser",
      script_name: input.scriptName,
      script_input: input.scriptInput,
      job_id: input.job.job_id,
      request_id: input.job.request_id,
      runtime_profile: input.job.runtime_profile ?? null,
      resolved_capabilities: input.job.resolved_capabilities ?? [],
      status: input.job.status,
      queued_at: input.job.queued_at ?? null,
      completed_at: input.job.completed_at ?? null,
      created_from_surface: "svg-library",
      render_format: input.render.format ?? null,
      manifest_path: input.render.manifest_path ?? null,
      saved_at: new Date().toISOString(),
      ...(input.metadataJson ?? {}),
    },
  }
}
