// src/components/Archetype/CreateArchetypeDialog.tsx

import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Crown, Loader2Icon, PlusIcon } from "lucide-react"
import { useState } from "react"

import type { ArchetypeCreate, ArchetypePublic } from "@/client"
import { ArchetypesService } from "@/client"
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
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"

interface CreateArchetypeDialogProps {
  /** Custom trigger element (defaults to "Create Archetype" button) */
  trigger?: React.ReactNode
  /** Callback after successful creation */
  onSuccess?: (archetype: ArchetypePublic) => void
  className?: string
}

/**
 * CreateArchetypeDialog - Dialog for creating new archetypes
 *
 * Provides a form with name and description fields.
 * Uses ArchetypesService.createArchetype for the API call.
 */
export default function CreateArchetypeDialog({
  trigger,
  onSuccess,
  className,
}: CreateArchetypeDialogProps) {
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
    mutationFn: (data: ArchetypeCreate) =>
      ArchetypesService.createArchetype({ requestBody: data }),
    onSuccess: (created) => {
      showSuccessToast(`Archetype "${created.name}" created`)
      handleOpenChange(false)
      onSuccess?.(created)
    },
    onError: (err: ApiError) => {
      const message =
        (err.body as { detail?: string })?.detail ||
        "Failed to create archetype"
      showErrorToast(message)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["archetypes"] })
    },
  })

  const handleSubmit = () => {
    if (!name.trim()) {
      showErrorToast("Archetype name is required")
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
      Create Archetype
    </Button>
  )

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>{trigger || defaultTrigger}</DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Crown className="size-5" />
            Create Archetype
          </DialogTitle>
          <DialogDescription>
            Create a new archetype to define a reusable set of traits and
            qualities that personas can inherit.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="space-y-2">
            <Label htmlFor="archetype-name">
              Name <span className="text-destructive">*</span>
            </Label>
            <Input
              id="archetype-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Creative Professional"
              maxLength={100}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="archetype-description">Description</Label>
            <Textarea
              id="archetype-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Short description of this archetype..."
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
            Create Archetype
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
