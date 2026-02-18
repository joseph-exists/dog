/**
 * Card Themes
 *
 * Theme tokens specifically for card-level styling.
 * These DO NOT include --background to preserve the page theme cascade.
 *
 * Card themes control: --card, --card-foreground, --border, --muted,
 * --foreground, --secondary, --accent, and agent-specific tokens.
 *
 * All color values use oklch() to match the project's design token system.
 */

import type React from "react"
import { presentationToStyle } from "./resolve"
import type { PresentationTokens } from "./types"

export interface CardTheme {
  id: string
  name: string
  description?: string
  tokens: PresentationTokens
  /** Optional avatar customization hint */
  avatar?: { emoji?: string; backgroundColor?: string }
  /** Optional decoration hint for typography/styling */
  decorationHint?:
    | "warm"
    | "neon"
    | "precise"
    | "organic"
    | "brutalist"
    | "ethereal"
}

/**
 * Convert theme tokens to inline style for wrapper div.
 * Uses the same mechanism as AgentCard presentation.
 */
export function getCardThemeStyle(
  theme: CardTheme,
): React.CSSProperties | undefined {
  return presentationToStyle(theme.tokens)
}

/**
 * Card themes for the cascade system.
 *
 * IMPORTANT: Do NOT include --background in card themes.
 * --background is controlled by the page theme (B layer).
 * Card themes only control card surfaces (C layer).
 *
 * "default" is empty — defers to upstream page theme.
 */
