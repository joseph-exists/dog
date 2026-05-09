import { ArrowUpRight, CheckCircle2, Plus } from "lucide-react"
import type { LLMProviderTypePublic } from "@/client/types.gen"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface ProviderTemplateCardProps {
  providerType: LLMProviderTypePublic
  configuredCount: number
  isSelected: boolean
  onSelect: (providerType: LLMProviderTypePublic) => void
}

const FALLBACK_ACCENTS: Record<string, string> = {
  major: "#2563eb",
  cloud: "#0f766e",
  self_hosted: "#7c3aed",
  custom: "#c2410c",
}

export function ProviderTemplateCard({
  providerType,
  configuredCount,
  isSelected,
  onSelect,
}: ProviderTemplateCardProps) {
  const accent =
    FALLBACK_ACCENTS[providerType.category ?? "custom"] ?? "#475569"
  const title = providerType.display_name || providerType.name

  return (
    <button
      type="button"
      onClick={() => onSelect(providerType)}
      className={cn(
        "group relative flex h-full flex-col overflow-hidden rounded-xl border bg-card text-left transition-all",
        "hover:-translate-y-0.5 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        isSelected && "border-transparent shadow-md ring-2 ring-ring/30",
      )}
      style={
        {
          "--provider-accent": accent,
          borderColor: isSelected ? accent : undefined,
          background:
            "linear-gradient(180deg, color-mix(in srgb, var(--provider-accent) 8%, transparent), transparent 34%)",
        } as React.CSSProperties
      }
    >
      <div className="flex items-start justify-between gap-3 border-b border-border/60 px-4 py-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span
              className="inline-flex h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: accent }}
            />
            <h4 className="text-sm font-semibold">{title}</h4>
          </div>
          <p className="text-xs text-muted-foreground">
            {providerType.details ||
              providerType.default_base_url ||
              "Template"}
          </p>
        </div>
        {configuredCount > 0 ? (
          <Badge variant="secondary" className="gap-1 whitespace-nowrap">
            <CheckCircle2 className="h-3.5 w-3.5" />
            {configuredCount} added
          </Badge>
        ) : null}
      </div>

      <div className="flex flex-1 flex-col gap-3 px-4 py-4">
        <div className="flex flex-wrap gap-2">
          <Badge variant="outline" className="capitalize">
            {(providerType.category ?? "custom").replace("_", " ")}
          </Badge>
          {providerType.validated ? (
            <Badge variant="outline">Supported</Badge>
          ) : null}
        </div>

        {providerType.default_base_url ? (
          <p className="rounded-md bg-muted/50 px-3 py-2 font-mono text-[11px] text-muted-foreground">
            {providerType.default_base_url}
          </p>
        ) : (
          <p className="text-xs text-muted-foreground">
            Use your own endpoint and adapter settings.
          </p>
        )}

        <div className="mt-auto flex items-center justify-between gap-3 pt-2">
          {providerType.docs_url ? (
            <a
              href={providerType.docs_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-xs text-muted-foreground transition-colors hover:text-foreground"
              onClick={(event) => event.stopPropagation()}
            >
              Docs
              <ArrowUpRight className="h-3.5 w-3.5" />
            </a>
          ) : (
            <span className="text-xs text-muted-foreground">
              Guided setup available
            </span>
          )}
          <Button size="sm" className="gap-1">
            <Plus className="h-3.5 w-3.5" />
            {configuredCount > 0 ? "Create another" : "Set up"}
          </Button>
        </div>
      </div>
    </button>
  )
}
