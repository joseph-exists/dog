# Frontend Client SDK Migration Guide

**Purpose**: Refactor components to use exported client SDK instead of deprecated service layer

**Status**: 3 TypeScript errors remaining (down from 102)


---

## The Golden Rule

> **USE THE EXPORTED CLIENT EXPORTS FOR GREAT HONOR**

Every function and type you need is in:
- `@/client/sdk.gen` - Service classes (AgentsService, LlmProvidersService, etc.)
- `@/client/types.gen` - TypeScript types (UserAccessProviderPublic, UserAgentConfigCreate, etc.)
- `@/client/schemas.gen` - Zod schemas (if needed)

---

## Quick Reference: What to Replace

### ❌ OLD PATTERN (Delete These)

```typescript
// BAD: Service layer imports
import { AgentService } from "@/services/agentService"
import { UserAccessProviderService } from "@/services/userAccessProviderService"
import type { AgentViewModel } from "@/services/agentService"
import type { UserAccessProviderViewModel } from "@/services/userAccessProviderService"

// BAD: Custom hooks wrapping services
import { useLlmProviders } from "@/hooks/useLlmProviders"
import useLlmCatalog from "@/hooks/useLlmCatalog"
import { useAgentSettings } from "@/hooks/useAgentSettings"

// BAD: Using the hook
const { providers, createProvider, deleteProvider } = useLlmProviders()

// BAD: ViewModel types
const provider: UserAccessProviderViewModel = ...
const agent: AgentViewModel = ...
```

### ✅ NEW PATTERN (Use These)

```typescript
// GOOD: Direct client SDK imports
import { AgentsService, LlmProvidersService } from "@/client/sdk.gen"
import type {
  UserAccessProviderPublic,
  UserAgentConfigCreate,
  UserAgentConfigPublic
} from "@/client/types.gen"

// GOOD: TanStack Query for data fetching
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"

// GOOD: Direct query
const { data: providersResponse, isLoading } = useQuery({
  queryKey: ["llm-providers"],
  queryFn: () => LlmProvidersService.listProviders(),
})
const providers: UserAccessProviderPublic[] = providersResponse?.data || []

// GOOD: Direct mutation
const queryClient = useQueryClient()
const createMutation = useMutation({
  mutationFn: (data: any) => LlmProvidersService.createProvider({ requestBody: data }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["llm-providers"] })
  },
})

// GOOD: Public types
const provider: UserAccessProviderPublic = ...
const agent: UserAgentConfigPublic = ...
```

---

## Step-by-Step Migration Process

### Step 1: Update Imports

**Before:**
```typescript
import { AgentService } from "@/services/agentService"
import type { AgentViewModel } from "@/services/agentService"
import { useLlmProviders } from "@/hooks/useLlmProviders"
```

**After:**
```typescript
import { AgentsService, LlmProvidersService } from "@/client/sdk.gen"
import type { UserAgentConfigPublic, UserAccessProviderPublic } from "@/client/types.gen"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
```

### Step 2: Replace Hook Usage with Direct Queries

**Before:**
```typescript
const { providers, isLoading, createProvider } = useLlmProviders()
```

**After:**
```typescript
const { data: providersResponse, isLoading } = useQuery({
  queryKey: ["llm-providers"],
  queryFn: () => LlmProvidersService.listProviders(),
})
const providers: UserAccessProviderPublic[] = providersResponse?.data || []
```

### Step 3: Replace Mutations

**Before:**
```typescript
const { createProvider, isCreating } = useLlmProviders()
await createProvider(data)
```

**After:**
```typescript
const queryClient = useQueryClient()
const createMutation = useMutation({
  mutationFn: (data: any) =>
    LlmProvidersService.createProvider({ requestBody: data }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["llm-providers"] })
  },
})
await createMutation.mutateAsync(data)
const isCreating = createMutation.isPending
```

### Step 4: Update Type References

**Before:**
```typescript
const provider: UserAccessProviderViewModel = ...
const agent: AgentViewModel = ...
provider.status // "verified" | "failed" | "unknown"
```

**After:**
```typescript
const provider: UserAccessProviderPublic = ...
const agent: UserAgentConfigPublic = ...
// Derive status from fields:
const status = provider.is_validated ? "verified" : "unknown"
```

---

## Common Query Keys

Use consistent query keys across the app:

```typescript
// Providers
["llm-providers"]
["llm-providers", providerId]

// Agents
["agents"]
["agents", agentId]
["agents", "available"]  // For listAvailableAgents

// Catalog
["llm-catalog"]
["llm-catalog", "models"]
["llm-catalog", "providers"]
```

