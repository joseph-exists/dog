##  Define a ContentRenderer component that:

1: Accepts a tuple: polymorphic content value, format.
 # TODO: review if we want decoration hints, semantic classes, and content overrides to apply - my intuition says yes, so we may want to leave an extensibility door here. 

2: Safely renders HTML, text, MDX‑like Markdown, JSON, SVG, and images (and future formats). 
# josep note: non-negotiable requirements.  we already have all of this - if we don't at least meet our current bar, this will be a useless exercise. Always be thinking about the past and the future while being present in the now: we must uphold the work we've done without regressions.  We must maintain stellar quality and usability for our users.  We must create the foundations for the future implementation in a way that is kind and helpful for the engineers who come after us.

3: Supports extensibility so that new formats and renderers can be added without breaking the core schema.
# incredibly critical.

4: Satisfies current component requirements for compositionality and structure. Can have multiple siblings/cousin containers within PageShell hierarchy.

5: Sheer majority of processing lives on the backend. If we need something, we can state that we need it and it will be built.  If we need to buy something, we can buy it.  Do not invent wheels that are the same as a thousand other wheels - we're only inventing wheels if they are better in some way.

6: i spy an enum coming.  if we have an enum, remember to add test, empty, unknown, and full - and do not be afraid to add a larger set of 'possibles' than we're going to shoot for with this iteration.  adding the enum is one of the trickier parts of our integrative dev environment, so let's just do the dang thing once until we *need* to iterate.

## Core type model

// ———————————————————————————————————————
// 1. Content format taxonomy
// ———————————————————————————————————————

enum ContentFormat {
  Text = "text",
  Markdown = "markdown",
  MDX = "mdx",        // MDX-like / JSX‑enabled content
  HTML = "html",
  JSON = "json",
  SVG = "svg",
  Image = "image",
  // Future examples:
  // YAML = "yaml",
  // XML = "xml",
  // Audio = "audio",
  // Video = "video",
}

// ———————————————————————————————————————
// 2. Generic content payload
// ———————————————————————————————————————

type ContentValue =
  | string              // for text, markdown, html, svg, JSON as string
  | unknown;            // for rich JSON objects, etc.

interface Content<T extends ContentFormat = ContentFormat> {
  format: T;
  value: ContentValue;
  // Optional metadata for UX/design
  metadata?: {
    /** When UX wants to treat this as a “snippet” vs “full page” */
    variant?: "inline" | "page" | "card";
    /** Optional heading level or label hint */
    label?: string;
    /** Optional constraints imposed by the content source */
    constraints?: {
      /** If non‑trusted, HTML/MDX must be heavily sanitized */
      isTrustedSource: boolean;
    };
  };
}

// Helper for type‑narrowed content
type TextContent = Content<ContentFormat.Text>;
type MarkdownContent = Content<ContentFormat.Markdown>;
type MDXContent = Content<ContentFormat.MDX>;
type HTMLContent = Content<ContentFormat.HTML>;
type JSONContent = Content<ContentFormat.JSON>;
type SVGContent = Content<ContentFormat.SVG>;
type ImageContent = Content<ContentFormat.Image>;


## Renderer contract and registry

// ———————————————————————————————————————
// 1. Renderer interface
// ———————————————————————————————————————

interface Renderer<T extends ContentFormat> {
  /** Format this renderer handles */
  format: T;
  /** Render function */
  Component: React.FC<ContentProps<T>>;
}

// ———————————————————————————————————————
// 2. Content‑specific prop shapes
// ———————————————————————————————————————

type ContentProps<T extends ContentFormat> = Content<T> & {
  /** Optional override behavior; e.g., “truncate long text” */
  options?: any;
};

// Concretizations:
type TextRendererProps = ContentProps<ContentFormat.Text>;
type MarkdownRendererProps = ContentProps<ContentFormat.Markdown>;
type MDXRendererProps = ContentProps<ContentFormat.MDX>;
type HTMLRendererProps = ContentProps<ContentFormat.HTML>;
type JSONRendererProps = ContentProps<ContentFormat.JSON>;
type SVGRendererProps = ContentProps<ContentFormat.SVG>;
type ImageRendererProps = ContentProps<ContentFormat.Image>;

// ———————————————————————————————————————
// 3. Renderer registry
// ———————————————————————————————————————

type RendererRegistry = {
  [K in ContentFormat]: Renderer<K>;
};

/**
 * Core contract for ContentRenderer:
 * Given a Content<T>, picks the appropriate entry from RendererRegistry.
 */
