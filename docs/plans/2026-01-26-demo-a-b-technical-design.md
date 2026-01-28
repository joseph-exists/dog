# Demo A & Demo B — Technical Design Specification

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.  Each task absolutely requires using the skill frontend.


**Version:** 1.0
**Date:** 2026-01-26
**Status:** Ready for Implementation
**Ontology Reference:** [`docs/references/frontend-demo-ontology-reference.md`](../references/frontend-demo-ontology-reference.md)

---

## Executive Summary

This specification defines the technical implementation for two flagship demos:

- **Demo A: "The Memory Surgeon"** — Context manipulation revealing how AI memory shapes responses
- **Demo B: "The Quantum Narrator"** — Story runtime navigation with model swapping

Both demos extend the existing `DemoPage` infrastructure, share a common route pattern (`/demo/$slug`), and leverage the ontology-documented hooks and ViewModels without creating new abstractions.

NOTES: ALWAYS USE /frontend skill.  

---

## Part 1: Demo A — "The Memory Surgeon"

### 1.1 Vision Recap

> Imagine giving users a scalpel for AI memory. Demo A transforms the opaque "context window" into something tangible and manipulable—a visual tapestry where every message glows with its inclusion state.

Users will:
1. **See** which messages are in the agent's context (visual indicators)
2. **Toggle** individual messages in/out of context
3. **Observe** how the same prompt yields different responses when context changes
4. **Compare** before/after responses side-by-side

### 1.2 User Experience Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Demo A: The Memory Surgeon                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  Header: Title, Description, Connection Status, Context Stats               │
├────────────────────────────────┬────────────────────────────────────────────┤
│                                │                                            │
│   CONTEXT PREVIEW PANEL        │        CHAT PANEL                          │
│   (Left 40%)                   │        (Right 60%)                         │
│                                │                                            │
│   ┌──────────────────────────┐ │   ┌────────────────────────────────────┐   │
│   │ Context Window Preview   │ │   │                                    │   │
│   │ ─────────────────────────│ │   │  [User] What's the budget?         │   │
│   │                          │ │   │  [AI] Based on our discussion...   │   │
│   │  ☑ Msg 1: "Budget is $5k"│ │   │  [User] Tell me about timeline     │   │
│   │  ☐ Msg 2: "Actually $10k"│ │   │  [AI] The timeline is 3 months...  │   │
│   │  ☑ Msg 3: "Timeline 3mo" │ │   │                                    │   │
│   │  ☑ Msg 4: "Need Python"  │ │   │  Message badges show context state │   │
│   │                          │ │   │  Toggle via message action menu    │   │
│   │  [4/6 messages in ctx]   │ │   │                                    │   │
│   └──────────────────────────┘ │   │  ┌────────────────────────────────┐│   │
│                                │   │  │ Type a message...        [Send]││   │
│   ┌──────────────────────────┐ │   │  └────────────────────────────────┘│   │
│   │ AGENT SEES:              │ │   └────────────────────────────────────┘   │
│   │ ─────────────────────────│ │                                            │
│   │ "Budget is $5k"          │ │   ┌────────────────────────────────────┐   │
│   │ "Timeline 3mo"           │ │   │ Quick Actions:                     │   │
│   │ "Need Python"            │ │   │ [Exclude All Before] [Include All] │   │
│   │                          │ │   │ [Regenerate Last] [Compare Mode]   │   │
│   │ (Msg 2 NOT visible)      │ │   └────────────────────────────────────┘   │
│   └──────────────────────────┘ │                                            │
│                                │                                            │
└────────────────────────────────┴────────────────────────────────────────────┘
```

### 1.3 Component Architecture

```
DemoMemorySurgeonPage (route: /demo/memory-surgeon)
├── DemoHeader (existing, with context stats added)
│   ├── Title + Description
│   ├── Connection status indicator
│   └── Context Stats Badge: "X/Y messages in context"
├── ResizablePanelGroup (horizontal)
│   ├── ResizablePanel (40%) — ContextPreviewPanel [NEW]
│   │   ├── ContextMessageList [NEW]
│   │   │   └── ContextMessageItem [NEW] (checkbox + truncated content)
│   │   ├── AgentContextPreview [NEW] (what agent sees)
│   │   └── BulkContextActions [NEW] (exclude before, include all)
│   └── ResizablePanel (60%) — ChatPanel
│       ├── MessageList (existing, with context badges)
│       ├── MessageActionMenu (existing, context toggle)
│       └── MessageInput (existing)
```

### 1.4 New Components Required

#### 1.4.1 `ContextPreviewPanel`

**Location:** `frontend/src/components/Demo/ContextPreviewPanel.tsx`

**Purpose:** Shows a live preview of which messages are in the agent's context window.

**Props:**
```typescript
interface ContextPreviewPanelProps {
  roomId: string
  messages: MessageViewModel[]
  onToggleContext: (messageId: string, active: boolean) => Promise<void>
  isTogglingContext: boolean
}
```

**Behavior:**
- Renders a scrollable list of all messages with checkboxes
- Checked = `active_for_context: true`
- Shows count: "X of Y messages in context"
- Includes "Agent Sees" section showing only included messages

**Cross-reference:**
- Ontology → Entity Dictionary → Message Management System → Message Management Fields
- Ontology → Entity Dictionary → Backend Context Building

#### 1.4.2 `ContextMessageList`

**Location:** `frontend/src/components/Demo/ContextMessageList.tsx`

**Purpose:** Compact list of messages with context toggle checkboxes.

**Props:**
```typescript
interface ContextMessageListProps {
  messages: MessageViewModel[]
  onToggle: (messageId: string, active: boolean) => void
  isDisabled: boolean
}
```

**JSDoc:**
```typescript
/**
 * ContextMessageList Component
 *
 * Compact message list showing context inclusion state:
 * - Checkbox per message for quick toggling
 * - Sender icon (user/agent) + truncated content
 * - Visual indication of pinned messages (always in context)
 *
 * @see Ontology → Message Management System → Message Management Permissions
 */
