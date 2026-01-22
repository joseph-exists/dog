// src/components/Page/blocks/DataTableBlock.tsx
import { useQuery } from "@tanstack/react-query"

import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

import { BlockContainer } from "../primitives"
import { fetchDataSource } from "../registry"

export interface ColumnConfig {
  key: string
  label: string
  width?: string
}

export interface DataTableBlockConfig {
  title: string
  dataSource: string
  columns: ColumnConfig[]
  maxRows: number
}

export interface DataTableContent {
  rows?: Record<string, unknown>[]
}

export interface DataTableBlockProps {
  config: DataTableBlockConfig
  content?: DataTableContent
  className?: string
}

/**
 * DataTableBlock - Displays tabular data from a configured data source
 *
 * Fetches data using TanStack Query and renders it in a shadcn Table.
 * Supports configurable columns and row limits.
 * Can receive data directly via content prop or fetch from dataSource.
 * View-only block - no edit functionality.
 */
export function DataTableBlock({
  config,
  content,
  className,
}: DataTableBlockProps) {
  // Only fetch if no content is provided
  const {
    data: fetchedData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["blockData", config.dataSource],
    queryFn: () => fetchDataSource(config.dataSource),
    enabled: !content?.rows,
  })

  // Use content if provided, otherwise use fetched data
  const data = content?.rows ?? fetchedData

  // Loading state (only if fetching)
  if (isLoading && !content?.rows) {
    return (
      <BlockContainer title={config.title} className={className}>
        <div className="p-4 space-y-2">
          {Array.from({ length: Math.min(config.maxRows, 5) }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      </BlockContainer>
    )
  }

  // Error state
  if (error && !content?.rows) {
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

  // Limit rows to maxRows
  const rows = data.slice(0, config.maxRows) as Record<string, unknown>[]

  return (
    <BlockContainer title={config.title} scrollable className={className}>
      <Table>
        <TableHeader>
          <TableRow>
            {config.columns.map((column) => (
              <TableHead
                key={column.key}
                style={column.width ? { width: column.width } : undefined}
              >
                {column.label}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((row, rowIndex) => (
            <TableRow key={rowIndex}>
              {config.columns.map((column) => (
                <TableCell key={column.key}>
                  {String(row[column.key] ?? "")}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </BlockContainer>
  )
}
