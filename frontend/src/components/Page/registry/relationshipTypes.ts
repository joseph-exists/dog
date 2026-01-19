// src/components/Page/registry/relationshipTypes.ts

/**
 * Valid source-target pair for a relationship type.
 */
export interface RelationshipPair {
  source: string // Entity type ID
  target: string // Entity type ID
}

/**
 * Relationship type definition for the registry.
 * Add new relationship types here - no component changes needed.
 */
export interface RelationshipTypeDefinition {
  /** Unique identifier */
  id: string
  /** Display label */
  label: string
  /** Inverse relationship ID for bidirectional relationships */
  inverseId?: string
  /** Valid entity type combinations */
  validPairs: RelationshipPair[]
}

export const relationshipTypes: RelationshipTypeDefinition[] = [
  {
    id: "member",
    label: "Member",
    inverseId: "has_member",
    validPairs: [{ source: "user", target: "team" }],
  },
  {
    id: "has_member",
    label: "Has Member",
    inverseId: "member",
    validPairs: [{ source: "team", target: "user" }],
  },
  {
    id: "owner",
    label: "Owner",
    inverseId: "owned_by",
    validPairs: [
      { source: "user", target: "team" },
      { source: "user", target: "agent" },
    ],
  },
  {
    id: "owned_by",
    label: "Owned By",
    inverseId: "owner",
    validPairs: [
      { source: "team", target: "user" },
      { source: "agent", target: "user" },
    ],
  },
  {
    id: "creator",
    label: "Creator",
    inverseId: "created_by",
    validPairs: [{ source: "user", target: "agent" }],
  },
  {
    id: "created_by",
    label: "Created By",
    inverseId: "creator",
    validPairs: [{ source: "agent", target: "user" }],
  },
  {
    id: "participant",
    label: "Participant",
    validPairs: [
      { source: "user", target: "room" },
      { source: "agent", target: "room" },
    ],
  },
]

/**
 * Get relationship type definition by ID
 */
export function getRelationshipType(
  id: string,
): RelationshipTypeDefinition | undefined {
  return relationshipTypes.find((r) => r.id === id)
}

/**
 * Check if a relationship is valid between two entity types
 */
export function isValidRelationship(
  relationshipId: string,
  sourceTypeId: string,
  targetTypeId: string,
): boolean {
  const relType = getRelationshipType(relationshipId)
  if (!relType) return false
  return relType.validPairs.some(
    (pair) => pair.source === sourceTypeId && pair.target === targetTypeId,
  )
}
