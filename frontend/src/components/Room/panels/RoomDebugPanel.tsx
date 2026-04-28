/**
 * RoomDebugPanel - Debug sidebar for room/agent debugging
 *
 * This file exports two components:
 * - RoomDebugPanelContent: The inner content (collapsible sections)
 * - RoomDebugPanel: The outer wrapper with aside styling (legacy)
 *
 * Features:
 * - Shows messages active for agent context
 * - Displays current streaming state
 * - Shows connection status
 * - Collapsible sections matching StoryPreview pattern
 *
 * @see Room/panels/DebugPanel.tsx for the new panel wrapper
 */

import {
  AlertTriangle,
  Bot,
  Bug,
  Check,
  ChevronDown,
  ChevronUp,
  Clock,
  Code,
  Copy,
  Database,
  Eye,
  FileJson,
  Hash,
  MessageSquare,
  RefreshCw,
  Trash2,
  Wifi,
  WifiOff,
} from "lucide-react"
import { useEffect, useMemo, useState } from "react"
import type {
  AgentInvocationPublic,
  AgentInvocationSummaryPublic,
} from "@/client"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import {
  useAgentInvocationDetail,
  useAgentInvocations,
} from "@/hooks/useAgentInvocations"
import type {
  MessageViewModel,
  ParticipantViewModel,
} from "@/services/roomService"

type JsonRecord = Record<string, unknown>

function isRecord(value: unknown): value is JsonRecord {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value)
}

function formatDateTime(value: string | null | undefined): string {
  if (!value) return "pending"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  })
}

