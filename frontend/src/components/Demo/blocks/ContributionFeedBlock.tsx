import { MessageSquare, Radio } from "lucide-react"
import type { MessageViewModel } from "@/services/roomService"
import { Badge } from "@/components/ui/badge"

interface ContributionFeedBlockProps {
  title?: string | null
  config: unknown
  messages: MessageViewModel[]
  streamingMessage: { agent_name: string; content: string } | null
  rowHighlightCss?: string
  calloutLabel?: string | null
}

export interface ContributionFeedConfig {
  max_items: number
  include_internal: boolean
  show_sender_type: boolean
  show_timestamps: boolean
  show_config_json: boolean
}

interface ContributionFeedSelection {
  filtered: MessageViewModel[]
  recentMessages: MessageViewModel[]
}

export function parseContributionFeedConfig(value: unknown): ContributionFeedConfig {
  const raw = value && typeof value === "object" ? (value as Record<string, unknown>) : {}

  const maxItemsRaw = raw.max_items
  const maxItems =
    typeof maxItemsRaw === "number" && Number.isFinite(maxItemsRaw) && maxItemsRaw > 0
      ? Math.floor(maxItemsRaw)
      : 12

  return {
    max_items: maxItems,
    include_internal: raw.include_internal === true,
    show_sender_type: raw.show_sender_type === true,
    show_timestamps: raw.show_timestamps !== false,
    show_config_json: raw.show_config_json === true,
  }
}

export function selectContributionFeedMessages({
  config,
  messages,
}: {
  config: ContributionFeedConfig
  messages: MessageViewModel[]
}): ContributionFeedSelection {
  const filtered = config.include_internal
    ? messages
    : messages.filter((message) => message.sender_type !== "agent_internal")

  const recentMessages = [...filtered]
    .sort((a, b) => b.created_at.getTime() - a.created_at.getTime())
    .slice(0, config.max_items)

  return {
    filtered,
    recentMessages,
  }
}

export function formatContributionSenderType(value: MessageViewModel["sender_type"]): string {
  if (value === "agent_internal") return "agent/internal"
  return value
}

function formatTime(value: Date): string {
  return value.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
}

export function ContributionFeedBlock({
  title,
  config,
  messages,
  streamingMessage,
  rowHighlightCss,
  calloutLabel,
}: ContributionFeedBlockProps) {
  const parsedConfig = parseContributionFeedConfig(config)
  const selection = selectContributionFeedMessages({ config: parsedConfig, messages })

  return (
    <div className="p-4 space-y-4">
      <div className="space-y-1">
        <div className="text-sm font-medium">{title ?? "Contribution Feed"}</div>
        <div className="text-xs text-muted-foreground">Recent room contributions from users and agents.</div>
      </div>
      {calloutLabel && (
        <div className="rounded border bg-muted/30 px-2 py-1 text-xs text-muted-foreground">
          {calloutLabel}
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        <Badge variant="outline" className="gap-1">
          <MessageSquare className="h-3 w-3" />
          Messages: {selection.filtered.length}
        </Badge>
        <Badge variant={parsedConfig.include_internal ? "default" : "secondary"}>
          Internal {parsedConfig.include_internal ? "included" : "hidden"}
        </Badge>
        {streamingMessage && (
          <Badge variant="default" className="gap-1">
            <Radio className="h-3 w-3" />
            {streamingMessage.agent_name} streaming
          </Badge>
        )}
      </div>

      <div className="rounded-md border bg-muted/20 p-3">
        {selection.recentMessages.length === 0 ? (
          <div className="text-xs text-muted-foreground">No contributions to display.</div>
        ) : (
          <div className="space-y-2">
            {selection.recentMessages.map((message) => (
              <div
                key={message.message_id}
                className="rounded-md border bg-background/60 p-2.5"
                style={rowHighlightCss ? { boxShadow: rowHighlightCss } : undefined}
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="text-xs font-medium truncate">{message.sender_name}</div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    {parsedConfig.show_sender_type && (
                      <Badge variant="secondary" className="text-[10px]">
                        {formatContributionSenderType(message.sender_type)}
                      </Badge>
                    )}
                    {parsedConfig.show_timestamps && (
                      <span className="text-[10px] text-muted-foreground">
                        {formatTime(message.created_at)}
                      </span>
                    )}
                  </div>
                </div>
                <div className="mt-1 text-xs text-muted-foreground line-clamp-3">
                  {message.content || "(empty message)"}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {parsedConfig.show_config_json && (
        <pre className="max-h-64 overflow-auto rounded border bg-muted/40 p-3 text-xs">
          {JSON.stringify(config ?? {}, null, 2)}
        </pre>
      )}
    </div>
  )
}
