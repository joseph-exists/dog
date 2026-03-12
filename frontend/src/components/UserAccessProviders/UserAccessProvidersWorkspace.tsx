import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  ArrowRight,
  CheckCircle2,
  KeyRound,
  Loader2,
  Pencil,
  Plus,
  RefreshCcw,
  Sparkles,
  Trash2,
} from "lucide-react"
import { useMemo, useState } from "react"
import { LlmProvidersService } from "@/client/sdk.gen"
import type {
  DetailedTestResult,
  LLMProviderTypePublic,
  UserAccessProviderCreate,
  UserAccessProviderPublic,
  UserAccessProviderUpdate,
} from "@/client/types.gen"
import { BlockContainer } from "@/components/Page/primitives"
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import useAuth from "@/hooks/useAuth"
import { handleError } from "@/utils"
import { ModelPinList, ProviderStatusBadge } from "./Display"
import { SetupSuccessPanel } from "./Flows"
import { ProviderTemplateGallery } from "./Gallery"
import { UserAccessProviderForm, ValidationPanel } from "./Forms"

const STALE_VALIDATION_WINDOW_MS = 1000 * 60 * 60 * 24 * 7

function isProviderStale(provider: UserAccessProviderPublic) {
  if (!provider.is_enabled) {
    return false
  }
  if (!provider.is_validated || !provider.last_validated_at) {
    return true
  }

  const lastValidated = new Date(provider.last_validated_at).getTime()
  if (Number.isNaN(lastValidated)) {
    return true
  }

  return Date.now() - lastValidated > STALE_VALIDATION_WINDOW_MS
}

function formatRelativeValidation(provider: UserAccessProviderPublic) {
  if (!provider.last_validated_at) {
    return "Never checked"
  }

  const deltaMs = Date.now() - new Date(provider.last_validated_at).getTime()
  const deltaHours = Math.floor(deltaMs / (1000 * 60 * 60))
  if (deltaHours < 1) {
    return "Checked less than an hour ago"
  }
  if (deltaHours < 24) {
    return `Checked ${deltaHours}h ago`
  }

  return `Checked ${Math.floor(deltaHours / 24)}d ago`
}

function formatBaseUrl(baseUrl: string | null | undefined) {
  if (!baseUrl) {
    return "Default endpoint"
  }

  try {
    return new URL(baseUrl).host
  } catch {
    return baseUrl
  }
}

function getProviderTypeName(
  provider: UserAccessProviderPublic,
  providerTypes: LLMProviderTypePublic[],
) {
  return providerTypes.find((item) => item.id === provider.alpha_provider_type_id)
}

