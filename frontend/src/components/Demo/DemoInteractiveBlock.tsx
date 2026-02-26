import { Send } from "lucide-react"
import type { ReactNode } from "react"
import { useMemo, useRef, useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import {
  buildClickPromptDispatchMessage,
  CLICK_PROMPT_DISPATCH_KIND,
  type DemoInteractionSourceBlock,
  extractSourceTextFromClick,
  parseClickPromptDispatchConfig,
} from "./demoInteractionHandlers"

export interface DemoInteractiveDispatchRequest {
  message: string
  interactionKind: string
  targetPanelId: string | null
  enforceRegisteredReceiver: boolean
}

interface DemoInteractiveBlockProps {
  block: DemoInteractionSourceBlock & { config_json?: unknown }
  children: ReactNode
  onDispatchInteraction: (request: DemoInteractiveDispatchRequest) => void
}

export function DemoInteractiveBlock({
  block,
  children,
  onDispatchInteraction,
}: DemoInteractiveBlockProps) {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [messageDraft, setMessageDraft] = useState("")
  const [selectedSource, setSelectedSource] = useState<string | null>(null)
  const rootRef = useRef<HTMLDivElement | null>(null)
  const modalRef = useRef<HTMLDivElement | null>(null)
  const config = useMemo(
    () => parseClickPromptDispatchConfig(block.config_json),
    [block.config_json],
  )

  if (!config || !config.enabled) {
    return children
  }

  return (
    <div
      ref={rootRef}
      className="relative"
      onClick={(event) => {
        if (!rootRef.current) return
        if (modalRef.current?.contains(event.target as Node)) {
          return
        }
        const source = extractSourceTextFromClick({
          root: rootRef.current,
          target: event.target,
          selector: config.trigger.selector,
          maxChars: config.trigger.maxSourceChars,
        })
        if (!source) return
        setSelectedSource(source)
        setIsModalOpen(true)
      }}
    >
      {children}

      {isModalOpen && (
        <div ref={modalRef} className="mt-2 rounded-md border bg-card p-3">
          <div className="space-y-1">
            <p className="text-sm font-medium">{config.modal.title}</p>
            <p className="text-xs text-muted-foreground">
              {config.modal.helperText}
            </p>
          </div>

          {selectedSource && (
            <pre className="mt-2 max-h-40 overflow-auto rounded border bg-muted/40 p-2 text-xs">
              {selectedSource}
            </pre>
          )}

          <div className="mt-3 space-y-2">
            {config.modal.multiline ? (
              <Textarea
                rows={4}
                maxLength={config.modal.maxMessageChars}
                value={messageDraft}
                placeholder={config.modal.placeholder}
                onChange={(event) => setMessageDraft(event.target.value)}
              />
            ) : (
              <Input
                maxLength={config.modal.maxMessageChars}
                value={messageDraft}
                placeholder={config.modal.placeholder}
                onChange={(event) => setMessageDraft(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key !== "Enter") return
                  event.preventDefault()
                  const trimmed = messageDraft.trim()
                  if (!trimmed) return
                  onDispatchInteraction({
                    message: buildClickPromptDispatchMessage({
                      block,
                      config,
                      selectedSource,
                      userMessage: trimmed,
                    }),
                    interactionKind: CLICK_PROMPT_DISPATCH_KIND,
                    targetPanelId: config.dispatch.targetPanelId,
                    enforceRegisteredReceiver:
                      config.dispatch.enforceRegisteredReceiver,
                  })
                  setMessageDraft("")
                  setSelectedSource(null)
                  setIsModalOpen(false)
                }}
              />
            )}

            <div className="flex items-center gap-2">
              <Button
                type="button"
                size="sm"
                disabled={messageDraft.trim().length === 0}
                onClick={() => {
                  const trimmed = messageDraft.trim()
                  if (!trimmed) return
                  onDispatchInteraction({
                    message: buildClickPromptDispatchMessage({
                      block,
                      config,
                      selectedSource,
                      userMessage: trimmed,
                    }),
                    interactionKind: CLICK_PROMPT_DISPATCH_KIND,
                    targetPanelId: config.dispatch.targetPanelId,
                    enforceRegisteredReceiver:
                      config.dispatch.enforceRegisteredReceiver,
                  })
                  setMessageDraft("")
                  setSelectedSource(null)
                  setIsModalOpen(false)
                }}
              >
                <Send className="mr-1 h-3.5 w-3.5" />
                {config.modal.submitLabel}
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  setMessageDraft("")
                  setSelectedSource(null)
                  setIsModalOpen(false)
                }}
              >
                {config.modal.cancelLabel}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
