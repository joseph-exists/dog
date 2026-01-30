# UserAccessProviders.tsx - Architectural Review

**File**: `frontend/src/components/UserSettings/UserAccessProviders.tsx`
**Status**: ⚠️ **CRITICAL - Complete refactor required**
**Architecture**: Misaligned with new three-way binding pattern

---

## Executive Summary

This component has **fundamental architectural misalignment** with the new service layer. It conflates:
- UserAccessProvider (user's API credentials) with
- LLMProviderType (API message format specification) with
- Catalog providers (system-wide provider registry)

**Key Issues**:
1. ❌ Imports services from `@/client` instead of service layer
2. ❌ Uses non-existent types (`UserLLMProviderCreate`, `UserLLMProviderPublic`)
3. ❌ Direct API calls instead of using hooks (`useLlmProviders`)
4. ❌ Tries to manage "provider_type" on UserAccessProvider (doesn't exist)
5. ❌ Calls `LlmCatalogService.listProviders()` which doesn't exist in minimal implementation
6. ❌ Complex provider_type_id mapping logic for removed fields
7. ❌ Missing proper form validation for new schema

---

## Understanding UserAccessProvider

**What UserAccessProvider IS**:
```typescript
{
  id: string                    // UUID
  name: string                  // User's friendly name ("My OpenAI API Key")
  base_url: string | null       // Custom endpoint (e.g., "https://api.openai.com/v1")
  api_key: string               // User's API key (encrypted)
  is_enabled: boolean           // Whether this provider is active
  is_validated: boolean         // Whether backend has validated it
  is_default: boolean           // Whether this is user's default
  description: string | null    // User's notes

  // Computed
  status: "verified" | "failed" | "unknown"
  is_usable: boolean
}
```

**What UserAccessProvider is NOT**:
- ❌ NOT associated with a specific LLMProviderType (openai, anthropic, etc.)
- ❌ NOT part of the system catalog
- ❌ DOES NOT have `provider_type` or `provider_type_id` fields
- ❌ DOES NOT determine which API format to use

**The Three-Way Binding**:
```
UserAgentConfig (the thing that uses all three):
├─ user_access_provider: UUID → UserAccessProvider (WHERE + WITH WHAT)
├─ provider_type: string      → LLMProviderType (HOW - API format)
└─ model_name: string         → Model identifier (WHAT)
```

UserAccessProvider is just credentials + endpoint. The agent config decides what API format and model to use with those credentials.

---

## CRITICAL ISSUES

### 🔴 CRITICAL 1: Wrong Service Imports

**Current (Lines 15, 59)**:
```typescript
import { LlmCatalogService, LlmProvidersService } from "@/client"
import type { UserAccessProviderCreate, UserAccessProviderPublic } from "@/client"
```

**Problem**:
- Importing from auto-generated client instead of service layer
- Service layer provides ViewModels, validation, and proper abstractions

**Fix**:
```typescript
// Import services (not client)
import { UserAccessProviderService } from "@/services/userAccessProviderService"
import type {
  CreateUserAccessProviderInput,
  UpdateUserAccessProviderInput,
  UserAccessProviderViewModel
} from "@/services/userAccessProviderService"

// Import hook (preferred over direct service calls)
import { useLlmProviders } from "@/hooks/useLlmProviders"
```

---

### 🔴 CRITICAL 2: Non-existent Types

**Current (Lines 134, 174, 191)**:
```typescript
const createMutation = useMutation({
  mutationFn: (data: UserLLMProviderCreate) =>  // ❌ Type doesn't exist
    LlmProvidersService.createProvider({ requestBody: data }),
})

const payload: UserLLMProviderCreate = {  // ❌ Type doesn't exist
  name: data.name,
  provider_type_id: providerTypeId,  // ❌ Field doesn't exist
  // ...
}

const handleDelete = (provider: UserLLMProviderPublic) => {  // ❌ Type doesn't exist
  // ...
}
```

**Problem**:
- `UserLLMProviderCreate` doesn't exist - was renamed to `CreateUserAccessProviderInput`
- `UserLLMProviderPublic` doesn't exist - transformed to `UserAccessProviderViewModel`
- `provider_type_id` field doesn't exist on UserAccessProvider

**Fix**:
```typescript
import type {
  CreateUserAccessProviderInput,
  UserAccessProviderViewModel
} from "@/services/userAccessProviderService"

const createMutation = useMutation({
  mutationFn: (data: CreateUserAccessProviderInput) =>
    UserAccessProviderService.createProvider(data),
})

const payload: CreateUserAccessProviderInput = {
  name: data.name,
  api_key: data.api_key,
  base_url: data.base_url || undefined,
  description: data.description || undefined,
  is_default: data.is_default,
  is_enabled: data.is_enabled,
  // NO provider_type or provider_type_id
}

const handleDelete = (provider: UserAccessProviderViewModel) => {
  // ...
}
```

---

### 🔴 CRITICAL 3: Should Use useLlmProviders Hook

**Current (Lines 108-166)**:
```typescript
// Direct TanStack Query + service calls
const { data: providersData, isLoading } = useQuery({
  queryKey: ["llm-providers"],
  queryFn: () => LlmProvidersService.listProviders(),
})

const createMutation = useMutation({
  mutationFn: (data: UserLLMProviderCreate) =>
    LlmProvidersService.createProvider({ requestBody: data }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["llm-providers"] })
  },
})

const deleteMutation = useMutation({
  mutationFn: (providerId: string) =>
    LlmProvidersService.deleteProvider({ providerId }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["llm-providers"] })
  },
})
```

**Problem**:
- Reimplementing logic already in `useLlmProviders` hook
- Using wrong query keys
- Using wrong types
- Missing computed fields (usableProviders, enabledProviders, etc.)

**Fix**:
```typescript
// Use the hook - it handles everything
const {
  providers,
  enabledProviders,
  usableProviders,
  defaultProvider,
  isLoading,
  error,
  createProvider,
  updateProvider,
  deleteProvider,
  testProvider,
  setDefaultProvider,
  isCreating,
  isDeleting,
  isTesting,
} = useLlmProviders()

// Form submission becomes:
const onSubmit = async (data: FormData) => {
  try {
    await createProvider({
      name: data.name,
      api_key: data.api_key,
      base_url: data.base_url || undefined,
      description: data.description || undefined,
      is_default: data.is_default,
      is_enabled: data.is_enabled,
    })
    setIsAddDialogOpen(false)
    form.reset()
  } catch (err) {
    // Hook handles error toasts
  }
}

// Delete becomes:
const handleDelete = async (provider: UserAccessProviderViewModel) => {
  if (window.confirm(`Delete "${provider.name}"? This cannot be undone.`)) {
    await deleteProvider(provider.id)
  }
}

// Test becomes:
const handleTest = async (providerId: string) => {
  setTestingProviderId(providerId)
  try {
    await testProvider(providerId)
  } finally {
    setTestingProviderId(null)
  }
}
```

---

### 🔴 CRITICAL 4: Wrong Catalog Service Usage

**Current (Lines 81-105)**:
```typescript
const { data: catalogProvidersData } = useQuery({
  queryKey: ["llm-catalog-providers"],
  queryFn: () => LlmCatalogService.listProviders({ limit: 200 }),  // ❌ Method doesn't exist
})

const providerTypeIdByName = useMemo(() => {
  const mapping: Record<string, string> = {}
  for (const provider of catalogProvidersData?.data ?? []) {
    if (provider.provider_type && provider.provider_type_id) {  // ❌ Fields don't exist
      mapping[provider.provider_type] = provider.provider_type_id
    }
  }
  return mapping
}, [catalogProvidersData])
```

**Problem**:
- `LlmCatalogService.listProviders()` doesn't exist - minimal implementation has no provider CRUD
- Catalog service is read-only and not yet fully implemented
- `provider_type_id` doesn't exist in new architecture
- UserAccessProvider doesn't have a type association

**Fix - Remove Entirely**:
```typescript
// UserAccessProvider doesn't need provider type selection
// Provider type is specified at the AgentConfig level, not here

// If you need to show known provider types for informational purposes:
import { LlmCatalogService } from "@/services/llmCatalogService"

const knownTypes = LlmCatalogService.getKnownProviderTypes()
// Returns: ["openai", "anthropic", "google", "azure_openai", "ollama"]

const getLabel = (type: string) => LlmCatalogService.getProviderTypeLabel(type)
// Returns: "OpenAI", "Anthropic", etc.
```

---

### 🔴 CRITICAL 5: Form Schema Wrong Fields

**Current (Lines 62-69, 120-127)**:
```typescript
const formSchema = z.object({
  name: z.string().min(1, "Name is required").max(100),
  api_key: z.string().min(1, "API key is required"),
  base_url: z.string().url("Must be a valid URL").optional().or(z.literal("")),
  description: z.string().max(500).optional(),
  is_default: z.boolean(),
  is_enabled: z.boolean(),
  // Missing: validation for base_url being optional
})

// Default values include non-existent field:
defaultValues: {
  name: "",
  provider_type: "openai",  // ❌ UserAccessProvider doesn't have this field
  api_key: "",
  base_url: "",
  description: "",
  is_default: false,
  is_enabled: true,
}
```

**Problem**:
- Includes `provider_type` which doesn't exist on UserAccessProvider
- Missing proper validation for optional fields

**Fix**:
```typescript
const formSchema = z.object({
  name: z.string().min(1, "Name is required").max(100),
  api_key: z.string().min(1, "API key is required"),
  base_url: z.string().url("Must be a valid URL").optional().or(z.literal("")),
  description: z.string().max(500).optional().or(z.literal("")),
  is_default: z.boolean().default(false),
  is_enabled: z.boolean().default(true),
})

type FormData = z.infer<typeof formSchema>

// Default values:
defaultValues: {
  name: "",
  api_key: "",
  base_url: "",
  description: "",
  is_default: false,
  is_enabled: true,
}
```

---

### 🔴 CRITICAL 6: Provider Type Selection in Form

**Current (Lines 236-272, 315-335)**:
```typescript
{/* Provider Type */}
<FormField
  control={form.control}
  name="provider_type"  // ❌ Field doesn't exist
  render={({ field }) => (
    <FormItem>
      <FormLabel>Provider Type</FormLabel>
      <Select onValueChange={field.onChange} defaultValue={field.value}>
        <SelectContent>
          {providerTypes.map((type) => (  // ❌ providerTypes not defined
            <SelectItem key={type.value} value={type.value}>
              {type.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </FormItem>
  )}
/>

{/* Base URL (for OpenAI-compatible) */}
{selectedProviderType === "openai_compatible" && (  // ❌ Field doesn't exist
  <FormField control={form.control} name="base_url">
    {/* ... */}
  </FormField>
)}
```

**Problem**:
- UserAccessProvider doesn't have `provider_type` field
- The "type" of API is determined by the AgentConfig that uses this provider
- Same provider can be used with multiple agent configs that have different provider_types

**Fix - Simplify**:
```typescript
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
        A friendly name to identify this API key configuration
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
        <PasswordInput placeholder="sk-..." autoComplete="off" {...field} />
      </FormControl>
      <FormDescription>
        Your API key will be encrypted before storage
      </FormDescription>
      <FormMessage />
    </FormItem>
  )}
/>

{/* Base URL - Always show, optional */}
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
        Custom endpoint URL. Leave empty to use default endpoints.
        Common uses: Ollama, Azure OpenAI, OpenAI-compatible services.
      </FormDescription>
      <FormMessage />
    </FormItem>
  )}
/>

{/* Description */}
{/* ... same as current ... */}

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
        <Switch checked={field.value} onCheckedChange={field.onChange} />
      </FormControl>
    </FormItem>
  )}
/>
```

---

### 🟡 PRIORITY 2: Provider Card Display

**Current (Lines 440-451)**:
```typescript
<CardDescription className="mt-1">
  {getProviderLabel(
    provider.provider_type ??  // ❌ Field doesn't exist
      (provider.provider_type_id  // ❌ Field doesn't exist
        ? providerTypeNameById[provider.provider_type_id]
        : null),
  )}
  {provider.base_url && (
    <span className="ml-2 text-xs font-mono">
      ({provider.base_url})
    </span>
  )}
</CardDescription>
```

**Problem**:
- Trying to display `provider_type` which doesn't exist
- UserAccessProvider is just credentials - no type info

**Fix**:
```typescript
<CardDescription className="mt-1">
  {provider.description || "API Access Provider"}
  {provider.base_url && (
    <span className="block mt-1 text-xs font-mono text-muted-foreground">
      {provider.base_url}
    </span>
  )}
</CardDescription>
```

---

### 🟡 PRIORITY 2: Missing Error Handling

**Current**:
- No error display for query errors
- No validation before form submit

**Fix**:
```typescript
const {
  providers,
  isLoading,
  error,
  // ...
} = useLlmProviders()

// Add error display:
{error && (
  <Alert variant="destructive">
    <AlertTitle>Error loading providers</AlertTitle>
    <AlertDescription>{error.message}</AlertDescription>
  </Alert>
)}

// Add client-side validation before submit:
const onSubmit = async (data: FormData) => {
  // Validate with service
  const validation = UserAccessProviderService.validateProviderConfig(data)

  if (!validation.is_valid) {
    validation.errors.forEach(err => showErrorToast(err))
    return
  }

  // Show warnings but allow
  validation.warnings.forEach(warn => console.warn(warn))

  try {
    await createProvider(data)
    setIsAddDialogOpen(false)
    form.reset()
  } catch (err) {
    // Error toast already shown by hook
  }
}
```

---

### 🟡 PRIORITY 2: Missing useCustomToast Import

**Current (Line 56, 75)**:
```typescript
import { showErrorToast } from "@/hooks/useCustomToast"

// Later:
const { showErrorToast, showSuccessToast } = useCustomToast()  // ❌ Not imported
```

**Problem**:
- Importing `showErrorToast` function but also trying to destructure from hook
- Inconsistent usage

**Fix**:
```typescript
import { useCustomToast } from "@/hooks/useCustomToast"

// In component:
const { showErrorToast, showSuccessToast } = useCustomToast()
```

---

### 🟢 PRIORITY 3: Missing Provider Status Display

**Current**:
- Shows verification status badge
- Doesn't show full status (verified/failed/unknown)

**Enhancement**:
```typescript
import { ProviderStatusBadge } from "@/components/Agents/ProviderStatusBadge"

// In card:
<div className="flex items-start justify-between">
  <div>
    <CardTitle className="flex items-center gap-2">
      {provider.name}
      {provider.is_default && (
        <Badge variant="secondary" className="text-xs">Default</Badge>
      )}
      {!provider.is_enabled && (
        <Badge variant="outline" className="text-xs">Disabled</Badge>
      )}
      <ProviderStatusBadge status={provider.status} />
    </CardTitle>
    {/* ... */}
  </div>
</div>
```

---

## RECOMMENDED REFACTOR APPROACH

### Step 1: Update Imports
```typescript
// Remove old imports
// import { LlmCatalogService, LlmProvidersService } from "@/client"

// Add new imports
import { useLlmProviders } from "@/hooks/useLlmProviders"
import { UserAccessProviderService } from "@/services/userAccessProviderService"
import type { UserAccessProviderViewModel } from "@/services/userAccessProviderService"
import { useCustomToast } from "@/hooks/useCustomToast"
```

### Step 2: Remove Catalog Logic
```typescript
// Remove lines 81-105 (catalog provider query and mappings)
// UserAccessProvider doesn't have provider type
```

### Step 3: Update Form Schema
```typescript
// Remove provider_type from schema and defaultValues
const formSchema = z.object({
  name: z.string().min(1, "Name is required").max(100),
  api_key: z.string().min(1, "API key is required"),
  base_url: z.string().url("Must be a valid URL").optional().or(z.literal("")),
  description: z.string().max(500).optional().or(z.literal("")),
  is_default: z.boolean().default(false),
  is_enabled: z.boolean().default(true),
})
```

### Step 4: Replace Queries/Mutations with Hook
```typescript
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
```

### Step 5: Update Form Submission
```typescript
const onSubmit = async (data: FormData) => {
  const validation = UserAccessProviderService.validateProviderConfig(data)

  if (!validation.is_valid) {
    validation.errors.forEach(err => showErrorToast(err))
    return
  }

  try {
    await createProvider(data)
    setIsAddDialogOpen(false)
    form.reset()
  } catch (err) {
    // Error handled by hook
  }
}
```

### Step 6: Remove Provider Type Selection from Form
```typescript
// Remove:
// - FormField for "provider_type"
// - Conditional base_url rendering based on provider type
// - providerTypes array
// - getProviderLabel function

// Make base_url always visible (optional)
```

### Step 7: Update Provider Card Display
```typescript
// Remove provider type display
// Show description and base_url instead
<CardDescription className="mt-1">
  {provider.description || "API Access Provider"}
  {provider.base_url && (
    <span className="block mt-1 text-xs font-mono">
      {provider.base_url}
    </span>
  )}
</CardDescription>
```

---

## FILE STRUCTURE RECOMMENDATION

```typescript
// UserAccessProviders.tsx - Simplified structure

import { /* ... */ } from "react"
import { useLlmProviders } from "@/hooks/useLlmProviders"
import { UserAccessProviderService } from "@/services/userAccessProviderService"
import type { UserAccessProviderViewModel } from "@/services/userAccessProviderService"

// Form schema (no provider_type)
const formSchema = z.object({ /* ... */ })

const UserAccessProviders = () => {
  // Use hook instead of direct queries
  const {
    providers,
    isLoading,
    error,
    createProvider,
    deleteProvider,
    testProvider,
    // ...
  } = useLlmProviders()

  const { showErrorToast, showSuccessToast } = useCustomToast()
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false)
  const [testingProviderId, setTestingProviderId] = useState<string | null>(null)

  const form = useForm<FormData>({ /* ... */ })

  const onSubmit = async (data: FormData) => {
    // Validate
    const validation = UserAccessProviderService.validateProviderConfig(data)
    if (!validation.is_valid) {
      validation.errors.forEach(err => showErrorToast(err))
      return
    }

    // Create
    try {
      await createProvider(data)
      setIsAddDialogOpen(false)
      form.reset()
    } catch (err) {
      // Error handled by hook
    }
  }

  const handleTest = async (providerId: string) => {
    setTestingProviderId(providerId)
    try {
      await testProvider(providerId)
    } finally {
      setTestingProviderId(null)
    }
  }

  const handleDelete = async (provider: UserAccessProviderViewModel) => {
    if (window.confirm(`Delete "${provider.name}"? This cannot be undone.`)) {
      await deleteProvider(provider.id)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header with Add button */}
      {/* Error display */}
      {/* Loading state */}
      {/* Empty state */}
      {/* Provider cards (simplified display) */}
    </div>
  )
}

export default UserAccessProviders
```

---

## SUMMARY OF CHANGES NEEDED

### Remove:
- ❌ Catalog provider query (lines 81-105)
- ❌ Provider type mappings (providerTypeIdByName, providerTypeNameById)
- ❌ Provider type selection in form
- ❌ Conditional base_url rendering based on type
- ❌ getProviderLabel function
- ❌ providerTypes array (undefined)
- ❌ Direct TanStack Query usage
- ❌ Direct service calls
- ❌ Custom query keys

### Add:
- ✅ Import `useLlmProviders` hook
- ✅ Import `UserAccessProviderService` for validation
- ✅ Import correct types from services
- ✅ Client-side validation before submit
- ✅ Error display for query errors
- ✅ Proper TypeScript types

### Update:
- 🔄 Form schema (remove provider_type)
- 🔄 Form defaultValues (remove provider_type)
- 🔄 Form submission logic (use hook methods)
- 🔄 Provider card display (show description, not type)
- 🔄 Test/delete handlers (use hook methods)
- 🔄 Type annotations (UserAccessProviderViewModel)

---

## COMPLETION CHECKLIST

- [ ] Remove all imports from `@/client`
- [ ] Add imports from services and hooks
- [ ] Remove catalog provider query
- [ ] Remove provider type mappings
- [ ] Update form schema (no provider_type)
- [ ] Replace queries/mutations with `useLlmProviders` hook
- [ ] Update form submission to use hook methods
- [ ] Remove provider type selection from form
- [ ] Make base_url always visible (optional field)
- [ ] Update provider card display (no type, show description)
- [ ] Add client-side validation
- [ ] Add error display
- [ ] Update all type annotations
- [ ] Test component with new architecture

---

## REFERENCES

- **UserAccessProviderService**: `frontend/src/services/userAccessProviderService.ts`
- **useLlmProviders Hook**: `frontend/src/hooks/useLlmProviders.ts`
- **Three-Way Binding**: See `agentService.ts` lines 40-54
- **ViewModel Pattern**: See `agentService.REVIEW.md`
