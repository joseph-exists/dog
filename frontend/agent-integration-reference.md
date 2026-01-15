# Agent Integration Reference Card

Quick implementation guide for agent management features.
All changes are frontend-only. Backend requests listed at end.

---

## Option A: Integration Focus

### A1. Add Navigation Link to /agents

**File:** `src/components/Sidebar/AppSidebar.tsx`

**Change:** Add Bot icon import and agents item to `baseItems`:

```tsx
import { BookOpen, Bot, Briefcase, Home, MessageSquare, Users } from "lucide-react"

const baseItems: Item[] = [
  { icon: Home, title: "Dashboard", path: "/" },
  { icon: BookOpen, title: "Stories", path: "/stories" },
  { icon: MessageSquare, title: "Rooms", path: "/rooms" },
  { icon: Bot, title: "Agents", path: "/agents" },  // ← ADD
  { icon: Briefcase, title: "Items", path: "/items" },
]
```

**Complexity:** 🟢 Low (2 lines)

---

### A2. Create Alternate Room Layout with Agent Panel

**New File:** `src/routes/_layout/room-v2.$roomId.tsx`

**Purpose:** Enhanced room with integrated agent management sidebar using Sprint 2 components.

**Layout Structure:**
```
┌─────────────────────────────────────────────────────────────┐
│ RoomHeader                                                   │
├─────────────────────────────────┬───────────────────────────┤
│                                 │ Tabs: [Participants|Agents]│
│    MessageList                  ├───────────────────────────┤
│                                 │ Tab: Participants          │
│                                 │   └─ UserList              │
│                                 │ Tab: Agents                │
│                                 │   ├─ RoomAgentList         │
│                                 │   ├─ AgentQuickAdd         │
│                                 │   └─ AgentPartyPicker btn  │
├─────────────────────────────────┴───────────────────────────┤
│ MessageInput                                                 │
└─────────────────────────────────────────────────────────────┘
```

**Imports Required:**
```tsx
// Existing
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

// Sprint 2 Agent Components
import {
  AgentQuickAdd,
  AgentPartyPicker,
  RoomAgentList,
  type AgentData,
} from "@/components/Agents"
```

**Key Implementation Pattern:**

```tsx
// Convert ParticipantViewModel to AgentData for Sprint 2 components
const roomAgentsAsAgentData: AgentData[] = activeAgents.map((p) => ({
  id: p.participant_id,
  name: p.display_name,
  description: null,
  participationMode: "on_mention" as const,
  isEnabled: p.is_active,
}))

// Fetch available agents (all agents user can add)
const { data: availableAgents } = useQuery({
  queryKey: ["agents", "available"],
  queryFn: () => AgentsService.getAvailableAgents(),
})

// Map to AgentData
const availableAgentData: AgentData[] = (availableAgents?.agents || []).map((a) => ({
  id: a.id,
  name: a.name,
  description: a.description,
  scope: a.scope as AgentScope,
  participationMode: a.participation_mode as ParticipationMode,
  isEnabled: a.is_enabled,
  modelName: a.model_name,
}))
```

**Sidebar Panel Component:**

```tsx
function AgentSidebarPanel({
  roomAgents,
  availableAgents,
  existingAgentIds,
  onAddAgent,
  onAddMultipleAgents,
  onRemoveAgent,
  canManage,
}: {
  roomAgents: AgentData[]
  availableAgents: AgentData[]
  existingAgentIds: string[]
  onAddAgent: (agent: AgentData) => Promise<void>
  onAddMultipleAgents: (agents: AgentData[]) => Promise<void>
  onRemoveAgent: (agent: AgentData) => Promise<void>
  canManage: boolean
}) {
  return (
    <div className="flex flex-col h-full">
      {/* Header with actions */}
      {canManage && (
        <div className="flex items-center gap-2 p-3 border-b">
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
            trigger={
              <Button variant="outline" size="sm">
                <UsersIcon className="size-4" />
              </Button>
            }
          />
        </div>
      )}

      {/* Agent list */}
      <div className="flex-1 overflow-y-auto p-3">
        <RoomAgentList
          agents={roomAgents}
          onRemove={canManage ? onRemoveAgent : undefined}
          canRemove={canManage}
          variant="list"
        />
      </div>
    </div>
  )
}
```

