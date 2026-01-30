/**
 * AddParticipantDialog Component
 *
 * Dialog for adding an agent to the room.
 * Fetches available agents from the agent registry API.
 */

import { useQuery } from "@tanstack/react-query"
import { Loader2, Plus } from "lucide-react"
import { useState } from "react"
import { type SubmitHandler, useForm } from "react-hook-form"

import { AgentsService } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import type { UserAgentConfigPublic } from "@/client/types.gen"
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

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
  const [selectedAgentId, setSelectedAgentId] = useState<string>("")
  const { showSuccessToast, showErrorToast } = useCustomToast()

  // Fetch available agents from the registry API
  const {
    data: agentsData,
    isLoading: isLoadingAgents,
    error: agentsError,
  } = useQuery({
    queryKey: ["agents", "available"],
    queryFn: () => AgentsService.listAvailableAgents(),
    // Only fetch when dialog is open to avoid unnecessary requests
    enabled: isOpen,
  })

  const {
    handleSubmit,
    reset,
    setValue,
    formState: { isSubmitting },
  } = useForm<AddParticipantForm>({
    mode: "onChange",
    defaultValues: {
      participant_type: "agent",
      participant_id: "",
    },
  })

  // Sync selected agent with form
  const handleAgentSelect = (value: string) => {
    setSelectedAgentId(value)
    setValue("participant_id", value)
  }

  // Reset state when dialog closes
  const handleOpenChange = (open: boolean) => {
    setIsOpen(open)
    if (!open) {
      setSelectedAgentId("")
      reset()
    }
  }

  // Transform API response to match component needs and filter out already-added agents
  const availableAgents = (agentsData?.data ?? [])
    .filter(
      (agent: UserAgentConfigPublic) => !currentParticipants.includes(agent.id),
    )
    .map((agent: UserAgentConfigPublic) => ({
      value: agent.id,
      label: agent.name,
      description: agent.description,
    }))

  const onSubmit: SubmitHandler<AddParticipantForm> = async (data) => {
    try {
      await onAdd(data.participant_id, data.participant_type)
      showSuccessToast("Participant added successfully.")
      setSelectedAgentId("")
      reset()
      setIsOpen(false)
    } catch (err) {
      handleError.call(showErrorToast, err as ApiError)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
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
            {/* Loading state */}
            {isLoadingAgents && (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                <span className="ml-2 text-sm text-muted-foreground">
                  Loading agents...
                </span>
              </div>
            )}

            {/* Error state */}
            {agentsError && (
              <p className="text-sm text-destructive">
                Failed to load available agents. Please try again.
              </p>
            )}

            {/* Agent selection */}
            {!isLoadingAgents && !agentsError && availableAgents.length > 0 && (
              <div className="space-y-2">
                <Label htmlFor="participant_id">
                  Agent <span className="text-destructive">*</span>
                </Label>
                <Select
                  value={selectedAgentId}
                  onValueChange={handleAgentSelect}
                >
                  <SelectTrigger id="participant_id">
                    <SelectValue placeholder="Select an agent" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableAgents.map((agent) => (
                      <SelectItem key={agent.value} value={agent.value}>
                        <div className="flex flex-col">
                          <span>{agent.label}</span>
                          {agent.description && (
                            <span className="text-xs text-muted-foreground">
                              {agent.description}
                            </span>
                          )}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* No agents available message */}
            {!isLoadingAgents &&
              !agentsError &&
              availableAgents.length === 0 && (
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
                !selectedAgentId ||
                availableAgents.length === 0 ||
                isSubmitting ||
                isLoadingAgents ||
                !!agentsError
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