type ContentRendererProps = {
  content: Content;
  /**
   * Optional additional renderers.
   * Pluggable formats / custom renderers can be merged here.
   */
  renderers?: Partial<RendererRegistry>;
  /**
   * If true, renderers must be “safe”: HTML/MDX sanitized, etc.
   * If false, assumes trusted source and may allow richer/less‑sanitized rendering.
   */
  safeMode?: boolean;
  /**
   * Optional global controls for UX variants.
   */
  variant?: "inline" | "page" | "card";
  /**
   * Fallback UI for unsupported formats.
   * Defaults to a simple “unsupported content” message + raw value preview.
   */
  fallback?: React.FC<Content>;
};


## Model-specific constraints and invariants

// ———————————————————————————————————————
// 1. Text renderer constraints
// ———————————————————————————————————————

/**
 * For `Content<ContentFormat.Text>`:
 * - value must be a string.
 * - No HTML/JSX; treated as plain text.
 *
 * UX may allow:
 * - `metadata.variant = "inline"`: short snippet, no line breaks.
 * - `metadata.variant = "page"`: long text, line breaks, scrolling.
 * - `metadata.variant = "card"`: compact, limited height.
 */
type TextConstraints = {
  [K in ContentFormat.Text]: {
    value: string;
  };
};

// ———————————————————————————————————————
// 2. Markdown vs MDX trade‑off
// ———————————————————————————————————————

/**
 * Markdown renderer (`markdown`):
 * - value is a string containing Markdown.
 * - Does **not** allow JSX or inline React components.
 * - Parsed via a Markdown‑to‑React layer (e.g., React‑Markdown‑like).
 */
type MarkdownConstraints = {
  [K in ContentFormat.Markdown]: {
    value: string;
    options?: {
      /**
       * If true, does not render any interactive elements (e.g., links).
       * Useful for previews or read‑only contexts.
       */
      readonly?: boolean;
    };
  };
};

/**
 * MDX renderer (`mdx`):
 * - value is a string containing MDX‑like syntax.
 * - Can include JSX‑style components embedded in the content.
 * - Requires:
 *   - A runtime or pre‑compiled MDX layer (e.g., `@mdx-js/react`).
 *   - A components map (`MDXComponents`) for headings, code blocks, etc.
 *   - Strong security model (trusted source only, or strict sanitization).
 */
type MDXConstraints = {
  [K in ContentFormat.MDX]: {
    value: string;
    // Optional MDX‑specific options
    options?: {
      /**
       * If true, only allow a whitelisted subset of components.
       */
      restrictedComponents?: boolean;
      /**
       * Map of React components that can be used inside MDX.
       * This is typically supplied via `MDXProvider`‑style configuration.
       */
      components?: MDXComponents;
    };
  };
};

// Import‑like placeholder for MDX types (implementation detail, not in the spec)
interface MDXComponents {
  [key: string]: React.ComponentType<any> | undefined;
}

// ———————————————————————————————————————
// 3. HTML renderer constraints
// ———————————————————————————————————————

/**
 * HTML renderer (`html`):
 * - value is a string containing serialized HTML.
 * - When `safeMode: true`, must be sanitized (e.g., via DOMPurify).
 * - When `safeMode: false`, may allow more permissive HTML.
 */
type HTMLConstraints = {
  [K in ContentFormat.HTML]: {
    value: string;
    options?: {
      /**
       * If true, assume source is unsafe and sanitize aggressively.
       */
      sanitize?: boolean;
      /**
       * Custom sanitizer options (e.g., allowed tags).
       * Mapped conceptually to DOMPurify‑style config.
       */
      sanitizerConfig?: unknown;
    };
  };
};

// ———————————————————————————————————————
// 4. JSON renderer constraints
// ———————————————————————————————————————

/**
 * JSON renderer (`json`):
 * - value can be:
 *   - a string (parsable JSON)
 *   - or an already‑parsed object/array.
 */
type JSONConstraints = {
  [K in ContentFormat.JSON]: {
    value: string | unknown;
    options?: {
      /**
       * Render as formatted string in `<pre><code>` or as an interactive tree.
       */
      viewMode?: "text" | "tree";
      /**
       * If true, enable expand/collapse for nested objects.
       */
      interactive?: boolean;
    };
  };
};

// ———————————————————————————————————————
// 5. SVG renderer constraints
// ———————————————————————————————————————

/**
 * SVG renderer (`svg`):
 * - value is a string containing `<svg>`‑like content.
 * - If `safeMode: true`, SVG must be sanitized (e.g., stripped of `script`).
 */
type SVGConstraints = {
  [K in ContentFormat.SVG]: {
    value: string;
    options?: {
      /** If true, render as inline <svg>; otherwise, as <img> */
      inline?: boolean;
    };
  };
};

// ———————————————————————————————————————
// 6. Image renderer constraints
// ———————————————————————————————————————

/**
 * Image renderer (`image`):
 * - value is a URL (or data‑URI / object‑URL).
 * - Metadata may include alt, dimensions, lazy‑load hints.
 */
