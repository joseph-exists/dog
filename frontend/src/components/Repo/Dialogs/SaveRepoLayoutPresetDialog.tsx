import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

interface SaveRepoLayoutPresetDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description?: string
  initialLabel?: string
  initialDescription?: string
  confirmLabel?: string
  onConfirm: (input: { label: string; description: string }) => void
}

export function SaveRepoLayoutPresetDialog({
  open,
  onOpenChange,
  title,
  description,
  initialLabel = "",
  initialDescription = "",
  confirmLabel = "Save Preset",
  onConfirm,
}: SaveRepoLayoutPresetDialogProps) {
  const [label, setLabel] = useState(initialLabel)
  const [details, setDetails] = useState(initialDescription)

  useEffect(() => {
    if (!open) return
    setLabel(initialLabel)
    setDetails(initialDescription)
  }, [initialDescription, initialLabel, open])

  const trimmedLabel = label.trim()

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          {description ? (
            <DialogDescription>{description}</DialogDescription>
          ) : null}
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="repo-layout-preset-label">Preset Name</Label>
            <Input
              id="repo-layout-preset-label"
              value={label}
              onChange={(event) => setLabel(event.target.value)}
              placeholder="Browser + Viewer"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="repo-layout-preset-description">Description</Label>
            <Input
              id="repo-layout-preset-description"
              value={details}
              onChange={(event) => setDetails(event.target.value)}
              placeholder="File browsing with preview panels."
            />
          </div>
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="ghost"
            onClick={() => onOpenChange(false)}
          >
            Cancel
          </Button>
          <Button
            type="button"
            disabled={trimmedLabel.length === 0}
            onClick={() =>
              onConfirm({ label: trimmedLabel, description: details.trim() })
            }
          >
            {confirmLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
