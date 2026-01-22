// src/components/Page/PageHeader.tsx
import { ChevronRight, MoreVertical, Pencil, Save, Share2 } from "lucide-react"

import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"

import { getEntityTypeOrThrow } from "./registry"

export interface PageHeaderProps {
  entityTypeId: string
  entityName: string
  createdAt: Date
  updatedAt: Date
  isOwner: boolean
  editMode: boolean
  onEditModeChange: (enabled: boolean) => void
  onSave?: () => void
  onShare: () => void
  onDelete?: () => void
  isSaving?: boolean
  isDirty?: boolean
}

/**
 * Simple relative time formatting
 */
function formatRelativeTime(date: Date): string {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffSeconds = Math.floor(diffMs / 1000)
  const diffMinutes = Math.floor(diffSeconds / 60)
  const diffHours = Math.floor(diffMinutes / 60)
  const diffDays = Math.floor(diffHours / 24)
  const diffWeeks = Math.floor(diffDays / 7)
  const diffMonths = Math.floor(diffDays / 30)
  const diffYears = Math.floor(diffDays / 365)

  if (diffSeconds < 60) {
    return "just now"
  }
  if (diffMinutes < 60) {
    return `${diffMinutes}m ago`
  }
  if (diffHours < 24) {
    return `${diffHours}h ago`
  }
  if (diffDays < 7) {
    return `${diffDays}d ago`
  }
  if (diffWeeks < 4) {
    return `${diffWeeks}w ago`
  }
  if (diffMonths < 12) {
    return `${diffMonths}mo ago`
  }
  return `${diffYears}y ago`
}

/**
 * PageHeader - Header component for entity pages
 *
 * Displays breadcrumb navigation, timestamps, and action buttons.
 * Actions vary based on whether the current user is the owner.
 */
export function PageHeader({
  entityTypeId,
  entityName,
  createdAt,
  updatedAt,
  isOwner,
  editMode,
  onEditModeChange,
  onSave,
  onShare,
  onDelete,
  isSaving,
  isDirty,
}: PageHeaderProps) {
  const entityType = getEntityTypeOrThrow(entityTypeId)

  return (
    <div className="flex items-center justify-between py-4">
      {/* Left section: Breadcrumb and timestamps */}
      <div className="flex flex-col gap-1">
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink href="#">{entityType.labelPlural}</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator>
              <ChevronRight className="h-3.5 w-3.5" />
            </BreadcrumbSeparator>
            <BreadcrumbItem>
              <BreadcrumbPage>{entityName}</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
        <p className="text-xs text-muted-foreground">
          Created {formatRelativeTime(createdAt)} · Updated{" "}
          {formatRelativeTime(updatedAt)}
        </p>
      </div>

      {/* Right section: Actions */}
      <div className="flex items-center gap-2">
        {/* Status indicator in edit mode */}
        {editMode && (
          <span className="text-xs text-muted-foreground">
            {isSaving ? "Saving..." : isDirty ? "Unsaved changes" : ""}
          </span>
        )}

        {/* Save button - shown in edit mode when dirty */}
        {editMode && isDirty && (
          <Button
            type="button"
            variant="default"
            size="sm"
            onClick={onSave}
            disabled={isSaving}
          >
            <Save className="h-4 w-4 mr-1" />
            {isSaving ? "Saving..." : "Save"}
          </Button>
        )}

        {/* Edit toggle - owner only */}
        {isOwner && (
          <div className="flex items-center gap-2">
            <Switch
              id="edit-mode"
              checked={editMode}
              onCheckedChange={onEditModeChange}
              disabled={isSaving}
            />
            <Label htmlFor="edit-mode" className="text-sm">
              Edit
            </Label>
          </div>
        )}

        {/* Share button */}
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={onShare}
          aria-label="Share"
        >
          <Share2 className="h-4 w-4" />
        </Button>

        {/* Edit button - owner only, also triggers edit mode */}
        {isOwner && (
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={() => onEditModeChange(true)}
            aria-label="Edit"
          >
            <Pencil className="h-4 w-4" />
          </Button>
        )}

        {/* More actions dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              aria-label="More options"
            >
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem>Change Template</DropdownMenuItem>
            <DropdownMenuItem>Export</DropdownMenuItem>
            <DropdownMenuSeparator />
            {isOwner ? (
              <DropdownMenuItem variant="destructive" onClick={onDelete}>
                Delete
              </DropdownMenuItem>
            ) : (
              <DropdownMenuItem>Report</DropdownMenuItem>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  )
}