type ImageConstraints = {
  [K in ContentFormat.Image]: {
    value: string;
    metadata?: {
      alt?: string;
      width?: number;
      height?: number;
      loading?: "eager" | "lazy";
    };
  };
};

## Extensibility and plugin contracts

// ———————————————————————————————————————
// 1. Plugin‑renderable format
// ———————————————————————————————————————

/**
 * A plugin can register a new format by:
 * - Adding a new item to `ContentFormat` (via declaration merging).
 * - Adding a new renderer to `RendererRegistry`.
 * - Providing a `ContentProps<T>` for that format.
 */

type PluginFormat =
  | ContentFormat.Text
  | ContentFormat.Markdown
  | ContentFormat.MDX
  | ContentFormat.HTML
  | ContentFormat.JSON
  | ContentFormat.SVG
  | ContentFormat.Image
  // Plus custom formats added by plugins.

type PluginRenderer<T extends PluginFormat> = Renderer<T> & {
  /** Plugin‑specific metadata */
  meta?: {
    /** Plugin name / ID */
    pluginId: string;
    /** Human‑readable label */
    label: string;
    /** When this renderer is preferred over others */
    priority?: number;
  };
};

type PluginRendererRegistry = {
  [K in PluginFormat]: PluginRenderer<K>;
};

// ———————————————————————————————————————
// 2. Plugin integration contract
// ———————————————————————————————————————

interface Plugin<
  T extends ContentFormat = ContentFormat,
  Props extends ContentProps<T> = ContentProps<T>
> {
  /** Unique plugin identifier */
  id: string;
  /**
   * Renderers provided by this plugin.
   * Overridden renderers replace the default ones.
   */
  renderers: Partial<PluginRendererRegistry>;
  /**
   * Optional validator for the plugin’s content.
   * Returns errors for invalid content.
   */
  validate?(content: Content): Array<Error> | null;
  /**
   * Optional transform applied before rendering.
   * Useful for:
   *  - Preprocessing MDX / Markdown.
   *  - Adding default metadata.
   */
  transform?(content: Content): Content;
}

/**
 * Example: MDX plugin that wants to control:
 * - Components map
 * - Sanitization
 * - Whether to treat MDX as “trusted”
 */
type MDXPlugin = Plugin<ContentFormat.MDX, MDXRendererProps> & {
  id: "mdx";
  renderers: {
    [ContentFormat.MDX]: PluginRenderer<ContentFormat.MDX>;
  };
};


## security and trust model

// ———————————————————————————————————————
// 1. Source trust levels
// ———————————————————————————————————————

enum ContentTrustLevel {
  /** No HTML, no JS; safe for anonymous user‑generated content */
  None = "none",
  /** Trusted: can render HTML/MDX with minimal sanitization */
  Trusted = "trusted",
  /** Moderated: can render HTML/MDX with configurable sanitization */
  Moderated = "moderated",
}

/**
 * Content with `metadata.constraints.isTrustedSource` implicitly sets trust level.
 * `safeMode` at the renderer level can downgrade trust level.
 */

// ———————————————————————————————————————
// 2. Security implications per format
// ———————————————————————————————————————

interface SecurityConstraints {
  [ContentFormat.Text]: {
    /** No security risk; always safe */
    riskyFeatures: [];
  };
  [ContentFormat.Markdown]: {
    riskyFeatures: [];
  };
  [ContentFormat.MDX]: {
    riskyFeatures: [
      "jsx_components",
      "inline_scripts",
      "arbitrary_html",
    ];
  };
  [ContentFormat.HTML]: {
    riskyFeatures: [
      "scripts",
      "iframes",
      "arbitrary_html",
    ];
  };
  [ContentFormat.JSON]: {
    /** Not inherently risky */
    riskyFeatures: [];
  };
  [ContentFormat.SVG]: {
    riskyFeatures: [
      "scripts",
      "external_refs",
    ];
  };
  [ContentFormat.Image]: {
    /** Can be abused via tracking, but not code execution */
    riskyFeatures: [
      "tracking_pixels",
    ];
  };
}

## design and ux oriented contracts

// ———————————————————————————————————————
// 1. UX variant model
// ———————————————————————————————————————

type ContentVariant = "inline" | "card" | "page" | "hero" | "dialog";

/**
 * UX‑oriented contract:
 * Each format can define how it behaves in different variants.
 * Example:
 * - `inline`: short, no scrolling, no headings.
 * - `card`: limited height, scrollable body.
 * - `page`: full‑page layout, headings, TOC, etc.
 */

interface UXContract<T extends ContentFormat> {
  /** Which variants are supported for this format */
  supportedVariants: ContentVariant[];
  /** Default variant if not specified */
  defaultVariant: ContentVariant;
  /** Whether this format is “scrollable” by default */
  scrollable: boolean;
}

