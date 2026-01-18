/**
 * LLM Providers Settings Component
 *
 * Allows users to manage their LLM provider API keys and custom endpoints.
 * API keys are encrypted at rest in the backend.
 */
import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Loader2, Plus, TestTube, Trash2 } from "lucide-react"
import { useState } from "react"
import type { Resolver } from "react-hook-form"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { LlmProvidersService } from "@/client"
import type {
  UserLLMProviderCreate,
  UserLLMProviderPublic,
} from "@/client/types.gen"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

const providerTypes = [
  { value: "openai", label: "OpenAI", description: "GPT-4, GPT-3.5, etc." },
  { value: "anthropic", label: "Anthropic", description: "Claude models" },
  {
    value: "google",
    label: "Google (Gemini)",
    description: "Gemini Pro, etc.",
  },
  {
    value: "openai_compatible",
    label: "OpenAI Compatible",
    description: "Ollama, vLLM, Azure OpenAI, proxies",
  },
] as const

const formSchema = z.object({
  name: z.string().min(1, "Name is required").max(100),
  provider_type: z.enum(["openai", "anthropic", "google", "openai_compatible"]),
  api_key: z.string().min(1, "API key is required"),
  base_url: z.string().url("Must be a valid URL").optional().or(z.literal("")),
  description: z.string().max(500).optional(),
  is_default: z.boolean(),
  is_enabled: z.boolean(),
})

type FormData = z.infer<typeof formSchema>

