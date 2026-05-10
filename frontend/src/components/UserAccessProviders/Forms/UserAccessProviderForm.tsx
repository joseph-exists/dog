import { zodResolver } from "@hookform/resolvers/zod"
import { Wand2 } from "lucide-react"
import { useEffect, useState } from "react"
import type { Resolver } from "react-hook-form"
import { useForm } from "react-hook-form"
import { z } from "zod"
import type {
  LLMProviderTypePublic,
  UserAccessProviderCreate,
  UserAccessProviderPublic,
  UserAccessProviderUpdate,
} from "@/client/types.gen"
import { BlockContainer } from "@/components/Page/primitives"
import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import { PasswordInput } from "@/components/ui/password-input"
import { Switch } from "@/components/ui/switch"
import { Textarea } from "@/components/ui/textarea"
import { AdapterConfigSection } from "./AdapterConfigSection"
import { ProviderConfigFields } from "./ProviderConfigFields"

const formSchema = z.object({
  name: z.string().min(1, "Name is required").max(100),
  api_key: z.string().max(500),
  base_url: z.string().url("Must be a valid URL").or(z.literal("")),
  description: z.string().max(500),
  is_default: z.boolean(),
  is_enabled: z.boolean(),
  timeout_seconds: z.coerce.number().min(1).max(600),
  max_retries: z.coerce.number().min(0).max(10),
  retry_delay_ms: z.coerce.number().min(0).max(60000),
  proxy_url: z.string().url("Must be a valid URL").or(z.literal("")),
  custom_headers_json: z.string(),
})

export type UserAccessProviderFormValues = z.infer<typeof formSchema>

interface UserAccessProviderFormProps {
  providerType: LLMProviderTypePublic | null
  provider?: UserAccessProviderPublic | null
  powerUserMode: boolean
  isSaving: boolean
  onSubmit: (
    payload: UserAccessProviderCreate | UserAccessProviderUpdate,
  ) => Promise<void>
  onCancelCreate: () => void
}

function parseJsonObject(raw: string, fieldName: string) {
  if (!raw.trim()) {
    return null
  }

  try {
    const parsed = JSON.parse(raw) as unknown
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      return parsed as Record<string, unknown>
    }
    throw new Error("Expected a JSON object")
  } catch {
    throw new Error(`${fieldName} must be valid JSON object`)
  }
}

function buildDefaultName(providerType: LLMProviderTypePublic | null) {
  if (!providerType) {
    return ""
  }

  return `${providerType.display_name || providerType.name} workspace`
}

function providerTypeRequiresApiKey(
  providerType: LLMProviderTypePublic | null,
) {
  const normalizedName =
    `${providerType?.display_name || providerType?.name || ""}`.toLowerCase()
  return ["openai", "anthropic", "google", "gemini"].some((token) =>
    normalizedName.includes(token),
  )
}

