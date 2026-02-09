/**
 * AgentusFormulaicus
 *
 * A four-chapter ritual for conjuring agent configurations.
 * Same zod + useForm bones as AgentForm — different soul.
 *
 * Chapter I:   "Who Is That Fancy Wonder?" — name, slug, description
 * Chapter II:  "Wherewithal" — provider & model binding
 * Chapter III: "The Incantation" — system prompt, instructions
 * Chapter IV:  "Temperament & Arcana" — modes, toggles, dark arts
 *
 * Stepped wizard. Framer-motion transitions. Fits in a dialog.
 * Each chapter validates before you can proceed.
 */

import { zodResolver } from "@hookform/resolvers/zod"
import { AnimatePresence, motion } from "framer-motion"
import {
  ArrowLeftIcon,
  ArrowRightIcon,
  Loader2,
  SparklesIcon,
} from "lucide-react"
import { useCallback, useEffect, useRef, useState } from "react"
import { useForm, useFormContext, FormProvider } from "react-hook-form"
import { z } from "zod/v4"

import { AgentsService } from "@/client/sdk.gen"
import type {
  LLMModelPublic,
  UserAccessProviderPublic,
  UserAgentConfigPublic,
} from "@/client/types.gen"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Textarea } from "@/components/ui/textarea"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { springConfig, useReduceMotion } from "@/components/ui/motion"
import { cn } from "@/lib/utils"
import { ProviderModelSelector } from "./FormSelectors/ProviderModelSelector"

// ══════════════════════════════════════════════════════════════════════════
// Emitted Shape
// ══════════════════════════════════════════════════════════════════════════

export type AgentFormData = {
  name: string
  slug: string
  description: string
  user_access_provider?: string | null
  provider_type: string
  model?: string | null
  model_id?: string | null
  model_name?: string
  system_prompt: string
  custom_system_prompt?: string | null
  instructions?: string | null
  is_enabled: boolean
  is_clonable: boolean
  is_visible: boolean
  scope: string
  participation_mode: string
  is_coordinator: boolean
  max_tool_iterations: number
  capabilities: string[]
  tool_config?: Record<string, unknown> | null
  deps_config?: Record<string, unknown> | null
  agent_metadata?: Record<string, unknown> | null
}

// ══════════════════════════════════════════════════════════════════════════
// Schema
// ══════════════════════════════════════════════════════════════════════════

const schema = z.object({
  // I: who is THAT FANCY WONDER?
  name: z.string().min(1, "Every being needs a name.").max(100),
  slug: z.string().min(1, "The sigil must be inscribed."),
  description: z.string().max(500).default(""),

  // II: wherewithal
  user_access_provider: z.string().nullable().default(null),
  provider_type: z.string().default(""),
  model: z.string().nullable().default(null),
  model_id: z.string().nullable().default(null),
  model_name: z.string().default(""),

  // III: guidance
  system_prompt: z.string().default(""),
  custom_system_prompt: z.string().nullable().default(null),
  instructions: z.string().nullable().default(null),

  // IV: behavioring and expressions
  participation_mode: z.string().default("on_mention"),
  scope: z.string().default("personal"),
  is_enabled: z.boolean().default(true),
  is_clonable: z.boolean().default(false),
  is_visible: z.boolean().default(true),
  is_coordinator: z.boolean().default(false),
  max_tool_iterations: z.coerce.number().int().min(0).max(100).default(10),

  // superfreaking powers
  capabilities_raw: z.string().default(""),
  tool_config_raw: z.string().default(""),
  deps_config_raw: z.string().default(""),
  agent_metadata_raw: z.string().default(""),
})

type FormValues = z.infer<typeof schema>

// Fields that must pass validation before leaving each chapter
const CHAPTER_FIELDS: Record<number, (keyof FormValues)[]> = {
  0: ["name", "slug"],
  1: [],
  2: [],
  3: [],
}

// ══════════════════════════════════════════════════════════════════════════
// Magic Words of Binding (Props)
// ══════════════════════════════════════════════════════════════════════════

interface AgentusFormulaicusProps {
  mode: "create" | "edit"
  defaultValues?: UserAgentConfigPublic
  onSubmit: (data: AgentFormData) => void | Promise<void>
  isSubmitting?: boolean
  className?: string
}

// ══════════════════════════════════════════════════════════════════════════
// Minions of Enlightenment and Despair (Helpers)
// ══════════════════════════════════════════════════════════════════════════

function safeJsonStringify(v: unknown): string {
  if (v == null) return ""
  try { return JSON.stringify(v, null, 2) } catch { return "" }
}

