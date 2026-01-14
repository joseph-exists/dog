/**
 * StateSchemaSheet - Sheet (drawer) wrapper for StateSchemaEditor
 *
 * Features:
 * - Side drawer with state schema editor
 * - Read-only mode toggle based on publication status
 * - Version info display
 */

import { Variable, Lock } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"
import { Badge } from "@/components/ui/badge"
import StateSchemaEditor from "./StateSchemaEditor"

interface StateSchemaSheetProps {
  storyId: string
  version: number
  isPublished?: boolean
  publishedVersion?: number | null
  trigger?: React.ReactNode
}

const StateSchemaSheet = ({
  storyId,
  version,
  isPublished = false,
  publishedVersion,
  trigger,
}: StateSchemaSheetProps) => {
  // Read-only if the story is published AND we're viewing the published version
  const isReadOnly = isPublished && publishedVersion === version

  return (
    <Sheet>
      <SheetTrigger asChild>
        {trigger || (
          <Button size="sm" variant="outline">
            <Variable className="h-4 w-4 mr-2" />
            State Schema
          </Button>
        )}
      </SheetTrigger>
      <SheetContent side="right" className="w-full sm:w-[540px] sm:max-w-full overflow-y-auto">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <Variable className="h-5 w-5" />
            State Schema
            <Badge variant="outline" className="ml-2">
              v{version}
            </Badge>
            {isReadOnly && (
              <Badge variant="secondary" className="gap-1">
                <Lock className="h-3 w-3" />
                Read Only
              </Badge>
            )}
          </SheetTitle>
          <SheetDescription>
            {isReadOnly ? (
              <>
                This version is published. Create a new version to modify the state schema.
              </>
            ) : (
              <>
                Define variables that track player state throughout the story.
                Use these in choice conditions and state mutations.
              </>
            )}
          </SheetDescription>
        </SheetHeader>

        <div className="mt-6">
          <StateSchemaEditor
            storyId={storyId}
            version={version}
            readOnly={isReadOnly}
          />
        </div>

        {/* Help text */}
        <div className="mt-8 p-4 bg-muted/50 rounded-lg text-sm">
          <h4 className="font-medium mb-2">Using State Variables</h4>
          <ul className="space-y-1 text-muted-foreground">
            <li>
              <strong>In Choices:</strong> Use "Requires State" to show/hide choices based on conditions
            </li>
            <li>
              <strong>State Mutations:</strong> Use "Sets State" to modify variables when a choice is selected
            </li>
            <li>
              <strong>Categories:</strong> Group related variables for better organization
            </li>
          </ul>
        </div>
      </SheetContent>
    </Sheet>
  )
}

export default StateSchemaSheet