// Example: MDX UX contract
type MDXUXContract = UXContract<ContentFormat.MDX>;

const defaultMDXUXContract: MDXUXContract = {
  supportedVariants: ["page", "card"],
  defaultVariant: "page",
  scrollable: true,
};

// ———————————————————————————————————————
// 2. Animation and interaction hints
// ———————————————————————————————————————

interface InteractionHints {
  /** Whether this content may contain interactive elements (links, buttons, etc.) */
  interactive: boolean;
  /** Whether this content may trigger animations or transitions */
  animatable: boolean;
  /** Optional animation set to apply (e.g., “fade‑in”, “slide‑from‑bottom”) */
  animation?: string;
}

type UXProps = {
  variant?: ContentVariant;
  interactionHints?: InteractionHints;
};


---

## 🔍 REVIEW: Questions & Comments from Claude (2024-02-14)

### High-Level Architecture Questions

**Q1: File location and import paths?**
Where does this live in the component hierarchy? Suggestions:
- `@/components/Common/ContentRenderer/` (shared across Page/Story/Room)
- `@/components/Page/primitives/ContentRenderer/` (Page-centric)
- `@/lib/content-renderer/` (utility-level)
josep-answer: we should think about *what* should live *where* - and we shouldn't be afraid of decomposing and overloading.  We need A) the Page-centric primitive - when folks clone Page/ to make new top level component structures, they should have a full library accessible.  we need B) the Common/ component.  when components (like Story, or Agent, or Room, need to import, this is where they should import from.)  we may need C, but we would need to think through why, and the justification, and if that actually maps to our patterns.  

Current duplication exists in:
- `Story/StoryPlayer/StoryContent.tsx` → `renderContent()`
- `Story/StoryPlayer/StoryPreview.tsx` → `renderContent()`
- `Story/StoryPlayer/StoryPlayer.tsx` → `renderContent()`
- `Page/panels/StoryPanel/NodeDisplay.tsx` → `renderNodeContent()`
- `Room/panels/StoryPanel/NodeDisplay.tsx` → `renderNodeContent()`
josep-answer: great question! Hopefully, this allows us to minimize this duplication. this can be an import for each of the above. note for later: we will want to define how we manage overload/implementation signatures, as well as inline type imports.


**Q2: Backend enum alignment?**
The spec mentions "remember to add test, empty, unknown, and full" to the enum. Current backend `ContentFormat` from OpenAPI client is:
```typescript
type ContentFormat = "text" | "html" | "markdown" | "json"
```
Should the frontend enum be a superset, or should we propose backend changes first?
josep-answer: we will propose the backend changes first. those will be accepted. we need to make the full set of requests at once - which means a sophisticated understanding of what we will need.


**Q3: Integration with presentation/theming system?**
Story components have a `StoryPresentation` system with `decorationHint` (brutalist, ethereal) that affects typography. Should ContentRenderer:
- Accept a `theme` or `decorationHint` prop?
- Compose with a separate theme wrapper?
- Ignore theming entirely (caller wraps)?

josep-answer: we want to enable the choice for accepting decorationHint, theme, and potentially more props. some components or props may need to override or be overridden - this increases complexity tree, but significantly enhances the possibility set for our authors and our viewers.

---

### Format-Specific Questions

**Q4: Markdown - Code blocks and syntax highlighting?**
Current `ReactMarkdown` renders code blocks as plain `<pre><code>`. Do we want:
- `rehype-highlight` or `prism-react-renderer` for syntax highlighting?
- Language detection hints from the backend?
- This is a common "nice to have" that becomes load-bearing fast.

josep-answer: define what you mean by load-bearing. perfect question.

**Q5: MDX runtime complexity?**
MDX requires either:
- **Compile-time**: Pre-compile MDX to JS (not feasible for dynamic user content)
- **Runtime**: `@mdx-js/react` + `@mdx-js/mdx` (significant bundle size)

Is MDX actually needed, or would "markdown with custom component slots" suffice?
The security implications (arbitrary JSX) are non-trivial.

josep-answer: i'll think about this one. for now, assume that the backend will compile the mdx to js 'on save' - so MDX won't be dynamic in the viewer, until the content is saved. At the same time - we need a stubbed toggle for 'switching' that mode. this is a 'full stub' - we need to wire in the calls for compile time and pulling it back, and we need to wire in the calls the component would make to the runtime.

**Q6: SVG - inline vs img tradeoffs?**
The spec mentions `inline?: boolean`. Considerations:
- Inline SVG: Styleable via CSS, but XSS risk if not sanitized
- `<img src="data:image/svg+xml,...">`: Safe, but no CSS styling

