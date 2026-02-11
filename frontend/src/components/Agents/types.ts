import type { UserAgentConfigPublic } from "@/client"

// ── Core Agent Data ───────────────────────────────────────────────────────
// Interim type that accepts BOTH loose API data (existing agents) AND strict typed data (new agents).
// Uses Omit to avoid intersection conflicts, then re-adds fields accepting both forms.
// Components use type guards (isAgentTypeKey, etc.) to narrow at runtime.
// When backend enforces strict types, we can simplify this.

export type UserAgentConfigData = Omit<UserAgentConfigPublic, 'agent_type' | 'presentation'> & {
  // Accepts API string OR narrow AgentTypeKey - use isAgentTypeKey() to narrow at runtime
  agent_type?: AgentTypeKey | string | null
  // Accepts API generic object OR structured AgentPresentation
  presentation?: AgentPresentation | { [key: string]: unknown } | null
}

// Strict variant for agent creation/validation where we require proper types
export type StrictAgentConfig = Omit<UserAgentConfigPublic, 'agent_type' | 'presentation'> & {
  agent_type: AgentTypeKey
  presentation?: AgentPresentation | null
}

// ── Narrowing Types ───────────────────────────────────────────────────────
// Backend stores these as strings. Frontend narrows for exhaustive switches
// and badge config lookups. No enums in the DB — these are declarative only.

export type AgentScope = "system" | "personal"
export type ParticipationMode = "always" | "on_mention" | "manual"
export type AgentTypeKey = "advisor" | "creative" | "analyst" | "guardian" | "oracle" | "engineer"

export function isAgentScope(s: string | null | undefined): s is AgentScope {
  return s === "system" || s === "personal"
}

export function isParticipationMode(s: string | null | undefined): s is ParticipationMode {
  return s === "always" || s === "on_mention" || s === "manual"
}

export function isAgentTypeKey(s: string | null | undefined): s is AgentTypeKey {
  return s === "advisor" || s === "creative" || s === "analyst"
    || s === "guardian" || s === "oracle" || s === "engineer"
}

// ── Presentation-as-Data Types ────────────────────────────────────────────
//
// Visual identity data that travels with an agent instance.
// All color values use oklch() format to match the project's design token system.
//
// Resolution order (lowest → highest):
//   1. Ambient page theme (CSS variables on ancestor container)
//   2. Agent type defaults (e.g., all "advisor" agents get green accent)
//   3. Agent instance presentation (creator's customization)

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
  "--foreground"?: string
  "--border"?: string
  "--muted"?: string
  "--muted-foreground"?: string
  "--secondary"?: string
  "--secondary-foreground"?: string
  "--accent"?: string
  "--accent-foreground"?: string

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
