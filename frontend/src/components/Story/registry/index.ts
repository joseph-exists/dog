// src/components/Story/registry/index.ts

// Panel types (for layout dialogs)
export {
  type PanelKind,
  type PanelProminence,
  type PanelContext,
  type PanelPermission,
  type PanelTypeDefinition,
  PANEL_TYPES,
  getPanelType,
  getPanelDisplayName,
  getPanelsForContext,
  getPanelsForEntityPermission,
  getPanelsForSystemRole,
  isValidPanelKind,
  getDefaultPanelConfig,
  getPanelDependents,
  areDependenciesSatisfied,
} from "./panelTypes"

// Block types
export {
  BLOCK_TYPES,
  type BlockType,
  type BlockTypeDefinition,
  blockTypes,
  type ConfigFieldSchema,
  type ConfigFieldType,
  getBlockType,
  getDataBlocks,
  getStandardBlocks,
} from "./blockTypes"
// Data sources
export {
  type DataSourceDefinition,
  dataSources,
  fetchDataSource,
  getDataSource,
} from "./dataSources"
// Entity types
export {
  type EntityTypeDefinition,
  entityTypes,
  getEntityType,
  getEntityTypeOrThrow,
} from "./entityTypes"

// Page templates
export {
  getDefaultTemplate,
  getPageTemplate,
  getTemplatesForEntityType,
  type InstantiatedBlock,
  type PageTemplate,
  pageTemplates,
  type TemplateBlock,
} from "./pageTemplates"
// Relationship types
export {
  getRelationshipType,
  isValidRelationship,
  type RelationshipPair,
  type RelationshipTypeDefinition,
  relationshipTypes,
} from "./relationshipTypes"
