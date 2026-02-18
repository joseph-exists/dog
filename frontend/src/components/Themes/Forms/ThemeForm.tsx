/**
 * ThemeForm
 *
 * Form for creating and editing themes.
 * Handles page and card theme categories with live preview.
 */

import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import type { ThemeViewModel } from "@/services/themeService"

// ============================================================================
// Schema
// ============================================================================

const themeFormSchema = z.object({
  name: z.string().min(1, "Name is required").max(100),
  description: z.string().max(500).optional(),
  category: z.enum(["page", "card", "syntax", "motion"]),
  scope: z.enum(["personal", "shared"]),
  // Token fields for page/card themes
  background: z.string().optional(),
  foreground: z.string().optional(),
  card: z.string().optional(),
  cardForeground: z.string().optional(),
  border: z.string().optional(),
  muted: z.string().optional(),
  mutedForeground: z.string().optional(),
  secondary: z.string().optional(),
  secondaryForeground: z.string().optional(),
  accent: z.string().optional(),
  accentForeground: z.string().optional(),
})

export type ThemeFormData = z.infer<typeof themeFormSchema>

// ============================================================================
// Props
// ============================================================================

export interface ThemeFormProps {
  mode: "create" | "edit"
  initialData?: ThemeViewModel
  onSubmit: (data: ThemeFormData) => void
  isSubmitting?: boolean
  onCancel?: () => void
}

// ============================================================================
// Component
// ============================================================================

export function ThemeForm({
  mode,
  initialData,
  onSubmit,
  isSubmitting,
  onCancel,
}: ThemeFormProps) {
  // Extract token values from initialData
  const tokens = initialData?.tokens ?? {}

  const form = useForm<ThemeFormData>({
    resolver: zodResolver(themeFormSchema),
    defaultValues: {
      name: initialData?.name ?? "",
      description: initialData?.description ?? "",
      category: initialData?.category ?? "page",
      scope: (initialData?.scope as "personal" | "shared") ?? "personal",
      background: (tokens["--background"] as string) ?? "",
      foreground: (tokens["--foreground"] as string) ?? "",
      card: (tokens["--card"] as string) ?? "",
      cardForeground: (tokens["--card-foreground"] as string) ?? "",
      border: (tokens["--border"] as string) ?? "",
      muted: (tokens["--muted"] as string) ?? "",
      mutedForeground: (tokens["--muted-foreground"] as string) ?? "",
      secondary: (tokens["--secondary"] as string) ?? "",
      secondaryForeground: (tokens["--secondary-foreground"] as string) ?? "",
      accent: (tokens["--accent"] as string) ?? "",
      accentForeground: (tokens["--accent-foreground"] as string) ?? "",
    },
  })

  const category = form.watch("category")
  const isPageTheme = category === "page"
  const isCardTheme = category === "card"
  const showColorFields = isPageTheme || isCardTheme

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        {/* Basic Info */}
        <div className="space-y-4">
          <FormField
            control={form.control}
            name="name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Name</FormLabel>
                <FormControl>
                  <Input placeholder="My Custom Theme" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="description"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Description</FormLabel>
                <FormControl>
                  <Textarea
                    placeholder="A brief description of this theme..."
                    className="resize-none"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <div className="grid grid-cols-2 gap-4">
            <FormField
              control={form.control}
              name="category"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Category</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value}
                    disabled={mode === "edit"}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select category" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="page">Page</SelectItem>
                      <SelectItem value="card">Card</SelectItem>
                      <SelectItem value="syntax">Syntax</SelectItem>
                      <SelectItem value="motion">Motion</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormDescription>
                    {isPageTheme && "Controls page surface colors"}
                    {isCardTheme && "Controls card/panel colors"}
                    {category === "syntax" && "Code syntax highlighting"}
                    {category === "motion" && "Animation settings"}
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="scope"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Visibility</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select visibility" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="personal">Personal</SelectItem>
                      <SelectItem value="shared">Shared</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormDescription>
                    {field.value === "personal"
                      ? "Only you can see this theme"
                      : "Others can use this theme"}
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>
        </div>

        {/* Color Tokens - Page/Card themes */}
        {showColorFields && (
          <div className="space-y-4">
            <h3 className="text-sm font-medium">Color Tokens</h3>
            <p className="text-xs text-muted-foreground">
              Use oklch() format, e.g., oklch(0.15 0.03 280)
            </p>

            <div className="grid grid-cols-2 gap-4">
              {/* Background - only for page themes */}
              {isPageTheme && (
                <FormField
                  control={form.control}
                  name="background"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Background</FormLabel>
                      <FormControl>
                        <Input placeholder="oklch(0.15 0.03 280)" {...field} />
                      </FormControl>
                    </FormItem>
                  )}
                />
              )}

              <FormField
                control={form.control}
                name="foreground"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Foreground</FormLabel>
                    <FormControl>
                      <Input placeholder="oklch(0.90 0.01 280)" {...field} />
                    </FormControl>
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="card"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Card</FormLabel>
                    <FormControl>
                      <Input placeholder="oklch(0.18 0.03 280)" {...field} />
                    </FormControl>
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="cardForeground"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Card Foreground</FormLabel>
                    <FormControl>
                      <Input placeholder="oklch(0.92 0.01 280)" {...field} />
                    </FormControl>
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="border"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Border</FormLabel>
                    <FormControl>
                      <Input placeholder="oklch(0.28 0.03 280)" {...field} />
                    </FormControl>
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="muted"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Muted</FormLabel>
                    <FormControl>
                      <Input placeholder="oklch(0.22 0.03 280)" {...field} />
                    </FormControl>
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="mutedForeground"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Muted Foreground</FormLabel>
                    <FormControl>
                      <Input placeholder="oklch(0.62 0.02 280)" {...field} />
                    </FormControl>
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="accent"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Accent</FormLabel>
                    <FormControl>
                      <Input placeholder="oklch(0.30 0.04 280)" {...field} />
                    </FormControl>
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="accentForeground"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Accent Foreground</FormLabel>
                    <FormControl>
                      <Input placeholder="oklch(0.92 0.01 280)" {...field} />
                    </FormControl>
                  </FormItem>
                )}
              />
            </div>
          </div>
        )}

        {/* Syntax theme placeholder */}
        {category === "syntax" && (
          <div className="rounded-lg border border-dashed p-4 text-center text-sm text-muted-foreground">
            Syntax theme editor coming soon. For now, system themes are
            available.
          </div>
        )}

        {/* Motion theme placeholder */}
        {category === "motion" && (
          <div className="rounded-lg border border-dashed p-4 text-center text-sm text-muted-foreground">
            Motion theme editor coming soon. For now, system themes are
            available.
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-2">
          {onCancel && (
            <Button type="button" variant="outline" onClick={onCancel}>
              Cancel
            </Button>
          )}
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting
              ? "Saving..."
              : mode === "create"
                ? "Create Theme"
                : "Save Changes"}
          </Button>
        </div>
      </form>
    </Form>
  )
}
