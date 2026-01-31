/**
 * User Access Providers Settings Component
 *
 * PURPOSE: Manage user's API access credentials (UserAccessProvider entities)
 *
 * ARCHITECTURAL CONTEXT - Three-Way Binding:
 * ==========================================
 *
 * UserAccessProvider is ONE PART of a three-way binding required for agents:
 *
 *   UserAgentConfig requires THREE aligned components:
 *     1. user_access_provider (UUID) → UserAccessProvider (WHERE + WITH WHAT)
 *     2. provider_type (string)      → LLMProviderType (HOW - API format)
 *     3. model_name (string)         → Model identifier (WHAT)



tinyfoot=# \d user_access_provider
                       Table "public.user_access_provider"
         Column         |          Type          | Collation | Nullable | Default 
------------------------+------------------------+-----------+----------+---------
 base_url               | character varying(100) |           |          | 
 this is the url used to connect to the user access provider's API (beans-ai.com/api/v1/)

 name                   | character varying(100) |           | not null | 
friendly name of the UAP given by the user to identify it - does not need to map to anything, user-only
 is_enabled             | boolean                |           | not null | 
users can enable and disable access providers - we can also disable user access providers if we need to.
 is_default             | boolean                |           | not null | 
is this the first one in the list when the user creates an agent? is this the default user access provider for that user?
 is_validated           | boolean                |           | not null | 
has the user run a test with the api?
 description            | character varying(500) |           |          | 
user description - we/system don't care about it.
 id                     | uuid                   |           | not null | 
uuid on create
 user_id                | uuid                   |           | not null | 
who made/owns the UAP
 provider_type_multiple | boolean                |           | not null | 
currently not used - here for test purposes
 alpha_provider_type_id | uuid                   |           | not null | 
this UUID is a FK reference on provider_type(id).

where provider_type is:
  name  | details   | validated | is_system |  id                  
-------------------------+-------------------------------------------------
 openai   | OpenAI models  | t | t | 673f1787-8474-4e1c-986c-8e19f14c989c



Indexes (for user access provider)
    "user_access_provider_pkey" PRIMARY KEY, btree (id)
    "ix_user_access_provider_alpha_provider_type_id" btree (alpha_provider_type_id)
    "ix_user_access_provider_user_id" btree (user_id)
Foreign-key constraints:
    "user_access_provider_alpha_provider_type_id_fkey" FOREIGN KEY (alpha_provider_type_id) REFERENCES provider_type(id)
    "user_access_provider_user_id_fkey" FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE
Referenced by:
    TABLE "room_participant_bindings" CONSTRAINT "room_participant_bindings_user_access_provider_id_fkey" FOREIGN KEY (user_access_provider_id) REFERENCES user_access_provider(id

 */

import { zodResolver } from "@hookform/resolvers/zod"
import { Loader2, Plus, TestTube, Trash2 } from "lucide-react"
import { useState } from "react"
import type { Resolver } from "react-hook-form"
import { useForm } from "react-hook-form"
import { z } from "zod"

// ============================================================================
// Service Layer Imports - Use hooks and services, not direct client
// ============================================================================

import { useLlmProviders } from "@/hooks/useLlmProviders"
import { UserAccessProviderService } from "@/services/userAccessProviderService"
import type { UserAccessProviderViewModel } from "@/services/userAccessProviderService"

// ============================================================================
// UI Component Imports
// ============================================================================

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
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
import { Switch } from "@/components/ui/switch"
import { showErrorToast } from "@/hooks/useCustomToast"

// ============================================================================
// Form Validation Schema
// ============================================================================

/**
 * UserAccessProvider creation form schema
 *
 * NOTE: No provider_type field - that's configured at the AgentConfig level!
 *
 * Fields:
 * - name: User's friendly identifier for this credential set
 * - api_key: Encrypted API key (required)
 * - base_url: Optional custom endpoint (e.g., Ollama, Azure OpenAI)
 * - description: Optional notes
 * - is_default: Whether this is the user's default provider
 * - is_enabled: Whether this provider is active
 */
const formSchema = z.object({
  name: z.string().min(1, "Name is required").max(100),
  api_key: z.string().min(1, "API key is required"),
  base_url: z.string().url("Must be a valid URL").optional().or(z.literal("")),
  description: z.string().max(500).optional().or(z.literal("")),
  is_default: z.boolean().default(false),
  is_enabled: z.boolean().default(true),
})

type FormData = z.infer<typeof formSchema>

// ============================================================================
// Component
// ============================================================================

