 ---
  🤖 Agent Management Features

  Current State (Backend Support ✅)
  ┌─────────────────────────────────┬──────────────────────────────────────┬──────────┐
  │             Feature             │             API Endpoint             │  Status  │
  ├─────────────────────────────────┼──────────────────────────────────────┼──────────┤
  │ List agents (system + personal) │ GET /agents/                         │ ✅ Ready │
  ├─────────────────────────────────┼──────────────────────────────────────┼──────────┤
  │ Get available for rooms         │ GET /agents/available                │ ✅ Ready │
  ├─────────────────────────────────┼──────────────────────────────────────┼──────────┤
  │ Get agent by ID                 │ GET /agents/{id}                     │ ✅ Ready │
  ├─────────────────────────────────┼──────────────────────────────────────┼──────────┤
  │ Create agent                    │ POST /agents/                        │ ✅ Ready │
  ├─────────────────────────────────┼──────────────────────────────────────┼──────────┤
  │ Update agent                    │ PUT /agents/{id}                     │ ✅ Ready │
  ├─────────────────────────────────┼──────────────────────────────────────┼──────────┤
  │ Delete agent                    │ DELETE /agents/{id}                  │ ✅ Ready │
  ├─────────────────────────────────┼──────────────────────────────────────┼──────────┤
  │ Add agent to room               │ POST /rooms/{id}/participants        │ ✅ Ready │
  ├─────────────────────────────────┼──────────────────────────────────────┼──────────┤
  │ Remove from room                │ DELETE /rooms/{id}/participants/{id} │ ✅ Ready │
  └─────────────────────────────────┴──────────────────────────────────────┴──────────┘
  AgentConfig fields available:
  - name, slug, description, model_name, system_prompt
  - scope (system/personal), participation_mode (always/on_mention/manual)
  - is_enabled, tool_config, deps_config, agent_metadata

  ✅ Foundation Agent Components Created

  All components built and verified. Here's what was created in frontend/src/components/Agents/:

  1. AgentAvatar (AgentAvatar.tsx) (complete)

  Generates colorful, deterministic avatars from agent names.

  import { AgentAvatar } from "@/components/Agents"

  <AgentAvatar name="Story Advisor" size="lg" />
  <AgentAvatar name="slug-beans" size="sm" showEmoji />

  Features:
  - Hash-based color selection (same name = same color always)
  - Smart initials extraction (handles "Story Advisor", "slug-beans", "CharacterForge")
  - 4 size variants: sm, md, lg, xl
  - Optional robot emoji mode

  ---
  2. AgentBadge (AgentBadge.tsx) (complete)

  Three specialized badge types for agent metadata.

  import { AgentScopeBadge, AgentModeBadge, AgentStatusBadge } from "@/components/Agents"

  <AgentScopeBadge scope="system" />      // 🌐 System
  <AgentScopeBadge scope="personal" />    // 👤 Personal

  <AgentModeBadge mode="always" />        // ⚡ Always Active
  <AgentModeBadge mode="on_mention" />    // @ On Mention
  <AgentModeBadge mode="manual" />        // 🎯 Manual

  <AgentStatusBadge isEnabled={true} />   // Green "Active"
  <AgentStatusBadge isEnabled={false} />  // Gray "Inactive"

  ---
  3. AgentCard (AgentCard.tsx) (complete)

  Versatile card with three variants for different contexts.

  import { AgentCard } from "@/components/Agents"

  // Full card (agent lists, management pages)
  <AgentCard
    id="123"
    name="Story Advisor"
    description="Helps with narrative structure"
    scope="system"
    participationMode="on_mention"
    isEnabled={true}
    modelName="openai:gpt-4o-mini"
    variant="full"
    onClick={() => selectAgent()}
    action={<Button>Edit</Button>}
  />

  // Compact card (sidebars, selection panels)
  <AgentCard variant="compact" {...props} />

  // Mini card (tight spaces, dropdowns)
  <AgentCard variant="mini" {...props} />

  ---
  4. Barrel Export (index.ts) (complete)

  Clean imports from a single location:

  import {
    AgentAvatar,
    AgentCard,
    AgentScopeBadge,
    AgentModeBadge,
    AgentStatusBadge,
    getInitials,
    getColorForName,
  } from "@/components/Agents"

  ---
  ★ Insight ─────────────────────────────────────
  Design Decisions:
  - Deterministic colors: Same agent always gets same color via hash function
  - Three card variants: Adapts to different UI contexts without duplication
  - Action slot pattern: Cards accept any action component (buttons, toggles, dropdowns)
  - Semantic colors: Uses Tailwind's semantic tokens for auto dark mode support
  - Type exports: AgentScope and ParticipationMode types available for consumers
  ─────────────────────────────────────────────────



