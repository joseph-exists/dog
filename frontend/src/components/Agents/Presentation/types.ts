/**
 * Presentation-as-Data Types
 *
 * Defines the shape of visual identity data that travels with an agent instance.
 * All color values use oklch() format to match the project's design token system.
 *
 * Resolution order (lowest → highest):
 *   1. Ambient page theme (CSS variables on ancestor container)
 *   2. Agent type defaults (e.g., all "advisor" agents get green accent)
 *   3. Agent instance presentation (creator's customization)
 */

/**
 * Semantic CSS variable overrides.
 * Keys map directly to the project's existing CSS variable names.
 * Values are oklch strings (e.g., "oklch(0.95 0.02 30)").
 *
 * When applied as inline style on a wrapper div, these override
 * the same-named variables that shadcn components read from.
 */
export interface PresentationTokens {
  // Card surface — overrides shadcn Card's bg-card, text-card-foreground, border
  "--card"?: string
  "--card-foreground"?: string
  "--border"?: string
  "--muted"?: string
  "--muted-foreground"?: string
  "--secondary"?: string
  "--secondary-foreground"?: string

  // Agent-specific accent — already defined in index.css
  "--agent-accent"?: string
  "--agent-accent-foreground"?: string

  // Extended: card-level visual properties (not in shadcn defaults)
  "--agent-card-shadow"?: string
  "--agent-card-radius"?: string
  "--agent-accent-position"?: "top" | "bottom" | "left" | "none"
  "--agent-accent-width"?: string
}

export interface AvatarPresentation {
  /** Custom emoji to display instead of initials */
  emoji?: string
  /** Override the hash-derived background color (oklch string) */
  backgroundColor?: string
}

export interface AgentPresentation {
  /** CSS variable token overrides */
  tokens?: PresentationTokens
  /** Avatar customization */
  avatar?: AvatarPresentation
  /** Typographic hint — component interprets, not raw CSS */
  decorationHint?: "warm" | "neon" | "precise" | "organic" | "brutalist" | "ethereal"
}

/**
 * Agent type defaults.
 * Every agent has a type (advisor, creative, analyst, etc.).
 * The type provides a baseline presentation that instances can override.
 */
export type AgentTypeKey = "advisor" | "creative" | "analyst" | "guardian" | "oracle" | "engineer"

export interface AgentWithPresentation {
  id: string
  name: string
  slug?: string
  description?: string | null
  scope?: "system" | "personal"
  participationMode?: "always" | "on_mention" | "manual"
  isEnabled?: boolean
  modelName?: string
  agentType?: AgentTypeKey
  creator?: string
  /** Instance-level presentation — set by the agent's creator */
  presentation?: AgentPresentation | null
}
