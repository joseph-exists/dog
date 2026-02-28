import { useQuery, useQueryClient } from "@tanstack/react-query"
import { ChevronDown, ChevronRight, Loader2 } from "lucide-react"
import { useEffect, useMemo, useState } from "react"
import type { ApiError } from "@/client"
import {
  PromptConfigsService,
  RoomAgentSettingsService,
} from "@/client/sdk.gen"
import type {
  PromptConfigPublic,
  RoomAgentSettingsBundle,
  RoomAgentSettingsPublic,
  RoomAgentSettingsUpdate,
} from "@/client/types.gen"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

type PromptBindingDraft = {
  promptConfigId: string
  versionPolicy: "latest" | "pinned"
  versionNumber: string
}

export interface RoomPromptTargetAgent {
  id: string
  slug: string | null
  name: string
  description?: string | null
}

interface RoomPromptSettingsDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  roomId: string
  agents: RoomPromptTargetAgent[]
}

const QUERY_KEY = (roomId: string) => ["rooms", roomId, "agent-settings"]

function toDraft(
  settings: RoomAgentSettingsPublic | null | undefined,
): PromptBindingDraft {
  return {
    promptConfigId: settings?.prompt_config_id ?? "",
    versionPolicy:
      settings?.prompt_config_version_policy === "pinned" ? "pinned" : "latest",
    versionNumber:
      settings?.prompt_config_version_number != null
        ? String(settings.prompt_config_version_number)
        : "",
  }
}

function describePromptConfig(
  promptConfigId: string | null | undefined,
  promptConfigs: PromptConfigPublic[],
): string {
  if (!promptConfigId) return "No PromptConfig attached"
  const config = promptConfigs.find((item) => item.id === promptConfigId)
  if (!config) return promptConfigId
  return `${config.slug} · ${config.name}`
}

function buildUpdatePayload(
  draft: PromptBindingDraft,
  existing: RoomAgentSettingsPublic | null | undefined,
): RoomAgentSettingsUpdate {
  const promptConfigId = draft.promptConfigId || null
  const versionPolicy = promptConfigId ? draft.versionPolicy : null
  const versionNumber =
    promptConfigId && draft.versionPolicy === "pinned"
      ? Number.parseInt(draft.versionNumber, 10) || null
      : null

  return {
    prompt_config_id: promptConfigId,
    prompt_config_version_policy: versionPolicy,
    prompt_config_version_number: versionNumber,
    expected_revision: existing?.revision ?? null,
  }
}

function isEmptyDraft(draft: PromptBindingDraft): boolean {
  return !draft.promptConfigId
}

