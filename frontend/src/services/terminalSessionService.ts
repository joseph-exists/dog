import type { Content } from "@/components/Common/ContentRenderer"

export type TerminalConnectionStatus =
  | "idle"
  | "connecting"
  | "open"
  | "closed"
  | "error"

export type TerminalFrameKind = "input" | "output" | "system"

export interface TerminalFrame {
  id: string
  kind: TerminalFrameKind
  text: string
  ansiText: string
  timestamp: Date
}

export interface TerminalViewport {
  cols: number | null
  rows: number | null
}

export interface TerminalSessionState {
  id: string
  url: string | null
  status: TerminalConnectionStatus
  connectedAt: Date | null
  lastFrameAt: Date | null
  frames: TerminalFrame[]
  plainText: string
  ansiChunks: string[]
  viewport: TerminalViewport
}

export interface AppendTerminalFrameOptions {
  maxFrames?: number
  maxChars?: number
}

const DEFAULT_MAX_FRAMES = 400
const DEFAULT_MAX_CHARS = 48_000

const ANSI_PATTERN =
  // Remove ANSI escape codes so transcript rendering stays readable.
  // This keeps the raw chunks separately for future richer terminal rendering.
  /\u001b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])/g

export function createTerminalSession(url: string | null): TerminalSessionState {
  return {
    id: `terminal-${crypto.randomUUID()}`,
    url,
    status: url ? "connecting" : "idle",
    connectedAt: null,
    lastFrameAt: null,
    frames: [],
    plainText: "",
    ansiChunks: [],
    viewport: {
      cols: null,
      rows: null,
    },
  }
}

export function stripAnsi(text: string): string {
  return text.replace(ANSI_PATTERN, "")
}

export async function decodeTerminalEventData(data: unknown): Promise<string> {
  if (typeof data === "string") {
    return data
  }

  if (data instanceof ArrayBuffer) {
    return new TextDecoder().decode(data)
  }

  if (ArrayBuffer.isView(data)) {
    return new TextDecoder().decode(data)
  }

  if (data instanceof Blob) {
    return data.text()
  }

  return String(data ?? "")
}

export function createTerminalFrame(
  kind: TerminalFrameKind,
  ansiText: string,
): TerminalFrame {
  return {
    id: crypto.randomUUID(),
    kind,
    ansiText,
    text: stripAnsi(ansiText),
    timestamp: new Date(),
  }
}

export function appendTerminalFrame(
  session: TerminalSessionState,
  frame: TerminalFrame,
  options: AppendTerminalFrameOptions = {},
): TerminalSessionState {
  const maxFrames = options.maxFrames ?? DEFAULT_MAX_FRAMES
  const maxChars = options.maxChars ?? DEFAULT_MAX_CHARS

  const nextFrames = [...session.frames, frame].slice(-maxFrames)
  const nextAnsiChunks = [...session.ansiChunks, frame.ansiText].slice(-maxFrames)

  const nextPlainText = trimToMaxChars(
    nextFrames.map((item) => item.text).join(""),
    maxChars,
  )

  return {
    ...session,
    lastFrameAt: frame.timestamp,
    frames: nextFrames,
    ansiChunks: nextAnsiChunks,
    plainText: nextPlainText,
  }
}

export function setTerminalConnectionStatus(
  session: TerminalSessionState,
  status: TerminalConnectionStatus,
): TerminalSessionState {
  return {
    ...session,
    status,
    connectedAt:
      status === "open" && session.connectedAt === null
        ? new Date()
        : session.connectedAt,
  }
}

export function clearTerminalSession(
  session: TerminalSessionState,
): TerminalSessionState {
  return {
    ...session,
    frames: [],
    plainText: "",
    ansiChunks: [],
    lastFrameAt: null,
  }
}

export function updateTerminalViewport(
  session: TerminalSessionState,
  viewport: Partial<TerminalViewport>,
): TerminalSessionState {
  return {
    ...session,
    viewport: {
      ...session.viewport,
      ...viewport,
    },
  }
}

export function toTerminalTranscriptContent(
  session: TerminalSessionState,
): Content<"code"> {
  return {
    format: "code",
    value:
      session.plainText.trim().length > 0
        ? session.plainText
        : "# Terminal transcript will appear here once output arrives.\n",
    metadata: {
      variant: "card",
      label: "Terminal Transcript",
      options: {
        language: "bash",
        copyable: true,
      },
    },
  }
}

function trimToMaxChars(value: string, maxChars: number): string {
  if (value.length <= maxChars) return value
  return value.slice(value.length - maxChars)
}
