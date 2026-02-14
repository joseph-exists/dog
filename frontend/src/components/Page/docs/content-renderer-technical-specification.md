Below is a **technical specification for review** that consolidates the current design, your FastAPI/Postgres/Redis stack, and modern MDX/shiki best practices into a single coherent doc. It assumes your existing `ContentFormat` model and `CodeRenderer`/`CodeHighlight` contracts.

***

### 1. Goal

Define a **unified content‑rendering architecture** for:

- Static and dynamic content across `ContentFormat.Text`, `Markdown`, `MDX`, `HTML`, `JSON`, `SVG`, `Image`, and `Code` (with Shiki‑powered syntax highlighting).  
- A **FastAPI/PostgreSQL/Redis** backend that safely stores and serves MDX/Markdown content and supports both build‑time and runtime compilation.  

This spec is framework‑agnostic at the backend, but aligned with React 19, TypeScript, `@mdx-js/react`, `@mdx-js/runtime` (if needed), `react-shiki`, and your existing frontend deps.

***

### 2. Core content model

```ts
enum ContentFormat {
  Text = "text",
  Markdown = "markdown",
  MDX = "mdx",
  HTML = "html",
  JSON = "json",
  SVG = "svg",
  Image = "image",
  Code = "code",
  // josep-note: TODO: need to add the rest here
}

interface Content<T extends ContentFormat = ContentFormat> {
  id: string;           // e.g., UUID from Postgres
  format: T;
  value: string;       // raw text/MDX/Markdown/HTML/SVG/JSON/code text
  metadata?: {
    constraints?: {
      /**
       * If true, this content is from a trusted source (e.g., admin, internal docs).
       * If false, treat as user‑authored and restrict components and JS.
       */
      isTrustedSource: boolean;
      /**
       * Optional cache invalidation hint.
       */
      cacheKey?: string;
    };
    /**
     * UX variant: inline vs card vs page vs hero, etc.
     */
    variant?: "inline" | "card" | "page" | "hero" | "dialog";
    /**
     * Content‑specific options (e.g., theme, language, copyable, etc.).
     * Typed per format below.
     */
    options?: Record<string, unknown>;
  };
}
```

This `Content` model is used by:

- The backend (Postgres/Redis) to store content.  
- The frontend to decide rendering strategy (precompiled vs runtime‑compiled MDX, static HTML, Shiki highlighting, etc.).  

***

### 3. `ContentFormat.MDX` and `Markdown` lifecycle

Define two **lifecycle modes** for MDX/Markdown:

#### 3.1. Static / precompiled MDX (recommended)

Used for:

- Help docs, static pages, pre‑authed user guides, onboarding flows, etc.  
- Content that is known at build time and can be compiled ahead of time.

Pattern:

