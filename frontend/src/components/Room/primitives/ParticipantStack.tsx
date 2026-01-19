/**
 * ParticipantStack Primitive
 *
 * Overlapping avatars showing room participants.
 * Click to open full participant list popover.
 */

import * as React from "react"
import { Bot, User } from "lucide-react"
import { cn } from "@/lib/utils"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { Button } from "@/components/ui/button"
import { getInitials } from "@/utils"

export interface Participant {
  id: string
  name: string
  type: "user" | "agent"
  role?: string
  badges?: string[]
  isActive?: boolean
}

interface ParticipantStackProps {
  /** List of participants */
  participants: Participant[]
  /** Max avatars to show before +N */
  maxVisible?: number
  /** Callback when participant is clicked */
  onParticipantClick?: (participant: Participant) => void
  /** Additional className */
  className?: string
}

export function ParticipantStack({
  participants,
  maxVisible = 4,
  onParticipantClick,
  className,
}: ParticipantStackProps) {
  const visible = participants.slice(0, maxVisible)
  const overflow = participants.length - maxVisible

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          className={cn("flex items-center gap-1 h-auto py-1 px-2", className)}
        >
          <div className="flex -space-x-2">
            {visible.map((participant) => (
              <Avatar
                key={participant.id}
                className="h-7 w-7 border-2 border-background"
              >
                <AvatarFallback
                  className={cn(
                    "text-xs",
                    participant.type === "agent"
                      ? "bg-primary/20 text-primary"
                      : "bg-muted text-muted-foreground"
                  )}
                >
                  {participant.type === "agent" ? (
                    <Bot className="h-3 w-3" />
                  ) : (
                    getInitials(participant.name)
                  )}
                </AvatarFallback>
              </Avatar>
            ))}
          </div>
          {overflow > 0 && (
            <span className="text-xs text-muted-foreground ml-1">
              +{overflow}
            </span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-72 p-0" align="end">
        <div className="p-3 border-b">
          <h4 className="font-medium text-sm">
            Participants ({participants.length})
          </h4>
        </div>
        <div className="max-h-64 overflow-y-auto p-2">
          {participants.map((participant) => (
            <button
              key={participant.id}
              onClick={() => onParticipantClick?.(participant)}
              className="flex items-center gap-3 w-full p-2 rounded-md hover:bg-muted text-left"
            >
              <Avatar className="h-8 w-8">
                <AvatarFallback
                  className={cn(
                    participant.type === "agent"
                      ? "bg-primary/20 text-primary"
                      : "bg-muted text-muted-foreground"
                  )}
                >
                  {participant.type === "agent" ? (
                    <Bot className="h-4 w-4" />
                  ) : (
                    getInitials(participant.name)
                  )}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{participant.name}</p>
                {participant.badges && participant.badges.length > 0 && (
                  <p className="text-xs text-muted-foreground">
                    {participant.badges.join(" ")}
                  </p>
                )}
              </div>
              {participant.role && (
                <span className="text-xs text-muted-foreground px-2 py-0.5 bg-muted rounded">
                  {participant.role}
                </span>
              )}
            </button>
          ))}
        </div>
      </PopoverContent>
    </Popover>
  )
}
