import { useCallback, useEffect, useRef } from "react"
import type { RoomStreamEvent } from "@/hooks/useRoomStream"
import type { DemoCanvasRenderJobResponse } from "@/services/demoService"

const DEMO_CANVAS_EVENT_TYPES = new Set([
  "room.canvas_render.completed",
  "room.canvas_render.failed",
])

interface PendingCanvasJob {
  resolve: (value: DemoCanvasRenderJobResponse) => void
  reject: (reason?: unknown) => void
  timeoutId: ReturnType<typeof globalThis.setTimeout>
}

function isCanvasRenderJobResponse(
  value: unknown,
): value is DemoCanvasRenderJobResponse {
  if (!value || typeof value !== "object") return false
  const payload = value as Record<string, unknown>
  return typeof payload.job_id === "string" && typeof payload.status === "string"
}

export function useCanvasRenderJobEvents() {
  const pendingJobsRef = useRef<Map<string, PendingCanvasJob>>(new Map())
  const completedJobsRef = useRef<Map<string, DemoCanvasRenderJobResponse>>(new Map())

  useEffect(() => {
    return () => {
      for (const pending of pendingJobsRef.current.values()) {
        globalThis.clearTimeout(pending.timeoutId)
      }
      pendingJobsRef.current.clear()
      completedJobsRef.current.clear()
    }
  }, [])

  const handleRoomEvent = useCallback((event: RoomStreamEvent) => {
    if (!DEMO_CANVAS_EVENT_TYPES.has(event.event_type)) {
      return
    }
    if (!isCanvasRenderJobResponse(event.payload)) {
      return
    }

    const payload = event.payload
    completedJobsRef.current.set(payload.job_id, payload)
    const pending = pendingJobsRef.current.get(payload.job_id)
    if (!pending) {
      return
    }

    globalThis.clearTimeout(pending.timeoutId)
    pendingJobsRef.current.delete(payload.job_id)
    pending.resolve(payload)
  }, [])

  const waitForJob = useCallback(
    (jobId: string, timeoutMs = 5 * 60 * 1000) =>
      new Promise<DemoCanvasRenderJobResponse>((resolve, reject) => {
        const cached = completedJobsRef.current.get(jobId)
        if (cached) {
          resolve(cached)
          return
        }

        const existing = pendingJobsRef.current.get(jobId)
        if (existing) {
          globalThis.clearTimeout(existing.timeoutId)
          pendingJobsRef.current.delete(jobId)
        }

        const timeoutId = globalThis.setTimeout(() => {
          pendingJobsRef.current.delete(jobId)
          reject(new Error("Canvas render event timed out."))
        }, timeoutMs)

        pendingJobsRef.current.set(jobId, { resolve, reject, timeoutId })
      }),
    [],
  )

  return {
    handleRoomEvent,
    waitForJob,
  }
}
