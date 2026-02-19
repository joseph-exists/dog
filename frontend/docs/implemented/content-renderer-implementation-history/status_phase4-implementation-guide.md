# Phase 4 Implementation Guide: Migration

> "The secret of change is to focus all of your energy not on fighting the old, but on building the new."
> — Socrates

This guide provides step-by-step implementation instructions for Phase 4 of the ContentRenderer system. Phase 4 is the **Migration** phase where we replace existing content rendering patterns with the proven ContentRenderer system.

---

## 1. Phase 4 Objectives

> **Traceability:** This guide implements Phase 4 as defined in `integrated-spec.md` Section 14.4.
> It assumes Phase 1 (core renderers), Phase 2 (MDX + Shiki transformers), and Phase 3 (proving ground) are complete.

From integrated-spec Section 14.4:

1. **Create re-export layer** - `@/components/Common/ContentRenderer/`
2. **Export compatibility helper** - `renderContent()` for gradual migration
3. **Migrate existing files** - Replace inline switch-case patterns
4. **Validate migration** - Ensure no regressions in existing functionality

### 1.1 Success Criteria

Phase 4 is successful when:

- [X] All migrated files use ContentRenderer instead of inline rendering
- [X] No visual or functional regressions in Story Player/Preview/Editor
- [X] DOMPurify and ReactMarkdown imports removed from migrated files
- [X] New formats (code, svg, image, mdx) available in all contexts
- [X] Common/ re-export pattern established for future consumers

---

## 2. Prerequisites Checklist

Before implementing, verify:

- [x] Phase 1 complete (core renderers in `Page/primitives/ContentRenderer/`)
- [x] Phase 2 complete (MDX + Shiki transformers working)
- [x] Phase 3 complete (demo validated, StoryEditor integration tested)
- [x] No critical bugs from Phase 3 testing

### 2.1 Phase 3 Outcomes Available

Phase 3 delivered:
- **ContentRendererDemo** at `/content-renderer-demo` - validates all formats
- **NodeEditorForm** with ContentRenderer preview integration
- **Shiki transformers** working: lineNumbers, highlightLines, startLine
- **MDX runtime** compilation validated
- **All 9 variants** tested in demo page

### 2.2 Migration Targets Inventory [X] COMPLETE

Files identified for migration:

| File | Location | Pattern | Formats Handled |
|------|----------|---------|-----------------|
| StoryContent.tsx | `Story/StoryPlayer/` | `renderContent(node)` | html, markdown, json, text |
| StoryPreview.tsx | `Story/StoryPlayer/` | `renderContent(node)` | html, markdown, json, text |
| StoryPreview.tsx | `Stories/StoryPlayer/` | `renderContent(node)` | html, json, text |
| NodeDisplay.tsx | `Page/panels/StoryPanel/` | `renderNodeContent()` | html, markdown, json, text |
| NodeDisplay.tsx | `Room/panels/StoryPanel/` | `renderNodeContent()` | html, markdown, json, text |


**Problems with legacy pattern:**
1. Duplicated across 5+ files
2. Inconsistent format support (some miss markdown)
3. No syntax highlighting for code
4. No support for new formats (code, svg, image, mdx)
5. Mixed styling approaches

---

## 3. Implementation Order [X] FULLY COMPLETE

```
Part A: Create Common Re-export Layer
════════════════════════════════════════
1. Create @/components/Common/ContentRenderer/index.ts
2. Create renderContent.ts compatibility helper
3. Create nodeToContent.ts adapter utility

Part B: Migrate Story Player Files
════════════════════════════════════════
4. Migrate StoryContent.tsx
5. Migrate StoryPreview.tsx (Story/StoryPlayer/)
6. Migrate StoryPreview.tsx (Stories/StoryPlayer/)

Part C: Migrate Panel NodeDisplay Files
════════════════════════════════════════
7. Migrate Page/panels/StoryPanel/NodeDisplay.tsx
8. Migrate Room/panels/StoryPanel/NodeDisplay.tsx

Part D: Cleanup & Validation
════════════════════════════════════════
9. Remove unused imports
10. Run regression tests
11. Validate all formats render correctly
```

---

## 4. Part A: Create Common Re-export Layer [X] FULLY COMPLETE

> **Architecture (from integrated-spec Section 9.2):**
> The Common/ re-export layer provides a stable import path for consumers.
> Primary implementation stays in Page/primitives/; Common/ re-exports for convenience.

