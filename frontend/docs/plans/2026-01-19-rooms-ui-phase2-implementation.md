# Rooms UI Phase 2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extend the multi-panel room system with entity cards, additional panels (Story, Debug, Canvas, A2UI), and backend panel persistence with room defaults + user overrides.

**Continues from:** `2026-01-19-rooms-ui-implementation.md` (Phase 1-5, Tasks 1-13)

**Design Reference:** `2026-01-19-rooms-ui-design.md`

---

## Phase 6: Theme Foundation & Primitives

### Task 14: Add Semantic Theme Tokens

**Files:**
- Modify: `frontend/src/index.css`

**Step 1: Add entity-specific CSS variables**

Add to `:root` and `.dark` sections in `frontend/src/index.css`:

```css
:root {
  /* Existing variables... */

  /* Entity accent colors - for cards and badges */
  --agent-accent: 262 83% 58%;
  --agent-accent-foreground: 0 0% 100%;
  --user-accent: 221 83% 53%;
  --user-accent-foreground: 0 0% 100%;
  --doc-accent: 142 76% 36%;
  --doc-accent-foreground: 0 0% 100%;
}

.dark {
  /* Existing variables... */

  --agent-accent: 263 70% 70%;
  --agent-accent-foreground: 0 0% 0%;
  --user-accent: 217 91% 75%;
  --user-accent-foreground: 0 0% 0%;
  --doc-accent: 142 71% 45%;
  --doc-accent-foreground: 0 0% 0%;
}
```

**Step 2: Verify styles load**

```bash
cd /home/josep/dog/frontend && npm run dev
```

Open DevTools, verify CSS variables are present in `:root`

**Step 3: Commit**

```bash
git add frontend/src/index.css
git commit -m "feat(theme): add entity accent color tokens for cards"
```

---

### Task 15: Create PlaceholderContent Primitive

**Files:**
- Create: `frontend/src/components/Room/primitives/PlaceholderContent.tsx`
- Modify: `frontend/src/components/Room/primitives/index.ts`

**Step 1: Create PlaceholderContent component**

```typescript
/**
 * PlaceholderContent Primitive
 *
 * Consistent "coming soon" or empty state for panels.
 * Used for placeholder panels and empty states.
 *
 * @example
 * ```tsx
 * <PlaceholderContent
 *   icon={Paintbrush}
 *   title="Canvas"
 *   description="Interactive canvas coming soon."
 * />
 * ```
 */

import type { LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"

interface PlaceholderContentProps {
  /** Icon to display */
  icon: LucideIcon
  /** Title text */
  title: string
  /** Description text */
  description?: string
  /** Optional action button */
  action?: React.ReactNode
  /** Additional className */
  className?: string
}

export function PlaceholderContent({
  icon: Icon,
  title,
  description,
  action,
  className,
}: PlaceholderContentProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center h-full p-8 text-center",
        className
      )}
    >
      <div className="rounded-full bg-muted p-4 mb-4">
        <Icon className="h-8 w-8 text-muted-foreground" />
      </div>
      <h3 className="text-lg font-medium text-foreground mb-2">{title}</h3>
      {description && (
        <p className="text-sm text-muted-foreground max-w-xs mb-4">
          {description}
        </p>
      )}
      {action}
    </div>
  )
}
```

**Step 2: Update primitives barrel export**

Add to `frontend/src/components/Room/primitives/index.ts`:
```typescript
export { PlaceholderContent } from "./PlaceholderContent"
```

**Step 3: Verify no TypeScript errors**

```bash
cd /home/josep/dog/frontend && npm run lint
```

**Step 4: Commit**

```bash
git add frontend/src/components/Room/primitives/
git commit -m "feat(room): add PlaceholderContent primitive for empty states"
```

---

## Phase 7: Entity Cards

### Task 16: Create EntityCardPopover Base

**Files:**
- Create: `frontend/src/components/Room/cards/EntityCardPopover.tsx`

**Step 1: Create base popover component**

```typescript
/**
 * EntityCardPopover
 *
 * Base popover wrapper for all entity cards (Agent, User, Doc).
 * Provides consistent structure: header, content, footer with actions.
 *
 * @example
 * ```tsx
 * <EntityCardPopover
 *   trigger={<Avatar ... />}
 *   header={<AgentCardHeader agent={agent} />}
 *   footer={<ActionBar actions={agentActions} />}
 * >
 *   <AgentCardContent agent={agent} />
 * </EntityCardPopover>
 * ```
 */

import * as React from "react"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { cn } from "@/lib/utils"

interface EntityCardPopoverProps {
  /** Element that triggers the popover */
  trigger: React.ReactNode
  /** Header content (avatar, name, status) */
  header: React.ReactNode
  /** Main content area */
  children: React.ReactNode
  /** Footer content (action buttons) */
  footer?: React.ReactNode
  /** Popover alignment */
  align?: "start" | "center" | "end"
  /** Popover side */
  side?: "top" | "right" | "bottom" | "left"
  /** Additional className for content */
  className?: string
  /** Controlled open state */
  open?: boolean
  /** Controlled open change handler */
  onOpenChange?: (open: boolean) => void
}

export function EntityCardPopover({
  trigger,
  header,
  children,
  footer,
  align = "start",
  side = "bottom",
  className,
  open,
  onOpenChange,
}: EntityCardPopoverProps) {
  return (
    <Popover open={open} onOpenChange={onOpenChange}>
      <PopoverTrigger asChild>{trigger}</PopoverTrigger>
      <PopoverContent
        align={align}
        side={side}
        className={cn("w-80 p-0", className)}
      >
        {/* Header */}
        <div className="border-b border-border p-4">{header}</div>

        {/* Content */}
        <div className="p-4">{children}</div>

        {/* Footer */}
        {footer && (
          <div className="border-t border-border p-3 bg-muted/30">{footer}</div>
        )}
      </PopoverContent>
    </Popover>
  )
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/Room/cards/
git commit -m "feat(room): add EntityCardPopover base component"
```

---

### Task 17: Create AgentCardPopover

**Files:**
- Create: `frontend/src/components/Room/cards/AgentCardPopover.tsx`
- Modify: `frontend/src/components/Room/cards/index.ts`

**Step 1: Create AgentCardPopover component**

