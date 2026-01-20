/**
 * A2UIPanel
 *
 * Primary panel for AGUI agent tool call rendering.
 * Currently a placeholder - will integrate AgentUIRenderer.
 *
 * @example Room panel usage
 * ```tsx
 * <A2UIPanel roomId={roomId} />
 * ```
 *
 * @example Standalone page usage
 * ```tsx
 * <A2UIPanel roomId={roomId} className="h-full" />
 * ```
 */

import { Blocks } from "lucide-react"
import { PanelContainer } from "../primitives/PanelContainer"
import { PlaceholderContent } from "../primitives/PlaceholderContent"

interface A2UIPanelProps {
  /** Room ID for context */
  roomId?: string
  /** Hide panel header */
  hideHeader?: boolean
  /** Additional className */
  className?: string
}

export function A2UIPanel({
  roomId: _roomId,
  hideHeader = false,
  className,
}: A2UIPanelProps) {
  const content = (
    <PlaceholderContent
      icon={Blocks}
      title="Agent UI"
      description="Structured UI components from agent tool calls will render here. Coming soon."
    />
  )

  if (hideHeader) {
    return <div className={className}>{content}</div>
  }

  return (
    <PanelContainer title="Agent UI" className={className}>
      {content}
    </PanelContainer>
  )
}
