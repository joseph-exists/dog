/**
 * AgentCloneButton Component
 *
 * Allows users to clone a system agent as a personal agent for customization.
 * Opens a dialog to confirm name/slug before creating the copy.
 */

import { useMutation, useQueryClient } from "@tanstack/react-query"
import { CopyIcon, Loader2Icon } from "lucide-react"
import { useState } from "react"
import type { ApiError } from "@/client/core/ApiError"
import { AgentsService } from "@/client/sdk.gen"
import type { AgentConfigPublic } from "@/client/types.gen"
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
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import useCustomToast from "@/hooks/useCustomToast"
import { generateSlug } from "./AgentForm"

interface AgentCloneButtonProps {
  /** The agent to clone */
  agent: AgentConfigPublic
  /** Callback when clone succeeds */
  onSuccess?: (newAgent: AgentConfigPublic) => void
  /** Button variant */
  variant?: "default" | "outline" | "ghost"
  /** Button size */
  size?: "default" | "sm" | "icon"
  /** Additional classes */
  className?: string
}

export default function AgentCloneButton({
  agent,
  onSuccess,
  variant = "outline",
  size = "sm",
  className,
}: AgentCloneButtonProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [newName, setNewName] = useState(`${agent.name} (Copy)`)
  const [newSlug, setNewSlug] = useState(`${agent.slug}-copy`)
  const [slugManuallyEdited, setSlugManuallyEdited] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  // Auto-generate slug from name unless manually edited
  const handleNameChange = (name: string) => {
    setNewName(name)
    if (!slugManuallyEdited) {
      setNewSlug(generateSlug(name))
    }
  }

  const handleSlugChange = (slug: string) => {
    setSlugManuallyEdited(true)
    setNewSlug(slug.toLowerCase().replace(/[^a-z0-9-]/g, ""))
  }

  const resetForm = () => {
    setNewName(`${agent.name} (Copy)`)
    setNewSlug(`${agent.slug}-copy`)
    setSlugManuallyEdited(false)
  }

  const handleOpenChange = (open: boolean) => {
    setIsOpen(open)
    if (open) {
      resetForm()
    }
  }

  const mutation = useMutation({
    mutationFn: () =>
      AgentsService.createAgent({
        requestBody: {
          name: newName.trim(),
          slug: newSlug.trim(),
          description: agent.description,
          model_name: agent.model_name,
          system_prompt: agent.system_prompt,
          participation_mode: agent.participation_mode,
          scope: "personal",
          is_enabled: true,
        },
      }),
    onSuccess: (newAgent) => {
      showSuccessToast(`Cloned as "${newAgent.name}"`)
      setIsOpen(false)
      onSuccess?.(newAgent)
    },
    onError: (err: ApiError) => {
      const message =
        (err.body as { detail?: string })?.detail || "Failed to clone agent"
      showErrorToast(message)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["agents"] })
    },
  })

  const isValid = newName.trim() && newSlug.trim()

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button variant={variant} size={size} className={className}>
          <CopyIcon className="size-4" />
          {size !== "icon" && <span>Clone</span>}
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Clone Agent</DialogTitle>
          <DialogDescription>
            Create a personal copy of "{agent.name}" that you can customize.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="clone-name">New Name</Label>
            <Input
              id="clone-name"
              value={newName}
              onChange={(e) => handleNameChange(e.target.value)}
              placeholder="My Custom Agent"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="clone-slug">New Slug</Label>
            <Input
              id="clone-slug"
              value={newSlug}
              onChange={(e) => handleSlugChange(e.target.value)}
              placeholder="my-custom-agent"
            />
            <p className="text-xs text-muted-foreground">
              Unique identifier for your cloned agent
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => setIsOpen(false)}
            disabled={mutation.isPending}
          >
            Cancel
          </Button>
          <Button
            onClick={() => mutation.mutate()}
            disabled={!isValid || mutation.isPending}
          >
            {mutation.isPending && (
              <Loader2Icon className="size-4 animate-spin" />
            )}
            Clone Agent
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
