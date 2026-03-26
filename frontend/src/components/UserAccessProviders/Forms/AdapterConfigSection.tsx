import { ChevronDown, Settings2 } from "lucide-react"
import { useState } from "react"
import type { UseFormReturn } from "react-hook-form"
import { Button } from "@/components/ui/button"
import {
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"

interface AdapterConfigSectionProps {
  form: UseFormReturn<any>
}

export function AdapterConfigSection({ form }: AdapterConfigSectionProps) {
  const [open, setOpen] = useState(false)

  return (
    <div className="rounded-xl border bg-muted/20">
      <Button
        type="button"
        variant="ghost"
        className="flex h-auto w-full items-center justify-between px-4 py-3"
        onClick={() => setOpen((value) => !value)}
      >
        <div className="text-left">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <Settings2 className="h-4 w-4" />
            Adapter controls
          </div>
          <p className="text-xs text-muted-foreground">
            Timeout, retry, proxy, and raw header overrides.
          </p>
        </div>
        <ChevronDown
          className={`h-4 w-4 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </Button>
      {open ? (
        <div className="grid gap-4 border-t px-4 py-4 md:grid-cols-2">
          <FormField
            control={form.control}
            name={"timeout_seconds" as never}
            render={({ field }) => (
              <FormItem>
                <FormLabel>Timeout (seconds)</FormLabel>
                <FormControl>
                  <Input
                    type="number"
                    value={String(field.value ?? 30)}
                    onChange={(event) =>
                      field.onChange(Number(event.target.value))
                    }
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name={"max_retries" as never}
            render={({ field }) => (
              <FormItem>
                <FormLabel>Max retries</FormLabel>
                <FormControl>
                  <Input
                    type="number"
                    value={String(field.value ?? 3)}
                    onChange={(event) =>
                      field.onChange(Number(event.target.value))
                    }
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name={"retry_delay_ms" as never}
            render={({ field }) => (
              <FormItem>
                <FormLabel>Retry delay (ms)</FormLabel>
                <FormControl>
                  <Input
                    type="number"
                    value={String(field.value ?? 1000)}
                    onChange={(event) =>
                      field.onChange(Number(event.target.value))
                    }
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name={"proxy_url" as never}
            render={({ field }) => (
              <FormItem>
                <FormLabel>Proxy URL</FormLabel>
                <FormControl>
                  <Input
                    value={String(field.value ?? "")}
                    onChange={field.onChange}
                    placeholder="https://proxy.internal:8080"
                  />
                </FormControl>
                <FormDescription>Optional outbound HTTP proxy.</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name={"custom_headers_json" as never}
            render={({ field }) => (
              <FormItem className="md:col-span-2">
                <FormLabel>Custom headers</FormLabel>
                <FormControl>
                  <Textarea
                    value={String(field.value ?? "{}")}
                    onChange={field.onChange}
                    className="min-h-28 font-mono text-xs"
                    placeholder='{"x-tenant-id":"team-a"}'
                  />
                </FormControl>
                <FormDescription>
                  JSON object merged into outbound request headers.
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>
      ) : null}
    </div>
  )
}
