import { useEffect, useMemo, useState } from "react"
import type React from "react"
import { cn } from "@/lib/utils"
import type { ResolvedDemoPresentationFrame } from "@/components/Demo/demoPresentationResolver"

interface DemoPresentationFrameProps {
  frame: ResolvedDemoPresentationFrame
  className?: string
  contentClassName?: string
  children: React.ReactNode
}

export function DemoPresentationFrame({
  frame,
  className,
  contentClassName,
  children,
}: DemoPresentationFrameProps) {
  const [entered, setEntered] = useState(frame.motionMs === undefined)

  useEffect(() => {
    if (frame.motionMs === undefined) return
    setEntered(false)
    const id = window.requestAnimationFrame(() => setEntered(true))
    return () => window.cancelAnimationFrame(id)
  }, [frame.motionMs, frame.style, frame.overlayCss, frame.easing])

  const animatedStyle = useMemo(() => {
    const style: React.CSSProperties = {
      ...(frame.style ?? {}),
    }
    if (frame.motionMs !== undefined) {
      const easing = frame.easing ?? "ease-out"
      style.transition = `opacity ${frame.motionMs}ms ${easing}, transform ${frame.motionMs}ms ${easing}`
      style.opacity = entered ? 1 : 0
      style.transform = entered ? "translateY(0)" : "translateY(4px)"
    }
    return Object.keys(style).length > 0 ? style : undefined
  }, [entered, frame.easing, frame.motionMs, frame.style])

  return (
    <div className={cn("relative", className)} style={animatedStyle}>
      {frame.overlayCss && (
        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 top-0 z-10 h-1.5"
          style={{ background: frame.overlayCss }}
        />
      )}
      <div className={cn("relative z-20", contentClassName)}>{children}</div>
    </div>
  )
}