const UserAccessProviders = () => {
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false)
  const [testingProviderId, setTestingProviderId] = useState<string | null>(null)

  // ==========================================================================
  // Data Fetching via useLlmProviders Hook
  // ==========================================================================
  //
  // This hook wraps userAccessProviderService and provides:
  // - Automatic query caching (TanStack Query)
  // - Computed fields (usableProviders, enabledProviders)
  // - Mutation helpers (create, update, delete, test)
  // - Loading and error states
  //
  // Using the hook instead of direct service calls ensures:
  // - Consistent query keys across the app
  // - Automatic cache invalidation
  // - Proper error handling with toasts
  // ==========================================================================

  const {
    providers,
    isLoading,
    error,
    createProvider,
    deleteProvider,
    testProvider,
    isCreating,
    isDeleting,
    isTesting,
  } = useLlmProviders()

  // ==========================================================================
  // Form Setup
  // ==========================================================================

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema) as Resolver<FormData>,
    mode: "onSubmit",
    defaultValues: {
      name: "",
      api_key: "",
      base_url: "",
      description: "",
      is_default: false,
      is_enabled: true,
    },
  })

  // ==========================================================================
  // Form Submission Handler
  // ==========================================================================
  //
  // Three-Way Binding Note:
  // This creates a UserAccessProvider (credentials + endpoint).
  // The provider_type and model_name are NOT specified here -
  // they will be specified when creating/configuring an AgentConfig
  // that uses this UserAccessProvider.
  // ==========================================================================

  const onSubmit = async (data: FormData) => {
    // Client-side validation using service utility
    const validation = UserAccessProviderService.validateProviderConfig(data)

    if (!validation.is_valid) {
      validation.errors.forEach((err) => showErrorToast(err))
      return
    }

    // Show warnings (non-blocking)
    validation.warnings.forEach((warn) => {
      console.warn("UserAccessProvider validation warning:", warn)
    })

    try {
      await createProvider({
        name: data.name,
        api_key: data.api_key,
        base_url: data.base_url || undefined,
        description: data.description || undefined,
        is_default: data.is_default,
        is_enabled: data.is_enabled,
      })

      // Success - hook already showed toast
      setIsAddDialogOpen(false)
      form.reset()
    } catch (err) {
      // Error already handled by hook (toast shown)
      console.error("Failed to create provider:", err)
    }
  }

  // ==========================================================================
  // Test Connection Handler
  // ==========================================================================
  //
  // Note: Backend endpoint for testing not yet implemented.
  // When implemented, this will:
  // 1. Make a test request to the provider's base_url with api_key
  // 2. Update last_tested_at and last_test_success fields
  // 3. Return success/failure status
  // ==========================================================================

  const handleTest = async (providerId: string) => {
    setTestingProviderId(providerId)
    try {
      await testProvider(providerId)
      // Success toast shown by hook
    } catch (err) {
      // Error toast shown by hook
      console.error("Provider test failed:", err)
    } finally {
      setTestingProviderId(null)
    }
  }

  // ==========================================================================
  // Delete Handler
  // ==========================================================================

  const handleDelete = async (provider: UserAccessProviderViewModel) => {
    if (
      window.confirm(
        `Delete "${provider.name}"?\n\nThis cannot be undone. Any agents using this provider will fail at runtime.`,
      )
    ) {
      try {
        await deleteProvider(provider.id)
        // Success toast shown by hook
      } catch (err) {
        // Error toast shown by hook
        console.error("Failed to delete provider:", err)
      }
    }
  }

  // ==========================================================================
  // Render
  // ==========================================================================

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">API Access Providers</h3>
          <p className="text-sm text-muted-foreground">
            Configure your API credentials for connecting to LLM services
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
              <DialogTitle>Add API Access Provider</DialogTitle>
              <DialogDescription>
                Add your API credentials. Keys are encrypted at rest and in transit.
              </DialogDescription>
            </DialogHeader>

            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(onSubmit)}
                className="flex flex-col gap-4"
              >
                {/* Name */}
                <FormField
                  control={form.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Name</FormLabel>
                      <FormControl>
                        <Input placeholder="My OpenAI API Key" {...field} />
                      </FormControl>
                      <FormDescription>
                        A friendly name to identify this API credential
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

                {/* Base URL (Optional) */}
                <FormField
                  control={form.control}
                  name="base_url"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Base URL (Optional)</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="https://api.openai.com/v1"
                          {...field}
                        />
                      </FormControl>
                      <FormDescription>
                        Custom endpoint URL. Leave empty for default endpoints.
                        Common uses: Ollama, Azure OpenAI, OpenAI-compatible services.
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

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
                          Use this provider by default when creating new agents
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
                  <LoadingButton type="submit" loading={isCreating}>
                    Add Provider
                  </LoadingButton>
                </DialogFooter>
              </form>
            </Form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Error Display */}
      {error && (
        <Alert variant="destructive">
          <AlertTitle>Error loading providers</AlertTitle>
          <AlertDescription>{error.message}</AlertDescription>
        </Alert>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      )}

      {/* Empty State */}
      {!isLoading && providers.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <p className="text-muted-foreground mb-4">
              No API providers configured yet
            </p>
            <Button variant="outline" onClick={() => setIsAddDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add your first provider
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Provider Cards */}
      <div className="grid gap-4">
        {providers.map((provider) => (
          <Card key={provider.id}>
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <CardTitle className="flex items-center gap-2 flex-wrap">
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
                    {provider.status === "verified" && (
                      <Badge variant="default" className="text-xs">
                        ✓ Verified
                      </Badge>
                    )}
                    {provider.status === "failed" && (
                      <Badge variant="destructive" className="text-xs">
                        ✗ Failed
                      </Badge>
                    )}
                  </CardTitle>
                  <CardDescription className="mt-1">
                    {/* Show description if available */}
                    {provider.description && (
                      <span className="block">{provider.description}</span>
                    )}
                    {/* Show custom endpoint if configured */}
                    {provider.base_url && (
                      <span className="block mt-1 text-xs font-mono text-muted-foreground">
                        Endpoint: {provider.base_url}
                      </span>
                    )}
                    {/* Show default endpoint message if no custom URL */}
                    {!provider.base_url && !provider.description && (
                      <span className="block">API Access Provider</span>
                    )}
                  </CardDescription>
                </div>
              </div>
            </CardHeader>

            <CardContent className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleTest(provider.id)}
                disabled={testingProviderId === provider.id || isTesting}
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
                disabled={isDeleting}
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

export default UserAccessProviders
