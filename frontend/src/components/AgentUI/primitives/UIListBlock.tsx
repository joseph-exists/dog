import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import type { UIListData } from "../types"

export function UIListBlock({ data }: { data: UIListData }) {
  const ListTag = data.ordered ? "ol" : "ul"

  return (
    <div>
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
