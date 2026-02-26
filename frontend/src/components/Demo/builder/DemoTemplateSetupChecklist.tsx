import type {
  DemoChatMode,
  DemoPersonaPolicy,
  DemoRuntimePolicy,
} from "@/client/types.gen"
import {
  type BuilderTemplateAssumptionKey,
  type BuilderTemplateChecklistStatus,
  type BuilderTemplateId,
  type EditableComposition,
  getBuilderCompositionFieldSpec,
} from "@/components/Demo/builder/demoBuilderSchema"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

function enumValuesFor(key: string): string[] {
  return [...(getBuilderCompositionFieldSpec(key)?.enumValues ?? [])]
}

function getDependencyQuickActions(
  assumption: BuilderTemplateAssumptionKey,
): Array<{
  label: string
  action: "story_picker" | "persona_picker"
}> {
  if (assumption === "story_id") {
    return [{ label: "Pick Story", action: "story_picker" }]
  }
  if (
    assumption === "persona_policy" ||
    assumption === "fixed_user_persona_id"
  ) {
    return [{ label: "Pick Persona", action: "persona_picker" }]
  }
  return []
}

interface DemoTemplateSetupChecklistProps {
  templateId: BuilderTemplateId
  templateLabel: string
  checklistStatus: BuilderTemplateChecklistStatus
  isDismissed: boolean
  composition: EditableComposition
  confirmations: Partial<Record<BuilderTemplateAssumptionKey, boolean>>
  onDismiss: () => void
  onResume: () => void
  onStoryIdChange: (value: string | null) => void
  onRuntimePolicyChange: (value: DemoRuntimePolicy) => void
  onPersonaPolicyChange: (value: DemoPersonaPolicy) => void
  onChatModeChange: (value: DemoChatMode) => void
  onFixedUserPersonaIdChange: (value: string | null) => void
  onAssumptionConfirmed: (
    assumption: BuilderTemplateAssumptionKey,
    checked: boolean,
  ) => void
  onOpenStoryPicker: () => void
  onOpenPersonaPicker: () => void
}

