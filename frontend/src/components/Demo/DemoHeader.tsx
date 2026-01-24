import { Badge } from "@/components/ui/badge"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"

interface DemoHeaderProps {
  title: string
  description: string
  autoRespond: boolean
  onAutoRespondChange: (value: boolean) => void
  isConnected: boolean
}

export function DemoHeader({
  title,
  description,
  autoRespond,
  onAutoRespondChange,
  isConnected,
}: DemoHeaderProps) {
  return (
    <div className="flex items-center justify-between px-4 py-3 border-b bg-background">
      <div className="flex flex-col gap-0.5">
        <h1 className="text-lg font-semibold">{title}</h1>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      <div className="flex items-center gap-4">
        <Badge
          variant={isConnected ? "default" : "secondary"}
          className="text-xs"
        >
          {isConnected ? "Connected" : "Disconnected"}
        </Badge>
        <div className="flex items-center gap-2">
          <Switch
            id="auto-respond"
            checked={autoRespond}
            onCheckedChange={onAutoRespondChange}
          />
          <Label htmlFor="auto-respond" className="text-sm cursor-pointer">
            Auto-respond
          </Label>
        </div>
      </div>
    </div>
  )
}