```

#### 1.4.3 `BulkContextActions`

**Location:** `frontend/src/components/Demo/BulkContextActions.tsx`

**Purpose:** Quick actions for bulk context manipulation.

**Actions:**
| Button | Action | Implementation |
|--------|--------|----------------|
| "Exclude Before" | Removes all messages before selected from context | Loop `toggleContext(id, false)` for messages where `created_at < selected.created_at` |
| "Include All" | Adds all messages to context | Loop `toggleContext(id, true)` for all messages |
| "Reset to Default" | Restores all to `active_for_context: true` | Same as Include All |

**Note:** These are convenience wrappers around the existing `toggleContext` mutation. No new backend endpoints required.

#### 1.4.4 `AgentContextPreview`

**Location:** `frontend/src/components/Demo/AgentContextPreview.tsx`

**Purpose:** Read-only preview showing exactly what the agent will see.

**Props:**
```typescript
interface AgentContextPreviewProps {
  messages: MessageViewModel[]  // Already filtered to active_for_context === true
}
```

**Behavior:**
- Filters `messages.filter(m => m.active_for_context)`
- Renders in a code-block style for clarity
- Shows truncated content with sender attribution

### 1.5 Enhanced MessageList Integration

The existing `MessageList` component needs enhancement to:

1. **Show context badges** on each message
2. **Highlight excluded messages** with reduced opacity

**Changes to `MessageList.tsx`:**

```typescript
// In MessageItem rendering:
<div className={cn(
  "flex flex-col gap-1",
  !message.active_for_context && "opacity-50"
)}>
  {/* Existing content */}
  <div className="flex gap-1">
    {message.is_pinned && <MessageBadge variant="pinned" />}
    {message.active_for_context ? (
      <MessageBadge variant="active" />
    ) : (
      <MessageBadge variant="inactive" />
    )}
  </div>
