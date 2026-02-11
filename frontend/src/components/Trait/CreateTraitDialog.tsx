// src/components/Trait/CreateTraitDialog.tsx

import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Loader2Icon, PlusIcon, Sparkles } from "lucide-react"
import { useState } from "react"

import type { TraitCreate, TraitPublic } from "@/client"
import { TraitsService } from "@/client"
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
import { Textarea } from "@/components/ui/textarea"
import { showSuccessToast, showErrorToast } from "@/hooks/useCustomToast"

interface CreateTraitDialogProps {
  /** Custom trigger element (defaults to "Create Trait" button) */
  trigger?: React.ReactNode
  /** Callback after successful creation */
  onSuccess?: (trait: TraitPublic) => void
  className?: string
}

/**
 * CreateTraitDialog - Dialog for creating new traits
 *
 * Provides a form with name and description fields.
 * Uses TraitsService.createTrait for the API call.
 */
export default function CreateTraitDialog({
  trigger,
  onSuccess,
  className,
}: CreateTraitDialogProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const queryClient = useQueryClient()
  

  const handleOpenChange = (open: boolean) => {
    setIsOpen(open)
    if (!open) {
      setName("")
      setDescription("")
    }
  }

  const createMutation = useMutation({
    mutationFn: (data: TraitCreate) =>
      TraitsService.createTrait({ requestBody: data }),
    onSuccess: (created) => {
      showSuccessToast(`Trait "${created.name}" created`)
      handleOpenChange(false)
      onSuccess?.(created)
    },
    onError: (err: ApiError) => {
      const message =
        (err.body as { detail?: string })?.detail || "Failed to create trait"
      showErrorToast(message)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["traits"] })
    },
  })

  const handleSubmit = () => {
    if (!name.trim()) {
      showErrorToast("Trait name is required")
      return
    }

    createMutation.mutate({
      name: name.trim(),
      description: description.trim() || null,
    })
  }

  const isValid = name.trim().length > 0

  const defaultTrigger = (
    <Button className={className}>
      <PlusIcon className="size-4" />
      Create Trait
    </Button>
  )

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>{trigger || defaultTrigger}</DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="size-5" />
            Create Trait
          </DialogTitle>
          <DialogDescription>
            Create a new trait that can be assigned to archetypes, personas, and
            linked to qualities.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="space-y-2">
            <Label htmlFor="trait-name">
              Name <span className="text-destructive">*</span>
            </Label>
            <Input
              id="trait-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Analytical Thinking"
              maxLength={100}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="trait-description">Description</Label>
            <Textarea
              id="trait-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Short description of this trait..."
              maxLength={300}
              className="min-h-[80px]"
            />
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => handleOpenChange(false)}
            disabled={createMutation.isPending}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!isValid || createMutation.isPending}
          >
            {createMutation.isPending && (
              <Loader2Icon className="size-4 animate-spin" />
            )}
            Create Trait
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