```typescript
/**
 * AgentCardPopover
 *
 * Popover showing agent details when triggered from participant UI.
 * Uses semantic --agent-accent color token for theming.
 *
 * @example Integration from ParticipantStack
 * ```tsx
 * <AgentCardPopover
 *   agent={agentData}
 *   trigger={<Avatar ... />}
 *   onEdit={() => openAgentEditor(id)}
 *   onRemove={() => removeFromRoom(id)}
 * />
 * ```
 *
 * @example Integration from message sender
 * ```tsx
 * <AgentCardPopover
 *   agent={agentData}
 *   trigger={<span className="cursor-pointer">{sender_name}</span>}
 * />
 * ```
 */

import * as React from "react"
import { Bot, Edit, Settings, Trash2, ExternalLink } from "lucide-react"
import { EntityCardPopover } from "./EntityCardPopover"
import { ActionBar, type ActionItem } from "../primitives/ActionBar"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

export interface AgentCardData {
  id: string
  name: string
  description?: string | null
  model_name?: string | null
  participation_mode?: "always" | "on_mention" | "manual"
  is_enabled?: boolean
  capabilities?: string[]
}

interface AgentCardPopoverProps {
  /** Agent data to display */
  agent: AgentCardData
  /** Element that triggers the popover */
  trigger: React.ReactNode
  /** Whether user can edit this agent */
  canEdit?: boolean
  /** Edit agent callback */
  onEdit?: () => void
  /** Remove from room callback */
  onRemove?: () => void
  /** View full agent page callback */
  onViewFull?: () => void
  /** Popover alignment */
  align?: "start" | "center" | "end"
}

const modeLabels: Record<string, string> = {
  always: "Always responds",
  on_mention: "Responds when mentioned",
  manual: "Manual trigger only",
}

export function AgentCardPopover({
  agent,
  trigger,
  canEdit = false,
  onEdit,
  onRemove,
  onViewFull,
  align = "start",
}: AgentCardPopoverProps) {
  const actions: ActionItem[] = []

  if (onViewFull) {
    actions.push({
      id: "view",
      icon: ExternalLink,
      label: "View agent details",
      onClick: onViewFull,
    })
  }

  if (canEdit && onEdit) {
    actions.push({
      id: "edit",
      icon: Settings,
      label: "Edit agent settings",
      onClick: onEdit,
    })
  }

  if (canEdit && onRemove) {
    actions.push({
      id: "remove",
      icon: Trash2,
      label: "Remove from room",
      onClick: onRemove,
      variant: "destructive",
    })
  }

  // Extract model display name
  const displayModel = agent.model_name
    ?.split(":")
    .pop()
    ?.replace(/-/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase())

  return (
    <EntityCardPopover
      trigger={trigger}
      align={align}
      header={
        <div className="flex items-center gap-3">
          <Avatar className="h-12 w-12 border-2 border-[hsl(var(--agent-accent)/0.3)]">
            <AvatarFallback className="bg-[hsl(var(--agent-accent)/0.15)] text-[hsl(var(--agent-accent))]">
              <Bot className="h-6 w-6" />
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <h4 className="font-semibold truncate">{agent.name}</h4>
            <div className="flex items-center gap-2 mt-1">
              <Badge
                variant={agent.is_enabled !== false ? "default" : "secondary"}
                className="text-xs"
              >
                {agent.is_enabled !== false ? "Active" : "Disabled"}
              </Badge>
            </div>
          </div>
        </div>
      }
      footer={actions.length > 0 ? <ActionBar actions={actions} /> : undefined}
    >
      <div className="space-y-3">
        {/* Description */}
        {agent.description && (
          <p className="text-sm text-muted-foreground">{agent.description}</p>
        )}

        {/* Model */}
        {displayModel && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Model</span>
            <span className="font-medium">{displayModel}</span>
          </div>
        )}

        {/* Participation Mode */}
        {agent.participation_mode && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Mode</span>
            <span className="font-medium">
              {modeLabels[agent.participation_mode] || agent.participation_mode}
            </span>
          </div>
        )}

        {/* Capabilities */}
        {agent.capabilities && agent.capabilities.length > 0 && (
          <div className="pt-2 border-t border-border">
            <p className="text-xs text-muted-foreground mb-2">Capabilities</p>
            <div className="flex flex-wrap gap-1">
              {agent.capabilities.map((cap) => (
                <Badge key={cap} variant="outline" className="text-xs">
                  {cap}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </div>
    </EntityCardPopover>
  )
}
```

**Step 2: Create cards barrel export**

Create `frontend/src/components/Room/cards/index.ts`:
```typescript
export { EntityCardPopover } from "./EntityCardPopover"
export { AgentCardPopover, type AgentCardData } from "./AgentCardPopover"
```

**Step 3: Verify no TypeScript errors**

```bash
cd /home/josep/dog/frontend && npm run lint
```

**Step 4: Commit**

```bash
git add frontend/src/components/Room/cards/
git commit -m "feat(room): add AgentCardPopover with theme tokens"
```

---

### Task 18: Create UserCardPopover

**Files:**
- Create: `frontend/src/components/Room/cards/UserCardPopover.tsx`
- Modify: `frontend/src/components/Room/cards/index.ts`

**Step 1: Create UserCardPopover component**

```typescript
/**
 * UserCardPopover
 *
 * Popover showing user details when triggered from participant UI.
 * Uses semantic --user-accent color token for theming.
 *
 * @example Integration from ParticipantStack
 * ```tsx
 * <UserCardPopover
 *   user={userData}
 *   trigger={<Avatar ... />}
 * />
 * ```
 */

import * as React from "react"
import { User, Mail, Shield, Clock } from "lucide-react"
import { EntityCardPopover } from "./EntityCardPopover"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { getInitials } from "@/utils"

export interface UserCardData {
  id: string
  name: string
  email?: string
  role?: "owner" | "member" | "viewer"
  joined_at?: string
  is_active?: boolean
}

interface UserCardPopoverProps {
  /** User data to display */
  user: UserCardData
  /** Element that triggers the popover */
  trigger: React.ReactNode
  /** Popover alignment */
  align?: "start" | "center" | "end"
}

const roleLabels: Record<string, string> = {
  owner: "Room Owner",
  member: "Member",
  viewer: "Viewer",
}

export function UserCardPopover({
  user,
  trigger,
  align = "start",
}: UserCardPopoverProps) {
  const formattedJoinDate = user.joined_at
    ? new Date(user.joined_at).toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        year: "numeric",
      })
    : null

  return (
    <EntityCardPopover
      trigger={trigger}
      align={align}
      header={
        <div className="flex items-center gap-3">
          <Avatar className="h-12 w-12 border-2 border-[hsl(var(--user-accent)/0.3)]">
            <AvatarFallback className="bg-[hsl(var(--user-accent)/0.15)] text-[hsl(var(--user-accent))]">
              {getInitials(user.name)}
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <h4 className="font-semibold truncate">{user.name}</h4>
            <div className="flex items-center gap-2 mt-1">
              {user.is_active !== false && (
                <span className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
                  <span className="h-2 w-2 rounded-full bg-green-500" />
                  Online
                </span>
              )}
            </div>
          </div>
        </div>
      }
    >
      <div className="space-y-3">
        {/* Email */}
        {user.email && (
          <div className="flex items-center gap-2 text-sm">
            <Mail className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground truncate">{user.email}</span>
          </div>
        )}

        {/* Role */}
        {user.role && (
          <div className="flex items-center gap-2 text-sm">
            <Shield className="h-4 w-4 text-muted-foreground" />
            <Badge variant="outline" className="text-xs">
              {roleLabels[user.role] || user.role}
            </Badge>
          </div>
        )}

        {/* Joined */}
        {formattedJoinDate && (
          <div className="flex items-center gap-2 text-sm">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">
              Joined {formattedJoinDate}
            </span>
          </div>
        )}
      </div>
    </EntityCardPopover>
  )
}
```

