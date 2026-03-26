import { useQuery, useQueryClient } from "@tanstack/react-query"
import { useCallback, useMemo, useState } from "react"
import {
  showErrorToast,
  showSuccessToast,
  showWarningToast,
} from "@/hooks/useCustomToast"
import { RoomService } from "@/services/roomService"

function toRecord(value: unknown): Record<string, unknown> | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null
  return value as Record<string, unknown>
}

function getString(value: unknown): string | null {
  return typeof value === "string" && value.trim().length > 0
    ? value.trim()
    : null
}

function hashToBase36(value: string): string {
  let hash = 2166136261
  for (let i = 0; i < value.length; i += 1) {
    hash ^= value.charCodeAt(i)
    hash = Math.imul(hash, 16777619)
  }
  return (hash >>> 0).toString(36)
}

function buildRepoFileContextKey(
  repoId: string,
  path: string,
  ref: string,
): string {
  return `${repoId}|${ref}|${path}`
}

function buildRepoFileContextType(
  repoId: string,
  path: string,
  ref: string,
): string {
  const hash = hashToBase36(buildRepoFileContextKey(repoId, path, ref))
  return `system.repo.file.${hash}`
}

function buildRepoFileContextId(
  repoId: string,
  path: string,
  ref: string,
): string {
  const hash = hashToBase36(`ctx|${buildRepoFileContextKey(repoId, path, ref)}`)
  return `repo-file-${hash}`
}

export interface RepoContextFileEntry {
  contextId: string
  repoId: string
  repoSlug: string | null
  path: string
  ref: string
  source: string
  sizeBytes: number | null
  isTruncated: boolean
  payload: Record<string, unknown>
}

export interface RepoFileContextStateInput {
  panelId: string
  repoId: string
  path: string
  ref: string
  isBinary: boolean
  hasContent: boolean
}

export interface RepoFileContextState {
  included: boolean
  pending: boolean
  canToggle: boolean
  disabledReason?: string | null
}

export interface RepoFileContextToggleInput {
  panelId: string
  repoId: string
  repoSlug: string
  path: string
  ref: string
  content: string
  contentType: string | null
  encoding: string | null
  sizeBytes: number | null
  isBinary: boolean
  isTruncated: boolean
  truncationReason: string | null
}

