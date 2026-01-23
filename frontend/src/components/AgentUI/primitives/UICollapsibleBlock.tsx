import { ChevronDown } from "lucide-react"
import { useState } from "react"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { cn } from "@/lib/utils"
import type { UICollapsibleData } from "../types"

export function UICollapsibleBlock({ data }: { data: UICollapsibleData }) {
  const [open, setOpen] = useState(data.default_open ?? false)

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
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
