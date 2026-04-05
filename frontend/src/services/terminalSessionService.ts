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
  truncation: {
    droppedFrames: number
    droppedChars: number
  }
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

export function createTerminalSession(
  url: string | null,
): TerminalSessionState {
  return {
    id: `terminal-${crypto.randomUUID()}`,
    url,
    status: url ? "connecting" : "idle",
    connectedAt: null,
    lastFrameAt: null,
    frames: [],
    plainText: "",
    ansiChunks: [],
    truncation: {
      droppedFrames: 0,
      droppedChars: 0,
    },
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

  const allFrames = [...session.frames, frame]
  const allAnsiChunks = [...session.ansiChunks, frame.ansiText]
  const droppedFrames = Math.max(0, allFrames.length - maxFrames)
  const nextFrames = allFrames.slice(-maxFrames)
  const nextAnsiChunks = allAnsiChunks.slice(
    -maxFrames,
  )

  const { value: nextPlainText, droppedChars } = trimToMaxChars(
    nextFrames.map((item) => item.text).join(""),
    maxChars,
  )

  return {
    ...session,
    lastFrameAt: frame.timestamp,
    frames: nextFrames,
    ansiChunks: nextAnsiChunks,
    plainText: nextPlainText,
    truncation: {
      droppedFrames: session.truncation.droppedFrames + droppedFrames,
      droppedChars: session.truncation.droppedChars + droppedChars,
    },
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
    truncation: {
      droppedFrames: 0,
      droppedChars: 0,
    },
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
  const transcriptValue = buildTranscriptDocument(session)

  return {
    format: "code",
    value: transcriptValue,
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

function buildTranscriptDocument(session: TerminalSessionState): string {
  if (session.frames.length === 0) {
    return "# Terminal transcript will appear here once output arrives.\n"
  }

  const lines: string[] = []

  if (
    session.truncation.droppedFrames > 0 ||
    session.truncation.droppedChars > 0
  ) {
    lines.push(
      `# Transcript truncated: dropped ${session.truncation.droppedFrames} older frame(s), ${session.truncation.droppedChars} older character(s).`,
      "",
    )
  }

  for (const frame of session.frames) {
    const timestamp = frame.timestamp.toLocaleTimeString()
    const kind = frame.kind.toUpperCase()
    lines.push(`[${timestamp}] ${kind}`)
    lines.push(frame.text || "(empty frame)")
    lines.push("")
  }

  return `${lines.join("\n").trimEnd()}\n`
}

function trimToMaxChars(
  value: string,
  maxChars: number,
): { value: string; droppedChars: number } {
  if (value.length <= maxChars) {
    return { value, droppedChars: 0 }
  }

  const droppedChars = value.length - maxChars
  return {
    value: value.slice(value.length - maxChars),
    droppedChars,
  }
}
