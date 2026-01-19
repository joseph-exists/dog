// src/components/Page/registry/index.ts

// Entity types
export {
  entityTypes,
  getEntityType,
  getEntityTypeOrThrow,
  type EntityTypeDefinition,
} from "./entityTypes"

// Relationship types
export {
  relationshipTypes,
  getRelationshipType,
  isValidRelationship,
  type RelationshipTypeDefinition,
  type RelationshipPair,
} from "./relationshipTypes"

// Block types
export {
  blockTypes,
  getBlockType,
  getStandardBlocks,
  getDataBlocks,
  type BlockType,
  type BlockTypeDefinition,
  type ConfigFieldSchema,
  type ConfigFieldType,
} from "./blockTypes"

// Page templates
export {
  pageTemplates,
  getPageTemplate,
  getTemplatesForEntityType,
  getDefaultTemplate,
  type PageTemplate,
  type TemplateBlock,
} from "./pageTemplates"

// Data sources
export {
  dataSources,
  getDataSource,
  fetchDataSource,
  type DataSourceDefinition,
} from "./dataSources"
