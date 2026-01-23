/**
 * Agent UI Renderer
 *
 * Thin orchestrator that dispatches UIComponent rendering to individual primitives.
 * Each primitive is a self-contained component in the primitives/ directory.
 *
 * Usage:
 *   {message.ui_components?.map((component, idx) => (
 *     <AgentUIRenderer key={component.id || idx} component={component} />
 *   ))}
 */

import {
  UIActionButtons,
  UIAlertBlock,
  UICardBlock,
  UICodeBlock,
  UICollapsibleBlock,
  UIDividerBlock,
  UIListBlock,
  UIPageLayoutPreview,
  UIProgressBlock,
  UIQuoteBlock,
  UITableBlock,
  UITabsBlock,
} from "./primitives"
import type {
  UIActionButtonsData,
  UIAlertData,
  UICardData,
  UICodeData,
  UICollapsibleData,
  UIComponent,
  UIDividerData,
  UIListData,
  UIPageLayoutPreviewData,
  UIProgressData,
  UIQuoteData,
  UITableData,
  UITabsData,
} from "./types"

interface AgentUIRendererProps {
  component: UIComponent
  onAction?: (action: string) => void
}

export default function AgentUIRenderer({
  component,
  onAction,
}: AgentUIRendererProps) {
  const { type, data, fallback_text } = component

  switch (type) {
    case "card":
      return <UICardBlock data={data as unknown as UICardData} />
    case "list":
      return <UIListBlock data={data as unknown as UIListData} />
    case "table":
      return <UITableBlock data={data as unknown as UITableData} />
    case "progress":
      return <UIProgressBlock data={data as unknown as UIProgressData} />
    case "action_buttons":
      return (
        <UIActionButtons
          data={data as unknown as UIActionButtonsData}
          onAction={onAction}
        />
      )
    case "code":
      return <UICodeBlock data={data as unknown as UICodeData} />
    case "quote":
      return <UIQuoteBlock data={data as unknown as UIQuoteData} />
    case "alert":
      return <UIAlertBlock data={data as unknown as UIAlertData} />
    case "collapsible":
      return <UICollapsibleBlock data={data as unknown as UICollapsibleData} />
    case "tabs":
      return <UITabsBlock data={data as unknown as UITabsData} />
    case "divider":
      return <UIDividerBlock data={data as unknown as UIDividerData} />
    case "page_layout_preview":
      return (
        <UIPageLayoutPreview
          data={data as unknown as UIPageLayoutPreviewData}
        />
      )
    default:
      return fallback_text ? (
        <p className="text-sm text-muted-foreground italic">{fallback_text}</p>
      ) : null
  }
}
