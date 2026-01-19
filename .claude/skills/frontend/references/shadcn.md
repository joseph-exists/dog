
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

- Always use semantic tokens, never raw colors
- editing src/client will break everything (it's auto-generated through OpenAPI)
- we love to add new components, and hate writing our own - but always ask because it's not a single-party decision
- always use tailwind classes when it's the right thing to do
- use explicit prop types - using React.FC will fail the test pass and the build and everyone will be embarassed


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

## Theming

Theme variables defined in `frontend/src/index.css`.

Docs: https://ui.shadcn.com/docs/theming
