# SVG Library: Compose Studio, Batch Seed, Gallery — Implementation Plan


**Goal:** Implement the D→B sequence from the design doc: Compose Studio tab, rebuilt Batch Seed dialog, and Gallery tagging/filtering/sort.

**Architecture:** All new compose functionality routes through the existing `useEnqueueTesserScript` hook targeting `svg.compose`. Domain constants live in a single TS file mirroring the Python source. Gallery features are client-side over already-loaded data.


**Design doc:** `docs/plans/2026-03-25-svg-library-compose-gallery-design.md`
**Python source:** `backend/app/test_scripts/render_things/svg_library_tools.py`
**Reference card:** `backend/app/test_scripts/render_things/svg_combinatorics_reference_card.md`

---

## Task 1: `svgComposeDomains.ts` — constants, types, knob group definitions

**Files:**
- Create: `src/components/Svg/constants/svgComposeDomains.ts`


---

## Task 2: `svgComposeDomains.ts` — `buildScenarios` + `applyFamilyBias`

**Files:**
- Modify: `src/components/Svg/constants/svgComposeDomains.ts` (append)  DONE


---

## Task 3: Extract `TesserJobRow` to shared display component

**Files:**
- Create: `src/components/Svg/display/TesserJobRow.tsx`
- Modify: `src/components/Svg/panels/TesserStudioPanel.tsx`

DONE
---

## Task 4: Build `ComposeStudioTab` component

**Files:**
- Create: `src/components/Svg/panels/ComposeStudioTab.tsx`

DONE

---

## Task 5: Add Compose Studio tab to `SvgOperationsPanel`


DONE
---

**Files:**
- Modify: `src/components/Svg/dialogs/BatchSeedSvgDialog.tsx` (full rewrite)

DONE 

## Task 7: Add tag display + inline editor to `SvgCard`

**Files:**
- Modify: `src/components/Svg/display/SvgCard.tsx`

**Step 1: Add tag utility functions and updated component**

DONE

**Step 2: Update `SvgsGalleryPanel` to pass `onTagFilter`**

This step is now sequenced together with Task 8 instead of landing as a temporary
search-seeding bridge.

`SvgCard` tag clicks should wire directly into the proper gallery filter state:

```typescript
onTagFilter={(tag) => {
  setFilterUserTags((prev) => {
    const next = new Set(prev)
    next.add(tag)
    return next
  })
  setFilterBarOpen(true)
}}
```

That means Task 7 Step 2 should be implemented concurrently with Task 8 in the
same `SvgsGalleryPanel.tsx` change so we do not introduce a short-lived
`setSearch(tag)` path that immediately becomes obsolete.

---

## Task 8: Filter bar + sort controls in `SvgsGalleryPanel`

**Files:**
- Modify: `src/components/Svg/panels/SvgsGalleryPanel.tsx`

**Step 1: Replace the panel with the extended version**

This task now owns the completion of Task 7 Step 2 as part of the same edit.
The filter bar state and the `SvgCard` tag-click wiring should land together.

Key additions to state:
```typescript
// Filter state
const [filterFamilies, setFilterFamilies] = useState<Set<string>>(new Set())
const [filterTiers, setFilterTiers] = useState<Set<string>>(new Set())
const [filterComplexity, setFilterComplexity] = useState<"all" | "low" | "mid" | "high">("all")
const [filterPalette, setFilterPalette] = useState<Set<string>>(new Set())
const [filterUserTags, setFilterUserTags] = useState<Set<string>>(new Set())
const [filterBarOpen, setFilterBarOpen] = useState(false)

// Sort state
const [sortBy, setSortBy] = useState<"name" | "updated" | "created" | "complexity" | "contrast">("updated")
const [sortDir, setSortDir] = useState<"asc" | "desc">("desc")
```

