# Rooms UI Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the flexible multi-panel room system defined in `2026-01-19-rooms-ui-design.md`.

**Architecture:** Build from primitives up - create atomic components first, then compose into panels, then wire into layout system and route. Reuse existing hooks (`useRoom`, `useRoomStream`) and adapt existing components (`MessageList`, `MessageInput`).

**Tech Stack:** React 19, TypeScript, TanStack Router, TanStack Query, shadcn/ui (resizable, tabs, popover), Lucide React

**Design Reference:** `frontend/docs/plans/2026-01-19-rooms-ui-design.md`

---

## Phase 1: Foundation - Primitives & Panel Container

### Task 1: Create Room Directory Structure

**Files:**
- Create: `frontend/src/components/Room/index.ts`
- Create: `frontend/src/components/Room/primitives/index.ts`
- Create: `frontend/src/components/Room/panels/index.ts`
- Create: `frontend/src/components/Room/cards/index.ts`

**Step 1: Create directory structure**

```bash
mkdir -p frontend/src/components/Room/primitives
mkdir -p frontend/src/components/Room/panels
mkdir -p frontend/src/components/Room/cards
```

**Step 2: Create barrel exports**

Create `frontend/src/components/Room/index.ts`:
```typescript
/**
 * Room Component System
 *
 * Unified room system with multi-panel support.
 * See: docs/plans/2026-01-19-rooms-ui-design.md
 */

// Primitives
export * from "./primitives"

// Panels
export * from "./panels"

// Cards
export * from "./cards"

// Main components (added in later tasks)
// export { RoomShell } from "./RoomShell"
// export { RoomHeader } from "./RoomHeader"
// export { RoomLayout } from "./RoomLayout"
```

Create `frontend/src/components/Room/primitives/index.ts`:
```typescript
export { PanelContainer } from "./PanelContainer"
export { ActionBar } from "./ActionBar"
export { ParticipantStack } from "./ParticipantStack"
```

Create `frontend/src/components/Room/panels/index.ts`:
```typescript
// Panels will be exported here as created
```

Create `frontend/src/components/Room/cards/index.ts`:
```typescript
// Cards will be exported here as created
```

**Step 3: Commit**

```bash
git add frontend/src/components/Room/
git commit -m "chore(room): create Room component directory structure"
```

---

### Task 2: Create PanelContainer Primitive

**Files:**
- Create: `frontend/src/components/Room/primitives/PanelContainer.tsx`

**Step 1: Create PanelContainer component**

```typescript
/**
 * PanelContainer Primitive
 *
 * Standard container for all room panels.
 * Provides consistent header/content/footer structure.
 */

import * as React from "react"
import { cn } from "@/lib/utils"

interface PanelContainerProps {
  /** Panel title displayed in header */
  title?: string
  /** Optional header actions (right side) */
  headerActions?: React.ReactNode
  /** Optional footer content */
  footer?: React.ReactNode
  /** Main content */
  children: React.ReactNode
  /** Additional className for the container */
  className?: string
  /** Whether content area should scroll */
  scrollable?: boolean
}

export function PanelContainer({
  title,
  headerActions,
  footer,
  children,
  className,
  scrollable = true,
}: PanelContainerProps) {
  return (
    <div className={cn("flex flex-col h-full bg-background", className)}>
      {/* Header */}
      {(title || headerActions) && (
        <div className="flex items-center justify-between px-4 py-3 border-b border-border shrink-0">
          {title && (
            <h3 className="text-sm font-medium text-foreground">{title}</h3>
          )}
          {headerActions && (
            <div className="flex items-center gap-2">{headerActions}</div>
          )}
        </div>
      )}

      {/* Content */}
      <div
        className={cn(
          "flex-1 min-h-0",
          scrollable && "overflow-y-auto"
        )}
      >
        {children}
      </div>

      {/* Footer */}
      {footer && (
        <div className="shrink-0 border-t border-border">{footer}</div>
      )}
    </div>
  )
}
```

**Step 2: Verify no TypeScript errors**

Run: `cd /home/josep/dog/frontend && npm run lint -- --filter=src/components/Room/`
Expected: No errors (or only pre-existing unrelated errors)

**Step 3: Commit**

```bash
git add frontend/src/components/Room/primitives/PanelContainer.tsx
git commit -m "feat(room): add PanelContainer primitive"
```

---

### Task 3: Create ActionBar Primitive

**Files:**
- Create: `frontend/src/components/Room/primitives/ActionBar.tsx`

**Step 1: Create ActionBar component**

```typescript
/**
 * ActionBar Primitive
 *
 * Horizontal row of icon buttons for panel headers and footers.
 */

import * as React from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import type { LucideIcon } from "lucide-react"

export interface ActionItem {
  /** Unique identifier */
  id: string
  /** Icon component */
  icon: LucideIcon
  /** Tooltip label */
  label: string
  /** Click handler */
  onClick: () => void
  /** Whether action is disabled */
  disabled?: boolean
  /** Variant for visual distinction */
  variant?: "default" | "destructive"
}

interface ActionBarProps {
  /** Array of action items */
  actions: ActionItem[]
  /** Size of buttons */
  size?: "sm" | "default"
  /** Additional className */
  className?: string
}

export function ActionBar({
  actions,
  size = "sm",
  className,
}: ActionBarProps) {
  return (
    <div className={cn("flex items-center gap-1", className)}>
      {actions.map((action) => (
        <Tooltip key={action.id}>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size={size === "sm" ? "icon" : "default"}
              onClick={action.onClick}
              disabled={action.disabled}
              className={cn(
                size === "sm" && "h-8 w-8",
                action.variant === "destructive" && "text-destructive hover:text-destructive"
              )}
            >
              <action.icon className={cn(size === "sm" ? "h-4 w-4" : "h-5 w-5")} />
              <span className="sr-only">{action.label}</span>
            </Button>
          </TooltipTrigger>
          <TooltipContent side="bottom">
            <p>{action.label}</p>
          </TooltipContent>
        </Tooltip>
      ))}
    </div>
  )
}
```

