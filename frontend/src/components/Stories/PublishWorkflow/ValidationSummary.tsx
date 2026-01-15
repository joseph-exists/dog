/**
 * ValidationSummary - Displays story validation results
 *
 * Features:
 * - Passed checks (green checkmarks)
 * - Error items (red, blocks publish)
 * - Warning items (yellow/amber)
 * - Overall status banner
 * - Stats: node count, choice count, orphaned count
 */

import {
  AlertOctagon,
  AlertTriangle,
  CheckCircle,
  FileText,
  GitBranch,
  XCircle,
} from "lucide-react"
import type { ValidationResult } from "@/hooks/stories/storyValidation"

interface ValidationSummaryProps {
  validation: ValidationResult
  nodeCount?: number
  choiceCount?: number
  orphanedCount?: number
}

const ValidationSummary = ({
  validation,
  nodeCount,
  choiceCount,
  orphanedCount,
}: ValidationSummaryProps) => {
  const passedChecks = [
    validation.errors.length === 0 && "Story structure is valid",
    validation.warnings.length === 0 && "No warnings detected",
  ].filter(Boolean) as string[]

  const hasStats = nodeCount !== undefined || choiceCount !== undefined

  return (
    <div className="flex flex-col gap-3">
      {/* Stats */}
      {hasStats && (
        <div className="flex flex-wrap gap-4 py-2 px-3 bg-muted/50 rounded-md text-sm">
          {nodeCount !== undefined && (
            <div className="flex items-center gap-1.5 text-muted-foreground">
              <FileText className="h-4 w-4" />
              <span>{nodeCount} nodes</span>
            </div>
          )}
          {choiceCount !== undefined && (
            <div className="flex items-center gap-1.5 text-muted-foreground">
              <GitBranch className="h-4 w-4" />
              <span>{choiceCount} choices</span>
            </div>
          )}
          {orphanedCount !== undefined && orphanedCount > 0 && (
            <div className="flex items-center gap-1.5 text-amber-600">
              <AlertOctagon className="h-4 w-4" />
              <span>{orphanedCount} orphaned</span>
            </div>
          )}
        </div>
      )}

      {/* Passed Checks */}
      {passedChecks.map((check) => (
        <div key={check} className="flex items-center gap-2 text-green-600">
          <CheckCircle className="h-5 w-5 shrink-0" />
          <span className="text-sm">{check}</span>
        </div>
      ))}

      {/* Errors */}
      {validation.errors.map((error) => (
        <div key={error} className="flex items-center gap-2 text-destructive">
          <XCircle className="h-5 w-5 shrink-0" />
          <span className="text-sm">{error}</span>
        </div>
      ))}

      {/* Warnings */}
      {validation.warnings.map((warning) => (
        <div key={warning} className="flex items-center gap-2 text-amber-600">
          <AlertTriangle className="h-5 w-5 shrink-0" />
          <span className="text-sm">{warning}</span>
        </div>
      ))}

      {/* Overall Status */}
      {validation.isValid ? (
        <div className="flex items-center gap-2 mt-2 p-3 bg-green-50 dark:bg-green-950/30 rounded-md text-green-700 dark:text-green-400">
          <CheckCircle className="h-6 w-6 shrink-0" />
          <span className="font-semibold">Story is ready to publish!</span>
        </div>
      ) : (
        <div className="flex items-center gap-2 mt-2 p-3 bg-destructive/10 rounded-md text-destructive">
          <XCircle className="h-6 w-6 shrink-0" />
          <span className="font-semibold">
            Please fix {validation.errors.length} error(s) before publishing
          </span>
        </div>
      )}
    </div>
  )
}

export default ValidationSummary
