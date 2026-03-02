import { expect, test } from "@playwright/test"
import {
  canPrimaryPanelCollapseToWidth,
  DEMO_LAYOUT_COLLAPSED_PRIMARY_SIZE,
  getPrimaryPanelCollapsedSize,
} from "@/components/Demo/DemoLayout"

test.describe("DemoLayout collapse semantics", () => {
  test("primary collapsed panels use minimized width", async () => {
    expect(
      getPrimaryPanelCollapsedSize({
        prominence: "primary",
        collapsed: true,
      }),
    ).toBe(DEMO_LAYOUT_COLLAPSED_PRIMARY_SIZE)
  })

  test("expanded or auxiliary panels keep normal sizing behavior", async () => {
    expect(
      getPrimaryPanelCollapsedSize({
        prominence: "primary",
        collapsed: false,
      }),
    ).toBeUndefined()
    expect(
      getPrimaryPanelCollapsedSize({
        prominence: "auxiliary",
        collapsed: true,
      }),
    ).toBeUndefined()
  })

  test("width collapse requires another expanded primary sibling", async () => {
    expect(
      canPrimaryPanelCollapseToWidth(
        [{ id: "runtime", prominence: "primary", collapsed: true }],
        "runtime",
      ),
    ).toBeFalsy()

    expect(
      canPrimaryPanelCollapseToWidth(
        [
          { id: "runtime", prominence: "primary", collapsed: true },
          { id: "chat", prominence: "primary", collapsed: false },
        ],
        "runtime",
      ),
    ).toBeTruthy()

    expect(
      canPrimaryPanelCollapseToWidth(
        [
          { id: "runtime", prominence: "primary", collapsed: true },
          { id: "chat", prominence: "primary", collapsed: true },
        ],
        "runtime",
      ),
    ).toBeFalsy()
  })
})