export function DemoTemplateSetupChecklist({
  templateId,
  templateLabel,
  checklistStatus,
  isDismissed,
  composition,
  confirmations,
  onDismiss,
  onResume,
  onStoryIdChange,
  onRuntimePolicyChange,
  onPersonaPolicyChange,
  onChatModeChange,
  onFixedUserPersonaIdChange,
  onAssumptionConfirmed,
  onOpenStoryPicker,
  onOpenPersonaPicker,
}: DemoTemplateSetupChecklistProps) {
  const unresolvedCount =
    checklistStatus.totalCount - checklistStatus.resolvedCount
  const unresolvedItems = checklistStatus.items.filter((item) => !item.resolved)
  const runtimePolicies = enumValuesFor("runtime_policy")
  const personaPolicies = enumValuesFor("persona_policy")
  const chatModes = enumValuesFor("chat_mode")

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between gap-2">
          <span>Template Setup Checklist</span>
          <Badge variant={unresolvedCount === 0 ? "default" : "secondary"}>
            {checklistStatus.resolvedCount}/{checklistStatus.totalCount}{" "}
            complete
          </Badge>
        </CardTitle>
        <CardDescription>
          {templateLabel} ({templateId}) assumptions and prompts.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {unresolvedCount === 0 ? (
          <div className="rounded border border-emerald-200 bg-emerald-50 px-3 py-2">
            <p className="text-sm text-emerald-800 font-medium">
              Template setup complete
            </p>
            <p className="text-xs text-emerald-700 mt-1">
              Required assumptions are satisfied. This template is ready to
              save.
            </p>
          </div>
        ) : (
          <div className="rounded border px-3 py-2 space-y-2">
            <p className="text-sm text-muted-foreground">
              {unresolvedCount} unresolved setup item
              {unresolvedCount === 1 ? "" : "s"}:
            </p>
            <div className="flex flex-wrap gap-2">
              {unresolvedItems.map((item) => (
                <a
                  key={`jump-${item.id}`}
                  href={`#template-checklist-item-${item.id}`}
                  className="text-xs underline text-primary"
                >
                  {item.label}
                </a>
              ))}
            </div>
          </div>
        )}

        {isDismissed ? (
          <div className="flex items-center justify-between gap-2 rounded border p-3">
            <p className="text-sm text-muted-foreground">
              Setup checklist hidden.{" "}
              {unresolvedCount > 0
                ? `${unresolvedCount} items still pending.`
                : "All items resolved."}
            </p>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onResume}
            >
              Resume Setup
            </Button>
          </div>
        ) : (
          <>
            {checklistStatus.items.map((item) => (
              <div
                key={item.id}
                id={`template-checklist-item-${item.id}`}
                className="rounded border p-3 space-y-2 scroll-mt-24"
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Badge variant={item.resolved ? "default" : "outline"}>
                      {item.resolved ? "Resolved" : "Pending"}
                    </Badge>
                    <span className="text-sm font-medium">{item.label}</span>
                  </div>
                  <span
                    className={
                      item.severity === "error"
                        ? "text-xs text-red-700"
                        : "text-xs text-amber-700"
                    }
                  >
                    {item.severity}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground">
                  {item.description}
                </p>
                {getDependencyQuickActions(item.id).length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {getDependencyQuickActions(item.id).map((action) => (
                      <Button
                        key={`${item.id}-${action.action}`}
                        type="button"
                        variant="outline"
                        size="sm"
                        className="h-7 px-2 text-xs"
                        onClick={() => {
                          if (action.action === "story_picker") {
                            onOpenStoryPicker()
                          } else {
                            onOpenPersonaPicker()
                          }
                        }}
                      >
                        {action.label}
                      </Button>
                    ))}
                  </div>
                )}
                {item.relatedIssues.length > 0 && (
                  <p className="text-xs text-red-700">
                    {item.relatedIssues[0]?.message}
                  </p>
                )}

                {item.id === "story_id" && (
                  <Input
                    value={
                      typeof composition.metadata_json === "object" &&
                      composition.metadata_json &&
                      !Array.isArray(composition.metadata_json) &&
                      typeof (
                        composition.metadata_json as { story_id?: unknown }
                      ).story_id === "string"
                        ? (composition.metadata_json as { story_id: string })
                            .story_id
                        : ""
                    }
                    placeholder="metadata_json.story_id"
                    onChange={(event) => {
                      const value = event.target.value.trim()
                      onStoryIdChange(value.length > 0 ? value : null)
                    }}
                  />
                )}

                {item.id === "runtime_policy" && (
                  <div className="flex items-center gap-3">
                    <Select
                      value={composition.runtime_policy ?? "auto"}
                      onValueChange={(value) => {
                        onRuntimePolicyChange(value as DemoRuntimePolicy)
                        onAssumptionConfirmed("runtime_policy", true)
                      }}
                    >
                      <SelectTrigger className="max-w-xs">
                        <SelectValue placeholder="runtime_policy" />
                      </SelectTrigger>
                      <SelectContent>
                        {runtimePolicies.map((policy) => (
                          <SelectItem key={policy} value={policy}>
                            {policy}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <label className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Checkbox
                        checked={Boolean(confirmations.runtime_policy)}
                        onCheckedChange={(checked) =>
                          onAssumptionConfirmed(
                            "runtime_policy",
                            Boolean(checked),
                          )
                        }
                      />
                      Confirmed
                    </label>
                  </div>
                )}

                {item.id === "persona_policy" && (
                  <div className="flex items-center gap-3">
                    <Select
                      value={composition.persona_policy ?? "first_available"}
                      onValueChange={(value) => {
                        onPersonaPolicyChange(value as DemoPersonaPolicy)
                        onAssumptionConfirmed("persona_policy", true)
                      }}
                    >
                      <SelectTrigger className="max-w-xs">
                        <SelectValue placeholder="persona_policy" />
                      </SelectTrigger>
                      <SelectContent>
                        {personaPolicies.map((policy) => (
                          <SelectItem key={policy} value={policy}>
                            {policy}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <label className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Checkbox
                        checked={Boolean(confirmations.persona_policy)}
                        onCheckedChange={(checked) =>
                          onAssumptionConfirmed(
                            "persona_policy",
                            Boolean(checked),
                          )
                        }
                      />
                      Confirmed
                    </label>
                  </div>
                )}

                {item.id === "chat_mode" && (
                  <div className="flex items-center gap-3">
                    <Select
                      value={composition.chat_mode ?? "participant"}
                      onValueChange={(value) => {
                        onChatModeChange(value as DemoChatMode)
                        onAssumptionConfirmed("chat_mode", true)
                      }}
                    >
                      <SelectTrigger className="max-w-xs">
                        <SelectValue placeholder="chat_mode" />
                      </SelectTrigger>
                      <SelectContent>
                        {chatModes.map((mode) => (
                          <SelectItem key={mode} value={mode}>
                            {mode}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <label className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Checkbox
                        checked={Boolean(confirmations.chat_mode)}
                        onCheckedChange={(checked) =>
                          onAssumptionConfirmed("chat_mode", Boolean(checked))
                        }
                      />
                      Confirmed
                    </label>
                  </div>
                )}

                {item.id === "fixed_user_persona_id" &&
                  (composition.persona_policy === "fixed_user_persona" ? (
                    <Input
                      value={composition.fixed_user_persona_id ?? ""}
                      placeholder="fixed_user_persona_id"
                      onChange={(event) => {
                        const value = event.target.value.trim()
                        onFixedUserPersonaIdChange(
                          value.length > 0 ? value : null,
                        )
                      }}
                    />
                  ) : (
                    <p className="text-xs text-muted-foreground">
                      Not required unless persona_policy is fixed_user_persona.
                    </p>
                  ))}
              </div>
            ))}

            <div className="flex justify-end">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={onDismiss}
              >
                Skip For Now
              </Button>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
