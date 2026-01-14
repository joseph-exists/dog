/**
 * RoomDebugPanel - Debug sidebar for room/agent debugging
 *
 * Features:
 * - Shows messages active for agent context
 * - Displays current streaming state
 * - Shows connection status
 * - Collapsible sections matching StoryPreview pattern
 *
 * @see StoryPreview.tsx for design pattern reference
 */

import { useState, useMemo } from "react"
import {
  Bug,
  ChevronDown,
  ChevronUp,
  Wifi,
  WifiOff,
  MessageSquare,
  Bot,
  Eye,
  Code,
  Copy,
  Check,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import type { MessageViewModel, ParticipantViewModel } from "@/services/roomService"

interface RoomDebugPanelProps {
  messages: MessageViewModel[]
  streamingMessage: { agent_name: string; content: string } | null
  isConnected: boolean
  activeAgents: ParticipantViewModel[]
}

export default function RoomDebugPanel({
  messages,
  streamingMessage,
  isConnected,
  activeAgents,
}: RoomDebugPanelProps) {
  const [expandedSections, setExpandedSections] = useState({
    apiPayload: true,
    context: true,
    streaming: true,
    agents: true,
    recent: false,
  })

  const [copiedPayload, setCopiedPayload] = useState(false)

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
      role: msg.sender_type === "agent" ? "assistant" : "user",
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

  const handleCopyPayload = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(apiPayload, null, 2))
      setCopiedPayload(true)
      setTimeout(() => setCopiedPayload(false), 2000)
    } catch (err) {
      console.error("Failed to copy:", err)
    }
  }

  return (
    <aside className="bg-background border-border w-80 overflow-y-auto border-l p-4 space-y-4">
      <h3 className="text-sm font-semibold flex items-center gap-2">
        <Bug className="h-4 w-4" />
        Debug Panel
      </h3>

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

      {/* API Payload Preview */}
      <Collapsible
        open={expandedSections.apiPayload}
        onOpenChange={() => toggleSection("apiPayload")}
      >
        <CollapsibleTrigger asChild>
          <Button variant="ghost" size="sm" className="w-full justify-between">
            <span className="flex items-center gap-2">
              <Code className="h-4 w-4" />
              API Payload Preview
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
                Messages sent to agent:
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
                ⚠️ No messages in context - agent will receive empty message array
              </p>
            )}
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
                          msg.sender_type === "agent"
                            ? "text-purple-600 dark:text-purple-400"
                            : "text-blue-600 dark:text-blue-400"
                        }`}
                      >
                        {msg.sender_name}
                      </span>
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
        <p>
          Pinned:{" "}
          {messages.filter((m) => m.is_pinned).length}
        </p>
      </div>
    </aside>
  )
}
