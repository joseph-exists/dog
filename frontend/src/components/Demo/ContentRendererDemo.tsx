/**
 * ContentRendererDemo - Interactive showcase of ContentRenderer
 *
 * Features:
 * - Format selector tabs
 * - Variant picker
 * - Live preview with actual ContentRenderer
 * - Theme toggle (dark/light affects code themes)
 * - Safe mode toggle
 */
import { useState } from "react"
import {
  ContentRenderer,
  type Content,
  type ContentVariant,
  type ContentFormat,
} from "@/components/Page/primitives/ContentRenderer"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  allExamples,
  variantDemos,
} from "./ContentRendererExamples"

const FORMAT_TABS: Array<{ value: ContentFormat; label: string }> = [
  { value: "text", label: "Text" },
  { value: "markdown", label: "Markdown" },
  { value: "code", label: "Code" },
  { value: "html", label: "HTML" },
  { value: "json", label: "JSON" },
  { value: "svg", label: "SVG" },
  { value: "image", label: "Image" },
  { value: "mdx", label: "MDX" },
]

export function ContentRendererDemo() {
  const [activeFormat, setActiveFormat] = useState<ContentFormat>("text")
  const [selectedVariant, setSelectedVariant] = useState<ContentVariant>("card")
  const [safeMode, setSafeMode] = useState(true)
  const [exampleIndex, setExampleIndex] = useState(0)

  // Get examples for current format
  const examples = allExamples[activeFormat as keyof typeof allExamples] || []
  const currentExample = examples[exampleIndex] as Content | undefined

  // Create content with selected variant override
  const displayContent: Content | null = currentExample
    ? {
        ...currentExample,
        metadata: {
          ...currentExample.metadata,
          variant: selectedVariant,
        },
      }
    : null

  return (
    <div className="container mx-auto py-8 space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">ContentRenderer Demo</h1>
        <p className="text-muted-foreground">
          Interactive showcase of all ContentRenderer formats and variants.
        </p>
      </div>

      {/* Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Controls</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-6">
          {/* Variant Selector */}
          <div className="space-y-2">
            <Label>Variant</Label>
            <Select
              value={selectedVariant}
              onValueChange={(v) => setSelectedVariant(v as ContentVariant)}
            >
              <SelectTrigger className="w-[180px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {/* removed description parameter due to compile time error */}
                {variantDemos.map(({ variant}) => (
                  <SelectItem key={variant} value={variant}>
                    {variant}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Example Selector */}
          <div className="space-y-2">
            <Label>Example</Label>
            <Select
              value={String(exampleIndex)}
              onValueChange={(v) => setExampleIndex(Number(v))}
            >
              <SelectTrigger className="w-[120px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {examples.map((_, i) => (
                  <SelectItem key={i} value={String(i)}>
                    Example {i + 1}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Safe Mode Toggle */}
          <div className="flex items-center space-x-2">
            <Switch
              id="safe-mode"
              checked={safeMode}
              onCheckedChange={setSafeMode}
            />
            <Label htmlFor="safe-mode">Safe Mode</Label>
          </div>
        </CardContent>
      </Card>

      {/* Format Tabs */}
      <Tabs
        value={activeFormat}
        onValueChange={(v) => {
          setActiveFormat(v as ContentFormat)
          setExampleIndex(0)
        }}
      >
        <TabsList className="flex-wrap h-auto">
          {FORMAT_TABS.map(({ value, label }) => (
            <TabsTrigger key={value} value={value}>
              {label}
            </TabsTrigger>
          ))}
        </TabsList>

        {FORMAT_TABS.map(({ value }) => (
          <TabsContent key={value} value={value} className="mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Preview */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">Preview</CardTitle>
                    <Badge variant="outline">{selectedVariant}</Badge>
                  </div>
                </CardHeader>
                <CardContent
                  className={
                    selectedVariant === "background"
                      ? "relative min-h-[200px]"
                      : ""
                  }
                >
                  {displayContent ? (
                    <ContentRenderer
                      content={displayContent}
                      safeMode={safeMode}
                    />
                  ) : (
                    <p className="text-muted-foreground">
                      No examples for this format.
                    </p>
                  )}
                </CardContent>
              </Card>

              {/* Source */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Source</CardTitle>
                </CardHeader>
                <CardContent>
                  <pre className="bg-muted p-4 rounded-md overflow-auto text-xs font-mono max-h-[400px]">
                    {displayContent
                      ? JSON.stringify(displayContent, null, 2)
                      : "null"}
                  </pre>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        ))}
      </Tabs>

      {/* Variant Gallery */}
      <Card>
        <CardHeader>
          <CardTitle>All Variants Gallery</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {variantDemos.map(({ variant, description }) => (
            <div key={variant} className="border rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Badge>{variant}</Badge>
                <span className="text-sm text-muted-foreground">
                  {description}
                </span>
              </div>
              <div
                className={
                  variant === "background"
                    ? "relative h-24 border rounded"
                    : ""
                }
              >
                {currentExample && (
                  <ContentRenderer
                    content={{
                      ...currentExample,
                      metadata: {
                        ...currentExample.metadata,
                        variant,
                      },
                    }}
                    safeMode={safeMode}
                  />
                )}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}