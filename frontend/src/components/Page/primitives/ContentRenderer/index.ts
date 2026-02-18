/**
 * ContentRenderer - Public Exports
 *
 * Primary export: ContentRenderer component
 * Type exports: Content, ContentFormat, ContentVariant, etc.
 */

// Main component
export { ContentRenderer } from "./ContentRenderer"
// Components
export { CodeHighlight } from "./components/CodeHighlight"
export { FallbackRenderer } from "./components/FallbackRenderer"
export { clearMDXCache, useMDXCompiler } from "./hooks/useMDXCompiler"
// Hooks
export { useThemeResolution } from "./hooks/useThemeResolution"
export {
  clearPlugins,
  disablePlugin,
  enablePlugin,
  getAllPlugins,
  getAllRenderersForFormat,
  getPlugin,
  hasPlugin,
  onPluginEvent,
  registerPlugin,
  transformContent,
  unregisterPlugin,
  validateContent,
} from "./pluginRegistry"
// Registry (for advanced use cases)
export { getRenderer, rendererRegistry } from "./registry"
export { CodeRenderer } from "./renderers/CodeRenderer"
export { HTMLRenderer } from "./renderers/HTMLRenderer"
export { ImageRenderer } from "./renderers/ImageRenderer"
export { JSONRenderer } from "./renderers/JSONRenderer"
export { MarkdownRenderer } from "./renderers/MarkdownRenderer"
export { MDXRenderer } from "./renderers/MDXRenderer"
export { SVGRenderer } from "./renderers/SVGRenderer"
// Individual renderers (for direct use or testing)
export { TextRenderer } from "./renderers/TextRenderer"
// Types (re-exported for consumer convenience)
export type {
  // Format-specific options
  CodeContentOptions,
  // CodeHighlight
  CodeHighlightProps,
  Content,
  ContentFormat,
  ContentMetadata,
  ContentProps,
  ContentRendererProps,
  ContentTrustLevel,
  ContentVariant,
  HTMLContentOptions,
  ImageContentOptions,
  JSONContentOptions,
  MarkdownContentOptions,
  MDXCompilationState,
  MDXCompiledResult,
  MDXComponents,
  MDXContentOptions,
  Plugin,
  PluginRegistrationOptions,
  PluginRenderer,
  PluginRendererRegistry,
  PluginResolutionResult,
  PluginValidationError,
  PluginValidationResult,
  RegisteredPlugin,
  // Registry types
  Renderer,
  RendererEntry,
  ShikiTransformer,
  SVGContentOptions,
  ThemeConfig,
} from "./types"
