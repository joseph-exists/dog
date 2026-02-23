import { expect, test } from "@playwright/test"
import { getDemoBlockContainerClassName } from "@/components/Demo/DemoShell"
import {
  getRenderableDemoBlocks,
  normalizeBlockVisibility,
  resolveDemoBlockRegion,
} from "@/components/Demo/blockVisibility"

test.describe("Demo visibility semantics helpers", () => {
  test("normalizeBlockVisibility supports explicit v2 values only", async () => {
    expect(normalizeBlockVisibility("visible")).toBe("visible")
    expect(normalizeBlockVisibility("hidden_unmounted")).toBe("hidden_unmounted")
    expect(normalizeBlockVisibility("hidden_mounted")).toBe("hidden_mounted")
    expect(normalizeBlockVisibility("hidden")).toBe("visible")
    expect(normalizeBlockVisibility(null)).toBe("visible")
    expect(normalizeBlockVisibility(undefined)).toBe("visible")
  })

  test("resolveDemoBlockRegion falls back invalid values to top", async () => {
    expect(resolveDemoBlockRegion("top")).toBe("top")
    expect(resolveDemoBlockRegion("primary")).toBe("primary")
    expect(resolveDemoBlockRegion("auxiliary")).toBe("auxiliary")
    expect(resolveDemoBlockRegion("footer")).toBe("footer")
    expect(resolveDemoBlockRegion("sidebar")).toBe("top")
    expect(resolveDemoBlockRegion(null)).toBe("top")
  })

  test("getRenderableDemoBlocks filters hidden_unmounted and preserves hidden_mounted", async () => {
    const blocks = [
      { id: "a", visibility: "visible", order: 3 },
      { id: "b", visibility: "hidden_unmounted", order: 1 },
      { id: "c", visibility: "hidden_mounted", order: 2 },
    ]

    const result = getRenderableDemoBlocks(blocks)
    expect(result.map((item) => item.block.id)).toEqual(["c", "a"])
    expect(result.map((item) => item.visibilityMode)).toEqual([
      "hidden_mounted",
      "visible",
    ])
  })

  test("getRenderableDemoBlocks applies default order and region mapping", async () => {
    const blocks = [
      { id: "a", region: "primary" },
      { id: "b", region: "footer", order: 5 },
      { id: "c", region: "unknown-region", order: 2 },
      { id: "d", region: "auxiliary", order: 1 },
    ]

    const result = getRenderableDemoBlocks(blocks)
    expect(result.map((item) => item.block.id)).toEqual(["a", "d", "c", "b"])
    expect(result.map((item) => item.region)).toEqual([
      "primary",
      "auxiliary",
      "top",
      "footer",
    ])
  })
})

test.describe("DemoShell visibility class behavior", () => {
  test("hidden_mounted adds hidden class", async () => {
    const className = getDemoBlockContainerClassName("hidden_mounted")
    expect(className).toContain("rounded-md")
    expect(className).toContain("hidden")
  })

  test("visible mode keeps container visible", async () => {
    const className = getDemoBlockContainerClassName("visible")
    expect(className).toContain("rounded-md")
    expect(className).not.toContain(" hidden ")
    expect(className.endsWith("hidden")).toBeFalsy()
  })
})

