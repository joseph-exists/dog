/**
 * CreateAgentDialog Component
 *
 * Dialog for creating a new personal agent.
 * Uses AgentForm for the form fields and handles API submission.
 */

import { useMutation, useQueryClient } from "@tanstack/react-query"
import { BotIcon, Loader2Icon, PlusIcon } from "lucide-react"
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
  type CreateAgentInput,
} from "@/services/agentService"
import AgentForm, { type AgentFormData } from "./AgentForm"

interface CreateAgentDialogProps {
  /** Custom trigger element (defaults to "Create Agent" button) */
  trigger?: React.ReactNode
  /** Callback when dialog open state changes */
  onOpenChange?: (open: boolean) => void
  /** Callback when agent is created successfully */
  onSuccess?: (agent: AgentViewModel) => void
  /** Additional classes for the trigger */
  className?: string
}

export default function CreateAgentDialog({
  trigger,
  onOpenChange,
  onSuccess,
  className,
}: CreateAgentDialogProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [formData, setFormData] = useState<AgentFormData | null>(null)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const handleOpenChange = (open: boolean) => {
    setIsOpen(open)
    onOpenChange?.(open)
    if (!open) {
      // Reset form data when closing
      setFormData(null)
    }
  }

  const mutation = useMutation({
    mutationFn: (data: CreateAgentInput) => AgentService.createAgent(data),
    onSuccess: (createdAgent) => {
      showSuccessToast(`Agent "${createdAgent.name}" created successfully.`)
      handleOpenChange(false)
      onSuccess?.(createdAgent)
    },
    onError: (err: ApiError) => {
      const message =
        (err.body as { detail?: string })?.detail || "Failed to create agent"
      showErrorToast(message)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["agents"] })
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
    if (!formData.slug.trim()) {
      showErrorToast("Agent slug is required")
      return
    }

    const payload: CreateAgentInput = {
      name: formData.name.trim(),
      slug: formData.slug.trim(),
      description: formData.description.trim() || null,
      provider_config_id: formData.provider_config_id,
      model_name: formData.model_name,
      system_prompt: formData.system_prompt.trim() || null,
      participation_mode: formData.participation_mode,
      scope: "personal", // Personal agents only from this dialog
      is_enabled: true,
    }

    mutation.mutate(payload)
  }

  const isValid = formData?.name.trim() && formData?.slug.trim()

  const defaultTrigger = (
    <Button className={className}>
      <PlusIcon className="size-4" />
      Create Agent
    </Button>
  )

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>{trigger || defaultTrigger}</DialogTrigger>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <BotIcon className="size-5" />
            Create New Agent
          </DialogTitle>
          <DialogDescription>
            Create a personal AI agent with custom instructions and behavior.
          </DialogDescription>
        </DialogHeader>

        <AgentForm onChange={handleFormChange} isEditMode={false} />

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
            Create Agent
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
