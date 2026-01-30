/**
 * AgentDetailDialog Component
 *
 * Unified dialog for viewing and editing agent details.
 * - View mode: Read-only display of all agent fields
 * - Edit mode: Switches to AgentForm for inline editing (personal agents only)
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { EyeIcon, Loader2Icon, PencilIcon } from "lucide-react"
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
import AgentAvatar from "../Display/AgentAvatar"
import {
  AgentModeBadge,
  AgentProviderBadge,
  AgentScopeBadge,
  parseProviderFromModelName,
} from "./AgentBadge"
import AgentForm, { type AgentFormData } from "../Forms/AgentForm"

interface AgentDetailDialogProps {
  /** Agent ID to display */
  agentId: string
  /** Custom trigger element */
  trigger?: React.ReactNode
  /** Additional classes for the trigger */
  className?: string
}

/** Read-only view of agent details */
function AgentViewContent({ agent }: { agent: AgentViewModel }) {
  const providerType = parseProviderFromModelName(agent.model_name)

  return (
    <div className="space-y-4">
      {/* Description */}
      {agent.description && (
        <div className="space-y-1">
          <p className="text-sm font-medium text-muted-foreground">
            Description
          </p>
          <p className="text-sm">{agent.description}</p>
        </div>
      )}

      {/* Model & Provider */}
      <div className="space-y-1">
        <p className="text-sm font-medium text-muted-foreground">Model</p>
        <div className="flex items-center gap-2">
          {providerType && <AgentProviderBadge providerType={providerType} />}
          <span className="text-sm font-mono">{agent.display_model}</span>
        </div>
      </div>

      {/* Participation Mode */}
      <div className="space-y-1">
        <p className="text-sm font-medium text-muted-foreground">
          Participation Mode
        </p>
        <AgentModeBadge mode={agent.participation_mode} />
      </div>

      {/* Slug */}
      <div className="space-y-1">
        <p className="text-sm font-medium text-muted-foreground">Slug</p>
        <p className="text-sm font-mono text-muted-foreground">@{agent.slug}</p>
      </div>

      {/* System Prompt */}
      {agent.system_prompt && (
        <div className="space-y-1">
          <p className="text-sm font-medium text-muted-foreground">
            System Prompt
          </p>
          <div className="p-3 rounded-md bg-muted text-sm whitespace-pre-wrap max-h-[200px] overflow-y-auto font-mono">
            {agent.system_prompt}
          </div>
        </div>
      )}
    </div>
  )
}

export default function AgentDetailDialog({
  agentId,
  trigger,
  className,
}: AgentDetailDialogProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [mode, setMode] = useState<"view" | "edit">("view")
  const [formData, setFormData] = useState<AgentFormData | null>(null)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  // Fetch full agent data when dialog opens
  const { data: agent, isLoading } = useQuery({
    queryKey: ["agent", agentId],
    queryFn: () => AgentService.getAgent(agentId),
    enabled: isOpen,
  })

  const handleOpenChange = (open: boolean) => {
    setIsOpen(open)
    if (!open) {
      setMode("view")
      setFormData(null)
    }
  }

  const mutation = useMutation({
    mutationFn: (data: UpdateAgentInput) =>
      AgentService.updateAgent(agentId, data),
    onSuccess: (updatedAgent) => {
      showSuccessToast(`Agent "${updatedAgent.name}" updated successfully.`)
      setMode("view")
      setFormData(null)
    },
    onError: (err: ApiError) => {
      const message =
        (err.body as { detail?: string })?.detail || "Failed to update agent"
      showErrorToast(message)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["agents"] })
      queryClient.invalidateQueries({ queryKey: ["agent", agentId] })
    },
  })

  const handleFormChange = useCallback((data: AgentFormData) => {
    setFormData(data)
  }, [])

  const handleSubmit = () => {
    if (!formData || !agent) return

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

    if (Object.keys(payload).length === 0) {
      showErrorToast("No changes to save")
      return
    }

    mutation.mutate(payload)
  }

  const isPersonal = agent?.scope === "personal"
  const isValid = formData?.name.trim()

  const defaultTrigger = (
    <Button variant="ghost" size="icon" className={className}>
      <EyeIcon className="size-4" />
    </Button>
  )

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>{trigger || defaultTrigger}</DialogTrigger>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        {isLoading || !agent ? (
          <div className="flex items-center justify-center py-8">
            <Loader2Icon className="size-6 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <AgentAvatar name={agent.name} size="sm" />
                <span className="truncate">{agent.name}</span>
                <AgentScopeBadge scope={agent.scope} className="shrink-0" />
              </DialogTitle>
              <DialogDescription>
                {mode === "view"
                  ? "Agent configuration and details"
                  : "Update your agent's configuration and behavior."}
              </DialogDescription>
            </DialogHeader>

            {mode === "view" ? (
              <AgentViewContent agent={agent} />
            ) : (
              <AgentForm
                initialData={agent}
                onChange={handleFormChange}
                isEditMode={true}
              />
            )}

            <DialogFooter>
              {mode === "view" ? (
                <>
                  {isPersonal && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setMode("edit")}
                    >
                      <PencilIcon className="size-4" />
                      Edit
                    </Button>
                  )}
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handleOpenChange(false)}
                  >
                    Close
                  </Button>
                </>
              ) : (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setMode("view")
                      setFormData(null)
                    }}
                    disabled={mutation.isPending}
                  >
                    Cancel
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleSubmit}
                    disabled={!isValid || mutation.isPending}
                  >
                    {mutation.isPending && (
                      <Loader2Icon className="size-4 animate-spin" />
                    )}
                    Save Changes
                  </Button>
                </>
              )}
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