**Complexity:** 🟡 Medium (new route file ~200 lines)

---

## Option B: Complete Sprint 3

### B1. AgentDetailPage Route

**New File:** `src/routes/_layout/agents.$agentId.tsx`

**Purpose:** Full page view for a single agent with stats, edit, and test capabilities.

**Layout Structure:**
```
┌─────────────────────────────────────────────────────────────┐
│ Breadcrumb: Agents > Agent Name                             │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐  ┌────────────────────────────────────┐ │
│ │  AgentAvatar    │  │ Name: Story Advisor                │ │
│ │  (xl size)      │  │ Slug: @story-advisor               │ │
│ │                 │  │ Scope: 🌐 System                   │ │
│ └─────────────────┘  │ Mode: @ On Mention                 │ │
│                      │ Model: gpt-4o-mini                 │ │
│                      │ Status: ● Active                   │ │
│                      └────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ Tabs: [Overview | System Prompt | Settings | Usage]         │
├─────────────────────────────────────────────────────────────┤
│ Tab Content                                                  │
│ - Overview: Description, created date, rooms participating  │
│ - System Prompt: Read-only view (or editable if personal)   │
│ - Settings: Edit form (personal agents only)                │
│ - Usage: Stats placeholder (needs backend)                  │
└─────────────────────────────────────────────────────────────┘
```

**Imports Required:**
```tsx
import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
// TODO : REVIEW lucide-react imports - we need to understand why and replace with shadcn unless we absolutely can't.
import { ArrowLeft, Copy, Settings, FileText, BarChart3 } from "lucide-react"

import { AgentsService } from "@/client/sdk.gen"
import {
  AgentAvatar,
  AgentScopeBadge,
  AgentModeBadge,
  AgentStatusBadge,
  EditAgentDialog,
} from "@/components/Agents"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
```

**NOTE:** Need to add breadcrumb component:
```bash
cd frontend && npx shadcn@latest add breadcrumb
```

**Route Definition:**
```tsx
export const Route = createFileRoute("/_layout/agents/$agentId")({
  component: AgentDetailPage,
  head: ({ params }) => ({
    meta: [{ title: `Agent - TinyFoot` }],
  }),
})

function AgentDetailPage() {
  const { agentId } = Route.useParams()

  const { data: agent, isLoading } = useQuery({
    queryKey: ["agent", agentId],
    queryFn: () => AgentsService.getAgent({ agentId }),
  })

  const isPersonal = agent?.scope === "personal"

  // ... render
}
```

**Complexity:** 🟡 Medium (new route file ~250 lines)

---

## Option C: Quick Wins

### C1. AgentClone Feature

**Purpose:** Allow users to clone a system agent as a personal agent for customization.

**Location:** Add to `AgentCard.tsx` action slot or `AgentDetailPage`

**New Component:** `src/components/Agents/AgentCloneButton.tsx`

```tsx
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { CopyIcon, Loader2Icon } from "lucide-react"
import { useState } from "react"

import type { ApiError } from "@/client/core/ApiError"
import { AgentsService } from "@/client/sdk.gen"
import type { AgentConfigPublic } from "@/client/types.gen"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import useCustomToast from "@/hooks/useCustomToast"

interface AgentCloneButtonProps {
  agent: AgentConfigPublic
  onSuccess?: (newAgent: AgentConfigPublic) => void
}

export default function AgentCloneButton({
  agent,
  onSuccess,
}: AgentCloneButtonProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [newName, setNewName] = useState(`${agent.name} (Copy)`)
  const [newSlug, setNewSlug] = useState(`${agent.slug}-copy`)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const mutation = useMutation({
    mutationFn: () =>
      AgentsService.createAgent({
        requestBody: {
          name: newName,
          slug: newSlug,
          description: agent.description,
          model_name: agent.model_name,
          system_prompt: agent.system_prompt,
          participation_mode: agent.participation_mode,
          scope: "personal", // Always personal
          is_enabled: true,
        },
      }),
    onSuccess: (newAgent) => {
      showSuccessToast(`Cloned as "${newAgent.name}"`)
      setIsOpen(false)
      onSuccess?.(newAgent)
    },
    onError: (err: ApiError) => {
      const message =
        (err.body as { detail?: string })?.detail || "Failed to clone agent"
      showErrorToast(message)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["agents"] })
    },
  })

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <CopyIcon className="size-4" />
          Clone
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Clone Agent</DialogTitle>
          <DialogDescription>
            Create a personal copy of "{agent.name}" that you can customize.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="clone-name">New Name</Label>
            <Input
              id="clone-name"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="clone-slug">New Slug</Label>
            <Input
              id="clone-slug"
              value={newSlug}
              onChange={(e) =>
                setNewSlug(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ""))
              }
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setIsOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={() => mutation.mutate()}
            disabled={!newName.trim() || !newSlug.trim() || mutation.isPending}
          >
            {mutation.isPending && <Loader2Icon className="size-4 animate-spin" />}
            Clone Agent
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
```

