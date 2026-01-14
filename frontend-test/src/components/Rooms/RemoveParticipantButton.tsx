/**
 * RemoveParticipantButton Component
 *
 * Confirmation dialog for removing a participant from the room.
 */

import { Loader2, Trash2 } from "lucide-react"
import { useState } from "react"

import type { ApiError } from "@/client/core/ApiError"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

interface RemoveParticipantButtonProps {
  participantId: string
  participantName: string
  participantType: "user" | "agent"
  onRemove: (participantId: string) => Promise<void>
}

export default function RemoveParticipantButton({
  participantId,
  participantName,
  participantType,
  onRemove,
}: RemoveParticipantButtonProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [isRemoving, setIsRemoving] = useState(false)
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const handleRemove = async () => {
    setIsRemoving(true)
    try {
      await onRemove(participantId)
      showSuccessToast(`${participantName} removed from room.`)
      setIsOpen(false)
    } catch (err) {
      handleError.call(showErrorToast, err as ApiError)
    } finally {
      setIsRemoving(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <Button
        size="icon-sm"
        variant="ghost"
        className="text-destructive hover:text-destructive hover:bg-destructive/10"
        onClick={() => setIsOpen(true)}
      >
        <Trash2 className="h-3 w-3" />
      </Button>

      <DialogContent>
        <DialogHeader>
          <DialogTitle>Remove Participant?</DialogTitle>
          <DialogDescription>
            Are you sure you want to remove <strong>{participantName}</strong>{" "}
            from this room?{" "}
            {participantType === "agent" &&
              "The agent will no longer respond to messages."}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline">Cancel</Button>
          </DialogClose>
          <Button
            variant="destructive"
            onClick={handleRemove}
            disabled={isRemoving}
          >
            {isRemoving && <Loader2 className="h-4 w-4 animate-spin" />}
            Remove
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
