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

import { Check, ChevronsUpDown, Loader2, Plus, Sparkles } from "lucide-react"
import { useState } from "react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Command,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import useLlmCatalog from "@/hooks/useLlmCatalog"
import { cn } from "@/lib/utils"

// can import ONLY from client sdk and client types.

interface ModelComboboxProps {
  /** Currently selected model value (e.g., "openai:gpt-4o") */
  value: string
  /** Called when selection changes */
  onChange: (value: string) => void
  /** Filter to specific provider type (hint: provider_type is not the same as user_access_provider) */
  providerType?: string
  /** Disable the combobox */
  disabled?: boolean
  /** Additional className for trigger button */
  className?: string
  /** Width of the popover */
  popoverWidth?: string
}


export default function ModelCombobox({
  value,
  onChange,
  providerType,
  placeholder = "Select a model...",
  disabled = false,
  className,
  popoverWidth = "w-[350px]",
}: ModelComboboxProps) {
  const [open, setOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const [isCreating, setIsCreating] = useState(false)
  const [newModelId, setNewModelId] = useState("")
  const [newDisplayName, setNewDisplayName] = useState("")
  const [createError, setCreateError] = useState<string | null>(null)

  // Get catalog data and createCustomModel from hook
  const {
    modelsByProvider,
    allModels,
    isLoading: catalogLoading,
    findModel,
    formatModelName,
    getProviderTypeLabel,
    createCustomModel,
    isCreatingCustomModel,
  } = useLlmCatalog()

  // Filter models by provider type if specified
  const filteredModels = providerType
    ? modelsByProvider[providerType] || []
    : allModels

  // Find selected model info
  const selectedModel = findModel(value)
  const displayValue = selectedModel?.label || formatModelName(value)

  // Check if search query matches any model
  const searchLower = searchQuery.toLowerCase()
  const hasExactMatch = filteredModels.some(
    (m) =>
      m.value.toLowerCase() === searchLower ||
      m.label.toLowerCase() === searchLower,
  )

  // Handle starting the create flow
  const handleStartCreate = () => {
    setNewModelId(searchQuery)
    setNewDisplayName(suggestDisplayName(searchQuery))
    setIsCreating(true)
  }

  // Handle creating the custom model
  const handleCreate = async () => {
    if (!newModelId.trim()) return

    const effectiveProviderType = providerType || "openai_compatible"
    setCreateError(null)

    try {
      const result = await createCustomModel({
        modelId: newModelId.trim(),
        displayName: newDisplayName.trim() || suggestDisplayName(newModelId),
        providerType: effectiveProviderType,
      })

      // Select the new model
      onChange(result.value)
      // Reset state
      setIsCreating(false)
      setNewModelId("")
      setNewDisplayName("")
      setSearchQuery("")
      setOpen(false)
    } catch (error) {
      setCreateError(
        error instanceof Error ? error.message : "Failed to create model",
      )
    }
  }

  // Handle selecting a model
  const handleSelect = (modelValue: string) => {
    onChange(modelValue)
    setOpen(false)
    setSearchQuery("")
    setIsCreating(false)
  }

  // Handle cancel create
  const handleCancelCreate = () => {
    setIsCreating(false)
    setNewModelId("")
    setNewDisplayName("")
  }

  // Group models by provider for display
  const groupedModels = providerType
    ? { [providerType]: filteredModels }
    : modelsByProvider

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
        {isCreating ? (
          /* Inline Create Form */
          <div className="p-4 space-y-4">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Sparkles className="size-4 text-primary" />
              Add Custom Model
            </div>

            <div className="space-y-3">
              <div className="space-y-1.5">
                <Label htmlFor="model-id" className="text-xs">
                  Model ID
                </Label>
                <Input
                  id="model-id"
                  value={newModelId}
                  onChange={(e) => {
                    setNewModelId(e.target.value)
                    setNewDisplayName(suggestDisplayName(e.target.value))
                  }}
                  placeholder="e.g., llama3.2:70b"
                  className="h-8"
                />
                <p className="text-xs text-muted-foreground">
                  The exact model name your provider expects
                </p>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="display-name" className="text-xs">
                  Display Name
                </Label>
                <Input
                  id="display-name"
                  value={newDisplayName}
                  onChange={(e) => setNewDisplayName(e.target.value)}
                  placeholder="e.g., Llama 3.2 70B"
                  className="h-8"
                />
                <p className="text-xs text-muted-foreground">
                  How it appears in the UI
                </p>
              </div>
            </div>

            {createError && (
              <p className="text-xs text-destructive">{createError}</p>
            )}

            <div className="flex gap-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleCancelCreate}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={handleCreate}
                disabled={!newModelId.trim() || isCreatingCustomModel}
                className="flex-1"
              >
                {isCreatingCustomModel ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  "Add Model"
                )}
              </Button>
            </div>
          </div>
        ) : (
          /* Search & Select Mode */
          <Command shouldFilter={false}>
            <CommandInput
              placeholder="Search models or type custom..."
              value={searchQuery}
              onValueChange={setSearchQuery}
            />
            <CommandList>
              {/* No results - show create option */}
              {filteredModels.filter(
                (m) =>
                  m.label.toLowerCase().includes(searchLower) ||
                  m.value.toLowerCase().includes(searchLower),
              ).length === 0 && searchQuery.length > 0 ? (
                <div className="p-2">
                  <button
                    type="button"
                    onClick={handleStartCreate}
                    className="flex w-full items-center gap-2 rounded-md px-2 py-3 text-sm hover:bg-accent transition-colors"
                  >
                    <Plus className="size-4 text-primary" />
                    <span>
                      Add "<span className="font-medium">{searchQuery}</span>"
                      as custom model
                    </span>
                  </button>
                </div>
              ) : (
                <>
                  {/* Catalog models grouped by provider */}
                  {(
                    Object.entries(groupedModels) as [
                      LLMProviderType,
                      ModelOption[],
                    ][]
                  ).map(([type, models]) => {
                    // Filter by search query
                    const filtered = models.filter(
                      (m) =>
                        m.label.toLowerCase().includes(searchLower) ||
                        m.value.toLowerCase().includes(searchLower),
                    )
                    if (filtered.length === 0) return null

                    return (
                      <CommandGroup key={type} heading={getProviderTypeLabel(type)}>
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
                  })}

                  {/* Add custom option at bottom when there's a search */}
                  {searchQuery.length > 2 && !hasExactMatch && (
                    <>
                      <CommandSeparator />
                      <div className="p-2">
                        <button
                          type="button"
                          onClick={handleStartCreate}
                          className="flex w-full items-center gap-2 rounded-md px-2 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
                        >
                          <Plus className="size-4" />
                          <span>
                            Add "
                            <span className="font-medium">{searchQuery}</span>"
                            as custom model
                          </span>
                        </button>
                      </div>
                    </>
                  )}
                </>
              )}
            </CommandList>
          </Command>
        )}
      </PopoverContent>
    </Popover>
  )
}

export { suggestDisplayName }
