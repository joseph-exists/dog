import type { ReactNode } from "react"

export type SvgPanelProminence = "primary" | "auxiliary"

export interface SvgPanelConfig {
  id: string
  kind: string
  prominence: SvgPanelProminence
  title: string
  default_size?: number
  min_size?: number
  max_size?: number
  render: () => ReactNode
}