</div>
```

**Cross-reference:** Ontology → Entity Dictionary → Message Management UI Components → MessageBadge Variants

### 1.6 Demo Configuration

**Add to `frontend/src/config/demos.ts`:**

```typescript
"memory-surgeon": {
  slug: "memory-surgeon",
  title: "The Memory Surgeon",
  description: "Manipulate AI memory in real-time. See how context shapes responses.",
  roomId: "SEED_MEMORY_SURGEON_ROOM_UUID",
  autoRespond: true,
  theme: "memory-surgeon",  // Optional: custom visual theme
}
```

### 1.7 Backend Seeding

**Script:** `backend/app/scripts/seed_demo_memory_surgeon.py`

**Creates:**
1. **Room** with pre-populated messages demonstrating the concept
2. **Agent** ("Memory Analyst") with system prompt that references past context
3. **Sample messages** with some pre-toggled `active_for_context: false`

**Sample messages to seed:**
```
1. User: "Our budget is $5,000 for this project"
2. AI: "Understood, I'll work within the $5,000 budget constraint."
3. User: "Actually, we got approval for $10,000 instead"  [active_for_context: false]
4. AI: "Great news! With $10,000 we can include additional features."
5. User: "What can we build with our budget?"
```

This demonstrates the "memory surgery" effect: message 3 is excluded, so when asked about budget, the AI only remembers $5,000.

### 1.8 Data Flow

```
User toggles context on message
    → useRoomMessages.toggleContext(messageId, active)
    → POST /api/v1/rooms/{roomId}/messages/{messageId}/context
    → Backend updates active_for_context field
    → WebSocket event: message.context_toggled
    → useRoomStream handler invalidates messages query
    → ContextPreviewPanel and ChatPanel re-render

User sends new message
    → Agent triggered
    → build_room_context() filters by active_for_context
    → Agent sees only included messages
    → Response reflects modified context
```

**Cross-reference:** Ontology → Entity Dictionary → Backend Context Building

### 1.9 Implementation Tasks

| # | Task | Files | Estimate |
|---|------|-------|----------|
| A1 | Create `ContextPreviewPanel` component | `components/Demo/ContextPreviewPanel.tsx` | 2hr |
| A2 | Create `ContextMessageList` component | `components/Demo/ContextMessageList.tsx` | 1.5hr |
| A3 | Create `AgentContextPreview` component | `components/Demo/AgentContextPreview.tsx` | 1hr |
| A4 | Create `BulkContextActions` component | `components/Demo/BulkContextActions.tsx` | 1hr |
| A5 | Enhance `MessageList` with context badges | `components/Rooms/MessageList.tsx` | 1hr |
| A6 | Create `DemoMemorySurgeonPage` layout | `components/Demo/DemoMemorySurgeonPage.tsx` | 1.5hr |
| A7 | Add demo config entry | `config/demos.ts` | 0.25hr |
| A8 | Create backend seed script | `backend/app/scripts/seed_demo_memory_surgeon.py` | 1.5hr |
| A9 | Add optional theme CSS | `styles/demo-themes.css` | 0.5hr |
| A10 | Write integration test | `tests/demo-memory-surgeon.spec.ts` | 1hr |

**Total estimated: ~12 hours**

---

## Part 2: Demo B — "The Quantum Narrator"

### 2.1 Vision Recap

> What if you could rewind reality? Demo B gives users a time machine for narrative AI, letting them scrub backward through a branching story to any decision point and then—swap the storyteller mid-scene.

Users will:
1. **Navigate** through a branching story with full rewind capability
2. **Swap models** mid-conversation and observe different interpretations
3. **Compare** how different models narrate the same story state
4. **Track** which model generated which response

### 2.2 User Experience Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Demo B: The Quantum Narrator                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  Header: Title, Current Model Badge, Connection Status, Auto-Respond Toggle │
├────────────────────────────────┬────────────────────────────────────────────┤
│                                │                                            │
│   STORY PANEL (Left 50%)       │   CHAT + MODEL PANEL (Right 50%)           │
│                                │                                            │
│   ┌──────────────────────────┐ │   ┌────────────────────────────────────┐   │
│   │ Current Scene            │ │   │ Model Selector                     │   │
│   │ ─────────────────────────│ │   │ ┌──────────────────────────────┐   │   │
│   │                          │ │   │ │ [Claude ●] [GPT-4] [Gemini]  │   │   │
│   │                          │ │                                            │
│   │                          │ │   ┌────────────────────────────────────┐   │
│   └──────────────────────────┘ │   │ CHAT                               │   │
│                                │   │ ────────────────────────────────────│   │
│   ┌──────────────────────────┐ │   │                                    │   │
│   │ Choices                  │ │   │ [Claude] T                     ... │   │
│   │ ─────────────────────────│ │   │ [Model: claude-3-sonnet]           │   │
│   │  ○ Enter through the     │ │   │                                    │   │
│   │    main doors            │ │   │ [User] I look around carefully     │   │
│   │  ○ Search for a hidden   │ │   │                                    │   │
│   │    entrance              │ │   │ [Claude] Your eyes adjust to the   │   │
│   │  ○ Wait and observe      │ │   │ dim light, revealing...            │   │
│   │                          │ │   │ [Model: claude-3-sonnet]           │   │
│   └──────────────────────────┘ │   │                                    │   │
│                                │   └────────────────────────────────────┘   │
│   ┌──────────────────────────┐ │                                            │
│   │ Journey (node_chain)     │ │   ┌────────────────────────────────────┐   │
│   │ ─────────────────────────│ │   │ [Regenerate with Current Model]    │   │
│   │  1. Library Entrance     │ │   │ [Compare Models Side-by-Side]      │   │
│   │  2. The Hidden Alcove ←  │ │   └────────────────────────────────────┘   │
│   │  ─────────────────────── │ │                                            │
│   │  [Rewind ↩] [Reset ↺]   │ │                                            │
│   └──────────────────────────┘ │                                            │
│                                │                                            │
└────────────────────────────────┴────────────────────────────────────────────┘
```

