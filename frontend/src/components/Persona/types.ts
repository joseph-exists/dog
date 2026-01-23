// src/components/Persona/types.ts

/**
 * Identifies who owns a persona library.
 * The picker is agnostic to owner type.
 */
export interface PersonaLibraryOwner {
  type: "user" | "agent"
  id: string
  name: string
}

/**
 * Unified view of a persona in someone's library.
 * Normalizes UserPersonaPublic + PersonaPublic into one shape.
 */
export interface LibraryPersona {
  // Junction data
  libraryEntryId: string
  ownerId: string
  ownerType: "user" | "agent"

  // Persona data (denormalized for display)
  personaId: string
  name: string
  nickname: string | null
  description: string | null
  isActive: boolean

  // Rich data (loaded on demand)
  longDescription?: string | null
  domains?: string[]
  traits?: Array<{ id: string; name: string }>
  qualities?: Array<{ id: string; name: string }>
}

/**
 * Picker interaction modes.
 */
export type PersonaPickerMode =
  | "select-single"
  | "select-multiple"
  | "manage"
  | "browse"

/**
 * Visual presentation variants.
 */
export type PersonaPickerVariant = "dropdown" | "popover" | "sheet" | "inline"

/**
 * Filter options for narrowing persona list.
 */
export interface PersonaFilter {
  isActive?: boolean
  domains?: string[]
  searchQuery?: string
}

/**
 * Main picker props - the unified interface.
 */
export interface PersonaPickerProps {
  owner: PersonaLibraryOwner
  mode: PersonaPickerMode
  variant: PersonaPickerVariant
  selected?: string | string[] | null
  onSelect?: (selected: string | string[] | null) => void
  filter?: PersonaFilter
  layout?: "list" | "grid"
  maxVisible?: number
  className?: string
  trigger?: React.ReactNode
  placeholder?: string
}

/**
 * PersonaItem props - compact single-line display.
 */
export interface PersonaItemProps {
  persona: LibraryPersona
  isSelected?: boolean
  selectionMode?: "none" | "radio" | "checkbox"
  onSelect?: () => void
  onEdit?: () => void
  onRemove?: () => void
  showActions?: boolean
  className?: string
}

/**
 * PersonaCard props - expanded detail view.
 */
export interface PersonaCardProps {
  persona: LibraryPersona
  isSelected?: boolean
  onSelect?: () => void
  onEditNickname?: (nickname: string) => void
  onRemove?: () => void
  readonly?: boolean
  className?: string
}

/**
 * PersonaAvatar props.
 */
export interface PersonaAvatarProps {
  name: string
  imageUrl?: string | null
  size?: "sm" | "md" | "lg"
  showActiveIndicator?: boolean
  isActive?: boolean
  className?: string
}

/**
 * Content component shared props.
 */
export interface PersonaContentProps {
  personas: LibraryPersona[]
  selectedIds: string[]
  selectionMode: "none" | "radio" | "checkbox"
  onSelect: (personaId: string) => void
  onEditNickname?: (entryId: string, nickname: string) => void
  onRemove?: (entryId: string) => void
  showActions: boolean
  className?: string
}
