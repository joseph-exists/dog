import type { LLMProviderTypePublic, UserAccessProviderPublic } from "@/client/types.gen"
import { BlockContainer } from "@/components/Page/primitives"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { ProviderCategoryAccordion } from "./ProviderCategoryAccordion"

interface ProviderTemplateGalleryProps {
  providerTypes: LLMProviderTypePublic[]
  configuredProviders: UserAccessProviderPublic[]
  selectedProviderTypeId: string | null
  powerUserMode: boolean
  onPowerUserModeChange: (value: boolean) => void
  onSelect: (providerType: LLMProviderTypePublic) => void
}

const CATEGORY_META: Record<string, { title: string; description: string }> = {
  major: {
    title: "Major providers",
    description: "Fast-start templates for the most common hosted APIs.",
  },
  cloud: {
    title: "Cloud platforms",
    description: "Managed enterprise endpoints with extra deployment fields.",
  },
  self_hosted: {
    title: "Self-hosted",
    description: "Endpoints you run or manage yourself.",
  },
  custom: {
    title: "Custom adapters",
    description: "Raw adapter access for compatible or niche providers.",
  },
}

export function ProviderTemplateGallery({
  providerTypes,
  configuredProviders,
  selectedProviderTypeId,
  powerUserMode,
  onPowerUserModeChange,
  onSelect,
}: ProviderTemplateGalleryProps) {
  const grouped = providerTypes.reduce<Record<string, LLMProviderTypePublic[]>>(
    (accumulator, providerType) => {
      const category = providerType.category ?? "custom"
      accumulator[category] ??= []
      accumulator[category].push(providerType)
      return accumulator
    },
    {},
  )

  return (
    <BlockContainer
      title="Provider templates"
      subtitle="Start from a curated template, then expand into adapter controls only when you need them."
      variant="card"
      density="comfortable"
      headerActions={
        <div className="flex items-center gap-3 rounded-full border bg-background px-3 py-1.5">
          <div className="text-right">
            <p className="text-xs font-medium">Power user mode</p>
            <p className="text-[11px] text-muted-foreground">
              Skip templates, edit raw settings
            </p>
          </div>
          <Switch
            checked={powerUserMode}
            onCheckedChange={onPowerUserModeChange}
            aria-label="Toggle power user mode"
          />
        </div>
      }
      toolbar={
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="secondary">{providerTypes.length} templates</Badge>
          <Badge variant="outline">
            {configuredProviders.length} configured provider
            {configuredProviders.length === 1 ? "" : "s"}
          </Badge>
        </div>
      }
      bodyClassName="space-y-4"
    >
      {Object.entries(CATEGORY_META).map(([category, meta]) => (
        <ProviderCategoryAccordion
          key={category}
          title={meta.title}
          description={meta.description}
          providerTypes={(grouped[category] ?? []).sort(
            (a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0),
          )}
          configuredProviders={configuredProviders}
          selectedProviderTypeId={selectedProviderTypeId}
          onSelect={onSelect}
        />
      ))}
    </BlockContainer>
  )
}
