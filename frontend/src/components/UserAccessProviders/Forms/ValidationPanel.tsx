import { useMutation, useQueryClient } from "@tanstack/react-query"
import { CheckCircle2, Loader2, RefreshCcw, TestTube2 } from "lucide-react"
import { useState } from "react"
import { LlmProvidersService } from "@/client/sdk.gen"
import type { DetailedTestResult, UserAccessProviderPublic } from "@/client/types.gen"
import { BlockContainer } from "@/components/Page/primitives"
import { Button } from "@/components/ui/button"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import { ValidationDiagnostics } from "../Display/ValidationDiagnostics"
import { ValidationErrorPanel } from "../Display/ValidationErrorPanel"

interface ValidationPanelProps {
  provider: UserAccessProviderPublic
  providerTypeName: string
  onValidated: (result: DetailedTestResult) => void
}

export function ValidationPanel({
  provider,
  providerTypeName,
  onValidated,
}: ValidationPanelProps) {
  const queryClient = useQueryClient()
  const [lastDetailedResult, setLastDetailedResult] =
    useState<DetailedTestResult | null>(null)

  const quickTestMutation = useMutation({
    mutationFn: () => LlmProvidersService.testProvider({ providerId: provider.id }),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["llm-providers"] })
      if (result.valid) {
        showSuccessToast("Connection succeeded")
      } else {
        showErrorToast(result.error || "Validation failed")
      }
    },
    onError: handleError.bind(showErrorToast),
  })

  const detailedTestMutation = useMutation({
    mutationFn: () =>
      LlmProvidersService.testProviderDetailed({ providerId: provider.id }),
    onSuccess: (result) => {
      setLastDetailedResult(result)
      queryClient.invalidateQueries({ queryKey: ["llm-providers"] })
      queryClient.invalidateQueries({
        queryKey: ["llm-catalog", "models-for-uap", provider.id],
      })
      queryClient.invalidateQueries({ queryKey: ["llm-catalog", "models"] })
      if (result.valid) {
        showSuccessToast("Provider validated and models fetched")
        onValidated(result)
      } else {
        showErrorToast(result.error || "Validation failed")
      }
    },
    onError: handleError.bind(showErrorToast),
  })

  const currentResult = lastDetailedResult

  return (
    <BlockContainer
      title="Validation"
      subtitle="Confirm the credentials work before you rely on them in agents or prompts."
      variant="card"
      density="default"
      headerActions={
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => quickTestMutation.mutate()}
            disabled={quickTestMutation.isPending || detailedTestMutation.isPending}
          >
            {quickTestMutation.isPending ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <TestTube2 className="h-3.5 w-3.5" />
            )}
            Quick test
          </Button>
          <Button
            size="sm"
            onClick={() => detailedTestMutation.mutate()}
            disabled={quickTestMutation.isPending || detailedTestMutation.isPending}
          >
            {detailedTestMutation.isPending ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <RefreshCcw className="h-3.5 w-3.5" />
            )}
            Fetch diagnostics
          </Button>
        </div>
      }
      bodyClassName="space-y-4"
    >
      <div className="rounded-xl border bg-muted/20 px-4 py-3">
        <div className="flex items-start gap-3">
          <div
            className={`mt-0.5 inline-flex h-8 w-8 items-center justify-center rounded-full ${
              provider.is_validated
                ? "bg-green-500/10 text-green-600"
                : "bg-muted text-muted-foreground"
            }`}
          >
            <CheckCircle2 className="h-4 w-4" />
          </div>
          <div>
            <p className="text-sm font-medium">
              {provider.is_validated ? "Last known status: verified" : "Not validated yet"}
            </p>
            <p className="text-xs text-muted-foreground">
              {provider.last_validated_at
                ? `Last successful validation: ${new Date(provider.last_validated_at).toLocaleString()}`
                : "Run the detailed test to fetch models and provider diagnostics."}
            </p>
          </div>
        </div>
      </div>

      {provider.validation_error && !currentResult ? (
        <ValidationErrorPanel
          providerName={providerTypeName}
          result={{
            error: provider.validation_error,
            error_code: null,
          }}
          onRetry={() => detailedTestMutation.mutate()}
        />
      ) : null}

      {currentResult && !currentResult.valid ? (
        <ValidationErrorPanel
          providerName={providerTypeName}
          result={currentResult}
          onRetry={() => detailedTestMutation.mutate()}
        />
      ) : null}

      {currentResult?.valid ? (
        <div className="rounded-xl border border-green-500/20 bg-green-500/5 px-4 py-3 text-sm text-green-700 dark:text-green-300">
          Validation passed. {currentResult.models?.length ?? 0} model
          {(currentResult.models?.length ?? 0) === 1 ? "" : "s"} returned.
        </div>
      ) : null}

      {currentResult ? <ValidationDiagnostics result={currentResult} /> : null}
    </BlockContainer>
  )
}