function PromptBindingEditor({
  title,
  description,
  draft,
  onDraftChange,
  promptConfigs,
  existing,
  saving,
  onSave,
  onClear,
  clearLabel,
}: {
  title: string
  description: string
  draft: PromptBindingDraft
  onDraftChange: (next: PromptBindingDraft) => void
  promptConfigs: PromptConfigPublic[]
  existing: RoomAgentSettingsPublic | null | undefined
  saving: boolean
  onSave: () => void
  onClear: (() => void) | null
  clearLabel: string
}) {
  const [inspectOpen, setInspectOpen] = useState(false)
  const hasInlineOverlay =
    existing?.prompt_config != null &&
    Object.keys(existing.prompt_config).length > 0

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-md border bg-muted/30 p-3 text-sm">
          <div className="font-medium">
            {describePromptConfig(existing?.prompt_config_id, promptConfigs)}
          </div>
          <div className="mt-1 text-muted-foreground">
            {existing?.prompt_config_id
              ? existing.prompt_config_version_policy === "pinned"
                ? `Pinned to version ${existing.prompt_config_version_number ?? "?"}`
                : "Tracks latest version"
              : "Falls through to the next lower runtime layer."}
          </div>
          <div className="mt-1 text-xs text-muted-foreground">
            Revision {existing?.revision ?? 0}
            {hasInlineOverlay ? " · includes inline overlay payload" : ""}
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-[minmax(0,1fr)_160px_140px]">
          <div className="space-y-2">
            <Label>PromptConfig</Label>
            <Select
              value={draft.promptConfigId || "__none__"}
              onValueChange={(value) =>
                onDraftChange({
                  ...draft,
                  promptConfigId: value === "__none__" ? "" : value,
                  versionPolicy:
                    value === "__none__" ? "latest" : draft.versionPolicy,
                  versionNumber: value === "__none__" ? "" : draft.versionNumber,
                })
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="No PromptConfig" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__none__">No PromptConfig</SelectItem>
                {promptConfigs.map((config) => (
                  <SelectItem key={config.id} value={config.id}>
                    {config.slug} · {config.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Version Policy</Label>
            <Select
              value={draft.versionPolicy}
              onValueChange={(value) =>
                onDraftChange({
                  ...draft,
                  versionPolicy: value as "latest" | "pinned",
                  versionNumber: value === "latest" ? "" : draft.versionNumber,
                })
              }
              disabled={!draft.promptConfigId}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="latest">Latest</SelectItem>
                <SelectItem value="pinned">Pinned</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Pinned Version</Label>
            <Input
              inputMode="numeric"
              min={1}
              placeholder="Version"
              value={draft.versionNumber}
              onChange={(event) =>
                onDraftChange({
                  ...draft,
                  versionNumber: event.target.value.replace(/[^\d]/g, ""),
                })
              }
              disabled={
                !draft.promptConfigId || draft.versionPolicy !== "pinned"
              }
            />
          </div>
        </div>

        {hasInlineOverlay ? (
          <Collapsible open={inspectOpen} onOpenChange={setInspectOpen}>
            <CollapsibleTrigger asChild>
              <Button variant="ghost" className="px-0 text-sm">
                {inspectOpen ? (
                  <ChevronDown className="mr-2 h-4 w-4" />
                ) : (
                  <ChevronRight className="mr-2 h-4 w-4" />
                )}
                Inspect Inline Overlay
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <Textarea
                readOnly
                className="min-h-40 font-mono text-xs"
                value={JSON.stringify(existing?.prompt_config ?? {}, null, 2)}
              />
            </CollapsibleContent>
          </Collapsible>
        ) : null}

        <div className="flex flex-wrap gap-2">
          <Button onClick={onSave} disabled={saving}>
            {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
            Save Binding
          </Button>
          {onClear ? (
            <Button
              variant="outline"
              onClick={onClear}
              disabled={saving && !existing}
            >
              {clearLabel}
            </Button>
          ) : null}
        </div>
      </CardContent>
    </Card>
  )
}

export function RoomPromptSettingsDialog({
  open,
  onOpenChange,
  roomId,
  agents,
}: RoomPromptSettingsDialogProps) {
  const queryClient = useQueryClient()
  const [roomDefaultsDraft, setRoomDefaultsDraft] = useState<PromptBindingDraft>(
    toDraft(null),
  )
  const [agentDrafts, setAgentDrafts] = useState<Record<string, PromptBindingDraft>>(
    {},
  )
  const [savingKey, setSavingKey] = useState<string | null>(null)

  const { data: settingsBundle, isLoading: isLoadingSettings } = useQuery<
    RoomAgentSettingsBundle,
    ApiError
  >({
    queryKey: QUERY_KEY(roomId),
    queryFn: () => RoomAgentSettingsService.readRoomAgentSettings({ roomId }),
    enabled: open,
  })

  const { data: promptConfigsResponse, isLoading: isLoadingPromptConfigs } =
    useQuery({
      queryKey: ["prompt-configs", "room-settings"],
      queryFn: () => PromptConfigsService.listPromptConfigs({ limit: 300 }),
      enabled: open,
    })

  const promptConfigs = promptConfigsResponse?.data ?? []
  const agentOverrides = useMemo(() => {
    const map = new Map<string, RoomAgentSettingsPublic>()
    for (const item of settingsBundle?.agent_overrides ?? []) {
      if (item.agent_slug) map.set(item.agent_slug, item)
    }
    return map
  }, [settingsBundle])

  const agentTargets = useMemo(() => {
    const bySlug = new Map<string, RoomPromptTargetAgent>()
    for (const agent of agents) {
      if (agent.slug) bySlug.set(agent.slug, agent)
    }
    for (const override of settingsBundle?.agent_overrides ?? []) {
      if (override.agent_slug && !bySlug.has(override.agent_slug)) {
        bySlug.set(override.agent_slug, {
          id: override.id,
          slug: override.agent_slug,
          name: override.agent_slug,
          description: "Override exists for an agent not currently in the room.",
        })
      }
    }
    return Array.from(bySlug.values()).sort((a, b) =>
      a.name.localeCompare(b.name),
    )
  }, [agents, settingsBundle?.agent_overrides])

  useEffect(() => {
    if (!open) return
    setRoomDefaultsDraft(toDraft(settingsBundle?.room_defaults))
    setAgentDrafts(() => {
      const next: Record<string, PromptBindingDraft> = {}
      for (const agent of agentTargets) {
        if (!agent.slug) continue
        next[agent.slug] = toDraft(agentOverrides.get(agent.slug))
      }
      return next
    })
  }, [open, settingsBundle, agentTargets, agentOverrides])

  const setAgentDraft = (slug: string, next: PromptBindingDraft) => {
    setAgentDrafts((prev) => ({
      ...prev,
      [slug]: next,
    }))
  }

  const refreshSettings = async () => {
    await queryClient.invalidateQueries({ queryKey: QUERY_KEY(roomId) })
  }

  const saveRoomDefaults = async () => {
    if (!settingsBundle?.room_defaults && isEmptyDraft(roomDefaultsDraft)) {
      showErrorToast("Select a PromptConfig or clear the room defaults.")
      return
    }
    const payload = buildUpdatePayload(roomDefaultsDraft, settingsBundle?.room_defaults)
    setSavingKey("room-defaults")
    try {
      await RoomAgentSettingsService.putRoomAgentSettings({
        roomId,
        requestBody: payload,
      })
      await refreshSettings()
      showSuccessToast("Room default PromptConfig binding updated.")
    } catch (error) {
      handleError.call(showErrorToast, error as ApiError)
    } finally {
      setSavingKey(null)
    }
  }

  const clearRoomDefaults = async () => {
    const existing = settingsBundle?.room_defaults
    if (!existing) {
      setRoomDefaultsDraft(toDraft(null))
      return
    }
    setSavingKey("room-defaults")
    try {
      await RoomAgentSettingsService.putRoomAgentSettings({
        roomId,
        requestBody: {
          prompt_config_id: null,
          prompt_config_version_policy: null,
          prompt_config_version_number: null,
          prompt_config: null,
          expected_revision: existing.revision ?? null,
        },
      })
      await refreshSettings()
      showSuccessToast("Room default PromptConfig binding cleared.")
    } catch (error) {
      handleError.call(showErrorToast, error as ApiError)
    } finally {
      setSavingKey(null)
    }
  }

  const saveAgentOverride = async (slug: string) => {
    const existing = agentOverrides.get(slug)
    const draft = agentDrafts[slug] ?? toDraft(existing)
    if (!existing && isEmptyDraft(draft)) {
      showErrorToast("Select a PromptConfig or use room defaults.")
      return
    }
    setSavingKey(`agent:${slug}`)
    try {
      await RoomAgentSettingsService.putRoomAgentSettingsOverride({
        roomId,
        agentSlug: slug,
        requestBody: buildUpdatePayload(draft, existing),
      })
      await refreshSettings()
      showSuccessToast(`Saved PromptConfig override for ${slug}.`)
    } catch (error) {
      handleError.call(showErrorToast, error as ApiError)
    } finally {
      setSavingKey(null)
    }
  }

  const clearAgentOverride = async (slug: string) => {
    const existing = agentOverrides.get(slug)
    if (!existing) {
      setAgentDraft(slug, toDraft(null))
      return
    }
    setSavingKey(`agent:${slug}`)
    try {
      await RoomAgentSettingsService.deleteRoomAgentSettings({
        roomId,
        agentSlug: slug,
      })
      await refreshSettings()
      showSuccessToast(`Removed PromptConfig override for ${slug}.`)
    } catch (error) {
      handleError.call(showErrorToast, error as ApiError)
    } finally {
      setSavingKey(null)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-5xl">
        <DialogHeader>
          <DialogTitle>Room Prompt Settings</DialogTitle>
          <DialogDescription>
            Room defaults apply after an agent&apos;s own PromptConfig binding.
            Per-agent overrides apply last. These bindings affect runtime
            behavior for chat-driven invocations and future panel surfaces that
            inspect room prompt state.
          </DialogDescription>
        </DialogHeader>

        {isLoadingSettings || isLoadingPromptConfigs ? (
          <div className="flex items-center justify-center py-12 text-sm text-muted-foreground">
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Loading room prompt settings…
          </div>
        ) : (
          <div className="space-y-6 py-2">
            <PromptBindingEditor
              title="Room Default Binding"
              description="Applied to all agent invocations in this room unless a per-agent override replaces it."
              draft={roomDefaultsDraft}
              onDraftChange={setRoomDefaultsDraft}
              promptConfigs={promptConfigs}
              existing={settingsBundle?.room_defaults}
              saving={savingKey === "room-defaults"}
              onSave={() => {
                void saveRoomDefaults()
              }}
              onClear={() => {
                void clearRoomDefaults()
              }}
              clearLabel="Clear Room Defaults"
            />

            <div className="space-y-3">
              <div>
                <h3 className="text-sm font-medium">Per-Agent Overrides</h3>
                <p className="text-sm text-muted-foreground">
                  These overrides are temporary room/session bindings layered on
                  top of room defaults and the agent&apos;s own PromptConfig.
                </p>
              </div>

              {agentTargets.length === 0 ? (
                <Card>
                  <CardContent className="py-6 text-sm text-muted-foreground">
                    No agent participants are currently available for room-level
                    overrides.
                  </CardContent>
                </Card>
              ) : (
                agentTargets.map((agent) => {
                  const slug = agent.slug
                  const existing = slug ? agentOverrides.get(slug) : null
                  const draft = slug
                    ? agentDrafts[slug] ?? toDraft(existing)
                    : toDraft(existing)
                  return (
                    <PromptBindingEditor
                      key={agent.id}
                      title={agent.name}
                      description={
                        agent.description ||
                        (slug
                          ? `Override the effective PromptConfig for ${slug} in this room.`
                          : "Agent slug unavailable; override controls disabled.")
                      }
                      draft={draft}
                      onDraftChange={(next) => {
                        if (slug) setAgentDraft(slug, next)
                      }}
                      promptConfigs={promptConfigs}
                      existing={existing}
                      saving={savingKey === `agent:${slug ?? "unknown"}`}
                      onSave={() => {
                        if (slug) void saveAgentOverride(slug)
                        else showErrorToast("This agent is missing a slug.")
                      }}
                      onClear={
                        slug
                          ? () => {
                              void clearAgentOverride(slug)
                            }
                          : null
                      }
                      clearLabel="Use Room Defaults"
                    />
                  )
                })
              )}
            </div>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
