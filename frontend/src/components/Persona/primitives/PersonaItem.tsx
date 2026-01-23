// src/components/Persona/primitives/PersonaItem.tsx
import { Check, Circle } from "lucide-react"
import { cn } from "@/lib/utils"
import type { PersonaItemProps } from "../types"
import { PersonaActions } from "./PersonaActions"
import { PersonaAvatar } from "./PersonaAvatar"

export function PersonaItem({
  persona,
  isSelected = false,
  selectionMode = "none",
  onSelect,
  onEdit,
  onRemove,
  showActions = false,
  className,
}: PersonaItemProps) {
  const displayName = persona.nickname || persona.name

  return (
    <div
      className={cn(
        "group flex items-center gap-3 px-3 py-2 rounded-md cursor-pointer",
        "hover:bg-accent/50 transition-colors",
        isSelected && "bg-accent",
        className,
      )}
      onClick={onSelect}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault()
          onSelect?.()
        }
      }}
      role="option"
      aria-selected={isSelected}
      tabIndex={0}
    >
      {/* Selection indicator */}
      {selectionMode === "radio" && (
        <div className="shrink-0">
          {isSelected ? (
            <Check className="h-4 w-4 text-primary" />
          ) : (
            <Circle className="h-4 w-4 text-muted-foreground/40" />
          )}
        </div>
      )}
      {selectionMode === "checkbox" && (
        <div
          className={cn(
            "shrink-0 h-4 w-4 rounded border",
            isSelected
              ? "bg-primary border-primary"
              : "border-muted-foreground/40",
          )}
        >
          {isSelected && <Check className="h-3 w-3 text-primary-foreground" />}
        </div>
      )}

      {/* Avatar */}
      <PersonaAvatar
        name={persona.name}
        size="sm"
        showActiveIndicator
        isActive={persona.isActive}
      />

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium truncate">{displayName}</div>
        {persona.description && (
          <div className="text-xs text-muted-foreground truncate">
            {persona.description}
          </div>
        )}
      </div>

      {/* Actions (hover only) */}
      {showActions && (
        <div className="opacity-0 group-hover:opacity-100 transition-opacity">
          <PersonaActions
            actions={[
              ...(onEdit ? (["edit"] as const) : []),
              ...(onRemove ? (["remove"] as const) : []),
            ]}
            onEdit={onEdit}
            onRemove={onRemove}
          />
        </div>
      )}
    </div>
  )
}
