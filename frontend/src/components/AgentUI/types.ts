/**
 * AG-UI Type Definitions
 *
 * TypeScript interfaces for agent-generated UI components.
 * These mirror the backend Pydantic schemas in app/schemas/ag_ui.py
 */

import type { TemplateBlock } from "@/components/Page/registry"

export type UIComponentType =
  | "card"
  | "list"
  | "table"
  | "progress"
  | "action_buttons"
  | "code"
  | "quote"
  | "alert"
  | "collapsible"
  | "tabs"
  | "divider"
  | "page_layout_preview"

export interface UIComponent {
  type: UIComponentType
  data: Record<string, unknown>
  id?: string
  fallback_text?: string
}

// Component-specific data types

export interface UICardData {
  title: string
  subtitle?: string
  body: string
  footer?: string
  variant?: "default" | "highlight" | "warning" | "success" | "info"
  icon?: string
}

export interface UIListItem {
  label: string
  description?: string
  icon?: string
  badge?: string
  badge_variant?: "default" | "success" | "warning" | "error"
}

export interface UIListData {
  title?: string
  items: UIListItem[]
  ordered?: boolean
  variant?: "default" | "compact" | "detailed"
}

export interface UITableColumn {
  key: string
  header: string
  align?: "left" | "center" | "right"
}

export interface UITableData {
  title?: string
  columns: UITableColumn[]
  rows: Record<string, unknown>[]
  striped?: boolean
  compact?: boolean
}

export interface UIProgressItem {
  label: string
  value: number
  color?: "blue" | "green" | "yellow" | "red" | "purple"
}

export interface UIProgressData {
  title?: string
  items: UIProgressItem[]
  show_percentage?: boolean
}

export interface UIActionButton {
  label: string
  action: string
  variant?: "primary" | "secondary" | "outline" | "ghost"
  icon?: string
  disabled?: boolean
}

export interface UIActionButtonsData {
  buttons: UIActionButton[]
  layout?: "horizontal" | "vertical" | "grid"
}

export interface UICodeData {
  code: string
  language?: string
  title?: string
  line_numbers?: boolean
}

export interface UIQuoteData {
  text: string
  attribution?: string
  variant?: "default" | "highlight" | "subtle"
}

export interface UIAlertData {
  title?: string
  message: string
  variant?: "info" | "success" | "warning" | "error"
  dismissible?: boolean
}

export interface UICollapsibleData {
  title: string
  content: string
  default_open?: boolean
  icon?: string
}

export interface UITabData {
  label: string
  content: string
}

export interface UITabsData {
  tabs: UITabData[]
  default_tab?: number
}

export interface UIDividerData {
  label?: string
  variant?: "solid" | "dashed" | "dotted"
}

export interface UIPageLayoutPreviewData {
  entity_type: string
  entity_id: string
  layout_json: TemplateBlock[]
  summary?: string
}