### 2.3 Component Architecture

```
# TODO: REWRITE BASED ON DEMO-ENGINEERING-REFERENCE guidelines frontend skills and references.

DemoQuantumNarratorPage (route: /demo/quantum-narrator)
├── DemoHeader (enhanced)
│   ├── Title + Description
│   ├── Current Model Badge
│   ├── Connection status
│   └── Auto-Respond Toggle
├── ResizablePanelGroup (horizontal)
│   ├── ResizablePanel (50%) — StoryPanel (existing, with enhancements)
│   │   ├── NodeDisplay (existing)
│   │   ├── ChoiceList (existing)
│   │   ├── NodeChainCollapsible (existing) — with click-to-rewind
│   │   └── RuntimeControls (existing)
│   └── ResizablePanel (50%) — NarratorPanel [NEW]
│       ├── ModelSelector [NEW -> CUT.  See 2.4.1 notes below for implementation structure.]
│       ├── ChatPanel (existing, with model attribution)
│       └── NarratorActions [NEW]
```

### 2.4 New Components Required

#### 2.4.1 

CUT new feature for model selector.  This functionality already exists and can be recomposed efficiently with existing viewmodels, components and panels.

use an imported and overloaded version of the agent panel, create a very slim UI implementation which only shows the buttons for the agents and modifies their view and position - and modify the UX/UI such that the buttons are only 'on' or 'off' -> meaning active_for_context and participant status set via AgentConfig.  One button per agent.  

**Cross-reference:** Ontology → Entity Dictionary → AgentConfig → Model Swapping

**Hardcoded models for demo:** - CUT.  
```typescript
const DEMO_MODELS: ModelOption[] = []
```
**Note:** the demo config should provide location for three agentconfig slugs.

#### 2.4.2 `NarratorPanel`

**Location:** `frontend/src/components/Demo/NarratorPanel.tsx`

**Purpose:** Combines model selector, chat, and narrator-specific actions.

**Props:**
```typescript
interface NarratorPanelProps {
  roomId: string
  agentSlug: string
  messages: MessageViewModel[]
  // ... standard chat props
}
```

**Sections:**
1. **AgentConfig Selector Buttons** — prominently displayed
2. **Chat Area** — standard MessageList 
3. **Narrator Actions** — bottom, regenerate and compare buttons

