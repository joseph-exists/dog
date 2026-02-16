# Phase 2 Implementation Guide: MDX Wiring & Shiki Transformers

> "The best way to predict the future is to invent it."
> — Alan Kay

This guide provides step-by-step implementation instructions for Phase 2 of the ContentRenderer system. It includes:
1. **Shiki Transformer Integration** (deferred from Phase 1)
2. **Full MDX Renderer Implementation** (Phase 2 scope)

---

## 1. Prerequisites Checklist

Before implementing, verify:

- [x] Phase 1 complete (all core renderers working)
- [x] Backend has `mdx` in ContentFormat enum
- [x] `@mdx-js/mdx@3.1.1` installed
- [x] `react-shiki@0.9.1` with `shiki@3.22.0` installed
- [ ] Backend MDX compilation endpoint ready (or will use runtime-only initially)

### 1.1 Package Versions

```
@mdx-js/mdx: 3.1.1
react-shiki: 0.9.1
shiki: 3.22.0
@shikijs/transformers: 3.22.0
@shikijs/types: (included with shiki)
```

### 1.2 New Dependencies (if not installed)

```bash
# These should already be installed, verify with:
npm ls @shikijs/transformers @mdx-js/mdx

# If missing, install:
npm install @shikijs/transformers
```

### 1.3 Files to Modify (Approved)

Per integrated-spec Section 9.1 and Phase 1 precedent:

**Existing files to update:**
- `types.ts` - Add MDX types, update CodeHighlightProps for transformers
- `components/CodeHighlight.tsx` - Add transformer support
- `renderers/CodeRenderer.tsx` - Wire transformer options
- `renderers/MarkdownRenderer.tsx` - Wire transformer options
- `renderers/MDXRenderer.tsx` - Full implementation
- `hooks/useMDXCompiler.ts` - MDX runtime compilation
- `index.ts` - Add new exports

---

## 2. Implementation Order

Files must be implemented in this dependency order:

```
Part A: Shiki Transformers (Phase 1 Deferred)
═══════════════════════════════════════════════
1. types.ts                 ← Add transformer types to CodeHighlightProps
2. CodeHighlight.tsx        ← Implement transformer integration
3. CodeRenderer.tsx         ← Wire lineNumbers, highlightLines, startLine
4. MarkdownRenderer.tsx     ← Ensure transformers work in MD code blocks

Part B: MDX Implementation
═══════════════════════════════════════════════
5. types.ts                 ← Add MDXContentOptions, MDXComponents
6. useMDXCompiler.ts        ← Lazy-load runtime compilation
7. MDXRenderer.tsx          ← Compile-time + runtime paths
8. index.ts                 ← Export new types and hook
```

---

## 3. Part A: Shiki Transformer Integration

### 3.1 Update types.ts - Add Transformer Support

**Location:** `types.ts`

**Changes:** Extend `CodeHighlightProps.options` to include transformer-related options.

[ ] complete: review requested

**Note:** We import `ShikiTransformer` from `@shikijs/types` rather than defining our own. This ensures compatibility with `@shikijs/transformers` and future Shiki updates.

---

### 3.2 Update CodeHighlight.tsx - Implement Transformers

**Location:** `components/CodeHighlight.tsx`

**Changes:** Add line numbers, line highlighting, and start line support using Shiki transformers.

**Note on @shikijs/transformers:** The project has `@shikijs/transformers@3.22.0` installed, which provides pre-built transformers. However, there's no built-in line numbers transformer, so we create a custom one. The `transformerCompactLineOptions` can be used for line-specific styling.

[X] complete - needs review


### 3.2.5 tailwind semantic class overrides - pending review of pattern integrations
**CSS Required:** Add these styles to support line numbers and highlighting:

TODO: apply via tailwind override: 
```css
/* Add to global styles or component-level CSS */
.shiki-line-numbers {
  counter-reset: line;
}

.shiki-line-numbers .line {
  display: block;
}

.shiki-line-numbers .line::before {
  counter-increment: line;
  content: counter(line);
  display: inline-block;
  width: 2rem;
  margin-right: 1rem;
  text-align: right;
  color: var(--muted-foreground);
  opacity: 0.5;
}

/* Use data-line attribute when startLine is set */
.shiki-line-numbers .line[data-line]::before {
  content: attr(data-line);
}

.shiki-highlighted {
  background-color: rgba(255, 255, 0, 0.1);
  display: block;
  margin: 0 -1rem;
  padding: 0 1rem;
}
```

**Note:** If CSS-in-JS is preferred, these styles can be added via Tailwind's `@apply` or inline styles.

---

### 3.3 Update CodeRenderer.tsx - Wire Options

**Location:** `renderers/CodeRenderer.tsx`

**Changes:** Pass transformer options through to CodeHighlight.

[ ] complete, requires review

---

### 3.4 Update MarkdownRenderer.tsx - Enable Transformers

**Location:** `renderers/MarkdownRenderer.tsx`

**Changes:** Allow transformer options to flow through markdown code blocks.

[ ] complete, requires review

---

## 4. Part B: MDX Implementation

### 4.1 Update types.ts - Add MDX Types

**Location:** `types.ts`

**Changes:** Add MDXContentOptions, MDXComponents, and MDXRendererProps.

[ ] complete, review requested
---

### 4.2 Implement useMDXCompiler.ts

**Location:** `hooks/useMDXCompiler.ts`

**Purpose:** Lazy-load @mdx-js/mdx and compile MDX at runtime.

[ ] complete, review requested
---

### 4.3 Implement MDXRenderer.tsx

**Location:** `renderers/MDXRenderer.tsx`

