export type DemoResolvedVisibility = "visible" | "hidden_unmounted" | "hidden_mounted"
export type DemoShellVisibility = "visible" | "hidden_mounted"
export type DemoBlockRegion = "top" | "primary" | "auxiliary" | "footer"

export interface DemoBlockLike {
  id: string
  order?: number | null
  region?: unknown
  visibility?: unknown
}

export interface DemoRenderableBlock<TBlock extends DemoBlockLike> {
  block: TBlock
  region: DemoBlockRegion
  visibilityMode: DemoShellVisibility
}

export function normalizeBlockVisibility(
  visibility: unknown,
): DemoResolvedVisibility {
  const rawVisibility = typeof visibility === "string" ? visibility : "visible"
  if (rawVisibility === "hidden_unmounted") return "hidden_unmounted"
  if (rawVisibility === "hidden_mounted") return "hidden_mounted"
  return "visible"
}

export function resolveDemoBlockRegion(region: unknown): DemoBlockRegion {
  if (region === "primary") return "primary"
  if (region === "auxiliary") return "auxiliary"
  if (region === "footer") return "footer"
  return "top"
}

export function getRenderableDemoBlocks<TBlock extends DemoBlockLike>(
  blocks: TBlock[],
): DemoRenderableBlock<TBlock>[] {
  return blocks
    .map((block) => ({
      block,
      region: resolveDemoBlockRegion(block.region),
      resolvedVisibility: normalizeBlockVisibility(block.visibility),
    }))
    .filter(({ resolvedVisibility }) => resolvedVisibility !== "hidden_unmounted")
    .sort((a, b) => (a.block.order ?? 1) - (b.block.order ?? 1))
    .map(({ block, region, resolvedVisibility }) => ({
      block,
      region,
      visibilityMode: resolvedVisibility === "hidden_mounted" ? "hidden_mounted" : "visible",
    }))
}

