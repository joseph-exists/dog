import type { ApiError } from "@/client/core/ApiError"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import { Button } from "@chakra-ui/react"
import { useState } from "react"
import { FaTrash } from "react-icons/fa"
import {
  DialogActionTrigger,
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTitle,
} from "../ui/dialog"

interface RemoveParticipantButtonProps {
  participantId: string
  participantName: string
  participantType: "user" | "agent"
  onRemove: (participantId: string) => Promise<void>
}

const RemoveParticipantButton = ({
  participantId,
  participantName,
  participantType,
  onRemove,
}: RemoveParticipantButtonProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const [isRemoving, setIsRemoving] = useState(false)
  const { showSuccessToast } = useCustomToast()

  const handleRemove = async () => {
    setIsRemoving(true)
    try {
      await onRemove(participantId)
      showSuccessToast(`${participantName} removed from room.`)
      setIsOpen(false)
    } catch (err) {
      handleError(err as ApiError)
    } finally {
      setIsRemoving(false)
    }
  }

  return (
    <DialogRoot
      size="sm"
      open={isOpen}
      onOpenChange={({ open }) => setIsOpen(open)}
    >
      <Button
        size="xs"
        variant="ghost"
        colorPalette="red"
        onClick={() => setIsOpen(true)}
      >
        <FaTrash />
      </Button>

      <DialogContent>
        <DialogHeader>
          <DialogTitle>Remove Participant?</DialogTitle>
        </DialogHeader>
        <DialogBody>
          Are you sure you want to remove <strong>{participantName}</strong>{" "}
          from this room?{" "}
          {participantType === "agent" &&
            "The agent will no longer respond to messages."}
        </DialogBody>
        <DialogFooter gap={2}>
          <DialogActionTrigger asChild>
            <Button variant="subtle" colorPalette="gray">
              Cancel
            </Button>
          </DialogActionTrigger>
          <Button
            colorPalette="red"
            onClick={handleRemove}
            loading={isRemoving}
          >
            Remove
          </Button>
        </DialogFooter>
        <DialogCloseTrigger />
      </DialogContent>
    </DialogRoot>
  )
}

export default RemoveParticipantButton
