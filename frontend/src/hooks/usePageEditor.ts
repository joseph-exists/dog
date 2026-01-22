/**
 * usePageEditor Hook
 *
 * Manages page layout editing with draft state management.
 * Provides block CRUD operations and editing lifecycle.
 *
 * Features:
 * - Fetches persisted layout via PageService
 * - Maintains draft state for unsaved changes
 * - Provides block operations (add, remove, update, reorder)
 * - Tracks dirty state by comparing draft to server state
 * - Explicit save to persist changes
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useCallback, useMemo, useState } from "react"
import type { ApiError } from "@/client"
import {
  type BlockType,
  getBlockType,
  getPageTemplate,
  type TemplateBlock,
} from "@/components/Page/registry"
import { PageService } from "@/services/pageService"

// ============================================================================
// Types
// ============================================================================

export interface UsePageEditorReturn {
  // Data
  blocks: TemplateBlock[] | undefined
  selectedBlockId: string | null
  selectedBlock: TemplateBlock | null

  // State
  isLoading: boolean
  isEditing: boolean
  isDirty: boolean
  isSaving: boolean
  error: ApiError | null
  pageExists: boolean

  // Editing lifecycle
  startEditing: () => void
  cancelEditing: () => void
  save: () => Promise<void>

  // Block selection (for sheet)
  selectBlock: (blockId: string | null) => void

  // Block operations
  updateBlockContent: (
    blockId: string,
    content: Record<string, unknown>,
  ) => void
  updateBlockConfig: (blockId: string, config: Record<string, unknown>) => void
  addBlock: (type: BlockType, column: "primary" | "auxiliary") => void
  removeBlock: (blockId: string) => void
  reorderBlocks: (column: "primary" | "auxiliary", orderedIds: string[]) => void
  toggleBlockVisibility: (blockId: string) => void

  // Page creation
  createPage: (templateId: string) => Promise<void>
}

// ============================================================================
// Hook Implementation
// ============================================================================

/**
 * Hook for managing page layout editing
 *
 * @param entityType - Type of entity (e.g., "user", "agent")
 * @param entityId - UUID of the entity
 * @returns Page editor state and operations
 *
 * @example
 * ```tsx
 * const {
 *   blocks,
 *   isEditing,
 *   isDirty,
 *   startEditing,
 *   cancelEditing,
 *   save,
 *   updateBlockContent,
 *   addBlock,
 * } = usePageEditor("user", userId)
 *
 * // Start editing
 * startEditing()
 *
 * // Make changes
 * updateBlockContent(blockId, { text: "New bio" })
 *
 * // Save or cancel
 * if (isDirty) {
 *   await save()
 * }
 * ```
 */
