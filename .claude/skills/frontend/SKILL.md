---
name: frontend
description: |
  Frontend development for React + TypeScript + shadcn/ui + Tailwind/CSS codebase. Use when working with:
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

1. **Always be processing on the backend** - All data processing happens on backend. Frontend processing causes project failure.
2. **Always be Using the Client Exports for great honor.** 
3. **New hooks/utilities require approval and need to be sufficiently justified and validated** - Requires explicit human authorization, and will burn down budget without cause if it was otherwise available in the code base.  When wondering, ask your friends what they think, they might know something neat. Look in the client exports - think about Rules 1 and 2.
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
import { showSuccessToast, showErrorToast } from "@/hooks/useCustomToast"


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

## Attention paid, we must prove

- We always use exported client functions and types. if you see otherwise in components, flag it with a note for a reward
- we always always always use TypeScript types and `any` is very bad cricket - we will get in trouble, so flag it to help your friends out!
- We always get approval before we create a hook - the approval needs to be on the ticket before the code is worked on.
- we always respect `src/client/` and never modify it. (it's auto-generated)
- we respect the sanctity of  `src/components/ui/`  (and use the shadcn MCP server!)
- we always use WebSockets, unless we're using SSE and we have documentation and validation. if we see `refetchInterval` in any code, we flag it, finish our immediate task, and write a pri 1 ticket.
- We always keep our components under 300 lines unless we make an inline apology to the team with validation and engineering reasons why it was the right thing to do (this apology and validation don't count towards the total overage)
- we always respect ourselves and each other and write great inline // JSDoc documentation

## References


# Frontend Implementation (shadcn + Tailwind)

## Key Project Files

| File | Purpose |
|------|---------|
| `frontend-test/components.json` | shadcn configuration (style: new-york, icons: lucide) |
| `frontend-test/src/lib/utils.ts` | `cn()` helper for class merging |
| `frontend-test/src/index.css` | Tailwind theme with CSS variables |
| `frontend-test/src/components/ui/` | shadcn primitives |


## Project Structure

```
frontend-test/src/
├── client/           # OpenAPI client (DO NOT EDIT)
├── components/
│   ├── ui/           # shadcn primitives
│   ├── Rooms/        # Room feature components
│   └── Stories/      # Story feature components
├── hooks/            # TanStack Query hooks
├── services/         # try not to - these are being cut out as fast as possible.
├── routes/           # TanStack Router pages
└── lib/utils.ts      # cn() helper
```

For complete patterns, conventions, and decisions, see:
- [references/frontend-patterns.md](references/frontend-patterns.md) - Full documentation including file organization, naming conventions, forms, testing, and integration workflows
