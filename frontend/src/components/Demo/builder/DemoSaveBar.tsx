import { Button } from "@/components/ui/button"
import { Loader2, Save } from "lucide-react"

interface DemoSaveBarProps {
  selectedDemoLabel: string
  isDirty: boolean
  canSave: boolean
  isSaving: boolean
  onSave: () => void
}

export function DemoSaveBar({
  selectedDemoLabel,
  isDirty,
  canSave,
  isSaving,
  onSave,
}: DemoSaveBarProps) {
  return (
    <div className="sticky bottom-4 flex items-center justify-between rounded-md border bg-background/95 backdrop-blur px-4 py-3">
      <div className="text-sm text-muted-foreground">
        {selectedDemoLabel}
        {isDirty ? " · unsaved changes" : " · saved"}
      </div>
      <Button
        type="button"
        onClick={onSave}
        disabled={!canSave || isSaving}
      >
        {isSaving
          ? <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          : <Save className="h-4 w-4 mr-2" />}
        Save Composition
      </Button>
    </div>
  )
}
