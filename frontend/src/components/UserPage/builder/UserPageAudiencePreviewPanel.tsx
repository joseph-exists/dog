import { useMemo, useState } from "react"

import type { AccessGrantPublic } from "@/client"
import type { TemplateBlock } from "@/components/Page/registry"
import type { AudienceScope } from "@/components/UserPage/types"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  EntityCombobox,
  type EntityComboboxOption,
} from "@/components/ui/entity-combobox"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { buildUserPageViewModel } from "@/hooks/useUserPageViewModel"
import {
  type UserPersonaAuthoringBundle,
  UserPersonaService,
} from "@/services/userPersonaService"

type PreviewScenario = "public" | "trusted" | "collaborators" | "custom"

interface UserPageAudiencePreviewPanelProps {
  userId: string
  slug: string
  blocks: TemplateBlock[]
  authoringBundle: UserPersonaAuthoringBundle
  pageGrants: AccessGrantPublic[]
}

function countPublishedSnapshotItems(blocks: TemplateBlock[]) {
  const personaBlock = blocks.find((block) => block.type === "personaManager")
  const audienceBlock = blocks.find(
    (block) => block.type === "audiencePresentation",
  )
  const personas = Array.isArray(personaBlock?.content?.personas)
    ? personaBlock.content.personas
    : []
  const presentations = Array.isArray(audienceBlock?.content?.presentations)
    ? audienceBlock.content.presentations
    : []

  return {
    personas: personas.length,
    presentations: presentations.length,
  }
}

