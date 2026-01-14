---
name: frontend-shadcn
description: Implement React components in frontend-test using shadcn/ui + Tailwind CSS v4. Use when: (1) converting Chakra UI components to Tailwind, (2) creating new UI components, (3) working with forms, dialogs, or data display, (4) managing hooks and services. Follow these patterns exactly for consistency.
---

# Frontend Implementation (shadcn + Tailwind)

## Key Project Files

| File | Purpose |
|------|---------|
| `frontend-test/components.json` | shadcn configuration (style: new-york, icons: lucide) |
| `frontend-test/src/lib/utils.ts` | `cn()` helper for class merging |
| `frontend-test/src/index.css` | Tailwind theme with CSS variables |
| `frontend-test/src/components/ui/` | shadcn primitives |

## Adding shadcn Components

The majority of necessary components are already installed in frontend-test/src/components/ui

**Never write shadcn components manually.** Use the CLI:

```bash
cd frontend-test
npx shadcn@latest add button      # Add single component
npx shadcn@latest add dialog card # Add multiple
npx shadcn@latest add -a          # Add all components
```

Browse available components: https://ui.shadcn.com/docs/components

## Core Pattern: `cn()` Helper

Always use for conditional/merged classes:

```tsx
import { cn } from "@/lib/utils"

<div className={cn(
  "p-4 rounded-md",
  isActive && "bg-primary",
  className
)} />
```

## Semantic Colors

Use theme tokens (auto dark mode), not raw colors:

```tsx
// ✅ Semantic (auto dark mode)
"bg-background"  "bg-card"  "bg-muted"  "bg-primary"  "bg-destructive"
"text-foreground"  "text-muted-foreground"  "text-primary"
"border-border"  "border-input"

// ❌ Raw colors
"bg-blue-500"  "text-gray-600"  "border-gray-200"
```

## Project Structure

```
frontend-test/src/
├── client/           # OpenAPI client (DO NOT EDIT)
├── components/
│   ├── ui/           # shadcn primitives
│   ├── Rooms/        # Room feature components
│   └── Stories/      # Story feature components
├── hooks/            # TanStack Query hooks
├── services/         # API service layers (ViewModels)
├── routes/           # TanStack Router pages
└── lib/utils.ts      # cn() helper
```

## Chakra → Tailwind Conversion

See [references/chakra-conversion.md](references/chakra-conversion.md) for complete mapping.

Quick reference:
| Chakra | Tailwind |
|--------|----------|
| `<Box>` | `<div>` |
| `<Flex>` | `<div className="flex">` |
| `<VStack>` | `<div className="flex flex-col gap-4">` |
| `p={4}` | `className="p-4"` |
| `_hover={{}}` | `hover:` prefix |
| `_dark={{}}` | Not needed (use semantic colors) |

## Component, Hook, and Service Patterns

See [references/patterns.md](references/patterns.md) for:
- Basic component structure
- TanStack Query hook patterns
- Service layer with ViewModels
- Form patterns with react-hook-form + zod

## DO NOT

- Import from `@chakra-ui/react` — not installed
- Use Chakra props (`p={4}`, `_hover`, `_dark`) — use Tailwind classes
- Write shadcn components manually — use `npx shadcn@latest add`
- Use raw colors (`bg-blue-500`) — use semantic tokens
- Edit `src/client/` — auto-generated from OpenAPI
- Use `React.FC` — use explicit prop types

## Theming

Theme variables defined in `frontend-test/src/index.css`.

Docs: https://ui.shadcn.com/docs/theming
