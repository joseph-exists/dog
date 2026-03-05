import { AlertCircleIcon } from "lucide-react"
import { PanelContainer } from "@/components/Page/primitives"

export function RepoCapabilityPlaceholderPanel({
  title,
  description,
  unmetRequirements,
}: {
  title: string
  description: string
  unmetRequirements: string[]
}) {
  return (
    <PanelContainer title={title} scrollable={false}>
      <div className="flex h-full flex-col items-center justify-center gap-3 p-6 text-center">
        <div className="rounded-full bg-muted p-3">
          <AlertCircleIcon className="size-6 text-muted-foreground" />
        </div>
        <div className="space-y-1">
          <div className="text-sm font-medium">{title} not yet connected</div>
          <div className="text-sm text-muted-foreground">{description}</div>
        </div>
        <div className="text-xs text-muted-foreground">
          Missing: {unmetRequirements.join(", ")}
        </div>
      </div>
    </PanelContainer>
  )
}
