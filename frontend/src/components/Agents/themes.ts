/**
 * Ambient Theme Stubs
 *
 * Typed theme data matching the future API shape.
 * Each theme that changes surface lightness includes the FULL variable surface
 * per Presentation/REFERENCE.md — partial overrides cause invisible text.
 *
 * All color values use oklch() to match the project's design token system.
 *
 * Migration path: when API endpoint exists, replace the static array with
 * a query. Interface stays the same. Components don't change.
 */

import { presentationToStyle } from "./resolve"
import type { PresentationTokens } from "./types"

export interface AmbientTheme {
  id: string
  name: string
  description?: string
  tokens: PresentationTokens
}

/**
 * Convert theme tokens to inline style for wrapper div.
 * Uses the same mechanism as AgentCard presentation.
 */
export function getThemeStyle(
  theme: AmbientTheme,
): React.CSSProperties | undefined {
  return presentationToStyle(theme.tokens)
}

/**
 * Stub themes for cascade proof.
 *
 * "default" is empty — defers to :root application theme.
 * All others include the complete variable surface.
 */
export const AMBIENT_THEMES: AmbientTheme[] = [
  {
    id: "default",
    name: "Default",
    description: "Application theme",
    tokens: {},
  },
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
    name: "cool ocean",
    description: "cool ocean no background",
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
]

/** Look up a theme by ID. Returns default if not found. */
export function getThemeById(id: string): AmbientTheme {
  return AMBIENT_THEMES.find((t) => t.id === id) ?? AMBIENT_THEMES[0]
}
