/**
 * Plugin Registry - Plugin lifecycle and renderer resolution
 *
 * Features:
 * - Plugin registration/unregistration
 * - Priority-based renderer resolution
 * - Transform chain execution
 * - Validation aggregation
 */

import type React from "react"
import type { ContentFormat } from "@/client"
import { rendererRegistry } from "./registry"
import type {
  Content,
  Plugin,
  PluginRegistrationOptions,
  PluginRenderer,
  PluginResolutionResult,
  PluginValidationResult,
  RegisteredPlugin,
  RendererEntry,
} from "./types"

// ═══════════════════════════════════════════════════════════════════════════
// PLUGIN STORAGE
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Registered plugins indexed by id
 */
const plugins = new Map<string, RegisteredPlugin>()

/**
 * Event listeners for plugin lifecycle
 */
type PluginEventType = "register" | "unregister" | "error"
type PluginEventListener = (
  plugin: RegisteredPlugin,
  event: PluginEventType,
) => void
const eventListeners = new Set<PluginEventListener>()

// ═══════════════════════════════════════════════════════════════════════════
// REGISTRATION API
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Register a plugin
 *
 * @param plugin - Plugin to register
 * @param options - Registration options
 * @returns The registered plugin
 * @throws If plugin with same id exists and replace=false
 */
export async function registerPlugin<T extends ContentFormat>(
  plugin: Plugin<T>,
  options: PluginRegistrationOptions = {},
): Promise<RegisteredPlugin<T>> {
  const { skipInit = false, replace = false } = options

  // Check for existing plugin
  if (plugins.has(plugin.id) && !replace) {
    throw new Error(
      `Plugin "${plugin.id}" is already registered. Use replace: true to override.`,
    )
  }

  // Unregister existing if replacing
  if (plugins.has(plugin.id)) {
    await unregisterPlugin(plugin.id)
  }

  // Create registered plugin
  const registered: RegisteredPlugin<T> = {
    ...plugin,
    registeredAt: Date.now(),
    status: "active",
  }

  // Call onRegister hook
  if (!skipInit && plugin.onRegister) {
    try {
      await plugin.onRegister()
    } catch (error) {
      registered.status = "error"
      registered.error =
        error instanceof Error ? error : new Error(String(error))
      console.error(`Plugin "${plugin.id}" registration failed:`, error)
    }
  }

  // Store plugin
  plugins.set(plugin.id, registered as RegisteredPlugin)

  // Notify listeners
  emitEvent(registered as RegisteredPlugin, "register")

  return registered
}

/**
 * Unregister a plugin
 *
 * @param pluginId - ID of plugin to unregister
 * @returns True if plugin was unregistered, false if not found
 */
export async function unregisterPlugin(pluginId: string): Promise<boolean> {
  const plugin = plugins.get(pluginId)
  if (!plugin) {
    return false
  }

  // Call onUnregister hook
  if (plugin.onUnregister) {
    try {
      plugin.onUnregister()
    } catch (error) {
      console.error(`Plugin "${pluginId}" cleanup failed:`, error)
    }
  }

  // Remove plugin
  plugins.delete(pluginId)

  // Notify listeners
  emitEvent(plugin, "unregister")

  return true
}

/**
 * Get a registered plugin by id
 */
export function getPlugin(pluginId: string): RegisteredPlugin | undefined {
  return plugins.get(pluginId)
}

/**
 * Get all registered plugins
 */
export function getAllPlugins(): RegisteredPlugin[] {
  return Array.from(plugins.values())
}

/**
 * Check if a plugin is registered
 */
export function hasPlugin(pluginId: string): boolean {
  return plugins.has(pluginId)
}

// ═══════════════════════════════════════════════════════════════════════════
// RENDERER RESOLUTION
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Resolve renderer for a format, checking plugins first
 *
 * Resolution order:
 * 1. Plugin renderers (sorted by priority, highest first)
 * 2. Core rendererRegistry
 *
 * @param format - Content format to resolve
 * @returns Resolution result with renderer and source info
 */
export function resolveRenderer(
  format: ContentFormat,
): PluginResolutionResult | null {
  // Collect plugin renderers for this format
  // Note: Using loose typing here due to TypeScript contravariance with function parameters.
  // Each renderer is individually typed at definition; the collection uses `any` for storage.
  const pluginRenderers: Array<{
    plugin: RegisteredPlugin
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    renderer: {
      format: ContentFormat
      Component: React.FC<any>
      meta: { pluginId: string; label: string; priority?: number }
    }
  }> = []

  for (const plugin of plugins.values()) {
    if (plugin.status !== "active") continue
    const renderer = plugin.renderers?.[format]
    if (renderer) {
      pluginRenderers.push({ plugin, renderer })
    }
  }

  // Sort by priority (highest first)
  pluginRenderers.sort((a, b) => {
    const priorityA = a.renderer.meta.priority ?? 0
    const priorityB = b.renderer.meta.priority ?? 0
    return priorityB - priorityA
  })

  // Return highest priority plugin renderer if any
  if (pluginRenderers.length > 0) {
    const { plugin, renderer } = pluginRenderers[0]
    return {
      renderer: {
        format: renderer.format,
        Component: renderer.Component,
      },
      plugin,
      isOverride: true,
    }
  }

  // Fallback to core registry
  const coreRenderer = rendererRegistry[format]
  if (coreRenderer) {
    return {
      renderer: coreRenderer,
      plugin: null,
      isOverride: false,
    }
  }

  return null
}

