import { cn } from "@/lib/utils"
import type { UIProgressData } from "../types"

const colorClasses = {
  blue: "bg-blue-500",
  green: "bg-green-500",
  yellow: "bg-yellow-500",
  red: "bg-red-500",
  purple: "bg-purple-500",
}

export function UIProgressBlock({ data }: { data: UIProgressData }) {
  return (
    <div className="space-y-2">
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