---

## Type Mapping Reference

| Old Type | New Type | Notes |
|----------|----------|-------|
| `AgentViewModel` | `UserAgentConfigPublic` | From API response |
| `CreateAgentInput` | `UserAgentConfigCreate` | For POST requests |
| `UpdateAgentInput` | `UserAgentConfigUpdate` | For PUT requests |
| `UserAccessProviderViewModel` | `UserAccessProviderPublic` | From API response |
| `AgentFormData` | Use `UserAgentConfigCreate` | Or create local type if needed |

---

## Service Method Patterns

### List/Get Operations

```typescript
// List all
const { data } = useQuery({
  queryKey: ["agents"],
  queryFn: () => AgentsService.listAgents(),
})
const agents = data?.data || []

// Get by ID
const { data: agent } = useQuery({
  queryKey: ["agents", agentId],
  queryFn: () => AgentsService.getAgent({ agentId }),
})
```

### Create/Update/Delete Operations

```typescript
const queryClient = useQueryClient()

// Create
const createMutation = useMutation({
  mutationFn: (data: UserAgentConfigCreate) =>
    AgentsService.createAgent({ requestBody: data }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["agents"] })
  },
})

// Update
const updateMutation = useMutation({
  mutationFn: ({ agentId, data }: { agentId: string; data: any }) =>
    AgentsService.updateAgent({ agentId, requestBody: data }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["agents"] })
    queryClient.invalidateQueries({ queryKey: ["agents", agentId] })
  },
})

// Delete
const deleteMutation = useMutation({
  mutationFn: (agentId: string) =>
    AgentsService.deleteAgent({ agentId }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["agents"] })
  },
})
```

---

## Real Examples from Completed Migrations

### Example 1: AgentForm.tsx

**Before:**
```typescript
import AgentService from "@/services/agentService"

useEffect(() => {
  AgentService.generateSlug()
    .then((slug) => form.setValue("slug", slug))
}, [])
```

**After:**
```typescript
import { AgentsService } from "@/client/sdk.gen"

useEffect(() => {
  AgentsService.generateAgentSlug()
    .then((generatedSlug) => {
      if (typeof generatedSlug === "string") {
        form.setValue("slug", generatedSlug)
      }
    })
}, [])
```

### Example 2: ProviderSelect.tsx

**Before:**
```typescript
import type { UserAccessProviderViewModel } from "@/services/userAccessProviderService"

interface ProviderSelectProps {
  providers: UserAccessProviderViewModel[]
  onChange: (provider: UserAccessProviderViewModel) => void
}

const status = provider.status // "verified" | "failed" | "unknown"
```

**After:**
```typescript
import type { UserAccessProviderPublic } from "@/client/types.gen"

interface ProviderSelectProps {
  providers: UserAccessProviderPublic[]
  onChange: (
    providerId: string | null,
    provider: UserAccessProviderPublic | null
  ) => void
}

// Derive status from provider fields
function getProviderStatus(
  provider: UserAccessProviderPublic
): "verified" | "unknown" {
  return provider.is_validated ? "verified" : "unknown"
}
```

### Example 3: UserAccessProviders.tsx

**Before:**
```typescript
import { useLlmProviders } from "@/hooks/useLlmProviders"

const {
  providers,
  createProvider,
  deleteProvider,
  isCreating,
  isDeleting,
} = useLlmProviders()

await createProvider(data)
```

**After:**
```typescript
import { LlmProvidersService } from "@/client/sdk.gen"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"

const queryClient = useQueryClient()

const { data: providersResponse, isLoading } = useQuery({
  queryKey: ["llm-providers"],
  queryFn: () => LlmProvidersService.listProviders(),
})
const providers = providersResponse?.data || []

const createMutation = useMutation({
  mutationFn: (data: any) =>
    LlmProvidersService.createProvider({ requestBody: data }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["llm-providers"] })
  },
})

await createMutation.mutateAsync(data)
const isCreating = createMutation.isPending
```

---

## Common Gotchas & Solutions

### Gotcha 1: Missing API Key Field

**Problem:**
```typescript
// TypeScript error: Property 'api_key' missing from UserAccessProviderCreate
```

**Solution:**
```typescript
// Use `any` type temporarily and add TODO comment
const createMutation = useMutation({
  mutationFn: (data: any) =>  // TODO: Fix backend type generation
    LlmProvidersService.createProvider({ requestBody: data }),
})
```

