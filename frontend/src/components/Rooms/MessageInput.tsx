/**
 * MessageInput Component
 *
 * Text input for sending messages with:
 * - Controlled input with local state
 * - Send on Enter key
 * - Clear input after send
 * - Loading state while sending
 * - Validation (no empty messages)
 * - WebSocket streaming support with REST API fallback
 */

import { Loader2, Send } from "lucide-react"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

interface MessageInputProps {
  roomId: string
  onSendMessage: (content: string) => Promise<void>
  isSending: boolean
  disabled?: boolean
  isConnected: boolean
  sendViaWebSocket: (content: string) => void
}

export default function MessageInput({
  onSendMessage,
  isSending,
  disabled = false,
  isConnected,
  sendViaWebSocket,
}: MessageInputProps) {
  const [content, setContent] = useState("")

  const handleSend = async () => {
    if (!content.trim() || isSending || disabled) return

    try {
      // Prefer WebSocket if connected, fallback to REST API
      if (isConnected) {
        sendViaWebSocket(content.trim())
        setContent("") // Clear immediately for WebSocket (optimistic)
      } else {
        await onSendMessage(content.trim())
        setContent("") // Clear on success
      }
    } catch (error) {
      console.error("Failed to send message:", error)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const isDisabled = !content.trim() || isSending || disabled

  return (
    <div className="p-4 border-t border-border bg-background">
      <div className="flex gap-2">
        <Input
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            isConnected
              ? "Type a message..."
              : "Type a message... (isConnected: offline bug?)"
          }
          disabled={disabled || isSending}
          className="flex-1"
        />
        <Button
          onClick={handleSend}
          disabled={isDisabled}
          aria-label="Send message"
        >
          {isSending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </Button>
      </div>
    </div>
  )
}