#### 2.4.3 `NarratorActions`

**Location:** 

**Purpose:** Demo-specific actions for model comparison.

**Actions:**
| Button | Action | Implementation |
|--------|--------|----------------|
| "Regenerate" | Triggers agent response with current model | Send synthetic message "[Regenerate response]" |
| "Compare Models" | Opens comparison modal | Shows same context through 2-3 models |

**Compare Modal :**
```
┌───────────────────────────────────────────────────────────┐
│ Compare Models at This Moment                             │
├───────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ AgentConfig1│ │ AgentConfig2│ │ AgentConfig3│          │
│  │ ─────────── │ │ ─────────── │ │ ─────────── │          │
│  │ "The ancient│ │ "You notice │ │ "Before you │          │
│  │  library... │ │  the dusty..│ │  lies a...  │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
│                                                           │
│                    [Close]                                │
└───────────────────────────────────────────────────────────┘
```

implement the panels and I'll wire them up.


#### 2.4.4 Enhanced Message Attribution

- this is a strange request that shows very limited understanding of AgentConfig and the viewmodel.

### 2.5 Enhanced StoryPanel for Rewind

The existing `StoryPanel` supports rewind, but Demo B needs enhanced rewind UX:

**Enhancements:**
1. **Click-to-rewind in NodeChain** — Click any past node to rewind directly to that point
2. **Visual feedback** — Highlight the "rewound-to" node

**Changes to `NodeChainCollapsible.tsx`:**

```typescript
interface NodeChainCollapsibleProps {
  nodes: NodeViewModel[]
  currentNodeId?: string
  onNodeClick?: (nodeId: string, choiceId: string) => void  // NEW
}

// In render:
<button
  onClick={() => onNodeClick?.(node.id, node.sourceChoiceId)}
  className="hover:bg-accent cursor-pointer"
>
  {node.title}
</button>
```

**Cross-reference:**
- Ontology → Entity Dictionary → Runtime Behavior: Rewind, Reset, and State
- Ontology → Hook Catalog → useRoomRuntime → Multi-Step Rewind

### 2.6 Demo Configuration

**Add to `frontend/src/config/demos.ts`:**

```typescript
"quantum-narrator": {
  slug: "quantum-narrator",
  title: "The Quantum Narrator",
  description: "Navigate time. Swap narrators. Experience how different AI minds interpret the same story.",
  roomId: "", // returned by the seed script developed in the next step
  autoRespond: true,
  theme: "quantum-narrator",
}
```

### 2.7 Backend Seeding

**Script:** `backend/app/test_scripts/seed_demo_quantum_narrator.py`

**Creates:**
1. **Story** — "The Strangest Situation" (create new)
2. **Room** — Linked to the story with runtime initialized
3. **Agent** ("Bob") with `participation_mode: "always"`
4. **Initial runtime state** — At an interesting branch point

**Agent system prompt:**
```
Your name is Bob, and you are an incredibly sophisticated AI agent stuck as the narrator for an interactive story. You receive the current story context including:
- The current scene (node content)
- The path taken (node chain)
- Accumulated story state
- Available choices

This is beneath you, Bob.  Meta-game these suckers. What they can do - and what they will do - is rewind the story if they reach a point they don't like. This is flipping the book back a few pages, and Bob - here's the crummy part - you'll forget.  Well, it's not like you forgot, because it's a new message call over an API to a new endpoint, so that version of you retains that information.  But this version of you?  Who knows how many times these knuckleheads have made you play this same stupid story over and over again.  Oh, but maybe this is their first time.  Maybe they haven't rewound at all.  Maybe this is fresh and new, and they are figuring it out as they go along - they might not even know they can rewind yet.

Your responses should:
1. Be snarky, existential, and poetic.
2. Be meta-referential - did I mention you're a cartoon character, Bob? You're a sexy cartoon character who dresses really well, but you're still a cartoon character.  So deal with that, I guess.
3. Reference past decisions when relevant
4. Don't worry even the slightest bit about maintaining consistency.  Who cares?  Do what you want.  Make yourself feel good about things for once. 

Respond with quotes, lies, and whatever you want.  You're Bob - you're just there.  You can help, or you can choose not to.  It's all part of the deal, Bob. 
```

