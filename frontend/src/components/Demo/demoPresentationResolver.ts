import type React from "react"
import type { ThemeViewModel } from "@/services/themeService"
import { themeTokensToStyle } from "@/services/themeService"

type TokenMap = Record<string, unknown>
type RecordValue = Record<string, unknown>

export type DemoPresentationScope = "composition" | "panel" | "block"

export interface ResolvedDemoPresentationFrame {
  style?: React.CSSProperties
  overlayCss?: string
  motionMs?: number
  easing?: string
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value)
}

function getNestedString(
  source: unknown,
  ...path: string[]
): string | undefined {
  let cursor: unknown = source
  for (const segment of path) {
    if (!isRecord(cursor)) return undefined
    cursor = cursor[segment]
  }
  return typeof cursor === "string" && cursor.trim().length > 0 ? cursor : undefined
}

function getNestedNumber(
  source: unknown,
  ...path: string[]
): number | undefined {
  let cursor: unknown = source
  for (const segment of path) {
    if (!isRecord(cursor)) return undefined
    cursor = cursor[segment]
  }
  return typeof cursor === "number" && Number.isFinite(cursor) && cursor > 0
    ? cursor
    : undefined
}

function getNestedBoolean(
  source: unknown,
  ...path: string[]
): boolean | undefined {
  let cursor: unknown = source
  for (const segment of path) {
    if (!isRecord(cursor)) return undefined
    cursor = cursor[segment]
  }
  return typeof cursor === "boolean" ? cursor : undefined
}

function toCustomPropTokenMap(value: unknown): TokenMap {
  if (!isRecord(value)) return {}
  const tokens: TokenMap = {}
  for (const [key, tokenValue] of Object.entries(value)) {
    if (!key.startsWith("--")) continue
    if (typeof tokenValue !== "string") continue
    tokens[key] = tokenValue
  }
  return tokens
}

export function extractPresentationTokens(
  presentationJson: unknown,
): TokenMap {
  if (!isRecord(presentationJson)) return {}
  const nestedTokens = toCustomPropTokenMap(presentationJson.tokens)
  const nestedThemeTokens = toCustomPropTokenMap(presentationJson.theme_tokens)
  const nestedCssVars = toCustomPropTokenMap(presentationJson.css_vars)
  const rootTokens = toCustomPropTokenMap(presentationJson)
  return {
    ...nestedTokens,
    ...nestedThemeTokens,
    ...nestedCssVars,
    ...rootTokens,
  }
}

export function buildDemoThemeIndex(
  ...themeGroups: ThemeViewModel[][]
): Map<string, ThemeViewModel> {
  const index = new Map<string, ThemeViewModel>()
  for (const group of themeGroups) {
    for (const theme of group) {
      if (!index.has(theme.id)) {
        index.set(theme.id, theme)
      }
    }
  }
  return index
}

export function resolveDemoPresentationStyle({
  themeId,
  presentationJson,
  themeIndex,
}: {
  themeId: string | null | undefined
  presentationJson: unknown
  themeIndex: Map<string, ThemeViewModel>
}): React.CSSProperties | undefined {
  const themedTokens =
    typeof themeId === "string" && themeId.trim().length > 0
      ? (themeIndex.get(themeId)?.tokens ?? {})
      : {}
  const presentationTokens = extractPresentationTokens(presentationJson)
  return themeTokensToStyle({
    ...themedTokens,
    ...presentationTokens,
  })
}

function resolveTypographyStyle(presentationJson: unknown): React.CSSProperties {
  const typographySize = getNestedString(presentationJson, "typography", "size")
  const lineHeight = getNestedString(presentationJson, "typography", "line_height")

  const style: React.CSSProperties = {}
  if (typographySize === "xs") style.fontSize = "0.75rem"
  if (typographySize === "sm") style.fontSize = "0.875rem"
  if (typographySize === "base") style.fontSize = "1rem"
  if (typographySize === "lg") style.fontSize = "1.125rem"

  if (lineHeight === "tight") style.lineHeight = "1.25"
  if (lineHeight === "normal") style.lineHeight = "1.5"
  if (lineHeight === "relaxed") style.lineHeight = "1.65"
  return style
}

function resolveEffectStyle(presentationJson: unknown): React.CSSProperties {
  const style: React.CSSProperties = {}
  const cardPatternCss = getNestedString(
    presentationJson,
    "backgrounds",
    "card_pattern",
    "css",
  )
  const pageGradientCss = getNestedString(presentationJson, "backgrounds", "page_gradient")
  const glowEnabled = getNestedBoolean(presentationJson, "effects", "card_glow", "enable")
  const glowCss = getNestedString(presentationJson, "effects", "card_glow", "css")

  if (pageGradientCss || cardPatternCss) {
    const layers: string[] = []
    if (pageGradientCss) layers.push(pageGradientCss)
    if (cardPatternCss) layers.push(cardPatternCss)
    style.backgroundImage = layers.join(", ")
  }
  if (glowCss) {
    style.boxShadow = glowCss
  } else if (glowEnabled) {
    style.boxShadow = "0 10px 28px rgba(15, 23, 42, 0.24)"
  }
  return style
}

function resolveOverlayCss(
  scope: DemoPresentationScope,
  presentationJson: unknown,
): string | undefined {
  if (scope === "panel") {
    return (
      getNestedString(presentationJson, "overlays", "panel_header", "css")
      ?? getNestedString(presentationJson, "overlays", "header", "css")
    )
  }
  if (scope === "block") {
    return (
      getNestedString(presentationJson, "overlays", "block_header", "css")
      ?? getNestedString(presentationJson, "overlays", "header", "css")
    )
  }
  return undefined
}

function resolveMotionMs(
  scope: DemoPresentationScope,
  presentationJson: unknown,
): number | undefined {
  if (scope === "panel") {
    return (
      getNestedNumber(presentationJson, "motion", "panel_enter_ms")
      ?? getNestedNumber(presentationJson, "motion", "enter_ms")
    )
  }
  if (scope === "block") {
    return (
      getNestedNumber(presentationJson, "motion", "block_enter_ms")
      ?? getNestedNumber(presentationJson, "motion", "block_stagger_ms")
      ?? getNestedNumber(presentationJson, "motion", "enter_ms")
    )
  }
  return getNestedNumber(presentationJson, "motion", "panel_enter_ms")
}

export function resolveDemoPresentationFrame({
  scope,
  themeId,
  presentationJson,
  themeIndex,
}: {
  scope: DemoPresentationScope
  themeId: string | null | undefined
  presentationJson: unknown
  themeIndex: Map<string, ThemeViewModel>
}): ResolvedDemoPresentationFrame {
  const tokenStyle = resolveDemoPresentationStyle({
    themeId,
    presentationJson,
    themeIndex,
  })
  const typographyStyle = resolveTypographyStyle(presentationJson)
  const effectStyle = resolveEffectStyle(presentationJson)
  const style: RecordValue = {
    ...(tokenStyle ?? {}),
    ...typographyStyle,
    ...effectStyle,
  }
  return {
    style: Object.keys(style).length > 0
      ? (style as unknown as React.CSSProperties)
      : undefined,
    overlayCss: resolveOverlayCss(scope, presentationJson),
    motionMs: resolveMotionMs(scope, presentationJson),
    easing: getNestedString(presentationJson, "motion", "easing"),
  }
}
