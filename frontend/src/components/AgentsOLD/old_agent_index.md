```typescript
/**
 * Agent Components
 *
 * Foundation and room integration components for agent UI.
 */

// ============================================================================
// Foundation Components 
// ============================================================================

// Avatar
export {
  default as AgentAvatar,
  getColorForName,
  getInitials,
} from 
export type { AgentScope, ParticipationMode } 
// Badges
export {
  AgentCoordinatorBadge,
  AgentModeBadge,
  AgentScopeBadge,
  AgentStatusBadge,
  default as AgentBadge,
} from "../UserAccessProviders/Display/AgentBadge"

// Card
export {
  AgentCardCompact,
  AgentCardFull,
  AgentCardMini,
  default as AgentCard,
} from "../UserAccessProviders/Display/AgentCard"

// ============================================================================
// Room Integration Components 
// ============================================================================


// Carousel
export { default as AgentCarousel } from "../Agents/RoomManagers/AgentCarousel"
// Party Picker (multi-select dialog)
export { default as AgentPartyPicker } from "../Agents/RoomManagers/AgentPartyPicker"
// Quick Add (dropdown)
export { default as AgentQuickAdd } from "../Agents/RoomManagers/AgentQuickAdd"

// Room Agent List
export { default as RoomAgentList } from "./RoomAgentList"

// ============================================================================
// Agent Management Components 
// ============================================================================

// Clone Button
export { default as AgentCloneButton } from "./Dialogs/AgentCloneButton"
// Shared Form
export type { AgentFormData } from "./Forms/AgentForm"
export { default as AgentForm, PARTICIPATION_MODES } from "./Forms/AgentForm"
// Create Dialog
export { default as CreateAgentDialog } from "../Agents/Dialogs/CreateAgentDialog"
// Edit Dialog
export { default as EditAgentDialog } from "./Dialogs/EditAgentDialog"

// ============================================================================
// Provider Configuration Components 
// ============================================================================

// Model Settings - allows users to customize model and provider for an agent
export { default as AgentModelSettings } from "../Agents/Dialogs/AgentModelSettings"
// Provider Selector - lightweight inline selector
export { default as AgentProviderSelector } from "../UserAccessProviders/Selectors/InlineProviderSelector"
// Provider components (reusable building blocks)
export { ProviderModelSelector } from "../Agents/Forms/FormSelectors/ProviderModelSelector"
export { ProviderStatusBadge } from "../UserAccessProviders/Display/ProviderStatusBadge"
```