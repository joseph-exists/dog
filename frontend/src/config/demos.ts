// todo: this needs migrated to backend ASAP.
// then we just use these as exported client functions, types, and schema - and we
// can interact with it via cli or other means

export interface DemoConfig {
  slug: string
  title: string
  description: string
  roomId: string
  autoRespond: boolean
  /** Optional theme identifier. Maps to [data-demo-theme="X"] CSS overrides. */
  theme?: string
}

export const DEMOS: Record<string, DemoConfig> = {
  "story-runtime": {
    slug: "story-runtime",
    title: "Story Runtime Demo",
    description:
      "Interactive branching narrative with AI agents that see your story context.",
    roomId: "e23c1dae-12f2-43ed-86d9-34b0893f2385",
    autoRespond: true,
  },
  "story-runtime-rose": {
    slug: "story-runtime-rose",
    title: "The Enchanted Library",
    description: "A romantic retelling with rose-tinted atmosphere.",
    roomId: "e23c1dae-12f2-43ed-86d9-34b0893f2385",
    autoRespond: true,
    theme: "enchanted-rose",
  },
  "story-runtime-forest": {
    slug: "story-runtime-forest",
    title: "The Dark Forest Library",
    description: "The same story, reimagined in a deep emerald forest.",
    roomId: "e23c1dae-12f2-43ed-86d9-34b0893f2385",
    autoRespond: true,
    theme: "dark-forest",
  },
  "story-runtime-tome": {
    slug: "story-runtime-tome",
    title: "The Ancient Tome",
    description: "A parchment-and-ink aesthetic for the scholarly explorer.",
    roomId: "e23c1dae-12f2-43ed-86d9-34b0893f2385",
    autoRespond: true,
    theme: "ancient-tome",
  },
  "story-runtime-gruvbox": {
    slug: "story-runtime-gruvbox",
    title: "Gruvbox Library",
    description: "Warm retro palette — earthy browns and orange accents.",
    roomId: "e23c1dae-12f2-43ed-86d9-34b0893f2385",
    autoRespond: true,
    theme: "gruvbox",
  },
  "story-runtime-dracula": {
    slug: "story-runtime-dracula",
    title: "Dracula's Library",
    description: "Rich purples, soft pinks, and glowing cyans in the dark.",
    roomId: "e23c1dae-12f2-43ed-86d9-34b0893f2385",
    autoRespond: true,
    theme: "dracula",
  },
  "story-runtime-bauhaus": {
    slug: "story-runtime-bauhaus",
    title: "Bauhaus Library",
    description: "Bold primary colors, geometric precision, modernist design.",
    roomId: "e23c1dae-12f2-43ed-86d9-34b0893f2385",
    autoRespond: true,
    theme: "bauhaus",
  },
  "story-runtime-dekonstruct": {
    slug: "story-runtime-dekonstruct",
    title: "DEKONSTRUCT",
    description: "Fragmented, raw, angular. Controlled chaos in monospace.",
    roomId: "e23c1dae-12f2-43ed-86d9-34b0893f2385",
    autoRespond: true,
    theme: "dekonstruct",
  },
  "story-runtime-medieval": {
    slug: "story-runtime-medieval",
    title: "The Illuminated Library",
    description:
      "Deep crimsons, burnished golds, and royal navy. Ye olde narrative.",
    roomId: "e23c1dae-12f2-43ed-86d9-34b0893f2385",
    autoRespond: true,
    theme: "medieval",
  },
  "story-runtime-math": {
    slug: "story-runtime-math",
    title: "∴ The Library",
    description: "Clean mathematical precision. Graph paper, monospace, QED.",
    roomId: "e23c1dae-12f2-43ed-86d9-34b0893f2385",
    autoRespond: true,
    theme: "math",
  },
  "story-runtime-technorave": {
    slug: "story-runtime-technorave",
    title: "TECHNORAVE//LIBRARY",
    description: "Neon void. Cyan. Magenta. Acid. Maximum intensity.",
    roomId: "e23c1dae-12f2-43ed-86d9-34b0893f2385",
    autoRespond: true,
    theme: "technorave",
  },
  "story-runtime-spiritual-math": {
    slug: "story-runtime-spiritual-math",
    title: "The Sacred Library",
    description: "Where golden ratios meet transcendent geometry.",
    roomId: "e23c1dae-12f2-43ed-86d9-34b0893f2385",
    autoRespond: true,
    theme: "spiritual-math",
  },
  "story-runtime-terminal": {
    slug: "story-runtime-terminal",
    title: "library.exe",
    description: "Green phosphor on black. CRT scanlines. >_ ",
    roomId: "e23c1dae-12f2-43ed-86d9-34b0893f2385",
    autoRespond: true,
    theme: "terminal",
  },
  "story-runtime-vaporwave": {
    slug: "story-runtime-vaporwave",
    title: "T H E  L I B R A R Y",
    description: "Aesthetic. Retro-futurist. Pink and blue forever.",
    roomId: "e23c1dae-12f2-43ed-86d9-34b0893f2385",
    autoRespond: true,
    theme: "vaporwave",
  },
}

export function getDemoConfig(slug: string): DemoConfig | undefined {
  return DEMOS[slug]
}