**Step 2: Update cards barrel export**

Add to `frontend/src/components/Room/cards/index.ts`:
```typescript
export { UserCardPopover, type UserCardData } from "./UserCardPopover"
```

**Step 3: Commit**

```bash
git add frontend/src/components/Room/cards/
git commit -m "feat(room): add UserCardPopover with theme tokens"
```

---

### Task 19: Create DocCardPopover

**Files:**
- Create: `frontend/src/components/Room/cards/DocCardPopover.tsx`
- Modify: `frontend/src/components/Room/cards/index.ts`

**Step 1: Create DocCardPopover component**

```typescript
/**
 * DocCardPopover
 *
 * Popover showing document/file details when triggered from references.
 * Uses semantic --doc-accent color token for theming.
 *
 * @example Integration from file reference
 * ```tsx
 * <DocCardPopover
 *   doc={docData}
 *   trigger={<span className="cursor-pointer">document.pdf</span>}
 *   onOpen={() => openDocument(id)}
 *   onDownload={() => downloadDocument(id)}
 * />
 * ```
 */

import * as React from "react"
import { FileText, Download, ExternalLink, Calendar, HardDrive } from "lucide-react"
import { EntityCardPopover } from "./EntityCardPopover"
import { ActionBar, type ActionItem } from "../primitives/ActionBar"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"

export interface DocCardData {
  id: string
  name: string
  type?: string
  size_bytes?: number
  created_at?: string
  preview_text?: string
}

interface DocCardPopoverProps {
  /** Document data to display */
  doc: DocCardData
  /** Element that triggers the popover */
  trigger: React.ReactNode
  /** Open document callback */
  onOpen?: () => void
  /** Download document callback */
  onDownload?: () => void
  /** Popover alignment */
  align?: "start" | "center" | "end"
}

function formatFileSize(bytes?: number): string {
  if (!bytes) return "Unknown size"
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function DocCardPopover({
  doc,
  trigger,
  onOpen,
  onDownload,
  align = "start",
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
      label: "Download document",
      onClick: onDownload,
    })
  }

  const formattedDate = doc.created_at
    ? new Date(doc.created_at).toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        year: "numeric",
      })
    : null

  return (
    <EntityCardPopover
      trigger={trigger}
      align={align}
      header={
        <div className="flex items-center gap-3">
          <Avatar className="h-12 w-12 border-2 border-[hsl(var(--doc-accent)/0.3)]">
            <AvatarFallback className="bg-[hsl(var(--doc-accent)/0.15)] text-[hsl(var(--doc-accent))]">
              <FileText className="h-6 w-6" />
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <h4 className="font-semibold truncate">{doc.name}</h4>
            {doc.type && (
              <Badge variant="outline" className="text-xs mt-1">
                {doc.type.toUpperCase()}
              </Badge>
            )}
          </div>
        </div>
      }
      footer={actions.length > 0 ? <ActionBar actions={actions} /> : undefined}
    >
      <div className="space-y-3">
        {/* Preview */}
        {doc.preview_text && (
          <div className="bg-muted rounded-md p-3">
            <p className="text-sm text-muted-foreground line-clamp-3">
              {doc.preview_text}
            </p>
          </div>
        )}

        {/* Metadata */}
        <div className="space-y-2 text-sm">
          {doc.size_bytes && (
            <div className="flex items-center gap-2">
              <HardDrive className="h-4 w-4 text-muted-foreground" />
              <span className="text-muted-foreground">
                {formatFileSize(doc.size_bytes)}
              </span>
            </div>
          )}

          {formattedDate && (
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <span className="text-muted-foreground">
                Created {formattedDate}
              </span>
            </div>
          )}
        </div>
      </div>
    </EntityCardPopover>
  )
}
```

**Step 2: Update cards barrel export**

Add to `frontend/src/components/Room/cards/index.ts`:
```typescript
export { DocCardPopover, type DocCardData } from "./DocCardPopover"
```

**Step 3: Update main Room barrel export**

Verify `frontend/src/components/Room/index.ts` includes:
```typescript
// Cards
export * from "./cards"
```

**Step 4: Commit**

```bash
git add frontend/src/components/Room/cards/
git commit -m "feat(room): add DocCardPopover with theme tokens"
```

---

## Phase 8: Additional Panels

### Task 20: Extract RoomDebugPanelContent

**Files:**
- Modify: `frontend/src/components/Rooms/RoomDebugPanel.tsx`

**Step 1: Extract content into a separate component**

Refactor `RoomDebugPanel.tsx` to separate the outer wrapper from the content:

```typescript
/**
 * RoomDebugPanel - Debug sidebar for room/agent debugging
 *
 * This file exports two components:
 * - RoomDebugPanelContent: The inner content (collapsible sections)
 * - RoomDebugPanel: The outer wrapper with aside styling (legacy)
 *
 * @see Room/panels/DebugPanel.tsx for the new panel wrapper
 */

// ... existing imports ...

interface RoomDebugPanelContentProps {
  messages: MessageViewModel[]
  streamingMessage: { agent_name: string; content: string } | null
  isConnected: boolean
  activeAgents: ParticipantViewModel[]
}

/**
 * Inner content of the debug panel - collapsible sections
 * Can be used standalone or wrapped by different containers
 */
export function RoomDebugPanelContent({
  messages,
  streamingMessage,
  isConnected,
  activeAgents,
}: RoomDebugPanelContentProps) {
  // ... move all the state and logic here ...
  // ... return everything EXCEPT the outer <aside> wrapper ...

  return (
    <div className="space-y-4">
      {/* Connection Status */}
      {/* ... all collapsible sections ... */}
      {/* Stats Footer */}
    </div>
  )
}

/**
 * Legacy wrapper - maintains backward compatibility
 * @deprecated Use DebugPanel from Room/panels for new code
 */
export default function RoomDebugPanel(props: RoomDebugPanelContentProps) {
  return (
    <aside className="bg-background border-border w-80 overflow-y-auto border-l p-4">
      <h3 className="text-sm font-semibold flex items-center gap-2 mb-4">
        <Bug className="h-4 w-4" />
        Debug Panel
      </h3>
      <RoomDebugPanelContent {...props} />
    </aside>
  )
}
```

**Step 2: Verify existing usages still work**

```bash
cd /home/josep/dog/frontend && npm run lint && npm run build
```

**Step 3: Commit**