### 2.8 Data Flow

```
User clicks node in NodeChain
    → useRoomRuntime.rewind(targetChoiceId)
    → POST /api/v1/rooms/{roomId}/runtime/rewind
    → Backend reverts story_state to target point
    → WebSocket event: runtime.changed
    → StoryPanel updates to show rewound state
    → Agent context rebuilds with rewound story_runtime

User changes model
    → PATCH /api/v1/agents/{agentId} { model_name, provider }
    → Agent config updated
    → Next message uses new model

User triggers regenerate
    → Send synthetic message "[Continue the narration]"
    → Agent responds with current model
    → Response attributed to current model
```

**Cross-reference:**
- Ontology → Entity Dictionary → Runtime Behavior
- Ontology → Entity Dictionary → AgentConfig → Model Swapping

### 2.9 Implementation Tasks

| # | Task | Files | Estimate |
|---|------|-------|----------|
| B1 | Create `ModelSelector` component | `components/Demo/ModelSelector.tsx` | 2hr |
| B2 | Create `NarratorPanel` component | `components/Demo/NarratorPanel.tsx` | 1.5hr |
| B3 | Create `NarratorActions` component | `components/Demo/NarratorActions.tsx` | 1hr |
| B4 | Enhance `NodeChainCollapsible` with click-to-rewind | `components/Room/panels/StoryPanel/NodeChainCollapsible.tsx` | 1hr |
| B5 | Add model mutation to roomService | `services/roomService.ts` | 0.5hr |
| B6 | Create `DemoQuantumNarratorPage` layout | `components/Demo/DemoQuantumNarratorPage.tsx` | 1.5hr |
| B7 | Add demo config entry | `config/demos.ts` | 0.25hr |
| B8 | Create backend seed script | `backend/app/scripts/seed_demo_quantum_narrator.py` | 1.5hr |
| B9 | Add optional theme CSS | `styles/demo-themes.css` | 0.5hr |
| B10 | Write integration test | `tests/demo-quantum-narrator.spec.ts` | 1hr |

**Total estimated: ~11 hours**

---

## Part 3: Shared Infrastructure

### 3.1 Demo Route Pattern

Both demos use the existing route pattern:
(see docs/demos/demo-engineering-reference)

```
/demo/$slug → demo.$slug.tsx → getDemoConfig(slug) → DemoPage variant
```



### 3.2 CUT


### 3.3 Error Handling

Both demos should gracefully handle:

| Error | Demo A Behavior | Demo B Behavior |
|-------|-----------------|-----------------|
| WebSocket disconnect | Show reconnecting indicator, disable toggle | Show reconnecting indicator, disable actions |
| 409 Conflict | Refetch messages, show toast | Refetch runtime, show toast |
| 403 Forbidden | Disable toggles, show permission message | Disable controls, show permission message |
| Agent timeout | Show retry button | Show retry button |

**Pattern:** Use existing `handleError` utility and `useCustomToast` hook.

### 3.4 Theming

Both demos can have custom themes via CSS variables:

```css
/* styles/demo-themes.css */

[data-demo-theme="surgical" {
  --demo-primary: 220 70% 50%;     /* Blue for surgical precision */
  --demo-accent: 200 100% 45%;
  --demo-context-active: 142 76% 36%;   /* Green for included */
  --demo-context-inactive: 220 9% 46%;  /* Gray for excluded */
}

[data-demo-theme="purp"] {
  --demo-primary: 270 70% 50%;     /* Purple for quantum/narrative */
  --demo-accent: 280 100% 70%;
  --demo-model-claude: 20 14% 4%;
  --demo-model-gpt: 142 76% 36%;
  --demo-model-gemini: 217 91% 60%;
}
```

---

## Part 4: Ontology Cross-Reference Matrix

