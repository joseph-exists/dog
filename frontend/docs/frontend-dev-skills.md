# Frontend Skill Definition - Working Document

## Scope & Purpose

### What specific tasks should the skill handle?

Multiple specialized skills will handle these frontend tasks:

- **Co-designing UI/UX** - discovery/planning phase
- **Reviewing backend reference card against design** - validating that design contracts are satisfiable with backend primitives/interfaces
- **Adding new UI/UX features as a whole** - using backend references (e.g., new observability page)
- **Assessing existing ui/components for feature needs**
- **Proposing new components to be added to ui/components**
- **Adding sub-features to an existing page or feature**
- **Ensuring best practices** - design, implementation, and rules of engagement with codebase

### What should it explicitly NOT do?

- Cross the boundary to the backend
- Look up models files
- Modify any services
- Create new utilities or hooks without explicit human authorization
- Create throwaway code
- Skip inline documentation (must always create accurate JSDoc)
- **Perform data processing on the frontend** - all processing happens on the backend; frontend processing will cause project failure

### When should it be invoked vs. other skills?

**TBD** - depends on skill decomposition (see multiple skills decision)

---

## Tech Stack Specifics

### Stack Overview

| Layer | Technology |
|-------|------------|
| Build | Vite |
| Framework | React 19 + TypeScript |
| Routing | TanStack Router (file-based) |
| Server State | TanStack Query |
| UI Components | shadcn/ui + Tailwind CSS (MCP server available) |
| Forms | React Hook Form + Zod |
| Icons | Lucide React |
| API Client | Auto-generated from OpenAPI via @hey-api/openapi-ts |

### Unique Codebase Patterns

1. **Service Layer with ViewModels** (MANDATORY)
   - All API calls go through `src/services/`
   - Services transform API responses to UI-optimized ViewModels
   - Never use raw API types directly in components

2. **Aggregate Hooks Pattern**
   - Composite hooks delegate to specialized hooks (e.g., `useRoom` wraps `useRoomMessages`)
   - Derived state computed via `useMemo`

3. **Polling → WebSocket/SSE Migration** 
   - Current: `refetchInterval` completely removed, replaced with WebSocket/SSE from event-sourcing system


### Auto-Generated API Client Workflow

- Client generated from backend OpenAPI spec
- **Location**: `src/client/`
- **Services**: Import from `@/client/sdk.gen`
- **Types**: Import from `@/client/types.gen`
- **HTTP Client**: Axios under the hood
- **Regenerate**: Run `npm run generate-client` after backend API changes
- **Never edit generated files** - changes will be overwritten

### Authentication

- JWT-based authentication via `useAuth` hook
- Token stored in localStorage
- Automatic redirects to `/login` for unauthenticated users (via `beforeLoad` guards)
- Role-based UI elements (superuser vs regular user)
- **All localStorage access for auth should go through `useAuth`**

---

## Conventions & Patterns

### File/Folder Organization

```
src/
├── client/           # Auto-generated API client (DO NOT EDIT)
├── components/
│   ├── Admin/        # Feature: admin/user management
│   ├── Agents/       # Feature: agent configuration
│   ├── Common/       # Shared components (AuthLayout, DataTable, etc.)
│   ├── Rooms/        # Feature: chat rooms
│   ├── Sidebar/      # Navigation
│   ├── Stories/      # Feature: story editor
│   ├── UserSettings/ # Feature: user preferences
│   └── ui/           # shadcn/ui primitives (install via shadcn CLI)
├── hooks/            # Custom hooks (useAuth, useRoom, etc.)
├── routes/           # TanStack Router file-based routes
├── services/         # Service layer with ViewModels
└── lib/              # Utilities (cn(), etc.)
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Components | PascalCase | `AddUser.tsx`, `MessageList.tsx` |
| Hooks | camelCase with `use` prefix | `useAuth.ts`, `useRoom.ts` |
| Services | camelCase with `Service` suffix | `roomService.ts` |
| Routes | kebab-case matching URL | `room-v2.$roomId.tsx` |
| Types/Interfaces | PascalCase | `RoomViewModel`, `MessageViewModel` |

### Component Principles

- **Single-responsibility** - each component does one thing well
- **Modular** - components are self-contained and reusable where appropriate
- **Default exports** - use `export default` for easier imports
- Install new shadcn components via CLI into `src/components/ui/`

### Component Structure Template

```typescript
/**
 * ComponentName Component
 *
 * Brief description of purpose
 * - Key feature 1
 * - Key feature 2
 */

// Imports: tanstack → react → @/ aliases → relative
import { useMutation, useQuery } from "@tanstack/react-query"
import { useState } from "react"

import { SomeService } from "@/client/sdk.gen"
import { Button } from "@/components/ui/button"
import type { SomeViewModel } from "@/services/someService"

interface ComponentNameProps {
  requiredProp: string
  optionalProp?: boolean
  onCallback?: (value: string) => void
}

export default function ComponentName({
  requiredProp,
  optionalProp = false,
  onCallback,
}: ComponentNameProps) {
  // Hooks first
  // State second
  // Derived values third
  // Handlers fourth
  // Return JSX
}
```

### State Management Rules

| State Type | Tool | Example |
|------------|------|---------|
| Server state | TanStack Query | `useQuery`, `useMutation` |
| UI state | `useState` | Dialog open, form inputs |
| Derived state | `useMemo` | Filtered lists, computed values |
| Shared UI state | Context (sparingly) | Theme |

### TanStack Query Patterns

```typescript
// Query keys: hierarchical arrays
["rooms"]
["rooms", roomId]
["rooms", roomId, "messages"]
["rooms", roomId, "participants"]