export function UserPageAudiencePreviewPanel({
  userId,
  slug,
  blocks,
  authoringBundle,
  pageGrants,
}: UserPageAudiencePreviewPanelProps) {
  const [scenario, setScenario] = useState<PreviewScenario>("public")
  const [customAudienceKey, setCustomAudienceKey] = useState("")

  const publishedSnapshot = useMemo(
    () => UserPersonaService.buildPublishedSnapshot(blocks, authoringBundle),
    [authoringBundle, blocks],
  )

  const customAudienceKeyOptions = useMemo<EntityComboboxOption[]>(() => {
    const keys = new Set<string>()
    for (const presentation of authoringBundle.presentations) {
      if (
        presentation.audienceScope === "custom" &&
        presentation.audienceKey &&
        presentation.audienceKey.trim()
      ) {
        keys.add(presentation.audienceKey.trim())
      }
    }
    for (const grant of pageGrants) {
      keys.add(grant.subject_id)
    }
    return Array.from(keys).map((key) => ({
      value: key,
      label: key,
      subtitle: "Custom audience key",
      keywords: [key],
    }))
  }, [authoringBundle.presentations, pageGrants])

  const resolvedAudienceScope: AudienceScope = scenario
  const resolvedAudienceKeys =
    scenario === "custom" && customAudienceKey.trim()
      ? [customAudienceKey.trim()]
      : []

  const previewViewModel = useMemo(
    () =>
      buildUserPageViewModel({
        slug,
        userId,
        isOwner: false,
        pageExists: true,
        blocks: publishedSnapshot,
        libraryPersonas: [],
        resolvedAudienceScope,
        resolvedAudienceKeys,
      }),
    [
      publishedSnapshot,
      resolvedAudienceKeys,
      resolvedAudienceScope,
      slug,
      userId,
    ],
  )

  const activePresentation =
    previewViewModel.audiencePresentations.find(
      (presentation) =>
        presentation.audienceScope === previewViewModel.selectedAudienceScope &&
        (previewViewModel.selectedAudienceScope !== "custom" ||
          (presentation.audienceKey &&
            previewViewModel.resolvedAudienceKeys.includes(
              presentation.audienceKey,
            ))),
    ) ?? null

  const selectedPersona =
    previewViewModel.personas.find(
      (persona) => persona.id === previewViewModel.selectedPersonaId,
    ) ?? null

  const snapshotCounts = countPublishedSnapshotItems(publishedSnapshot)
  const trustedGrantCount = pageGrants.filter(
    (grant) =>
      grant.subject_type === "user" || grant.subject_type === "user_persona",
  ).length
  const collaboratorGrantCount = pageGrants.filter(
    (grant) =>
      grant.subject_type === "group" || grant.subject_type === "persona_group",
  ).length

  const accessExplanation =
    scenario === "public"
      ? "Public visitors see the published fallback path when no more specific grant or custom match applies."
      : scenario === "trusted"
        ? trustedGrantCount > 0
          ? `Trusted views are activated by ${trustedGrantCount} direct user or persona grant${trustedGrantCount === 1 ? "" : "s"}.`
          : "Trusted views are authored, but there are no direct user or persona grants yet."
        : scenario === "collaborators"
          ? collaboratorGrantCount > 0
            ? `Collaborator views are activated by ${collaboratorGrantCount} group or persona-group grant${collaboratorGrantCount === 1 ? "" : "s"}.`
            : "Collaborator views are authored, but there are no group or persona-group grants yet."
          : resolvedAudienceKeys.length > 0
            ? `Custom views match when the resolved audience key equals ${resolvedAudienceKeys[0]}.`
            : "Select a custom audience key to preview the exact targeted outcome."

  return (
    <Card>
      <CardHeader>
        <CardTitle>Audience Outcome Preview</CardTitle>
        <CardDescription>
          Preview the published visitor contract by audience lens before saving.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 md:grid-cols-3">
          <div className="space-y-1.5">
            <Label>Preview audience</Label>
            <Select
              value={scenario}
              onValueChange={(value) => setScenario(value as PreviewScenario)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="public">Public</SelectItem>
                <SelectItem value="trusted">Trusted</SelectItem>
                <SelectItem value="collaborators">Collaborators</SelectItem>
                <SelectItem value="custom">Custom</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5 md:col-span-2">
            <Label>Custom audience key</Label>
            <EntityCombobox
              value={customAudienceKey}
              onChange={setCustomAudienceKey}
              options={customAudienceKeyOptions}
              placeholder="Choose a custom audience key"
              searchPlaceholder="Search audience keys..."
              emptyMessage="No custom audience keys or grant ids available."
              disabled={scenario !== "custom"}
            />
            {scenario === "custom" ? (
              <Input
                value={customAudienceKey}
                onChange={(event) => setCustomAudienceKey(event.target.value)}
                placeholder="Or enter a custom audience key directly"
              />
            ) : null}
          </div>
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          <div className="rounded border px-3 py-2">
            <div className="text-xs text-muted-foreground">
              Published Personas
            </div>
            <div className="text-lg font-semibold">
              {snapshotCounts.personas}
            </div>
          </div>
          <div className="rounded border px-3 py-2">
            <div className="text-xs text-muted-foreground">
              Published Audience Views
            </div>
            <div className="text-lg font-semibold">
              {snapshotCounts.presentations}
            </div>
          </div>
          <div className="rounded border px-3 py-2">
            <div className="text-xs text-muted-foreground">
              Visible Work In Preview
            </div>
            <div className="text-lg font-semibold">
              {previewViewModel.workFeed.length}
            </div>
          </div>
        </div>

        <div className="rounded-lg border bg-muted/30 p-4">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline">
              {previewViewModel.selectedAudienceLabel}
            </Badge>
            {selectedPersona ? (
              <Badge>{selectedPersona.nickname || selectedPersona.name}</Badge>
            ) : (
              <Badge variant="secondary">No matching persona</Badge>
            )}
            {activePresentation ? (
              <Badge variant="outline">
                {activePresentation.publicationState}
              </Badge>
            ) : null}
          </div>
          <div className="mt-3 space-y-2">
            <div className="text-sm font-medium">
              {activePresentation?.headline ??
                "No audience presentation matches this preview."}
            </div>
            <div className="text-sm text-muted-foreground">
              {activePresentation?.framingText ??
                "The current published snapshot does not contain a matching audience presentation for this lens."}
            </div>
            <div className="text-xs text-muted-foreground">
              {accessExplanation}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
