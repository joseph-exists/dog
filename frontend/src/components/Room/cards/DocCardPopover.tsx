/**
 * DocCardPopover
 *
 * Popover component for displaying document/file details.
 * Uses EntityCardPopover as the base wrapper.
 */

import {
  Calendar,
  Download,
  ExternalLink,
  FileText,
  HardDrive,
} from "lucide-react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { ActionBar, type ActionItem } from "../primitives/ActionBar"
import { EntityCardPopover } from "./EntityCardPopover"

export interface DocCardData {
  id: string
  name: string
  type?: string // file extension like "pdf", "md", "txt"
  size_bytes?: number
  created_at?: string
  preview_text?: string
}

interface DocCardPopoverProps {
  doc: DocCardData
  trigger: React.ReactNode
  onOpen?: () => void
  onDownload?: () => void
  align?: "start" | "center" | "end"
}

function formatFileSize(bytes?: number): string {
  if (!bytes) return "Unknown size"
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatDate(dateString?: string): string {
  if (!dateString) return "Unknown date"
  return new Date(dateString).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  })
}

export function DocCardPopover({
  doc,
  trigger,
  onOpen,
  onDownload,
  align = "center",
}: DocCardPopoverProps) {
  const actions: ActionItem[] = []

  if (onOpen) {
    actions.push({
      id: "open",
      icon: ExternalLink,
      label: "Open document",
      onClick: onOpen,
    })
  }

  if (onDownload) {
    actions.push({
      id: "download",
      icon: Download,
      label: "Download",
      onClick: onDownload,
    })
  }

  const header = (
    <div className="flex items-center gap-3">
      <Avatar className="h-10 w-10 border bg-[hsl(var(--doc-accent)/0.15)] border-[hsl(var(--doc-accent)/0.3)]">
        <AvatarFallback className="bg-transparent text-[hsl(var(--doc-accent))]">
          <FileText className="h-5 w-5" />
        </AvatarFallback>
      </Avatar>
      <div className="flex-1 min-w-0">
        <p className="font-medium truncate">{doc.name}</p>
        {doc.type && (
          <Badge variant="secondary" className="text-xs uppercase">
            {doc.type}
          </Badge>
        )}
      </div>
    </div>
  )

  const footer =
    actions.length > 0 ? <ActionBar actions={actions} /> : undefined

  return (
    <EntityCardPopover
      trigger={trigger}
      header={header}
      footer={footer}
      align={align}
    >
      <div className="space-y-3">
        {doc.preview_text && (
          <div className="rounded-md bg-muted/50 p-3">
            <p className="text-sm text-muted-foreground line-clamp-3">
              {doc.preview_text}
            </p>
          </div>
        )}
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-1.5">
            <HardDrive className="h-3.5 w-3.5" />
            <span>{formatFileSize(doc.size_bytes)}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Calendar className="h-3.5 w-3.5" />
            <span>{formatDate(doc.created_at)}</span>
          </div>
        </div>
      </div>
    </EntityCardPopover>
  )
}
