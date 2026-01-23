// src/components/Persona/primitives/PersonaAvatar.tsx
import { Smile } from "lucide-react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { cn } from "@/lib/utils"
import type { PersonaAvatarProps } from "../types"

const sizeClasses = {
  sm: "h-6 w-6",
  md: "h-8 w-8",
  lg: "h-12 w-12",
}

const iconSizes = {
  sm: "h-3 w-3",
  md: "h-4 w-4",
  lg: "h-6 w-6",
}

export function PersonaAvatar({
  name,
  imageUrl,
  size = "md",
  showActiveIndicator = false,
  isActive = false,
  className,
}: PersonaAvatarProps) {
  const initials = name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2)

  return (
    <div className={cn("relative", className)}>
      <Avatar className={cn(sizeClasses[size])}>
        {imageUrl && <AvatarImage src={imageUrl} alt={name} />}
        <AvatarFallback className="text-xs">
          {initials || <Smile className={iconSizes[size]} />}
        </AvatarFallback>
      </Avatar>
      {showActiveIndicator && (
        <span
          className={cn(
            "absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border-2 border-background",
            isActive ? "bg-green-500" : "bg-muted-foreground/40",
          )}
        />
      )}
    </div>
  )
}
