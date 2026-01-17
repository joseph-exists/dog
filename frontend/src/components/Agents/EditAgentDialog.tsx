/**
 * EditAgentDialog Component
 *
 * Dialog for editing an existing agent configuration.
 * Uses AgentForm with initial data and handles update API.
 */

import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Loader2Icon, PencilIcon } from "lucide-react"
import { useCallback, useState } from "react"

import type { ApiError } from "@/client/core/ApiError"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import useCustomToast from "@/hooks/useCustomToast"
import {
  AgentService,
  type AgentViewModel,
  type UpdateAgentInput,
} from "@/services/agentService"
import AgentAvatar from "./AgentAvatar"
import AgentForm, { type AgentFormData } from "./AgentForm"

interface EditAgentDialogProps {
  /** The agent to edit */
  agent: AgentViewModel
  /** Custom trigger element (defaults to "Edit" button) */
  trigger?: React.ReactNode
  /** Callback when dialog open state changes */
  onOpenChange?: (open: boolean) => void
  /** Callback when agent is updated successfully */
  onSuccess?: (agent: AgentViewModel) => void
  /** Additional classes for the trigger */
  className?: string
}

export default function EditAgentDialog({
  agent,
  trigger,
  onOpenChange,
  onSuccess,
  className,
}: EditAgentDialogProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [formData, setFormData] = useState<AgentFormData | null>(null)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const handleOpenChange = (open: boolean) => {
    setIsOpen(open)
    onOpenChange?.(open)
    if (!open) {
      setFormData(null)
    }
  }

  const mutation = useMutation({
    mutationFn: (data: UpdateAgentInput) =>
      AgentService.updateAgent(agent.id, data),
    onSuccess: (updatedAgent) => {
      showSuccessToast(`Agent "${updatedAgent.name}" updated successfully.`)
      handleOpenChange(false)
      onSuccess?.(updatedAgent)
    },
    onError: (err: ApiError) => {
      const message =
        (err.body as { detail?: string })?.detail || "Failed to update agent"
      showErrorToast(message)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["agents"] })
      queryClient.invalidateQueries({ queryKey: ["agent", agent.id] })
    },
  })

  const handleFormChange = useCallback((data: AgentFormData) => {
    setFormData(data)
  }, [])

  const handleSubmit = () => {
    if (!formData) return

    // Validate required fields
    if (!formData.name.trim()) {
      showErrorToast("Agent name is required")
      return
    }

    // Only send fields that changed
    const payload: UpdateAgentInput = {}

    if (formData.name.trim() !== agent.name) {
      payload.name = formData.name.trim()
    }
    if ((formData.description.trim() || null) !== (agent.description || null)) {
      payload.description = formData.description.trim() || null
    }
    if (formData.model_name !== agent.model_name) {
      payload.model_name = formData.model_name
    }
    if (
      (formData.system_prompt.trim() || null) !== (agent.system_prompt || null)
    ) {
      payload.system_prompt = formData.system_prompt.trim() || null
    }
    if (formData.participation_mode !== agent.participation_mode) {
      payload.participation_mode = formData.participation_mode
    }

    // Check if anything changed
    if (Object.keys(payload).length === 0) {
      showErrorToast("No changes to save")
      return
    }

    mutation.mutate(payload)
  }

  const isValid = formData?.name.trim()

  const defaultTrigger = (
    <Button variant="outline" size="sm" className={className}>
      <PencilIcon className="size-4" />
      Edit
    </Button>
  )

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>{trigger || defaultTrigger}</DialogTrigger>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AgentAvatar name={agent.name} size="sm" />
            Edit Agent
          </DialogTitle>
          <DialogDescription>
            Update your agent's configuration and behavior.
          </DialogDescription>
        </DialogHeader>

        <AgentForm
          initialData={agent}
          onChange={handleFormChange}
          isEditMode={true}
        />

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => handleOpenChange(false)}
            disabled={mutation.isPending}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!isValid || mutation.isPending}
          >
            {mutation.isPending && (
              <Loader2Icon className="size-4 animate-spin" />
            )}
            Save Changes
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