export function usePageEditor(
  entityType: string,
  entityId: string,
): UsePageEditorReturn {
  const queryClient = useQueryClient()

  // Query key for cache management
  const queryKey = ["pages", entityType, entityId] as const

  // ==========================================================================
  // Local State
  // ==========================================================================

  const [draftBlocks, setDraftBlocks] = useState<TemplateBlock[] | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [selectedBlockId, setSelectedBlockId] = useState<string | null>(null)

  // ==========================================================================
  // Server State Query
  // ==========================================================================

  const layoutQuery = useQuery({
    queryKey,
    queryFn: () => PageService.getLayout(entityType, entityId),
  })

  // ==========================================================================
  // Save Mutation
  // ==========================================================================

  const saveMutation = useMutation({
    mutationFn: async (blocks: TemplateBlock[]) => {
      return PageService.saveLayout({
        entityType,
        entityId,
        layout: blocks,
        layoutVersion: layoutQuery.data?.layoutVersion,
      })
    },
    onSuccess: () => {
      // Invalidate query to refresh server state
      queryClient.invalidateQueries({ queryKey })
      // Exit editing mode
      setDraftBlocks(null)
      setIsEditing(false)
      setSelectedBlockId(null)
    },
  })

  // ==========================================================================
  // Derived State
  // ==========================================================================

  // Server blocks (from query)
  const serverBlocks = layoutQuery.data?.layout

  // Current blocks to display (draft if editing, otherwise server)
  const blocks = isEditing ? (draftBlocks ?? serverBlocks) : serverBlocks

  // Whether the page exists on the server
  const pageExists = layoutQuery.data !== null && layoutQuery.data !== undefined

  // Whether draft differs from server state
  const isDirty = useMemo(() => {
    if (!isEditing || !draftBlocks) return false
    return JSON.stringify(draftBlocks) !== JSON.stringify(serverBlocks ?? [])
  }, [isEditing, draftBlocks, serverBlocks])

  // Selected block from current blocks
  const selectedBlock = useMemo(() => {
    if (!selectedBlockId || !blocks) return null
    return blocks.find((b) => b.id === selectedBlockId) ?? null
  }, [selectedBlockId, blocks])

  // ==========================================================================
  // Editing Lifecycle
  // ==========================================================================

  const startEditing = useCallback(() => {
    // Copy server blocks to draft state (or empty array if no page)
    setDraftBlocks(serverBlocks ? [...serverBlocks] : [])
    setIsEditing(true)
  }, [serverBlocks])

  const cancelEditing = useCallback(() => {
    setDraftBlocks(null)
    setIsEditing(false)
    setSelectedBlockId(null)
  }, [])

  const save = useCallback(async () => {
    if (!draftBlocks) return
    await saveMutation.mutateAsync(draftBlocks)
  }, [draftBlocks, saveMutation])

  // ==========================================================================
  // Block Selection
  // ==========================================================================

  const selectBlock = useCallback((blockId: string | null) => {
    setSelectedBlockId(blockId)
  }, [])

  // ==========================================================================
  // Block Operations
  // ==========================================================================

  const updateBlockContent = useCallback(
    (blockId: string, content: Record<string, unknown>) => {
      if (!draftBlocks) return

      setDraftBlocks((prev) => {
        if (!prev) return prev
        return prev.map((block) =>
          block.id === blockId ? { ...block, content } : block,
        )
      })
    },
    [draftBlocks],
  )

  const updateBlockConfig = useCallback(
    (blockId: string, config: Record<string, unknown>) => {
      if (!draftBlocks) return

      setDraftBlocks((prev) => {
        if (!prev) return prev
        return prev.map((block) =>
          block.id === blockId ? { ...block, config } : block,
        )
      })
    },
    [draftBlocks],
  )

  const addBlock = useCallback(
    (type: BlockType, column: "primary" | "auxiliary") => {
      if (!draftBlocks) return

      // Get block type definition for defaults
      const blockTypeDef = getBlockType(type)
      if (!blockTypeDef) return

      // Calculate next order number for the column
      const columnBlocks = draftBlocks.filter((b) => b.column === column)
      const maxOrder = columnBlocks.reduce(
        (max, b) => Math.max(max, b.order),
        0,
      )

      const newBlock: TemplateBlock = {
        id: crypto.randomUUID(),
        type,
        column,
        order: maxOrder + 1,
        config: { ...blockTypeDef.defaultConfig },
        content: { ...blockTypeDef.defaultContent },
        visibility: "visible",
      }

      setDraftBlocks((prev) => (prev ? [...prev, newBlock] : [newBlock]))
    },
    [draftBlocks],
  )

  const removeBlock = useCallback(
    (blockId: string) => {
      if (!draftBlocks) return

      setDraftBlocks((prev) => {
        if (!prev) return prev
        return prev.filter((block) => block.id !== blockId)
      })

      // Clear selection if removed block was selected
      if (selectedBlockId === blockId) {
        setSelectedBlockId(null)
      }
    },
    [draftBlocks, selectedBlockId],
  )

  const reorderBlocks = useCallback(
    (column: "primary" | "auxiliary", orderedIds: string[]) => {
      if (!draftBlocks) return

      setDraftBlocks((prev) => {
        if (!prev) return prev

        return prev.map((block) => {
          // Only update blocks in the target column
          if (block.column !== column) return block

          const newOrder = orderedIds.indexOf(block.id!)
          if (newOrder === -1) return block

          return { ...block, order: newOrder + 1 }
        })
      })
    },
    [draftBlocks],
  )

  const toggleBlockVisibility = useCallback(
    (blockId: string) => {
      if (!draftBlocks) return

      setDraftBlocks((prev) => {
        if (!prev) return prev
        return prev.map((block) => {
          if (block.id !== blockId) return block
          const currentVisibility = block.visibility ?? "visible"
          return {
            ...block,
            visibility: currentVisibility === "visible" ? "hidden" : "visible",
          }
        })
      })
    },
    [draftBlocks],
  )

  // ==========================================================================
  // Page Creation
  // ==========================================================================

  const createPage = useCallback(
    async (templateId: string) => {
      const template = getPageTemplate(templateId)
      if (!template) {
        throw new Error(`Template not found: ${templateId}`)
      }

      // Instantiate template blocks with new UUIDs
      const instantiatedBlocks: TemplateBlock[] = template.defaultBlocks.map(
        (block) => ({
          ...block,
          id: crypto.randomUUID(),
          visibility: block.visibility ?? "visible",
          content: block.content ?? {},
        }),
      )

      // Save immediately
      await saveMutation.mutateAsync(instantiatedBlocks)
    },
    [saveMutation],
  )

  // ==========================================================================
  // Return Value
  // ==========================================================================

  return {
    // Data
    blocks,
    selectedBlockId,
    selectedBlock,

    // State
    isLoading: layoutQuery.isLoading,
    isEditing,
    isDirty,
    isSaving: saveMutation.isPending,
    error: layoutQuery.error as ApiError | null,
    pageExists,

    // Editing lifecycle
    startEditing,
    cancelEditing,
    save,

    // Block selection
    selectBlock,

    // Block operations
    updateBlockContent,
    updateBlockConfig,
    addBlock,
    removeBlock,
    reorderBlocks,
    toggleBlockVisibility,

    // Page creation
    createPage,
  }
}
