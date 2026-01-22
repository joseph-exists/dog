// src/components/Page/CreatePageDialog.tsx

import { useState } from "react"
import { Check, LayoutTemplate } from "lucide-react"
import { pageTemplates, getTemplatesForEntityType } from "@/components/Page/registry"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { cn } from "@/lib/utils"

interface CreatePageDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onCreatePage: (templateId: string) => Promise<void>
  isCreating: boolean
  entityType?: string
}

/**
 * CreatePageDialog - Dialog for creating a new page from a template
 *
 * Shows available templates as selectable cards.
 * Confirms selection to create the page.
 */
export function CreatePageDialog({
  open,
  onOpenChange,
  onCreatePage,
  isCreating,
  entityType,
}: CreatePageDialogProps) {
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null)

  // Get templates, optionally filtered by entity type
  const templates = entityType
    ? getTemplatesForEntityType(entityType)
    : pageTemplates

  const handleCreate = async () => {
    if (!selectedTemplateId) return
    await onCreatePage(selectedTemplateId)
    setSelectedTemplateId(null)
  }

  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      setSelectedTemplateId(null)
    }
    onOpenChange(newOpen)
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <LayoutTemplate className="h-5 w-5" />
            Create Your Page
          </DialogTitle>
          <DialogDescription>
            Choose a template to get started. You can customize it after creation.
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 py-4">
          {templates.map((template) => (
            <button
              key={template.id}
              type="button"
              onClick={() => setSelectedTemplateId(template.id)}
              className={cn(
                "relative flex flex-col p-4 rounded-lg border-2 text-left transition-all",
                "hover:border-primary/50 hover:bg-accent/50",
                selectedTemplateId === template.id
                  ? "border-primary bg-accent"
                  : "border-border"
              )}
            >
              {selectedTemplateId === template.id && (
                <div className="absolute top-2 right-2">
                  <Check className="h-4 w-4 text-primary" />
                </div>
              )}
              <h3 className="font-medium text-sm">{template.label}</h3>
              <p className="text-xs text-muted-foreground mt-1">
                {template.description}
              </p>
              <div className="mt-3 text-xs text-muted-foreground">
                {template.defaultBlocks.length} blocks
              </div>
            </button>
          ))}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => handleOpenChange(false)}
            disabled={isCreating}
          >
            Cancel
          </Button>
          <Button
            onClick={handleCreate}
            disabled={!selectedTemplateId || isCreating}
          >
            {isCreating ? "Creating..." : "Create Page"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