### Gotcha 2: UUID Generation Required

**Problem:**
```typescript
// Backend expects 'id' field in create request
```

**Solution:**
```typescript
await createMutation.mutateAsync({
  id: crypto.randomUUID(),
  name: data.name,
  // ... other fields
})
```

### Gotcha 3: Loading State Names Changed

**Problem:**
```typescript
// Old: isCreating, isDeleting
// New: mutation.isPending
```

**Solution:**
```typescript
// Instead of separate state variables:
const isCreating = createMutation.isPending
const isDeleting = deleteMutation.isPending
```

### Gotcha 4: Response Shape

**Problem:**
```typescript
// Service returns { data: [...], count: number }
// Direct assignment fails
const providers = LlmProvidersService.listProviders()
```

**Solution:**
```typescript
// Extract data array from response
const { data: response } = useQuery({
  queryFn: () => LlmProvidersService.listProviders(),
})
const providers = response?.data || []
```

### Gotcha 5: Model Combobox Props

**Problem:**
```typescript
// ModelCombobox expects specific props
<ModelCombobox placeholder="Select..." />  // Error: placeholder doesn't exist
```

**Solution:**
```typescript
// Check the component's actual interface
interface ModelComboboxProps {
  value: string
  onChange: (value: string) => void
  providerType?: string
  disabled?: boolean
  className?: string
  popoverWidth?: string
  // NO placeholder prop
}

// Use correct props:
<ModelCombobox
  value={field.value ?? ""}
  onChange={handleModelChange}
  providerType={undefined}
/>
```

---

## Validation Checklist

Before marking a component as "fixed", verify:

- [ ] No imports from `@/services/`
- [ ] No imports from custom hooks (`@/hooks/useLlm*`, `@/hooks/useAgent*`)
- [ ] All services imported from `@/client/sdk.gen`
- [ ] All types imported from `@/client/types.gen`
- [ ] Using `useQuery` for GET operations
- [ ] Using `useMutation` for POST/PUT/DELETE operations
- [ ] Query keys follow consistent pattern
- [ ] Cache invalidation on successful mutations
- [ ] No `any` types (except temporary with TODO comment)
- [ ] Component compiles without TypeScript errors

---

## Files to Migrate (Remaining)

**Priority Order** (by error count):

1. ✅ **UserAccessProviders.tsx** - DONE (26 → 1 errors)
2. **ModelCombobox.tsx** (16 errors)
3. **AgentDetailDialog.tsx** (10 errors)
4. **ProviderModelSelector.tsx** (9 errors)
5. **InlineProviderSelector.tsx** (8 errors)
6. **AgentCloneButton.tsx** (8 errors)
7. **EditAgentDialog.tsx** (7 errors)
8. **CreateAgentDialog.tsx** (6 errors)
9. **AgentModelSettings.tsx** (2 errors)
10. Routes and other files (8 errors combined)

---

## Success Criteria

**Goal**: Build passes with 0 TypeScript errors

**Current**: 73 errors remaining (down from 102)

**Next Milestone**: Get below 50 errors by fixing ModelCombobox.tsx

---

## Getting Help

**If you're stuck:**

1. Check the client SDK exports:
   ```bash
   grep "export class.*Service" frontend/src/client/sdk.gen.ts
   grep "export type.*Public" frontend/src/client/types.gen.ts
   ```

2. Look at completed examples:
   - `frontend/src/components/Agents/Forms/AgentForm.tsx`
   - `frontend/src/components/Agents/Selectors/ProviderSelect.tsx`
   - `frontend/src/components/UserSettings/UserAccessProviders.tsx`

3. Read the frontend patterns:
   - `.claude/skills/frontend/references/frontend-patterns.md`
   - `CLAUDE.md` - Critical Rule #2

---

## Notes for Backend Team

If you encounter missing fields or type mismatches:

**Don't create service layer workarounds!**

Instead:
1. Document the issue in a TODO comment
2. Use `any` type temporarily if needed
3. File an issue for backend team to fix type generation
4. Continue with migration - we can fix types later

Example:
```typescript
// TODO: Backend type generation missing api_key field in UserAccessProviderCreate
// See issue #XXX
const createMutation = useMutation({
  mutationFn: (data: any) =>
    LlmProvidersService.createProvider({ requestBody: data }),
})
```

---

**Last Updated**: 2026-01-31
**Migration Status**: In Progress (73/102 errors remaining)
