import { AlertTriangle, ArrowUpRight, RotateCcw } from "lucide-react"
import type { DetailedTestResult } from "@/client/types.gen"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"

interface ValidationErrorPanelProps {
  providerName: string
  result: Pick<DetailedTestResult, "error" | "error_code">
  onRetry?: () => void
}

type ErrorGuidance = {
  title: string
  guidance: string
  docsUrl?: string
}

const ERROR_GUIDANCE: Record<string, Record<string, ErrorGuidance>> = {
  openai: {
    "401": {
      title: "Authentication failed",
      guidance:
        "Check that the API key is current, belongs to the right project, and that any organization or project IDs match the key.",
      docsUrl: "https://platform.openai.com/api-keys",
    },
    "429": {
      title: "Rate limit or quota issue",
      guidance:
        "The credentials connected, but the account is out of quota or temporarily throttled. Confirm usage and billing, then retry.",
      docsUrl: "https://platform.openai.com/usage",
    },
  },
  anthropic: {
    "401": {
      title: "Authentication failed",
      guidance:
        "Confirm the key is active and the Anthropic version header, if set, matches the provider expectation.",
      docsUrl: "https://console.anthropic.com/settings/keys",
    },
  },
  default: {
    unknown: {
      title: "Validation failed",
      guidance:
        "Check the endpoint, key, and any provider-specific settings. If this is a custom adapter, verify the base URL and headers first.",
    },
  },
}

export function ValidationErrorPanel({
  providerName,
  result,
  onRetry,
}: ValidationErrorPanelProps) {
  const guidance =
    ERROR_GUIDANCE[providerName]?.[result.error_code ?? ""] ??
    ERROR_GUIDANCE.default.unknown

  return (
    <Alert variant="destructive" className="border-red-500/30 bg-red-500/5">
      <AlertTriangle className="h-4 w-4" />
      <AlertTitle>{guidance.title}</AlertTitle>
      <AlertDescription className="space-y-3">
        <p>{result.error || guidance.guidance}</p>
        {result.error && result.error !== guidance.guidance ? (
          <p className="text-xs text-red-700/80 dark:text-red-200/80">
            Guidance: {guidance.guidance}
          </p>
        ) : null}
        <div className="flex flex-wrap gap-2">
          {guidance.docsUrl ? (
            <Button variant="outline" size="sm" asChild>
              <a href={guidance.docsUrl} target="_blank" rel="noreferrer">
                Open provider docs
                <ArrowUpRight className="h-3.5 w-3.5" />
              </a>
            </Button>
          ) : null}
          {onRetry ? (
            <Button variant="outline" size="sm" onClick={onRetry}>
              <RotateCcw className="h-3.5 w-3.5" />
              Retry
            </Button>
          ) : null}
        </div>
      </AlertDescription>
    </Alert>
  )
}