Do we need both modes, or is one sufficient?
josep-response: both modes.  this will be based on the security model. for now, we will have a toggle and a tuneable on the component.

**Q7: Image - URL types?**
`value: string` for images could be:
- External URL (`https://...`)
- Data URI (`data:image/png;base64,...`)
- Blob URL (`blob:...`)
- Relative path (`/uploads/...`)

Should the renderer normalize these, or is that caller responsibility?

josep-response: let's think through this one a bit further in our implementation. it's a valid concern, but needs a bit more thought, and i may need to see the work in flight before I have a grasp on where it should live. 

---

### Implementation Concerns

**Q8: Error boundaries per format?**
What happens when:
- Markdown has invalid syntax
- JSON fails to parse
- Image URL 404s
- SVG is malformed

Should each format renderer have its own error boundary, or a single top-level one?
josep-response: it depends on where it is.  for preview - when an 'Author' is making a Story - just show the error in the preview. we can have guards at the 'save' and 'publish' levels where it's parsed and validated by the backend - or by the frontend if it's simple enough.  

**Q9: Dark mode handling?**
Current implementations use `prose-lg dark:prose-invert`. Should this be:
- Baked into the default renderers?
- Passed via UX props?
- Handled by a parent theme provider?

josep-response: let's remove it from the default renderer.  this is something that should be passed down from the parent.  this is based on the current StoryEditor, i believe - so we'll strip out all innate styling from the renderer and add it back in as/when we need it, in specific contexts.   

**Q10: Progressive enhancement / loading states?**
For heavy content (large markdown, big images), should renderers:
- Accept `Suspense` boundaries?
- Show skeleton loaders?
- Have their own loading states?

josep-response: yeah, maybe? we should lazyload and cache, accept Suspense, and have skeleton loaders such that we're not causing 'page jumps' when content loads in.

---

### Migration Path

**Q11: How do we get there from here?**
Proposed incremental approach:
1. Create `ContentRenderer` component with current formats (text, html, markdown, json)
2. Export a `renderContent()` helper for legacy call sites
3. Migrate `StoryContent`, `StoryPreview`, `StoryPlayer` to use shared renderer
4. Migrate `NodeDisplay` components
5. Add new formats (SVG, Image, MDX) as needed
6. Add plugin system once core is stable

Does this sequence make sense, or should we do a "big bang" migration?

josep-response: this incremental approach would be fine if our most important target was the migration to a shared renderer. While I agree that's an important consideration, this work is prioritized because it's the new formats that increase the quality and value of the system for users and operators.  Once the new content renderer proves more valuable, then we migrate, not before.  Does that make sense?

---

### Missing from Spec?

**Q12: Accessibility?**
No mention of:
- `aria-label` for non-text content
- `role` attributes
- Screen reader considerations for interactive JSON trees
- Alt text requirements for images

Should accessibility contracts be part of the format constraints?
josep-response: yes, but those are satisfied at a higher level of design and testing.  interactive-json trees won't be accessible by screen-readers through the component itself - those users will have a distinct interface which is already approved. 


**Q13: Testing strategy?**
Should the spec include:
- Unit test expectations per renderer?
- Visual regression testing approach?
- Security audit requirements (especially for HTML/MDX)?

---
josep-response: 
security audit happens on the backend, already handled.
unit test expectations: high, but will define once spec is agreed to.
visual regression testing: yes, pin this for now, not part of current process.

### Comments (Not Questions)

**C1: Love the plugin system design.** The `Plugin<T>` interface with `validate` and `transform` hooks is elegant. This will make it easy to add format-specific preprocessing (e.g., resolving internal links in markdown).
josep-response: yay!  I'm glad you think so.  it's going to be fun.

**C2: Security model is well thought out.** The `ContentTrustLevel` enum and per-format `riskyFeatures` documentation is exactly what we need for code review discussions.
josep-response: yes - will be required for some of our later work.

**C3: UX variants are flexible.** The `"inline" | "card" | "page" | "hero" | "dialog"` variants cover most use cases. Might want to add `"tooltip"` for hover previews?
josep-response: let's do it! what else might be valuable - if not for this iteration, for the future?

**C4: Consider a `"code"` format?** Distinct from JSON, for syntax-highlighted source code (Python, TypeScript, etc.). Could be:
```typescript
ContentFormat.Code = "code"
// with options like:
{ language: "typescript", lineNumbers: true, highlightLines: [3, 5] }
```
1000% agree!  beautiful idea, wonderful thinking.
---

### Next Steps (Claude's Recommendation)

1. **Align on Q1-Q3** before writing code (architecture decisions)
2. **Start with Q11's incremental approach** - get a working `ContentRenderer` with current formats
3. **Defer MDX (Q5)** until we have a concrete use case requiring JSX in content
4. **Add Q12 accessibility contracts** to the spec before implementation

