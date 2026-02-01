/**
 * AgentCloneButton Component
 *
 * Allows users to clone a system agent as a personal agent for customization.
 * Opens a dialog to confirm name/slug before creating the copy.
 */

import { useMutation, useQueryClient } from "@tanstack/react-query"
import { CopyIcon, Loader2Icon } from "lucide-react"
import { useEffect, useState } from "react"

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
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import useCustomToast from "@/hooks/useCustomToast"
import {
  AgentsService,
} from "@/client"

interface AgentCloneButtonProps {
  /** The agent to clone */
  agent: AgentViewModel
  /** Callback when clone succeeds */
  onSuccess?: (newAgent: AgentViewModel) => void
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
  const [newSlug, setNewSlug] = useState("")
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const handleOpenChange = (open: boolean) => {
    setIsOpen(open)
    if (open) {
      setNewName(`${agent.name} (Copy)`)
      setNewSlug("")
    }
  }

  // Auto-generate slug from backend when dialog opens
  useEffect(() => {
    if (!isOpen || newSlug) return

    AgentsService.generateSlug()
      .then((generatedSlug) => setNewSlug(generatedSlug))
      .catch(() => setNewSlug(`${agent.slug}-copy`))
  }, [isOpen, newSlug, agent.slug])

  const mutation = useMutation({
    mutationFn: () => {
      const payload:  = {
        name: newName.trim(),
        slug: newSlug.trim(),
        description: agent.description,
        model_name: agent.model_name,
        system_prompt: agent.system_prompt,
        participation_mode: agent.participation_mode,
        scope: "personal",
        is_enabled: true,
        provider_type: "empty",
        // (don't copy user access source provider as it may not be accessible to the cloning user)
        user_access_provider: null,
      }
      return AgentsService.createAgent(payload)
    },
    onSuccess: (clonedAgent) => {
      showSuccessToast(`Cloned as "${clonedAgent.name}"`)
      setIsOpen(false)
      onSuccess?.(clonedAgent)
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
          <DialogTitle>Frends Copyings</DialogTitle>
          <DialogDescription>
            make your own friend of "{agent.name}" 
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="clone-name">New Name</Label>
            <Input
              id="clone-name"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Fart"
            />
          </div>
          <div className="space-y-2">
            <Label>Slug</Label>
            <p className="text-sm font-mono text-muted-foreground px-3 py-2 rounded-md bg-muted">
              {newSlug ? `@${newSlug}` : "Generating..."}
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
