import { BlockContainer } from "@/components/Page/primitives"
import { useTerminalSession } from "@/hooks/useTerminalSession"
import { TerminalStatusBar } from "./TerminalStatusBar"
import { TerminalViewer } from "./TerminalViewer"

export interface TerminalBlockProps {
  title?: string
  subtitle?: string
  terminalUrl?: string | null
  mode?: "live" | "transcript"
  className?: string
}

export function TerminalBlock({
  title = "Terminal Block",
  subtitle = "Embeddable terminal surface for shared page and block use.",
  terminalUrl,
  mode = "transcript",
  className,
}: TerminalBlockProps) {
  const { session, status } = useTerminalSession({
    url: terminalUrl ?? null,
    enabled: Boolean(terminalUrl) && mode === "live",
  })

  return (
    <BlockContainer
      title={title}
      subtitle={subtitle}
      className={className}
      bodyClassName="min-h-[22rem] p-0"
      footer={<TerminalStatusBar session={session} status={status} />}
    >
      <TerminalViewer session={session} status={status} mode={mode} className="h-full" />
    </BlockContainer>
  )
}
