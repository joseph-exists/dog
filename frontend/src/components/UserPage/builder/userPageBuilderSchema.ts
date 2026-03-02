import type { UserPageBuilderDraft } from "./userPageBuilderAdapter"

export type UserPageBuilderSurface =
  | "overview"
  | "layout"
  | "work"
  | "personas"
  | "audiences"
  | "relations"

export interface UserPageBuilderIssue {
  code:
    | "duplicate_primary_persona"
    | "primary_persona_missing"
    | "presentation_persona_missing"
    | "presentation_work_missing"
    | "relation_source_missing"
  severity: "warning" | "error"
  message: string
  path?: string
}

export function validateUserPageBuilderDraft(
  draft: UserPageBuilderDraft,
): UserPageBuilderIssue[] {
  const issues: UserPageBuilderIssue[] = []

  const primaryPersonaId =
    typeof draft.primaryPersona.primaryPersonaId === "string" &&
    draft.primaryPersona.primaryPersonaId.trim().length > 0
      ? draft.primaryPersona.primaryPersonaId.trim()
      : null

  const personas = draft.personaManager.personas ?? []
  const personaIds = new Set(personas.map((persona) => persona.id))
  const primaryCount = personas.filter((persona) => persona.isPrimary).length

  if (primaryCount > 1) {
    issues.push({
      code: "duplicate_primary_persona",
      severity: "error",
      message: "Only one persona can be primary.",
      path: "personaManager.personas",
    })
  }

  if (primaryPersonaId && !personaIds.has(primaryPersonaId)) {
    issues.push({
      code: "primary_persona_missing",
      severity: "error",
      message: "Primary persona id does not exist in persona management content.",
      path: "primaryPersona.primaryPersonaId",
    })
  }

  const workIds = new Set((draft.workFeed.items ?? []).map((item) => item.id))
  const presentations = draft.audiencePresentation.presentations ?? []
  presentations.forEach((presentation, index) => {
    const personaId = presentation.personaId.trim()
    if (personaId && !personaIds.has(personaId)) {
      issues.push({
        code: "presentation_persona_missing",
        severity: "error",
        message: "Audience presentation references a persona that is not defined.",
        path: `audiencePresentation.presentations[${index}].personaId`,
      })
    }

    const visibleWorkIds = presentation.visibleWorkIds
    visibleWorkIds.forEach((workId, workIndex) => {
      if (workIds.has(workId.trim())) return
      issues.push({
        code: "presentation_work_missing",
        severity: "warning",
        message: "Audience presentation references work that is not defined.",
        path: `audiencePresentation.presentations[${index}].visibleWorkIds[${workIndex}]`,
      })
    })
  })

  const relations = draft.relationshipManager.relations ?? []
  relations.forEach((relation, index) => {
    const sourcePersonaId = relation.sourcePersonaId.trim()
    if (sourcePersonaId && !personaIds.has(sourcePersonaId)) {
      issues.push({
        code: "relation_source_missing",
        severity: "error",
        message: "Relation references a source persona that is not defined.",
        path: `relationshipManager.relations[${index}].sourcePersonaId`,
      })
    }
  })

  return issues
}

export function getSurfaceForBlockType(
  blockType: UserPageBuilderDraft["blocks"][number]["type"],
): UserPageBuilderSurface {
  if (blockType === "workFeed") return "work"
  if (blockType === "personaManager" || blockType === "primaryPersona") {
    return "personas"
  }
  if (blockType === "audiencePresentation") return "audiences"
  if (blockType === "relationshipManager") return "relations"
  return "layout"
}
