import { expect, test } from "@playwright/test"
import {
  buildDemoThemeIndex,
  extractPresentationTokens,
  resolveDemoPresentationFrame,
  resolveDemoPresentationStyle,
} from "@/components/Demo/demoPresentationResolver"

test.describe("demoPresentationResolver", () => {
  test("extracts token-like keys from nested and root presentation json", async () => {
    const tokens = extractPresentationTokens({
      "--root-a": "1",
      tokens: {
        "--nested-a": "2",
        ignored: "x",
      },
      theme_tokens: {
        "--theme-a": "3",
      },
      css_vars: {
        "--css-a": "4",
      },
    })

    expect(tokens).toEqual({
      "--nested-a": "2",
      "--theme-a": "3",
      "--css-a": "4",
      "--root-a": "1",
    })
  })

  test("resolves style with presentation tokens overriding theme tokens", async () => {
    const themeIndex = buildDemoThemeIndex([
      {
        id: "theme-1",
        name: "Theme 1",
        description: null,
        category: "card",
        scope: "system",
        ownerId: null,
        isSystem: true,
        tokens: {
          "--card": "oklch(0.1 0.02 20)",
          "--border": "oklch(0.2 0.02 20)",
        },
        createdAt: new Date(),
        updatedAt: new Date(),
      },
    ])

    const style = resolveDemoPresentationStyle({
      themeId: "theme-1",
      presentationJson: {
        tokens: {
          "--border": "oklch(0.8 0.02 20)",
        },
      },
      themeIndex,
    })

    expect(style).toEqual({
      "--card": "oklch(0.1 0.02 20)",
      "--border": "oklch(0.8 0.02 20)",
    })
  })

  test("resolves non-token effects for panel presentation", async () => {
    const themeIndex = buildDemoThemeIndex([])
    const frame = resolveDemoPresentationFrame({
      scope: "panel",
      themeId: null,
      presentationJson: {
        overlays: {
          panel_header: {
            css: "linear-gradient(90deg, red, blue)",
          },
        },
        motion: {
          panel_enter_ms: 320,
          easing: "ease-in-out",
        },
        backgrounds: {
          card_pattern: {
            css: "repeating-linear-gradient(45deg, rgba(255,255,255,0.05) 0 8px, transparent 8px 16px)",
          },
        },
      },
      themeIndex,
    })

    expect(frame.overlayCss).toBe("linear-gradient(90deg, red, blue)")
    expect(frame.motionMs).toBe(320)
    expect(frame.easing).toBe("ease-in-out")
    expect(frame.style).toEqual(
      expect.objectContaining({
        backgroundImage: "repeating-linear-gradient(45deg, rgba(255,255,255,0.05) 0 8px, transparent 8px 16px)",
      }),
    )
  })
})
