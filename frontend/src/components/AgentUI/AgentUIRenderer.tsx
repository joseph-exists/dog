/**
 * Agent UI Renderer
 *
 * Renders structured UI components emitted by agents alongside their text responses.
 * Falls back gracefully when component types aren't supported.
 *
 * Usage:
 *   {message.ui_components?.map((component, idx) => (
 *     <AgentUIRenderer key={component.id || idx} component={component} />
 *   ))}
 */

import {
  AlertCircle,
  AlertTriangle,
  CheckCircle,
  ChevronDown,
  Info,
  Quote,
} from "lucide-react"
import { useState } from "react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { Separator } from "@/components/ui/separator"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { cn } from "@/lib/utils"
import type {
  UIActionButtonsData,
  UIAlertData,
  UICardData,
  UICodeData,
  UICollapsibleData,
  UIComponent,
  UIDividerData,
  UIListData,
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

  // Render based on component type
  // Cast through unknown since data comes from JSON and we trust the backend schema
  switch (type) {
    case "card":
      return <CardComponent data={data as unknown as UICardData} />
    case "list":
      return <ListComponent data={data as unknown as UIListData} />
    case "table":
      return <TableComponent data={data as unknown as UITableData} />
    case "progress":
      return <ProgressComponent data={data as unknown as UIProgressData} />
    case "action_buttons":
      return (
        <ActionButtonsComponent
          data={data as unknown as UIActionButtonsData}
          onAction={onAction}
        />
      )
    case "code":
      return <CodeComponent data={data as unknown as UICodeData} />
    case "quote":
      return <QuoteComponent data={data as unknown as UIQuoteData} />
    case "alert":
      return <AlertComponent data={data as unknown as UIAlertData} />
    case "collapsible":
      return (
        <CollapsibleComponent data={data as unknown as UICollapsibleData} />
      )
    case "tabs":
      return <TabsComponent data={data as unknown as UITabsData} />
    case "divider":
      return <DividerComponent data={data as unknown as UIDividerData} />
    default:
      // Unknown component type - show fallback
      return fallback_text ? (
        <p className="text-sm text-muted-foreground italic">{fallback_text}</p>
      ) : null
  }
}

// =============================================================================
// Individual Component Implementations
// =============================================================================

function CardComponent({ data }: { data: UICardData }) {
  const variantStyles = {
    default: "",
    highlight: "border-primary bg-primary/5",
    warning: "border-yellow-500 bg-yellow-50 dark:bg-yellow-900/10",
    success: "border-green-500 bg-green-50 dark:bg-green-900/10",
    info: "border-blue-500 bg-blue-50 dark:bg-blue-900/10",
  }

  return (
    <Card className={cn("mt-3", variantStyles[data.variant || "default"])}>
      <CardHeader className="pb-2">
        <CardTitle className="text-base flex items-center gap-2">
          {data.icon && <span className="text-lg">📌</span>}
          {data.title}
        </CardTitle>
        {data.subtitle && <CardDescription>{data.subtitle}</CardDescription>}
      </CardHeader>
      <CardContent>
        <p className="text-sm whitespace-pre-wrap">{data.body}</p>
      </CardContent>
      {data.footer && (
        <CardFooter className="text-xs text-muted-foreground">
          {data.footer}
        </CardFooter>
      )}
    </Card>
  )
}

function ListComponent({ data }: { data: UIListData }) {
  const ListTag = data.ordered ? "ol" : "ul"

  return (
    <div className="mt-3">
      {data.title && <h4 className="text-sm font-medium mb-2">{data.title}</h4>}
      <ListTag
        className={cn(
          "space-y-1 pl-4",
          data.ordered ? "list-decimal" : "list-disc",
        )}
      >
        {data.items.map((item, idx) => (
          <li key={idx} className="text-sm">
            <span className="font-medium">{item.label}</span>
            {item.badge && (
              <Badge
                variant={
                  item.badge_variant === "success"
                    ? "default"
                    : item.badge_variant === "warning"
                      ? "secondary"
                      : item.badge_variant === "error"
                        ? "destructive"
                        : "outline"
                }
                className="ml-2 text-xs"
              >
                {item.badge}
              </Badge>
            )}
            {item.description && (
              <p className="text-muted-foreground text-xs mt-0.5">
                {item.description}
              </p>
            )}
          </li>
        ))}
      </ListTag>
    </div>
  )
}

