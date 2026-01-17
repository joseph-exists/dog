---
name: frontend
description: |
  Frontend development for React + TypeScript + shadcn/ui codebase. Use when working with:
  - Components in frontend/src/components/
  - Routes in frontend/src/routes/
  - Hooks in frontend/src/hooks/
  - Services in frontend/src/services/
  - Any .tsx/.ts files in frontend/src/

  Triggers: component creation, UI implementation, form handling, state management,
  TanStack Query/Router, shadcn components, frontend features, ViewModels, styling
---

# Frontend Development

## Critical Rules

1. **No frontend processing** - All data processing happens on backend. Frontend processing causes project failure.
2. **ViewModels are mandatory** - Never use raw API types in components. Always use services with ViewModels.
3. **No new hooks/utilities without approval** - Requires explicit human authorization.
4. **No throwaway code** - All code must be production-ready with JSDoc documentation.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Build | Vite |
| Framework | React 19 + TypeScript |
| Routing | TanStack Router (file-based) |
| Server State | TanStack Query |
| UI | shadcn/ui + Tailwind CSS (MCP server available) |
| Forms | React Hook Form + Zod |
| Icons | Lucide React |
| API Client | Auto-generated via @hey-api/openapi-ts |

## Data Flow

```
Component → Service (ViewModel) → API Client (sdk.gen) → Backend
    ↑                                                        ↓
    ←←←←←←←←←← TanStack Query (cache, loading, error) ←←←←←←←
```

## Component Pattern

```typescript
/**
 * ComponentName Component
 *
 * Brief description
 * - Feature 1
 * - Feature 2
 */

// Imports: tanstack → react → @/ aliases → relative
import { useMutation, useQuery } from "@tanstack/react-query"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import type { SomeViewModel } from "@/services/someService"

interface ComponentNameProps {
  requiredProp: string
  optionalProp?: boolean
}

export default function ComponentName({
  requiredProp,
  optionalProp = false,
}: ComponentNameProps) {
  // Hooks first, state second, derived values third, handlers fourth
  return <div>{/* JSX */}</div>
}
```

## Error Handling Pattern

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

## Query Keys

```typescript
["rooms"]
["rooms", roomId]
["rooms", roomId, "messages"]
["rooms", roomId, "participants"]
```

## DO NOT

- Use raw API types in components (use ViewModels)
- Create inline API calls (use services)
- Skip TypeScript types or use `any`
- Create new hooks without approval
- Edit `src/client/` (auto-generated)
- Edit `src/components/ui/` without shadcn CLI
- Use `refetchInterval` for new features (WebSocket migration planned)
- Create components over 300 lines
- Skip JSDoc documentation

## References

For complete patterns, conventions, and decisions, see:
- [references/frontend-patterns.md](references/frontend-patterns.md) - Full documentation including file organization, naming conventions, forms, testing, and integration workflows