```bash
git add frontend/src/components/Rooms/RoomDebugPanel.tsx
git commit -m "refactor(rooms): extract RoomDebugPanelContent for reuse"
```

---

### Task 21: Create DebugPanel

**Files:**
- Create: `frontend/src/components/Room/panels/DebugPanel.tsx`
- Modify: `frontend/src/components/Room/panels/index.ts`

**Step 1: Create DebugPanel wrapper**

```typescript
/**
 * DebugPanel
 *
 * Auxiliary panel for room/agent debugging.
 * Wraps RoomDebugPanelContent with PanelContainer.
 *
 * @example Room panel usage
 * ```tsx
 * <DebugPanel
 *   messages={messages}
 *   streamingMessage={streaming}
 *   isConnected={connected}
 *   activeAgents={agents}
 * />
 * ```
 *
 * @example Standalone page usage
 * ```tsx
 * <DebugPanel
 *   className="h-full"
 *   messages={messages}
 *   {...otherProps}
 * />
 * ```
 */

import * as React from "react"
import { Trash2 } from "lucide-react"
import { PanelContainer } from "../primitives/PanelContainer"
import { ActionBar, type ActionItem } from "../primitives/ActionBar"
import { RoomDebugPanelContent } from "@/components/Rooms/RoomDebugPanel"
import type {
  MessageViewModel,
  ParticipantViewModel,
} from "@/services/roomService"

interface DebugPanelProps {
  /** Messages to analyze */
  messages: MessageViewModel[]
  /** Current streaming message from agent */
  streamingMessage: { agent_name: string; content: string } | null
  /** WebSocket connection status */
  isConnected: boolean
  /** Active agents in room */
  activeAgents: ParticipantViewModel[]
  /** Hide panel header (when page provides its own) */
  hideHeader?: boolean
  /** Additional className */
  className?: string
}

export function DebugPanel({
  messages,
  streamingMessage,
  isConnected,
  activeAgents,
  hideHeader = false,
  className,
}: DebugPanelProps) {
  const headerActions: ActionItem[] = [
    {
      id: "clear",
      icon: Trash2,
      label: "Clear console",
      onClick: () => {
        // Clear is informational only - messages come from parent
        console.clear()
      },
    },
  ]

  if (hideHeader) {
    return (
      <div className={className}>
        <RoomDebugPanelContent
          messages={messages}
          streamingMessage={streamingMessage}
          isConnected={isConnected}
          activeAgents={activeAgents}
        />
      </div>
    )
  }

  return (
    <PanelContainer
      title="Debug"
      headerActions={<ActionBar actions={headerActions} />}
      className={className}
    >
      <div className="p-4">
        <RoomDebugPanelContent
          messages={messages}
          streamingMessage={streamingMessage}
          isConnected={isConnected}
          activeAgents={activeAgents}
        />
      </div>
    </PanelContainer>
  )
}
```

**Step 2: Update panels barrel export**

Add to `frontend/src/components/Room/panels/index.ts`:
```typescript
export { DebugPanel } from "./DebugPanel"
```

**Step 3: Commit**

```bash
git add frontend/src/components/Room/panels/
git commit -m "feat(room): add DebugPanel wrapping existing debug content"
```

---

### Task 22: Create StoryEditorPanel

**Files:**
- Create: `frontend/src/components/Room/panels/StoryEditorPanel.tsx`
- Modify: `frontend/src/components/Room/panels/index.ts`

**Step 1: Create StoryEditorPanel component**

