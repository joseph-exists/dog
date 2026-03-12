export type BuilderTemplateAssumptionKey =
  | "story_id"
  | "runtime_policy"
  | "persona_policy"
  | "chat_mode"
  | "fixed_user_persona_id"

export type BuilderTemplateConfirmations = Partial<
  Record<BuilderTemplateAssumptionKey, boolean>
>

export type BuilderTemplateId =
  | "composition_a_baseline"
  | "composition_b_runtime_coupled"
  | "composition_c_visibility_semantics"
  | "composition_d_stylized_agent_ops"
  | "composition_d1_enhanced_normal"
  | "composition_d2_enhanced_bonkers"
  | "composition_e_tabs_content_studio"
  | "composition_f_presentation_passthrough_audit"
  | "composition_g_ux_style_matrix"
  | "composition_h_chaotic_combinatorics"
  | "composition_i_intensity"

export interface BuilderCompositionTemplateOption {
  id: BuilderTemplateId
  label: string
  description: string
}

export interface BuilderTemplateChecklistItemDefinition {
  id: BuilderTemplateAssumptionKey
  label: string
  description: string
  severity: "warning" | "error"
}

export interface BuilderCompositionTemplateSchema
  extends BuilderCompositionTemplateOption {
  requiredAssumptions: BuilderTemplateAssumptionKey[]
  checklistItems: BuilderTemplateChecklistItemDefinition[]
}
