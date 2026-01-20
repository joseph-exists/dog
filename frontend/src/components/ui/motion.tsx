/**
 * Motion Configuration
 *
 * Shared animation configuration for consistent motion across the app.
 * Provides spring configs, transition presets, and reduce motion support.
 *
 * @example
 * ```tsx
 * import { springConfig, useReduceMotion } from "@/components/ui/motion"
 *
 * const reducedMotion = useReduceMotion()
 * <motion.div
 *   animate={{ scale: 1 }}
 *   transition={reducedMotion ? { duration: 0 } : springConfig.snappy}
 * />
 * ```
 */

import * as React from "react"
import { createContext, useContext, useEffect, useState } from "react"

// ============================================================================
// Spring Configurations
// ============================================================================

/**
 * Spring animation configurations
 *
 * - snappy: Quick, responsive feedback (buttons, drag)
 * - gentle: Smooth transitions (collapse, expand)
 * - bouncy: Playful motion (drop into place)
 */
export const springConfig = {
  snappy: { type: "spring" as const, stiffness: 500, damping: 30 },
  gentle: { type: "spring" as const, stiffness: 300, damping: 25 },
  bouncy: { type: "spring" as const, stiffness: 400, damping: 20 },
}

/**
 * Tween transition configurations
 *
 * - collapse: Panel collapse/expand
 * - fade: Opacity transitions
 * - preset: Layout preset switches
 */
export const transitions = {
  collapse: { duration: 0.2, ease: "easeOut" as const },
  fade: { duration: 0.15, ease: "easeInOut" as const },
  preset: { duration: 0.3, ease: "easeInOut" as const },
}

/**
 * Instant transition for reduced motion
 */
export const instantTransition = { duration: 0 }

// ============================================================================
// Reduce Motion Context
// ============================================================================

interface ReduceMotionContextValue {
  reduceMotion: boolean
  setReduceMotion: (value: boolean) => void
}

const ReduceMotionContext = createContext<ReduceMotionContextValue | undefined>(
  undefined
)

interface ReduceMotionProviderProps {
  children: React.ReactNode
  /** Override the initial value (for testing or user preference) */
  initialValue?: boolean
}

/**
 * ReduceMotionProvider
 *
 * Provides reduce motion preference throughout the app.
 * Respects system preference and allows user override.
 *
 * @example
 * ```tsx
 * // In app root
 * <ReduceMotionProvider>
 *   <App />
 * </ReduceMotionProvider>
 *
 * // In components
 * const reduceMotion = useReduceMotion()
 * ```
 */
export function ReduceMotionProvider({
  children,
  initialValue,
}: ReduceMotionProviderProps) {
  const [reduceMotion, setReduceMotion] = useState(() => {
    if (initialValue !== undefined) return initialValue
    // Check system preference
    if (typeof window !== "undefined") {
      return window.matchMedia("(prefers-reduced-motion: reduce)").matches
    }
    return false
  })

  // Listen for system preference changes
  useEffect(() => {
    if (typeof window === "undefined") return

    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)")
    const handler = (e: MediaQueryListEvent) => {
      // Only update if user hasn't set a manual preference
      // (we could add localStorage tracking here in the future)
      setReduceMotion(e.matches)
    }

    mediaQuery.addEventListener("change", handler)
    return () => mediaQuery.removeEventListener("change", handler)
  }, [])

  const value = React.useMemo(
    () => ({ reduceMotion, setReduceMotion }),
    [reduceMotion, setReduceMotion]
  )

  return (
    <ReduceMotionContext.Provider value={value}>
      {children}
    </ReduceMotionContext.Provider>
  )
}

/**
 * useReduceMotion
 *
 * Returns whether reduced motion is preferred.
 * Use this to conditionally disable animations.
 *
 * @example
 * ```tsx
 * const reduceMotion = useReduceMotion()
 * const transition = reduceMotion ? instantTransition : springConfig.snappy
 * ```
 */
export function useReduceMotion(): boolean {
  const context = useContext(ReduceMotionContext)
  if (context === undefined) {
    // Fallback: check system preference directly
    if (typeof window !== "undefined") {
      return window.matchMedia("(prefers-reduced-motion: reduce)").matches
    }
    return false
  }
  return context.reduceMotion
}

/**
 * useReduceMotionControl
 *
 * Returns both the value and setter for reduce motion.
 * Use in settings UI to toggle the preference.
 */
export function useReduceMotionControl(): ReduceMotionContextValue {
  const context = useContext(ReduceMotionContext)
  if (context === undefined) {
    throw new Error(
      "useReduceMotionControl must be used within ReduceMotionProvider"
    )
  }
  return context
}

// ============================================================================
// Animation Variants
// ============================================================================

/**
 * Common animation variants for reuse
 */
export const variants = {
  /** Fade in/out */
  fade: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
  },

  /** Scale + fade (for dialogs) */
  scaleIn: {
    initial: { opacity: 0, scale: 0.95 },
    animate: { opacity: 1, scale: 1 },
    exit: { opacity: 0, scale: 0.95 },
  },

  /** Slide up (for sheets) */
  slideUp: {
    initial: { y: "100%" },
    animate: { y: 0 },
    exit: { y: "100%" },
  },

  /** Panel drag lift */
  dragLift: {
    rest: { scale: 1, boxShadow: "0 0 0 rgba(0,0,0,0)" },
    dragging: {
      scale: 1.02,
      boxShadow: "0 8px 24px rgba(0,0,0,0.15)",
    },
  },

  /** Collapse/expand height */
  collapse: {
    open: { height: "auto", opacity: 1 },
    closed: { height: 0, opacity: 0 },
  },
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Get transition config based on reduce motion preference
 */
export function getTransition(
  config: typeof springConfig.snappy | typeof transitions.collapse,
  reduceMotion: boolean
) {
  return reduceMotion ? instantTransition : config
}
