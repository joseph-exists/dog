/**
 * ContentRenderer - Public Exports
 *
 * Primary export: ContentRenderer component
 * Type exports: Content, ContentFormat, ContentVariant, etc.
 */

// Main component
export { ContentRenderer } from "./ContentRenderer"

// Types (re-exported for consumer convenience)
export type {
  Content,
  ContentFormat,
  ContentVariant,
  ContentMetadata,
  ContentProps,
  ContentRendererProps,
  ThemeConfig,
  ContentTrustLevel,
  // Format-specific options
  CodeContentOptions,
  HTMLContentOptions,
  JSONContentOptions,
  SVGContentOptions,
  ImageContentOptions,
  MarkdownContentOptions,
  MDXContentOptions,
  // CodeHighlight
  CodeHighlightProps,
  ShikiTransformer,
  MDXComponents,
  MDXCompiledResult,
  MDXCompilationState,
  // Registry types
  Renderer,
  RendererEntry,
  Plugin,
  PluginRenderer,
  PluginRendererRegistry,
  PluginValidationResult,
  PluginValidationError,
  RegisteredPlugin,
  PluginRegistrationOptions,
  PluginResolutionResult,
} from "./types"

// Registry (for advanced use cases)
export { rendererRegistry, getRenderer } from "./registry"

export {
  registerPlugin,
  unregisterPlugin,
  getPlugin,
  getAllPlugins,
  hasPlugin,
  validateContent,
  transformContent,
  onPluginEvent,
  clearPlugins,
  disablePlugin,
  enablePlugin,
  getAllRenderersForFormat,
} from "./pluginRegistry"

// Individual renderers (for direct use or testing)
export { TextRenderer } from "./renderers/TextRenderer"
export { CodeRenderer } from "./renderers/CodeRenderer"
export { HTMLRenderer } from "./renderers/HTMLRenderer"
export { JSONRenderer } from "./renderers/JSONRenderer"
export { SVGRenderer } from "./renderers/SVGRenderer"
export { ImageRenderer } from "./renderers/ImageRenderer"
export { MarkdownRenderer } from "./renderers/MarkdownRenderer"
export { MDXRenderer } from "./renderers/MDXRenderer"

// Components
export { CodeHighlight } from "./components/CodeHighlight"
export { FallbackRenderer } from "./components/FallbackRenderer"

// Hooks
export { useThemeResolution } from "./hooks/useThemeResolution"
export { useMDXCompiler, clearMDXCache } from "./hooks/useMDXCompiler"