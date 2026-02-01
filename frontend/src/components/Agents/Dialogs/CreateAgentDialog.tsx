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
import { AgentsService } from "@/client/sdk.gen"
import type {
  UserAgentConfigCreate,
  UserAgentConfigPublic,
} from "@/client/types.gen"
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
import AgentForm, { type AgentFormData } from "../Forms/AgentForm"
import { validateAgentFormData } from "../utils/agentValidation"


interface CreateAgentDialogProps {
  /** Custom trigger element (defaults to "Create Agent" button) */
  trigger?: React.ReactNode
  /** Callback when dialog open state changes */
  onOpenChange?: (open: boolean) => void
  /** Callback when agent is created successfully */
  onSuccess?: (agent: UserAgentConfigPublic) => void
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
    mutationFn: (data: UserAgentConfigCreate) =>
      AgentsService.createAgent({ requestBody: data }),
    onSuccess: (createdAgent) => {
      showSuccessToast(`Agent "${createdAgent.name}" created successfully.`)
      handleOpenChange(false)
      onSuccess?.(createdAgent)
    },
    onError: (err: ApiError) => {
      const message =
        (err.body as { detail?: string })?.detail || "aw. you bonzered that one, mckraclin."
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

    // Validate form data
    const validation = validateAgentFormData(formData)
    if (!validation.isValid) {
      validation.errors.forEach((error) => showErrorToast(error))
      return
    }

    // Show warnings (non-blocking)
    validation.warnings.forEach((warning) => {
      console.warn("Agent creation warning:", warning)
    })

    const payload: UserAgentConfigCreate = {
      name: formData.name.trim(),
      slug: formData.slug.trim(),
      description: formData.description.trim() || null,
      provider_type_id: formData.provider_type_id,
      model_name: formData.model_name || undefined,
      user_access_provider: formData.user_access_provider ?? undefined,
      system_prompt: formData.system_prompt.trim() || undefined,
      participation_mode: formData.participation_mode || undefined,
      scope: "personal",
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
            CreateAgentDialog - make you an agent, bud.
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
              <Loader2Icon className="size-22 animate-spin" />
            )}
            Create Agent
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
