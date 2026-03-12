import { Check, ChevronsUpDown } from "lucide-react"
import { useState } from "react"

import { cn } from "@/lib/utils"
import { Button } from "./button"
import {
  Command,
  CommandEmpty,
  CommandInput,
  CommandItem,
  CommandList,
} from "./command"
import { Popover, PopoverContent, PopoverTrigger } from "./popover"

export interface EntityComboboxOption {
  value: string
  label: string
  subtitle?: string
  keywords?: string[]
}

interface EntityComboboxProps {
  value: string
  onChange: (value: string) => void
  options: EntityComboboxOption[]
  placeholder: string
  searchPlaceholder: string
  emptyMessage: string
  disabled?: boolean
  className?: string
}

export function EntityCombobox({
  value,
  onChange,
  options,
  placeholder,
  searchPlaceholder,
  emptyMessage,
  disabled = false,
  className,
}: EntityComboboxProps) {
  const [open, setOpen] = useState(false)
  const selected = options.find((option) => option.value === value) ?? null

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          disabled={disabled}
          className={cn("w-full justify-between", className)}
        >
          <span className={cn("truncate", !selected && "text-muted-foreground")}>
            {selected?.label ?? placeholder}
          </span>
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[360px] p-0" align="start">
        <Command>
          <CommandInput placeholder={searchPlaceholder} />
          <CommandList>
            <CommandEmpty>{emptyMessage}</CommandEmpty>
            {options.map((option) => (
              <CommandItem
                key={option.value}
                value={[option.label, option.subtitle, option.value, ...(option.keywords ?? [])]
                  .filter(Boolean)
                  .join(" ")}
                onSelect={() => {
                  onChange(option.value)
                  setOpen(false)
                }}
                className="flex items-start justify-between gap-3"
              >
                <div className="min-w-0">
                  <div className="truncate font-medium">{option.label}</div>
                  {option.subtitle ? (
                    <div className="truncate text-xs text-muted-foreground">
                      {option.subtitle}
                    </div>
                  ) : null}
                </div>
                <Check
                  className={cn(
                    "mt-0.5 h-4 w-4 shrink-0",
                    value === option.value ? "opacity-100" : "opacity-0",
                  )}
                />
              </CommandItem>
            ))}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}
