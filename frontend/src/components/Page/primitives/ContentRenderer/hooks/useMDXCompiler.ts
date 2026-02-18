/**
 * useMDXCompiler - Runtime MDX compilation hook
 *
 * Lazily loads @mdx-js/mdx and compiles MDX source to React components.
 * Uses dynamic import to avoid bundling the compiler for non-MDX content.
 */
import { useCallback, useEffect, useRef, useState } from "react"
import type { MDXCompilationState, MDXCompiledResult } from "../types"

// Cache for compiled MDX to avoid recompilation
const compilationCache = new Map<string, MDXCompiledResult>()

// Lazy-loaded compiler module
let compilerPromise: Promise<typeof import("@mdx-js/mdx")> | null = null

/**
 * Lazily load the MDX compiler
 */
async function getCompiler() {
  if (!compilerPromise) {
    compilerPromise = import("@mdx-js/mdx")
  }
  return compilerPromise
}

/**
 * Generate a cache key from MDX source
 */
function getCacheKey(source: string): string {
  // Simple hash for cache key
  let hash = 0
  for (let i = 0; i < source.length; i++) {
    const char = source.charCodeAt(i)
    hash = (hash << 5) - hash + char
    hash = hash & hash // Convert to 32-bit integer
  }
  return `mdx_${hash}`
}

/**
 * Compile MDX source to a React component
 */
async function compileMDX(source: string): Promise<MDXCompiledResult> {
  const cacheKey = getCacheKey(source)

  // Check cache first
  const cached = compilationCache.get(cacheKey)
  if (cached) {
    return cached
  }

  // Load compiler
  const { compile, run } = await getCompiler()

  // Compile MDX to JS
  const compiled = await compile(source, {
    outputFormat: "function-body",
    development: process.env.NODE_ENV === "development",
  })

  // Run the compiled code to get the component
  const { default: runtime } = await import("react/jsx-runtime")
  const result = await run(compiled, {
    ...runtime,
    baseUrl: import.meta.url,
  })

  // Cache and return
  compilationCache.set(cacheKey, result as MDXCompiledResult)
  return result as MDXCompiledResult
}

/**
 * Hook for runtime MDX compilation
 *
 * @param source - MDX source string
 * @param enabled - Whether to compile (false = skip compilation)
 * @returns Compilation state with result or error
 */
export function useMDXCompiler(
  source: string,
  enabled: boolean = true,
): MDXCompilationState {
  const [state, setState] = useState<MDXCompilationState>({
    status: "idle",
  })

  // Track current source to handle race conditions
  const sourceRef = useRef(source)
  sourceRef.current = source

  const compile = useCallback(async () => {
    if (!enabled || !source) {
      setState({ status: "idle" })
      return
    }

    setState({ status: "compiling" })

    try {
      const result = await compileMDX(source)

      // Check if source changed during compilation
      if (sourceRef.current !== source) {
        return // Discard stale result
      }

      setState({ status: "success", result })
    } catch (error) {
      // Check if source changed during compilation
      if (sourceRef.current !== source) {
        return
      }

      setState({
        status: "error",
        error: error instanceof Error ? error : new Error(String(error)),
      })
    }
  }, [source, enabled])

  useEffect(() => {
    compile()
  }, [compile])

  return state
}

/**
 * Clear the MDX compilation cache
 * Useful for development or memory management
 */
export function clearMDXCache(): void {
  compilationCache.clear()
}
