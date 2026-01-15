/**
 * PublishModal - Dialog for publishing a story to the catalog
 *
 * Features:
 * - Shows validation results (errors block publish, warnings allow proceed)
 * - Confirmation checkbox for acknowledging publish action
 * - Loading state during validation
 * - Loading state during publish
 * - Displays version being published
 */

import { Loader2 } from "lucide-react"
import { useMemo, useState } from "react"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { usePublishWorkflow } from "@/hooks/stories/usePublishWorkflow"
import ValidationSummary from "./ValidationSummary"

interface PublishModalProps {
  storyId: string
  isOpen: boolean
  onClose: () => void
}

const PublishModal = ({ storyId, isOpen, onClose }: PublishModalProps) => {
  const [confirmChecked, setConfirmChecked] = useState(false)
  const [warningsAcknowledged, setWarningsAcknowledged] = useState(false)
  const {
    story,
    nodes,
    choices,
    validation,
    isReady,
    isLoading,
    publishAsync,
    isPublishing,
  } = usePublishWorkflow({ storyId })

  // Calculate stats from nodes and choices
  const stats = useMemo(() => {
    // Calculate orphaned nodes count from validation warnings
    const orphanWarning = validation.warnings.find((w) =>
      w.includes("orphan node"),
    )
    const orphanedMatch = orphanWarning?.match(/(\d+) orphan/)
    const orphanedCount = orphanedMatch ? parseInt(orphanedMatch[1], 10) : 0

    return {
      nodeCount: nodes.length,
      choiceCount: choices.length,
      orphanedCount,
    }
  }, [nodes.length, choices.length, validation.warnings])

  // Determine if warnings need acknowledgment
  const hasWarnings = validation.warnings.length > 0
  const canPublish =
    isReady && confirmChecked && (!hasWarnings || warningsAcknowledged)

  const handlePublish = async () => {
    try {
      await publishAsync()
      // Only close on success
      onClose()
      setConfirmChecked(false)
      setWarningsAcknowledged(false)
    } catch {
      // Error is handled by the mutation's onError callback
      // Dialog stays open so user can see there was an issue
    }
  }

  const handleClose = () => {
    onClose()
    setConfirmChecked(false)
    setWarningsAcknowledged(false)
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && handleClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>
            Publish Story{story ? ` v${story.current_version}` : ""}?
          </DialogTitle>
          <DialogDescription>
            Publishing will make your story available in the catalog for all
            users to discover and play.
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-4">
          {isLoading ? (
            <div className="flex flex-col items-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <p className="mt-2 text-sm text-muted-foreground">
                Validating story...
              </p>
            </div>
          ) : (
            <>
              <Separator />

              <div>
                <h4 className="font-medium mb-3">Validation Results</h4>
                <ValidationSummary
                  validation={validation}
                  nodeCount={stats.nodeCount}
                  choiceCount={stats.choiceCount}
                  orphanedCount={stats.orphanedCount}
                />
              </div>

              {hasWarnings && (
                <>
                  <div className="p-3 bg-amber-50 dark:bg-amber-950/30 rounded-md">
                    <p className="text-sm text-amber-800 dark:text-amber-300">
                      <strong>Note:</strong> You can publish despite warnings,
                      but we recommend addressing them for the best player
                      experience.
                    </p>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="acknowledge-warnings"
                      checked={warningsAcknowledged}
                      onCheckedChange={(checked) =>
                        setWarningsAcknowledged(checked === true)
                      }
                    />
                    <Label
                      htmlFor="acknowledge-warnings"
                      className="text-sm font-normal cursor-pointer text-amber-700 dark:text-amber-400"
                    >
                      I acknowledge the warnings and want to proceed
                    </Label>
                  </div>
                </>
              )}

              <Separator />

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="confirm-publish"
                  checked={confirmChecked}
                  onCheckedChange={(checked) =>
                    setConfirmChecked(checked === true)
                  }
                  disabled={!isReady}
                />
                <Label
                  htmlFor="confirm-publish"
                  className="text-sm font-normal cursor-pointer"
                >
                  I understand this will make the story available in the catalog
                </Label>
              </div>
            </>
          )}
        </div>

        <DialogFooter className="gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={handleClose}
            disabled={isPublishing}
          >
            Cancel
          </Button>
          <Button onClick={handlePublish} disabled={!canPublish || isLoading}>
            {isPublishing && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Publish v{story?.current_version || "?"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default PublishModal
