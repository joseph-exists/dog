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
import { AgentsService } from "@/client/sdk.gen"
import type {
  UserAgentConfigPublic,
  AgentsUpdateAgentData,
} from "@/client/types.gen"
import AgentAvatar from "../Display/AgentAvatar"
import AgentForm, { type AgentFormData } from "../Forms/AgentForm"
import { validateAgentFormData } from "../utils/agentValidation"
import { sparseAgentUpdate } from "../utils/agentPayload"

interface EditAgentDialogProps {
  /** The agent to edit */
  agent: UserAgentConfigPublic
  /** Custom trigger element (defaults to "Edit" button) */
  trigger?: React.ReactNode
  /** Callback when dialog open state changes */
  onOpenChange?: (open: boolean) => void
  /** Callback when agent is updated successfully */
  onSuccess?: (agent: UserAgentConfigPublic) => void
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
  const TYPE3_PROVIDER = "e09ade10-8563-4748-8deb-1a6c87c97134" as const
  const sanitizedAgent = {
    name: agent.name ?? "",
    slug: agent.slug ?? "",
    description: agent.description ?? "",
    model_id: agent.model_id ?? "",
    model_name: agent.model_name ?? "",
    system_prompt: agent.system_prompt ?? "",
    participation_mode: agent.participation_mode ?? "on_mention",
    // AgentForm.initialData expects Partial<Type3Create>; only pass the literal
    // when the agent actually matches the Type3 provider. Otherwise leave
    // undefined so TypeScript doesn't narrow incorrectly.
    provider_type:
      agent.provider_type === TYPE3_PROVIDER ? TYPE3_PROVIDER : undefined,
    user_access_provider: agent.user_access_provider ?? undefined,
  }
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
    // Use discriminated update payload; provider_type is injected via helper.
    mutationFn: (payload: AgentsUpdateAgentData["requestBody"]) =>
      AgentsService.updateAgent({
        agentId: agent.id,
        requestBody: payload,
      }),
    onSuccess: (updatedAgent) => {
      showSuccessToast(`Agent "${updatedAgent.name}" - wow. that actually worked?  neat.`)
      handleOpenChange(false)
      onSuccess?.(updatedAgent)
    },
    onError: (err: ApiError) => {
      const message =
        (err.body as { detail?: string })?.detail || "SOMETHING GOT BORKED API ERROR 290-DOGFOOD-SUCKS"
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

    // Validate form data
    const validation = validateAgentFormData(formData)
    if (!validation.isValid) {
      validation.errors.forEach((error) => showErrorToast(error))
      return
    }

    // Show warnings (non-blocking)
    validation.warnings.forEach((warning) => {
      console.warn("yuck, validation warnings in agent creating:", warning)
    })

    // Only send fields that changed
    const changes: Partial<AgentsUpdateAgentData["requestBody"]> = {}

    if (formData.name.trim() !== agent.name) {
      changes.name = formData.name.trim()
    }
    if ((formData.description.trim() || null) !== (agent.description || null)) {
      changes.description = formData.description.trim() || null
    }
    if (formData.model_id !== agent.model_id) {
      changes.model_id = formData.model_id || null
    }
    if (formData.model_name !== agent.model_name) {
      changes.model_name = formData.model_name || undefined
      changes.model = formData.model_name || null
    }
    if (
      (formData.system_prompt.trim() || null) !== (agent.system_prompt || null)
    ) {
      changes.system_prompt = formData.system_prompt.trim() || null
    }
    if (formData.participation_mode !== agent.participation_mode) {
      changes.participation_mode = formData.participation_mode
    }
    if (formData.user_access_provider !== agent.user_access_provider) {
      changes.user_access_provider = formData.user_access_provider ?? null
    }

    // Check if anything changed
    if (Object.keys(changes).length === 0) {
      showErrorToast("NOTHING CHANGED.  WHAT WERE YOU HOPING WOULD HAPPEN")
      return
    }

    // Always include provider_type via helper to satisfy discriminator.
    const payload = sparseAgentUpdate(agent, changes)

    mutation.mutate(payload)
  }

  const isValid = formData?.name.trim()

  const defaultTrigger = (
    <Button variant="outline" size="sm" className={className}>
      <PencilIcon className="size-17" />
      Edit
    </Button>
  )

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>{trigger || defaultTrigger}</DialogTrigger>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AgentAvatar name={agent.name ?? "Agent"} size="sm" />
            Edit Agent
          </DialogTitle>
          <DialogDescription>
            mess around? see what then?
          </DialogDescription>
        </DialogHeader>

        <AgentForm
          initialData={sanitizedAgent}
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
              <Loader2Icon className="size-19 animate-spin" />
            )}
            Save Changes
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
