/**
 * CreateAgentDialog
 *
 * Thin dialog shell around AgentForm for creating new agents.
 * Owns: open/close state, create mutation, toast feedback, query invalidation.
 * Delegates: form state, validation, submit button → AgentForm.
 */

import { useMutation, useQueryClient } from "@tanstack/react-query"
import { BotIcon, PlusIcon } from "lucide-react"
import { useState } from "react"

import type { ApiError } from "@/client/core/ApiError"
import { AgentsService } from "@/client/sdk.gen"
import type {
  AgentsCreateAgentData,
  UserAgentConfigPublic,
} from "@/client/types.gen"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import AgentForm, { type AgentFormData } from "../Forms/AgentForm"

interface CreateAgentDialogProps {
  trigger?: React.ReactNode
  onOpenChange?: (open: boolean) => void
  onSuccess?: (agent: UserAgentConfigPublic) => void
  className?: string
}

export default function CreateAgentDialog({
  trigger,
  onOpenChange,
  onSuccess,
  className,
}: CreateAgentDialogProps) {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()

  const handleOpenChange = (open: boolean) => {
    setIsOpen(open)
    onOpenChange?.(open)
  }

  const mutation = useMutation({
    mutationFn: (payload: AgentsCreateAgentData["requestBody"]) =>
      AgentsService.createAgent({ requestBody: payload }),
    onSuccess: (created) => {
      showSuccessToast(`Agent "${created.name}" created.`)
      handleOpenChange(false)
      onSuccess?.(created)
    },
    onError: (err: ApiError) => {
      const detail = (err.body as { detail?: string })?.detail
      showErrorToast(detail || "Failed to create agent.")
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["agents"] })
    },
  })

  const handleSubmit = async (data: AgentFormData) => {
    type ProviderType = AgentsCreateAgentData["requestBody"]["provider_type"]

    const payload: AgentsCreateAgentData["requestBody"] = {
      name: data.name,
      slug: data.slug,
      description: data.description || "",
      provider_type: data.provider_type as ProviderType,
      user_access_provider: data.user_access_provider ?? null,
      model: data.model ?? null,
      model_id: data.model_id ?? null,
      model_name: data.model_name,
      system_prompt: data.system_prompt || "",
      custom_system_prompt: data.custom_system_prompt ?? null,
      instructions: data.instructions ?? null,
      participation_mode: data.participation_mode,
      scope: data.scope,
      is_enabled: data.is_enabled,
      is_clonable: data.is_clonable,
      is_visible: data.is_visible,
      is_coordinator: data.is_coordinator,
      max_tool_iterations: data.max_tool_iterations,
      capabilities: data.capabilities,
      tool_config: data.tool_config ?? null,
      deps_config: data.deps_config ?? null,
      agent_metadata: data.agent_metadata ?? null,
    }

    mutation.mutate(payload)
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        {trigger ?? (
          <Button className={className}>
            <PlusIcon className="size-4" />
            Create Agent
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <BotIcon className="size-5" />
            Create New Agent
          </DialogTitle>
          <DialogDescription>
            Configure a new personal agent.
          </DialogDescription>
        </DialogHeader>

        <AgentForm
          mode="create"
          onSubmit={handleSubmit}
          isSubmitting={mutation.isPending}
        />
      </DialogContent>
    </Dialog>
  )
}