// Invalidation after mutation
onSuccess: () => {
  queryClient.invalidateQueries({ queryKey: ["rooms", roomId] })
}


```

### Data Flow

```
Component → Service (ViewModel) → API Client (sdk.gen) → Backend
    ↑                                                        ↓
    ←←←←←←←←←← TanStack Query (cache, loading, error) ←←←←←←←
```

1. Components call services (never API client directly)
2. Services transform responses to ViewModels
3. TanStack Query handles caching, loading states, error states
4. Mutations update server state and invalidate relevant queries

---

## Forms - DECIDED

**Default**: Full stack (React Hook Form + Zod + shadcn/ui)

**Simpler forms** acceptable ONLY if:
- Simple case with no complex validation
- No new patterns or dependencies introduced
- **Requires explicit approval**

### Standard Form Pattern

```typescript
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"

const formSchema = z.object({
  name: z.string().min(1, "Required"),
  email: z.string().email("Invalid email"),
})

type FormData = z.infer<typeof formSchema>

function MyForm() {
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    defaultValues: { name: "", email: "" },
  })

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Name</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button type="submit" disabled={form.formState.isSubmitting}>
          Submit
        </Button>
      </form>
    </Form>
  )
}
```

---

## Quality & Verification

### Biome Linting

- Config: `frontend/biome.json`
- 2-space indents, double quotes, no semicolons
- Run: `npm run lint`
- Excluded: `dist/`, `node_modules/`, `src/client/`, `src/components/ui/`

### TypeScript

- Strict mode enabled
- No unused locals/parameters
- Path alias: `@/*` → `./src/*`

### Testing

- **Write tests for all new components**
- E2E: Playwright in `frontend/tests/`
- Requires running backend: `docker compose up -d --wait backend`
- Run: `npx playwright test`
- UI mode: `npx playwright test --ui`
- Use `data-testid` attributes for test selectors
- Mock API responses for testing async functionality
- Test UI interactions and form validation

### Performance

- Use `useMemo` for expensive calculations
- Use `useCallback` for functions passed as props to prevent unnecessary re-renders
- Structure component hierarchies to minimize re-renders
- Implement pagination for long lists

---

## Error Handling - DECIDED

Use `ApiError` from `src/client/core/ApiError.ts` as the primary error type.

### Current Architecture

| Layer | Mechanism |
|-------|-----------|
| API errors | `ApiError` + `handleError` utility → toast |
| Auth errors (401/403) | Global QueryCache/MutationCache → redirect to `/login` |
| Network errors | AxiosError handling in `extractErrorMessage` |
| Route errors | `ErrorComponent` (generic error page) |
| Form validation | Zod + React Hook Form |
| Optimistic update rollback | `onError` in mutations with context restore |
| WebSocket errors | `console.error` + optional `onError` callback |

### Standard Pattern

```typescript
import { ApiError } from "@/client"
import { handleError } from "@/utils"
import useCustomToast from "@/hooks/useCustomToast"

const { showErrorToast } = useCustomToast()

const mutation = useMutation({
  mutationFn: (data) => SomeService.doThing({ requestBody: data }),
  onError: (err: ApiError) => {
    handleError.call(showErrorToast, err)
  },
})
```

### Future Considerations

The following cases may need additional handling in the future:
- Specific HTTP status codes (404 vs 500 vs 429 rate limiting)
- Timeout errors with special messaging
- Offline/connectivity detection
- Error logging/reporting (Sentry, etc.)
- Retry logic for transient failures
- User-actionable errors ("Try again" buttons in toasts)

---

## Integration

### Frontend ↔ Backend Coordination

1. Backend team updates API
2. Backend deploys or runs locally
3. Frontend runs `npm run generate-client`
4. Frontend updates services/ViewModels if needed
5. Frontend updates components

### When to Regenerate API Client

- After any backend API route changes
- After model changes that affect API responses
- Before starting work that depends on new backend endpoints

### Dev Workflow

```bash
npm install          # Install deps
npm run dev          # Start dev server (localhost:5173)
npm run generate-client  # Regenerate API client
npm run lint         # Run Biome
npm run build        # Production build
```

---

## Anti-patterns to Prevent

### DO NOT

- Use raw API types in components (use ViewModels)
- Create inline API calls (use services)
- Skip TypeScript types or use `any`
- Create new hooks without approval
- Edit files in `src/client/` (auto-generated)
- Edit files in `src/components/ui/` without shadcn CLI
- Use `refetchInterval` for new features 
- Create components over 300 lines without extracting logic
- Skip JSDoc documentation on components and hooks
- Introduce new dependencies without approval

### Legacy Patterns to Avoid

- Direct localStorage access outside useAuth
- Custom toast implementations (use useCustomToast)
- Manual fetch/axios calls (use generated client)
- Class components
- Prop drilling beyond 2 levels (use hooks or context)

---

## Open Questions Remaining

- [ ] Exact skill decomposition (which tasks map to which skills)
- [ ] WebSocket/SSE migration timeline and impact assessment
- [ ] Event-emit strategy for Rooms - how does this affect frontend state management?
- [ ] Routing caveats for agents and rooms - what are the specific exceptions to standard TanStack Router patterns?
- [ ] Complex state logic on frontend - what patterns will we use, if any?
