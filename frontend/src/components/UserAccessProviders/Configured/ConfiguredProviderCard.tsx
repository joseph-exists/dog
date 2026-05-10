import {
  CheckCircle2,
  ChevronDown,
  Circle,
  Clock3,
  Pencil,
  RefreshCcw,
  Sparkles,
  Trash2,
} from "lucide-react"
import type { ReactNode } from "react"
import type {
  LLMProviderTypePublic,
  UserAccessProviderPublic,
} from "@/client/types.gen"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { ProviderStatusBadge } from "../Display"

interface ConfiguredProviderCardProps {
  provider: UserAccessProviderPublic
  providerType: LLMProviderTypePublic | null
  isActive: boolean
  isOpen: boolean
  isStale: boolean
  validationLabel: string
  baseUrlLabel: string
  onToggleOpen: () => void
  onEdit: () => void
  onManageModels: () => void
  onValidate: () => void
  onDelete: () => void
  hideValidateAction?: boolean
  children?: ReactNode
}

type LifecycleStatus = "complete" | "current" | "pending"

function LifecycleStep({
  label,
  detail,
  status,
}: {
  label: string
  detail: string
  status: LifecycleStatus
}) {
  const Icon =
    status === "complete"
      ? CheckCircle2
      : status === "current"
        ? Clock3
        : Circle

  return (
    <div className="flex min-w-0 items-start gap-2">
      <Icon
        className={cn(
          "mt-0.5 h-4 w-4 shrink-0",
          status === "complete" && "text-green-600",
          status === "current" && "text-primary",
          status === "pending" && "text-muted-foreground",
        )}
      />
      <div className="min-w-0">
        <p className="text-xs font-medium text-foreground">{label}</p>
        <p className="text-[11px] text-muted-foreground">{detail}</p>
      </div>
    </div>
  )
}

export function ConfiguredProviderCard({
  provider,
  providerType,
  isActive,
  isOpen,
  isStale,
  validationLabel,
  baseUrlLabel,
  onToggleOpen,
  onEdit,
  onManageModels,
  onValidate,
  onDelete,
  hideValidateAction = false,
  children,
}: ConfiguredProviderCardProps) {
  const modelCount = provider.available_models_cache?.length ?? 0
  const hasModelCache = modelCount > 0 || Boolean(provider.models_cached_at)
  const status = provider.is_validated
    ? "verified"
    : provider.validation_error
      ? "failed"
      : "unknown"
  const providerTypeLabel =
    providerType?.display_name || providerType?.name || "Provider"

  return (
    <div
      className={cn(
        "rounded-lg border bg-background/80 transition-colors",
        isActive && "border-primary/40 bg-primary/5",
      )}
    >
      <Button
        type="button"
        variant="ghost"
        onClick={onToggleOpen}
        className="flex h-auto w-full items-start justify-between rounded-lg px-4 py-4 text-left"
      >
        <div className="min-w-0 space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-semibold">{provider.name}</span>
            <ProviderStatusBadge status={status} />
            {provider.is_default ? (
              <Badge variant="secondary">Default</Badge>
            ) : null}
            {!provider.is_enabled ? (
              <Badge variant="outline">Disabled</Badge>
            ) : null}
            {isStale ? <Badge variant="outline">Needs refresh</Badge> : null}
          </div>
          <p className="text-xs text-muted-foreground">
            {providerTypeLabel} - {baseUrlLabel}
          </p>
          <div className="flex flex-wrap gap-2">
            <Badge variant="outline" className="text-[10px]">
              {validationLabel}
            </Badge>
            <Badge variant="outline" className="text-[10px]">
              {modelCount} cached model{modelCount === 1 ? "" : "s"}
            </Badge>
          </div>
        </div>
        <ChevronDown
          className={cn(
            "mt-1 h-4 w-4 shrink-0 transition-transform",
            isOpen && "rotate-180",
          )}
        />
      </Button>

      {isOpen ? (
        <div className="space-y-4 border-t px-4 py-4">
          {provider.description ? (
            <p className="text-sm text-muted-foreground">
              {provider.description}
            </p>
          ) : null}

          <div className="grid gap-3 rounded-lg border bg-muted/20 p-3 sm:grid-cols-4">
            <LifecycleStep
              label="Saved"
              detail="Credentials stored"
              status="complete"
            />
            <LifecycleStep
              label="Validated"
              detail={
                provider.is_validated ? validationLabel : "Run validation"
              }
              status={provider.is_validated ? "complete" : "current"}
            />
            <LifecycleStep
              label="Models fetched"
              detail={
                hasModelCache ? `${modelCount} cached` : "Fetch from provider"
              }
              status={
                hasModelCache
                  ? "complete"
                  : provider.is_validated
                    ? "current"
                    : "pending"
              }
            />
            <LifecycleStep
              label="Choose favorites"
              detail={
                hasModelCache ? "Optional model pins" : "Available after fetch"
              }
              status={hasModelCache ? "current" : "pending"}
            />
          </div>

          <div className="grid gap-3 text-xs text-muted-foreground sm:grid-cols-3">
            <div className="rounded-lg border bg-muted/20 p-3">
              <p className="font-medium text-foreground">Connection</p>
              <p className="mt-1">
                {provider.is_enabled ? "Enabled" : "Disabled"}
              </p>
            </div>
            <div className="rounded-lg border bg-muted/20 p-3">
              <p className="font-medium text-foreground">Validation</p>
              <p className="mt-1">{validationLabel}</p>
            </div>
            <div className="rounded-lg border bg-muted/20 p-3">
              <p className="font-medium text-foreground">Models</p>
              <p className="mt-1">{modelCount} cached</p>
            </div>
          </div>

          {provider.validation_error ? (
            <p className="rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2 text-xs text-destructive">
              {provider.validation_error}
            </p>
          ) : null}

          <div className="flex flex-wrap justify-end gap-2">
            <Button variant="outline" size="sm" onClick={onEdit}>
              <Pencil className="h-3.5 w-3.5" />
              Edit
            </Button>
            {!hideValidateAction ? (
              <Button variant="outline" size="sm" onClick={onValidate}>
                <RefreshCcw className="h-3.5 w-3.5" />
                Validate and fetch models
              </Button>
            ) : null}
            <Button variant="outline" size="sm" onClick={onManageModels}>
              <Sparkles className="h-3.5 w-3.5" />
              Models
            </Button>
            <Button variant="destructive" size="sm" onClick={onDelete}>
              <Trash2 className="h-3.5 w-3.5" />
              Delete
            </Button>
          </div>

          {children ? <div className="pt-1">{children}</div> : null}
        </div>
      ) : null}
    </div>
  )
}
