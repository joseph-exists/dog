/**
 * Presentation Resolution
 *
 * Merges presentation layers: type defaults → instance overrides.
 * Converts resolved presentation into inline CSS style objects.
 */

import type {
  AgentPresentation,
  AgentTypeKey,
  PresentationTokens,
  StoryPresentation,
  StoryTypeKey,
} from "./types"

/**
 * Type-level presentation defaults.
 * These provide baseline visual identity for each agent category.
 * Instance-level presentation overrides any values set here.
 */
export const STORY_TYPE_PRESENTATIONS: Record<StoryTypeKey, StoryPresentation> =
  {
    process: {
      tokens: {
        "--story-accent": "oklch(0.6 0.15 155)",
        "--story-accent-foreground": "oklch(1 0 0)",
      },
      avatar: { emoji: "🧭" },
      decorationHint: "organic",
    },
    dynamic: {
      tokens: {
        "--story-accent": "oklch(0.6 0.2 310)",
        "--story-accent-foreground": "oklch(1 0 0)",
      },
      avatar: { emoji: "🎨" },
      decorationHint: "warm",
    },
    analytic: {
      tokens: {
        "--story-accent": "oklch(0.6 0.15 240)",
        "--story-accent-foreground": "oklch(1 0 0)",
      },
      avatar: { emoji: "📊" },
      decorationHint: "precise",
    },
    safety: {
      tokens: {
        "--story-accent": "oklch(0.65 0.18 55)",
        "--story-accent-foreground": "oklch(1 0 0)",
      },
      avatar: { emoji: "🛡️" },
      decorationHint: "brutalist",
    },
    prediction: {
      tokens: {
        "--story-accent": "oklch(0.55 0.18 290)",
        "--story-accent-foreground": "oklch(1 0 0)",
      },
      avatar: { emoji: "🔮" },
      decorationHint: "ethereal",
    },
    review: {
      tokens: {
        "--story-accent": "oklch(0.8 0.16 85)",
        "--story-accent-foreground": "oklch(0.2 0 0)",
      },
      avatar: { emoji: "⚙️" },
      decorationHint: "neon",
    },
  }

export const AGENT_TYPE_PRESENTATIONS: Record<AgentTypeKey, AgentPresentation> =
  {
    advisor: {
      tokens: {
        "--agent-accent": "oklch(0.6 0.15 155)",
        "--agent-accent-foreground": "oklch(1 0 0)",
      },
      avatar: { emoji: "🧭" },
    },
    creative: {
      tokens: {
        "--agent-accent": "oklch(0.6 0.2 310)",
        "--agent-accent-foreground": "oklch(1 0 0)",
      },
      avatar: { emoji: "🎨" },
    },
    analyst: {
      tokens: {
        "--agent-accent": "oklch(0.6 0.15 240)",
        "--agent-accent-foreground": "oklch(1 0 0)",
      },
      avatar: { emoji: "📊" },
    },
    guardian: {
      tokens: {
        "--agent-accent": "oklch(0.65 0.18 55)",
        "--agent-accent-foreground": "oklch(1 0 0)",
      },
      avatar: { emoji: "🛡️" },
    },
    oracle: {
      tokens: {
        "--agent-accent": "oklch(0.55 0.18 290)",
        "--agent-accent-foreground": "oklch(1 0 0)",
      },
      avatar: { emoji: "🔮" },
    },
    engineer: {
      tokens: {
        "--agent-accent": "oklch(0.8 0.16 85)",
        "--agent-accent-foreground": "oklch(0.2 0 0)",
      },
      avatar: { emoji: "⚙️" },
    },
  }

/**
 * Merge presentation layers.
 * Later layers override earlier ones (shallow merge per sub-object).
 */
export function resolvePresentation(
  ...layers: (AgentPresentation | null | undefined)[]
): AgentPresentation {
  const result: AgentPresentation = {
    tokens: {},
    avatar: {},
    decorationHint: undefined,
  }

  for (const layer of layers) {
    if (!layer) continue
    if (layer.tokens) {
      result.tokens = { ...result.tokens, ...layer.tokens }
    }
    if (layer.avatar) {
      result.avatar = { ...result.avatar, ...layer.avatar }
    }
    if (layer.decorationHint) {
      result.decorationHint = layer.decorationHint
    }
  }

  return result
}

export function resolveStoryPresentation(
  ...layers: (StoryPresentation | null | undefined)[]
): StoryPresentation {
  const result: StoryPresentation = {
    tokens: {},
    avatar: {},
    decorationHint: undefined,
  }

  for (const layer of layers) {
    if (!layer) continue
    if (layer.tokens) {
      result.tokens = { ...result.tokens, ...layer.tokens }
    }
    if (layer.avatar) {
      result.avatar = { ...result.avatar, ...layer.avatar }
    }
    if (layer.decorationHint) {
      result.decorationHint = layer.decorationHint
    }
  }

  return result
}

/**
 * Convert presentation tokens to a React inline style object.
 * Only includes CSS custom properties — safe, scoped, no injection risk.
 *
 * When placed on a wrapper div, these override the CSS variables
 * that descendant shadcn components read from via Tailwind utilities.
 */
export function presentationToStyle(
  tokens?: PresentationTokens,
): React.CSSProperties | undefined {
  if (!tokens || Object.keys(tokens).length === 0) return undefined

  const style: Record<string, string> = {}
  for (const [key, value] of Object.entries(tokens)) {
    if (value !== undefined) {
      style[key] = value
    }
  }

  return style as unknown as React.CSSProperties
}

/**
 * Resolve the full presentation for an agent, given its type and instance data.
 */
export function resolveAgentPresentation(
  agentType?: AgentTypeKey,
  instancePresentation?: AgentPresentation | null,
): AgentPresentation {
  const typeDefaults = agentType
    ? AGENT_TYPE_PRESENTATIONS[agentType]
    : undefined
  return resolvePresentation(typeDefaults, instancePresentation)
}