### 4.1 Files to Create [X] DONE

```
@/components/Common/ContentRenderer/
├── index.ts              # Public API re-exports
├── renderContent.tsx     # Compatibility helper function
└── nodeToContent.ts      # StoryNode → Content adapter
```

### 4.2 Common/ContentRenderer/index.ts [X] DONE

**Purpose:** Re-export everything from Page/primitives/ContentRenderer for convenient importing.


### 4.3 Common/ContentRenderer/nodeToContent.ts

**Purpose:** Convert StoryNodePublic to Content object for ContentRenderer.

### 4.4 Common/ContentRenderer/renderContent.tsx [X] DONE

**Purpose:** Compatibility helper for gradual migration. Preserves existing function signature.



---

## 5. Part B: Migrate Story Player Files

### 5.1 Migrate StoryContent.tsx [X] DONE


### 5.2 Migrate StoryPreview.tsx (Story/StoryPlayer/) [X] DONE



### 5.3 Migrate StoryPreview.tsx (Stories/StoryPlayer/)  [X] DONE
**Location:** `@/components/Stories/StoryPlayer/StoryPreview.tsx`

**Note:** This file only handles html, json, text (no markdown). After migration, it will gain markdown support for free.

**Migration approach:** Same as above.

---

## 6. Part C: Migrate Panel NodeDisplay Files [X] DONE

### 6.1 NodeDisplay Migration Pattern

Both NodeDisplay files have the same structure with a twist: they accept an optional `renderContent` prop for custom rendering.


### 6.2 Migrate Page/panels/StoryPanel/NodeDisplay.tsx

**Location:** `@/components/Page/panels/StoryPanel/NodeDisplay.tsx`


### 6.3 Migrate Room/panels/StoryPanel/NodeDisplay.tsx

**Location:** `@/components/Room/panels/StoryPanel/NodeDisplay.tsx`

**Migration:** Identical to Page version. These files are currently duplicates.

**Note:** Consider extracting to a shared component in Common/ in a future refactor.

---

## 7. Part D: Cleanup & Validation

### 7.1 Remove Unused Imports

After migration, verify these imports are removed from migrated files:

```typescript
// REMOVE from all migrated files:
import DOMPurify from "dompurify"
import ReactMarkdown from "react-markdown"
```

### 7.2 Regression Testing Checklist

| Test | Location | Expected Result | Status |
|------|----------|-----------------|--------|
| Story Player loads | StoryContent | Content renders | [ ] |
| HTML content renders | StoryContent | Sanitized HTML | [ ] |
| Markdown content renders | StoryContent | Prose styling, code highlighted | [ ] |
| JSON content renders | StoryContent | Formatted pre block | [ ] |
| Text content renders | StoryContent | Whitespace preserved | [ ] |
| Story Preview loads | StoryPreview | All formats work | [ ] |
| Node Display renders | NodeDisplay | Card format works | [ ] |
| Custom renderContent works | NodeDisplay | Backwards compatible | [ ] |
| New formats available | All | code, svg, image, mdx | [ ] |

### 7.3 Format Upgrade Validation

After migration, these formats should now work that didn't before:

| Format | Before Migration | After Migration | Phase |
|--------|------------------|-----------------|-------|
| code | ❌ Not supported | ✅ Shiki highlighting | Phase 1 |
| svg | ❌ Not supported | ✅ Inline or img mode | Phase 1 |
| image | ❌ Not supported | ✅ URL normalization | Phase 1 |
| mdx | ❌ Not supported | ✅ Runtime compilation | Phase 2 |
| markdown (code blocks) | ⚠️ No highlighting | ✅ Shiki highlighting | Phase 1 |
| code (line numbers) | ❌ Not supported | ✅ lineNumbers option | Phase 2 |
| code (highlights) | ❌ Not supported | ✅ highlightLines option | Phase 2 |

### 7.4 Visual Regression Check

For each migrated file, verify:

- [ ] Text styling matches original (font size, line height)
- [ ] Prose classes applied consistently
- [ ] Dark mode works correctly
- [ ] Scrolling behavior unchanged
- [ ] Error states render correctly (invalid JSON, missing content)

---

## 8. Paradigm Shifts Documentation

### 8.1 From Function to Component

| Before | After |
|--------|-------|
| `{renderContent(node)}` | `<ContentRenderer content={...} />` |
| Inline switch-case | Registry-based dispatch |
| Manual DOMPurify calls | `safeMode={true}` prop |
| Per-file format handling | Centralized renderer system |

