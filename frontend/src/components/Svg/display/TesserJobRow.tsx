import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { useTesserJob } from "@/hooks/useTesserJob"
import {
  type TesserJobStatusResponse,
  TesserService,
} from "@/services/tesserService"

export interface LocalTesserJob {
  jobId: string
  requestId?: string | null
  scriptName: string
  queuedAt?: string | null
  scriptInput: Record<string, unknown>
}

export function TesserJobRow({
  job,
  onSave,
  savedAssetId,
}: {
  job: LocalTesserJob
  onSave: (input: {
    scriptName: string
    job: TesserJobStatusResponse
    scriptInput: Record<string, unknown>
  }) => Promise<void>
  savedAssetId?: string | null
}) {
  const jobQuery = useTesserJob(job.jobId)
  const status = jobQuery.data?.status ?? "queued"
  const render = jobQuery.data?.render
  const svgMarkup = TesserService.getSvgMarkupFromRender(render)

  return (
    <div className="space-y-3 rounded-xl border bg-gradient-to-br from-background via-background to-muted/20 p-3 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="min-w-0">
          <div className="truncate text-sm font-medium">{job.scriptName}</div>
          <div className="truncate text-xs text-muted-foreground">
            job `{job.jobId}`
          </div>
        </div>
        <Badge
          variant={
            status === "error" || status === "failed"
              ? "destructive"
              : "secondary"
          }
        >
          {status}
        </Badge>
      </div>

      {jobQuery.isLoading ? <Skeleton className="h-16 w-full" /> : null}

      {jobQuery.error ? (
        <Alert variant="destructive">
          <AlertTitle>Failed to refresh job</AlertTitle>
          <AlertDescription>{jobQuery.error.message}</AlertDescription>
        </Alert>
      ) : null}

      {jobQuery.data?.error ? (
        <Alert variant="destructive">
          <AlertTitle>Render failed</AlertTitle>
          <AlertDescription>{jobQuery.data.error}</AlertDescription>
        </Alert>
      ) : null}

      {jobQuery.data && !jobQuery.data.error ? (
        <div className="space-y-2 text-xs text-muted-foreground">
          {jobQuery.data.runtime_profile ? (
            <div>runtime_profile: {jobQuery.data.runtime_profile}</div>
          ) : null}
          {jobQuery.data.queued_at ? (
            <div>queued_at: {jobQuery.data.queued_at}</div>
          ) : null}
          {jobQuery.data.completed_at ? (
            <div>completed_at: {jobQuery.data.completed_at}</div>
          ) : null}
        </div>
      ) : null}

      {svgMarkup ? (
        <div className="space-y-2">
          <div className="text-xs font-medium text-foreground">
            SVG output ready
          </div>
          <div className="h-40 overflow-hidden rounded-xl border bg-[radial-gradient(circle_at_top,_rgba(251,191,36,0.15),_transparent_45%),linear-gradient(180deg,rgba(15,23,42,0.02),rgba(15,23,42,0.06))] p-2">
            <div
              className="h-full w-full [&_svg]:h-full [&_svg]:w-full [&_svg]:object-contain"
              dangerouslySetInnerHTML={{ __html: svgMarkup }}
            />
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button
              size="sm"
              onClick={() => {
                if (!jobQuery.data) return
                void onSave({
                  scriptName: job.scriptName,
                  job: jobQuery.data,
                  scriptInput: job.scriptInput,
                })
              }}
              disabled={!jobQuery.data || Boolean(savedAssetId)}
            >
              {savedAssetId ? "Saved to Library" : "Save to Library"}
            </Button>
            {savedAssetId ? (
              <Badge variant="secondary">
                asset {savedAssetId.slice(0, 8)}
              </Badge>
            ) : null}
          </div>
          <p className="text-xs text-muted-foreground">
            Save creates a normal private SVG asset with Tesser provenance
            metadata.
          </p>
        </div>
      ) : null}
    </div>
  )
}
