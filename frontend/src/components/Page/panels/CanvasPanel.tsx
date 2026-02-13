/**
 * CanvasPanel
 *
 * Primary panel for interactive canvas collaboration.
 * Currently a placeholder for future implementation.
 *
 * @example Room panel usage
 * ```tsx
 * <CanvasPanel />
 * ```
 *
 * @example Standalone page usage
 * ```tsx
 * <CanvasPanel className="h-full" />
 * ```
 */

import { Paintbrush } from "lucide-react"
import { PanelContainer } from "../primitives/PanelContainer"
import { PlaceholderContent } from "../primitives/PlaceholderContent"

interface CanvasPanelProps {
  /** Hide panel header */
  hideHeader?: boolean
  /** Additional className */
  className?: string
}

export function CanvasPanel({
  hideHeader = false,
  className,
}: CanvasPanelProps) {
  const content = (
    <PlaceholderContent
      icon={Paintbrush}
      title="Canvas"
      description="Interactive canvas for agent and user collaboration. Coming soon."
    />
  )

  if (hideHeader) {
    return <div className={className}>{content}</div>
  }

  return (
    <PanelContainer title="Canvas" className={className}>
      {content}
    </PanelContainer>
  )
}