**Add to barrel export:** `src/components/Agents/index.ts`
```tsx
export { default as AgentCloneButton } from "./AgentCloneButton"
```

**Complexity:** 🟢 Low (single component ~100 lines)

---

### C2. System Prompt Preview Enhancement

**Purpose:** Add collapsible preview to AgentForm system prompt field.

**Location:** Modify `src/components/Agents/AgentForm.tsx`

**Add imports:**
```tsx
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { ChevronDown } from "lucide-react"
```

**Replace system prompt section:**
```tsx
{/* System Prompt with Preview */}
<div className="space-y-2">
  <Label htmlFor="agent-prompt">System Prompt</Label>
  <Textarea
    id="agent-prompt"
    value={systemPrompt}
    onChange={(e) => setSystemPrompt(e.target.value)}
    placeholder="You are a helpful assistant that..."
    className="min-h-[150px] font-mono text-sm"
  />

  {systemPrompt && (
    <Collapsible>
      <CollapsibleTrigger className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground">
        <ChevronDown className="size-3" />
        Preview rendered prompt
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="mt-2 p-3 rounded-md bg-muted text-sm whitespace-pre-wrap">
          {systemPrompt}
        </div>
      </CollapsibleContent>
    </Collapsible>
  )}

  <p className="text-xs text-muted-foreground">
    Instructions that define your agent's personality and behavior
  </p>
</div>
```

**Complexity:** 🟢 Low (modify existing component ~20 lines)

---

## shadcn Components Checklist

| Component | Status | Needed For |
|-----------|--------|------------|
| `tabs` | ✅ Installed | Room sidebar, AgentDetailPage |
| `dialog` | ✅ Installed | Clone, Create, Edit dialogs |
| `card` | ✅ Installed | AgentDetailPage |
| `collapsible` | ✅ Installed | Prompt preview |
| `breadcrumb` | ❌ Need to add | AgentDetailPage |

**Install missing:**
```bash
cd frontend && npx shadcn@latest add breadcrumb
```

---

## File Summary

| File | Action | Option |
|------|--------|--------|
| `src/components/Sidebar/AppSidebar.tsx` | Edit | A1 |
| `src/routes/_layout/room-v2.$roomId.tsx` | Create | A2 |
| `src/routes/_layout/agents.$agentId.tsx` | Create | B1 |
| `src/components/Agents/AgentCloneButton.tsx` | Create | C1 |
| `src/components/Agents/AgentForm.tsx` | Edit | C2 |
| `src/components/Agents/index.ts` | Edit | C1 |

---

## Backend Requests (Future Work)

These features would need backend changes:

| Feature | Backend Need | Priority |
|---------|--------------|----------|
| Agent usage stats | Analytics table + endpoint | Medium |
| Party presets | User preferences storage | Low |
| Agent test chat | Temp room or mock endpoint | Medium |
| Version history | Version table beyond counter | Low |

---

## Quick Start Order

Recommended implementation sequence:

1. **A1: Add navigation** (2 min) - Immediate value
2. **C1: AgentCloneButton** (15 min) - Useful feature, low effort
3. **C2: Prompt preview** (10 min) - UX enhancement
4. **B1: AgentDetailPage** (45 min) - Complete Sprint 3
5. **A2: Enhanced room layout** (60 min) - Full integration

---

*Reference card created for TinyFoot agent management feature integration.*