export function useRoomRepoContext(
  roomId: string,
  canManageRoomContext: boolean,
) {
  const queryClient = useQueryClient()
  const [pendingContextKeys, setPendingContextKeys] = useState<Set<string>>(
    new Set(),
  )

  const { data: roomContextsData } = useQuery({
    queryKey: ["rooms", roomId, "contexts"],
    queryFn: () => RoomService.listRoomContexts(roomId),
  })

  const roomContextByRepoFileKey = useMemo(() => {
    const index = new Map<string, { id: string; source: string }>()
    const contexts = roomContextsData?.data ?? []
    for (const item of contexts) {
      const payload = toRecord(item.payload)
      if (!payload) continue
      const payloadRepoId = getString(payload.repo_id)
      const payloadPath = getString(payload.path)
      const payloadRef = getString(payload.ref)
      if (!payloadRepoId || !payloadPath || !payloadRef) continue
      index.set(
        buildRepoFileContextKey(payloadRepoId, payloadPath, payloadRef),
        {
          id: item.id,
          source: item.source,
        },
      )
    }
    return index
  }, [roomContextsData?.data])

  const repoContextFiles = useMemo(() => {
    const contexts = roomContextsData?.data ?? []
    return contexts
      .map((item) => {
        const payload = toRecord(item.payload)
        if (!payload) return null
        const repoId = getString(payload.repo_id)
        const path = getString(payload.path)
        const ref = getString(payload.ref)
        if (!repoId || !path || !ref) return null
        return {
          contextId: item.id,
          repoId,
          repoSlug: getString(payload.repo_slug),
          path,
          ref,
          source: item.source,
          sizeBytes:
            typeof payload.size_bytes === "number" ? payload.size_bytes : null,
          isTruncated: payload.is_truncated === true,
          payload,
        } satisfies RepoContextFileEntry
      })
      .filter((item): item is RepoContextFileEntry => item !== null)
  }, [roomContextsData?.data])

  const getFileRoomContextState = useCallback(
    ({
      repoId,
      path,
      ref,
      isBinary,
      hasContent,
    }: RepoFileContextStateInput) => {
      const fileKey = buildRepoFileContextKey(repoId, path, ref)
      const included = roomContextByRepoFileKey.has(fileKey)
      const pending = pendingContextKeys.has(fileKey)
      if (!canManageRoomContext) {
        return {
          included,
          pending,
          canToggle: false,
          disabledReason: "Only room owners can add or remove room context.",
        } satisfies RepoFileContextState
      }
      if (isBinary) {
        return {
          included,
          pending,
          canToggle: false,
          disabledReason: "Binary files cannot be added to room context in v1.",
        } satisfies RepoFileContextState
      }
      if (!hasContent) {
        return {
          included,
          pending,
          canToggle: false,
          disabledReason: "This file has no readable content to attach.",
        } satisfies RepoFileContextState
      }
      return {
        included,
        pending,
        canToggle: true,
        disabledReason: null,
      } satisfies RepoFileContextState
    },
    [canManageRoomContext, pendingContextKeys, roomContextByRepoFileKey],
  )

  const toggleFileRoomContext = useCallback(
    async (input: RepoFileContextToggleInput) => {
      if (!canManageRoomContext) {
        showWarningToast("Only room owners can add or remove room context.")
        return
      }
      if (input.isBinary) {
        showWarningToast("Binary files cannot be added to room context in v1.")
        return
      }

      const fileKey = buildRepoFileContextKey(
        input.repoId,
        input.path,
        input.ref,
      )
      if (pendingContextKeys.has(fileKey)) return

      setPendingContextKeys((current) => {
        const next = new Set(current)
        next.add(fileKey)
        return next
      })

      try {
        const existing = roomContextByRepoFileKey.get(fileKey)
        if (existing) {
          await RoomService.deleteRoomContext(roomId, existing.id)
          showSuccessToast("File removed from room context.")
        } else {
          const contextPayload: Record<string, unknown> = {
            repo_id: input.repoId,
            repo_slug: input.repoSlug,
            path: input.path,
            ref: input.ref,
            content: input.content,
            content_type: input.contentType,
            encoding: input.encoding,
            size_bytes: input.sizeBytes,
            is_binary: input.isBinary,
            is_truncated: input.isTruncated,
            truncation_reason: input.truncationReason,
          }
          const payloadBytes = new TextEncoder().encode(
            JSON.stringify(contextPayload),
          ).length
          if (payloadBytes > 49_000) {
            showWarningToast(
              "File too large for room context payload limit. Try a smaller file.",
            )
            return
          }
          await RoomService.upsertRoomContext(
            roomId,
            buildRepoFileContextId(input.repoId, input.path, input.ref),
            {
              agent_slug: null,
              context_type: buildRepoFileContextType(
                input.repoId,
                input.path,
                input.ref,
              ),
              payload: contextPayload,
              source: "frontend",
              expires_at: null,
            },
            { replaceByType: false },
          )
          showSuccessToast("File added to room context.")
        }
      } catch (error) {
        console.error("Failed to toggle file room context", error)
        showErrorToast("Failed to update room context for this file.")
      } finally {
        await queryClient.invalidateQueries({
          queryKey: ["rooms", roomId, "contexts"],
        })
        setPendingContextKeys((current) => {
          const next = new Set(current)
          next.delete(fileKey)
          return next
        })
      }
    },
    [
      canManageRoomContext,
      pendingContextKeys,
      queryClient,
      roomContextByRepoFileKey,
      roomId,
    ],
  )

  const removeRepoContextFile = useCallback(
    async (contextId: string) => {
      if (!canManageRoomContext) {
        showWarningToast("Only room owners can remove room context files.")
        return
      }
      try {
        await RoomService.deleteRoomContext(roomId, contextId)
        showSuccessToast("Removed file from room context.")
      } catch (error) {
        console.error("Failed to remove room context file", error)
        showErrorToast("Failed to remove file from room context.")
      } finally {
        await queryClient.invalidateQueries({
          queryKey: ["rooms", roomId, "contexts"],
        })
      }
    },
    [canManageRoomContext, queryClient, roomId],
  )

  return {
    repoContextFiles,
    getFileRoomContextState,
    toggleFileRoomContext,
    removeRepoContextFile,
  }
}
