import { CheckCircle2, FolderPlus, Pin, Plus, Sparkles } from "lucide-react"
import type {
  DetailedTestResult,
  UserAccessProviderPublic,
} from "@/client/types.gen"
import { BlockContainer } from "@/components/Page/primitives"
import { Badge } from "@/components/ui/badge"
import { QuickActionCard } from "./QuickActionCard"

interface SetupSuccessPanelProps {
  provider: UserAccessProviderPublic
  validationResult?: DetailedTestResult | null
  onBrowseModels: () => void
  onPinFavorites: () => void
  onAddAnother: () => void
  onDismiss: () => void
}

export function SetupSuccessPanel({
  provider,
  validationResult,
  onBrowseModels,
  onPinFavorites,
  onAddAnother,
  onDismiss,
}: SetupSuccessPanelProps) {
  const modelCount = validationResult?.models?.length ?? 0
  const visionCount =
    validationResult?.models?.filter((model) => model.supports_vision).length ?? 0

  return (
    <BlockContainer
      title="Provider ready"
      subtitle={`${provider.name} passed validation and is ready for model-aware workflows.`}
      variant="card"
      density="comfortable"
      metadata={
        <div className="inline-flex items-center gap-2 rounded-full border border-green-500/20 bg-green-500/10 px-3 py-1 text-xs text-green-700 dark:text-green-300">
          <CheckCircle2 className="h-3.5 w-3.5" />
          Validated
        </div>
      }
      bodyClassName="space-y-4"
    >
      {validationResult?.valid ? (
        <div className="flex flex-wrap gap-2">
          <Badge variant="secondary">{modelCount} models found</Badge>
          <Badge variant="outline">{visionCount} vision-ready</Badge>
          {validationResult.latency_ms ? (
            <Badge variant="outline">{validationResult.latency_ms} ms latency</Badge>
          ) : null}
        </div>
      ) : null}
      <div className="grid gap-3 md:grid-cols-2">
        <QuickActionCard
          title="Create agent"
          description="Jump straight into an agent configured to use this provider."
          icon={<FolderPlus className="h-5 w-5" />}
          href={`/agents/new?provider=${provider.id}`}
        />
        <QuickActionCard
          title="Browse models"
          description="Inspect the model catalog exposed by this credential set."
          icon={<Sparkles className="h-5 w-5" />}
          onClick={onBrowseModels}
        />
        <QuickActionCard
          title="Pin favorites"
          description="Mark the models your team will reach for most often."
          icon={<Pin className="h-5 w-5" />}
          onClick={onPinFavorites}
        />
        <QuickActionCard
          title="Add another provider"
          description="Return to the gallery to configure another credential."
          icon={<Plus className="h-5 w-5" />}
          onClick={onAddAnother}
        />
      </div>
      <button
        type="button"
        className="text-xs text-muted-foreground transition-colors hover:text-foreground"
        onClick={onDismiss}
      >
        Skip for now
      </button>
    </BlockContainer>
  )
}