- Store MDX text in Postgres with `format: "mdx"` or `format: "markdown"` and `metadata.constraints.isTrustedSource: true`.  
- At build time (Vite), use `@mdx-js/loader` (or similar) to compile MDX → React component.  
- Fallback: pre‑render MDX to HTML or `shiki`‑highlighted HTML/CSS at build time so the frontend receives only static markup. [mdxjs](https://mdxjs.com/guides/syntax-highlighting/)

In the spec:

- `ContentFormat.MDX` with `isTrustedSource: true` ⇾ **precompiled component**; the frontend imports the resulting React component.  
- `ContentFormat.Markdown` with `isTrustedSource: true` ⇾ can be rendered via `react-markdown` or pre‑rendered to HTML.

#### 3.2. Dynamic / runtime‑compiled MDX

Used for:

- CMS‑style user‑authored content stored in Postgres and served by FastAPI.  
- Content that can be edited in the UI and rendered immediately.

Pattern:

- Store MDX text in Postgres with `format: "mdx"` and `metadata.constraints.isTrustedSource: boolean` reflecting the source.  
- Expose it via a FastAPI endpoint (e.g., `/api/content/:id`).  
- In the frontend:
  - For untrusted content, use a **restricted MDX runtime** (e.g., `@mdx-js/runtime` or `mdx-bundler` with a whitelisted component set). [github](https://github.com/orgs/mdx-js/discussions/1862)
  - For trusted content, allow richer MDX components but keep the runtime compact and auditable.

In the spec:

- `ContentFormat.MDX` with `isTrustedSource: false` ⇾ only a **whitelisted set of components** allowed; no arbitrary JSX.  
- `ContentFormat.MDX` with `isTrustedSource: true` ⇾ richer MDX set, but still scoped to `MDXComponents` map. [blog.onrr](https://blog.onrr.gov/implementing-mdx/)

***

### 4. Shiki and code highlighting contracts

```ts
// Conceptual type; exact shape comes from `react-shiki` ecosystem.
type ShikiTransformer = unknown;

interface CodeMetadata {
  language?: string;           // e.g., "tsx", "sql", "json"
  theme?: string;              // e.g., "github-dark", "ayu-dark"
  variant?: "inline" | "block";
  showLineNumbers?: boolean;
  copyable?: boolean;
  transformers?: ShikiTransformer[];
}

type ContentFormatCode = Content<ContentFormat.Code> & {
  metadata: CodeMetadata;
};

type CodeRendererProps = Content<ContentFormat.Code> & {
  theme?: string;
  transformers?: ShikiTransformer[];
  className?: string;
};
```

Two rendering entry points:

1. **Top‑level `ContentFormat.Code`**
   - Rendered by `CodeRenderer` via `ContentRenderer`’s `format` dispatch.  
   - Must use `react-shiki` or a Shiki‑compatible layer to produce highlighted HTML/CSS. [npmjs](https://www.npmjs.com/react-shiki)

2. **Code inside `ContentFormat.Markdown` or `MDX`**
   - `react-markdown`’s `components.code` is mapped to `CodeHighlight`:

     ```ts
     interface CodeHighlightProps {
       className?: string;
       children?: ReactNode;
       node?: Element;
       options?: {
         language?: string;
         theme?: string;
         forceBlock?: boolean;
         copyable?: boolean;
         transformers?: ShikiTransformer[];
       };
       onRendered?: () => void;
     }

     type CodeHighlightComponent = React.FC<CodeHighlightProps>;
     ```

   - `CodeHighlight` uses `shiki` / `react-shiki` for runtime highlighting only for dynamic content; for static content, Shiki can be done at build time. [mdxjs](https://mdxjs.com/guides/syntax-highlighting/)

In your spec, **Shiki** is:

- Allowed at build time for static MDX/Markdown (no runtime cost).  
- Allowed at runtime only for user‑authored MDX/Markdown or `ContentFormat.Code` blocks, with `transformers` as the extension point for diff highlighting, annotations, etc. [libhunt](https://www.libhunt.com/compare-mdx-vs-shiki)

***

### 5. MDX renderer and `MDXComponents` contract

```ts
type MDXComponents = {
  h1: React.ComponentType<any>;
  h2: React.ComponentType<any>;
  h3: React.ComponentType<any>;
  p: React.ComponentType<any>;
  strong: React.ComponentType<any>;
  em: React.ComponentType<any>;
  ul: React.ComponentType<any>;
  ol: React.ComponentType<any>;
  li: React.ComponentType<any>;
  blockquote: React.ComponentType<any>;
  code: React.ComponentType<CodeHighlightProps>;
  pre: React.ComponentType<React.PropsWithChildren<React.HTMLAttributes<HTMLPreElement>>>;
  // other custom components used in MDX (e.g., <Callout />, <Note />)
  [key: string]: React.ComponentType<any>;
};

type MDXRendererProps = Content<ContentFormat.MDX> & {
  /**
   * MDX component map.
   * Required for runtime MDX; optional for precompiled MDX.
   */
  components?: MDXComponents;
  /**
   * If true, only allow a whitelisted subset of components.
   */
  restricted?: boolean;
  /**
   * If true, treat MDX as untrusted and sanitize.
   */
  safeMode?: boolean;
};
```

Two modes:

- **Precompiled MDX**:
  - `MDXRenderer` just renders the imported React component; `components` is unused.  
  - FastAPI/Postgres store only the MDX source; build step compiles it.

- **Runtime MDX**:
  - `MDXRenderer` uses `@mdx-js/runtime` or equivalent, passing `components` and `restricted` to control which JSX tags are allowed.  
  - `safeMode` governs sanitization and execution surface (e.g., no `script` tags, no arbitrary components). [mdxjs](https://mdxjs.com/docs/using-mdx/)

***

### 6. Backend structure (FastAPI / Postgres / Redis)

#### 6.1. Data model



```ts

// josep-note: THIS IS NOT OUR DATA MODEL :)
// josep-note: using this will be yucky form,
// because this is not the right form.\
// the right form exists, but i have not added it to the doc
// on purpose - design the needed contracts and functionality first,
// then we will see if the shape of the data constructs suit that need.
// PostgreSQL (simplified conceptual)
interface DbContent {
  id: string;           // PK
  format: ContentFormat;
  value: string;        // MDX/Markdown/HTML/JSON/text/code block
  created_at: string;
  updated_at: string;
  constraints: {
    is_trusted_source: boolean;
  };
  metadata_json: object; // JSONB for metadata.options, variant, etc.
}
```

- Use `JSONB` for `metadata` so you can index variant‑like fields and cache keys.  
- Use UUIDs for `id` to align with distributed content–ID generation.

#### 6.2. API contract

```ts
// FastAPI endpoints

// josep-note: these are not actual - the endpoints exist, but not in the form below - and we'll be using the exported client sdk to interact with these endpoints, regardless.
// i'll add the correct ones when they are needed.
GET /api/content/{id}: Returns Content<T> (JSON)
POST /api/content: Create or update Content (with proper auth/permissions)
```

- `value` can be:
  - Raw MDX/Markdown for runtime‑compiled content.  
  - Pre‑rendered HTML or `shiki` output for static content.

#### 6.3. Redis caching

Use Redis as a **cache** for:

- Pre‑rendered MDX/Markdown → HTML (e.g., `content:<id>:html`).  
- Shiki‑highlighted code blocks (e.g., `code:<id>:<theme>`).

Contract:

- When `metadata.constraints.cacheKey` is present, Frontend can cache the rendered HTML or `shiki` blob.  
- FastAPI invalidates cache on content update (e.g., via `updated_at` or explicit `invalidate` hook). [reddit](https://www.reddit.com/r/reactjs/comments/1apws3b/syntax_highlighting_with_shiki_react_server/)

This reduces runtime MDX parsing and Shiki work on the client, especially for user‑authored content.

***

### 7. Frontend rendering architecture

#### 7.1. `ContentRenderer` contract

```ts
interface Renderer<T extends ContentFormat> {
  format: T;
  Component: React.FC<ContentProps<T>>;
}

type RendererRegistry = {
  [K in ContentFormat]: Renderer<K>;
};

type ContentRendererProps = {
  content: Content;
  renderers?: Partial<RendererRegistry>;
  safeMode?: boolean;
  variant?: "inline" | "card" | "page" | "hero" | "dialog";
  fallback?: React.FC<Content>;
};
```

- Responsible for format‑based dispatch:
  - `Text` ⇾ `TextRenderer`  
  - `Markdown` ⇾ `MarkdownRenderer` (possibly using `react-markdown` with `CodeHighlight`)  
  - `MDX` ⇾ `MDXRenderer` (precompiled if static, runtime‑compiled if dynamic)  
  - `HTML` ⇾ `HTMLRenderer` (with `dompurify` sanitization when `safeMode: true`)  
  - `JSON` ⇾ `JSONRenderer`  
  - `SVG` ⇾ `SVGRenderer`  
  - `Image` ⇾ `ImageRenderer`  
  - `Code` ⇾ `CodeRenderer` (with `react-shiki` integration) [legacy.reactjs](https://legacy.reactjs.org/docs/conditional-rendering.html)

#### 7.2. `MDX` and `Markdown` integration

- `MDXRenderer`:
  - If the content is **precompiled**, render the imported component.  
  - If it’s **runtime‑compiled**, use `@mdx-js/runtime` with `MDXComponents` and `restricted` flag. [github](https://github.com/orgs/mdx-js/discussions/1862)

- `MarkdownRenderer`:
  - Uses `react-markdown` with `components` including `CodeHighlight` for code blocks.  
  - Respects `metadata.variant` for inline vs block behavior. [stackoverflow](https://stackoverflow.com/questions/31875748/how-do-i-render-markdown-from-a-react-component)

This keeps your UX/design team’s desire for MDX‑like richness, but under an explicit security and performance model.

***

### 8. Security and trust model

```ts
enum ContentTrustLevel {
  None = "none",
  Moderated = "moderated",
  Trusted = "trusted",
}

interface SecurityPolicy {
  [ContentFormat.Text]: {
    riskyFeatures: [];
  };
  [ContentFormat.Markdown]: {
    riskyFeatures: [];
  };
  [ContentFormat.MDX]: {
    riskyFeatures: ["jsx_components", "inline_scripts", "arbitrary_html"];
  };
  [ContentFormat.HTML]: {
    riskyFeatures: ["scripts", "iframes", "arbitrary_html"];
  };
  [ContentFormat.SVG]: {
    riskyFeatures: ["scripts", "external_refs"];
  };
  [ContentFormat.Code]: {
    riskyFeatures: [];
  };
  [ContentFormat.JSON]: {
    riskyFeatures: [];
  };
  [ContentFormat.Image]: {
    riskyFeatures: ["tracking_pixels"];
  };
}
```

- When `safeMode: true` or `ContentTrustLevel.None/Moderated`:
  - `MDX` runtime must be **restricted** (no arbitrary components).  
  - `HTML`/`MDX` must be **sanitized** (e.g., via `DOMPurify`).  
  - `SVG` must be sanitized or rendered as `<img>` when possible. [skeleton](https://www.skeleton.dev/docs/react/integrations/code-block)

- When `ContentTrustLevel.Trusted`:
  - `MDX` can be fully featured, but still scoped to `MDXComponents`.  
  - `HTML`/`SVG` are allowed with minimal sanitization. [mdxjs](https://mdxjs.com/docs/using-mdx/)

This is codified in the `MDXRenderer` and `HTMLRenderer` implementations, but the spec declares the **policy boundary**.

***

### 9. Extensibility and plugin model

```ts
type PluginFormat =
  | ContentFormat.Text
  | ContentFormat.Markdown
  | ContentFormat.MDX
  | ContentFormat.HTML
  | ContentFormat.JSON
  | ContentFormat.SVG
  | ContentFormat.Image
  | ContentFormat.Code;

interface PluginRenderer<T extends PluginFormat> {
  format: T;
  Component: React.FC<ContentProps<T>>;
  meta: {
    pluginId: string;
    label: string;
    priority?: number;
  };
}

type PluginRendererRegistry = {
  [K in PluginFormat]: PluginRenderer<K>;
};
```

- Plugins can register new renderers for existing formats (e.g., a custom `MDXRenderer` for a CMS‑specific feature).  
- Shiki‑based enhancements (e.g., animated code blocks via `framer-motion`) can be expressed as `transformers` on `CodeRendererProps`. [joyofcode](https://joyofcode.xyz/animated-code-blocks-using-shiki)

***

### 10. Recommended recommendations for the review

- **Adopt MDX at build time** for static content and **reserve runtime MDX** for user‑authored CMS‑style MDX. [nextjs](https://nextjs.org/docs/pages/guides/mdx)
- **Use Shiki at build time** for static docs and **only at runtime** for dynamic code blocks, with `transformers` as the extensibility point. [libhunt](https://www.libhunt.com/compare-mdx-vs-shiki)
- **Enforce MDX restrictions** for untrusted content via `restricted` and `components` maps, and align with FastAPI/Postgres/Redis for caching and lifecycle. [kentcdodds](https://kentcdodds.com/blog/fixing-a-memory-leak-in-a-production-node-js-app)
- **Standardize on the `Content` / `ContentFormat` / `Renderer` model** across the spec so all new formats (e.g., `YAML`, `SQL`) follow the same pattern.

This spec is ready to be reviewed by:

- **Frontend team** (React/TypeScript/MDX/shiki concerns).  
- **Backend team** (FastAPI/Postgres/Redis content model and API contract).  
- **Design/UX** (who can sign off on MDX/Markdown/Code behavior and trust levels). [mdxjs](https://mdxjs.com/docs/getting-started/)