```typescript
/**
 * StoryEditorPanel
 *
 * Primary panel for collaborative story editing within a room.
 * Wraps the existing StoryEditor components with panel-friendly interface.
 *
 * @example Room panel usage
 * ```tsx
 * <StoryEditorPanel
 *   storyId={storyId}
 *   onNavigateToStories={() => navigate({ to: "/stories" })}
 * />
 * ```
 *
 * @example Standalone page usage
 * ```tsx
 * <StoryEditorPanel
 *   storyId={storyId}
 *   className="h-full"
 *   hideHeader={false}
 * />
 * ```
 */

import * as React from "react"
import { useState } from "react"
import {
  AlertTriangle,
  CheckCircle,
  Copy,
  Eye,
  Loader2,
} from "lucide-react"
import { PanelContainer } from "../primitives/PanelContainer"
import { ActionBar, type ActionItem } from "../primitives/ActionBar"
import { PlaceholderContent } from "../primitives/PlaceholderContent"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable"
import { useStoryEditor } from "@/hooks/stories/useStoryEditor"
import { useCloneStory } from "@/hooks/stories/useStories"
import { usePublishWorkflow } from "@/hooks/stories/usePublishWorkflow"
import NodeTree from "@/components/Stories/StoryEditor/NodeTree/NodeTree"
import NodeEditor from "@/components/Stories/StoryEditor/NodeEditor/NodeEditor"
import StoryPreview from "@/components/Stories/StoryPlayer/StoryPreview"
import { PublishModal } from "@/components/Stories/PublishWorkflow"
import { StateSchemaSheet } from "@/components/Stories/StoryEditor/StateSchema"
import { BookOpen } from "lucide-react"

interface StoryEditorPanelProps {
  /** Story ID to edit */
  storyId: string
  /** Hide panel header (when page provides its own) */
  hideHeader?: boolean
  /** Additional header actions to merge */
  additionalActions?: ActionItem[]
  /** Additional className */
  className?: string
  /** Callback when user wants to navigate to stories list */
  onNavigateToStories?: () => void
  /** Callback for fullscreen preview mode */
  onPreviewFullscreen?: () => void
}

export function StoryEditorPanel({
  storyId,
  hideHeader = false,
  additionalActions = [],
  className,
  onNavigateToStories,
  onPreviewFullscreen,
}: StoryEditorPanelProps) {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [isPreviewMode, setIsPreviewMode] = useState(false)
  const [showPublishDialog, setShowPublishDialog] = useState(false)

  const { story, nodes, choices, isLoading, error, validateForPublish } =
    useStoryEditor({ storyId })

  const { unpublish, isUnpublishing } = usePublishWorkflow({ storyId })
  const cloneMutation = useCloneStory()

  // Loading state
  if (isLoading) {
    return (
      <PanelContainer title="Story Editor" className={className}>
        <div className="flex items-center justify-center h-full">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </PanelContainer>
    )
  }

  // Error state
  if (error || !story) {
    return (
      <PanelContainer title="Story Editor" className={className}>
        <PlaceholderContent
          icon={BookOpen}
          title="Story not found"
          description={error?.message || "Unable to load story"}
          action={
            onNavigateToStories && (
              <Button variant="outline" onClick={onNavigateToStories}>
                Back to Stories
              </Button>
            )
          }
        />
      </PanelContainer>
    )
  }

  const validation = validateForPublish()
  const needsPublish =
    !story.is_published ||
    (story.published_version !== null &&
      story.current_version > story.published_version)

  // Preview mode (inline, not fullscreen)
  if (isPreviewMode) {
    return (
      <PanelContainer
        title="Story Preview"
        headerActions={
          <Button size="sm" variant="ghost" onClick={() => setIsPreviewMode(false)}>
            Exit Preview
          </Button>
        }
        className={className}
      >
        <StoryPreview
          story={story}
          nodes={nodes}
          choices={choices}
          onExit={() => setIsPreviewMode(false)}
        />
      </PanelContainer>
    )
  }

  // Build header actions
  const headerActions: ActionItem[] = [
    {
      id: "preview",
      icon: Eye,
      label: "Preview story",
      onClick: () => setIsPreviewMode(true),
    },
    {
      id: "clone",
      icon: Copy,
      label: "Clone story",
      onClick: async () => {
        const cloned = await cloneMutation.mutateAsync({
          title: story.title,
          description: story.description,
        })
        // Parent can handle navigation if needed
      },
      disabled: cloneMutation.isPending,
    },
    ...additionalActions,
  ]

  // Build title with status
  const titleContent = (
    <div className="flex items-center gap-2">
      <span>{story.title}</span>
      <Badge variant="outline" className="text-xs">
        v{story.current_version}
      </Badge>
      {story.is_published && (
        <Badge variant="default" className="text-xs">
          Published
        </Badge>
      )}
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <div>
              {validation.isValid ? (
                <CheckCircle className="h-4 w-4 text-green-500" />
              ) : (
                <AlertTriangle className="h-4 w-4 text-yellow-500" />
              )}
            </div>
          </TooltipTrigger>
          <TooltipContent>
            {validation.isValid ? "Ready to publish" : "Has validation issues"}
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </div>
  )

  if (hideHeader) {
    return (
      <div className={className}>
        <ResizablePanelGroup direction="horizontal">
          <ResizablePanel defaultSize={30} minSize={20}>
            <NodeTree
              nodes={nodes}
              choices={choices}
              selectedNodeId={selectedNodeId}
              onSelectNode={setSelectedNodeId}
              storyId={storyId}
              storyVersion={story.current_version}
            />
          </ResizablePanel>
          <ResizableHandle withHandle />
          <ResizablePanel defaultSize={70} minSize={40}>
            <NodeEditor
              nodeId={selectedNodeId}
              storyId={storyId}
              storyVersion={story.current_version}
              availableNodes={nodes}
            />
          </ResizablePanel>
        </ResizablePanelGroup>
      </div>
    )
  }

  return (
    <PanelContainer
      title={titleContent}
      headerActions={
        <div className="flex items-center gap-2">
          <ActionBar actions={headerActions} />
          <StateSchemaSheet
            storyId={storyId}
            version={story.current_version}
            isPublished={story.is_published}
            publishedVersion={story.published_version}
          />
          {needsPublish ? (
            <>
              <Button size="sm" onClick={() => setShowPublishDialog(true)}>
                Publish
              </Button>
              <PublishModal
                storyId={storyId}
                isOpen={showPublishDialog}
                onClose={() => setShowPublishDialog(false)}
              />
            </>
          ) : story.is_published ? (
            <Button
              size="sm"
              variant="outline"
              onClick={unpublish}
              disabled={isUnpublishing}
            >
              {isUnpublishing ? "..." : "Unpublish"}
            </Button>
          ) : null}
        </div>
      }
      className={className}
      scrollable={false}
    >
      <ResizablePanelGroup direction="horizontal" className="h-full">
        <ResizablePanel defaultSize={30} minSize={20}>
          <div className="h-full overflow-y-auto bg-muted/30">
            <NodeTree
              nodes={nodes}
              choices={choices}
              selectedNodeId={selectedNodeId}
              onSelectNode={setSelectedNodeId}
              storyId={storyId}
              storyVersion={story.current_version}
            />
          </div>
        </ResizablePanel>
        <ResizableHandle withHandle />
        <ResizablePanel defaultSize={70} minSize={40}>
          <div className="h-full overflow-y-auto">
            <NodeEditor
              nodeId={selectedNodeId}
              storyId={storyId}
              storyVersion={story.current_version}
              availableNodes={nodes}
            />
          </div>
        </ResizablePanel>
      </ResizablePanelGroup>
    </PanelContainer>
  )
}
```

**Step 2: Update panels barrel export**

Add to `frontend/src/components/Room/panels/index.ts`:
```typescript
export { StoryEditorPanel } from "./StoryEditorPanel"
```

**Step 3: Verify no TypeScript errors**

```bash
cd /home/josep/dog/frontend && npm run lint
```

**Step 4: Commit**

```bash
git add frontend/src/components/Room/panels/
git commit -m "feat(room): add StoryEditorPanel for story editing in rooms"
```

---

### Task 23: Create CanvasPanel Placeholder

**Files:**
- Create: `frontend/src/components/Room/panels/CanvasPanel.tsx`
- Modify: `frontend/src/components/Room/panels/index.ts`

**Step 1: Create CanvasPanel placeholder**

```typescript
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

import * as React from "react"
import { Paintbrush } from "lucide-react"
import { PanelContainer } from "../primitives/PanelContainer"
import { PlaceholderContent } from "../primitives/PlaceholderContent"

interface CanvasPanelProps {
  /** Hide panel header */
  hideHeader?: boolean
  /** Additional className */
  className?: string
}

export function CanvasPanel({ hideHeader = false, className }: CanvasPanelProps) {
  const content = (
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
      {content}
    </PanelContainer>
  )
}
```

**Step 2: Update panels barrel export**

Add to `frontend/src/components/Room/panels/index.ts`:
```typescript
export { CanvasPanel } from "./CanvasPanel"
```

**Step 3: Commit**

```bash
git add frontend/src/components/Room/panels/
git commit -m "feat(room): add CanvasPanel placeholder"
```

---

### Task 24: Create A2UIPanel Placeholder

**Files:**
- Create: `frontend/src/components/Room/panels/A2UIPanel.tsx`
- Modify: `frontend/src/components/Room/panels/index.ts`

**Step 1: Create A2UIPanel placeholder**

```typescript
/**
 * A2UIPanel
 *
 * Primary panel for AGUI agent tool call rendering.
 * Currently a placeholder - will integrate AgentUIRenderer.
 *
 * @example Room panel usage
 * ```tsx
 * <A2UIPanel roomId={roomId} />
 * ```
 *
 * @example Standalone page usage
 * ```tsx
 * <A2UIPanel roomId={roomId} className="h-full" />
 * ```
 */

import * as React from "react"
import { Blocks } from "lucide-react"
import { PanelContainer } from "../primitives/PanelContainer"
import { PlaceholderContent } from "../primitives/PlaceholderContent"

interface A2UIPanelProps {
  /** Room ID for context */
  roomId?: string
  /** Hide panel header */
  hideHeader?: boolean
  /** Additional className */
  className?: string
}

export function A2UIPanel({ roomId, hideHeader = false, className }: A2UIPanelProps) {
  const content = (
    <PlaceholderContent
      icon={Blocks}
      title="Agent UI"
      description="Structured UI components from agent tool calls will render here. Coming soon."
    />
  )

  if (hideHeader) {
    return <div className={className}>{content}</div>
  }

  return (
    <PanelContainer title="Agent UI" className={className}>
      {content}
    </PanelContainer>
  )
}
```

