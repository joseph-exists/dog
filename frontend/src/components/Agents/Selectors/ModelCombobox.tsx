/**
 * ModelCombobox Component
 *
 * A searchable combobox for selecting LLM models with support for:
 * - Catalog models grouped by provider
 * - User's custom models
 * - Inline creation of new custom models
 * - Smart display name suggestions
 * - Recently used models (future)
 */

import { useQuery } from "@tanstack/react-query"
import { Check, ChevronsUpDown, Loader2 } from "lucide-react"
import { useMemo, useState } from "react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Command,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { LlmCatalogService } from "@/client/sdk.gen"
import type { LLMModelPublic } from "@/client/types.gen"
import { cn } from "@/lib/utils"

// can import ONLY from client sdk and client types.

interface ModelComboboxProps {
  /** Currently selected model value (e.g., "openai:gpt-4o") */
  value: string
  /** Called when selection changes */
  onChange: (value: string) => void
  /** Called with full model on selection */
  onModelSelected?: (model: LLMModelPublic | null) => void
  /** Filter to specific provider type (hint: provider_type is not the same as user_access_provider) */
  providerType?: string
  /** Disable the combobox */
  disabled?: boolean
  /** Additional className for trigger button */
  className?: string
  /** Width of the popover */
  popoverWidth?: string
  /** Placeholder text */
  placeholder?: string
}


export default function ModelCombobox({
  value,
  onChange,
  onModelSelected,
  providerType,
  placeholder = "Select a model...",
  disabled = false,
  className,
  popoverWidth = "w-[350px]",
}: ModelComboboxProps) {
  const [open, setOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const { data, isLoading: catalogLoading } = useQuery({
    queryKey: ["llm-catalog", "models"],
    queryFn: () => LlmCatalogService.listModels(),
  })

  const models: LLMModelPublic[] = data?.data ?? []

  const options = useMemo(() => {
    return models
      .filter((m) =>
        providerType ? m.primary_provider_type_id === providerType : true,
      )
      .map((m) => ({
        value: (m as any).id ?? m.model_id, // backend UUID id is what agent endpoints expect
        label: m.display_name ?? m.model_id,
        description: m.description ?? undefined,
        providerType: m.primary_provider_type_id,
        isDefault: !!m.is_default,
        friendlyId: m.model_id,
        raw: m,
      }))
  }, [models, providerType])

  const grouped = useMemo(() => {
    const groups: Record<string, typeof options> = {}
    options.forEach((opt) => {
      const key = opt.providerType || "unknown"
      if (!groups[key]) groups[key] = []
      groups[key].push(opt)
    })
    return groups
  }, [options])

  const selectedModel =
    options.find((m) => m.value === value) ??
    (value ? { value, label: value, providerType: "", isDefault: false } : null)
  const displayValue = selectedModel?.label ?? placeholder

  // Handle selecting a model
  const handleSelect = (modelValue: string) => {
    onChange(modelValue)
    const selected =
      models.find(
        (m) => (m as any).id === modelValue || m.model_id === modelValue,
      ) ?? null
    onModelSelected?.(selected)
    setOpen(false)
    setSearchQuery("")
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          disabled={disabled || catalogLoading}
          className={cn("w-full justify-between", className)}
        >
          {catalogLoading ? (
            <span className="flex items-center gap-2">
              <Loader2 className="size-4 animate-spin" />
              Loading models...
            </span>
          ) : (
            <>
              <span className="flex items-center gap-2 truncate">
                {value ? (
                  displayValue
                ) : (
                  <span className="text-muted-foreground">{placeholder}</span>
                )}
                {value && selectedModel?.isDefault && (
                  <Badge variant="secondary" className="text-xs">
                    Default
                  </Badge>
                )}
              </span>
              <ChevronsUpDown className="ml-2 size-4 shrink-0 opacity-50" />
            </>
          )}
        </Button>
      </PopoverTrigger>

      <PopoverContent className={cn("p-0", popoverWidth)} align="start">
        <Command shouldFilter={false}>
          <CommandInput
            placeholder="Search models..."
            value={searchQuery}
            onValueChange={setSearchQuery}
          />
          <CommandList>
            {(Object.entries(grouped) as [string, typeof options][]).map(
              ([type, modelsForType]) => {
                const filtered = modelsForType.filter(
                  (m) =>
                    m.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
                    m.value.toLowerCase().includes(searchQuery.toLowerCase()),
                )
                if (filtered.length === 0) return null

                return (
                  <CommandGroup key={type} heading={type}>
                    {filtered.map((model) => (
                      <CommandItem
                        key={model.value}
                        value={model.value}
                        onSelect={() => handleSelect(model.value)}
                        className="flex items-center justify-between"
                      >
                        <div className="flex flex-col">
                          <span className="flex items-center gap-2">
                            {model.label}
                            {model.isDefault && (
                              <Badge
                                variant="outline"
                                className="text-[10px] px-1 py-0"
                              >
                                Default
                              </Badge>
                            )}
                          </span>
                          {model.description && (
                            <span className="text-xs text-muted-foreground">
                              {model.description}
                            </span>
                          )}
                        </div>
                        <Check
                          className={cn(
                            "size-4 shrink-0",
                            value === model.value
                              ? "opacity-100"
                              : "opacity-0",
                          )}
                        />
                      </CommandItem>
                    ))}
                  </CommandGroup>
                )
              },
            )}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}
