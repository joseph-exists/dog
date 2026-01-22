// src/components/Page/blocks/ChartBlock.tsx
import { useQuery } from "@tanstack/react-query"
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  XAxis,
  YAxis,
} from "recharts"
import {
  type ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"
import { Skeleton } from "@/components/ui/skeleton"

import { BlockContainer } from "../primitives"
import { fetchDataSource } from "../registry"

export interface ChartBlockConfig {
  title: string
  chartType: "area" | "bar" | "line" | "pie"
  dataSource: string
}

export interface ChartContent {
  data?: Record<string, unknown>[]
}

export interface ChartBlockProps {
  config: ChartBlockConfig
  content?: ChartContent
  className?: string
}

// Default chart config for styling
const defaultChartConfig: ChartConfig = {
  value: {
    label: "Value",
    color: "hsl(var(--chart-1))",
  },
}

// Default colors for pie chart segments
const PIE_COLORS = [
  "hsl(var(--chart-1))",
  "hsl(var(--chart-2))",
  "hsl(var(--chart-3))",
  "hsl(var(--chart-4))",
  "hsl(var(--chart-5))",
]

/**
 * ChartBlock - Displays chart visualization from a configured data source
 *
 * Fetches data using TanStack Query and renders it using recharts.
 * Supports area, bar, line, and pie chart types.
 * Can receive data directly via content prop or fetch from dataSource.
 * View-only block - no edit functionality.
 */
export function ChartBlock({ config, content, className }: ChartBlockProps) {
  // Only fetch if no content is provided
  const { data: fetchedData, isLoading, error } = useQuery({
    queryKey: ["blockData", config.dataSource],
    queryFn: () => fetchDataSource(config.dataSource),
    enabled: !content?.data,
  })

  // Use content if provided, otherwise use fetched data
  const data = content?.data ?? fetchedData

  // Loading state (only if fetching)
  if (isLoading && !content?.data) {
    return (
      <BlockContainer title={config.title} className={className}>
        <div className="p-4">
          <Skeleton className="h-[200px] w-full" />
        </div>
      </BlockContainer>
    )
  }

  // Error state
  if (error && !content?.data) {
    return (
      <BlockContainer title={config.title} className={className}>
        <div className="p-4 text-sm text-destructive">
          Failed to load data:{" "}
          {error instanceof Error ? error.message : "Unknown error"}
        </div>
      </BlockContainer>
    )
  }

  // Empty state
  if (!data || data.length === 0) {
    return (
      <BlockContainer title={config.title} className={className}>
        <div className="p-4 text-sm text-muted-foreground">
          No data available
        </div>
      </BlockContainer>
    )
  }

  const chartData = data as Record<string, unknown>[]

  return (
    <BlockContainer title={config.title} className={className}>
      <div className="p-4">
        <ChartContainer
          config={defaultChartConfig}
          className="h-[200px] w-full"
        >
          {renderChart(config.chartType, chartData)}
        </ChartContainer>
      </div>
    </BlockContainer>
  )
}

/**
 * Renders the appropriate chart based on chart type
 */
function renderChart(
  chartType: ChartBlockConfig["chartType"],
  data: Record<string, unknown>[],
) {
  // Try to infer data keys from the first item
  const firstItem = data[0]
  const keys = Object.keys(firstItem)
  const labelKey = keys.find((k) => typeof firstItem[k] === "string") || keys[0]
  const valueKey =
    keys.find((k) => typeof firstItem[k] === "number") || keys[1] || "value"

  switch (chartType) {
    case "area":
      return (
        <AreaChart data={data} accessibilityLayer>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={labelKey} tickLine={false} axisLine={false} />
          <YAxis tickLine={false} axisLine={false} />
          <ChartTooltip content={<ChartTooltipContent />} />
          <Area
            type="monotone"
            dataKey={valueKey}
            fill="var(--color-value)"
            fillOpacity={0.3}
            stroke="var(--color-value)"
          />
        </AreaChart>
      )

    case "bar":
      return (
        <BarChart data={data} accessibilityLayer>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={labelKey} tickLine={false} axisLine={false} />
          <YAxis tickLine={false} axisLine={false} />
          <ChartTooltip content={<ChartTooltipContent />} />
          <Bar
            dataKey={valueKey}
            fill="var(--color-value)"
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      )

    case "line":
      return (
        <LineChart data={data} accessibilityLayer>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={labelKey} tickLine={false} axisLine={false} />
          <YAxis tickLine={false} axisLine={false} />
          <ChartTooltip content={<ChartTooltipContent />} />
          <Line
            type="monotone"
            dataKey={valueKey}
            stroke="var(--color-value)"
            strokeWidth={2}
            dot={{ fill: "var(--color-value)" }}
          />
        </LineChart>
      )

    case "pie":
      return (
        <PieChart accessibilityLayer>
          <ChartTooltip content={<ChartTooltipContent />} />
          <Pie
            data={data}
            dataKey={valueKey}
            nameKey={labelKey}
            cx="50%"
            cy="50%"
            innerRadius={40}
            outerRadius={80}
          >
            {data.map((_, index) => (
              <Cell
                key={`cell-${index}`}
                fill={PIE_COLORS[index % PIE_COLORS.length]}
              />
            ))}
          </Pie>
        </PieChart>
      )
  }
}
