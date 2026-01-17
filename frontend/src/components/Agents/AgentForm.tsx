/**
 * AgentForm Component
 *
 * Shared form for creating and editing agents.
 * Features:
 * - Name and slug inputs (slug auto-generated from name if empty)
 * - Description textarea
 * - Model selector dropdown
 * - System prompt textarea with character count
 * - Participation mode selector
 */

import { ChevronDownIcon } from "lucide-react"
import { useEffect, useState } from "react"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"
import type { AgentViewModel, ParticipationMode } from "@/services/agentService"
import {
  type LLMProviderType,
  PROVIDER_TYPE_LABELS,
  SUPPORTED_MODELS,
} from "@/services/llmProviderService"

// Available models - now sourced from llmProviderService
const AVAILABLE_MODELS = Object.entries(SUPPORTED_MODELS).flatMap(
  ([, models]) => models,
)

// Participation modes
const PARTICIPATION_MODES = [
  {
    value: "on_mention",
    label: "On Mention",
    description: "Responds when @mentioned",
  },
  {
    value: "always",
    label: "Always Active",
    description: "Responds to all messages",
  },
  {
    value: "manual",
    label: "Manual",
    description: "Only responds when explicitly triggered",
  },
] as const

export interface AgentFormData {
  name: string
  slug: string
  description: string
  model_name: string
  system_prompt: string
  participation_mode: ParticipationMode
}

interface AgentFormProps {
  /** Initial values (for edit mode) */
  initialData?: Partial<AgentViewModel>
  /** Called when form data changes */
  onChange: (data: AgentFormData) => void
  /** Whether this is edit mode (affects slug editability) */
  isEditMode?: boolean
  /** Additional classes */
  className?: string
}

/**
 * Generate a slug from a name
 * "Story Advisor" -> "story-advisor"
 */
function generateSlug(name: string): string {
  return name
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, "") // Remove special chars
    .replace(/\s+/g, "-") // Replace spaces with hyphens
    .replace(/-+/g, "-") // Remove duplicate hyphens
    .slice(0, 50) // Limit length
}