Ready to discuss any of these points! 🚀

---

## 🔄 FOLLOW-UP: Continued Discussion (2024-02-14)

### Clarifications Requested

**Q4 Follow-up: Defining "load-bearing"**

You asked me to define "load-bearing" in the context of syntax highlighting. Here's what I mean:

**Load-bearing** describes a feature that:
1. Starts as a "nice to have" visual enhancement
2. Becomes something users/authors rely on for comprehension (code without highlighting is harder to read)
3. Eventually becomes assumed functionality—if it breaks or disappears, users perceive it as a regression
4. Other features get built assuming it exists (e.g., "copy code" buttons, line number references in documentation)

For syntax highlighting specifically:
- Once authors see their code blocks rendered with highlighting, they'll write content assuming that highlighting exists
- Documentation might say "see the highlighted line 3" or "the red keywords are..."
- Removing it later causes a worse UX than never having it

**Question**: Given this definition, should we:
- Include syntax highlighting in v1 (accept the load-bearing responsibility now)?
- Explicitly mark it as "preview/experimental" in v1 (set expectations)?
- Defer entirely until v2 (avoid the commitment)?

josep-response: perfect clarification. include syntax highlighting, accept the load-bearing responsibility now.
---

### Priority Alignment

**Q11 Follow-up: New formats first, migration second**

I hear you clearly on the priority shift. Let me reframe my understanding:

**Your priority order:**
1. **Prove value** → New formats (SVG, Image, MDX, Code) that aren't possible today
2. **Then consolidate** → Migrate existing `renderContent()` call sites once value is proven
3. **Not**: Fix existing duplication first and add formats incrementally

**This changes my implementation sequence to:**
1. Build `ContentRenderer` with NEW formats (SVG, Image, MDX, Code)
2. Keep existing `renderContent()` functions as-is initially
3. Demo the new capabilities in a specific context (Story? Page? Room?)
4. Once stakeholders see value, migrate legacy code to shared renderer

josep-response: yes, with the caveat/constraint that ContentRenderer should be developed with the knowledge that it will be integrated. When & if there are conflicts between paradigms or constructs, we document (at a high level of abstraction) what would need to change in the downstream to support the change, and why we made it - we are optimizing for user/operator value, while also knowing that we will be responsible for the migration.

