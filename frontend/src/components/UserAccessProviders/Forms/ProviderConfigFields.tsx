import type { LLMProviderTypePublic } from "@/client/types.gen"
import {
  FormControl,
  FormDescription,
  FormItem,
  FormLabel,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"

interface ProviderConfigFieldsProps {
  providerType: LLMProviderTypePublic | null
  values: Record<string, unknown>
  onChange: (key: string, value: unknown) => void
}

type JsonSchemaProperty = {
  type?: string
  title?: string
  description?: string
  default?: unknown
}

export function ProviderConfigFields({
  providerType,
  values,
  onChange,
}: ProviderConfigFieldsProps) {
  const schema = providerType?.config_schema

  if (
    !schema ||
    typeof schema !== "object" ||
    !("properties" in schema) ||
    !schema.properties ||
    typeof schema.properties !== "object"
  ) {
    return null
  }

  const properties = Object.entries(
    schema.properties as Record<string, JsonSchemaProperty>,
  )

  if (properties.length === 0) {
    return null
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {properties.map(([key, property]) => {
        const label =
          property.title ||
          key
            .split("_")
            .map((part) => part[0]?.toUpperCase() + part.slice(1))
            .join(" ")

        if (property.type === "boolean") {
          return (
            <FormItem
              key={key}
              className="flex items-center justify-between rounded-lg border p-3 md:col-span-2"
            >
              <div className="space-y-1">
                <FormLabel>{label}</FormLabel>
                {property.description ? (
                  <FormDescription>{property.description}</FormDescription>
                ) : null}
              </div>
              <FormControl>
                <Switch
                  checked={Boolean(values[key])}
                  onCheckedChange={(checked) => onChange(key, checked)}
                />
              </FormControl>
            </FormItem>
          )
        }

        return (
          <FormItem key={key}>
            <FormLabel>{label}</FormLabel>
            <FormControl>
              <Input
                value={String(values[key] ?? property.default ?? "")}
                onChange={(event) =>
                  onChange(
                    key,
                    property.type === "number"
                      ? Number(event.target.value)
                      : event.target.value,
                  )
                }
                placeholder={label}
              />
            </FormControl>
            {property.description ? (
              <FormDescription>{property.description}</FormDescription>
            ) : null}
          </FormItem>
        )
      })}
    </div>
  )
}