**Step 2: Update panels barrel export**

Add to `frontend/src/components/Room/panels/index.ts`:
```typescript
export { A2UIPanel } from "./A2UIPanel"
```

**Step 3: Final panels index should look like:**

```typescript
export { ChatPanel } from "./ChatPanel"
export { AgentPanel } from "./AgentPanel"
export { DebugPanel } from "./DebugPanel"
export { StoryEditorPanel } from "./StoryEditorPanel"
export { CanvasPanel } from "./CanvasPanel"
export { A2UIPanel } from "./A2UIPanel"
```

**Step 4: Commit**

```bash
git add frontend/src/components/Room/panels/
git commit -m "feat(room): add A2UIPanel placeholder"
```

---

## Phase 9: Backend Panel Persistence

### Task 25: Create Panel Config Models

**Files:**
- Modify: `backend/app/models.py`

**Step 1: Add panel config models**

Add to `backend/app/models.py`:

```python
# =============================================================================
# Room Panel Configuration
# =============================================================================

class PanelConfigItem(SQLModel):
    """Individual panel configuration"""
    id: str
    kind: str  # chat, storyEditor, agentPanel, debug, canvas, a2ui
    prominence: str  # primary, auxiliary


class RoomPanelDefaultsBase(SQLModel):
    """Base properties for room panel defaults"""
    panels: list[dict] = Field(default=[], sa_column=Column(JSON))


class RoomPanelDefaults(RoomPanelDefaultsBase, table=True):
    """Default panel configuration set by room owner"""
    __tablename__ = "room_panel_defaults"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    room_id: uuid.UUID = Field(foreign_key="room.id", unique=True, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship
    room: "Room" = Relationship(back_populates="panel_defaults")


class RoomPanelDefaultsPublic(RoomPanelDefaultsBase):
    """Public response for room panel defaults"""
    id: uuid.UUID
    room_id: uuid.UUID
    updated_at: datetime


class UserRoomPanelConfigBase(SQLModel):
    """Base properties for user room panel config"""
    panels: list[dict] | None = Field(default=None, sa_column=Column(JSON))
    use_room_defaults: bool = Field(default=True)


class UserRoomPanelConfig(UserRoomPanelConfigBase, table=True):
    """User's personal panel override for a specific room"""
    __tablename__ = "user_room_panel_config"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    room_id: uuid.UUID = Field(foreign_key="room.id", index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Composite unique constraint
    __table_args__ = (UniqueConstraint("user_id", "room_id"),)


class UserRoomPanelConfigPublic(UserRoomPanelConfigBase):
    """Public response for user panel config"""
    id: uuid.UUID
    user_id: uuid.UUID
    room_id: uuid.UUID
    updated_at: datetime


class ResolvedPanelConfig(SQLModel):
    """Resolved panel config for a user in a room"""
    panels: list[dict]
    source: str  # "user_override", "room_defaults", "type_defaults"
```

**Step 2: Add relationship to Room model**

Find the Room model and add:
```python
class Room(...):
    # ... existing fields ...

    # Panel defaults (one-to-one)
    panel_defaults: "RoomPanelDefaults" | None = Relationship(
        back_populates="room",
        sa_relationship_kwargs={"uselist": False}
    )
```

**Step 3: Create migration**

```bash
cd /home/josep/dog/backend
alembic revision --autogenerate -m "Add room panel configuration tables"
```

**Step 4: Review and apply migration**

Review the generated migration file, then:
```bash
alembic upgrade head
```

**Step 5: Commit**

```bash
git add backend/app/models.py backend/app/alembic/versions/
git commit -m "feat(models): add room panel configuration models"
```

---

### Task 26: Create Panel Config CRUD

**Files:**
- Create: `backend/app/crud_panels.py`

**Step 1: Create CRUD functions**

```python
"""
CRUD operations for room panel configuration.
"""

from uuid import UUID
from datetime import datetime
from sqlmodel import Session, select

from app.models import (
    Room,
    RoomPanelDefaults,
    UserRoomPanelConfig,
)

# Default panel configs by room type
DEFAULT_PANELS = {
    "chat": [
        {"id": "chat", "kind": "chat", "prominence": "primary"},
        {"id": "agents", "kind": "agentPanel", "prominence": "auxiliary"},
    ],
    "story": [
        {"id": "story", "kind": "storyEditor", "prominence": "primary"},
        {"id": "chat", "kind": "chat", "prominence": "primary"},
        {"id": "agents", "kind": "agentPanel", "prominence": "auxiliary"},
    ],
    "workspace": [],
}


def get_room_panel_defaults(
    session: Session, room_id: UUID
) -> RoomPanelDefaults | None:
    """Get room's default panel configuration."""
    statement = select(RoomPanelDefaults).where(
        RoomPanelDefaults.room_id == room_id
    )
    return session.exec(statement).first()


def set_room_panel_defaults(
    session: Session, room_id: UUID, panels: list[dict]
) -> RoomPanelDefaults:
    """Set or update room's default panel configuration."""
    existing = get_room_panel_defaults(session, room_id)

    if existing:
        existing.panels = panels
        existing.updated_at = datetime.utcnow()
        session.add(existing)
    else:
        existing = RoomPanelDefaults(
            room_id=room_id,
            panels=panels,
        )
        session.add(existing)

    session.commit()
    session.refresh(existing)
    return existing


def get_user_room_panel_config(
    session: Session, user_id: UUID, room_id: UUID
) -> UserRoomPanelConfig | None:
    """Get user's panel config override for a room."""
    statement = select(UserRoomPanelConfig).where(
        UserRoomPanelConfig.user_id == user_id,
        UserRoomPanelConfig.room_id == room_id,
    )
    return session.exec(statement).first()


def set_user_room_panel_config(
    session: Session,
    user_id: UUID,
    room_id: UUID,
    panels: list[dict] | None,
    use_room_defaults: bool,
) -> UserRoomPanelConfig:
    """Set or update user's panel config for a room."""
    existing = get_user_room_panel_config(session, user_id, room_id)

    if existing:
        existing.panels = panels
        existing.use_room_defaults = use_room_defaults
        existing.updated_at = datetime.utcnow()
        session.add(existing)
    else:
        existing = UserRoomPanelConfig(
            user_id=user_id,
            room_id=room_id,
            panels=panels,
            use_room_defaults=use_room_defaults,
        )
        session.add(existing)

    session.commit()
    session.refresh(existing)
    return existing


def resolve_panels_for_user(
    session: Session, user_id: UUID, room_id: UUID
) -> tuple[list[dict], str]:
    """
    Resolve the effective panel configuration for a user in a room.

    Returns: (panels, source) where source is one of:
        - "user_override": User has custom config
        - "room_defaults": Using room owner's defaults
        - "type_defaults": Using built-in type defaults
    """
    # Check for user override
    user_config = get_user_room_panel_config(session, user_id, room_id)
    if user_config and not user_config.use_room_defaults and user_config.panels:
        return user_config.panels, "user_override"

    # Check for room defaults
    room_defaults = get_room_panel_defaults(session, room_id)
    if room_defaults and room_defaults.panels:
        return room_defaults.panels, "room_defaults"

    # Fall back to type defaults
    room = session.get(Room, room_id)
    room_type = getattr(room, "type", "chat") if room else "chat"
    return DEFAULT_PANELS.get(room_type, DEFAULT_PANELS["chat"]), "type_defaults"
```