/**
 * Get all renderers for a format (plugin + core)
 *
 * Useful for debugging or UI that shows available renderers.
 */
export function getAllRenderersForFormat(format: ContentFormat): Array<{
  renderer: RendererEntry | PluginRenderer
  source: "core" | string // "core" or plugin id
  priority: number
}> {
  const result: Array<{
    renderer: RendererEntry | PluginRenderer
    source: "core" | string
    priority: number
  }> = []

  // Add core renderer
  const coreRenderer = rendererRegistry[format]
  if (coreRenderer) {
    result.push({
      renderer: coreRenderer,
      source: "core",
      priority: -1, // Core has lowest priority
    })
  }

  // Add plugin renderers
  for (const plugin of plugins.values()) {
    if (plugin.status !== "active") continue
    const renderer = plugin.renderers?.[format]
    if (renderer) {
      result.push({
        renderer,
        source: plugin.id,
        priority: renderer.meta.priority ?? 0,
      })
    }
  }

  // Sort by priority (highest first)
  result.sort((a, b) => b.priority - a.priority)

  return result
}

// ═══════════════════════════════════════════════════════════════════════════
// VALIDATION
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Run all plugin validators for content
 *
 * Aggregates validation results from all active plugins.
 * Does NOT throw - returns combined validation result.
 *
 * @param content - Content to validate
 * @returns Aggregated validation result
 */
export function validateContent(content: Content): PluginValidationResult {
  const errors: PluginValidationResult["errors"] = []

  for (const plugin of plugins.values()) {
    if (plugin.status !== "active") continue
    if (!plugin.validate) continue

    try {
      const result = plugin.validate(content)
      if (!result.valid) {
        // Prefix errors with plugin id for debugging
        const prefixedErrors = result.errors.map((error) => ({
          ...error,
          code: `${plugin.id}:${error.code}`,
        }))
        errors.push(...prefixedErrors)
      }
    } catch (error) {
      // Validator threw - add as error
      errors.push({
        code: `${plugin.id}:validator_error`,
        message: error instanceof Error ? error.message : String(error),
        severity: "error",
      })
    }
  }

  return {
    valid: errors.filter((e) => e.severity === "error").length === 0,
    errors,
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// TRANSFORM CHAIN
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Apply all plugin transforms to content
 *
 * Transforms are applied in priority order (highest first).
 * Each transform receives the output of the previous.
 *
 * @param content - Content to transform
 * @returns Transformed content
 */
export function transformContent<T extends ContentFormat>(
  content: Content<T>,
): Content<T> {
  // Get plugins with transforms, sorted by priority
  const transformPlugins = Array.from(plugins.values())
    .filter((p) => p.status === "active" && p.transform)
    .sort((a, b) => {
      // Use highest renderer priority as plugin priority
      const getMaxPriority = (plugin: RegisteredPlugin): number => {
        if (!plugin.renderers) return 0
        return Math.max(
          0,
          ...Object.values(plugin.renderers).map((r) => r?.meta.priority ?? 0),
        )
      }
      return getMaxPriority(b) - getMaxPriority(a)
    })

  // Apply transforms in chain
  let result = content
  for (const plugin of transformPlugins) {
    try {
      result = plugin.transform!(result) as Content<T>
    } catch (error) {
      console.error(`Plugin "${plugin.id}" transform failed:`, error)
      // Continue with untransformed content on error
    }
  }

  return result
}

// ═══════════════════════════════════════════════════════════════════════════
// EVENT SYSTEM
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Subscribe to plugin lifecycle events
 */
export function onPluginEvent(listener: PluginEventListener): () => void {
  eventListeners.add(listener)
  return () => eventListeners.delete(listener)
}

function emitEvent(plugin: RegisteredPlugin, event: PluginEventType): void {
  for (const listener of eventListeners) {
    try {
      listener(plugin, event)
    } catch (error) {
      console.error("Plugin event listener error:", error)
    }
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// UTILITIES
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Clear all plugins (useful for testing)
 */
export function clearPlugins(): void {
  for (const pluginId of plugins.keys()) {
    unregisterPlugin(pluginId)
  }
}

/**
 * Disable a plugin without unregistering
 */
export function disablePlugin(pluginId: string): boolean {
  const plugin = plugins.get(pluginId)
  if (!plugin) return false
  plugin.status = "disabled"
  return true
}

/**
 * Enable a previously disabled plugin
 */
export function enablePlugin(pluginId: string): boolean {
  const plugin = plugins.get(pluginId)
  if (!plugin) return false
  if (plugin.status === "error") return false // Can't enable errored plugins
  plugin.status = "active"
  return true
}
