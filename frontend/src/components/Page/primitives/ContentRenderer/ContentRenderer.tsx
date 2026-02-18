/**
 * ContentRenderer - Main dispatcher for polymorphic content
 *
 * Routes content.format to appropriate renderer from registry.
 * Handles theme resolution, variant propagation, and fallback.
 */
import { useMemo } from "react"
import { FallbackRenderer } from "./components/FallbackRenderer"
import { useThemeResolution } from "./hooks/useThemeResolution"
import { transformContent, validateContent } from "./pluginRegistry"
import { resolveRenderer } from "./registry"
import type { ContentRendererProps, PluginValidationResult } from "./types"

export function ContentRenderer({
  content,
  variant,
  safeMode = true,
  fallback: FallbackComponent = FallbackRenderer,
  // decorationHint reserved for future theme integration
  decorationHint: _decorationHint,
  theme,
  className,
}: ContentRendererProps) {
  // Resolve variant: props override > content.metadata > default
  const resolvedVariant = variant ?? content.metadata?.variant ?? "card"

  // Theme resolution (codeTheme available for future use in augmentedContent pattern)
  const { codeTheme: _codeTheme } = useThemeResolution({
    content,
    propsTheme: theme,
  })

  // Apply plugin transforms
  const transformedContent = useMemo(() => {
    return transformContent(content)
  }, [content])

  // Run plugin validators (for debugging/preview - doesn't block render)
  const validation = useMemo<PluginValidationResult>(() => {
    return validateContent(transformedContent)
  }, [transformedContent])

  // Log validation warnings in development
  if (process.env.NODE_ENV === "development" && validation.errors.length > 0) {
    console.warn("ContentRenderer validation issues:", validation.errors)
  }

  // Resolve renderer (plugins first, then core)
  const resolution = resolveRenderer(transformedContent.format)

  if (!resolution) {
    return <FallbackComponent content={transformedContent} />
  }

  const { renderer, plugin, isOverride } = resolution
  const RendererComponent = renderer.Component

  // Debug logging in development
  if (process.env.NODE_ENV === "development" && isOverride) {
    console.debug(
      `ContentRenderer: Using plugin "${plugin?.id}" for format "${transformedContent.format}"`,
    )
  }

  return (
    <RendererComponent
      content={transformedContent}
      variant={resolvedVariant}
      safeMode={safeMode}
      className={className}
    />
  )
}

// // Get renderer for this format
// const renderer = getRenderer(content.format)

// if (!renderer) {
//   // Use custom fallback or default
//   if (fallback) {
//     const FallbackComponent = fallback
//     return <FallbackComponent {...content} />
//   }
//   return <FallbackRenderer content={content} />
// }

// Augment content with theme if not already set
// This enables the cascade: props.theme → content.metadata.options.theme
//   const augmentedContent: Content = theme?.codeTheme
//     ? {
//         ...content,
//         metadata: {
//           ...content.metadata,
//           options: {
//             ...content.metadata?.options,
//             // Only set if not already specified in content
//             theme: (content.metadata?.options as { theme?: string })?.theme ?? theme.codeTheme,
//           },
//         },
//       }
//     : content

//   // Render with resolved props
//   const { Component } = renderer
//   return (
//     <Component
//       content={augmentedContent}
//       variant={resolvedVariant}
//       safeMode={safeMode}
//       className={className}
//     />
//   )
// }
