import { Separator } from "@/components/ui/separator"
import { cn } from "@/lib/utils"
import type { UIDividerData } from "../types"

const variantStyles = {
  solid: "",
  dashed: "border-dashed",
  dotted: "border-dotted",
}

export function UIDividerBlock({ data }: { data: UIDividerData }) {
  if (data.label) {
    return (
      <div className="flex items-center gap-4">
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

  return <Separator className={cn(variantStyles[data.variant || "solid"])} />
}