**Step 2: Commit**

```bash
git add backend/app/crud_panels.py
git commit -m "feat(crud): add panel configuration CRUD operations"
```

---

### Task 27: Create Panel Config Routes

**Files:**
- Create: `backend/app/api/routes/room_panels.py`
- Modify: `backend/app/api/main.py`

**Step 1: Create routes**

```python
"""
API routes for room panel configuration.
"""

from uuid import UUID
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, SessionDep
from app.crud_panels import (
    get_room_panel_defaults,
    set_room_panel_defaults,
    get_user_room_panel_config,
    set_user_room_panel_config,
    resolve_panels_for_user,
)
from app.models import (
    Room,
    RoomPanelDefaultsPublic,
    UserRoomPanelConfigPublic,
    ResolvedPanelConfig,
)
from app.crud import get_room_participant

router = APIRouter()


@router.get("/{room_id}/panels", response_model=ResolvedPanelConfig)
def get_resolved_panels(
    room_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Get resolved panel configuration for current user.
    Returns the effective panels based on user override or room/type defaults.
    """
    # Verify room exists and user has access
    room = session.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    panels, source = resolve_panels_for_user(session, current_user.id, room_id)
    return ResolvedPanelConfig(panels=panels, source=source)


@router.get("/{room_id}/panels/defaults", response_model=RoomPanelDefaultsPublic | None)
def get_room_defaults(
    room_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Get room's default panel configuration (set by owner)."""
    room = session.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    return get_room_panel_defaults(session, room_id)


@router.put("/{room_id}/panels/defaults", response_model=RoomPanelDefaultsPublic)
def update_room_defaults(
    room_id: UUID,
    panels: list[dict],
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Update room's default panel configuration.
    Only room owner can modify.
    """
    room = session.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Check ownership
    participant = get_room_participant(session, room_id, current_user.id)
    if not participant or participant.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only room owner can set default panels",
        )

    return set_room_panel_defaults(session, room_id, panels)


@router.get("/{room_id}/panels/me", response_model=UserRoomPanelConfigPublic | None)
def get_my_panel_config(
    room_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Get current user's panel configuration override for this room."""
    room = session.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    return get_user_room_panel_config(session, current_user.id, room_id)


@router.put("/{room_id}/panels/me", response_model=UserRoomPanelConfigPublic)
def update_my_panel_config(
    room_id: UUID,
    panels: list[dict] | None,
    use_room_defaults: bool,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Update current user's panel configuration for this room."""
    room = session.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    return set_user_room_panel_config(
        session, current_user.id, room_id, panels, use_room_defaults
    )
```

**Step 2: Register router in main.py**

Add to `backend/app/api/main.py`:
```python
from app.api.routes import room_panels

api_router.include_router(
    room_panels.router,
    prefix="/rooms",
    tags=["room-panels"],
)
```

**Step 3: Verify backend runs**

```bash
cd /home/josep/dog/backend && fastapi dev app/main.py
```

Check `/docs` for new endpoints.

**Step 4: Commit**

```bash
git add backend/app/api/routes/room_panels.py backend/app/api/main.py
git commit -m "feat(api): add room panel configuration endpoints"
```

---

### Task 28: Create Frontend Panel Service

**Files:**
- Create: `frontend/src/services/panelService.ts`

**Step 1: Regenerate API client**

```bash
cd /home/josep/dog/frontend && npm run generate-client
```

**Step 2: Create panel service**

```typescript
/**
 * Panel Configuration Service
 *
 * Manages room panel configuration - resolving, updating,
 * and managing user overrides vs room defaults.
 */

import {
  RoomPanelsService,
  type ResolvedPanelConfig,
  type RoomPanelDefaultsPublic,
  type UserRoomPanelConfigPublic,
} from "@/client/sdk.gen"

// Re-export types for convenience
export type { ResolvedPanelConfig, RoomPanelDefaultsPublic, UserRoomPanelConfigPublic }

export interface PanelConfig {
  id: string
  kind: string
  prominence: "primary" | "auxiliary"
}

/**
 * Get resolved panel configuration for current user
 */
export async function getResolvedPanels(roomId: string): Promise<ResolvedPanelConfig> {
  const response = await RoomPanelsService.getResolvedPanels({ roomId })
  return response
}

/**
 * Get room's default panel configuration
 */
export async function getRoomPanelDefaults(
  roomId: string
): Promise<RoomPanelDefaultsPublic | null> {
  const response = await RoomPanelsService.getRoomDefaults({ roomId })
  return response
}

/**
 * Update room's default panel configuration (owner only)
 */
export async function updateRoomPanelDefaults(
  roomId: string,
  panels: PanelConfig[]
): Promise<RoomPanelDefaultsPublic> {
  const response = await RoomPanelsService.updateRoomDefaults({
    roomId,
    requestBody: panels,
  })
  return response
}

/**
 * Get current user's panel config override
 */
export async function getMyPanelConfig(
  roomId: string
): Promise<UserRoomPanelConfigPublic | null> {
  const response = await RoomPanelsService.getMyPanelConfig({ roomId })
  return response
}

/**
 * Update current user's panel config
 */
export async function updateMyPanelConfig(
  roomId: string,
  panels: PanelConfig[] | null,
  useRoomDefaults: boolean
): Promise<UserRoomPanelConfigPublic> {
  const response = await RoomPanelsService.updateMyPanelConfig({
    roomId,
    panels,
    useRoomDefaults,
  })
  return response
}
```

**Step 3: Commit**

```bash
git add frontend/src/services/panelService.ts frontend/src/client/
git commit -m "feat(frontend): add panel configuration service"
```

---

### Task 29: Create useRoomPanels Hook

**Files:**
- Create: `frontend/src/hooks/useRoomPanels.ts`

**Step 1: Create hook**