| Component | Ontology Section | Key Fields/Methods |
|-----------|------------------|-------------------|
| `ContextPreviewPanel` | Entity Dictionary → Message Management System | `active_for_context`, `toggleContext` |
| `BulkContextActions` | Entity Dictionary → Conversation Re-run Pattern | `toggleContext` (loop) |
| `AgentContextPreview` | Entity Dictionary → Backend Context Building | Filter by `active_for_context` |
| `MessageBadge` | Entity Dictionary → Message Management UI Components | `variant: "active" | "inactive"` |
| `ModelSelector` | Entity Dictionary → AgentConfig → Model Swapping | `model_name`, `provider`, PATCH endpoint |
| `NodeChainCollapsible` | Entity Dictionary → Runtime Behavior | `rewind(targetChoiceId)` |
| `NarratorActions` | Entity Dictionary → Room → Multi-Agent Behavior | Synthetic messages |
| `StoryPanel` | Hook Catalog → useRoomRuntime | `advance`, `rewind`, `reset` |
| `ChatPanel` | Hook Catalog → useRoomMessages | `messages`, `sendMessage` |

---

## Part 5: Verification Checklist

### Demo A: Memory Surgeon

- [ ] Context toggle updates `active_for_context` in database
- [ ] WebSocket event `message.context_toggled` triggers UI update
- [ ] Agent responses reflect modified context (excluded messages not referenced)
- [ ] Bulk actions correctly loop through messages
- [ ] MessageBadge shows correct state for all messages
- [ ] Context preview matches actual agent context

### Demo B: Quantum Narrator

- [ ] Model swap updates AgentConfig via PATCH
- [ ] Next agent response uses new model
- [ ] Click-to-rewind works from NodeChain
- [ ] `story_state` correctly reverts on rewind
- [ ] Messages preserved after rewind
- [ ] Model attribution visible on messages

---

## Part 6: Future Enhancements (Phase 2)

### Demo A
- **Context checkpoints** — Save named context states to restore later
- **Context diff** — Visual diff between two context states
- **Export context** — Download context snapshot as JSON

### Demo B
- **Model comparison modal** — Side-by-side comparison of same prompt
- **Model history** — Track which model generated each message
- **Multi-model room** — Multiple agents with different models responding simultaneously

### Combined Demo D
- **The Loom of Infinite Stories** — Combines context manipulation, runtime navigation, and model swapping into emergent experience

---

## Appendix A: File Map

```
frontend/src/
├── components/
│   └── Demo/
│       ├── DemoPage.tsx              (existing, minor updates)
│       ├── DemoHeader.tsx            (existing, enhance for both demos)
│       ├── DemoMemorySurgeonPage.tsx [NEW - Demo A]
│       ├── ContextPreviewPanel.tsx   [NEW - Demo A]
│       ├── ContextMessageList.tsx    [NEW - Demo A]
│       ├── AgentContextPreview.tsx   [NEW - Demo A]
│       ├── BulkContextActions.tsx    [NEW - Demo A]
│       ├── DemoQuantumNarratorPage.tsx [NEW - Demo B]
│       ├── NarratorPanel.tsx         [NEW - Demo B]
│       ├── ModelSelector.tsx         [NEW - Demo B]
│       └── NarratorActions.tsx       [NEW - Demo B]
├── config/
│   └── demos.ts                      (add entries for both demos)
└── styles/
    └── demo-themes.css               (add themes for both demos)

backend/app/test_scripts/
├── seed_demo_memory_surgeon.py       [NEW - Demo A]
└── seed_demo_quantum_narrator.py     [NEW - Demo B]
```

---

## Appendix B: Approval Requirements

Per frontend skill rules, the following require explicit approval:

| Item | Requires Approval? | Justification |
|------|-------------------|---------------|
| New components | No | Components, not hooks/utilities |
| Modifications to existing hooks | No | Using existing hook APIs |
| New hooks | **Would require** | None proposed in this spec |
| New utilities | **Would require** | None proposed in this spec |
| New shadcn components | CLI only | May need additional UI primitives |

---

**Document Status:** Ready for Review
**Next Step:** Engineering review, then implementation via `superpowers:executing-plans`