function safeJsonParse(v: string | null): Record<string, unknown> | null {
  if (!v?.trim()) return null
  try { return JSON.parse(v) } catch { return null }
}

/** Thin field wrapper — label + input + error. No ceremony. */
function Field({
  name,
  label,
  children,
  className,
}: {
  name: string
  label?: string
  children: React.ReactNode
  className?: string
}) {
  const { formState } = useFormContext<FormValues>()
  const error = formState.errors[name as keyof FormValues]

  return (
    <div className={cn("space-y-1.5", className)}>
      {label && (
        <Label htmlFor={name} className="text-xs tracking-wide text-muted-foreground">
          {label}
        </Label>
      )}
      {children}
      {error?.message && (
        <p className="text-xs text-destructive">{error.message as string}</p>
      )}
    </div>
  )
}

/** Toggle row — label left, switch right. */
function ToggleRow({
  label,
  hint,
  checked,
  onChange,
}: {
  label: string
  hint?: string
  checked: boolean
  onChange: (v: boolean) => void
}) {
  return (
    <div className="flex items-center justify-between py-2">
      <div>
        <span className="text-sm">{label}</span>
        {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
      </div>
      <Switch checked={checked} onCheckedChange={onChange} />
    </div>
  )
}

// ══════════════════════════════════════════════════════════════════════════
// The Four Sigils (Step Indicator)
// ══════════════════════════════════════════════════════════════════════════

const SIGILS = ["✦", "⚡", "✍", "☽"]
const CHAPTER_NAMES = [
  "That Fancy Wonder",
  "Wherewithal",
  "The Incantation",
  "Temperament & Arcana",
]

function StepIndicator({
  current,
  onNavigate,
}: {
  current: number
  onNavigate: (i: number) => void
}) {
  return (
    <div className="flex items-center justify-center gap-1">
      {SIGILS.map((sigil, i) => (
        <button
          key={i}
          type="button"
          onClick={() => onNavigate(i)}
          title={CHAPTER_NAMES[i]}
          className={cn(
            "relative flex items-center justify-center size-9 rounded-full text-sm transition-all duration-300 select-none",
            i === current
              ? "bg-primary text-primary-foreground scale-110 shadow-md"
              : i < current
                ? "bg-primary/15 text-primary hover:bg-primary/25"
                : "bg-muted text-muted-foreground hover:bg-muted/80",
          )}
        >
          {sigil}
          {i < SIGILS.length - 1 && (
            <div
              className={cn(
                "absolute left-full top-1/2 w-4 h-px -translate-y-1/2",
                i < current ? "bg-primary/30" : "bg-border",
              )}
            />
          )}
        </button>
      ))}
    </div>
  )
}

// ══════════════════════════════════════════════════════════════════════════
// Chapter I: Who Is That Fancy Wonder?
// ══════════════════════════════════════════════════════════════════════════

function ChapterIdentity({ isEdit }: { isEdit: boolean }) {
  const { register, watch, setValue } = useFormContext<FormValues>()
  const [slugLoading, setSlugLoading] = useState(false)
  const slugFetched = useRef(false)

  const fetchSlug = useCallback(async () => {
    if (slugLoading) return
    setSlugLoading(true)
    try {
      const res = await AgentsService.generateAgentSlug()
      const slug = typeof res === "string" ? res : (res as { slug?: string })?.slug
      if (slug) setValue("slug", slug, { shouldValidate: true })
    } catch { /* slug stays empty, zod catches it */ }
    finally { setSlugLoading(false) }
  }, [setValue, slugLoading])

  useEffect(() => {
    if (isEdit || slugFetched.current || watch("slug")) return
    slugFetched.current = true
    void fetchSlug()
  }, [isEdit, watch, fetchSlug])

  const slug = watch("slug")
  const desc = watch("description")

  return (
    <div className="space-y-5">
      <Field name="name" label="Name">
        <Input
          id="name"
          {...register("name")}
          placeholder="What shall we call this one?"
          autoFocus
          className="text-base"
        />
      </Field>

      <div className="flex items-center gap-3">
        <div className="flex-1 px-3 py-2 rounded-md bg-muted font-mono text-sm text-muted-foreground truncate">
          {slug ? `@${slug}` : "inscribing..."}
        </div>
        {!isEdit && (
          <Button
            type="button"
            size="sm"
            variant="ghost"
            onClick={() => void fetchSlug()}
            disabled={slugLoading}
            className="shrink-0 text-xs"
          >
            {slugLoading ? "..." : "reroll"}
          </Button>
        )}
      </div>

      <Field name="description" label="Description">
        <Textarea
          id="description"
          {...register("description")}
          placeholder="A brief account of its purpose and peculiarities."
          maxLength={500}
          className="min-h-[80px] resize-none"
        />
        <div className="text-right text-[10px] text-muted-foreground">
          {desc?.length ?? 0}/500
        </div>
      </Field>
    </div>
  )
}

// ══════════════════════════════════════════════════════════════════════════
// Chapter II: Wherewithal
// ══════════════════════════════════════════════════════════════════════════

function ChapterBinding({ defaultModel }: { defaultModel: string }) {
  const { watch, setValue } = useFormContext<FormValues>()

  const handleProviderChange = (id: string | null) =>
    setValue("user_access_provider", id, { shouldValidate: true })

  const handleProviderResolved = (p: UserAccessProviderPublic | null) => {
    if (p?.alpha_provider_type_id)
      setValue("provider_type", p.alpha_provider_type_id, { shouldValidate: true })
  }

  const handleModelChange = (v: string | null) =>
    setValue("model_id", v, { shouldValidate: true })

  const handleModelSelected = (m: LLMModelPublic | null) => {
    if (m) {
      setValue("model_name", m.model_id ?? m.display_name ?? "")
      setValue("model", m.model_id ?? null)
      setValue("model_id", m.id, { shouldValidate: true })
    } else {
      setValue("model_name", "")
      setValue("model", null)
      setValue("model_id", null)
    }
  }

  return (
    <div className="space-y-2">
      <p className="text-xs text-muted-foreground">
        Choose the power source. System default requires no key.
      </p>
      <ProviderModelSelector
        providerId={watch("user_access_provider")}
        modelName={watch("model_id")}
        agentDefaultModel={defaultModel}
        onProviderChange={handleProviderChange}
        onModelChange={handleModelChange}
        onModelSelected={handleModelSelected}
        onProviderResolved={handleProviderResolved}
        size="compact"
      />
    </div>
  )
}

// ══════════════════════════════════════════════════════════════════════════
// Chapter III: The Incantation
// ══════════════════════════════════════════════════════════════════════════

function ChapterVoice() {
  const { register, watch } = useFormContext<FormValues>()
  const [showExtras, setShowExtras] = useState(false)
  const prompt = watch("system_prompt")

  return (
    <div className="space-y-4">
      <Field name="system_prompt" label="System Prompt">
        <Textarea
          id="system_prompt"
          {...register("system_prompt")}
          placeholder="You are..."
          className="min-h-[180px] font-mono text-sm resize-none"
        />
        {prompt && (
          <span className="text-[10px] text-muted-foreground">
            {prompt.length} chars
          </span>
        )}
      </Field>

      <button
        type="button"
        onClick={() => setShowExtras(!showExtras)}
        className="text-xs text-muted-foreground hover:text-foreground transition-colors"
      >
        {showExtras ? "− hide extras" : "+ override & instructions"}
      </button>

      <AnimatePresence>
        {showExtras && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden space-y-4"
          >
            <Field name="custom_system_prompt" label="System Prompt Override">
              <Textarea
                {...register("custom_system_prompt")}
                placeholder="Replaces the system prompt entirely..."
                className="min-h-[80px] font-mono text-sm resize-none"
              />
            </Field>

            <Field name="instructions" label="Instructions">
              <Textarea
                {...register("instructions")}
                placeholder="Supplementary context appended to the prompt..."
                className="min-h-[80px] font-mono text-sm resize-none"
              />
            </Field>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// ══════════════════════════════════════════════════════════════════════════
// Chapter IV: Temperament & Arcana
// ══════════════════════════════════════════════════════════════════════════

const PARTICIPATION_MODES = [
  { value: "on_mention", label: "say my name", icon: "@" },
  { value: "always", label: "chatterer", icon: "⚡" },
  { value: "manual", label: "when summoned", icon: "🎯" },
] as const

const SCOPE_OPTIONS = [
  { value: "personal", label: "yourn" },
  { value: "system", label: "theirn" },
] as const

function ChapterNature() {
  const { register, watch, setValue } = useFormContext<FormValues>()
  const [showArcana, setShowArcana] = useState(false)

  const mode = watch("participation_mode")
  const scope = watch("scope")

  return (
    <div className="space-y-5">
      {/* Participation Mode — toggle group */}
      <div className="space-y-1.5">
        <Label className="text-xs tracking-wide text-muted-foreground">
          Disposition
        </Label>
        <ToggleGroup
          type="single"
          value={mode}
          onValueChange={(v) => v && setValue("participation_mode", v)}
          className="w-full"
        >
          {PARTICIPATION_MODES.map((m) => (
            <ToggleGroupItem
              key={m.value}
              value={m.value}
              className="flex-1 gap-1.5 text-xs"
            >
              <span>{m.icon}</span>
              <span>{m.label}</span>
            </ToggleGroupItem>
          ))}
        </ToggleGroup>
      </div>

      {/* Scope — toggle group */}
      <div className="space-y-1.5">
        <Label className="text-xs tracking-wide text-muted-foreground">
          Dominion
        </Label>
        <ToggleGroup
          type="single"
          value={scope}
          onValueChange={(v) => v && setValue("scope", v)}
          className="w-full"
        >
          {SCOPE_OPTIONS.map((s) => (
            <ToggleGroupItem
              key={s.value}
              value={s.value}
              className="flex-1 text-xs"
            >
              {s.label}
            </ToggleGroupItem>
          ))}
        </ToggleGroup>
      </div>

      {/* Toggle rows */}
      <div className="divide-y divide-border">
        <ToggleRow
          label="Awakened"
          hint="Active and ready"
          checked={watch("is_enabled")}
          onChange={(v) => setValue("is_enabled", v)}
        />
        <ToggleRow
          label="Visible"
          hint="Appears in listings"
          checked={watch("is_visible")}
          onChange={(v) => setValue("is_visible", v)}
        />
        <ToggleRow
          label="Clonable"
          hint="Others may copy this configuration"
          checked={watch("is_clonable")}
          onChange={(v) => setValue("is_clonable", v)}
        />
        <ToggleRow
          label="Coordinator"
          hint="Can orchestrate other agents"
          checked={watch("is_coordinator")}
          onChange={(v) => setValue("is_coordinator", v)}
        />
      </div>

      {/* Tool iterations */}
      <div className="flex items-center justify-between">
        <Label className="text-xs text-muted-foreground">
          Max tool loops
        </Label>
        <Input
          type="number"
          min={0}
          max={100}
          {...register("max_tool_iterations")}
          className="w-20 h-8 text-center text-sm"
        />
      </div>

      {/* Arcana */}
      <button
        type="button"
        onClick={() => setShowArcana(!showArcana)}
        className="text-xs text-muted-foreground hover:text-foreground transition-colors"
      >
        {showArcana ? "− seal the arcana" : "+ reveal the arcana"}
      </button>

      <AnimatePresence>
        {showArcana && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden space-y-4"
          >
            <Field name="capabilities_raw" label="Capabilities">
              <Input
                {...register("capabilities_raw")}
                placeholder="web_search, code_execution, ..."
                className="text-sm font-mono"
              />
            </Field>

            <Field name="tool_config_raw" label="Tool Config">
              <Textarea
                {...register("tool_config_raw")}
                placeholder='{"tools": []}'
                className="min-h-[70px] font-mono text-xs resize-none"
              />
            </Field>

            <Field name="deps_config_raw" label="Dependencies Config">
              <Textarea
                {...register("deps_config_raw")}
                placeholder='{"dependencies": {}}'
                className="min-h-[70px] font-mono text-xs resize-none"
              />
            </Field>

            <Field name="agent_metadata_raw" label="Agent Metadata">
              <Textarea
                {...register("agent_metadata_raw")}
                placeholder='{"key": "value"}'
                className="min-h-[70px] font-mono text-xs resize-none"
              />
            </Field>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// ══════════════════════════════════════════════════════════════════════════
// The Augur, The Compass, The Dark Dagger (Component)
// ══════════════════════════════════════════════════════════════════════════

export default function AgentusFormulaicus({
  mode,
  defaultValues: dv,
  onSubmit,
  isSubmitting = false,
  className,
}: AgentusFormulaicusProps) {
  const isEdit = mode === "edit"
  const reduceMotion = useReduceMotion()
  const [chapter, setChapter] = useState(0)
  const [direction, setDirection] = useState(1) // 1 = forward, -1 = back

  // ── Tracing the Lines of Magic (Form Setup) ─────────────────────────

  const form = useForm({
    resolver: zodResolver(schema),
    mode: "onBlur",
    defaultValues: {
      name: dv?.name ?? "",
      slug: dv?.slug ?? "",
      description: dv?.description ?? "",
      user_access_provider: dv?.user_access_provider ?? null,
      provider_type: dv?.provider_type ?? "",
      model: dv?.model ?? null,
      model_id: dv?.model_id ?? null,
      model_name: dv?.model_name ?? "",
      system_prompt: dv?.system_prompt ?? "",
      custom_system_prompt: dv?.custom_system_prompt ?? null,
      instructions: dv?.instructions ?? null,
      participation_mode: dv?.participation_mode ?? "on_mention",
      scope: dv?.scope ?? "personal",
      is_enabled: dv?.is_enabled ?? true,
      is_clonable: dv?.is_clonable ?? false,
      is_visible: dv?.is_visible ?? true,
      is_coordinator: dv?.is_coordinator ?? false,
      max_tool_iterations: dv?.max_tool_iterations ?? 10,
      capabilities_raw: dv?.capabilities?.join(", ") ?? "",
      tool_config_raw: safeJsonStringify(dv?.tool_config),
      deps_config_raw: safeJsonStringify(dv?.deps_config),
      agent_metadata_raw: safeJsonStringify(dv?.agent_metadata),
    },
  })

  // ── Navigation ──────────────────────────────────────────────────────

  const goTo = async (target: number) => {
    // Validate current chapter fields before moving forward
    if (target > chapter) {
      const fields = CHAPTER_FIELDS[chapter] ?? []
      if (fields.length > 0) {
        const ok = await form.trigger(fields)
        if (!ok) return
      }
    }
    setDirection(target > chapter ? 1 : -1)
    setChapter(target)
  }

  const prev = () => goTo(chapter - 1)
  const next = () => goTo(chapter + 1)

  // ── Invoke thy Mighty Masterwork (Submit) ───────────────────────────

  const handleSubmit = form.handleSubmit(async (v) => {
    const capabilities = v.capabilities_raw
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean)

    const data: AgentFormData = {
      name: v.name,
      slug: v.slug,
      description: v.description,
      user_access_provider: v.user_access_provider || null,
      provider_type: v.provider_type,
      model: v.model || null,
      model_id: v.model_id || null,
      model_name: v.model_name || undefined,
      system_prompt: v.system_prompt,
      custom_system_prompt: v.custom_system_prompt || null,
      instructions: v.instructions || null,
      participation_mode: v.participation_mode,
      scope: v.scope,
      is_enabled: v.is_enabled,
      is_clonable: v.is_clonable,
      is_visible: v.is_visible,
      is_coordinator: v.is_coordinator,
      max_tool_iterations: v.max_tool_iterations,
      capabilities,
      tool_config: safeJsonParse(v.tool_config_raw),
      deps_config: safeJsonParse(v.deps_config_raw),
      agent_metadata: safeJsonParse(v.agent_metadata_raw),
    }

    await onSubmit(data)
  })

  // ── Animation config ────────────────────────────────────────────────

  const motionProps = reduceMotion
    ? {}
    : {
        initial: { x: direction * 60, opacity: 0 },
        animate: { x: 0, opacity: 1 },
        exit: { x: direction * -60, opacity: 0 },
        transition: { ...springConfig.snappy, stiffness: 400 },
      }

  // ── Render ──────────────────────────────────────────────────────────

  const chapters = [
    <ChapterIdentity key="identity" isEdit={isEdit} />,
    <ChapterBinding key="binding" defaultModel={dv?.model_name ?? ""} />,
    <ChapterVoice key="voice" />,
    <ChapterNature key="nature" />,
  ]

  const isLast = chapter === chapters.length - 1
  const isFirst = chapter === 0

  return (
    <FormProvider {...form}>
      <form onSubmit={handleSubmit} className={cn("flex flex-col gap-6", className)}>
        {/* Sigils */}
        <StepIndicator current={chapter} onNavigate={(i) => goTo(i)} />

        {/* Chapter title */}
        <div className="text-center">
          <h3 className="text-sm font-medium tracking-wide">
            {CHAPTER_NAMES[chapter]}
          </h3>
          <p className="text-[11px] text-muted-foreground mt-0.5">
            chapter {chapter + 1} of {chapters.length}
          </p>
        </div>

        {/* Active chapter */}
        <div className="relative min-h-[280px]">
          <AnimatePresence mode="wait" custom={direction}>
            <motion.div key={chapter} {...motionProps}>
              {chapters[chapter]}
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-between pt-2 border-t border-border">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={prev}
            disabled={isFirst}
            className="gap-1"
          >
            <ArrowLeftIcon className="size-3" />
            back
          </Button>

          {isLast ? (
            <Button
              type="submit"
              size="sm"
              disabled={isSubmitting}
              className="gap-1.5"
            >
              {isSubmitting ? (
                <Loader2 className="size-3 animate-spin" />
              ) : (
                <SparklesIcon className="size-3" />
              )}
              {isEdit ? "reforge" : "conjure"}
            </Button>
          ) : (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => void next()}
              className="gap-1"
            >
              next
              <ArrowRightIcon className="size-3" />
            </Button>
          )}
        </div>
      </form>
    </FormProvider>
  )
}