```typescript
/**
 * useRoomPanels Hook
 *
 * Manages room panel configuration with React Query.
 * Handles resolving, updating, and toggling between
 * room defaults and user overrides.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import {
  getResolvedPanels,
  getRoomPanelDefaults,
  updateRoomPanelDefaults,
  getMyPanelConfig,
  updateMyPanelConfig,
  type PanelConfig,
} from "@/services/panelService"

interface UseRoomPanelsOptions {
  /** Whether to fetch panel config */
  enabled?: boolean
}

export function useRoomPanels(roomId: string, options: UseRoomPanelsOptions = {}) {
  const { enabled = true } = options
  const queryClient = useQueryClient()

  // Resolved panels for current user
  const resolvedQuery = useQuery({
    queryKey: ["rooms", roomId, "panels"],
    queryFn: () => getResolvedPanels(roomId),
    enabled,
  })

  // Room defaults (for owner editing)
  const defaultsQuery = useQuery({
    queryKey: ["rooms", roomId, "panels", "defaults"],
    queryFn: () => getRoomPanelDefaults(roomId),
    enabled,
  })

  // User's personal config
  const myConfigQuery = useQuery({
    queryKey: ["rooms", roomId, "panels", "me"],
    queryFn: () => getMyPanelConfig(roomId),
    enabled,
  })

  // Update room defaults (owner)
  const updateDefaultsMutation = useMutation({
    mutationFn: (panels: PanelConfig[]) =>
      updateRoomPanelDefaults(roomId, panels),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rooms", roomId, "panels"] })
    },
  })

  // Update user's config
  const updateMyConfigMutation = useMutation({
    mutationFn: ({
      panels,
      useRoomDefaults,
    }: {
      panels: PanelConfig[] | null
      useRoomDefaults: boolean
    }) => updateMyPanelConfig(roomId, panels, useRoomDefaults),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rooms", roomId, "panels"] })
    },
  })

  return {
    // Resolved panels
    panels: (resolvedQuery.data?.panels || []) as PanelConfig[],
    panelSource: resolvedQuery.data?.source,
    isLoading: resolvedQuery.isLoading,
    error: resolvedQuery.error,

    // Room defaults
    roomDefaults: defaultsQuery.data,
    isLoadingDefaults: defaultsQuery.isLoading,

    // User config
    myConfig: myConfigQuery.data,
    isUsingRoomDefaults: myConfigQuery.data?.use_room_defaults ?? true,

    // Mutations
    updateRoomDefaults: updateDefaultsMutation.mutate,
    isUpdatingDefaults: updateDefaultsMutation.isPending,

    updateMyConfig: updateMyConfigMutation.mutate,
    isUpdatingMyConfig: updateMyConfigMutation.isPending,

    // Convenience methods
    setUseRoomDefaults: (useDefaults: boolean) => {
      updateMyConfigMutation.mutate({
        panels: myConfigQuery.data?.panels || null,
        useRoomDefaults: useDefaults,
      })
    },

    setCustomPanels: (panels: PanelConfig[]) => {
      updateMyConfigMutation.mutate({
        panels,
        useRoomDefaults: false,
      })
    },
  }
}
```

**Step 2: Commit**

```bash
git add frontend/src/hooks/useRoomPanels.ts
git commit -m "feat(hooks): add useRoomPanels hook for panel management"
```

---

## Phase 10: Integration & Verification

### Task 30: Update Room Route to Use Panel Config

**Files:**
- Modify: `frontend/src/routes/_layout/r.$roomId.tsx`

**Step 1: Integrate useRoomPanels**

Update the room route to use the panel configuration:

```typescript
// Add import
import { useRoomPanels } from "@/hooks/useRoomPanels"
import { DebugPanel, StoryEditorPanel, CanvasPanel, A2UIPanel } from "@/components/Room"

// In RoomView component, add:
const {
  panels: panelConfigs,
  panelSource,
  isLoading: isLoadingPanels,
} = useRoomPanels(roomId)

// Update the panels array builder to use config:
const panelComponents: Record<string, () => React.ReactNode> = {
  chat: () => (
    <ChatPanel
      roomId={roomId}
      messages={messages}
      // ... all existing props
    />
  ),
  agentPanel: () => (
    <AgentPanel
      roomAgents={roomAgentsAsAgentData}
      // ... all existing props
    />
  ),
  debug: () => (
    <DebugPanel
      messages={messages}
      streamingMessage={streamingMessage}
      isConnected={isConnected}
      activeAgents={activeAgents}
    />
  ),
  storyEditor: () => (
    <StoryEditorPanel
      storyId={room?.story_id || ""}
      onNavigateToStories={() => navigate({ to: "/stories" })}
    />
  ),
  canvas: () => <CanvasPanel />,
  a2ui: () => <A2UIPanel roomId={roomId} />,
}

// Build panels from config
const panels: PanelConfig[] = panelConfigs.map((config) => ({
  id: config.id,
  kind: config.kind,
  prominence: config.prominence as "primary" | "auxiliary",
  title: config.kind.charAt(0).toUpperCase() + config.kind.slice(1),
  render: panelComponents[config.kind] || (() => null),
}))
```

**Step 2: Verify integration works**

```bash
cd /home/josep/dog/frontend && npm run dev
```

Navigate to a room, verify panels render from config.

**Step 3: Commit**

```bash
git add frontend/src/routes/_layout/r.\$roomId.tsx
git commit -m "feat(room): integrate panel configuration into room route"
```

---

### Task 31: Full Build and Test

**Step 1: Run backend tests**

```bash
cd /home/josep/dog/backend && pytest app/tests/ -v
```

**Step 2: Run frontend linter and build**

```bash
cd /home/josep/dog/frontend && npm run lint && npm run build
```

**Step 3: Manual verification checklist**

- [ ] Navigate to /rooms → room list displays
- [ ] Click room → navigates to /r/:roomId
- [ ] Panels render from configuration
- [ ] Cards show on participant click (if integrated)
- [ ] Debug panel shows correct data
- [ ] Story editor panel loads (if story room)
- [ ] Placeholder panels show coming soon message
- [ ] Theme colors apply correctly (agent/user accents)

**Step 4: Final commit if fixes needed**

```bash
git add -A
git commit -m "chore: phase 2 verification and fixes"
```

---

## Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| 6 | 14-15 | Theme tokens and PlaceholderContent primitive |
| 7 | 16-19 | Entity cards (Agent, User, Doc) with theming |
| 8 | 20-24 | Additional panels (Debug, StoryEditor, Canvas, A2UI) |
| 9 | 25-29 | Backend panel persistence with room defaults + user overrides |
| 10 | 30-31 | Integration and verification |

**Total: 18 tasks (Tasks 14-31)**

**Files Created:** ~15
**Files Modified:** ~8

**Key Deliverables:**
- Entity card popovers with semantic theming
- Portable panels (room, standalone, embedded)
- Backend panel persistence with user overrides
- Full integration with existing room system