● ---
  ✅ Sprint 2 Complete: Room Integration Components

  Build successful! Here's what was created:

  1. AgentCarousel (AgentCarousel.tsx) (complete)

  Horizontal scrollable gallery for browsing agents.

  import { AgentCarousel } from "@/components/Agents"

  <AgentCarousel
    agents={availableAgents}
    selectedId={selectedAgentId}
    onSelect={(agent) => handleSelect(agent)}
    cardVariant="compact"  // or "mini"
    showArrows={true}
  />

  Features:
  - Smooth horizontal scrolling
  - Navigation arrows on hover
  - Fade edges for visual hint
  - Responsive to resize

  ---
  2. AgentQuickAdd (AgentQuickAdd.tsx) (complete)

  Dropdown menu for quickly adding one agent.

  import { AgentQuickAdd } from "@/components/Agents"

  <AgentQuickAdd
    availableAgents={allAgents}
    existingAgentIds={roomAgentIds}  // Filters these out
    onAdd={async (agent) => await addAgentToRoom(agent)}
  />

  Features:
  - Auto-filters already-added agents
  - Loading state during add
  - Customizable trigger button

  ---
  3. AgentPartyPicker (AgentPartyPicker.tsx) (complete)

  Dialog for selecting multiple agents at once.

  import { AgentPartyPicker } from "@/components/Agents"

  <AgentPartyPicker
    availableAgents={allAgents}
    existingAgentIds={roomAgentIds}
    onConfirm={async (agents) => await addAgentsToRoom(agents)}
    title="Build Your Team"
    confirmText="Add to Room"
  />

  Features:
  - Checkbox multi-select
  - Search/filter
  - Select All / Clear buttons
  - Shows "Already in Room" section
  - Batch confirmation

  ---
  4. RoomAgentList (RoomAgentList.tsx) (complete)

  Display agents currently in a room.

  import { RoomAgentList } from "@/components/Agents"

  // Full list with remove buttons
  <RoomAgentList
    agents={roomAgents}
    onRemove={async (agent) => await removeAgent(agent)}
    variant="list"
  />

  // Compact chips
  <RoomAgentList agents={roomAgents} variant="compact" />

  // Stacked avatars (for headers)
  <RoomAgentList agents={roomAgents} variant="avatars-only" />

  Features:
  - 3 display variants
  - Remove with loading state
  - Empty state with call-to-action

  ---
  Unified Import

  import {
    // Sprint 1 - Foundation
    AgentAvatar,
    AgentCard,
    AgentScopeBadge,
    AgentModeBadge,
    AgentStatusBadge,

    // Sprint 2 - Room Integration
    AgentCarousel,
    AgentQuickAdd,
    AgentPartyPicker,
    RoomAgentList,

    // Types
    type AgentData,
    type AgentScope,
    type ParticipationMode,
  } from "@/components/Agents"

  ★ Insight ─────────────────────────────────────
  Design Pattern Used:
  All Sprint 2 components use the AgentData interface as their data contract, making them composable. You can:
  1. Fetch agents from API → pass to Carousel
  2. User selects → pass to PartyPicker
  3. Confirmed agents → show in RoomAgentList
  4. Quick adds via dropdown → updates RoomAgentList

  The components don't manage data fetching themselves - they're pure presentation, making them easy to wire up to your existing hooks and services.

  ---
  Feature Categories

  1️⃣ Foundation Components
  Component: AgentCard
  Complete: 100%
  Complexity: 🟢 Low
  Description: Display card with avatar, name, description, status
  Extensibility: Base for all agent displays
  ────────────────────────────────────────
  Component: AgentAvatar
  Complete: 100%
  Complexity: 🟢 Low
  Description: Generated avatar from name/slug (color hash, initials, or emoji)
  Extensibility: Used across all components
  ────────────────────────────────────────
  Component: AgentBadge
  Complexity: 🟢 Low
  Description: Small badge showing scope (🌐 System / 👤 Personal) and mode
  Extensibility: Reusable status indicator
  2️⃣ Agent Discovery & Selection
  ┌───────────────┬────────────┬───────────────────────────────────────────────────┬────────────────────┐
  │    Feature    │ Complexity │                    Description                    │  Backend Support   │
  ├───────────────┼────────────┼───────────────────────────────────────────────────┼────────────────────┤
  │ AgentList     │ 🟢 Low     │ Sortable/filterable list view of agents           │ ✅ GET /agents/    │
  ├───────────────┼────────────┼───────────────────────────────────────────────────┼────────────────────┤
  │ AgentGrid     │ 🟢 Low     │ Grid view of AgentCards                           │ ✅ Same endpoint   │
  ├───────────────┼────────────┼───────────────────────────────────────────────────┼────────────────────┤
  │ AgentCarousel │ 🟡 Medium  │ Horizontal scrollable carousel for quick browsing │ ✅ Same endpoint   │
  ├───────────────┼────────────┼───────────────────────────────────────────────────┼────────────────────┤
  │ AgentSearch   │ 🟢 Low     │ Search by name/description with debounce          │ Client-side filter │
  ├───────────────┼────────────┼───────────────────────────────────────────────────┼────────────────────┤
  │ AgentFilters  │ 🟢 Low     │ Filter by scope, mode, enabled status             │ Client-side filter │
  └───────────────┴────────────┴───────────────────────────────────────────────────┴────────────────────┘
  3️⃣ Room Integration
  Feature: AgentToggle
  Complexity: ✅ Done
  Description: Toggle agent in/out of room
  Backend Support: ✅ Participant endpoints
  ────────────────────────────────────────
  Feature: AgentPartyPicker
  Complexity: 🟡 Medium
  Description: Multi-select panel to pick agents for room
  Backend Support: ✅ Ready
  ────────────────────────────────────────
  Feature: AgentQuickAdd
  Complexity: 🟢 Low
  Description: Dropdown/popover to quickly add one agent
  Backend Support: ✅ Ready
  ────────────────────────────────────────
  Feature: RoomAgentList
  Complexity: 🟢 Low
  Description: Show current agents in room with remove option
  Backend Support: ✅ GET /rooms/{id}/participants
  ────────────────────────────────────────
  Feature: AgentPartyPresets
  Complexity: 🟡 Medium
  Description: Save/load agent combinations ("Writing Team", "Brainstorm Squad")
  Backend Support: 🔶 Needs user_preferences table
  4️⃣ Agent Creation & Management
  ┌────────────────────┬────────────┬─────────────────────────────────────────┬─────────────────────┐
  │      Feature       │ Complexity │               Description               │   Backend Support   │
  ├────────────────────┼────────────┼─────────────────────────────────────────┼─────────────────────┤
  │ CreateAgentDialog  │ 🟡 Medium  │ Form to create personal agent           │ ✅ POST /agents/    │
  ├────────────────────┼────────────┼─────────────────────────────────────────┼─────────────────────┤
  │ EditAgentDialog    │ 🟡 Medium  │ Edit existing agent config              │ ✅ PUT /agents/{id} │
  ├────────────────────┼────────────┼─────────────────────────────────────────┼─────────────────────┤
  │ AgentDetailPage    │ 🟡 Medium  │ Full page view with stats, edit, test   │ ✅ Ready            │
  ├────────────────────┼────────────┼─────────────────────────────────────────┼─────────────────────┤
  │ AgentPromptEditor  │ 🟡 Medium  │ Textarea with preview for system prompt │ ✅ Ready            │
  ├────────────────────┼────────────┼─────────────────────────────────────────┼─────────────────────┤
  │ AgentModelSelector │ 🟢 Low     │ Dropdown for model selection            │ ✅ Ready            │
  ├────────────────────┼────────────┼─────────────────────────────────────────┼─────────────────────┤
  │ MyAgentsPage       │ 🟡 Medium  │ Dashboard of user's personal agents     │ ✅ Ready            │
  └────────────────────┴────────────┴─────────────────────────────────────────┴─────────────────────┘
  5️⃣ Advanced Features (Phase 2+)
  ┌─────────────────────┬────────────┬─────────────────────────────────────┬────────────────────────────┐
  │       Feature       │ Complexity │             Description             │      Backend Support       │
  ├─────────────────────┼────────────┼─────────────────────────────────────┼────────────────────────────┤
  │ AgentTestChat       │ 🔴 High    │ Preview/test agent in isolated chat │ 🔶 Needs temp room or mock │
  ├─────────────────────┼────────────┼─────────────────────────────────────┼────────────────────────────┤
  │ AgentClone          │ 🟢 Low     │ Clone system agent as personal      │ ✅ Create with copied data │
  ├─────────────────────┼────────────┼─────────────────────────────────────┼────────────────────────────┤
  │ AgentVersionHistory │ 🟡 Medium  │ View/rollback agent versions        │ 🔶 Needs version table     │
  ├─────────────────────┼────────────┼─────────────────────────────────────┼────────────────────────────┤
  │ AgentUsageStats     │ 🟡 Medium  │ Messages sent, rooms participated   │ 🔶 Needs analytics table   │
  ├─────────────────────┼────────────┼─────────────────────────────────────┼────────────────────────────┤
  │ AgentMarketplace    │ 🔴 High    │ Share/discover community agents     │ 🔶 Needs sharing model     │
  ├─────────────────────┼────────────┼─────────────────────────────────────┼────────────────────────────┤
  │ AgentTemplates      │ 🟡 Medium  │ Pre-built prompt templates          │ 🔶 Needs template table    │
  └─────────────────────┴────────────┴─────────────────────────────────────┴────────────────────────────┘
  ---