Replace the `filtered` memo with `filteredAndSorted`:
```typescript
const filteredAndSorted = useMemo(() => {
  const term = search.trim().toLowerCase()
  let rows = listQuery.data?.data ?? []

  // Text search
  if (term) {
    rows = rows.filter((row) => {
      const haystack = [row.name, row.description ?? "", JSON.stringify(row.metadata_json ?? {})]
        .join(" ").toLowerCase()
      return haystack.includes(term)
    })
  }

  // Family filter
  if (filterFamilies.size > 0) {
    rows = rows.filter((row) => {
      const meta = (row.metadata_json ?? {}) as Record<string, unknown>
      return filterFamilies.has(meta.family as string)
    })
  }

  // Tier filter
  if (filterTiers.size > 0) {
    rows = rows.filter((row) => {
      const meta = (row.metadata_json ?? {}) as Record<string, unknown>
      return filterTiers.has(meta.generation_tier as string) ||
        filterTiers.has(meta.source as string)
    })
  }

  // Complexity filter
  if (filterComplexity !== "all") {
    rows = rows.filter((row) => {
      const meta = (row.metadata_json ?? {}) as Record<string, unknown>
      const score = typeof meta.complexity_score === "number" ? meta.complexity_score : null
      if (score === null) return false
      if (filterComplexity === "low") return score < 0.33
      if (filterComplexity === "mid") return score >= 0.33 && score < 0.66
      return score >= 0.66
    })
  }

  // Palette filter
  if (filterPalette.size > 0) {
    rows = rows.filter((row) => {
      const meta = (row.metadata_json ?? {}) as Record<string, unknown>
      const knobs = meta.knobs as Record<string, unknown> | undefined
      return knobs && filterPalette.has(knobs.palette_family as string)
    })
  }

  // User tag filter
  if (filterUserTags.size > 0) {
    rows = rows.filter((row) => {
      const meta = (row.metadata_json ?? {}) as Record<string, unknown>
      const tags = Array.isArray(meta.tags) ? (meta.tags as string[]) : []
      return [...filterUserTags].every((t) => tags.includes(t))
    })
  }

  // Sort
  rows = [...rows].sort((a, b) => {
    let cmp = 0
    if (sortBy === "name") {
      cmp = a.name.localeCompare(b.name)
    } else if (sortBy === "updated") {
      cmp = new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime()
    } else if (sortBy === "created") {
      cmp = new Date(a.created_at ?? a.updated_at).getTime() - new Date(b.created_at ?? b.updated_at).getTime()
    } else if (sortBy === "complexity") {
      const aScore = ((a.metadata_json ?? {}) as Record<string, unknown>).complexity_score as number ?? 0
      const bScore = ((b.metadata_json ?? {}) as Record<string, unknown>).complexity_score as number ?? 0
      cmp = aScore - bScore
    } else if (sortBy === "contrast") {
      const aScore = ((a.metadata_json ?? {}) as Record<string, unknown>).contrast_score as number ?? 0
      const bScore = ((b.metadata_json ?? {}) as Record<string, unknown>).contrast_score as number ?? 0
      cmp = aScore - bScore
    }
    return sortDir === "asc" ? cmp : -cmp
  })

  return rows
}, [listQuery.data?.data, search, filterFamilies, filterTiers, filterComplexity, filterPalette, filterUserTags, sortBy, sortDir])
```

Active filter count badge:
```typescript
const activeFilterCount = filterFamilies.size + filterTiers.size +
  (filterComplexity !== "all" ? 1 : 0) + filterPalette.size + filterUserTags.size
```

