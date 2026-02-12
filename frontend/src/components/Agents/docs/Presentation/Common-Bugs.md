### Diagnosis pattern for invisible text:

1. Identify the invisible element's Tailwind class (e.g., `text-foreground`)
2. Find which CSS variable that maps to (e.g., `--foreground`)
3. Check whether the current scope (ambient or object) overrides that variable
4. If not → that's the bug. The element is reading a value from a higher scope with incompatible lightness.


## Gotcha: Container Text Color

### Problem

Compact and mini variants use plain `<div>` containers (not `<Card>`). The `<Card>` component includes `text-card-foreground` in its class, but a plain div does not. Without an explicit text color class, text inherits `color` from the nearest ancestor that sets it — often `<body>` via `text-foreground`. When the ambient or object scope changes surface lightness, this inherited body-level color may be wrong.

### Solution

Always set `text-card-foreground` explicitly on any container that uses `bg-card`:

```tsx
// ✗ Broken — text color inherits from body
<div className="bg-card rounded-lg border p-3">

// ✓ Fixed — text color reads from scoped --card-foreground
<div className="bg-card text-card-foreground rounded-lg border p-3">
```