function formatDuration(
  startedAt: string,
  completedAt: string | null | undefined,
): string {
  if (!completedAt) return "running"
  const start = new Date(startedAt).getTime()
  const end = new Date(completedAt).getTime()
  if (Number.isNaN(start) || Number.isNaN(end)) return "unknown"
  const ms = Math.max(0, end - start)
  return ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s`
}

function shortId(value: string | null | undefined): string {
  if (!value) return "none"
  return value.length > 12 ? `${value.slice(0, 8)}...${value.slice(-4)}` : value
}

function storyNodeTitle(
  invocation: AgentInvocationSummaryPublic | AgentInvocationPublic | null,
): string | null {
  const storyRuntime = invocation?.story_runtime_json
  if (!isRecord(storyRuntime)) return null
  const title = storyRuntime.current_node_title
  return typeof title === "string" && title.trim() ? title : null
}

function getExtraContexts(
  invocation: AgentInvocationPublic | null,
): JsonRecord[] {
  const context = invocation?.room_context_json
  if (!isRecord(context) || !Array.isArray(context.extra_contexts)) return []
  return context.extra_contexts.filter(isRecord)
}

function countRepoContexts(invocation: AgentInvocationPublic | null): number {
  return getExtraContexts(invocation).filter((item) => {
    const contextType =
      typeof item.context_type === "string" ? item.context_type : ""
    const source = typeof item.source === "string" ? item.source : ""
    return /repo|file|git/i.test(`${contextType} ${source}`)
  }).length
}

function jsonText(value: unknown): string {
  if (typeof value === "string") return value
  return JSON.stringify(value ?? null, null, 2)
}

export interface RoomDebugPanelContentProps {
  roomId?: string
  messages: MessageViewModel[]
  streamingMessage: { agent_name: string; content: string } | null
  isConnected: boolean
  activeAgents: ParticipantViewModel[]
  /** Whether internal agent messages are visible in the message list. */
  showInternalMessages: boolean
  /** Toggle internal message visibility in the message list. */
  onToggleInternalMessages: (enabled: boolean) => void
  /** Current non-null repo file selections by selection key. */
  selectedRepoFiles?: Array<{ selectionKey: string; path: string }>
  /** Repo files currently attached to room context. */
  repoContextFiles?: Array<{
    contextId: string
    repoId: string
    repoSlug: string | null
    path: string
    ref: string
    source: string
    sizeBytes: number | null
    isTruncated: boolean
    payload: Record<string, unknown>
  }>
  /** Whether current user can remove room context items. */
  canManageRoomContext?: boolean
  /** Remove a repo context file by context id. */
  onRemoveRepoContextFile?: (contextId: string) => Promise<void>
}

/**
 * Inner content of the debug panel - collapsible sections
 * Can be used standalone or wrapped by different containers
 */
export function RoomDebugPanelContent({
  roomId: roomIdProp,
  messages,
  streamingMessage,
  isConnected,
  activeAgents,
  showInternalMessages,
  onToggleInternalMessages,
  selectedRepoFiles = [],
  repoContextFiles = [],
  canManageRoomContext = false,
  onRemoveRepoContextFile,
}: RoomDebugPanelContentProps) {
  const [expandedSections, setExpandedSections] = useState({
    apiPayload: false,
    invocations: true,
    context: true,
    streaming: true,
    agents: true,
    repoFiles: true,
    recent: false,
  })

  const [copiedPayload, setCopiedPayload] = useState(false)
  const [selectedInvocationId, setSelectedInvocationId] = useState<
    string | null
  >(null)
  const [copiedInvocationTarget, setCopiedInvocationTarget] = useState<
    string | null
  >(null)
  const [removingContextIds, setRemovingContextIds] = useState<
    Record<string, boolean>
  >({})
  const [copiedContextIds, setCopiedContextIds] = useState<
    Record<string, boolean>
  >({})

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }))
  }

  // Get messages that are active for context (what agents see)
  const contextMessages = messages.filter((m) => m.active_for_context)

  // Get the most recent messages (last 5)
  const recentMessages = messages.slice(-5).reverse()

  // Get the most recent user message (likely what triggered agent response)
  const lastUserMessage = [...messages]
    .reverse()
    .find((m) => m.sender_type === "user")

  // Build API payload preview (approximates what backend sends to agent)
  const apiPayload = useMemo(() => {
    // Format context messages as they would appear in an API call
    const formattedMessages = contextMessages.map((msg) => ({
      role: msg.sender_type !== "user" ? "assistant" : "user",
      content: msg.content,
      name: msg.sender_name,
      // Include metadata that might be relevant
      ...(msg.is_pinned && { pinned: true }),
    }))

    return {
      messages: formattedMessages,
      metadata: {
        room_id: messages[0]?.room_id || "unknown",
        context_count: contextMessages.length,
        total_messages: messages.length,
      },
    }
  }, [contextMessages, messages])

  const roomId = roomIdProp ?? messages[0]?.room_id ?? null
  const invocationsQuery = useAgentInvocations({
    roomId,
    limit: 20,
    live: Boolean(streamingMessage),
  })
  const invocations = invocationsQuery.data?.data ?? []
  const selectedInvocationSummary =
    invocations.find((item) => item.id === selectedInvocationId) ??
    invocations[0] ??
    null
  const detailQuery = useAgentInvocationDetail({
    roomId,
    invocationId: selectedInvocationSummary?.id,
  })
  const selectedInvocation = detailQuery.data ?? null
  const selectedStoryNode =
    storyNodeTitle(selectedInvocation) ??
    storyNodeTitle(selectedInvocationSummary)
  const selectedRepoContextCount = countRepoContexts(selectedInvocation)
  const selectedExtraContextCount = getExtraContexts(selectedInvocation).length

  const selectedPathSet = useMemo(
    () => new Set(selectedRepoFiles.map((item) => item.path)),
    [selectedRepoFiles],
  )

  useEffect(() => {
    if (!selectedInvocationId && invocations.length > 0) {
      setSelectedInvocationId(invocations[0].id)
      return
    }
    if (
      selectedInvocationId &&
      invocations.length > 0 &&
      !invocations.some((item) => item.id === selectedInvocationId)
    ) {
      setSelectedInvocationId(invocations[0].id)
    }
  }, [invocations, selectedInvocationId])

  const handleCopyPayload = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(apiPayload, null, 2))
      setCopiedPayload(true)
      setTimeout(() => setCopiedPayload(false), 2000)
    } catch (err) {
      console.error("Failed to copy:", err)
    }
  }

  const handleCopyInvocation = async (target: string, value: unknown) => {
    try {
      await navigator.clipboard.writeText(jsonText(value))
      setCopiedInvocationTarget(target)
      setTimeout(() => setCopiedInvocationTarget(null), 1600)
    } catch (err) {
      console.error("Failed to copy invocation data:", err)
    }
  }

  return (
    <div className="space-y-4">
      {/* Developer Mode */}
      <div className="flex items-center justify-between gap-2 text-xs rounded-md border border-border p-2">
        <div>
          <p className="text-xs font-medium">Dev Mode</p>
          <p className="text-[10px] text-muted-foreground">
            Show internal agent-to-agent messages
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Switch
            id="internal-messages"
            checked={showInternalMessages}
            onCheckedChange={onToggleInternalMessages}
          />
          <Label htmlFor="internal-messages" className="text-[10px]">
            Internal
          </Label>
        </div>
      </div>

      {/* Connection Status */}
      <div className="flex items-center gap-2 text-xs">
        {isConnected ? (
          <>
            <Wifi className="h-4 w-4 text-green-500" />
            <span className="text-green-600 dark:text-green-400">
              WebSocket Connected
            </span>
          </>
        ) : (
          <>
            <WifiOff className="h-4 w-4 text-amber-500" />
            <span className="text-amber-600 dark:text-amber-400">
              WebSocket Disconnected
            </span>
          </>
        )}
      </div>

      {/* Exact Backend Invocation Snapshots */}
      <Collapsible
        open={expandedSections.invocations}
        onOpenChange={() => toggleSection("invocations")}
      >
        <CollapsibleTrigger asChild>
          <Button variant="ghost" size="sm" className="w-full justify-between">
            <span className="flex items-center gap-2">
              <Database className="h-4 w-4" />
              Agent Invocations ({invocations.length})
              {invocations.some((item) => item.completed_at === null) ? (
                <Badge variant="default" className="animate-pulse text-[10px]">
                  LIVE
                </Badge>
              ) : null}
            </span>
            {expandedSections.invocations ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <div className="bg-muted rounded-md p-3 mt-2 text-xs space-y-3">
            <div className="flex items-center justify-between gap-2">
              <div>
                <p className="text-muted-foreground text-[10px] uppercase">
                  Exact backend snapshots
                </p>
                <p className="text-[10px] text-muted-foreground">
                  Stored prompt and context at model invocation time
                </p>
              </div>
              <Button
                size="sm"
                variant="ghost"
                className="h-7 px-2"
                disabled={!roomId || invocationsQuery.isFetching}
                onClick={() => invocationsQuery.refetch()}
                title="Refresh invocation history"
              >
                <RefreshCw
                  className={`h-3 w-3 ${
                    invocationsQuery.isFetching ? "animate-spin" : ""
                  }`}
                />
              </Button>
            </div>

            {!roomId ? (
              <p className="text-amber-600 dark:text-amber-400">
                Waiting for a room id before loading invocation records.
              </p>
            ) : invocationsQuery.isError ? (
              <div className="flex items-start gap-2 text-amber-600 dark:text-amber-400">
                <AlertTriangle className="h-4 w-4 mt-0.5" />
                <p>
                  Invocation records could not be loaded. Check room membership
                  and backend availability.
                </p>
              </div>
            ) : invocationsQuery.isLoading ? (
              <p className="text-muted-foreground">Loading invocations...</p>
            ) : invocations.length === 0 ? (
              <p className="text-muted-foreground">
                No recorded agent invocations for this room yet.
              </p>
            ) : (
              <div className="space-y-3">
                <div className="space-y-2 max-h-56 overflow-y-auto">
                  {invocations.map((item) => {
                    const selected = item.id === selectedInvocationSummary?.id
                    return (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => setSelectedInvocationId(item.id)}
                        className={`w-full rounded border p-2 text-left transition-colors ${
                          selected
                            ? "border-primary bg-background"
                            : "border-border hover:bg-background/70"
                        }`}
                      >
                        <div className="flex items-center justify-between gap-2">
                          <div className="min-w-0">
                            <p className="font-medium truncate">
                              {item.agent_slug}
                            </p>
                            <p className="text-[10px] text-muted-foreground truncate">
                              {item.trigger_source}
                              {item.a2a_depth > 0
                                ? ` depth ${item.a2a_depth}`
                                : ""}{" "}
                              • {formatDateTime(item.started_at)}
                            </p>
                          </div>
                          <Badge
                            variant={
                              item.success === false
                                ? "destructive"
                                : item.completed_at
                                  ? "secondary"
                                  : "default"
                            }
                            className="text-[9px]"
                          >
                            {item.success === false
                              ? "error"
                              : item.completed_at
                                ? "done"
                                : "running"}
                          </Badge>
                        </div>
                        <div className="mt-2 grid grid-cols-2 gap-2 text-[10px] text-muted-foreground">
                          <span className="flex items-center gap-1 min-w-0">
                            <Clock className="h-3 w-3 shrink-0" />
                            <span className="truncate">
                              {formatDuration(
                                item.started_at,
                                item.completed_at,
                              )}
                            </span>
                          </span>
                          <span className="flex items-center gap-1 min-w-0">
                            <Hash className="h-3 w-3 shrink-0" />
                            <span className="truncate">
                              {item.prompt_sha256.slice(0, 12)}
                            </span>
                          </span>
                        </div>
                        {storyNodeTitle(item) ? (
                          <p className="mt-1 text-[10px] text-muted-foreground truncate">
                            Story node: {storyNodeTitle(item)}
                          </p>
                        ) : null}
                      </button>
                    )
                  })}
                </div>

                <div className="rounded border border-border bg-background p-2 space-y-3">
                  {detailQuery.isLoading ? (
                    <p className="text-muted-foreground">
                      Loading invocation detail...
                    </p>
                  ) : selectedInvocation ? (
                    <>
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <p className="font-medium truncate">
                            {selectedInvocation.agent_slug}
                          </p>
                          <p className="text-[10px] text-muted-foreground truncate">
                            {selectedInvocation.model_name || "model unknown"} •{" "}
                            {selectedInvocation.prompt_builder_version}
                          </p>
                        </div>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 px-2"
                          onClick={() =>
                            handleCopyInvocation(
                              "invocation",
                              selectedInvocation,
                            )
                          }
                          title="Copy full invocation response JSON"
                        >
                          {copiedInvocationTarget === "invocation" ? (
                            <Check className="h-3 w-3 text-green-500" />
                          ) : (
                            <Copy className="h-3 w-3" />
                          )}
                        </Button>
                      </div>

                      <div className="grid grid-cols-2 gap-2 text-[10px]">
                        <div>
                          <p className="text-muted-foreground">Prompt hash</p>
                          <p className="font-mono truncate">
                            {selectedInvocation.prompt_sha256}
                          </p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">
                            Response event
                          </p>
                          <p className="font-mono truncate">
                            {shortId(selectedInvocation.response_event_id)}
                          </p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Story node</p>
                          <p className="truncate">
                            {selectedStoryNode || "none captured"}
                          </p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Context items</p>
                          <p>
                            {selectedExtraContextCount} extra /{" "}
                            {selectedRepoContextCount} repo-like
                          </p>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <div className="flex flex-wrap gap-1">
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-7 px-2 text-[10px]"
                            onClick={() =>
                              handleCopyInvocation(
                                "prompt",
                                selectedInvocation.full_prompt ??
                                  selectedInvocation.full_prompt_redacted ??
                                  "",
                              )
                            }
                          >
                            {copiedInvocationTarget === "prompt" ? (
                              <Check className="h-3 w-3 mr-1 text-green-500" />
                            ) : (
                              <Copy className="h-3 w-3 mr-1" />
                            )}
                            Prompt
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-7 px-2 text-[10px]"
                            onClick={() =>
                              handleCopyInvocation(
                                "context",
                                selectedInvocation.room_context_json,
                              )
                            }
                          >
                            {copiedInvocationTarget === "context" ? (
                              <Check className="h-3 w-3 mr-1 text-green-500" />
                            ) : (
                              <FileJson className="h-3 w-3 mr-1" />
                            )}
                            Context
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-7 px-2 text-[10px]"
                            onClick={() =>
                              handleCopyInvocation(
                                "runtime",
                                selectedInvocation.story_runtime_json,
                              )
                            }
                          >
                            {copiedInvocationTarget === "runtime" ? (
                              <Check className="h-3 w-3 mr-1 text-green-500" />
                            ) : (
                              <FileJson className="h-3 w-3 mr-1" />
                            )}
                            Runtime
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-7 px-2 text-[10px]"
                            onClick={() =>
                              handleCopyInvocation("provenance", {
                                runtime_prompt_payload:
                                  selectedInvocation.runtime_prompt_payload,
                                runtime_prompt_provenance:
                                  selectedInvocation.runtime_prompt_provenance,
                              })
                            }
                          >
                            {copiedInvocationTarget === "provenance" ? (
                              <Check className="h-3 w-3 mr-1 text-green-500" />
                            ) : (
                              <FileJson className="h-3 w-3 mr-1" />
                            )}
                            Provenance
                          </Button>
                        </div>

                        <pre className="bg-muted rounded p-2 max-h-56 overflow-auto text-[10px] font-mono whitespace-pre-wrap">
                          {selectedInvocation.full_prompt ??
                            selectedInvocation.full_prompt_redacted ??
                            "No prompt returned by API policy."}
                        </pre>
                        {selectedInvocation.full_prompt ? null : (
                          <p className="text-[10px] text-muted-foreground">
                            Full prompt is hidden for this user; copy uses the
                            redacted prompt returned by the API.
                          </p>
                        )}
                        {selectedInvocation.error ? (
                          <p className="text-[10px] text-destructive">
                            Error: {selectedInvocation.error}
                          </p>
                        ) : null}
                      </div>
                    </>
                  ) : (
                    <p className="text-muted-foreground">
                      Select an invocation to inspect its exact prompt and
                      context snapshot.
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        </CollapsibleContent>
      </Collapsible>

      {/* API Payload Preview */}
      <Collapsible
        open={expandedSections.apiPayload}
        onOpenChange={() => toggleSection("apiPayload")}
      >
        <CollapsibleTrigger asChild>
          <Button variant="ghost" size="sm" className="w-full justify-between">
            <span className="flex items-center gap-2">
              <Code className="h-4 w-4" />
              Message Context Preview
            </span>
            {expandedSections.apiPayload ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <div className="bg-muted rounded-md p-3 mt-2 text-xs">
            <div className="flex items-center justify-between mb-2">
              <p className="text-muted-foreground text-[10px] uppercase">
                Frontend approximation:
              </p>
              <Button
                size="sm"
                variant="ghost"
                className="h-6 px-2"
                onClick={handleCopyPayload}
              >
                {copiedPayload ? (
                  <Check className="h-3 w-3 text-green-500" />
                ) : (
                  <Copy className="h-3 w-3" />
                )}
              </Button>
            </div>
            <pre className="bg-background rounded p-2 max-h-64 overflow-auto text-[10px] font-mono whitespace-pre-wrap">
              {JSON.stringify(apiPayload, null, 2)}
            </pre>
            {contextMessages.length === 0 && (
              <p className="text-amber-600 dark:text-amber-400 text-[10px] mt-2">
                ⚠️ No messages in context - agent will receive empty message
                array
              </p>
            )}
          </div>
        </CollapsibleContent>
      </Collapsible>

      {/* Repo File Context */}
      <Collapsible
        open={expandedSections.repoFiles}
        onOpenChange={() => toggleSection("repoFiles")}
      >
        <CollapsibleTrigger asChild>
          <Button variant="ghost" size="sm" className="w-full justify-between">
            <span className="flex items-center gap-2">
              <Code className="h-4 w-4" />
              Repo Files ({repoContextFiles.length} in context /{" "}
              {selectedRepoFiles.length} selected)
            </span>
            {expandedSections.repoFiles ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <div className="bg-muted rounded-md p-3 mt-2 text-xs space-y-3">
            <div>
              <p className="text-muted-foreground text-[10px] uppercase mb-1">
                Selected paths
              </p>
              {selectedRepoFiles.length === 0 ? (
                <p className="text-muted-foreground">No selected files.</p>
              ) : (
                <div className="space-y-1 max-h-24 overflow-y-auto">
                  {selectedRepoFiles.map((item) => (
                    <div
                      key={`${item.selectionKey}:${item.path}`}
                      className="font-mono text-[10px] truncate"
                    >
                      {item.selectionKey}: {item.path}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div>
              <p className="text-muted-foreground text-[10px] uppercase mb-1">
                In room context
              </p>
              {repoContextFiles.length === 0 ? (
                <p className="text-muted-foreground">
                  No repo files in room context.
                </p>
              ) : (
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {repoContextFiles.map((item) => {
                    const isSelected = selectedPathSet.has(item.path)
                    const isRemoving =
                      removingContextIds[item.contextId] === true
                    return (
                      <div
                        key={item.contextId}
                        className="rounded border border-border p-2"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <div className="min-w-0">
                            <p className="font-mono text-[10px] truncate">
                              {item.path}
                            </p>
                            <p className="text-[10px] text-muted-foreground truncate">
                              {item.repoSlug || item.repoId} @ {item.ref}
                            </p>
                          </div>
                          <div className="flex items-center gap-1">
                            {isSelected ? (
                              <Badge variant="secondary" className="text-[9px]">
                                Selected
                              </Badge>
                            ) : null}
                            {item.isTruncated ? (
                              <Badge variant="outline" className="text-[9px]">
                                Truncated
                              </Badge>
                            ) : null}
                            {canManageRoomContext && onRemoveRepoContextFile ? (
                              <Button
                                size="sm"
                                variant="ghost"
                                className="h-6 px-2"
                                disabled={isRemoving}
                                onClick={async () => {
                                  setRemovingContextIds((current) => ({
                                    ...current,
                                    [item.contextId]: true,
                                  }))
                                  try {
                                    await onRemoveRepoContextFile(
                                      item.contextId,
                                    )
                                  } finally {
                                    setRemovingContextIds((current) => ({
                                      ...current,
                                      [item.contextId]: false,
                                    }))
                                  }
                                }}
                                title="Remove from room context"
                              >
                                <Trash2 className="h-3 w-3" />
                              </Button>
                            ) : null}
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-6 px-2"
                              onClick={async () => {
                                try {
                                  await navigator.clipboard.writeText(
                                    JSON.stringify(item.payload, null, 2),
                                  )
                                  setCopiedContextIds((current) => ({
                                    ...current,
                                    [item.contextId]: true,
                                  }))
                                  setTimeout(() => {
                                    setCopiedContextIds((current) => ({
                                      ...current,
                                      [item.contextId]: false,
                                    }))
                                  }, 1500)
                                } catch (error) {
                                  console.error(
                                    "Failed to copy context payload",
                                    error,
                                  )
                                }
                              }}
                              title="Copy context payload JSON"
                            >
                              {copiedContextIds[item.contextId] ? (
                                <Check className="h-3 w-3 text-green-500" />
                              ) : (
                                <Copy className="h-3 w-3" />
                              )}
                            </Button>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
              {!canManageRoomContext && repoContextFiles.length > 0 ? (
                <p className="text-[10px] text-muted-foreground mt-2">
                  Only room owners can remove context files.
                </p>
              ) : null}
            </div>
          </div>
        </CollapsibleContent>
      </Collapsible>

      {/* Streaming State */}
      <Collapsible
        open={expandedSections.streaming}
        onOpenChange={() => toggleSection("streaming")}
      >
        <CollapsibleTrigger asChild>
          <Button variant="ghost" size="sm" className="w-full justify-between">
            <span className="flex items-center gap-2">
              <Bot className="h-4 w-4" />
              Streaming Response
              {streamingMessage && (
                <Badge variant="default" className="animate-pulse text-[10px]">
                  LIVE
                </Badge>
              )}
            </span>
            {expandedSections.streaming ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <div className="bg-muted rounded-md p-3 mt-2 text-xs">
            {streamingMessage ? (
              <div className="space-y-2">
                <div>
                  <span className="font-semibold text-primary">
                    {streamingMessage.agent_name}
                  </span>
                  <span className="text-muted-foreground"> is typing...</span>
                </div>
                <div className="bg-background rounded p-2 max-h-32 overflow-y-auto">
                  <p className="whitespace-pre-wrap text-xs">
                    {streamingMessage.content || "(waiting for content...)"}
                  </p>
                </div>
                {lastUserMessage && (
                  <div className="border-t pt-2 mt-2">
                    <p className="text-muted-foreground text-[10px] uppercase mb-1">
                      Responding to:
                    </p>
                    <p className="text-xs truncate">
                      "{lastUserMessage.content}"
                    </p>
                    <p className="text-muted-foreground text-[10px]">
                      — {lastUserMessage.sender_name}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <span className="text-muted-foreground">
                No agent currently streaming
              </span>
            )}
          </div>
        </CollapsibleContent>
      </Collapsible>

      {/* Active Context */}
      <Collapsible
        open={expandedSections.context}
        onOpenChange={() => toggleSection("context")}
      >
        <CollapsibleTrigger asChild>
          <Button variant="ghost" size="sm" className="w-full justify-between">
            <span className="flex items-center gap-2">
              <Eye className="h-4 w-4" />
              Agent Context ({contextMessages.length})
            </span>
            {expandedSections.context ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <div className="bg-muted rounded-md p-3 mt-2 text-xs max-h-60 overflow-y-auto">
            {contextMessages.length === 0 ? (
              <span className="text-muted-foreground">
                No messages in agent context
              </span>
            ) : (
              <div className="space-y-2">
                <p className="text-muted-foreground text-[10px] uppercase">
                  Messages visible to agents:
                </p>
                {contextMessages.slice(-10).map((msg) => (
                  <div
                    key={msg.message_id}
                    className="border-l-2 border-primary/30 pl-2 py-1"
                  >
                    <p className="font-semibold text-[10px]">
                      {msg.sender_name}
                      {msg.is_pinned && (
                        <Badge variant="outline" className="ml-1 text-[8px]">
                          📌
                        </Badge>
                      )}
                    </p>
                    <p className="truncate">{msg.content}</p>
                  </div>
                ))}
                {contextMessages.length > 10 && (
                  <p className="text-muted-foreground text-[10px]">
                    ...and {contextMessages.length - 10} more
                  </p>
                )}
              </div>
            )}
          </div>
        </CollapsibleContent>
      </Collapsible>

      {/* Active Agents */}
      <Collapsible
        open={expandedSections.agents}
        onOpenChange={() => toggleSection("agents")}
      >
        <CollapsibleTrigger asChild>
          <Button variant="ghost" size="sm" className="w-full justify-between">
            <span className="flex items-center gap-2">
              <Bot className="h-4 w-4" />
              Active Agents ({activeAgents.length})
            </span>
            {expandedSections.agents ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <div className="bg-muted rounded-md p-3 mt-2 text-xs">
            {activeAgents.length === 0 ? (
              <span className="text-muted-foreground">
                No agents active in this room
              </span>
            ) : (
              <div className="space-y-2">
                {activeAgents.map((agent) => (
                  <div
                    key={agent.participant_id}
                    className="flex items-center gap-2"
                  >
                    <div className="h-2 w-2 rounded-full bg-green-500" />
                    <span>{agent.display_name}</span>
                    <Badge variant="outline" className="text-[10px]">
                      {agent.role}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </div>
        </CollapsibleContent>
      </Collapsible>

      {/* Recent Messages */}
      <Collapsible
        open={expandedSections.recent}
        onOpenChange={() => toggleSection("recent")}
      >
        <CollapsibleTrigger asChild>
          <Button variant="ghost" size="sm" className="w-full justify-between">
            <span className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              Recent Messages ({Math.min(5, messages.length)})
            </span>
            {expandedSections.recent ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <div className="bg-muted rounded-md p-3 mt-2 text-xs max-h-48 overflow-y-auto">
            {recentMessages.length === 0 ? (
              <span className="text-muted-foreground">No messages yet</span>
            ) : (
              <div className="space-y-2">
                {recentMessages.map((msg) => (
                  <div key={msg.message_id} className="space-y-1">
                    <div className="flex items-center gap-1">
                      <span
                        className={`font-semibold ${
                          msg.sender_type === "user"
                            ? "text-blue-600 dark:text-blue-400"
                            : "text-purple-600 dark:text-purple-400"
                        }`}
                      >
                        {msg.sender_name}
                      </span>
                      {msg.sender_type === "agent_internal" && (
                        <Badge variant="outline" className="text-[8px]">
                          internal
                        </Badge>
                      )}
                      {msg.active_for_context && (
                        <Eye className="h-3 w-3 text-green-500" />
                      )}
                    </div>
                    <p className="truncate text-muted-foreground">
                      {msg.content}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </CollapsibleContent>
      </Collapsible>

      {/* Stats Footer */}
      <div className="border-t pt-4 text-xs text-muted-foreground space-y-1">
        <p>Total Messages: {messages.length}</p>
        <p>In Context: {contextMessages.length}</p>
        <p>Pinned: {messages.filter((m) => m.is_pinned).length}</p>
      </div>
    </div>
  )
}

/**
 * Legacy wrapper - maintains backward compatibility
 * @deprecated Use DebugPanel from Room/panels for new code
 */
export default function RoomDebugPanel(props: RoomDebugPanelContentProps) {
  return (
    <aside className="bg-background border-border w-80 overflow-y-auto border-l p-4 space-y-4">
      <h3 className="text-sm font-semibold flex items-center gap-2">
        <Bug className="h-4 w-4" />
        Debug Panel
      </h3>
      <RoomDebugPanelContent {...props} />
    </aside>
  )
}
