/**
 * Agent Components
 *
 * Foundation and room integration components for agent UI.
 */

// ============================================================================
// Foundation Components (Sprint 1)
// ============================================================================

// Avatar
export {
  default as AgentAvatar,
  getColorForName,
  getInitials,
} from "./AgentAvatar"
export type { AgentScope, ParticipationMode } from "./AgentBadge"
// Badges
export {
  AgentModeBadge,
  AgentScopeBadge,
  AgentStatusBadge,
  default as AgentBadge,
} from "./AgentBadge"

// Card
export {
  AgentCardCompact,
  AgentCardFull,
  AgentCardMini,
  default as AgentCard,
} from "./AgentCard"

// ============================================================================
// Room Integration Components (Sprint 2)
// ============================================================================

export type { AgentData } from "./AgentCarousel"
// Carousel
export { default as AgentCarousel } from "./AgentCarousel"
// Party Picker (multi-select dialog)
export { default as AgentPartyPicker } from "./AgentPartyPicker"
// Quick Add (dropdown)
export { default as AgentQuickAdd } from "./AgentQuickAdd"

// Room Agent List
export { default as RoomAgentList } from "./RoomAgentList"

// ============================================================================
// Agent Management Components (Sprint 3)
// ============================================================================

// Shared Form
export type { AgentFormData } from "./AgentForm"
export {
  default as AgentForm,
  AVAILABLE_MODELS,
  PARTICIPATION_MODES,
  generateSlug,
} from "./AgentForm"

// Create Dialog
export { default as CreateAgentDialog } from "./CreateAgentDialog"

// Edit Dialog
export { default as EditAgentDialog } from "./EditAgentDialog"

// Clone Button
export { default as AgentCloneButton } from "./AgentCloneButton"
