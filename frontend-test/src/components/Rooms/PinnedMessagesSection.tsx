/**
 * PinnedMessagesSection Component
 *
 * Dedicated section displaying pinned messages at top of message list.
 * Visually distinct with yellow theme and pin icon.
 */

import { Pin } from "lucide-react"
import type { MessageViewModel } from "@/services/roomService"
import Message from "./Message"

interface PinnedMessagesSectionProps {
  messages: MessageViewModel[]
}

export default function PinnedMessagesSection({
  messages,
}: PinnedMessagesSectionProps) {
  if (messages.length === 0) {
    return null
  }

  return (
    <div className="bg-yellow-50 dark:bg-yellow-900/30 border-l-4 border-yellow-400 dark:border-yellow-600 p-4 rounded-md">
      {/* Header with pin icon and count */}
      <div className="flex items-center gap-2 mb-3">
        <Pin className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
        <span className="font-bold text-yellow-800 dark:text-yellow-200">
          Pinned Messages ({messages.length})
        </span>
      </div>

      {/* Pinned message list */}
      <div className="flex flex-col gap-2">
        {messages.map((message) => (
          <Message key={message.message_id} message={message} />
        ))}
      </div>
    </div>
  )
}
