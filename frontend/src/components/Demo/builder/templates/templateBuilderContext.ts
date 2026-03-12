import type {
  ActiveBuilderBlockType,
  ActiveBuilderPanelKind,
  EditableBlock,
  EditableComposition,
  EditablePanel,
} from "@/components/Demo/builder/demoBuilderSchema"
import type { BuilderTemplateId } from "@/components/Demo/builder/templates/types"

export interface TemplateBuilderContext {
  createEmptyComposition: () => EditableComposition
  createPanelTemplate: (kind: ActiveBuilderPanelKind) => EditablePanel
  createBlockTemplate: (type: ActiveBuilderBlockType) => EditableBlock
  createTemplate: (templateId: BuilderTemplateId) => EditableComposition
}

export type TemplateBuilder = (
  context: TemplateBuilderContext,
) => EditableComposition
