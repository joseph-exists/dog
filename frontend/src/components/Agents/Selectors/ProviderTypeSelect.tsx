import { useMemo } from "react"
import { useQuery } from "@tanstack/react-query"

import { LlmProvidersService } from "@/client/sdk.gen"
import type { LLMProviderTypePublic } from "@/client/types.gen"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { cn } from "@/lib/utils"

type ProviderTypeSelectProps = {
  value: string | null
  onChange: (id: string, providerType: LLMProviderTypePublic | null) => void
  disabled?: boolean
  placeholder?: string
  className?: string
}

export function ProviderTypeSelect({
  value,
  onChange,
  disabled = false,
  placeholder = "Select a provider type...",
  className,
}: ProviderTypeSelectProps) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["llm-provider-type-list"],
    queryFn: () => LlmProvidersService.getProviderTypeList(),
    staleTime: 5 * 60 * 1000,
  })

  const providerTypes = useMemo(
    () =>
      [...(data?.data ?? [])].sort((a, b) =>
        a.name.localeCompare(b.name, undefined, { sensitivity: "base" }),
      ),
    [data],
  )

  const handleChange = (newValue: string) => {
    const selected = providerTypes.find((p) => p.id === newValue) ?? null
    onChange(newValue, selected)
  }

  return (
    <Select
      value={value ?? undefined}
      onValueChange={handleChange}
      disabled={disabled || isLoading || isError}
    >
      <SelectTrigger className={cn("w-full", className)}>
        <SelectValue
          placeholder={
            isLoading
              ? "Loading provider types..."
              : isError
                ? "Unable to load provider types"
                : placeholder
          }
        />
      </SelectTrigger>
      <SelectContent>
        {providerTypes.map((providerType) => (
          <SelectItem key={providerType.id} value={providerType.id}>
            <div className="flex flex-col">
              <span className="font-medium">{providerType.name}</span>
              {providerType.details && (
                <span className="text-xs text-muted-foreground">
                  {providerType.details}
                </span>
              )}
            </div>
          </SelectItem>
        ))}
        {!isLoading && providerTypes.length === 0 && (
          <div className="px-2 py-1.5 text-xs text-muted-foreground">
            No provider types available
          </div>
        )}
      </SelectContent>
    </Select>
  )
}