Filter bar JSX (add below the search input, above the grid):
```tsx
<Collapsible open={filterBarOpen} onOpenChange={setFilterBarOpen}>
  <CollapsibleTrigger asChild>
    <Button variant="outline" size="sm" className="gap-2">
      Filters
      {activeFilterCount > 0 ? (
        <Badge variant="secondary" className="h-4 px-1 text-[10px]">{activeFilterCount}</Badge>
      ) : null}
      <ChevronDown className={["size-3.5 transition-transform", filterBarOpen ? "rotate-180" : ""].join(" ")} />
    </Button>
  </CollapsibleTrigger>
  <CollapsibleContent>
    <div className="mt-2 space-y-3 rounded-lg border bg-muted/10 p-3">

      {/* Family */}
      <div className="space-y-1.5">
        <Label className="text-xs">Family</Label>
        <div className="flex flex-wrap gap-1.5">
          {STYLE_FAMILIES.map((f) => (
            <Badge
              key={f}
              variant={filterFamilies.has(f) ? "default" : "outline"}
              className="cursor-pointer capitalize"
              onClick={() => setFilterFamilies((prev) => {
                const next = new Set(prev)
                next.has(f) ? next.delete(f) : next.add(f)
                return next
              })}
            >
              {f}
            </Badge>
          ))}
        </div>
      </div>

      {/* Tier */}
      <div className="space-y-1.5">
        <Label className="text-xs">Tier</Label>
        <div className="flex flex-wrap gap-1.5">
          {["pairwise-core", "hero-extreme", "safe-utility", "compose-studio", "tesser"].map((t) => (
            <Badge
              key={t}
              variant={filterTiers.has(t) ? "default" : "outline"}
              className="cursor-pointer"
              onClick={() => setFilterTiers((prev) => {
                const next = new Set(prev)
                next.has(t) ? next.delete(t) : next.add(t)
                return next
              })}
            >
              {t}
            </Badge>
          ))}
        </div>
      </div>

      {/* Complexity */}
      <div className="space-y-1.5">
        <Label className="text-xs">Complexity</Label>
        <ToggleGroup
          type="single"
          value={filterComplexity}
          onValueChange={(v) => setFilterComplexity((v || "all") as typeof filterComplexity)}
          variant="outline"
        >
          {(["all", "low", "mid", "high"] as const).map((c) => (
            <ToggleGroupItem key={c} value={c} className="h-7 text-xs">{c}</ToggleGroupItem>
          ))}
        </ToggleGroup>
      </div>

      {/* Clear */}
      {activeFilterCount > 0 ? (
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => {
            setFilterFamilies(new Set())
            setFilterTiers(new Set())
            setFilterComplexity("all")
            setFilterPalette(new Set())
            setFilterUserTags(new Set())
          }}
        >
          Clear all filters
        </Button>
      ) : null}
    </div>
  </CollapsibleContent>
</Collapsible>
```

Sort row JSX (add above the grid, right-aligned):
```tsx
<div className="flex items-center justify-end gap-1 flex-wrap">
  <span className="text-xs text-muted-foreground mr-1">Sort:</span>
  {(["name", "updated", "created", "complexity", "contrast"] as const).map((field) => (
    <Button
      key={field}
      size="sm"
      variant={sortBy === field ? "default" : "ghost"}
      className="h-7 px-2 text-xs capitalize"
      onClick={() => {
        if (sortBy === field) setSortDir((d) => d === "asc" ? "desc" : "asc")
        else { setSortBy(field); setSortDir("desc") }
      }}
    >
      {field}
      {sortBy === field ? (sortDir === "asc" ? " ↑" : " ↓") : null}
    </Button>
  ))}
</div>
```

Also update `SvgCard` usage to pass `onTagFilter`:
```tsx
onTagFilter={(tag) => {
  setFilterUserTags((prev) => {
    const next = new Set(prev)
    next.add(tag)
    return next
  })
  setFilterBarOpen(true)
}}
```

Required new imports in `SvgsGalleryPanel.tsx`:
```typescript
import { ChevronDown } from "lucide-react"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { STYLE_FAMILIES } from "@/components/Svg/constants/svgComposeDomains"
```



---

## Verification Checklist: Outside of sandbox environment, manual testing by UX team

- [ ] `npm run build` completes without errors
- [ ] `npm run lint` passes
- [ ] Dev server starts: `npm run dev`
- [ ] Operations panel shows 3 tabs: Compose Studio (default), Combinatorics, Asset Editor
- [ ] Compose Studio: clicking a family preset updates knob values
- [ ] Compose Studio: Geometry group open by default, others collapsed
- [ ] Compose Studio: Enqueue Render creates a job visible in the Jobs section
- [ ] Batch Seed: opens dialog, Generate Plan shows accordion of scenarios
- [ ] Batch Seed: Edit chevron expands inline knob editor
- [ ] Batch Seed: Enqueue All shows progress counter then job list
- [ ] Gallery: SvgCard shows tag row with derived tags
- [ ] Gallery: clicking a tag opens filter bar with that tag active
- [ ] Gallery: sort buttons change order of cards
- [ ] TesserStudioPanel still works (TesserJobRow extraction didn't break it)
