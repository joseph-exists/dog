/**
 * StoryStateCollapsible
 *
 * Collapsible story state inspector with JSON rendering.
 */

import { ChevronDown, ChevronUp } from "lucide-react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"

interface StoryStateCollapsibleProps {
  storyState: Record<string, unknown> | null
}

export function StoryStateCollapsible({
  storyState,
}: StoryStateCollapsibleProps) {
  const [open, setOpen] = useState(false)

  return (
    <Collapsible open={open} onOpenChange={setOpen} className="space-y-2">
      <CollapsibleTrigger asChild>
        <Button variant="ghost" className="w-full justify-between px-0">
          <span className="text-sm font-medium">Story State</span>
          {open ? (
            <ChevronUp className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
        </Button>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="demo-state rounded-md border bg-muted/30 p-3 text-xs font-mono whitespace-pre-wrap">
          {storyState ? (
            JSON.stringify(storyState, null, 2)
          ) : (
            <span className="text-muted-foreground">
              No story state available.
            </span>
          )}
        </div>
      </CollapsibleContent>
    </Collapsible>
  )
}