**Purpose:** Full MDX rendering with compile-time and runtime paths.

[ ] complete - review requested.
---

### 4.4 Update index.ts - Add New Exports

**Location:** `index.ts`

**Changes:** Export new types and the useMDXCompiler hook.

[ ] complete, review requested
---

## 5. Testing Strategy

### 5.1 Shiki Transformer Testing

```typescript
// Test line numbers
<ContentRenderer
  content={{
    format: "code",
    value: `function hello() {\n  console.log("world")\n}`,
    metadata: {
      options: {
        language: "typescript",
        lineNumbers: true,
        startLine: 10,
      }
    }
  }}
/>

// Test line highlighting
<ContentRenderer
  content={{
    format: "code",
    value: `const a = 1\nconst b = 2\nconst c = 3`,
    metadata: {
      options: {
        language: "typescript",
        highlightLines: [1, 3],
      }
    }
  }}
/>
```

### 5.2 MDX Testing

```typescript
// Test runtime MDX compilation
<ContentRenderer
  content={{
    format: "mdx",
    value: `# Hello World\n\nThis is **MDX** content.\n\n\`\`\`typescript\nconst x = 1\n\`\`\``,
  }}
/>

// Test with custom components
<ContentRenderer
  content={{
    format: "mdx",
    value: `<CustomAlert>Important!</CustomAlert>`,
    metadata: {
      options: {
        components: {
          CustomAlert: ({ children }) => <div className="alert">{children}</div>
        }
      }
    }
  }}
/>

// Test safe mode (should filter custom components)
<ContentRenderer
  content={{
    format: "mdx",
    value: `<DangerousComponent />`,
  }}
  safeMode={true}
/>
```

### 5.3 Manual Testing Checklist

- [ ] Code blocks show line numbers when `lineNumbers: true`
- [ ] Line numbers start from `startLine` value
- [ ] Highlighted lines are visually distinct
- [ ] MDX compiles and renders basic markdown
- [ ] MDX renders code blocks with Shiki highlighting
- [ ] MDX custom components work when not in safeMode
- [ ] MDX custom components are filtered in safeMode
- [ ] MDX shows loading state during compilation
- [ ] MDX shows error state on compilation failure
- [ ] Compiled MDX (backend-provided) renders correctly

---

## 6. Success Criteria

Phase 2 is complete when:

1. **Shiki Transformers:**
   - [ ] `lineNumbers` option works in CodeRenderer and MarkdownRenderer
   - [ ] `highlightLines` visually highlights specified lines
   - [ ] `startLine` offsets line number display

2. **MDX Renderer:**
   - [ ] Runtime compilation path works (lazy-loads @mdx-js/mdx)
   - [ ] Compiled MDX path works (hydrates backend-compiled JS)
   - [ ] MDXComponents map applied correctly
   - [ ] safeMode filters to restricted components only
   - [ ] Code blocks in MDX use Shiki highlighting

3. **Exports:**
   - [ ] All new types exported from index.ts
   - [ ] useMDXCompiler hook exported and documented

---

## 7. Paradigm Conflicts Resolved

| Conflict from Phase 1 | Resolution in Phase 2 |
|-----------------------|----------------------|
| Line numbers not implemented | ✅ Shiki transformer `lineNumbers` |
| highlightLines not implemented | ✅ Shiki transformer `highlightLines` |
| startLine not implemented | ✅ Shiki transformer `startLine` |
| MDXRenderer stub | ✅ Full implementation with runtime + compiled paths |

---

## 8. Open Items Remaining

| Item | Status | Notes |
|------|--------|-------|
| decorationHint wiring | Deferred | Can be added to useThemeResolution when design system requires |
| JSON tree interactive mode | Deferred | Basic text mode works; tree needs library (Phase 3+) |
| Backend MDX compilation API | External | Frontend ready; backend integration pending |

---

## 9. Holistic Review

### 9.1 Data Flow with Transformers

```
CodeRenderer receives content with options
       │
       ├── options.lineNumbers = true
       ├── options.highlightLines = [2, 4]
       ├── options.startLine = 10
       │
       ▼
CodeHighlight receives options
       │
       ├── Creates lineNumbers transformer
       ├── Creates highlightLines transformer
       │
       ▼
ShikiHighlighter with transformers
       │
       ▼
Rendered code with line numbers and highlights
```

### 9.2 MDX Compilation Flow

```
MDXRenderer receives content
       │
       ├── content.value is string?
       │   │
       │   ▼ YES: Runtime path
       │   useMDXCompiler(source)
       │       │
       │       ├── Lazy-load @mdx-js/mdx
       │       ├── Compile source to JS
       │       ├── Run JS to get React component
       │       ├── Cache result
       │       │
       │       ▼
       │   <MDXContent components={...} />
       │
       └── content.value has .default?
           │
           ▼ YES: Compiled path
           <CompiledMDXRenderer compiled={value} />
               │
               ▼
           <MDXContent components={...} />
```

### 9.3 Security Model Update

```
safeMode: true (default)
  ├── HTML: DOMPurify sanitization
  ├── SVG: Rendered as <img> data URL
  └── MDX: RESTRICTED_COMPONENT_NAMES only ← NEW
           (h1-h6, p, strong, em, ul, ol, li,
            blockquote, a, img, hr, table elements,
            pre, code)

safeMode: false
  ├── HTML: Minimal sanitization
  ├── SVG: Can render inline
  └── MDX: Full component access ← NEW
           (custom components allowed)
```

---

*Phase 2 Implementation Guide. Builds on Phase 1 foundation. Aligned with integrated-spec.md.*
