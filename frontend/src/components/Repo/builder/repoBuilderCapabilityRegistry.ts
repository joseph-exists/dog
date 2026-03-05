import {
  getRepoBlockDefinition,
  getRepoCapabilityAvailability,
  getRepoPanelDefinition,
  type RepoCapabilityAvailabilityInput,
} from "@/components/Repo/registry"
import {
  ACTIVE_REPO_BUILDER_BLOCK_TYPES,
  ACTIVE_REPO_BUILDER_PANEL_KINDS,
  type ActiveRepoBuilderBlockType,
  type ActiveRepoBuilderPanelKind,
} from "./repoBuilderSchema"

export interface RepoBuilderPanelCapability {
  kind: ActiveRepoBuilderPanelKind
  displayName: string
}

export interface RepoBuilderBlockCapability {
  type: ActiveRepoBuilderBlockType
  displayName: string
}

export const REPO_BUILDER_PANEL_CAPABILITIES: RepoBuilderPanelCapability[] =
  ACTIVE_REPO_BUILDER_PANEL_KINDS.map((kind) => ({
    kind,
    displayName: getRepoPanelDefinition(kind)?.label ?? kind,
  }))

export const REPO_BUILDER_BLOCK_CAPABILITIES: RepoBuilderBlockCapability[] =
  ACTIVE_REPO_BUILDER_BLOCK_TYPES.map((type) => ({
    type,
    displayName: getRepoBlockDefinition(type)?.label ?? type,
  }))

export function getRepoPanelCapabilityAvailability(
  kind: ActiveRepoBuilderPanelKind,
  input: RepoCapabilityAvailabilityInput,
) {
  const definition = getRepoPanelDefinition(kind)
  return definition
    ? getRepoCapabilityAvailability(definition.requirements, input)
    : { available: false, unmetRequirements: ["unknown panel kind"] }
}

export function getRepoBlockCapabilityAvailability(
  type: ActiveRepoBuilderBlockType,
  input: RepoCapabilityAvailabilityInput,
) {
  const definition = getRepoBlockDefinition(type)
  return definition
    ? getRepoCapabilityAvailability(definition.requirements, input)
    : { available: false, unmetRequirements: ["unknown block type"] }
}