export function UserAccessProvidersWorkspace() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [powerUserMode, setPowerUserMode] = useState(false)
  const [selectedProviderTypeId, setSelectedProviderTypeId] = useState<string | null>(
    null,
  )
  const [editingProviderId, setEditingProviderId] = useState<string | null>(null)
  const [showModelPinsForProviderId, setShowModelPinsForProviderId] = useState<
    string | null
  >(null)
  const [highlightPins, setHighlightPins] = useState(false)
  const [successProviderId, setSuccessProviderId] = useState<string | null>(null)
  const [validationResults, setValidationResults] = useState<
    Record<string, DetailedTestResult>
  >({})

  const providerTypesQuery = useQuery({
    queryKey: ["llm-provider-type-list"],
    queryFn: () => LlmProvidersService.getProviderTypeList(),
    staleTime: 5 * 60 * 1000,
  })
  const providersQuery = useQuery({
    queryKey: ["llm-providers"],
    queryFn: () => LlmProvidersService.listProviders(),
  })

  const providerTypes = useMemo(
    () => providerTypesQuery.data?.data ?? [],
    [providerTypesQuery.data],
  )
  const providers = useMemo(
    () => providersQuery.data?.data ?? [],
    [providersQuery.data],
  )

  const selectedProvider = useMemo(
    () => providers.find((provider) => provider.id === editingProviderId) ?? null,
    [providers, editingProviderId],
  )
  const selectedProviderType = useMemo(() => {
    if (selectedProvider) {
      return getProviderTypeName(selectedProvider, providerTypes) ?? null
    }

    return (
      providerTypes.find((providerType) => providerType.id === selectedProviderTypeId) ??
      null
    )
  }, [providerTypes, selectedProvider, selectedProviderTypeId])

  const createMutation = useMutation({
    mutationFn: (payload: UserAccessProviderCreate) =>
      LlmProvidersService.createProvider({
        requestBody: payload,
      }),
    onSuccess: (provider) => {
      showSuccessToast("Provider created")
      queryClient.invalidateQueries({ queryKey: ["llm-providers"] })
      setEditingProviderId(provider.id)
      setSuccessProviderId(null)
    },
    onError: handleError.bind(showErrorToast),
  })

  const updateMutation = useMutation({
    mutationFn: ({
      providerId,
      payload,
    }: {
      providerId: string
      payload: UserAccessProviderUpdate
    }) =>
      LlmProvidersService.updateProvider({
        providerId,
        requestBody: payload,
      }),
    onSuccess: (provider) => {
      showSuccessToast("Provider updated")
      queryClient.invalidateQueries({ queryKey: ["llm-providers"] })
      setEditingProviderId(provider.id)
    },
    onError: handleError.bind(showErrorToast),
  })

  const deleteMutation = useMutation({
    mutationFn: (providerId: string) =>
      LlmProvidersService.deleteProvider({
        providerId,
      }),
    onSuccess: () => {
      showSuccessToast("Provider deleted")
      queryClient.invalidateQueries({ queryKey: ["llm-providers"] })
      setEditingProviderId(null)
      setSuccessProviderId(null)
      setShowModelPinsForProviderId(null)
    },
    onError: handleError.bind(showErrorToast),
  })

  const isSaving = createMutation.isPending || updateMutation.isPending

  const activeProviderType = selectedProviderType
  const staleProviders = useMemo(
    () => providers.filter((provider) => isProviderStale(provider)),
    [providers],
  )

  const validateAllMutation = useMutation({
    mutationFn: async (providersToValidate: UserAccessProviderPublic[]) =>
      Promise.allSettled(
        providersToValidate.map(async (provider) => ({
          providerId: provider.id,
          result: await LlmProvidersService.testProviderDetailed({
            providerId: provider.id,
          }),
        })),
      ),
    onSuccess: (results) => {
      const succeeded = results.filter(
        (result): result is PromiseFulfilledResult<{
          providerId: string
          result: DetailedTestResult
        }> => result.status === "fulfilled" && result.value.result.valid,
      )
      const failedCount = results.length - succeeded.length

      if (succeeded.length > 0) {
        setValidationResults((current) => {
          const next = { ...current }
          for (const result of succeeded) {
            next[result.value.providerId] = result.value.result
          }
          return next
        })
      }

      queryClient.invalidateQueries({ queryKey: ["llm-providers"] })

      if (succeeded.length > 0 && failedCount === 0) {
        showSuccessToast(
          `Validated ${succeeded.length} provider${succeeded.length === 1 ? "" : "s"}`,
        )
      } else if (succeeded.length > 0) {
        showSuccessToast(
          `Validated ${succeeded.length}; ${failedCount} still need attention`,
        )
      } else {
        showErrorToast("No stale providers validated successfully")
      }
    },
    onError: handleError.bind(showErrorToast),
  })

  return (
    <div className="space-y-6">
      <BlockContainer
        title="Access providers"
        subtitle="Bring your own provider credentials, validate them before use, and surface the models your team actually cares about."
        variant="card"
        density="comfortable"
        metadata={
          <div className="flex flex-wrap gap-2">
            <Badge variant="secondary" className="gap-1">
              <KeyRound className="h-3.5 w-3.5" />
              {providers.length} provider{providers.length === 1 ? "" : "s"}
            </Badge>
            <Badge variant="outline" className="gap-1">
              <CheckCircle2 className="h-3.5 w-3.5" />
              {providers.filter((provider) => provider.is_validated).length} validated
            </Badge>
            {staleProviders.length > 0 ? (
              <Badge variant="outline" className="gap-1">
                <RefreshCcw className="h-3.5 w-3.5" />
                {staleProviders.length} stale
              </Badge>
            ) : null}
          </div>
        }
        headerActions={
          <div className="flex flex-wrap gap-2">
            {staleProviders.length > 0 ? (
              <Button
                variant="outline"
                onClick={() => validateAllMutation.mutate(staleProviders)}
                disabled={validateAllMutation.isPending}
              >
                {validateAllMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCcw className="h-4 w-4" />
                )}
                Validate all stale
              </Button>
            ) : null}
            <Button
              onClick={() => {
                setEditingProviderId(null)
                setSuccessProviderId(null)
                setShowModelPinsForProviderId(null)
                if (!selectedProviderTypeId && providerTypes[0]) {
                  setSelectedProviderTypeId(providerTypes[0].id)
                }
              }}
            >
              <Plus className="h-4 w-4" />
              Add provider
            </Button>
          </div>
        }
        bodyClassName="space-y-4"
      >
        <div className="grid gap-3 md:grid-cols-3">
          <div className="rounded-xl border bg-background/70 p-4">
            <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
              First-time path
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              Choose a template, verify it, then pin the models you actually use.
            </p>
          </div>
          <div className="rounded-xl border bg-background/70 p-4">
            <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
              Power controls
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              Advanced transport settings stay available, but tucked behind a dedicated section.
            </p>
          </div>
          <div className="rounded-xl border bg-background/70 p-4">
            <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
              Outcome
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              Agents and prompts can consume validated providers immediately.
            </p>
          </div>
        </div>
      </BlockContainer>

      {(providerTypesQuery.isLoading || providersQuery.isLoading) && (
        <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Loading provider workspace...
        </div>
      )}

      {providerTypesQuery.error || providersQuery.error ? (
        <Alert variant="destructive">
          <AlertTitle>Unable to load provider settings</AlertTitle>
          <AlertDescription>
            {(providerTypesQuery.error as Error | null)?.message ||
              (providersQuery.error as Error | null)?.message}
          </AlertDescription>
        </Alert>
      ) : null}

      {!providerTypesQuery.isLoading && !providersQuery.isLoading ? (
        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.1fr)_minmax(360px,0.9fr)]">
          <div className="space-y-6">
            <ProviderTemplateGallery
              providerTypes={providerTypes}
              configuredProviders={providers}
              selectedProviderTypeId={activeProviderType?.id ?? selectedProviderTypeId}
              powerUserMode={powerUserMode}
              onPowerUserModeChange={setPowerUserMode}
              onSelect={(providerType) => {
                setSelectedProviderTypeId(providerType.id)
                setEditingProviderId(null)
                setSuccessProviderId(null)
              }}
            />

            {showModelPinsForProviderId ? (
              <ModelPinList
                providerId={showModelPinsForProviderId}
                providerName={
                  providers.find((provider) => provider.id === showModelPinsForProviderId)
                    ?.name || "Provider"
                }
                shouldHighlightPins={highlightPins}
              />
            ) : null}
          </div>

          <div className="space-y-6">
            <BlockContainer
              title="Configured providers"
              subtitle="Saved credentials, validation status, and entry points for further tuning."
              variant="card"
              density="default"
              bodyClassName="space-y-3"
            >
              {providers.length === 0 ? (
                <div className="rounded-xl border border-dashed px-4 py-8 text-center">
                  <p className="text-sm font-medium">No providers configured yet</p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Pick a template to create your first provider connection.
                  </p>
                </div>
              ) : (
                providers.map((provider) => {
                  const providerType = getProviderTypeName(provider, providerTypes)
                  const isActive = editingProviderId === provider.id

                  return (
                    <div
                      key={provider.id}
                      className={`rounded-xl border px-4 py-4 transition-colors ${
                        isActive ? "border-primary/40 bg-primary/5" : "bg-background/80"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="space-y-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="text-sm font-semibold">{provider.name}</p>
                            <ProviderStatusBadge
                              status={
                                provider.is_validated
                                  ? "verified"
                                  : provider.validation_error
                                    ? "failed"
                                    : "unknown"
                              }
                            />
                            {provider.is_default ? (
                              <Badge variant="secondary">Default</Badge>
                            ) : null}
                            {!provider.is_enabled ? (
                              <Badge variant="outline">Disabled</Badge>
                            ) : null}
                          </div>
                          <p className="text-xs text-muted-foreground">
                            {providerType?.display_name || providerType?.name || "Provider"}
                            {provider.base_url ? ` • ${formatBaseUrl(provider.base_url)}` : ""}
                          </p>
                          {provider.description ? (
                            <p className="text-sm text-muted-foreground">
                              {provider.description}
                            </p>
                          ) : null}
                          <div className="flex flex-wrap gap-2 pt-1">
                            <Badge variant="outline" className="text-[10px]">
                              {formatRelativeValidation(provider)}
                            </Badge>
                            <Badge variant="outline" className="text-[10px]">
                              {provider.available_models_cache?.length ?? 0} cached models
                            </Badge>
                            {isProviderStale(provider) ? (
                              <Badge variant="outline" className="text-[10px]">
                                Needs refresh
                              </Badge>
                            ) : null}
                          </div>
                          {provider.validation_error ? (
                            <p className="line-clamp-2 text-xs text-destructive">
                              {provider.validation_error}
                            </p>
                          ) : null}
                        </div>
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setEditingProviderId(provider.id)
                              setSelectedProviderTypeId(provider.alpha_provider_type_id)
                              setSuccessProviderId(null)
                            }}
                          >
                            <Pencil className="h-3.5 w-3.5" />
                            Edit
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setShowModelPinsForProviderId(provider.id)
                              setHighlightPins(false)
                            }}
                          >
                            <Sparkles className="h-3.5 w-3.5" />
                            Models
                          </Button>
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => {
                              if (
                                window.confirm(
                                  `Delete ${provider.name}? Agents using it may stop working.`,
                                )
                              ) {
                                deleteMutation.mutate(provider.id)
                              }
                            }}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  )
                })
              )}
            </BlockContainer>

            <UserAccessProviderForm
              providerType={activeProviderType}
              provider={selectedProvider}
              powerUserMode={powerUserMode}
              isSaving={isSaving}
              onCancelCreate={() => {
                setSelectedProviderTypeId(providerTypes[0]?.id ?? null)
                setEditingProviderId(null)
              }}
              onSubmit={async (payload) => {
                if (!activeProviderType && !selectedProvider) {
                  showErrorToast("Select a provider template first")
                  return
                }

                if (selectedProvider) {
                  await updateMutation.mutateAsync({
                    providerId: selectedProvider.id,
                    payload,
                  })
                  return
                }

                await createMutation.mutateAsync({
                  ...(payload as UserAccessProviderCreate),
                  alpha_provider_type_id: activeProviderType?.id,
                  owner_id: user?.id,
                })
              }}
            />

            {selectedProvider ? (
              <ValidationPanel
                provider={selectedProvider}
                providerTypeName={activeProviderType?.name || "default"}
                onValidated={(result: DetailedTestResult) => {
                  if (result.valid) {
                    setValidationResults((current) => ({
                      ...current,
                      [selectedProvider.id]: result,
                    }))
                    setSuccessProviderId(selectedProvider.id)
                    setShowModelPinsForProviderId(selectedProvider.id)
                  }
                }}
              />
            ) : (
              <BlockContainer
                title="Validation unlocks the next step"
                subtitle="Create the provider first, then run the detailed test to fetch models and account diagnostics."
                variant="card"
                density="default"
              >
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <ArrowRight className="h-4 w-4" />
                  New providers become editable and testable as soon as they are saved.
                </div>
              </BlockContainer>
            )}

            {selectedProvider && successProviderId === selectedProvider.id ? (
              <SetupSuccessPanel
                provider={selectedProvider}
                validationResult={validationResults[selectedProvider.id] ?? null}
                onBrowseModels={() => {
                  setShowModelPinsForProviderId(selectedProvider.id)
                  setHighlightPins(false)
                }}
                onPinFavorites={() => {
                  setShowModelPinsForProviderId(selectedProvider.id)
                  setHighlightPins(true)
                }}
                onAddAnother={() => {
                  setEditingProviderId(null)
                  setSuccessProviderId(null)
                }}
                onDismiss={() => setSuccessProviderId(null)}
              />
            ) : null}
          </div>
        </div>
      ) : null}
    </div>
  )
}
