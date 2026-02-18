/**
 * useThemeResolution - Resolves theme following cascade order
 *
 * Cascade (highest wins):
 * 1. content.metadata.options.theme
 * 2. props.theme
 * 3. Parent ThemeContext (future)
 * 4. Default
 */
import { useMemo } from "react"
import type { Content, ThemeConfig } from "../types"

const DEFAULT_CODE_THEME = "github-dark"

interface ThemeResolutionInput {
  content: Content
  propsTheme?: ThemeConfig
}

interface ResolvedTheme {
  codeTheme: string
  prose: boolean
}

export function useThemeResolution({
  content,
  propsTheme,
}: ThemeResolutionInput): ResolvedTheme {
  return useMemo(() => {
    // Extract content-level theme override
    const contentOptions = content.metadata?.options
    const contentTheme =
      contentOptions && "theme" in contentOptions
        ? (contentOptions as { theme?: string }).theme
        : undefined

    // Cascade resolution
    const codeTheme =
      contentTheme ?? propsTheme?.codeTheme ?? DEFAULT_CODE_THEME

    // Prose defaults to true unless explicitly disabled
    const prose = propsTheme?.prose ?? true

    return { codeTheme, prose }
  }, [content.metadata?.options, propsTheme])
}
