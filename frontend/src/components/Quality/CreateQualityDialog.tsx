// src/components/Quality/CreateQualityDialog.tsx

import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Gem, Loader2Icon, PlusIcon } from "lucide-react"
import { useState } from "react"

import type { QualityCreate, QualityPublic } from "@/client"
import { QualitiesService } from "@/client"
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
import useCustomToast from "@/hooks/useCustomToast"

interface CreateQualityDialogProps {
  /** Custom trigger element (defaults to "Create Quality" button) */
  trigger?: React.ReactNode
  /** Callback after successful creation */
  onSuccess?: (quality: QualityPublic) => void
  className?: string
}

/**
 * CreateQualityDialog - Dialog for creating new qualities
 *
 * Provides a form with name and description fields.
 * Uses QualitiesService.createQuality for the API call.
 */
export default function CreateQualityDialog({
  trigger,
  onSuccess,
  className,
}: CreateQualityDialogProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const handleOpenChange = (open: boolean) => {
    setIsOpen(open)
    if (!open) {
      setName("")
      setDescription("")
    }
  }

  const createMutation = useMutation({
    mutationFn: (data: QualityCreate) =>
      QualitiesService.createQuality({ requestBody: data }),
    onSuccess: (created) => {
      showSuccessToast(`Quality "${created.name}" created`)
      handleOpenChange(false)
      onSuccess?.(created)
    },
    onError: (err: ApiError) => {
      const message =
        (err.body as { detail?: string })?.detail ||
        "Failed to create quality"
      showErrorToast(message)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["qualities"] })
    },
  })

  const handleSubmit = () => {
    if (!name.trim()) {
      showErrorToast("Quality name is required")
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
      Create Quality
    </Button>
  )

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>{trigger || defaultTrigger}</DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Gem className="size-5" />
            Create Quality
          </DialogTitle>
          <DialogDescription>
            Create a new quality that can be assigned to archetypes, personas,
            and linked to traits.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="space-y-2">
            <Label htmlFor="quality-name">
              Name <span className="text-destructive">*</span>
            </Label>
            <Input
              id="quality-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Empathy"
              maxLength={100}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="quality-description">Description</Label>
            <Textarea
              id="quality-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Short description of this quality..."
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
            Create Quality
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