const LLMProviders = () => {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false)
  const [testingProviderId, setTestingProviderId] = useState<string | null>(
    null,
  )

  // Fetch existing providers
  const { data: providersData, isLoading } = useQuery({
    queryKey: ["llm-providers"],
    queryFn: () => LlmProvidersService.listProviders(),
  })

  const providers = providersData?.data ?? []

  // Form setup - cast resolver to fix type inference issue with zodResolver + react-hook-form
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema) as Resolver<FormData>,
    mode: "onSubmit",
    defaultValues: {
      name: "",
      provider_type: "openai",
      api_key: "",
      base_url: "",
      description: "",
      is_default: false,
      is_enabled: true,
    },
  })

  const selectedProviderType = form.watch("provider_type")

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data: UserLLMProviderCreate) =>
      LlmProvidersService.createProvider({ requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Provider added successfully")
      setIsAddDialogOpen(false)
      form.reset()
      queryClient.invalidateQueries({ queryKey: ["llm-providers"] })
    },
    onError: handleError.bind(showErrorToast),
  })

  // Test connection mutation
  const testMutation = useMutation({
    mutationFn: (providerId: string) =>
      LlmProvidersService.testProvider({ providerId }),
    onSuccess: () => {
      showSuccessToast("Connection test successful!")
      queryClient.invalidateQueries({ queryKey: ["llm-providers"] })
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => setTestingProviderId(null),
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (providerId: string) =>
      LlmProvidersService.deleteProvider({ providerId }),
    onSuccess: () => {
      showSuccessToast("Provider deleted")
      queryClient.invalidateQueries({ queryKey: ["llm-providers"] })
    },
    onError: handleError.bind(showErrorToast),
  })

  const onSubmit = (data: FormData) => {
    const payload: UserLLMProviderCreate = {
      name: data.name,
      provider_type: data.provider_type,
      api_key: data.api_key,
      base_url: data.base_url || undefined,
      description: data.description || undefined,
      is_default: data.is_default,
      is_enabled: data.is_enabled,
    }
    createMutation.mutate(payload)
  }

  const handleTest = (providerId: string) => {
    setTestingProviderId(providerId)
    testMutation.mutate(providerId)
  }

  const handleDelete = (provider: UserLLMProviderPublic) => {
    if (window.confirm(`Delete "${provider.name}"? This cannot be undone.`)) {
      deleteMutation.mutate(provider.id)
    }
  }

  const getProviderLabel = (type: string) => {
    return providerTypes.find((p) => p.value === type)?.label ?? type
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">AI Providers</h3>
          <p className="text-sm text-muted-foreground">
            Configure your API keys for AI language models
          </p>
        </div>

        {/* Add Provider Dialog */}
        <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Add Provider
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Add LLM Provider</DialogTitle>
              <DialogDescription>
                Add your API key for an AI provider. Keys are encrypted at rest.
              </DialogDescription>
            </DialogHeader>

            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(onSubmit)}
                className="flex flex-col gap-4"
              >
                {/* Provider Type */}
                <FormField
                  control={form.control}
                  name="provider_type"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Provider Type</FormLabel>
                      <Select
                        onValueChange={field.onChange}
                        defaultValue={field.value}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select a provider" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {providerTypes.map((type) => (
                            <SelectItem key={type.value} value={type.value}>
                              <div className="flex flex-col">
                                <span>{type.label}</span>
                                <span className="text-xs text-muted-foreground">
                                  {type.description}
                                </span>
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {/* Name */}
                <FormField
                  control={form.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Name</FormLabel>
                      <FormControl>
                        <Input placeholder="My OpenAI Key" {...field} />
                      </FormControl>
                      <FormDescription>
                        A friendly name to identify this configuration
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {/* API Key */}
                <FormField
                  control={form.control}
                  name="api_key"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>API Key</FormLabel>
                      <FormControl>
                        <PasswordInput
                          placeholder="sk-..."
                          autoComplete="off"
                          {...field}
                        />
                      </FormControl>
                      <FormDescription>
                        Your API key will be encrypted before storage
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {/* Base URL (for OpenAI-compatible) */}
                {selectedProviderType === "openai_compatible" && (
                  <FormField
                    control={form.control}
                    name="base_url"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Base URL</FormLabel>
                        <FormControl>
                          <Input
                            placeholder="https://api.example.com/v1"
                            {...field}
                          />
                        </FormControl>
                        <FormDescription>
                          Custom endpoint URL (e.g., Ollama, Azure OpenAI)
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                )}

                {/* Description */}
                <FormField
                  control={form.control}
                  name="description"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Description (optional)</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="Personal account, work account, etc."
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {/* Is Default */}
                <FormField
                  control={form.control}
                  name="is_default"
                  render={({ field }) => (
                    <FormItem className="flex items-center justify-between rounded-lg border p-3">
                      <div className="space-y-0.5">
                        <FormLabel>Set as default</FormLabel>
                        <FormDescription>
                          Use this provider by default for{" "}
                          {getProviderLabel(selectedProviderType)}
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

                <DialogFooter className="pt-4">
                  <DialogClose asChild>
                    <Button type="button" variant="outline">
                      Cancel
                    </Button>
                  </DialogClose>
                  <LoadingButton
                    type="submit"
                    loading={createMutation.isPending}
                  >
                    Add Provider
                  </LoadingButton>
                </DialogFooter>
              </form>
            </Form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      )}

      {/* Empty state */}
      {!isLoading && providers.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <p className="text-muted-foreground mb-4">
              No AI providers configured yet
            </p>
            <Button variant="outline" onClick={() => setIsAddDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add your first provider
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Provider cards */}
      <div className="grid gap-4">
        {providers.map((provider) => (
          <Card key={provider.id}>
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    {provider.name}
                    {provider.is_default && (
                      <Badge variant="secondary" className="text-xs">
                        Default
                      </Badge>
                    )}
                    {!provider.is_enabled && (
                      <Badge variant="outline" className="text-xs">
                        Disabled
                      </Badge>
                    )}
                  </CardTitle>
                  <CardDescription className="mt-1">
                    {getProviderLabel(
                      provider.provider_type ?? "openai_compatible",
                    )}
                    {provider.base_url && (
                      <span className="ml-2 text-xs font-mono">
                        ({provider.base_url})
                      </span>
                    )}
                  </CardDescription>
                </div>

                {/* Test status indicator */}
                {provider.last_tested_at && (
                  <Badge
                    variant={
                      provider.last_test_success ? "default" : "destructive"
                    }
                    className="text-xs"
                  >
                    {provider.last_test_success ? "✓ Verified" : "✗ Failed"}
                  </Badge>
                )}
              </div>
            </CardHeader>

            <CardContent className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleTest(provider.id)}
                disabled={testingProviderId === provider.id}
              >
                {testingProviderId === provider.id ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : (
                  <TestTube className="h-4 w-4 mr-2" />
                )}
                Test Connection
              </Button>
              <Button
                variant="destructive"
                size="sm"
                onClick={() => handleDelete(provider)}
                disabled={deleteMutation.isPending}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}

export default LLMProviders
