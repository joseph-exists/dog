/**
 * KeyboardShortcutProvider Primitive
 *
 * React context for registering and handling keyboard shortcuts.
 * Platform-aware (Cmd on Mac, Ctrl on Windows/Linux).
 *
 * @example
 * ```tsx
 * const shortcuts = [
 *   { key: "1", modifiers: ["mod"], action: () => focusPanel(0), description: "Focus first panel" },
 *   { key: "l", modifiers: ["mod", "shift"], action: () => openSettings(), description: "Open layout" },
 * ]
 *
 * <KeyboardShortcutProvider shortcuts={shortcuts}>
 *   <RoomContent />
 * </KeyboardShortcutProvider>
 * ```
 */

import * as React from "react"
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
} from "react"

// ============================================================================
// Types
// ============================================================================

export type Modifier = "mod" | "shift" | "alt" | "ctrl"

export interface KeyboardShortcut {
  /** The key to listen for (lowercase) */
  key: string
  /** Required modifiers */
  modifiers: Modifier[]
  /** Action to execute */
  action: () => void
  /** Description for display */
  description: string
  /** Whether this shortcut is currently enabled */
  enabled?: boolean
}

interface KeyboardShortcutContextValue {
  /** Register a shortcut */
  registerShortcut: (shortcut: KeyboardShortcut) => () => void
  /** Get all registered shortcuts */
  getShortcuts: () => KeyboardShortcut[]
  /** Whether we're on Mac */
  isMac: boolean
  /** Format a shortcut for display (e.g., "⌘⇧L" or "Ctrl+Shift+L") */
  formatShortcut: (modifiers: Modifier[], key: string) => string
}

// ============================================================================
// Context
// ============================================================================

const KeyboardShortcutContext = createContext<
  KeyboardShortcutContextValue | undefined
>(undefined)

// ============================================================================
// Platform Detection
// ============================================================================

function detectPlatform(): boolean {
  if (typeof navigator === "undefined") return false
  return /Mac|iPod|iPhone|iPad/.test(navigator.platform)
}

// ============================================================================
// Shortcut Formatting
// ============================================================================

const MAC_SYMBOLS: Record<Modifier | string, string> = {
  mod: "⌘",
  ctrl: "⌃",
  shift: "⇧",
  alt: "⌥",
}

const WIN_SYMBOLS: Record<Modifier | string, string> = {
  mod: "Ctrl",
  ctrl: "Ctrl",
  shift: "Shift",
  alt: "Alt",
}

function formatShortcutKey(key: string): string {
  const specialKeys: Record<string, string> = {
    escape: "Esc",
    arrowup: "↑",
    arrowdown: "↓",
    arrowleft: "←",
    arrowright: "→",
    enter: "↵",
    backspace: "⌫",
    delete: "Del",
    tab: "Tab",
    space: "Space",
  }
  return specialKeys[key.toLowerCase()] || key.toUpperCase()
}

// ============================================================================
// KeyboardShortcutProvider Component
// ============================================================================

interface KeyboardShortcutProviderProps {
  children: React.ReactNode
  /** Initial shortcuts to register */
  shortcuts?: KeyboardShortcut[]
  /** Whether shortcuts are globally enabled */
  enabled?: boolean
}

export function KeyboardShortcutProvider({
  children,
  shortcuts: initialShortcuts = [],
  enabled = true,
}: KeyboardShortcutProviderProps) {
  const isMac = useMemo(() => detectPlatform(), [])
  const shortcutsRef = React.useRef<Map<string, KeyboardShortcut>>(new Map())

  // Initialize with provided shortcuts
  useEffect(() => {
    initialShortcuts.forEach((shortcut) => {
      const key = `${shortcut.modifiers.sort().join("+")}+${shortcut.key}`
      shortcutsRef.current.set(key, shortcut)
    })
  }, [initialShortcuts])

  const registerShortcut = useCallback((shortcut: KeyboardShortcut) => {
    const key = `${shortcut.modifiers.sort().join("+")}+${shortcut.key}`
    shortcutsRef.current.set(key, shortcut)

    // Return unregister function
    return () => {
      shortcutsRef.current.delete(key)
    }
  }, [])

  const getShortcuts = useCallback(() => {
    return Array.from(shortcutsRef.current.values())
  }, [])

  const formatShortcut = useCallback(
    (modifiers: Modifier[], key: string) => {
      const symbols = isMac ? MAC_SYMBOLS : WIN_SYMBOLS
      const modString = modifiers
        .map((m) => symbols[m] || m)
        .join(isMac ? "" : "+")
      const keyString = formatShortcutKey(key)

      return isMac ? `${modString}${keyString}` : `${modString}+${keyString}`
    },
    [isMac],
  )

  // Global keyboard listener
  useEffect(() => {
    if (!enabled) return

    const handleKeyDown = (e: KeyboardEvent) => {
      // Skip if focus is in an input/textarea
      const target = e.target as HTMLElement
      if (
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable
      ) {
        // Allow Escape to still work
        if (e.key !== "Escape") return
      }

      // Build modifier set
      const activeModifiers: Modifier[] = []
      if (e.metaKey || e.ctrlKey) activeModifiers.push("mod")
      if (e.shiftKey) activeModifiers.push("shift")
      if (e.altKey) activeModifiers.push("alt")

      // Also check explicit ctrl on non-Mac
      if (!isMac && e.ctrlKey && !activeModifiers.includes("mod")) {
        activeModifiers.push("ctrl")
      }

      const key = `${activeModifiers.sort().join("+")}+${e.key.toLowerCase()}`
      const shortcut = shortcutsRef.current.get(key)

      if (shortcut && shortcut.enabled !== false) {
        e.preventDefault()
        shortcut.action()
      }
    }

    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [enabled, isMac])

  const value = useMemo(
    () => ({
      registerShortcut,
      getShortcuts,
      isMac,
      formatShortcut,
    }),
    [registerShortcut, getShortcuts, isMac, formatShortcut],
  )

  return (
    <KeyboardShortcutContext.Provider value={value}>
      {children}
    </KeyboardShortcutContext.Provider>
  )
}

// ============================================================================
// Hooks
// ============================================================================

/**
 * useKeyboardShortcuts
 *
 * Access the keyboard shortcut context.
 */
export function useKeyboardShortcuts(): KeyboardShortcutContextValue {
  const context = useContext(KeyboardShortcutContext)
  if (!context) {
    throw new Error(
      "useKeyboardShortcuts must be used within KeyboardShortcutProvider",
    )
  }
  return context
}

/**
 * useShortcut
 *
 * Register a single shortcut. Automatically unregisters on unmount.
 *
 * @example
 * ```tsx
 * useShortcut({
 *   key: "l",
 *   modifiers: ["mod", "shift"],
 *   action: () => setOpen(true),
 *   description: "Open layout settings",
 * })
 * ```
 */
export function useShortcut(shortcut: KeyboardShortcut) {
  const { registerShortcut } = useKeyboardShortcuts()

  useEffect(() => {
    return registerShortcut(shortcut)
  }, [registerShortcut, shortcut.key, shortcut])
}

/**
 * useShortcutDisplay
 *
 * Get formatted shortcut string for display.
 *
 * @example
 * ```tsx
 * const display = useShortcutDisplay(["mod", "shift"], "l")
 * // Returns "⌘⇧L" on Mac, "Ctrl+Shift+L" on Windows
 * ```
 */
export function useShortcutDisplay(modifiers: Modifier[], key: string): string {
  const { formatShortcut } = useKeyboardShortcuts()
  return formatShortcut(modifiers, key)
}