**Clarifying questions:**
- Which context should be the "proving ground" for new formats? (I'd suggest a new Page or dedicated "Content Showcase" panel)

josep-response: a new Page clone: we should review whether 'Demo' suits this purpose, and if so, we can build from there - cloning in or importing after we implement in Page.

- Should new formats be available in the StoryEditor immediately, or gated behind a feature flag?

josep-response: immediately. it will help us test/refine/iterate. We don't start there, though - when we're ready to test a format in StoryEditor, then we pull it in from Page - through import, overload, or inline.

- When you say "proves more valuable"—what does success look like? User feedback? Author adoption? Specific use cases demonstrated?

josep-response: Specific use-cases - the experience of using both sides.  The StoryEditor 


---

### UX Variants Expansion

**C3 Follow-up: Additional variants beyond "tooltip"**

Adding `"tooltip"` is great. Here are other variants that might be valuable:

| Variant | Use Case | Characteristics |
|---------|----------|-----------------|
| `"tooltip"` | Hover previews | Very small, no scroll, truncated, dismisses on mouse-out |
| `"preview"` | Quick look (like macOS) | Medium size, possibly animated entrance, read-only |
| `"embed"` | Content within content (blockquotes, references) | Reduced chrome, subtle borders, nested context |
| `"fullscreen"` | Immersive viewing | No header/footer, focus mode, escape to dismiss |
| `"thumbnail"` | Grid views, cards | Fixed dimensions, cropped/scaled, click to expand |
| `"banner"` | Announcements, heroes with text | Full-width, limited height, prominent typography |
| `"drawer"` | Side panel content | Constrained width, full height, scrollable |
| `"modal"` | Dialog content | Centered, backdrop, dismissible |

**For this iteration**, I'd recommend:
- **Add now**: `tooltip`, `preview`, `embed` (covers common interactive patterns)
- **Defer**: `fullscreen`, `thumbnail`, `banner`, `drawer`, `modal` (these are more about layout containers than content rendering)

Does this align with your thinking?

josep-response: add now (tooltip, preview, embed, modal, thumbnail.) defer the others.

---

### MDX Implementation Scope

**Q5 Follow-up: Clarifying the "full stub" requirement**

You mentioned needing a "full stub" for MDX with compile-time backend and runtime toggles. Let me make sure I understand the wiring:

**Compile-time path (backend-compiled MDX):**
```
Author writes MDX → Save → Backend compiles to JS → Stores compiled output
Viewer requests content → Backend returns compiled JS → Frontend hydrates/renders
```

josep-response: yes.


**Runtime path (frontend-compiled MDX):**
```
Author writes MDX → Save → Backend stores raw MDX
Viewer requests content → Backend returns raw MDX → Frontend compiles + renders
```

**The stub needs to wire:**
1. API call shape for "save MDX content" (format indicator, raw content) 
2. API call shape for "get compiled MDX" (returns JS or render instructions)

josep-response: (backend API for both exists - after we add 'mdx' to ContentFormat)

3. Toggle mechanism in component: `useCompiledMDX: boolean`

josep-response: yes

4. Frontend MDX compiler as lazy-loaded module (not included in main bundle)

josep-response: yes. 

**Questions:**
- Does the backend MDX compilation exist today, or is this also new backend work?

josep-response:new backend work being designed outside of the scope of this plan.

frontend should expect (after the request is made to the backend team) that the call to get content for the component (API through service to "get compiled MDX" will return that object.)


- Should the toggle be per-content-item (stored in metadata) or per-user-session (preference)?

josep-response: pause on this until we're there.  we may need both - i need to finish working through the RBAC/trust system.

- For the runtime path stub, should it actually render, or just show "[MDX: Runtime mode not available]"?

josep-response: it has to render. 


---

### Backend Enum Request

**Q2 Follow-up: Full enum proposal for backend**

You mentioned we need a "sophisticated understanding" of what we'll need. Here's my proposed full `ContentFormat` enum for the backend request:

```python
class ContentFormat(str, Enum):
    # Core text formats
    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"

    # Structured data formats
    JSON = "json"
    YAML = "yaml"  # Future: config files, structured content

    # Rich content formats
    MDX = "mdx"
    CODE = "code"  # Per C4 discussion

    # Media formats
    SVG = "svg"
    IMAGE = "image"
    AUDIO = "audio"    # Future
    VIDEO = "video"    # Future

    # Special/meta formats
    EMPTY = "empty"      # Explicitly empty content
    UNKNOWN = "unknown"  # Format couldn't be determined
    TEST = "test"        # For testing purposes

    # Reserved for future
    # XML = "xml"
    # PDF = "pdf"
    # EMBED = "embed"  # External embeds (YouTube, etc.)
```

**Question**: Does this capture what you had in mind, or are there formats I'm missing?

josep-response: this is the right set!

---

### Remaining Concerns

**Concern 1: Code format details (from C4)**

For `ContentFormat.Code`, we need to decide on the options shape:

```typescript
type CodeContentOptions = {
  /** Programming language for syntax highlighting */
  language?: string;  // "typescript", "python", "bash", etc.
  /** Show line numbers */
  lineNumbers?: boolean;
  /** Lines to visually highlight (1-indexed) */
  highlightLines?: number[];
  /** Start line number (for snippets) */
  startLine?: number;
  /** Show filename/title bar */
  filename?: string;
  /** Enable copy button */
  copyable?: boolean;
};
```

josep-response: all of them.  if we're doing this, we should do it in one-shot - if we do it halfway, there's no value because people may think 'oh, it's missing copyable? this is kind of useless'.

**Concern 2: Theme/decoration passthrough**

You confirmed that we should "enable the choice for accepting decorationHint, theme, and potentially more props." This creates a prop interface like:

```typescript
type ContentRendererProps = {
  content: Content;
  // ... existing props ...

  // Theme integration
  decorationHint?: "brutalist" | "ethereal" | string;
  theme?: ThemeConfig;  // Need to define this
  overrides?: {
    typography?: Partial<TypographyConfig>;
    colors?: Partial<ColorConfig>;
  };
};
```

Is this the right level of granularity, or should theme be handled entirely by parent context providers?

josep-response: this is the right level of granularity - we accept theme from parent context providers, but allow the content object to override if it's specified.



---

### Updated Implementation Sequence

Based on your feedback, here's my revised plan:
josep-response: edited the plan - still needs revision to integrate last answers

**Phase 1: New Format Value Proof**
1. Create `@/components/Page/primitives/ContentRenderer/` with new formats
2. Implement: `SVG`, `Image`, `Code` renderers 

2.5. Implement `MDX` renderer.
  1. Implement backend API stubs for MDX compile flow
  2. Wire frontend toggle and lazy-loaded compiler

3. Add UX variants: `inline`, `card`, `page`, `tooltip`, `preview`, `embed`, `modal`, `thumbnail`
4. Demo in a visible location (new Page panel, Story content, Demo)


**Phase 3: Migration**
1. Create `@/components/Common/ContentRenderer/` that re-exports from Page/
2. Export `renderContent()` compatibility helper
3. Migrate `StoryContent`, `StoryPreview`, `StoryPlayer`
4. Migrate `NodeDisplay` components

**Phase 4: Polish**
1. Add syntax highlighting to Markdown code blocks
2. Add remaining UX variants
3. Plugin system formalization

Does this sequence align with your priorities?

---

Ready for your review! 📝

---

## 🔄 FINAL REVIEW: Open Items & Revised Plan (2024-02-14)

### Items Needing Clarification

**Open Item 1: Q11 Success criteria (incomplete response)**

Your response was:
> "Specific use-cases - the experience of using both sides. The StoryEditor"

This seems to have been cut off. Could you complete this thought? I want to understand what "success" looks like so we can design demos that prove value effectively.

josep-response: an author can use the story editor to add these contenttypes to a story.  a viewer/player can use the story player to watch/play that story.  these are the required success criteria - it has to be smooth, it has to be a good experience - well designed, sophisticated, and aligned with our standards for quality and exceptional user value.

**Open Item 2: Demo Page exploration**

You mentioned reviewing whether "Demo" suits the proving ground purpose. Should I:
- Explore the existing Demo route/components to assess suitability?
- Or is "Demo" a conceptual name for a new page we'd create?

josep-response - let's pin this as an open item, deferring until we believe we're ready. Once the components are ready for evaluation, I have stub/mock frameworks to prove them rapidly.

---

### ✅ Decisions Confirmed (No Further Questions)

| Item | Decision |
|------|----------|
| Syntax highlighting | Include in v1, load-bearing responsibility accepted |
| UX variants (v1) | `inline`, `card`, `page`, `tooltip`, `preview`, `embed`, `modal`, `thumbnail` |
| UX variants (deferred) | `fullscreen`, `banner`, `drawer` |
| Backend enum | Full set approved (text, markdown, html, json, yaml, mdx, code, svg, image, audio, video, empty, unknown, test) |
| Code format options | All options in v1 (language, lineNumbers, highlightLines, startLine, filename, copyable) |
| Theme handling | Accept from parent context, allow content object override |
| MDX toggle scope | Paused until RBAC/trust system is resolved |
| MDX runtime | Must actually render (not placeholder) |
| Dark mode | Remove from default renderer, passed from parent |
| StoryEditor integration | Immediately available when formats are ready |
| Migration constraint | Document downstream changes needed when paradigms conflict |

---

### 📋 Revised Implementation Plan (Integrating All Answers)

**Phase 1: New Format Value Proof**
1. Create `@/components/Page/primitives/ContentRenderer/`
2. Implement core renderers:
   - `Text` (baseline)
   - `Markdown` (with syntax highlighting via rehype-highlight/prism)
   - `HTML` (with DOMPurify sanitization, trust-level aware)
   - `JSON` (text + tree modes, expand/collapse)
   - `SVG` (inline + img modes, sanitization toggle)
   - `Image` (URL handling deferred to implementation)
   - `Code` (full options: language, lineNumbers, highlightLines, startLine, filename, copyable)
3. Implement UX variants: `inline`, `card`, `page`, `tooltip`, `preview`, `embed`, `modal`, `thumbnail`
4. Wire theme/decorationHint props with parent context fallback

**Phase 2: MDX Wiring**
1. Add `MDX` to backend ContentFormat enum (request to backend team)
2. Implement MDX renderer with:
   - Compile-time path: hydrate backend-compiled JS
   - Runtime path: lazy-load `@mdx-js/mdx`, compile + render
   - Toggle: `useCompiledMDX` (scope TBD pending RBAC)
3. Define MDXComponents whitelist

**Phase 3: Proving Ground Demo**
1. Review/create Demo page for showcasing all formats
2. Add ContentRenderer to StoryEditor (import from Page/)
3. Test all formats in authoring + viewing contexts
4. Document any paradigm conflicts discovered

**Phase 4: Migration**
1. Create `@/components/Common/ContentRenderer/` (re-exports from Page/)
2. Export `renderContent()` compatibility helper for gradual migration
3. Migrate: `StoryContent`, `StoryPreview`, `StoryPlayer`
4. Migrate: `Page/panels/StoryPanel/NodeDisplay`, `Room/panels/StoryPanel/NodeDisplay`

**Phase 5: Plugin System**
1. Formalize `Plugin<T>` interface
2. Add plugin registration API
3. Document plugin authoring guide

---

### Pre-Implementation Checklist

Before starting implementation, confirm:

- [ ] **Open Item 1**: Success criteria clarified
- [ ] **Open Item 2**: Demo page approach decided
- [ ] **Backend request**: ContentFormat enum expansion submitted
- [ ] **Spec update**: Update `ContentVariant` type in spec to include new variants

---

Ready for your final review! Once Open Items 1 & 2 are resolved, this spec is ready for implementation. 🚀
