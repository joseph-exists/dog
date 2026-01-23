import { Quote } from "lucide-react"
import { cn } from "@/lib/utils"
import type { UIQuoteData } from "../types"

const variantStyles = {
  default: "border-l-muted-foreground",
  highlight: "border-l-primary bg-primary/5",
  subtle: "border-l-muted opacity-80",
}

export function UIQuoteBlock({ data }: { data: UIQuoteData }) {
  return (
    <blockquote
      className={cn(
        "border-l-4 pl-4 py-2",
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
