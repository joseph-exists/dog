/**
 * ChoiceItem
 *
 * Renders a single story choice with availability and loading states.
 */

import { Loader2, Lock } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import type { ChoiceViewModel } from "@/services/roomRuntimeService"

interface ChoiceItemProps {
  choice: ChoiceViewModel
  isAvailable: boolean
  unavailableReason?: string
  isLoading?: boolean
  onSelect: (choice: ChoiceViewModel) => void
  onInspect?: (choice: ChoiceViewModel) => void
  variant?: "button" | "card" | "compact"
}

export function ChoiceItem({
  choice,
  isAvailable,
  unavailableReason,
  isLoading = false,
  onSelect,
  onInspect,
  variant = "button",
}: ChoiceItemProps) {
  const isDisabled = !isAvailable || isLoading

  if (variant === "compact") {
    return (
      <div className="space-y-1">
        <button
          type="button"
          className={cn(
            "demo-choice w-full rounded-md border px-3 py-2 text-left text-sm transition-colors",
            isDisabled
              ? "cursor-not-allowed bg-muted text-muted-foreground"
              : "hover:border-primary hover:bg-muted/60",
          )}
          disabled={isDisabled}
          onClick={() => onSelect(choice)}
          title={unavailableReason || undefined}
        >
          <div className="flex items-center gap-2">
            {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
            {!isAvailable && !isLoading && <Lock className="h-4 w-4" />}
            <span>{choice.text}</span>
          </div>
        </button>
        {isDisabled && unavailableReason && (
          <p className="text-xs text-muted-foreground">{unavailableReason}</p>
        )}
      </div>
    )
  }

  if (variant === "card") {
    return (
      <div
        className={cn(
          "demo-choice rounded-md border p-3 transition-colors",
          isDisabled
            ? "cursor-not-allowed bg-muted text-muted-foreground"
            : "hover:border-primary hover:bg-muted/60",
        )}
      >
        <button
          type="button"
          className="w-full text-left"
          onClick={() => onSelect(choice)}
          disabled={isDisabled}
          title={unavailableReason || undefined}
        >
          <div className="flex items-center gap-2">
            {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
            {!isAvailable && !isLoading && <Lock className="h-4 w-4" />}
            <span className="font-medium">{choice.text}</span>
          </div>
        </button>
        {isDisabled && unavailableReason && (
          <p className="mt-2 text-xs text-muted-foreground">
            {unavailableReason}
          </p>
        )}
        {onInspect && (
          <button
            type="button"
            className="mt-2 text-xs text-muted-foreground hover:text-foreground"
            onClick={() => onInspect(choice)}
          >
            Inspect
          </button>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-1">
      <Button
        type="button"
        variant="secondary"
        className="demo-choice w-full justify-start gap-2"
        disabled={isDisabled}
        onClick={() => onSelect(choice)}
        title={unavailableReason || undefined}
      >
        {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
        {!isAvailable && !isLoading && <Lock className="h-4 w-4" />}
        <span className="truncate">{choice.text}</span>
      </Button>
      {isDisabled && unavailableReason && (
        // TODO: consider using a tooltip component when reason codes stabilize.
        <p className="text-xs text-muted-foreground">{unavailableReason}</p>
      )}
    </div>
  )
}
