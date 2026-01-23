import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { cn } from "@/lib/utils"
import type { UICardData } from "../types"

const variantStyles = {
  default: "",
  highlight: "border-primary bg-primary/5",
  warning: "border-yellow-500 bg-yellow-50 dark:bg-yellow-900/10",
  success: "border-green-500 bg-green-50 dark:bg-green-900/10",
  info: "border-blue-500 bg-blue-50 dark:bg-blue-900/10",
}

export function UICardBlock({ data }: { data: UICardData }) {
  return (
    <Card className={cn(variantStyles[data.variant || "default"])}>
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