### 8.2 Import Changes

```typescript
// BEFORE (each file)
import DOMPurify from "dompurify"
import ReactMarkdown from "react-markdown"

// AFTER (single import)
import { ContentRenderer, nodeToContent } from "@/components/Common/ContentRenderer"
```

### 8.3 Node Adaptation

```typescript
// BEFORE: Direct property access
const format = node.content_format || "text"
const content = node.content || ""

// AFTER: Adapter function
const content = nodeToContent(node, "page")
// or for raw strings:
const content = toContent(rawContent, format, "card")
```

---

## 9. Files Modified Summary

| File | Action | Purpose |
|------|--------|---------|
| `Common/ContentRenderer/index.ts` | CREATE | Re-export layer |
| `Common/ContentRenderer/renderContent.tsx` | CREATE | Compatibility helper |
| `Common/ContentRenderer/nodeToContent.ts` | CREATE | Node adapter |
| `Story/StoryPlayer/StoryContent.tsx` | UPDATE | Use ContentRenderer |
| `Story/StoryPlayer/StoryPreview.tsx` | UPDATE | Use ContentRenderer |
| `Stories/StoryPlayer/StoryPreview.tsx` | UPDATE | Use ContentRenderer |
| `Page/panels/StoryPanel/NodeDisplay.tsx` | UPDATE | Use ContentRenderer |
| `Room/panels/StoryPanel/NodeDisplay.tsx` | UPDATE | Use ContentRenderer |

---

## 10. Phase 4 Completion Checklist

**Part A: Common Re-export Layer:**
- [X] `Common/ContentRenderer/index.ts` created with re-exports
- [X] `Common/ContentRenderer/renderContent.tsx` created
- [X] `Common/ContentRenderer/nodeToContent.ts` created
- [X] Import path `@/components/Common/ContentRenderer` works

**Part B: Story Player Migration:**
- [X] StoryContent.tsx migrated
- [X] StoryPreview.tsx (Story/) migrated
- [X] StoryPreview.tsx (Stories/) migrated
- [X] DOMPurify/ReactMarkdown imports removed

**Part C: NodeDisplay Migration:**
- [X] Page/panels/StoryPanel/NodeDisplay.tsx migrated
- [X] Room/panels/StoryPanel/NodeDisplay.tsx migrated
- [X] Custom renderContent prop still works

**Part D: Validation:**
- [X] Regression tests pass
- [X] All formats render correctly
- [X] Visual regression check complete
- [X] New formats (code, svg, image, mdx) available

---

## 11. Transition to Phase 5

With Phase 4 complete:

1. **ContentRenderer is production-ready** across Story system
2. **Migration pattern established** for future consumers
3. **Common/ re-export provides stable import path**
4. **Ready for plugin system** formalization

### 11.1 Phase 5 Scope (from integrated-spec Section 14.5)

Phase 5 Plugin System work:

1. Formalize `Plugin<T>` interface
2. Add plugin registration API
3. Document plugin authoring guide
4. Enable third-party format extensions

### 11.2 Future Considerations

- **Shared NodeDisplay:** Page/ and Room/ versions are identical; consider consolidation
- **Bundle optimization:** Tree-shake unused renderers based on format usage
- **Server-side rendering:** Consider SSR-compatible MDX compilation path

---

## Appendix A: Quick Reference

### Import Pattern

```typescript
// Recommended for new code
import {
  ContentRenderer,
  type Content,
  type ContentVariant,
} from "@/components/Common/ContentRenderer"

// For migration (node objects)
import {
  ContentRenderer,
  nodeToContent,
} from "@/components/Common/ContentRenderer"

// For migration (raw strings)
import {
  ContentRenderer,
  toContent,
} from "@/components/Common/ContentRenderer"
```

### Basic Usage

```typescript
// From StoryNodePublic
<ContentRenderer
  content={nodeToContent(node, "page")}
  safeMode={true}
/>

// From raw content
<ContentRenderer
  content={{
    format: "markdown",
    value: "# Hello World",
    metadata: { variant: "card" }
  }}
  safeMode={true}
/>

// With all options
<ContentRenderer
  content={content}
  variant="page"
  safeMode={true}
  theme={{ codeTheme: "github-dark" }}
/>
```

---

*Phase 4 Implementation Guide. Builds on Phase 3 validation. Migration to unified ContentRenderer.*
