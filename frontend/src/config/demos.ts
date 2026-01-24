export interface DemoConfig {
  slug: string
  title: string
  description: string
  roomId: string
  autoRespond: boolean
}

export const DEMOS: Record<string, DemoConfig> = {
  "story-runtime": {
    slug: "story-runtime",
    title: "Story Runtime Demo",
    description:
      "Interactive branching narrative with AI agents that see your story context.",
    roomId: "00000000-0000-0000-0000-de0000000001",
    autoRespond: true,
  },
}

export function getDemoConfig(slug: string): DemoConfig | undefined {
  return DEMOS[slug]
}
