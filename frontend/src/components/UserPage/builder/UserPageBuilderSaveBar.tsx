import { Loader2, Save } from "lucide-react"

import { Button } from "@/components/ui/button"

interface UserPageBuilderSaveBarProps {
  label: string
  isDirty: boolean
  isSaving: boolean
  canSave: boolean
  statusNote?: string
  onSave: () => void
}

export function UserPageBuilderSaveBar({
  label,
  isDirty,
  isSaving,
  canSave,
  statusNote,
  onSave,
}: UserPageBuilderSaveBarProps) {
  return (
    <div className="sticky bottom-4 flex items-center justify-between rounded-md border bg-background/95 px-4 py-3 backdrop-blur">
      <div className="space-y-1">
        <div className="text-sm text-muted-foreground">
          {label}
          {isDirty ? " · unsaved changes" : " · saved"}
        </div>
        {statusNote ? (
          <div className="text-xs text-muted-foreground">{statusNote}</div>
        ) : null}
      </div>
      <Button onClick={onSave} disabled={!canSave || isSaving}>
        {isSaving ? (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        ) : (
          <Save className="mr-2 h-4 w-4" />
        )}
        Save User Page
      </Button>
    </div>
  )
}
