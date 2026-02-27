/**
 * CanvasPanel
 *
 * Primary panel for interactive canvas collaboration.
 * Currently a placeholder for future implementation.
 *
 * @example Room panel usage
 * ```tsx
 * <CanvasPanel />
 * ```
 *
 * @example Standalone page usage
 * ```tsx
 * <CanvasPanel className="h-full" />
 * ```
 */

import { Paintbrush } from "lucide-react"
import { useEffect, useMemo, useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { PanelContainer } from "../primitives/PanelContainer"
import { PlaceholderContent } from "../primitives/PlaceholderContent"

interface CanvasPanelProps {
  /** Hide panel header */
  hideHeader?: boolean
  /** Additional className */
  className?: string
  /** Optional SVG markup to render in the panel */
  svgContent?: string | null
  canWrite?: boolean
  onRenderSvg?: (payload: {
    scriptName?: string
    title?: string
    subtitle?: string | null
    scriptInput?: Record<string, unknown>
  }) => Promise<void>
  isRendering?: boolean
  renderError?: string | null
  lastRequestId?: string | null
  lastCommitSha?: string | null
  lastScriptName?: string | null
  availableScripts?: Array<{
    name: string
    description?: string | null
    input_schema?: Record<string, unknown>
    help_text?: string | null
    kind?: string | null
    source_path?: string | null
  }>
  onRequestScriptHelp?: (scriptName: string) => Promise<string | null>
  onRequestExamplesIndex?: () => Promise<string | null>
}

export function CanvasPanel({
  hideHeader = false,
  className,
  svgContent,
  canWrite = false,
  onRenderSvg,
  isRendering = false,
  renderError = null,
  lastRequestId = null,
  lastCommitSha = null,
  lastScriptName = null,
  availableScripts = [],
  onRequestScriptHelp,
  onRequestExamplesIndex,
}: CanvasPanelProps) {
  const [scriptName, setScriptName] = useState("")
  const [title, setTitle] = useState("Tesser Render")
  const [subtitle, setSubtitle] = useState("")
  const [configJson, setConfigJson] = useState("{}")
  const [configError, setConfigError] = useState<string | null>(null)
  const [scriptHelp, setScriptHelp] = useState<string | null>(null)
  const [isLoadingHelp, setIsLoadingHelp] = useState(false)
  const [examplesIndex, setExamplesIndex] = useState<string | null>(null)
  const [isLoadingExamplesIndex, setIsLoadingExamplesIndex] = useState(false)
  const hasSvg = typeof svgContent === "string" && svgContent.trim().length > 0
  const canRender = canWrite && Boolean(onRenderSvg)
  const availableScriptNames = useMemo(
    () => availableScripts.map((script) => script.name),
    [availableScripts],
  )

  useEffect(() => {
    if (scriptName && availableScriptNames.includes(scriptName)) return
    if (availableScriptNames.length > 0) {
      setScriptName(availableScriptNames[0])
      return
    }
    setScriptName("simple_svg")
  }, [availableScriptNames, scriptName])

  const selectedScript =
    availableScripts.find((script) => script.name === scriptName) ?? null

  useEffect(() => {
    setScriptHelp(selectedScript?.help_text ?? null)
  }, [selectedScript?.help_text, scriptName])

  const handleRenderClick = async () => {
    if (!onRenderSvg || isRendering) return
    let parsedConfig: Record<string, unknown> = {}
    const trimmed = configJson.trim()
    if (trimmed.length > 0) {
      try {
        const parsed = JSON.parse(trimmed)
        if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
          parsedConfig = parsed as Record<string, unknown>
        } else {
          setConfigError("Config JSON must be an object.")
          return
        }
      } catch {
        setConfigError("Config JSON is invalid.")
        return
      }
    }
    setConfigError(null)
    await onRenderSvg({
      scriptName,
      title,
      subtitle: subtitle.trim().length > 0 ? subtitle : null,
      scriptInput: parsedConfig,
    })
  }

  const handleLoadHelp = async () => {
    if (!onRequestScriptHelp || !scriptName) return
    setIsLoadingHelp(true)
    try {
      const help = await onRequestScriptHelp(scriptName)
      setScriptHelp(help)
    } finally {
      setIsLoadingHelp(false)
    }
  }

  const handleLoadExamplesIndex = async () => {
    if (!onRequestExamplesIndex) return
    setIsLoadingExamplesIndex(true)
    try {
      const indexContent = await onRequestExamplesIndex()
      setExamplesIndex(indexContent)
    } finally {
      setIsLoadingExamplesIndex(false)
    }
  }
  const content = hasSvg ? (
    <div className="h-full w-full overflow-auto rounded border bg-background p-2">
      <div
        className="mx-auto h-full w-full max-w-full [&_svg]:h-auto [&_svg]:max-h-full [&_svg]:max-w-full"
        // Trusted internal tesser output; keep steel-thread path simple.
        dangerouslySetInnerHTML={{ __html: svgContent }}
      />
    </div>
  ) : (
    <PlaceholderContent
      icon={Paintbrush}
      title="Canvas"
      description="Interactive canvas for agent and user collaboration. Coming soon."
    />
  )

  if (hideHeader) {
    return <div className={className}>{content}</div>
  }

  return (
    <PanelContainer title="Canvas" className={className}>
      {canRender && (
        <div className="mb-3 rounded border bg-muted/20 p-2">
          <div className="grid gap-2 md:grid-cols-4">
            <Input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Render title"
            />
            <Input
              value={subtitle}
              onChange={(event) => setSubtitle(event.target.value)}
              placeholder="Subtitle (optional)"
            />
            <select
              className="h-9 rounded border border-input bg-background px-3 text-sm"
              value={scriptName}
              onChange={(event) => setScriptName(event.target.value)}
            >
              {(availableScripts.length > 0 ? availableScripts : [{ name: "simple_svg" }]).map(
                (script) => (
                  <option key={script.name} value={script.name}>
                    {script.name}
                  </option>
                ),
              )}
            </select>
            <Button onClick={() => void handleRenderClick()} disabled={isRendering}>
              {isRendering ? "Rendering..." : "Render SVG"}
            </Button>
          </div>
          {selectedScript?.description && (
            <div className="mt-2 text-xs text-muted-foreground">
              {selectedScript.description}
            </div>
          )}
          {(selectedScript?.kind || selectedScript?.source_path) && (
            <div className="mt-1 text-xs text-muted-foreground">
              {selectedScript?.kind ? `kind=${selectedScript.kind} ` : ""}
              {selectedScript?.source_path ? `path=${selectedScript.source_path}` : ""}
            </div>
          )}
          <div className="mt-2">
            <textarea
              className="min-h-20 w-full rounded border border-input bg-background px-3 py-2 font-mono text-xs"
              value={configJson}
              onChange={(event) => setConfigJson(event.target.value)}
              placeholder='{"status":"ok","entity_type":"demo","entity_id":"..."}'
            />
          </div>
          <div className="mt-2 flex items-center gap-2">
            <Button
              variant="outline"
              onClick={() => void handleLoadHelp()}
              disabled={isLoadingHelp || !onRequestScriptHelp}
            >
              {isLoadingHelp ? "Loading help..." : "Show --help"}
            </Button>
            <Button
              variant="outline"
              onClick={() => void handleLoadExamplesIndex()}
              disabled={isLoadingExamplesIndex || !onRequestExamplesIndex}
            >
              {isLoadingExamplesIndex ? "Loading index..." : "Show examples index"}
            </Button>
          </div>
          {scriptHelp && (
            <pre className="mt-2 max-h-48 overflow-auto rounded border bg-background p-2 text-xs">
              {scriptHelp}
            </pre>
          )}
          {examplesIndex && (
            <pre className="mt-2 max-h-64 overflow-auto rounded border bg-background p-2 text-xs">
              {examplesIndex}
            </pre>
          )}
          {configError && (
            <div className="mt-2 text-xs text-red-600">{configError}</div>
          )}
          {renderError && <div className="mt-2 text-xs text-red-600">{renderError}</div>}
          {!renderError && (lastRequestId || lastCommitSha || lastScriptName) && (
            <div className="mt-2 text-xs text-muted-foreground">
              {lastScriptName ? `script=${lastScriptName} ` : ""}
              {lastRequestId ? `request=${lastRequestId} ` : ""}
              {lastCommitSha ? `commit=${lastCommitSha.slice(0, 8)}` : ""}
            </div>
          )}
        </div>
      )}
      {content}
    </PanelContainer>
  )
}