export default function AgentForm({
  initialData,
  onChange,
  isEditMode = false,
  className,
}: AgentFormProps) {
  const [name, setName] = useState(initialData?.name || "")
  const [slug, setSlug] = useState(initialData?.slug || "")
  const [slugManuallyEdited, setSlugManuallyEdited] = useState(false)
  const [description, setDescription] = useState(initialData?.description || "")
  const [modelName, setModelName] = useState(
    initialData?.model_name || "openai:gpt-4o-mini",
  )
  const [systemPrompt, setSystemPrompt] = useState(
    initialData?.system_prompt || "",
  )
  const [participationMode, setParticipationMode] = useState<ParticipationMode>(
    initialData?.participation_mode || "on_mention",
  )

  // Auto-generate slug from name (only in create mode and if not manually edited)
  useEffect(() => {
    if (!isEditMode && !slugManuallyEdited && name) {
      setSlug(generateSlug(name))
    }
  }, [name, isEditMode, slugManuallyEdited])

  // Notify parent of changes
  useEffect(() => {
    onChange({
      name,
      slug,
      description,
      model_name: modelName,
      system_prompt: systemPrompt,
      participation_mode: participationMode,
    })
  }, [
    name,
    slug,
    description,
    modelName,
    systemPrompt,
    participationMode,
    onChange,
  ])

  const handleSlugChange = (value: string) => {
    setSlugManuallyEdited(true)
    // Sanitize slug as user types
    setSlug(value.toLowerCase().replace(/[^a-z0-9-]/g, ""))
  }

  return (
    <div className={cn("space-y-6", className)}>
      {/* Name */}
      <div className="space-y-2">
        <Label htmlFor="agent-name">
          Name <span className="text-destructive">*</span>
        </Label>
        <Input
          id="agent-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="My Helpful Agent"
          maxLength={100}
        />
        <p className="text-xs text-muted-foreground">
          Display name for your agent
        </p>
      </div>

      {/* Slug */}
      <div className="space-y-2">
        <Label htmlFor="agent-slug">
          Slug <span className="text-destructive">*</span>
        </Label>
        <Input
          id="agent-slug"
          value={slug}
          onChange={(e) => handleSlugChange(e.target.value)}
          placeholder="my-helpful-agent"
          maxLength={50}
          disabled={isEditMode}
          className={isEditMode ? "opacity-60" : ""}
        />
        <p className="text-xs text-muted-foreground">
          {isEditMode
            ? "Slug cannot be changed after creation"
            : "Unique identifier (auto-generated from name)"}
        </p>
      </div>

      {/* Description */}
      <div className="space-y-2">
        <Label htmlFor="agent-description">Description</Label>
        <Textarea
          id="agent-description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Describe what this agent does..."
          maxLength={500}
          className="min-h-[80px]"
        />
        <p className="text-xs text-muted-foreground text-right">
          {description.length}/500
        </p>
      </div>

      {/* Model Selector */}
      <div className="space-y-2">
        <Label htmlFor="agent-model">Model</Label>
        <Select value={modelName} onValueChange={setModelName}>
          <SelectTrigger id="agent-model" className="w-full">
            <SelectValue placeholder="Select a model" />
          </SelectTrigger>
          <SelectContent>
            {(
              Object.entries(SUPPORTED_MODELS) as [
                LLMProviderType,
                typeof AVAILABLE_MODELS,
              ][]
            ).map(([providerType, models]) => (
              <SelectGroup key={providerType}>
                <SelectLabel>{PROVIDER_TYPE_LABELS[providerType]}</SelectLabel>
                {models.map((model) => (
                  <SelectItem key={model.value} value={model.value}>
                    <div className="flex flex-col">
                      <span>{model.label}</span>
                      <span className="text-xs text-muted-foreground">
                        {model.description}
                      </span>
                    </div>
                  </SelectItem>
                ))}
              </SelectGroup>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* System Prompt */}
      <div className="space-y-2">
        <Label htmlFor="agent-prompt">System Prompt</Label>
        <Textarea
          id="agent-prompt"
          value={systemPrompt}
          onChange={(e) => setSystemPrompt(e.target.value)}
          placeholder="You are a helpful assistant that..."
          className="min-h-[150px] font-mono text-sm"
        />

        {/* Collapsible Preview */}
        {systemPrompt && (
          <Collapsible>
            <CollapsibleTrigger className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors">
              <ChevronDownIcon className="size-3" />
              Preview rendered prompt ({systemPrompt.length} chars)
            </CollapsibleTrigger>
            <CollapsibleContent>
              <div className="mt-2 p-3 rounded-md bg-muted text-sm whitespace-pre-wrap max-h-[200px] overflow-y-auto">
                {systemPrompt}
              </div>
            </CollapsibleContent>
          </Collapsible>
        )}

        <p className="text-xs text-muted-foreground">
          Instructions that define your agent's personality and behavior
        </p>
      </div>

      {/* Participation Mode */}
      <div className="space-y-2">
        <Label htmlFor="agent-mode">Participation Mode</Label>
        <Select
          value={participationMode}
          onValueChange={(v) => setParticipationMode(v as ParticipationMode)}
        >
          <SelectTrigger id="agent-mode" className="w-full">
            <SelectValue placeholder="Select mode" />
          </SelectTrigger>
          <SelectContent>
            {PARTICIPATION_MODES.map((mode) => (
              <SelectItem key={mode.value} value={mode.value}>
                <div className="flex flex-col">
                  <span>{mode.label}</span>
                  <span className="text-xs text-muted-foreground">
                    {mode.description}
                  </span>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  )
}

// Export constants for reuse
export { AVAILABLE_MODELS, PARTICIPATION_MODES, generateSlug }