**Step 2: Verify no TypeScript errors**

Run: `cd /home/josep/dog/frontend && npm run lint -- --filter=src/components/Room/`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/components/Room/primitives/ActionBar.tsx
git commit -m "feat(room): add ActionBar primitive"
```

---

### Task 4: Create ParticipantStack Primitive

**Files:**
- Create: `frontend/src/components/Room/primitives/ParticipantStack.tsx`

**Step 1: Create ParticipantStack component**

```typescript
/**
 * ParticipantStack Primitive
 *
 * Overlapping avatars showing room participants.
 * Click to open full participant list popover.
 */

import * as React from "react"
import { Bot, User } from "lucide-react"
import { cn } from "@/lib/utils"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { Button } from "@/components/ui/button"
import { getInitials } from "@/utils"

export interface Participant {
  id: string
  name: string
  type: "user" | "agent"
  role?: string
  badges?: string[]
  isActive?: boolean
}

interface ParticipantStackProps {
  /** List of participants */
  participants: Participant[]
  /** Max avatars to show before +N */
  maxVisible?: number
  /** Callback when participant is clicked */
  onParticipantClick?: (participant: Participant) => void
  /** Additional className */
  className?: string
}

export function ParticipantStack({
  participants,
  maxVisible = 4,
  onParticipantClick,
  className,
}: ParticipantStackProps) {
  const visible = participants.slice(0, maxVisible)
  const overflow = participants.length - maxVisible

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          className={cn("flex items-center gap-1 h-auto py-1 px-2", className)}
        >
          <div className="flex -space-x-2">
            {visible.map((participant) => (
              <Avatar
                key={participant.id}
                className="h-7 w-7 border-2 border-background"
              >
                <AvatarFallback
                  className={cn(
                    "text-xs",
                    participant.type === "agent"
                      ? "bg-primary/20 text-primary"
                      : "bg-muted text-muted-foreground"
                  )}
                >
                  {participant.type === "agent" ? (
                    <Bot className="h-3 w-3" />
                  ) : (
                    getInitials(participant.name)
                  )}
                </AvatarFallback>
              </Avatar>
            ))}
          </div>
          {overflow > 0 && (
            <span className="text-xs text-muted-foreground ml-1">
              +{overflow}
            </span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-72 p-0" align="end">
        <div className="p-3 border-b">
          <h4 className="font-medium text-sm">
            Participants ({participants.length})
          </h4>
        </div>
        <div className="max-h-64 overflow-y-auto p-2">
          {participants.map((participant) => (
            <button
              key={participant.id}
              onClick={() => onParticipantClick?.(participant)}
              className="flex items-center gap-3 w-full p-2 rounded-md hover:bg-muted text-left"
            >
              <Avatar className="h-8 w-8">
                <AvatarFallback
                  className={cn(
                    participant.type === "agent"
                      ? "bg-primary/20 text-primary"
                      : "bg-muted text-muted-foreground"
                  )}
                >
                  {participant.type === "agent" ? (
                    <Bot className="h-4 w-4" />
                  ) : (
                    getInitials(participant.name)
                  )}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{participant.name}</p>
                {participant.badges && participant.badges.length > 0 && (
                  <p className="text-xs text-muted-foreground">
                    {participant.badges.join(" ")}
                  </p>
                )}
              </div>
              {participant.role && (
                <span className="text-xs text-muted-foreground px-2 py-0.5 bg-muted rounded">
                  {participant.role}
                </span>
              )}
            </button>
          ))}
        </div>
      </PopoverContent>
    </Popover>
  )
}
```

**Step 2: Verify no TypeScript errors**

Run: `cd /home/josep/dog/frontend && npm run lint -- --filter=src/components/Room/`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/components/Room/primitives/ParticipantStack.tsx
git commit -m "feat(room): add ParticipantStack primitive"
```

---

## Phase 2: Core Panels

### Task 5: Create ChatPanel

**Files:**
- Create: `frontend/src/components/Room/panels/ChatPanel.tsx`
- Modify: `frontend/src/components/Room/panels/index.ts`

**Step 1: Create ChatPanel component**

This wraps the existing `MessageList` and `MessageInput` components.

```typescript
/**
 * ChatPanel
 *
 * Primary panel for chat messages.
 * Wraps existing MessageList and MessageInput components.
 */

import * as React from "react"
import { Search, Download, Copy } from "lucide-react"
import { PanelContainer } from "../primitives/PanelContainer"
import { ActionBar, type ActionItem } from "../primitives/ActionBar"
import MessageList from "@/components/Rooms/MessageList"
import MessageInput from "@/components/Rooms/MessageInput"
import { Input } from "@/components/ui/input"
import type { MessageViewModel } from "@/services/roomService"

interface ChatPanelProps {
  /** Room ID */
  roomId: string
  /** Messages to display */
  messages: MessageViewModel[]
  /** Whether more messages can be loaded */
  hasMore: boolean
  /** Load more messages callback */
  onLoadMore: () => void
  /** Whether loading more messages */
  isLoadingMore: boolean
  /** Whether initial load is happening */
  isLoading: boolean
  /** Streaming message from WebSocket */
  streamingMessage?: MessageViewModel | null
  /** Whether current user is room owner */
  isRoomOwner: boolean
  /** Send message callback */
  onSendMessage: (content: string) => Promise<void>
  /** Whether sending message */
  isSending: boolean
  /** Whether WebSocket is connected */
  isConnected: boolean
  /** Send via WebSocket callback */
  sendViaWebSocket?: (content: string) => void
  /** Edit message callback */
  onEditMessage?: (message: MessageViewModel) => void
  /** Pin message callback */
  onPinMessage?: (messageId: string) => void
  /** Unpin message callback */
  onUnpinMessage?: (messageId: string) => void
  /** Toggle context callback */
  onToggleContext?: (messageId: string, active: boolean) => void
  /** Delete message callback */
  onDeleteMessage?: (messageId: string) => void
}

export function ChatPanel({
  roomId,
  messages,
  hasMore,
  onLoadMore,
  isLoadingMore,
  isLoading,
  streamingMessage,
  isRoomOwner,
  onSendMessage,
  isSending,
  isConnected,
  sendViaWebSocket,
  onEditMessage,
  onPinMessage,
  onUnpinMessage,
  onToggleContext,
  onDeleteMessage,
}: ChatPanelProps) {
  const [searchQuery, setSearchQuery] = React.useState("")
  const [showSearch, setShowSearch] = React.useState(false)

  const headerActions: ActionItem[] = [
    {
      id: "search",
      icon: Search,
      label: "Search messages",
      onClick: () => setShowSearch(!showSearch),
    },
    {
      id: "copy",
      icon: Copy,
      label: "Copy conversation",
      onClick: () => {
        const text = messages.map((m) => `${m.sender_name}: ${m.content}`).join("\n")
        navigator.clipboard.writeText(text)
      },
    },
    {
      id: "export",
      icon: Download,
      label: "Export conversation",
      onClick: () => {
        // TODO: Implement export
        console.log("Export not implemented")
      },
    },
  ]

  // Filter messages by search query
  const filteredMessages = searchQuery
    ? messages.filter(
        (m) =>
          m.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
          m.sender_name.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : messages

  return (
    <PanelContainer
      title="Chat"
      headerActions={<ActionBar actions={headerActions} />}
      footer={
        <MessageInput
          roomId={roomId}
          onSendMessage={onSendMessage}
          isSending={isSending}
          isConnected={isConnected}
          sendViaWebSocket={sendViaWebSocket}
        />
      }
    >
      {showSearch && (
        <div className="p-2 border-b">
          <Input
            placeholder="Search messages..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-8"
          />
        </div>
      )}
      <div className="flex-1 overflow-y-auto p-4">
        <MessageList
          roomId={roomId}
          messages={filteredMessages}
          hasMore={hasMore}
          onLoadMore={onLoadMore}
          isLoadingMore={isLoadingMore}
          isLoading={isLoading}
          streamingMessage={streamingMessage}
          isRoomOwner={isRoomOwner}
          onEditMessage={onEditMessage}
          onPinMessage={onPinMessage}
          onUnpinMessage={onUnpinMessage}
          onToggleContext={onToggleContext}
          onDeleteMessage={onDeleteMessage}
        />
      </div>
    </PanelContainer>
  )
}
```

**Step 2: Update panels barrel export**

Update `frontend/src/components/Room/panels/index.ts`:
```typescript
export { ChatPanel } from "./ChatPanel"
```

**Step 3: Verify no TypeScript errors**

Run: `cd /home/josep/dog/frontend && npm run lint -- --filter=src/components/Room/`
Expected: No errors

**Step 4: Commit**

```bash
git add frontend/src/components/Room/panels/
git commit -m "feat(room): add ChatPanel wrapping existing message components"
```

---

### Task 6: Create AgentPanel

**Files:**
- Create: `frontend/src/components/Room/panels/AgentPanel.tsx`
- Modify: `frontend/src/components/Room/panels/index.ts`

**Step 1: Create AgentPanel component**

```typescript
/**
 * AgentPanel
 *
 * Auxiliary panel for managing room agents.
 * Adapts existing agent management components.
 */

import * as React from "react"
import { Plus, Users } from "lucide-react"
import { PanelContainer } from "../primitives/PanelContainer"
import { ActionBar, type ActionItem } from "../primitives/ActionBar"
import {
  type AgentData,
  AgentQuickAdd,
  AgentPartyPicker,
  RoomAgentList,
} from "@/components/Agents"
import { Button } from "@/components/ui/button"
import { Loader2 } from "lucide-react"

interface AgentPanelProps {
  /** Agents currently in the room */
  roomAgents: AgentData[]
  /** All available agents */
  availableAgents: AgentData[]
  /** IDs of agents already in room */
  existingAgentIds: string[]
  /** Add single agent callback */
  onAddAgent: (agent: AgentData) => Promise<void>
  /** Add multiple agents callback */
  onAddMultipleAgents: (agents: AgentData[]) => Promise<void>
  /** Remove agent callback */
  onRemoveAgent: (agent: AgentData) => Promise<void>
  /** Whether user can manage agents */
  canManage: boolean
  /** Whether loading */
  isLoading: boolean
  /** Callback when agent is clicked for details */
  onAgentClick?: (agent: AgentData) => void
}

export function AgentPanel({
  roomAgents,
  availableAgents,
  existingAgentIds,
  onAddAgent,
  onAddMultipleAgents,
  onRemoveAgent,
  canManage,
  isLoading,
  onAgentClick,
}: AgentPanelProps) {
  if (isLoading) {
    return (
      <PanelContainer title="Agents">
        <div className="flex items-center justify-center p-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      </PanelContainer>
    )
  }

  const headerActions = canManage ? (
    <div className="flex items-center gap-1">
      <AgentQuickAdd
        availableAgents={availableAgents}
        existingAgentIds={existingAgentIds}
        onAdd={onAddAgent}
        buttonSize="sm"
      />
      <AgentPartyPicker
        availableAgents={availableAgents}
        existingAgentIds={existingAgentIds}
        onConfirm={onAddMultipleAgents}
        title="Add Agents to Room"
        description="Select multiple agents to add at once"
        trigger={
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <Users className="h-4 w-4" />
          </Button>
        }
      />
    </div>
  ) : undefined

  return (
    <PanelContainer
      title={`Agents (${roomAgents.length})`}
      headerActions={headerActions}
    >
      <div className="p-3">
        {roomAgents.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">
            No agents in this room
          </p>
        ) : (
          <RoomAgentList
            agents={roomAgents}
            onRemove={canManage ? onRemoveAgent : undefined}
            canRemove={canManage}
            variant="list"
          />
        )}
      </div>
    </PanelContainer>
  )
}
```

**Step 2: Update panels barrel export**

Update `frontend/src/components/Room/panels/index.ts`:
```typescript
export { ChatPanel } from "./ChatPanel"
export { AgentPanel } from "./AgentPanel"
```

**Step 3: Verify no TypeScript errors**

Run: `cd /home/josep/dog/frontend && npm run lint -- --filter=src/components/Room/`
Expected: No errors

**Step 4: Commit**

```bash
git add frontend/src/components/Room/panels/
git commit -m "feat(room): add AgentPanel for room agent management"
```

---

## Phase 3: Layout System

### Task 7: Create RoomLayout Component

**Files:**
- Create: `frontend/src/components/Room/RoomLayout.tsx`
- Modify: `frontend/src/components/Room/index.ts`

**Step 1: Create RoomLayout component**

```typescript
/**
 * RoomLayout
 *
 * Manages panel arrangement with resizable splits.
 * Handles responsive behavior and panel/tab toggle.
 */

import * as React from "react"
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useIsMobile } from "@/hooks/use-mobile"
import { cn } from "@/lib/utils"

export interface PanelConfig {
  id: string
  kind: string
  prominence: "primary" | "auxiliary"
  title: string
  render: () => React.ReactNode
}

interface RoomLayoutProps {
  /** Panel configurations */
  panels: PanelConfig[]
  /** Layout mode */
  mode: "panels" | "tabs"
  /** Additional className */
  className?: string
}

export function RoomLayout({ panels, mode, className }: RoomLayoutProps) {
  const isMobile = useIsMobile()

  const primaryPanels = panels.filter((p) => p.prominence === "primary")
  const auxiliaryPanels = panels.filter((p) => p.prominence === "auxiliary")

  // Mobile always uses tabs
  const effectiveMode = isMobile ? "tabs" : mode

  if (effectiveMode === "tabs") {
    return (
      <Tabs defaultValue={panels[0]?.id} className={cn("flex flex-col h-full", className)}>
        <TabsList className="w-full justify-start rounded-none border-b bg-transparent h-auto p-0">
          {panels.map((panel) => (
            <TabsTrigger
              key={panel.id}
              value={panel.id}
              className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-4 py-2"
            >
              {panel.title}
            </TabsTrigger>
          ))}
        </TabsList>
        {panels.map((panel) => (
          <TabsContent
            key={panel.id}
            value={panel.id}
            className="flex-1 mt-0 overflow-hidden"
          >
            {panel.render()}
          </TabsContent>
        ))}
      </Tabs>
    )
  }

  // Desktop panel layout
  return (
    <ResizablePanelGroup
      direction="horizontal"
      className={cn("h-full", className)}
    >
      {/* Primary panels */}
      {primaryPanels.map((panel, index) => (
        <React.Fragment key={panel.id}>
          {index > 0 && <ResizableHandle withHandle />}
          <ResizablePanel
            defaultSize={100 / primaryPanels.length}
            minSize={20}
          >
            {panel.render()}
          </ResizablePanel>
        </React.Fragment>
      ))}

      {/* Auxiliary panels column */}
      {auxiliaryPanels.length > 0 && (
        <>
          <ResizableHandle withHandle />
          <ResizablePanel defaultSize={25} minSize={15} maxSize={40}>
            <ResizablePanelGroup direction="vertical">
              {auxiliaryPanels.map((panel, index) => (
                <React.Fragment key={panel.id}>
                  {index > 0 && <ResizableHandle withHandle />}
                  <ResizablePanel
                    defaultSize={100 / auxiliaryPanels.length}
                    minSize={10}
                  >
                    {panel.render()}
                  </ResizablePanel>
                </React.Fragment>
              ))}
            </ResizablePanelGroup>
          </ResizablePanel>
        </>
      )}
    </ResizablePanelGroup>
  )
}
```

**Step 2: Update main barrel export**

Update `frontend/src/components/Room/index.ts`:
```typescript
/**
 * Room Component System
 *
 * Unified room system with multi-panel support.
 * See: docs/plans/2026-01-19-rooms-ui-design.md
 */

// Primitives
export * from "./primitives"

// Panels
export * from "./panels"

// Cards
export * from "./cards"

// Layout
export { RoomLayout, type PanelConfig } from "./RoomLayout"
```

**Step 3: Verify no TypeScript errors**

Run: `cd /home/josep/dog/frontend && npm run lint -- --filter=src/components/Room/`
Expected: No errors

**Step 4: Commit**

```bash
git add frontend/src/components/Room/
git commit -m "feat(room): add RoomLayout with resizable panels and tab mode"
```

---

### Task 8: Create RoomHeader Component

**Files:**
- Create: `frontend/src/components/Room/RoomHeader.tsx`
- Modify: `frontend/src/components/Room/index.ts`

**Step 1: Create RoomHeader component**

```typescript
/**
 * RoomHeader
 *
 * Room header with title, participants, and actions.
 * Consistent across all room types.
 */

import * as React from "react"
import {
  LayoutGrid,
  LayoutList,
  MoreVertical,
  Plus,
  Settings,
  Link,
  Trash2,
  MessageSquare,
  BookOpen,
  Grid3X3,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { ParticipantStack, type Participant } from "./primitives/ParticipantStack"

export type RoomType = "chat" | "story" | "workspace"

interface RoomHeaderProps {
  /** Room title */
  title: string
  /** Room type */
  type: RoomType
  /** Participants in the room */
  participants: Participant[]
  /** Current layout mode */
  layoutMode: "panels" | "tabs"
  /** Layout mode change callback */
  onLayoutModeChange: (mode: "panels" | "tabs") => void
  /** Whether user can edit room */
  canEdit: boolean
  /** Add panel callback (workspace only) */
  onAddPanel?: () => void
  /** Room settings callback */
  onSettings?: () => void
  /** Copy link callback */
  onCopyLink?: () => void
  /** Delete room callback */
  onDelete?: () => void
  /** Participant click callback */
  onParticipantClick?: (participant: Participant) => void
  /** Additional className */
  className?: string
}

const roomTypeIcons: Record<RoomType, React.ElementType> = {
  chat: MessageSquare,
  story: BookOpen,
  workspace: Grid3X3,
}

export function RoomHeader({
  title,
  type,
  participants,
  layoutMode,
  onLayoutModeChange,
  canEdit,
  onAddPanel,
  onSettings,
  onCopyLink,
  onDelete,
  onParticipantClick,
  className,
}: RoomHeaderProps) {
  const TypeIcon = roomTypeIcons[type]

  return (
    <header
      className={cn(
        "flex items-center justify-between px-4 py-3 border-b border-border bg-background shrink-0",
        className
      )}
    >
      {/* Left: Room identity */}
      <div className="flex items-center gap-3">
        <TypeIcon className="h-5 w-5 text-muted-foreground" />
        <div>
          <h1 className="text-base font-semibold">{title}</h1>
        </div>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-2">
        {/* Participants */}
        <ParticipantStack
          participants={participants}
          onParticipantClick={onParticipantClick}
        />

        {/* Layout toggle (desktop only) */}
        <ToggleGroup
          type="single"
          value={layoutMode}
          onValueChange={(value) => value && onLayoutModeChange(value as "panels" | "tabs")}
          className="hidden md:flex"
        >
          <ToggleGroupItem value="panels" aria-label="Panel layout">
            <LayoutGrid className="h-4 w-4" />
          </ToggleGroupItem>
          <ToggleGroupItem value="tabs" aria-label="Tab layout">
            <LayoutList className="h-4 w-4" />
          </ToggleGroupItem>
        </ToggleGroup>

        {/* Room menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {type === "workspace" && onAddPanel && (
              <DropdownMenuItem onClick={onAddPanel}>
                <Plus className="h-4 w-4 mr-2" />
                Add Panel
              </DropdownMenuItem>
            )}
            {onCopyLink && (
              <DropdownMenuItem onClick={onCopyLink}>
                <Link className="h-4 w-4 mr-2" />
                Copy Link
              </DropdownMenuItem>
            )}
            {canEdit && onSettings && (
              <DropdownMenuItem onClick={onSettings}>
                <Settings className="h-4 w-4 mr-2" />
                Room Settings
              </DropdownMenuItem>
            )}
            {canEdit && onDelete && (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={onDelete}
                  className="text-destructive focus:text-destructive"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete Room
                </DropdownMenuItem>
              </>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}
```

**Step 2: Update main barrel export**

Update `frontend/src/components/Room/index.ts`:
```typescript
/**
 * Room Component System
 *
 * Unified room system with multi-panel support.
 * See: docs/plans/2026-01-19-rooms-ui-design.md
 */

// Primitives
export * from "./primitives"

// Panels
export * from "./panels"

// Cards
export * from "./cards"

// Layout
export { RoomLayout, type PanelConfig } from "./RoomLayout"

// Header
export { RoomHeader, type RoomType } from "./RoomHeader"
```

**Step 3: Verify no TypeScript errors**

Run: `cd /home/josep/dog/frontend && npm run lint -- --filter=src/components/Room/`
Expected: No errors

**Step 4: Commit**

```bash
git add frontend/src/components/Room/
git commit -m "feat(room): add RoomHeader with participants and layout toggle"
```

---

## Phase 4: Shell & Route

### Task 9: Create RoomShell Component

**Files:**
- Create: `frontend/src/components/Room/RoomShell.tsx`
- Modify: `frontend/src/components/Room/index.ts`

**Step 1: Create RoomShell component**

```typescript
/**
 * RoomShell
 *
 * Outer container for the room.
 * Manages room-level state and composes header + layout.
 */

import * as React from "react"
import { cn } from "@/lib/utils"
import { RoomHeader, type RoomType } from "./RoomHeader"
import { RoomLayout, type PanelConfig } from "./RoomLayout"
import type { Participant } from "./primitives/ParticipantStack"

interface RoomShellProps {
  /** Room title */
  title: string
  /** Room type */
  type: RoomType
  /** Participants */
  participants: Participant[]
  /** Panel configurations */
  panels: PanelConfig[]
  /** Whether user can edit room */
  canEdit: boolean
  /** Add panel callback */
  onAddPanel?: () => void
  /** Room settings callback */
  onSettings?: () => void
  /** Copy link callback */
  onCopyLink?: () => void
  /** Delete room callback */
  onDelete?: () => void
  /** Participant click callback */
  onParticipantClick?: (participant: Participant) => void
  /** Additional className */
  className?: string
}

export function RoomShell({
  title,
  type,
  participants,
  panels,
  canEdit,
  onAddPanel,
  onSettings,
  onCopyLink,
  onDelete,
  onParticipantClick,
  className,
}: RoomShellProps) {
  const [layoutMode, setLayoutMode] = React.useState<"panels" | "tabs">("panels")

  return (
    <div className={cn("flex flex-col h-full", className)}>
      <RoomHeader
        title={title}
        type={type}
        participants={participants}
        layoutMode={layoutMode}
        onLayoutModeChange={setLayoutMode}
        canEdit={canEdit}
        onAddPanel={type === "workspace" ? onAddPanel : undefined}
        onSettings={onSettings}
        onCopyLink={onCopyLink}
        onDelete={onDelete}
        onParticipantClick={onParticipantClick}
      />
      <div className="flex-1 min-h-0">
        <RoomLayout panels={panels} mode={layoutMode} />
      </div>
    </div>
  )
}
```

**Step 2: Update main barrel export**

Update `frontend/src/components/Room/index.ts`:
```typescript
/**
 * Room Component System
 *
 * Unified room system with multi-panel support.
 * See: docs/plans/2026-01-19-rooms-ui-design.md
 */

// Primitives
export * from "./primitives"

// Panels
export * from "./panels"

// Cards
export * from "./cards"

// Layout
export { RoomLayout, type PanelConfig } from "./RoomLayout"

// Header
export { RoomHeader, type RoomType } from "./RoomHeader"

// Shell
export { RoomShell } from "./RoomShell"
```

**Step 3: Verify no TypeScript errors**

Run: `cd /home/josep/dog/frontend && npm run lint -- --filter=src/components/Room/`
Expected: No errors

**Step 4: Commit**

```bash
git add frontend/src/components/Room/
git commit -m "feat(room): add RoomShell as main room container"
```

---

### Task 10: Create New Room Route

**Files:**
- Create: `frontend/src/routes/_layout/r.$roomId.tsx`

**Step 1: Create the new unified room route**

```typescript
/**
 * Unified Room Route
 *
 * New room implementation with multi-panel support.
 * Replaces room.$roomId.tsx and room-v2.$roomId.tsx
 */

import { useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { AlertCircle, Loader2 } from "lucide-react"
import { useEffect, useState } from "react"

import {
  RoomShell,
  ChatPanel,
  AgentPanel,
  type PanelConfig,
  type Participant,
} from "@/components/Room"
import EditDrawer from "@/components/Common/EditDrawer"
import useCustomToast from "@/hooks/useCustomToast"
import { useRoom } from "@/hooks/useRoom"
import { useRoomStream } from "@/hooks/useRoomStream"
import { AgentService, type AgentViewModel } from "@/services/agentService"
import type { MessageViewModel, ParticipantViewModel } from "@/services/roomService"

export const Route = createFileRoute("/_layout/r/$roomId")({
  component: RoomView,
})

/**
 * Convert ParticipantViewModel to Participant for Room components
 */
function toParticipant(p: ParticipantViewModel): Participant {
  return {
    id: p.participant_id,
    name: p.display_name,
    type: p.participant_type as "user" | "agent",
    role: p.role,
    isActive: p.is_active,
  }
}

/**
 * Convert AgentViewModel to AgentData format
 */
function toAgentData(a: AgentViewModel) {
  return {
    id: a.id,
    name: a.name,
    description: a.description,
  }
}

function RoomView() {
  const { roomId } = Route.useParams()
  const navigate = useNavigate()
  const { showSuccessToast } = useCustomToast()

  // Edit drawer state
  const [isEditDrawerOpen, setIsEditDrawerOpen] = useState(false)
  const [editingMessage, setEditingMessage] = useState<MessageViewModel | null>(null)

  // Fetch available agents
  const { data: availableAgentsData, isLoading: isLoadingAvailable } = useQuery({
    queryKey: ["agents", "available"],
    queryFn: () => AgentService.listAvailableAgents(),
  })

  // Use the aggregate room hook
  const {
    room,
    messages,
    participants,
    isLoadingRoom,
    isLoadingMessages,
    isLoadingParticipants,
    roomError,
    currentUserRole,
    activeAgents,
    activeUsers,
    hasMoreMessages,
    loadMoreMessages,
    isLoadingMoreMessages,
    sendMessage,
    isSending,
    addParticipant,
    removeParticipant,
    updateRoom,
    deleteRoom,
    editMessage,
    isEditing,
    pinMessage,
    unpinMessage,
    toggleContext,
    deleteMessage,
  } = useRoom(roomId, {
    enablePolling: true,
    onDeleteSuccess: () => {
      navigate({ to: "/rooms" })
    },
  })

  // WebSocket connection
  const {
    isConnected,
    sendMessage: sendViaWebSocket,
    streamingMessage,
  } = useRoomStream(roomId)

  // Handle authorization errors
  useEffect(() => {
    if (roomError && "status" in roomError && roomError.status === 403) {
      navigate({ to: "/rooms" })
    }
  }, [roomError, navigate])

  // Convert data for components
  const roomParticipants: Participant[] = participants.map(toParticipant)
  const roomAgentsAsAgentData = activeAgents.map((p) => ({
    id: p.participant_id,
    name: p.display_name,
    description: null,
    participationMode: "on_mention" as const,
    isEnabled: p.is_active,
  }))
  const availableAgentsAsAgentData = (availableAgentsData?.agents || []).map(toAgentData)
  const existingAgentIds = activeAgents.map((a) => a.participant_id)

  // Handlers
  const handleAddAgent = async (agent: { id: string; name: string }) => {
    await addParticipant(agent.id, "agent")
    showSuccessToast(`Added ${agent.name} to the room`)
  }

  const handleAddMultipleAgents = async (agents: { id: string; name: string }[]) => {
    for (const agent of agents) {
      await addParticipant(agent.id, "agent")
    }
    showSuccessToast(`Added ${agents.length} agent(s) to the room`)
  }

  const handleRemoveAgent = async (agent: { id: string; name: string }) => {
    await removeParticipant(agent.id)
    showSuccessToast(`Removed ${agent.name} from the room`)
  }

  const handleEditMessage = (message: MessageViewModel) => {
    setEditingMessage(message)
    setIsEditDrawerOpen(true)
  }

  const handleSaveEdit = async (content: string) => {
    if (!editingMessage) return
    await editMessage(editingMessage.message_id, content)
    showSuccessToast("Message updated successfully")
    setIsEditDrawerOpen(false)
    setEditingMessage(null)
  }

  const handlePinMessage = async (messageId: string) => {
    await pinMessage(messageId)
    showSuccessToast("Message pinned")
  }

  const handleUnpinMessage = async (messageId: string) => {
    await unpinMessage(messageId)
    showSuccessToast("Message unpinned")
  }

  const handleToggleContext = async (messageId: string, active: boolean) => {
    await toggleContext(messageId, active)
    showSuccessToast(active ? "Added to context" : "Removed from context")
  }

  const handleDeleteMessage = async (messageId: string) => {
    if (window.confirm("Are you sure you want to delete this message?")) {
      await deleteMessage(messageId)
      showSuccessToast("Message deleted")
    }
  }

  const handleCopyLink = () => {
    navigator.clipboard.writeText(window.location.href)
    showSuccessToast("Link copied to clipboard")
  }

  const handleDeleteRoom = async () => {
    if (window.confirm("Are you sure you want to delete this room?")) {
      await deleteRoom()
    }
  }

  // Loading state
  if (isLoadingRoom || isLoadingMessages) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  // Error state
  if (roomError) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-destructive/10 p-4 mb-4">
          <AlertCircle className="h-8 w-8 text-destructive" />
        </div>
        <h3 className="text-lg font-semibold">Room not found</h3>
        <p className="text-muted-foreground">
          This room doesn't exist or you don't have access to it.
        </p>
      </div>
    )
  }

  const canManage = currentUserRole === "owner"

  // Build panel configuration
  const panels: PanelConfig[] = [
    {
      id: "chat",
      kind: "chat",
      prominence: "primary",
      title: "Chat",
      render: () => (
        <ChatPanel
          roomId={roomId}
          messages={messages}
          hasMore={hasMoreMessages}
          onLoadMore={loadMoreMessages}
          isLoadingMore={isLoadingMoreMessages}
          isLoading={isLoadingMessages}
          streamingMessage={streamingMessage}
          isRoomOwner={canManage}
          onSendMessage={sendMessage}
          isSending={isSending}
          isConnected={isConnected}
          sendViaWebSocket={sendViaWebSocket}
          onEditMessage={handleEditMessage}
          onPinMessage={handlePinMessage}
          onUnpinMessage={handleUnpinMessage}
          onToggleContext={handleToggleContext}
          onDeleteMessage={handleDeleteMessage}
        />
      ),
    },
    {
      id: "agents",
      kind: "agentPanel",
      prominence: "auxiliary",
      title: "Agents",
      render: () => (
        <AgentPanel
          roomAgents={roomAgentsAsAgentData}
          availableAgents={availableAgentsAsAgentData}
          existingAgentIds={existingAgentIds}
          onAddAgent={handleAddAgent}
          onAddMultipleAgents={handleAddMultipleAgents}
          onRemoveAgent={handleRemoveAgent}
          canManage={canManage}
          isLoading={isLoadingParticipants || isLoadingAvailable}
        />
      ),
    },
  ]

  return (
    <div className="h-[calc(100vh-8rem)]">
      <RoomShell
        title={room?.title || "Untitled Room"}
        type="chat"
        participants={roomParticipants}
        panels={panels}
        canEdit={canManage}
        onCopyLink={handleCopyLink}
        onDelete={canManage ? handleDeleteRoom : undefined}
      />

      {/* Edit Message Drawer */}
      {editingMessage && (
        <EditDrawer
          isOpen={isEditDrawerOpen}
          onClose={() => {
            setIsEditDrawerOpen(false)
            setEditingMessage(null)
          }}
          onSave={handleSaveEdit}
          initialContent={editingMessage.content}
          title="Edit Message"
          description="Changes will be visible to all participants."
          isSaving={isEditing}
        />
      )}
    </div>
  )
}
```

**Step 2: Verify no TypeScript errors**

Run: `cd /home/josep/dog/frontend && npm run lint -- --filter=src/routes/_layout/r`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/routes/_layout/r.\$roomId.tsx
git commit -m "feat(room): add unified room route at /r/:roomId"
```

---

### Task 11: Update Room List Navigation

**Files:**
- Modify: `frontend/src/routes/_layout/rooms.tsx`

**Step 1: Update navigation to use new route**

In `rooms.tsx`, find the `handleRoomSelect` function and update:

```typescript
// OLD:
const handleRoomSelect = (roomId: string) => {
  navigate({ to: "/room-v2/$roomId", params: { roomId } })
}

// NEW:
const handleRoomSelect = (roomId: string) => {
  navigate({ to: "/r/$roomId", params: { roomId } })
}
```

**Step 2: Verify navigation works**

Run: `cd /home/josep/dog/frontend && npm run dev`
Navigate to /rooms and click a room - should go to /r/:roomId

**Step 3: Commit**

```bash
git add frontend/src/routes/_layout/rooms.tsx
git commit -m "feat(rooms): navigate to new unified room route"
```

---

### Task 12: Add V2 Link to Sidebar (Temporary)

**Files:**
- Modify: `frontend/src/components/Sidebar/AppSidebar.tsx`

**Step 1: Add temporary V2 link**

In `AppSidebar.tsx`, add to `baseItems`:

```typescript
const baseItems: Item[] = [
  { icon: Home, title: "Dashboard", path: "/" },
  { icon: BookOpen, title: "Stories", path: "/stories" },
  { icon: MessageSquare, title: "Rooms", path: "/rooms" },
  { icon: Bot, title: "Agents", path: "/agents" },
  { icon: Briefcase, title: "Items", path: "/items" },
]

// Add temporary V2 link for testing comparison
const devItems: Item[] = [
  { icon: MessageSquare, title: "Rooms (V2)", path: "/room-v2" },
]
```

Then update the items usage to include devItems when in development:

```typescript
const items = currentUser?.is_superuser
  ? [...baseItems, ...devItems, { icon: Users, title: "Admin", path: "/admin" }]
  : [...baseItems, ...devItems]
```

**Step 2: Verify sidebar shows both links**

Run: `cd /home/josep/dog/frontend && npm run dev`
Check sidebar shows "Rooms" and "Rooms (V2)"

**Step 3: Commit**

```bash
git add frontend/src/components/Sidebar/AppSidebar.tsx
git commit -m "chore(sidebar): add temporary V2 rooms link for testing"
```

---

## Phase 5: Verification

### Task 13: Full Build and Test

**Step 1: Run linter**

```bash
cd /home/josep/dog/frontend && npm run lint
```

Expected: No new errors from Room components

**Step 2: Run build**

```bash
cd /home/josep/dog/frontend && npm run build
```

Expected: Build succeeds

**Step 3: Manual smoke test**

```bash
cd /home/josep/dog/frontend && npm run dev
```

Verify:
- [ ] Navigate to /rooms → room list displays
- [ ] Click room → navigates to /r/:roomId
- [ ] New room shows header with title and participants
- [ ] Chat panel displays messages
- [ ] Agent panel shows in sidebar column
- [ ] Layout toggle switches between panels/tabs
- [ ] Resize handles work between panels
- [ ] Mobile view shows tabs instead of panels

**Step 4: Final commit if fixes needed**

```bash
git add -A
git commit -m "chore: final verification and fixes"
```

---

## Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| 1 | 1-4 | Foundation: directory structure and primitives |
| 2 | 5-6 | Core panels: ChatPanel, AgentPanel |
| 3 | 7-8 | Layout system: RoomLayout, RoomHeader |
| 4 | 9-12 | Shell, route, and navigation updates |
| 5 | 13 | Verification |

**Total: 13 tasks**

**Files Created:** ~12
**Files Modified:** ~3

**Future Tasks (not in this plan):**
- Create AgentCard, UserCard, DocCard
- Create StoryEditorPanel
- Create DebugPanel (wrap existing)
- Create CanvasPanel, A2UIPanel (placeholders)
- Add panel persistence to backend
- Remove V1/V2 routes after testing complete
