/**
 * Page Themes
 *
 * Theme tokens for page-level styling.
 * These INCLUDE --background to control the page surface.
 *
 * Page themes control the entire page including header and content area backgrounds.
 * Card themes (C layer) can override card-specific variables within the page.
 *
 * All color values use oklch() to match the project's design token system.
 */

import type React from "react"
import { presentationToStyle } from "./resolve"
import type { PresentationTokens } from "./types"

export interface PageTheme {
  id: string
  name: string
  description?: string
  tokens: PresentationTokens
}

/**
 * Convert theme tokens to inline style for wrapper div.
 * Uses the same mechanism as AgentCard presentation.
 */
export function getPageThemeStyle(
  theme: PageTheme,
): React.CSSProperties | undefined {
  return presentationToStyle(theme.tokens)
}

/**
 * Page themes for the cascade system.
 *
 * Page themes control the B layer (page surface).
 * They MUST include --background for proper cascade behavior.
 *
 * "default" is empty — defers to application theme (:root).
 */
export const PAGE_THEMES: PageTheme[] = [
  // ═══════════════════════════════════════════════════════════════════════════
  // Default - inherits from application theme
  // ═══════════════════════════════════════════════════════════════════════════
  {
    id: "default",
    name: "Default",
    description: "Application theme",
    tokens: {},
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // Core Page Themes
  // ═══════════════════════════════════════════════════════════════════════════
  {
    id: "midnight",
    name: "Midnight",
    description: "Deep blue-violet dark surface",
    tokens: {
      "--background": "oklch(0.15 0.03 280)",
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
      "--background": "oklch(0.97 0.02 75)",
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
      "--background": "oklch(0.13 0.04 155)",
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
      "--background": "oklch(0.98 0.01 230)",
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
      "--background": "oklch(0.17 0.01 250)",
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
  // Demo-Themes CSS Conversions
  // ═══════════════════════════════════════════════════════════════════════════
  {
    id: "enchanted-rose",
    name: "Enchanted Rose",
    description: "Warm romantic pink tones",
    tokens: {
      "--background": "oklch(0.97 0.02 350)",
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
    },
  },
  {
    id: "dark-forest",
    name: "Dark Forest",
    description: "Moody emerald and amber",
    tokens: {
      "--background": "oklch(0.15 0.04 160)",
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
    },
  },
  {
    id: "ancient-tome",
    name: "Ancient Tome",
    description: "Parchment sepia tones",
    tokens: {
      "--background": "oklch(0.96 0.02 80)",
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
    },
  },
  {
    id: "gruvbox",
    name: "Gruvbox",
    description: "Classic warm retro palette",
    tokens: {
      "--background": "oklch(0.22 0.02 60)",
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
    },
  },
  {
    id: "dracula",
    name: "Dracula",
    description: "Rich purples and soft pinks",
    tokens: {
      "--background": "oklch(0.22 0.03 280)",
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
    },
  },
  {
    id: "bauhaus",
    name: "Bauhaus",
    description: "Bold primary colors, geometric",
    tokens: {
      "--background": "oklch(0.96 0 0)",
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
    },
  },
  {
    id: "dekonstruct",
    name: "Dekonstruct",
    description: "Fragmented brutalist aesthetic",
    tokens: {
      "--background": "oklch(0.94 0 0)",
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
    },
  },
  {
    id: "medieval",
    name: "Medieval",
    description: "Illuminated manuscript style",
    tokens: {
      "--background": "oklch(0.93 0.03 70)",
      "--card": "oklch(0.95 0.03 70)",
      "--card-foreground": "oklch(0.25 0.08 30)",
      "--foreground": "oklch(0.20 0.06 30)",
      "--border": "oklch(0.70 0.12 70)",
      "--muted": "oklch(0.92 0.03 70)",
      "--muted-foreground": "oklch(0.45 0.06 45)",
      "--secondary": "oklch(0.22 0.04 280)",
      "--secondary-foreground": "oklch(0.80 0.10 70)",
      "--accent": "oklch(0.45 0.15 30)",
      "--accent-foreground": "oklch(0.95 0.02 70)",
    },
  },
  {
    id: "math",
    name: "Math",
    description: "LaTeX-inspired academic",
    tokens: {
      "--background": "oklch(0.99 0 0)",
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
    },
  },
  {
    id: "technorave",
    name: "Technorave",
    description: "Cyberpunk neon on black",
    tokens: {
      "--background": "oklch(0.08 0 0)",
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
    },
  },
  {
    id: "spiritual-math",
    name: "Spiritual Math",
    description: "Sacred geometry meets mathematics",
    tokens: {
      "--background": "oklch(0.18 0.05 280)",
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
    },
  },
  {
    id: "terminal",
    name: "Terminal",
    description: "Green phosphor CRT aesthetic",
    tokens: {
      "--background": "oklch(0.08 0.01 145)",
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
    },
  },
  {
    id: "vaporwave",
    name: "Vaporwave",
    description: "Retro-futurist pastels",
    tokens: {
      "--background": "oklch(0.15 0.06 310)",
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
    },
  },
]

/** Look up a theme by ID. Returns default if not found. */
export function getPageThemeById(id: string): PageTheme {
  return PAGE_THEMES.find((t) => t.id === id) ?? PAGE_THEMES[0]
}
