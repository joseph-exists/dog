/**
 * AddParticipantDialog Component
 *
 * Dialog for adding an agent to the room.
 */

import { Loader2, Plus } from "lucide-react"
import { useState } from "react"
import { type SubmitHandler, useForm } from "react-hook-form"

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
  DialogTrigger,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import useCustomToast from "@/hooks/useCustomToast"
import { cn } from "@/lib/utils"
import { handleError } from "@/utils"

// Available agents from backend
const AVAILABLE_AGENTS = [
  { value: "StoryAdvisor", label: "Story Advisor" },
  { value: "SymbolWeaver", label: "Symbol Weaver" },
  { value: "CharacterForge", label: "Character Forge" },
  { value: "PlotTwistArchitect", label: "Plot Twist Architect" },
  { value: "DialogueCoach", label: "Dialogue Coach" },
]

interface AddParticipantForm {
  participant_type: "agent" | "user"
  participant_id: string
}

interface AddParticipantDialogProps {
  roomId: string
  currentParticipants: string[]
  onAdd: (participantId: string, type: "user" | "agent") => Promise<void>
}

export default function AddParticipantDialog({
  currentParticipants,
  onAdd,
}: AddParticipantDialogProps) {
  const [isOpen, setIsOpen] = useState(false)
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isValid, isSubmitting },
  } = useForm<AddParticipantForm>({
    mode: "onChange",
    defaultValues: {
      participant_type: "agent",
      participant_id: "",
    },
  })

  // Filter out agents already in the room
  const availableAgents = AVAILABLE_AGENTS.filter(
    (agent) => !currentParticipants.includes(agent.value),
  )

  const onSubmit: SubmitHandler<AddParticipantForm> = async (data) => {
    try {
      await onAdd(data.participant_id, data.participant_type)
      showSuccessToast("Participant added successfully.")
      reset()
      setIsOpen(false)
    } catch (err) {
      handleError.call(showErrorToast, err as ApiError)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline">
          <Plus className="h-4 w-4" />
          Add Participant
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Add Participant to Room</DialogTitle>
            <DialogDescription>
              Select an agent to add to this collaborative room.
            </DialogDescription>
          </DialogHeader>

          <div className="flex flex-col gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="participant_id">
                Agent <span className="text-destructive">*</span>
              </Label>
              <select
                id="participant_id"
                {...register("participant_id", {
                  required: "Please select an agent",
                })}
                className={cn(
                  "flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
                  errors.participant_id && "border-destructive",
                )}
              >
                <option value="" disabled>
                  Select an agent
                </option>
                {availableAgents.map((agent) => (
                  <option key={agent.value} value={agent.value}>
                    {agent.label}
                  </option>
                ))}
              </select>
              {errors.participant_id && (
                <p className="text-sm text-destructive">
                  {errors.participant_id.message}
                </p>
              )}
            </div>

            {availableAgents.length === 0 && (
              <p className="text-sm text-muted-foreground">
                All available agents are already in this room.
              </p>
            )}
          </div>

          <DialogFooter>
            <DialogClose asChild>
              <Button type="button" variant="outline" disabled={isSubmitting}>
                Cancel
              </Button>
            </DialogClose>
            <Button
              type="submit"
              disabled={
                !isValid || availableAgents.length === 0 || isSubmitting
              }
            >
              {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
              Add Agent
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
