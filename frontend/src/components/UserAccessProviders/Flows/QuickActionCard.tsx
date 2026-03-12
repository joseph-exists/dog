import { ArrowRight } from "lucide-react"
import type { ReactNode } from "react"
import { Button } from "@/components/ui/button"

interface QuickActionCardProps {
  title: string
  description: string
  icon: ReactNode
  onClick?: () => void
  href?: string
}

export function QuickActionCard({
  title,
  description,
  icon,
  onClick,
  href,
}: QuickActionCardProps) {
  const content = (
    <div className="flex h-full flex-col rounded-xl border bg-background/80 p-4 text-left transition-all hover:-translate-y-0.5 hover:shadow-sm">
      <div className="mb-3 inline-flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary">
        {icon}
      </div>
      <h4 className="text-sm font-semibold">{title}</h4>
      <p className="mt-1 flex-1 text-sm text-muted-foreground">{description}</p>
      <span className="mt-4 inline-flex items-center gap-1 text-xs font-medium text-primary">
        Continue
        <ArrowRight className="h-3.5 w-3.5" />
      </span>
    </div>
  )

  if (href) {
    return (
      <Button asChild variant="ghost" className="h-auto p-0">
        <a href={href}>{content}</a>
      </Button>
    )
  }

  return (
    <Button variant="ghost" className="h-auto p-0" onClick={onClick}>
      {content}
    </Button>
  )
}
