import { ChevronDown, Info } from "lucide-react"
import { useState } from "react"
import type { DetailedTestResult } from "@/client/types.gen"
import { Button } from "@/components/ui/button"

interface ValidationDiagnosticsProps {
  result: DetailedTestResult
}

export function ValidationDiagnostics({ result }: ValidationDiagnosticsProps) {
  const [open, setOpen] = useState(false)

  return (
    <div className="rounded-lg border border-dashed bg-muted/30">
      <Button
        type="button"
        variant="ghost"
        size="sm"
        className="flex w-full items-center justify-between px-3 py-2"
        onClick={() => setOpen((value) => !value)}
      >
        <span className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
          <Info className="h-3.5 w-3.5" />
          Diagnostics
        </span>
        <ChevronDown
          className={`h-4 w-4 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </Button>
      {open ? (
        <div className="space-y-3 border-t px-3 py-3 text-xs">
          <div className="grid gap-2 md:grid-cols-3">
            <div>
              <p className="font-medium text-foreground">Status</p>
              <p className="text-muted-foreground">
                {result.valid ? "Valid" : "Failed"}
              </p>
            </div>
            <div>
              <p className="font-medium text-foreground">Latency</p>
              <p className="text-muted-foreground">
                {result.latency_ms ? `${result.latency_ms} ms` : "Unavailable"}
              </p>
            </div>
            <div>
              <p className="font-medium text-foreground">Error code</p>
              <p className="text-muted-foreground">
                {result.error_code || "Not provided"}
              </p>
            </div>
          </div>
          {result.rate_limits ? (
            <pre className="overflow-x-auto rounded-md bg-background p-3 text-[11px] text-muted-foreground">
              {JSON.stringify(result.rate_limits, null, 2)}
            </pre>
          ) : null}
          {result.account_info ? (
            <pre className="overflow-x-auto rounded-md bg-background p-3 text-[11px] text-muted-foreground">
              {JSON.stringify(result.account_info, null, 2)}
            </pre>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}
