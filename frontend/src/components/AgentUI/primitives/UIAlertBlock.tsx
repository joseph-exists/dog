import { AlertCircle, AlertTriangle, CheckCircle, Info } from "lucide-react"
import { useState } from "react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { cn } from "@/lib/utils"
import type { UIAlertData } from "../types"

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

export function UIAlertBlock({ data }: { data: UIAlertData }) {
  const [dismissed, setDismissed] = useState(false)

  if (dismissed) return null

  return (
    <Alert className={cn(variantStyles[data.variant || "info"])}>
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
          aria-label="Dismiss alert"
        >
          x
        </button>
      )}
    </Alert>
  )
}
