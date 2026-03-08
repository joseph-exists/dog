export type UserPageMode = "owner-empty" | "owner-manage" | "visitor-view"

export type AudienceScope =
  | "public"
  | "trusted"
  | "collaborators"
  | "custom"

export type WorkVisibilityState = "draft" | "published"

export type PersonaPublicationState = "draft" | "published"

export type UserWorkType =
  | "demo"
  | "prompt"
  | "story"
  | "page"
  | "artifact"
  | "other"

export interface WeightedTag {
  id: string
  label: string
  weight: number
  source: "user" | "system"
}

export interface UserWorkFeedItem {
  id: string
  title: string
  workType: UserWorkType
  summary: string | null
  status: WorkVisibilityState
  tags: string[]
  associatedPersonaIds: string[]
  intendedAudienceScopes: AudienceScope[]
  timestampLabel: string
  href: string | null
  isRepresentative: boolean
}

export interface UserPersonaSummary {
  id: string
  userPersonaId?: string | null
  personaVisibility?: "private" | "system" | null
  name: string
  nickname: string | null
  shortBio: string | null
  longBio: string | null
  tags: WeightedTag[]
  publicationState: PersonaPublicationState
  associatedWorkCount: number
  isPrimary: boolean
  isVisibleInCurrentAudience: boolean
}

export interface AudiencePresentationSummary {
  id: string
  userPersonaId?: string | null
  personaId: string
  audienceScope: AudienceScope
  audienceLabel: string
  headline: string
  framingText: string | null
  visibleWorkIds: string[]
  relationCallToAction:
    | "none"
    | "request_contact"
    | "invite_collaboration"
    | "follow_work"
}

export interface PersonaRelationSummary {
  id: string
  sourcePersonaId: string
  targetLabel: string
  targetType: "persona" | "external"
  relationKind: "collaborator" | "trusted" | "learning_from" | "working_with"
  audienceScope: AudienceScope
  note: string | null
  status: "active" | "pending"
}

export interface UserPageViewModel {
  userId: string
  slug: string
  isOwner: boolean
  mode: UserPageMode
  primaryPersonaId: string | null
  selectedPersonaId: string | null
  selectedAudienceScope: AudienceScope
  selectedAudienceLabel: string
  workFeed: UserWorkFeedItem[]
  personas: UserPersonaSummary[]
  audiencePresentations: AudiencePresentationSummary[]
  relations: PersonaRelationSummary[]
}

export interface WorkFeedBlockContent {
  title?: string
  emptyMessage?: string
  items?: UserWorkFeedItem[]
}

export interface PersonaManagerBlockContent {
  personas?: UserPersonaSummary[]
}

export interface AudiencePresentationBlockContent {
  presentations?: AudiencePresentationSummary[]
}

export interface RelationshipManagerBlockContent {
  relations?: PersonaRelationSummary[]
}

export interface PrimaryPersonaBlockContent {
  primaryPersonaId?: string | null
  explanation?: string
}