function TableComponent({ data }: { data: UITableData }) {
  return (
    <div className="mt-3">
      {data.title && <h4 className="text-sm font-medium mb-2">{data.title}</h4>}
      <div className="rounded-md border overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              {data.columns.map((col) => (
                <TableHead
                  key={col.key}
                  className={cn(
                    col.align === "center" && "text-center",
                    col.align === "right" && "text-right",
                  )}
                >
                  {col.header}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.rows.map((row, idx) => (
              <TableRow
                key={idx}
                className={cn(data.striped && idx % 2 === 1 && "bg-muted/50")}
              >
                {data.columns.map((col) => (
                  <TableCell
                    key={col.key}
                    className={cn(
                      col.align === "center" && "text-center",
                      col.align === "right" && "text-right",
                      data.compact && "py-1 text-xs",
                    )}
                  >
                    {String(row[col.key] ?? "")}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}

function ProgressComponent({ data }: { data: UIProgressData }) {
  const colorClasses = {
    blue: "bg-blue-500",
    green: "bg-green-500",
    yellow: "bg-yellow-500",
    red: "bg-red-500",
    purple: "bg-purple-500",
  }

  return (
    <div className="mt-3 space-y-2">
      {data.title && <h4 className="text-sm font-medium">{data.title}</h4>}
      {data.items.map((item, idx) => (
        <div key={idx} className="space-y-1">
          <div className="flex justify-between text-xs">
            <span>{item.label}</span>
            {data.show_percentage !== false && <span>{item.value}%</span>}
          </div>
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <div
              className={cn(
                "h-full transition-all",
                colorClasses[item.color || "blue"],
              )}
              style={{ width: `${Math.min(100, Math.max(0, item.value))}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}

function ActionButtonsComponent({
  data,
  onAction,
}: {
  data: UIActionButtonsData
  onAction?: (action: string) => void
}) {
  const layoutClasses = {
    horizontal: "flex flex-wrap gap-2",
    vertical: "flex flex-col gap-2",
    grid: "grid grid-cols-2 gap-2",
  }

  return (
    <div className={cn("mt-3", layoutClasses[data.layout || "horizontal"])}>
      {data.buttons.map((btn, idx) => (
        <Button
          key={idx}
          variant={
            btn.variant === "primary"
              ? "default"
              : btn.variant === "outline"
                ? "outline"
                : btn.variant === "ghost"
                  ? "ghost"
                  : "secondary"
          }
          size="sm"
          disabled={btn.disabled}
          onClick={() => onAction?.(btn.action)}
        >
          {btn.label}
        </Button>
      ))}
    </div>
  )
}

function CodeComponent({ data }: { data: UICodeData }) {
  return (
    <div className="mt-3">
      {data.title && (
        <div className="text-xs text-muted-foreground mb-1 font-mono">
          {data.title}
        </div>
      )}
      <pre className="bg-muted rounded-md p-3 overflow-x-auto text-sm">
        <code className={data.language ? `language-${data.language}` : ""}>
          {data.code}
        </code>
      </pre>
    </div>
  )
}

function QuoteComponent({ data }: { data: UIQuoteData }) {
  const variantStyles = {
    default: "border-l-muted-foreground",
    highlight: "border-l-primary bg-primary/5",
    subtle: "border-l-muted opacity-80",
  }

  return (
    <blockquote
      className={cn(
        "mt-3 border-l-4 pl-4 py-2",
        variantStyles[data.variant || "default"],
      )}
    >
      <Quote className="h-4 w-4 text-muted-foreground mb-1" />
      <p className="text-sm italic">{data.text}</p>
      {data.attribution && (
        <cite className="text-xs text-muted-foreground mt-1 block">
          — {data.attribution}
        </cite>
      )}
    </blockquote>
  )
}

function AlertComponent({ data }: { data: UIAlertData }) {
  const [dismissed, setDismissed] = useState(false)

  if (dismissed) return null

  const icons = {
    info: <Info className="h-4 w-4" />,
    success: <CheckCircle className="h-4 w-4" />,
    warning: <AlertTriangle className="h-4 w-4" />,
    error: <AlertCircle className="h-4 w-4" />,
  }

  const variantStyles = {
    info: "",
    success: "border-green-500 text-green-700 dark:text-green-400",
    warning: "border-yellow-500 text-yellow-700 dark:text-yellow-400",
    error: "border-red-500 text-red-700 dark:text-red-400",
  }

  return (
    <Alert className={cn("mt-3", variantStyles[data.variant || "info"])}>
      {icons[data.variant || "info"]}
      <div className="flex-1">
        {data.title && <AlertTitle>{data.title}</AlertTitle>}
        <AlertDescription>{data.message}</AlertDescription>
      </div>
      {data.dismissible && (
        <button
          type="button"
          onClick={() => setDismissed(true)}
          className="absolute top-2 right-2 text-muted-foreground hover:text-foreground"
        >
          ×
        </button>
      )}
    </Alert>
  )
}

function CollapsibleComponent({ data }: { data: UICollapsibleData }) {
  const [open, setOpen] = useState(data.default_open ?? false)

  return (
    <Collapsible open={open} onOpenChange={setOpen} className="mt-3">
      <CollapsibleTrigger className="flex items-center gap-2 text-sm font-medium hover:text-primary transition-colors">
        <ChevronDown
          className={cn("h-4 w-4 transition-transform", open && "rotate-180")}
        />
        {data.title}
      </CollapsibleTrigger>
      <CollapsibleContent className="mt-2 pl-6">
        <p className="text-sm text-muted-foreground whitespace-pre-wrap">
          {data.content}
        </p>
      </CollapsibleContent>
    </Collapsible>
  )
}

function TabsComponent({ data }: { data: UITabsData }) {
  const defaultTab = `tab-${data.default_tab ?? 0}`

  return (
    <Tabs defaultValue={defaultTab} className="mt-3">
      <TabsList>
        {data.tabs.map((tab, idx) => (
          <TabsTrigger key={idx} value={`tab-${idx}`}>
            {tab.label}
          </TabsTrigger>
        ))}
      </TabsList>
      {data.tabs.map((tab, idx) => (
        <TabsContent key={idx} value={`tab-${idx}`} className="text-sm">
          <p className="whitespace-pre-wrap">{tab.content}</p>
        </TabsContent>
      ))}
    </Tabs>
  )
}

function DividerComponent({ data }: { data: UIDividerData }) {
  const variantStyles = {
    solid: "",
    dashed: "border-dashed",
    dotted: "border-dotted",
  }

  if (data.label) {
    return (
      <div className="mt-3 flex items-center gap-4">
        <Separator
          className={cn("flex-1", variantStyles[data.variant || "solid"])}
        />
        <span className="text-xs text-muted-foreground">{data.label}</span>
        <Separator
          className={cn("flex-1", variantStyles[data.variant || "solid"])}
        />
      </div>
    )
  }

  return (
    <Separator className={cn("mt-3", variantStyles[data.variant || "solid"])} />
  )
}