Implementation Order:

Complete:
  Sprint 1: Foundation (4 components)
  AgentAvatar → AgentBadge → AgentCard → AgentList

Complete:
  Sprint 2: Room Integration (4 components)
  AgentCarousel → AgentQuickAdd → AgentPartyPicker → RoomAgentList

Complete:
  Sprint 3: Agent Management (4 components)
  CreateAgentDialog → EditAgentDialog → MyAgentsPage → AgentDetailPage

  ---
  Fun Feature Ideas 🎉
  ┌──────────────────────┬───────────────────────────────────────────────────────────────┬────────────┐
  │         Idea         │                             Vibe                              │ Complexity │
  ├──────────────────────┼───────────────────────────────────────────────────────────────┼────────────┤
  │ Agent Personalities  │ Random quirky titles ("The Verbose One", "Chaos Gremlin")     │ 🟢 Low     │
  ├──────────────────────┼───────────────────────────────────────────────────────────────┼────────────┤
  │ Agent Mood Indicator │ Show if agent is "chatty" or "quiet" based on recent activity │ 🟡 Medium  │
  ├──────────────────────┼───────────────────────────────────────────────────────────────┼────────────┤
  │ Agent Relationships  │ "Works well with Symbol Weaver" compatibility hints           │ 🟡 Medium  │
  ├──────────────────────┼───────────────────────────────────────────────────────────────┼────────────┤
  │ Party Combos         │ Named combos like "The Writing Room" with suggested agents    │ 🟢 Low     │
  ├──────────────────────┼───────────────────────────────────────────────────────────────┼────────────┤
  │ Agent Achievements   │ "Helped write 100 stories" badges                             │ 🟡 Medium  │
  ├──────────────────────┼───────────────────────────────────────────────────────────────┼────────────┤
  │ Drag-to-Room         │ Drag agents from carousel directly into room                  │ 🟡 Medium  │
  └──────────────────────┴───────────────────────────────────────────────────────────────┴────────────┘
  ---
  ★ Insight ─────────────────────────────────────
  What's "Free" (Backend Ready):
  - Full CRUD for agents with scope-based permissions
  - Room participation (add/remove agents)
  - Personal vs system agent distinction
  - Participation modes (always/on_mention/manual)
  - Flexible metadata fields for future expansion

  What Needs Backend Work:
  - Party presets (user preferences storage)
  - Usage analytics
  - Version history beyond simple version counter
  - Community sharing/marketplace
  ─────────────────────────────────────────────────

"Four things share a house with no door:
The first devours and is never fed.
The second drinks and cries for more, though its throat is always wet.
The third breathes but has no lungs, and speaks in tongues of fire.
The fourth dies a thousand times, yet rises, wanting, never tire.
What is the house, who is the master, and what is the name of their desire?"