export function UserAccessProviderForm({
  providerType,
  provider,
  powerUserMode,
  isSaving,
  onSubmit,
  onCancelCreate,
}: UserAccessProviderFormProps) {
  const [providerConfig, setProviderConfig] = useState<Record<string, unknown>>(
    () => (provider?.provider_config as Record<string, unknown>) ?? {},
  )
  const [jsonError, setJsonError] = useState<string | null>(null)

  const form = useForm<UserAccessProviderFormValues>({
    resolver: zodResolver(formSchema) as Resolver<UserAccessProviderFormValues>,
    defaultValues: {
      name: provider?.name || buildDefaultName(providerType),
      api_key: "",
      base_url: provider?.base_url || providerType?.default_base_url || "",
      description: provider?.description || "",
      is_default: provider?.is_default ?? false,
      is_enabled: provider?.is_enabled ?? true,
      timeout_seconds: provider?.timeout_seconds ?? 30,
      max_retries: provider?.max_retries ?? 3,
      retry_delay_ms: provider?.retry_delay_ms ?? 1000,
      proxy_url: provider?.proxy_url || "",
      custom_headers_json: JSON.stringify(
        provider?.custom_headers ?? {},
        null,
        2,
      ),
    },
  })

  useEffect(() => {
    form.reset({
      name: provider?.name || buildDefaultName(providerType),
      api_key: "",
      base_url: provider?.base_url || providerType?.default_base_url || "",
      description: provider?.description || "",
      is_default: provider?.is_default ?? false,
      is_enabled: provider?.is_enabled ?? true,
      timeout_seconds: provider?.timeout_seconds ?? 30,
      max_retries: provider?.max_retries ?? 3,
      retry_delay_ms: provider?.retry_delay_ms ?? 1000,
      proxy_url: provider?.proxy_url || "",
      custom_headers_json: JSON.stringify(
        provider?.custom_headers ?? {},
        null,
        2,
      ),
    })
    setProviderConfig(
      (provider?.provider_config as Record<string, unknown>) ?? {},
    )
    setJsonError(null)
  }, [form, provider, providerType])

  const handleSubmit = form.handleSubmit(async (values) => {
    setJsonError(null)

    try {
      if (
        !provider &&
        providerTypeRequiresApiKey(providerType) &&
        !values.api_key.trim()
      ) {
        form.setError("api_key", {
          type: "manual",
          message: "API key is required for this provider",
        })
        return
      }

      const customHeaders = parseJsonObject(
        values.custom_headers_json,
        "Custom headers",
      )

      const payload = {
        name: values.name,
        base_url: values.base_url || providerType?.default_base_url || null,
        description: values.description || null,
        is_default: values.is_default,
        is_enabled: values.is_enabled,
        timeout_seconds: values.timeout_seconds,
        max_retries: values.max_retries,
        retry_delay_ms: values.retry_delay_ms,
        proxy_url: values.proxy_url || null,
        custom_headers: customHeaders,
        provider_config:
          Object.keys(providerConfig).length > 0 ? providerConfig : null,
        ...(values.api_key ? { api_key: values.api_key } : {}),
      }

      await onSubmit(payload)
    } catch (error) {
      setJsonError(error instanceof Error ? error.message : "Invalid form data")
    }
  })

  const title = provider
    ? `Edit ${provider.name}`
    : providerType
      ? `Create new ${providerType.display_name || providerType.name} provider`
      : "Select a provider type"

  return (
    <BlockContainer
      title={title}
      subtitle={
        provider
          ? "Update this saved provider. Save changes before validating again."
          : providerType
            ? powerUserMode
              ? "Advanced setup is enabled. Adapter and transport controls remain available below."
              : "Add credentials using the template defaults, then validate the connection."
            : "Choose a provider type from Add a provider to begin setup."
      }
      variant="card"
      density="comfortable"
      headerActions={
        !provider && providerType ? (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => {
              form.setValue("name", buildDefaultName(providerType))
              form.setValue("base_url", providerType.default_base_url || "")
            }}
          >
            <Wand2 className="h-3.5 w-3.5" />
            Reset to template
          </Button>
        ) : null
      }
      bodyClassName="space-y-5"
    >
      <Form {...form}>
        <form className="space-y-5" onSubmit={handleSubmit}>
          {!providerType && !provider ? (
            <div className="rounded-lg border border-dashed px-4 py-8 text-center">
              <p className="text-sm font-medium">No provider type selected</p>
              <p className="mt-1 text-sm text-muted-foreground">
                Pick a template from Add a provider to create a saved
                connection.
              </p>
            </div>
          ) : null}

          {providerType || provider ? (
            <>
              <div className="grid gap-4 md:grid-cols-2">
                <FormField
                  control={form.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Name</FormLabel>
                      <FormControl>
                        <Input placeholder="Production OpenAI" {...field} />
                      </FormControl>
                      <FormDescription>
                        Friendly label used in selectors and setup flows.
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="base_url"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Base URL</FormLabel>
                      <FormControl>
                        <Input
                          placeholder={
                            providerType?.default_base_url ||
                            "https://api.openai.com/v1"
                          }
                          {...field}
                        />
                      </FormControl>
                      <FormDescription>
                        Leave the template default unless your account uses a
                        custom endpoint.
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={form.control}
                name="api_key"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      {provider ? "Replace API key" : "API key"}
                    </FormLabel>
                    <FormControl>
                      <PasswordInput
                        placeholder="sk-..."
                        autoComplete="off"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>
                      {provider
                        ? "Leave blank to keep the current encrypted key."
                        : "Stored server-side and used only for this provider configuration."}
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <ProviderConfigFields
                providerType={providerType}
                values={providerConfig}
                onChange={(key, value) =>
                  setProviderConfig((current) => ({
                    ...current,
                    [key]: value,
                  }))
                }
              />

              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Description</FormLabel>
                    <FormControl>
                      <Textarea
                        className="min-h-24"
                        placeholder="What this provider is for, who owns it, or when to use it."
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="grid gap-3 md:grid-cols-2">
                <FormField
                  control={form.control}
                  name="is_default"
                  render={({ field }) => (
                    <FormItem className="flex items-center justify-between rounded-lg border p-3">
                      <div className="space-y-0.5">
                        <FormLabel>Default provider</FormLabel>
                        <FormDescription>
                          Prefer this provider in new workflows.
                        </FormDescription>
                      </div>
                      <FormControl>
                        <Switch
                          checked={field.value}
                          onCheckedChange={field.onChange}
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="is_enabled"
                  render={({ field }) => (
                    <FormItem className="flex items-center justify-between rounded-lg border p-3">
                      <div className="space-y-0.5">
                        <FormLabel>Enabled</FormLabel>
                        <FormDescription>
                          Disable it without deleting the saved configuration.
                        </FormDescription>
                      </div>
                      <FormControl>
                        <Switch
                          checked={field.value}
                          onCheckedChange={field.onChange}
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />
              </div>

              <AdapterConfigSection form={form} />

              {jsonError ? (
                <p className="text-sm text-destructive">{jsonError}</p>
              ) : null}

              <div className="flex items-center justify-between gap-3">
                {!provider ? (
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={onCancelCreate}
                  >
                    Clear draft
                  </Button>
                ) : (
                  <span className="text-xs text-muted-foreground">
                    Save changes before re-running validation.
                  </span>
                )}
                <LoadingButton type="submit" loading={isSaving}>
                  {provider ? "Save changes" : "Create provider"}
                </LoadingButton>
              </div>
            </>
          ) : null}
        </form>
      </Form>
    </BlockContainer>
  )
}
