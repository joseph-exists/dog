import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  ArrowRight,
  CheckCircle2,
  ChevronDown,
  KeyRound,
  Loader2,
  Plus,
  RefreshCcw,
} from "lucide-react"
import { useMemo, useRef, useState } from "react"
import { LlmProvidersService } from "@/client/sdk.gen"
import type {
  DetailedTestResult,
  LLMProviderTypePublic,
  UserAccessProviderCreate,
  UserAccessProviderPublic,
  UserAccessProviderUpdate,
} from "@/client/types.gen"
import { BlockContainer } from "@/components/Page/primitives"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import useAuth from "@/hooks/useAuth"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import { ConfiguredProviderCard } from "./Configured"
import { ModelPinList } from "./Display"
import { SetupSuccessPanel } from "./Flows"
import { UserAccessProviderForm, ValidationPanel } from "./Forms"
import { ProviderTemplateGallery } from "./Gallery"

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
  return providerTypes.find(
    (item) => item.id === provider.alpha_provider_type_id,
  )
}

export function UserAccessProvidersWorkspace() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const addProviderSectionRef = useRef<HTMLDivElement | null>(null)
  const [powerUserMode, setPowerUserMode] = useState(false)
  const [selectedProviderTypeId, setSelectedProviderTypeId] = useState<
    string | null
  >(null)
  const [editingProviderId, setEditingProviderId] = useState<string | null>(
    null,
  )
  const [showModelPinsForProviderId, setShowModelPinsForProviderId] = useState<
    string | null
  >(null)
  const [highlightPins, setHighlightPins] = useState(false)
  const [successProviderId, setSuccessProviderId] = useState<string | null>(
    null,
  )
  const [validationResults, setValidationResults] = useState<
    Record<string, DetailedTestResult>
  >({})
  const [openConfiguredProviderId, setOpenConfiguredProviderId] = useState<
    string | null
  >(null)
  const [yourProvidersOpen, setYourProvidersOpen] = useState(true)

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
    () =>
      providers.find((provider) => provider.id === editingProviderId) ?? null,
    [providers, editingProviderId],
  )
  const selectedProviderType = useMemo(() => {
    if (selectedProvider) {
      return getProviderTypeName(selectedProvider, providerTypes) ?? null
    }

    return (
      providerTypes.find(
        (providerType) => providerType.id === selectedProviderTypeId,
      ) ?? null
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
      setOpenConfiguredProviderId(provider.id)
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
      setOpenConfiguredProviderId(provider.id)
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
      setOpenConfiguredProviderId(null)
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
        (
          result,
        ): result is PromiseFulfilledResult<{
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

  const validateProviderMutation = useMutation({
    mutationFn: async (provider: UserAccessProviderPublic) => ({
      providerId: provider.id,
      result: await LlmProvidersService.testProviderDetailed({
        providerId: provider.id,
      }),
    }),
    onSuccess: ({ providerId, result }) => {
      queryClient.invalidateQueries({ queryKey: ["llm-providers"] })
      queryClient.invalidateQueries({
        queryKey: ["llm-catalog", "models-for-uap", providerId],
      })
      queryClient.invalidateQueries({ queryKey: ["llm-catalog", "models"] })

      setValidationResults((current) => ({
        ...current,
        [providerId]: result,
      }))

      if (result.valid) {
        showSuccessToast("Provider validated and models fetched")
        setSuccessProviderId(providerId)
        setShowModelPinsForProviderId(providerId)
      } else {
        showErrorToast(result.error || "Validation failed")
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
              {providers.filter((provider) => provider.is_validated).length}{" "}
              validated
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
                addProviderSectionRef.current?.scrollIntoView({
                  behavior: "smooth",
                  block: "start",
                })
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
              Choose a template, verify it, then pin the models you actually
              use.
            </p>
          </div>
          <div className="rounded-xl border bg-background/70 p-4">
            <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
              Power controls
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              Advanced transport settings stay available, but tucked behind a
              dedicated section.
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
        <div className="space-y-6">
          <BlockContainer
            title="Your providers"
            subtitle="Saved connections, validation health, and model entry points."
            variant="card"
            density="default"
            headerActions={
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setYourProvidersOpen((open) => !open)}
                aria-expanded={yourProvidersOpen}
              >
                <ChevronDown
                  className={`h-4 w-4 transition-transform ${
                    yourProvidersOpen ? "rotate-180" : ""
                  }`}
                />
                {yourProvidersOpen ? "Minimize" : "Expand"}
              </Button>
            }
            bodyClassName="space-y-3"
          >
            {yourProvidersOpen ? (
              providers.length === 0 ? (
                <div className="rounded-xl border border-dashed px-4 py-8 text-center">
                  <p className="text-sm font-medium">
                    No providers configured yet
                  </p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Pick a template to create your first provider connection.
                  </p>
                </div>
              ) : (
                providers.map((provider) => {
                  const providerType = getProviderTypeName(
                    provider,
                    providerTypes,
                  )
                  const isActive = editingProviderId === provider.id

                  return (
                    <ConfiguredProviderCard
                      key={provider.id}
                      provider={provider}
                      providerType={providerType ?? null}
                      isActive={isActive}
                      isOpen={
                        openConfiguredProviderId === provider.id || isActive
                      }
                      isStale={isProviderStale(provider)}
                      validationLabel={formatRelativeValidation(provider)}
                      baseUrlLabel={formatBaseUrl(provider.base_url)}
                      onToggleOpen={() =>
                        setOpenConfiguredProviderId((current) =>
                          current === provider.id ? null : provider.id,
                        )
                      }
                      onEdit={() => {
                        setEditingProviderId(provider.id)
                        setOpenConfiguredProviderId(provider.id)
                        setSelectedProviderTypeId(
                          provider.alpha_provider_type_id,
                        )
                        setSuccessProviderId(null)
                      }}
                      onManageModels={() => {
                        setShowModelPinsForProviderId(provider.id)
                        setHighlightPins(false)
                      }}
                      onValidate={() =>
                        validateProviderMutation.mutate(provider)
                      }
                      onDelete={() => {
                        if (
                          window.confirm(
                            `Delete ${provider.name}? Agents using it may stop working.`,
                          )
                        ) {
                          deleteMutation.mutate(provider.id)
                        }
                      }}
                    />
                  )
                })
              )
            ) : (
              <div className="flex flex-wrap gap-2">
                <Badge variant="secondary">
                  {providers.length} saved provider
                  {providers.length === 1 ? "" : "s"}
                </Badge>
                <Badge variant="outline">
                  {providers.filter((provider) => provider.is_validated).length}{" "}
                  validated
                </Badge>
                {staleProviders.length > 0 ? (
                  <Badge variant="outline">{staleProviders.length} stale</Badge>
                ) : null}
              </div>
            )}
          </BlockContainer>

          {showModelPinsForProviderId ? (
            <ModelPinList
              providerId={showModelPinsForProviderId}
              providerName={
                providers.find(
                  (provider) => provider.id === showModelPinsForProviderId,
                )?.name || "Provider"
              }
              shouldHighlightPins={highlightPins}
            />
          ) : null}

          <div ref={addProviderSectionRef} className="space-y-6">
            <ProviderTemplateGallery
              providerTypes={providerTypes}
              configuredProviders={providers}
              selectedProviderTypeId={
                selectedProvider ? null : selectedProviderTypeId
              }
              powerUserMode={powerUserMode}
              onPowerUserModeChange={setPowerUserMode}
              onSelect={(providerType) => {
                setSelectedProviderTypeId(providerType.id)
                setEditingProviderId(null)
                setSuccessProviderId(null)
              }}
            />

            <UserAccessProviderForm
              providerType={activeProviderType}
              provider={selectedProvider}
              powerUserMode={powerUserMode}
              isSaving={isSaving}
              onCancelCreate={() => {
                setSelectedProviderTypeId(null)
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
          </div>

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
                New providers become editable and testable as soon as they are
                saved.
              </div>
            </BlockContainer>
          )}
        </div>
      ) : null}
    </div>
  )
}
