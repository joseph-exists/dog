/**
 * AgentDetailDialog
 *
 * View/edit dialog for an existing agent.
 * - View mode: read-only display using Display components
 * - Edit mode: AgentForm (personal agents only)
 *
 * Owns: open/close state, view/edit toggle, update mutation, toast feedback, query invalidation.
 * Delegates: form state, validation, submit button → AgentForm.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { EyeIcon, Loader2Icon, PencilIcon } from "lucide-react"
import { useState } from "react"

import type { ApiError } from "@/client/core/ApiError"
import { AgentsService } from "@/client/sdk.gen"
import type { UserAgentConfigPublic } from "@/client/types.gen"
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
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import useAuth from "@/hooks/useAuth"

import AgentAvatar from "../Display/AgentAvatar"
import {
  AgentCoordinatorBadge,
  AgentModeBadge,
  AgentProviderBadge,
  AgentScopeBadge,
  AgentStatusBadge,
} from "../Display/AgentBadge"
import AgentForm, { type AgentFormData } from "../Forms/AgentForm"
import { isAgentScope, isParticipationMode } from "../types"
import { sparseAgentUpdate } from "../utils"

// ── View Mode ─────────────────────────────────────────────────────────────

function AgentViewContent({ agent }: { agent: UserAgentConfigPublic }) {
  const scope = isAgentScope(agent.scope) ? agent.scope : undefined
  const mode = isParticipationMode(agent.participation_mode)
    ? agent.participation_mode
    : undefined

  return (
    <div className="space-y-4">
      {/* Badges row */}
      <div className="flex flex-wrap gap-2">
        <AgentStatusBadge isEnabled={agent.is_enabled ?? true} />
        {scope && <AgentScopeBadge scope={scope} />}
        {mode && <AgentModeBadge mode={mode} />}
        {agent.is_coordinator && <AgentCoordinatorBadge />}
        {agent.provider_type && <AgentProviderBadge providerType={agent.provider_type} />}
      </div>

      {/* Description */}
      {agent.description && (
        <div className="space-y-1">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            Description
          </p>
          <p className="text-sm">{agent.description}</p>
        </div>
      )}

      {/* Model */}
      {agent.model_name && (
        <div className="space-y-1">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            Model
          </p>
          <p className="text-sm font-mono">{agent.model_name}</p>
        </div>
      )}

      {/* Slug */}
      {agent.slug && (
        <div className="space-y-1">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            Slug
          </p>
          <p className="text-sm font-mono text-muted-foreground">
            @{agent.slug}
          </p>
        </div>
      )}

      {/* System Prompt */}
      {agent.system_prompt && (
        <div className="space-y-1">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            System Prompt
          </p>
          <div className="p-3 rounded-md bg-muted text-sm whitespace-pre-wrap max-h-[200px] overflow-y-auto font-mono">
            {agent.system_prompt}
          </div>
        </div>
      )}

      {/* Settings summary */}
      <div className="space-y-1">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
          Settings
        </p>
        <div className="text-sm text-muted-foreground space-y-0.5">
          <p>
            Visible: {agent.is_visible ? "Yes" : "No"} · Clonable:{" "}
            {agent.is_clonable ? "Yes" : "No"}
          </p>
          {agent.max_tool_iterations != null && (
            <p>Max tool iterations: {agent.max_tool_iterations}</p>
          )}
          {agent.capabilities && agent.capabilities.length > 0 && (
            <p>Capabilities: {agent.capabilities.join(", ")}</p>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Main Dialog ───────────────────────────────────────────────────────────

interface AgentDetailDialogProps {
  agentId: string
  trigger?: React.ReactNode
  className?: string
}

export default function AgentDetailDialog({
  agentId,
  trigger,
  className,
}: AgentDetailDialogProps) {
  const { user } = useAuth()
  const [isOpen, setIsOpen] = useState(false)
  const [mode, setMode] = useState<"view" | "edit">("view")
  const queryClient = useQueryClient()

  const { data: agent, isLoading } = useQuery({
    queryKey: ["agent", agentId],
    queryFn: () => AgentsService.getAgent({ agentId }),
    enabled: isOpen,
  })

  const handleOpenChange = (open: boolean) => {
    setIsOpen(open)
    if (!open) setMode("view")
  }

  const mutation = useMutation({
    mutationFn: (data: AgentFormData) => {
      if (!agent) throw new Error("No agent loaded")

      const payload = sparseAgentUpdate(agent, {
        name: data.name,
        slug: data.slug,
        description: data.description || null,
        user_access_provider: data.user_access_provider ?? null,
        model: data.model ?? null,
        model_id: data.model_id ?? null,
        model_name: data.model_name,
        system_prompt: data.system_prompt || null,
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
      })

      return AgentsService.updateAgent({
        agentId,
        requestBody: payload,
      })
    },
    onSuccess: (updated) => {
      showSuccessToast(`Agent "${updated.name}" updated.`)
      setMode("view")
    },
    onError: (err: ApiError) => {
      const detail = (err.body as { detail?: string })?.detail
      showErrorToast(detail || "Failed to update agent.")
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["agents"] })
      queryClient.invalidateQueries({ queryKey: ["agent", agentId] })
    },
  })

  const handleSubmit = async (data: AgentFormData) => {
    mutation.mutate(data)
  }

  const isPersonal = agent?.scope === "personal"
  const canEdit = Boolean(isPersonal || user?.is_superuser)

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        {trigger ?? (
          <Button variant="ghost" size="icon" className={className}>
            <EyeIcon className="size-4" />
          </Button>
        )}
      </DialogTrigger>
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
              </DialogTitle>
              <DialogDescription>
                {mode === "view"
                  ? "Agent configuration details."
                  : "Update this agent's configuration."}
              </DialogDescription>
            </DialogHeader>

            {mode === "view" ? (
              <AgentViewContent agent={agent} />
            ) : (
              <AgentForm
                mode="edit"
                defaultValues={agent}
                onSubmit={handleSubmit}
                isSubmitting={mutation.isPending}
              />
            )}

            {/* View-mode footer with edit/close buttons.
                Edit mode footer is inside AgentForm (its own submit button). */}
            {mode === "view" && (
              <DialogFooter>
                {canEdit && (
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
              </DialogFooter>
            )}
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
