import { useQuery } from "@tanstack/react-query"
import { Check, ChevronsUpDown, Loader2 } from "lucide-react"
import { useDeferredValue, useState } from "react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Command,
  CommandEmpty,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { cn } from "@/lib/utils"
import {
  UserPersonaDiscoveryService,
  type DiscoverableUserPersona,
} from "@/services/userPersonaDiscoveryService"

interface DiscoverUserPersonaComboboxProps {
  value: string
  onChange: (value: string) => void
  onPersonaSelected?: (persona: DiscoverableUserPersona | null) => void
  placeholder?: string
  disabled?: boolean
  excludeCurrentUser?: boolean
}

function getPersonaLabel(persona: DiscoverableUserPersona) {
  return persona.nickname?.trim() || persona.name
}

export function DiscoverUserPersonaCombobox({
  value,
  onChange,
  onPersonaSelected,
  placeholder = "Search published collaborator personas",
  disabled = false,
  excludeCurrentUser = true,
}: DiscoverUserPersonaComboboxProps) {
  const [open, setOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const deferredQuery = useDeferredValue(searchQuery)

  const resultsQuery = useQuery({
    queryKey: ["user-personas", "discoverable", deferredQuery, excludeCurrentUser],
    queryFn: () =>
      UserPersonaDiscoveryService.search(deferredQuery, {
        limit: 12,
        excludeCurrentUser,
      }),
    enabled: deferredQuery.trim().length >= 2,
  })

  const options = resultsQuery.data ?? []
  const selectedPersona = options.find((persona) => persona.id === value) ?? null

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          disabled={disabled}
          className="w-full justify-between"
        >
          <span className={cn("truncate", !value && "text-muted-foreground")}>
            {selectedPersona
              ? `${getPersonaLabel(selectedPersona)} · ${selectedPersona.ownerDisplayName}`
              : value
                ? value
                : placeholder}
          </span>
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[420px] p-0" align="start">
        <Command shouldFilter={false}>
          <CommandInput
            placeholder="Search published personas..."
            value={searchQuery}
            onValueChange={setSearchQuery}
          />
          <CommandList>
            {resultsQuery.isLoading ? (
              <div className="flex items-center gap-2 px-3 py-4 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Searching personas...
              </div>
            ) : deferredQuery.trim().length < 2 ? (
              <CommandEmpty>Type at least 2 characters to search.</CommandEmpty>
            ) : options.length === 0 ? (
              <CommandEmpty>No published personas matched this search.</CommandEmpty>
            ) : (
              options.map((persona) => (
                <CommandItem
                  key={persona.id}
                  value={[
                    persona.id,
                    persona.personaId,
                    persona.name,
                    persona.nickname ?? "",
                    persona.ownerDisplayName,
                    persona.shortBio ?? "",
                  ].join(" ")}
                  onSelect={() => {
                    onChange(persona.id)
                    onPersonaSelected?.(persona)
                    setOpen(false)
                  }}
                  className="flex items-start justify-between gap-3"
                >
                  <div className="min-w-0 space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="truncate font-medium">
                        {getPersonaLabel(persona)}
                      </span>
                      {persona.isPrimary ? (
                        <Badge variant="secondary" className="text-[10px]">
                          Primary
                        </Badge>
                      ) : null}
                    </div>
                    <div className="truncate text-xs text-muted-foreground">
                      {persona.name} · {persona.ownerDisplayName}
                    </div>
                    {persona.shortBio ? (
                      <div className="line-clamp-2 text-xs text-muted-foreground">
                        {persona.shortBio}
                      </div>
                    ) : null}
                  </div>
                  <Check
                    className={cn(
                      "mt-0.5 h-4 w-4 shrink-0",
                      value === persona.id ? "opacity-100" : "opacity-0",
                    )}
                  />
                </CommandItem>
              ))
            )}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}