export const CARD_THEMES: CardTheme[] = [
  // ═══════════════════════════════════════════════════════════════════════════
  // Default - inherits from page theme
  // ═══════════════════════════════════════════════════════════════════════════
  {
    id: "default",
    name: "Upstream",
    description: "Inherit from page theme",
    tokens: {},
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // Core Card Themes
  // ═══════════════════════════════════════════════════════════════════════════
  {
    id: "midnight",
    name: "Midnight",
    description: "Deep blue-violet dark surface",
    tokens: {
      "--card": "oklch(0.18 0.03 280)",
      "--card-foreground": "oklch(0.92 0.01 280)",
      "--foreground": "oklch(0.90 0.01 280)",
      "--border": "oklch(0.28 0.03 280)",
      "--muted": "oklch(0.22 0.03 280)",
      "--muted-foreground": "oklch(0.62 0.02 280)",
      "--secondary": "oklch(0.25 0.04 280)",
      "--secondary-foreground": "oklch(0.88 0.01 280)",
      "--accent": "oklch(0.30 0.04 280)",
      "--accent-foreground": "oklch(0.92 0.01 280)",
    },
  },
  {
    id: "warm-sand",
    name: "Warm Sand",
    description: "Warm neutral light surface",
    tokens: {
      "--card": "oklch(0.95 0.02 75)",
      "--card-foreground": "oklch(0.20 0.02 75)",
      "--foreground": "oklch(0.18 0.02 75)",
      "--border": "oklch(0.85 0.03 75)",
      "--muted": "oklch(0.90 0.02 75)",
      "--muted-foreground": "oklch(0.45 0.02 75)",
      "--secondary": "oklch(0.88 0.03 75)",
      "--secondary-foreground": "oklch(0.25 0.02 75)",
      "--accent": "oklch(0.90 0.04 75)",
      "--accent-foreground": "oklch(0.20 0.02 75)",
    },
  },
  {
    id: "forest",
    name: "Forest",
    description: "Dark green surface",
    tokens: {
      "--card": "oklch(0.16 0.04 155)",
      "--card-foreground": "oklch(0.92 0.02 155)",
      "--foreground": "oklch(0.90 0.02 155)",
      "--border": "oklch(0.26 0.04 155)",
      "--muted": "oklch(0.20 0.03 155)",
      "--muted-foreground": "oklch(0.62 0.03 155)",
      "--secondary": "oklch(0.23 0.04 155)",
      "--secondary-foreground": "oklch(0.88 0.02 155)",
      "--accent": "oklch(0.28 0.05 155)",
      "--accent-foreground": "oklch(0.92 0.02 155)",
    },
  },
  {
    id: "cool-ocean",
    name: "Cool Ocean",
    description: "Cool blue-tinted light surface",
    tokens: {
      "--card": "oklch(0.97 0.015 230)",
      "--card-foreground": "oklch(0.15 0.03 230)",
      "--foreground": "oklch(0.15 0.03 230)",
      "--border": "oklch(0.88 0.02 230)",
      "--muted": "oklch(0.94 0.01 230)",
      "--muted-foreground": "oklch(0.5 0.02 230)",
      "--secondary": "oklch(0.93 0.015 230)",
      "--secondary-foreground": "oklch(0.2 0.03 230)",
      "--accent": "oklch(0.93 0.015 230)",
      "--accent-foreground": "oklch(0.2 0.03 230)",
    },
  },
  {
    id: "slate",
    name: "Slate",
    description: "Cool neutral dark surface",
    tokens: {
      "--card": "oklch(0.20 0.01 250)",
      "--card-foreground": "oklch(0.90 0.01 250)",
      "--foreground": "oklch(0.88 0.01 250)",
      "--border": "oklch(0.30 0.01 250)",
      "--muted": "oklch(0.24 0.01 250)",
      "--muted-foreground": "oklch(0.60 0.01 250)",
      "--secondary": "oklch(0.27 0.01 250)",
      "--secondary-foreground": "oklch(0.86 0.01 250)",
      "--accent": "oklch(0.32 0.02 250)",
      "--accent-foreground": "oklch(0.90 0.01 250)",
    },
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // Agent-Style Card Themes (with presentation features)
  // ═══════════════════════════════════════════════════════════════════════════
  {
    id: "oracle",
    name: "Oracle",
    description: "Mystical green with organic feel",
    tokens: {
      "--agent-accent": "oklch(0.6 0.15 150)",
      "--agent-accent-foreground": "oklch(1 0 0)",
      "--card": "oklch(0.97 0.015 145)",
      "--card-foreground": "oklch(0.18 0.03 150)",
      "--border": "oklch(0.85 0.03 145)",
      "--muted": "oklch(0.93 0.01 145)",
      "--muted-foreground": "oklch(0.5 0.02 150)",
      "--agent-card-shadow":
        "0 6px 24px oklch(0.5 0.1 150 / 0.07), 0 2px 6px oklch(0.5 0.08 150 / 0.04)",
      "--agent-card-radius": "20px",
      "--agent-accent-position": "top",
      "--agent-accent-width": "3px",
    },
    avatar: { emoji: "🌿", backgroundColor: "oklch(0.55 0.15 150)" },
    decorationHint: "organic",
  },
  {
    id: "whisper",
    name: "Whisper",
    description: "Soft ethereal lavender",
    tokens: {
      "--agent-accent": "oklch(0.65 0.1 290)",
      "--agent-accent-foreground": "oklch(1 0 0)",
      "--card": "oklch(0.98 0.008 290)",
      "--card-foreground": "oklch(0.25 0.02 290)",
      "--border": "oklch(0.92 0.015 290)",
      "--muted": "oklch(0.96 0.006 290)",
      "--muted-foreground": "oklch(0.55 0.03 290)",
      "--agent-card-shadow": "0 8px 32px oklch(0.5 0.08 290 / 0.05)",
      "--agent-card-radius": "24px",
      "--agent-accent-position": "none",
      "--agent-accent-width": "0px",
    },
    avatar: { emoji: "◯", backgroundColor: "oklch(0.65 0.1 290)" },
    decorationHint: "ethereal",
  },
  {
    id: "precise",
    name: "Precise",
    description: "Clean analytical blue",
    tokens: {
      "--agent-accent": "oklch(0.5 0.08 240)",
      "--agent-accent-foreground": "oklch(1 0 0)",
      "--card": "oklch(0.97 0.01 80)",
      "--card-foreground": "oklch(0.18 0.02 240)",
      "--border": "oklch(0.84 0.02 240)",
      "--muted": "oklch(0.94 0.008 80)",
      "--muted-foreground": "oklch(0.5 0.02 240)",
      "--agent-card-shadow": "0 1px 2px oklch(0.4 0.04 240 / 0.06)",
      "--agent-card-radius": "2px",
      "--agent-accent-position": "bottom",
      "--agent-accent-width": "2px",
    },
    avatar: { emoji: "🗺️", backgroundColor: "oklch(0.5 0.08 240)" },
    decorationHint: "precise",
  },
  {
    id: "neon",
    name: "Neon",
    description: "Electric cyberpunk glow",
    tokens: {
      "--agent-accent": "oklch(0.7 0.25 340)",
      "--agent-accent-foreground": "oklch(1 0 0)",
      "--card": "oklch(0.18 0.04 300)",
      "--card-foreground": "oklch(0.92 0.02 320)",
      "--border": "oklch(0.32 0.08 340)",
      "--muted": "oklch(0.22 0.03 300)",
      "--muted-foreground": "oklch(0.6 0.04 320)",
      "--secondary": "oklch(0.25 0.05 310)",
      "--secondary-foreground": "oklch(0.85 0.06 330)",
      "--foreground": "oklch(0.92 0.02 320)",
      "--agent-card-shadow":
        "0 0 25px oklch(0.65 0.25 340 / 0.12), 0 0 5px oklch(0.7 0.2 340 / 0.08)",
      "--agent-card-radius": "4px",
      "--agent-accent-position": "left",
      "--agent-accent-width": "4px",
    },
    avatar: { emoji: "⚡", backgroundColor: "oklch(0.65 0.25 340)" },
    decorationHint: "neon",
  },
  {
    id: "armadillo",
    name: "Armadillo",
    description: "Warm amber protective shell",
    tokens: {
      "--agent-accent": "oklch(0.65 0.14 55)",
      "--agent-accent-foreground": "oklch(1 0 0)",
      "--card": "oklch(0.96 0.015 60)",
      "--card-foreground": "oklch(0.2 0.02 50)",
      "--border": "oklch(0.85 0.04 55)",
      "--muted": "oklch(0.92 0.01 55)",
      "--muted-foreground": "oklch(0.5 0.02 50)",
      "--agent-card-shadow":
        "0 4px 20px oklch(0.5 0.1 55 / 0.1), 0 1px 3px oklch(0.5 0.08 55 / 0.06)",
      "--agent-card-radius": "14px",
      "--agent-accent-position": "top",
      "--agent-accent-width": "3px",
    },
    avatar: { emoji: "🦔", backgroundColor: "oklch(0.65 0.14 55)" },
    decorationHint: "warm",
  },
  {
    id: "axiom",
    name: "Axiom",
    description: "Brutalist black and yellow",
    tokens: {
      "--agent-accent": "oklch(0.85 0.17 90)",
      "--agent-accent-foreground": "oklch(0.15 0 0)",
      "--card": "oklch(0.97 0 0)",
      "--card-foreground": "oklch(0.12 0 0)",
      "--border": "oklch(0.7 0 0)",
      "--muted": "oklch(0.93 0 0)",
      "--muted-foreground": "oklch(0.45 0 0)",
      "--agent-card-shadow": "6px 6px 0 oklch(0.55 0.25 29)",
      "--agent-card-radius": "0px",
      "--agent-accent-position": "left",
      "--agent-accent-width": "6px",
    },
    avatar: { emoji: "◆", backgroundColor: "oklch(0.8 0.15 90)" },
    decorationHint: "brutalist",
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // Demo-Themes CSS Conversions
  // ═══════════════════════════════════════════════════════════════════════════
  {
    id: "enchanted-rose",
    name: "Enchanted Rose",
    description: "Warm romantic pink tones",
    tokens: {
      "--card": "oklch(0.95 0.03 350)",
      "--card-foreground": "oklch(0.30 0.12 350)",
      "--foreground": "oklch(0.28 0.10 350)",
      "--border": "oklch(0.80 0.10 350)",
      "--muted": "oklch(0.92 0.04 350)",
      "--muted-foreground": "oklch(0.45 0.08 350)",
      "--secondary": "oklch(0.90 0.06 350)",
      "--secondary-foreground": "oklch(0.32 0.10 350)",
      "--accent": "oklch(0.70 0.15 350)",
      "--accent-foreground": "oklch(0.98 0.01 350)",
      "--agent-card-shadow": "0 2px 8px oklch(0.65 0.15 350 / 0.12)",
      "--agent-card-radius": "12px",
    },
  },
  {
    id: "dark-forest",
    name: "Dark Forest",
    description: "Moody emerald and amber",
    tokens: {
      "--card": "oklch(0.22 0.05 160)",
      "--card-foreground": "oklch(0.92 0.04 160)",
      "--foreground": "oklch(0.85 0.04 160)",
      "--border": "oklch(0.35 0.06 160)",
      "--muted": "oklch(0.25 0.04 160)",
      "--muted-foreground": "oklch(0.65 0.05 160)",
      "--secondary": "oklch(0.28 0.05 160)",
      "--secondary-foreground": "oklch(0.88 0.04 160)",
      "--accent": "oklch(0.55 0.12 160)",
      "--accent-foreground": "oklch(0.95 0.02 160)",
      "--agent-card-shadow": "0 2px 8px oklch(0.35 0.08 160 / 0.2)",
      "--agent-card-radius": "8px",
    },
  },
  {
    id: "ancient-tome",
    name: "Ancient Tome",
    description: "Parchment sepia tones",
    tokens: {
      "--card": "oklch(0.94 0.03 80)",
      "--card-foreground": "oklch(0.28 0.05 45)",
      "--foreground": "oklch(0.22 0.04 45)",
      "--border": "oklch(0.65 0.10 45)",
      "--muted": "oklch(0.90 0.04 80)",
      "--muted-foreground": "oklch(0.45 0.06 45)",
      "--secondary": "oklch(0.88 0.05 80)",
      "--secondary-foreground": "oklch(0.30 0.05 45)",
      "--accent": "oklch(0.60 0.12 45)",
      "--accent-foreground": "oklch(0.95 0.02 80)",
      "--agent-card-radius": "4px",
    },
  },
  {
    id: "gruvbox",
    name: "Gruvbox",
    description: "Classic warm retro palette",
    tokens: {
      "--card": "oklch(0.28 0.02 60)",
      "--card-foreground": "oklch(0.88 0.04 80)",
      "--foreground": "oklch(0.85 0.03 80)",
      "--border": "oklch(0.38 0.02 60)",
      "--muted": "oklch(0.32 0.02 60)",
      "--muted-foreground": "oklch(0.60 0.02 60)",
      "--secondary": "oklch(0.35 0.02 60)",
      "--secondary-foreground": "oklch(0.82 0.03 80)",
      "--accent": "oklch(0.65 0.15 45)",
      "--accent-foreground": "oklch(0.92 0.02 80)",
      "--agent-card-shadow": "0 2px 6px oklch(0.1 0 0 / 0.3)",
      "--agent-card-radius": "8px",
    },
  },
  {
    id: "dracula",
    name: "Dracula",
    description: "Rich purples and soft pinks",
    tokens: {
      "--card": "oklch(0.32 0.03 280)",
      "--card-foreground": "oklch(0.95 0.01 0)",
      "--foreground": "oklch(0.95 0.01 0)",
      "--border": "oklch(0.45 0.04 260)",
      "--muted": "oklch(0.35 0.03 280)",
      "--muted-foreground": "oklch(0.55 0.04 260)",
      "--secondary": "oklch(0.40 0.03 280)",
      "--secondary-foreground": "oklch(0.92 0.01 0)",
      "--accent": "oklch(0.70 0.18 300)",
      "--accent-foreground": "oklch(0.98 0.01 0)",
      "--agent-card-shadow": "0 2px 8px oklch(0.1 0 0 / 0.4)",
      "--agent-card-radius": "8px",
    },
  },
  {
    id: "bauhaus",
    name: "Bauhaus",
    description: "Bold primary colors, geometric",
    tokens: {
      "--card": "oklch(1 0 0)",
      "--card-foreground": "oklch(0.15 0 0)",
      "--foreground": "oklch(0.15 0 0)",
      "--border": "oklch(0.15 0 0)",
      "--muted": "oklch(0.95 0 0)",
      "--muted-foreground": "oklch(0.40 0 0)",
      "--secondary": "oklch(0.85 0.20 90)",
      "--secondary-foreground": "oklch(0.15 0 0)",
      "--accent": "oklch(0.55 0.22 30)",
      "--accent-foreground": "oklch(1 0 0)",
      "--agent-card-shadow": "6px 6px 0 oklch(0.15 0 0)",
      "--agent-card-radius": "0px",
    },
    decorationHint: "brutalist",
  },
  {
    id: "dekonstruct",
    name: "Dekonstruct",
    description: "Fragmented brutalist aesthetic",
    tokens: {
      "--card": "oklch(1 0 0)",
      "--card-foreground": "oklch(0.12 0 0)",
      "--foreground": "oklch(0.25 0 0)",
      "--border": "oklch(0.12 0 0)",
      "--muted": "oklch(0.95 0 0)",
      "--muted-foreground": "oklch(0.45 0 0)",
      "--secondary": "oklch(0.90 0 0)",
      "--secondary-foreground": "oklch(0.15 0 0)",
      "--accent": "oklch(0.55 0.22 25)",
      "--accent-foreground": "oklch(1 0 0)",
      "--agent-card-shadow":
        "8px 8px 0 oklch(0.12 0 0), -2px -2px 0 oklch(0.55 0.22 25)",
      "--agent-card-radius": "0px",
    },
    decorationHint: "brutalist",
  },
  {
    id: "medieval",
    name: "Medieval",
    description: "Illuminated manuscript style",
    tokens: {
      "--card": "oklch(0.95 0.03 70)",
      "--card-foreground": "oklch(0.25 0.08 30)",
      "--foreground": "oklch(0.20 0.06 30)",
      "--border": "oklch(0.45 0.15 30)",
      "--muted": "oklch(0.92 0.03 70)",
      "--muted-foreground": "oklch(0.45 0.06 45)",
      "--secondary": "oklch(0.22 0.04 280)",
      "--secondary-foreground": "oklch(0.80 0.10 70)",
      "--accent": "oklch(0.70 0.12 70)",
      "--accent-foreground": "oklch(0.20 0.06 30)",
      "--agent-card-radius": "2px",
    },
  },
  {
    id: "math",
    name: "Math",
    description: "LaTeX-inspired academic",
    tokens: {
      "--card": "oklch(1 0 0)",
      "--card-foreground": "oklch(0.15 0 0)",
      "--foreground": "oklch(0.25 0 0)",
      "--border": "oklch(0.80 0 0)",
      "--muted": "oklch(0.97 0 0)",
      "--muted-foreground": "oklch(0.50 0 0)",
      "--secondary": "oklch(0.96 0.01 230)",
      "--secondary-foreground": "oklch(0.35 0.08 230)",
      "--accent": "oklch(0.55 0.15 250)",
      "--accent-foreground": "oklch(0.98 0 0)",
      "--agent-card-radius": "0px",
    },
    decorationHint: "precise",
  },
  {
    id: "technorave",
    name: "Technorave",
    description: "Cyberpunk neon on black",
    tokens: {
      "--card": "oklch(0.12 0 0)",
      "--card-foreground": "oklch(0.90 0 0)",
      "--foreground": "oklch(0.90 0 0)",
      "--border": "oklch(0.60 0.25 190)",
      "--muted": "oklch(0.15 0 0)",
      "--muted-foreground": "oklch(0.55 0 0)",
      "--secondary": "oklch(0.15 0 0)",
      "--secondary-foreground": "oklch(0.75 0.25 330)",
      "--accent": "oklch(0.70 0.25 330)",
      "--accent-foreground": "oklch(1 0 0)",
      "--agent-card-shadow": "0 0 10px oklch(0.60 0.25 190 / 0.3)",
      "--agent-card-radius": "0px",
    },
    decorationHint: "neon",
  },
  {
    id: "spiritual-math",
    name: "Spiritual Math",
    description: "Sacred geometry meets mathematics",
    tokens: {
      "--card": "oklch(0.25 0.05 280)",
      "--card-foreground": "oklch(0.85 0.05 260)",
      "--foreground": "oklch(0.80 0.05 260)",
      "--border": "oklch(0.65 0.12 70)",
      "--muted": "oklch(0.28 0.04 280)",
      "--muted-foreground": "oklch(0.65 0.06 260)",
      "--secondary": "oklch(0.30 0.05 280)",
      "--secondary-foreground": "oklch(0.82 0.05 260)",
      "--accent": "oklch(0.72 0.12 70)",
      "--accent-foreground": "oklch(0.15 0.04 280)",
      "--agent-card-shadow": "0 4px 15px oklch(0.65 0.10 70 / 0.1)",
      "--agent-card-radius": "50% / 10%",
    },
    decorationHint: "ethereal",
  },
  {
    id: "terminal",
    name: "Terminal",
    description: "Green phosphor CRT aesthetic",
    tokens: {
      "--card": "oklch(0.12 0.02 145)",
      "--card-foreground": "oklch(0.75 0.20 145)",
      "--foreground": "oklch(0.70 0.18 145)",
      "--border": "oklch(0.35 0.10 145)",
      "--muted": "oklch(0.15 0.02 145)",
      "--muted-foreground": "oklch(0.50 0.12 145)",
      "--secondary": "oklch(0.18 0.03 145)",
      "--secondary-foreground": "oklch(0.72 0.18 145)",
      "--accent": "oklch(0.75 0.22 145)",
      "--accent-foreground": "oklch(0.12 0.02 145)",
      "--agent-card-shadow": "0 0 8px oklch(0.65 0.18 145 / 0.1)",
      "--agent-card-radius": "0px",
    },
    decorationHint: "precise",
  },
  {
    id: "vaporwave",
    name: "Vaporwave",
    description: "Retro-futurist pastels",
    tokens: {
      "--card": "oklch(0.22 0.08 310)",
      "--card-foreground": "oklch(0.88 0.06 300)",
      "--foreground": "oklch(0.85 0.05 300)",
      "--border": "oklch(0.55 0.18 310)",
      "--muted": "oklch(0.25 0.06 310)",
      "--muted-foreground": "oklch(0.60 0.10 310)",
      "--secondary": "oklch(0.28 0.07 310)",
      "--secondary-foreground": "oklch(0.82 0.05 300)",
      "--accent": "oklch(0.70 0.22 350)",
      "--accent-foreground": "oklch(1 0 0)",
      "--agent-card-shadow": "0 4px 20px oklch(0.55 0.18 310 / 0.15)",
      "--agent-card-radius": "16px",
    },
    decorationHint: "neon",
  },
]

/** Look up a theme by ID. Returns default if not found. */
export function getCardThemeById(id: string): CardTheme {
  return CARD_THEMES.find((t) => t.id === id) ?? CARD_THEMES[0]
}
