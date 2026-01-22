/**
 * RuntimeControls
 *
 * Operator controls for rewind/reset actions.
 */

import { Rewind, RotateCcw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface RuntimeControlsProps {
  canRewind: boolean
  canReset: boolean
  isRewinding: boolean
  isResetting: boolean
  onRewind: () => void
  onReset: () => void
  isReadOnly?: boolean
}

export function RuntimeControls({
  canRewind,
  canReset,
  isRewinding,
  isResetting,
  onRewind,
  onReset,
  isReadOnly = false,
}: RuntimeControlsProps) {
  return (
    <div className="space-y-2">
      <Button
        type="button"
        variant="outline"
        className={cn("w-full justify-start gap-2")}
        disabled={!canRewind || isRewinding || isReadOnly}
        onClick={onRewind}
      >
        <Rewind className="h-4 w-4" />
        Rewind one step
      </Button>
      <Button
        type="button"
        variant="outline"
        className={cn("w-full justify-start gap-2")}
        disabled={!canReset || isResetting || isReadOnly}
        onClick={onReset}
      >
        <RotateCcw className="h-4 w-4" />
        Reset to start
      </Button>
      {isReadOnly && (
        <p className="text-xs text-muted-foreground">Read-only room.</p>
      )}
    </div>
  )
}
