import { RotateCcw } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"

interface DemoRawJsonEditorProps {
  rawJsonDraft: string
  rawJsonError?: string
  onRawJsonDraftChange: (value: string) => void
  onResetFromCurrent: () => void
  onApplyRawJson: () => void
}

export function DemoRawJsonEditor({
  rawJsonDraft,
  rawJsonError,
  onRawJsonDraftChange,
  onResetFromCurrent,
  onApplyRawJson,
}: DemoRawJsonEditorProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Raw Composition JSON</CardTitle>
        <CardDescription>
          Power-user editor for bulk edits and copy/paste between environments.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        <Textarea
          rows={16}
          value={rawJsonDraft}
          onChange={(event) => onRawJsonDraftChange(event.target.value)}
        />
        {rawJsonError && (
          <p className="text-xs text-destructive">{rawJsonError}</p>
        )}
        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="outline" onClick={onResetFromCurrent}>
            <RotateCcw className="h-4 w-4 mr-2" />
            Reset Raw JSON From Current
          </Button>
          <Button type="button" variant="outline" onClick={onApplyRawJson}>
            Apply Raw JSON To Editor
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
