import { ChevronDown } from "lucide-react"
import { useState } from "react"
import type {
  LLMProviderTypePublic,
  UserAccessProviderPublic,
} from "@/client/types.gen"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { ProviderTemplateCard } from "./ProviderTemplateCard"

interface ProviderCategoryAccordionProps {
  title: string
  description: string
  providerTypes: LLMProviderTypePublic[]
  configuredProviders: UserAccessProviderPublic[]
  selectedProviderTypeId: string | null
  defaultOpen?: boolean
  onSelect: (providerType: LLMProviderTypePublic) => void
}

export function ProviderCategoryAccordion({
  title,
  description,
  providerTypes,
  configuredProviders,
  selectedProviderTypeId,
  defaultOpen = true,
  onSelect,
}: ProviderCategoryAccordionProps) {
  const [open, setOpen] = useState(defaultOpen)

  if (providerTypes.length === 0) {
    return null
  }

  return (
    <div className="rounded-xl border bg-background/70">
      <Button
        type="button"
        variant="ghost"
        onClick={() => setOpen((value) => !value)}
        className="flex h-auto w-full items-center justify-between rounded-xl px-4 py-4"
      >
        <div className="text-left">
          <div className="text-sm font-semibold">{title}</div>
          <div className="text-xs text-muted-foreground">{description}</div>
        </div>
        <div className="flex items-center gap-3">
          <span className="rounded-full bg-muted px-2.5 py-1 text-[11px] text-muted-foreground">
            {providerTypes.length}
          </span>
          <ChevronDown
            className={cn("h-4 w-4 transition-transform", open && "rotate-180")}
          />
        </div>
      </Button>

      {open ? (
        <div className="grid gap-4 border-t px-4 py-4 md:grid-cols-2 xl:grid-cols-3">
          {providerTypes.map((providerType) => (
            <ProviderTemplateCard
              key={providerType.id}
              providerType={providerType}
              isConfigured={configuredProviders.some(
                (provider) =>
                  provider.alpha_provider_type_id === providerType.id,
              )}
              isSelected={selectedProviderTypeId === providerType.id}
              onSelect={onSelect}
            />
          ))}
        </div>
      ) : null}
    </div>
  )
}
