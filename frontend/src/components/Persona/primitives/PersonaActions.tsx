// src/components/Persona/primitives/PersonaActions.tsx
import { Edit2, Plus, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

type ActionType = "add" | "edit" | "remove"

interface PersonaActionsProps {
  actions: ActionType[]
  onAdd?: () => void
  onEdit?: () => void
  onRemove?: () => void
  isLoading?: boolean
  className?: string
}

const actionConfig = {
  add: { icon: Plus, label: "Add", variant: "ghost" as const },
  edit: { icon: Edit2, label: "Edit", variant: "ghost" as const },
  remove: { icon: Trash2, label: "Remove", variant: "ghost" as const },
}

export function PersonaActions({
  actions,
  onAdd,
  onEdit,
  onRemove,
  isLoading = false,
  className,
}: PersonaActionsProps) {
  const handlers = { add: onAdd, edit: onEdit, remove: onRemove }

  return (
    <div className={cn("flex items-center gap-1", className)}>
      {actions.map((action) => {
        const config = actionConfig[action]
        const Icon = config.icon
        return (
          <Button
            key={action}
            variant={config.variant}
            size="icon"
            className="h-7 w-7"
            onClick={(e) => {
              e.stopPropagation()
              handlers[action]?.()
            }}
            disabled={isLoading}
            aria-label={config.label}
          >
            <Icon className="h-4 w-4" />
          </Button>
        )
      })}
    </div>
  )
}
