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
import { AgentsService } from "@/client/sdk.gen"
import type {
  UserAgentConfigPublic,
  AgentsUpdateAgentData,
  Type1Update,
  Type3Update,
} from "@/client/types.gen"
import AgentAvatar from "../Display/AgentAvatar"
import {
  AgentModeBadge,
  AgentProviderBadge,
  AgentScopeBadge,
  parseProviderFromModelName,
} from "../Display/AgentBadge"
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
function AgentViewContent({ agent }: { agent: UserAgentConfigPublic }) {
  const providerType = parseProviderFromModelName(agent.model_name ?? "")

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
          <span className="text-sm font-mono">{agent.model_name}</span>
        </div>
      </div>

      {/* Participation Mode */}
      <div className="space-y-1">
        <p className="text-sm font-medium text-muted-foreground">
          Participation Mode
        </p>
        <AgentModeBadge
          mode={(agent.participation_mode ?? "on_mention") as any}
        />
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
  const TYPE3_PROVIDER = "e09ade10-8563-4748-8deb-1a6c87c97134" as const
  const [isOpen, setIsOpen] = useState(false)
  const [mode, setMode] = useState<"view" | "edit">("view")
  const [formData, setFormData] = useState<AgentFormData | null>(null)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  // Fetch full agent data when dialog opens
  const { data: agent, isLoading } = useQuery({
    queryKey: ["agent", agentId],
    queryFn: () => AgentsService.getAgent({ agentId }),
    enabled: isOpen,
  })

  const handleOpenChange = (open: boolean) => {
    setIsOpen(open)
    if (!open) {
      setMode("view")
      setFormData(null)
    }
  }

  type ProviderType =
    | Type1Update["provider_type"]
    | Type3Update["provider_type"]

  const buildDiscriminatedPayload = (
    data: AgentFormData,
    agent: UserAgentConfigPublic
  ): AgentsUpdateAgentData["requestBody"] | null => {
    const providerType = (data.provider_type || agent.provider_type) as
      | ProviderType
      | undefined

    if (!providerType) {
      showErrorToast("Provider type is required")
      return null
    }

    const trimmedName = data.name.trim()
    const trimmedDescription = data.description.trim()
    const trimmedSystemPrompt = data.system_prompt.trim()
    const slug = data.slug || agent.slug || ""

    const payload: AgentsUpdateAgentData["requestBody"] = {
      name: trimmedName,
      slug,
      provider_type: providerType,
    }

    let changed =
      trimmedName !== (agent.name ?? "") ||
      slug !== (agent.slug ?? "") ||
      providerType !== (agent.provider_type as ProviderType)

    if (trimmedDescription !== (agent.description ?? "")) {
      payload.description = trimmedDescription || null
      changed = true
    }

    if (data.model_id !== (agent.model_id ?? "")) {
      payload.model_id = data.model_id || null
      changed = true
    }

    if (data.model_name !== (agent.model_name ?? "")) {
      payload.model_name = data.model_name || undefined
      payload.model = data.model_name || null
      changed = true
    }

    if (trimmedSystemPrompt !== (agent.system_prompt ?? "")) {
      payload.system_prompt = trimmedSystemPrompt || null
      changed = true
    }

    if (data.participation_mode !== (agent.participation_mode ?? "")) {
      payload.participation_mode = data.participation_mode
      changed = true
    }

    if (data.user_access_provider !== agent.user_access_provider) {
      payload.user_access_provider = data.user_access_provider ?? null
      changed = true
    }

    if (!changed) {
      showErrorToast("No changes to save")
      return null
    }

    return payload
  }

  const mutation = useMutation({
    mutationFn: (payload: AgentsUpdateAgentData["requestBody"]) =>
      AgentsService.updateAgent({
        agentId,
        requestBody: payload,
      }),
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

    const payload = buildDiscriminatedPayload(formData, agent)

    if (!payload) return

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
                <AgentAvatar name={agent.name ?? "Agent"} size="sm" />
                <span className="truncate">{agent.name ?? "Agent"}</span>
                <AgentScopeBadge
                  scope={(agent.scope ?? "system") as any}
                  className="shrink-0"
                />
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
                initialData={{
                  name: agent.name ?? "",
                  slug: agent.slug ?? "",
                  description: agent.description ?? "",
                  model_id: agent.model_id ?? "",
                  model_name: agent.model_name ?? "",
                  system_prompt: agent.system_prompt ?? "",
                  participation_mode: agent.participation_mode ?? "on_mention",
                  provider_type:
                    agent.provider_type === TYPE3_PROVIDER
                      ? TYPE3_PROVIDER
                      : undefined,
                  user_access_provider: agent.user_access_provider ?? undefined,
                }}
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
