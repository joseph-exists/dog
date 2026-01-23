// src/components/Persona/primitives/PersonaCard.tsx
import { Check } from "lucide-react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"
import type { PersonaCardProps } from "../types"
import { PersonaAvatar } from "./PersonaAvatar"
import { PersonaBadges } from "./PersonaBadges"

export function PersonaCard({
  persona,
  isSelected = false,
  onSelect,
  onEditNickname,
  onRemove,
  readonly = false,
  className,
}: PersonaCardProps) {
  const [isEditingNickname, setIsEditingNickname] = useState(false)
  const [nicknameValue, setNicknameValue] = useState(persona.nickname || "")

  const handleSaveNickname = () => {
    onEditNickname?.(nicknameValue)
    setIsEditingNickname(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleSaveNickname()
    if (e.key === "Escape") setIsEditingNickname(false)
  }

  return (
    <Card
      className={cn(
        "relative transition-all cursor-pointer",
        "hover:shadow-md",
        isSelected && "ring-2 ring-primary",
        className,
      )}
      onClick={onSelect}
    >
      {isSelected && (
        <div className="absolute top-2 right-2">
          <Check className="h-4 w-4 text-primary" />
        </div>
      )}

      <CardContent className="p-4 space-y-3">
        {/* Header: avatar + name */}
        <div className="flex items-center gap-3">
          <PersonaAvatar
            name={persona.name}
            size="lg"
            showActiveIndicator
            isActive={persona.isActive}
          />
          <div className="flex-1 min-w-0">
            <div className="font-medium truncate">{persona.name}</div>
            {isEditingNickname ? (
              <Input
                value={nicknameValue}
                onChange={(e) => setNicknameValue(e.target.value)}
                onBlur={handleSaveNickname}
                onKeyDown={handleKeyDown}
                placeholder="Nickname..."
                className="h-6 text-xs mt-1"
                autoFocus
                onClick={(e) => e.stopPropagation()}
              />
            ) : (
              persona.nickname && (
                <button
                  type="button"
                  className="text-xs text-muted-foreground truncate cursor-text text-left bg-transparent border-none p-0"
                  onClick={(e) => {
                    if (!readonly && onEditNickname) {
                      e.stopPropagation()
                      setIsEditingNickname(true)
                    }
                  }}
                >
                  aka &ldquo;{persona.nickname}&rdquo;
                </button>
              )
            )}
          </div>
        </div>

        {/* Description */}
        {persona.description && (
          <p className="text-sm text-muted-foreground line-clamp-2">
            {persona.description}
          </p>
        )}

        {/* Badges */}
        <PersonaBadges
          traits={persona.traits}
          qualities={persona.qualities}
          domains={persona.domains}
          variant="compact"
        />
      </CardContent>

      {/* Actions footer */}
      {!readonly && (onEditNickname || onRemove) && (
        <CardFooter className="p-3 pt-0 gap-2">
          {onEditNickname && !isEditingNickname && (
            <Button
              variant="outline"
              size="sm"
              className="text-xs"
              onClick={(e) => {
                e.stopPropagation()
                setIsEditingNickname(true)
              }}
            >
              Edit nickname
            </Button>
          )}
          {onRemove && (
            <Button
              variant="ghost"
              size="sm"
              className="text-xs text-destructive hover:text-destructive"
              onClick={(e) => {
                e.stopPropagation()
                onRemove()
              }}
            >
              Remove
            </Button>
          )}
        </CardFooter>
      )}
    </Card>
  )
}
