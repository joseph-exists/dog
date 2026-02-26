import type { BuilderValidationIssue } from "@/components/Demo/builder/demoBuilderSchema"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

interface DemoValidationPanelProps {
  issues: BuilderValidationIssue[]
}

export function DemoValidationPanel({ issues }: DemoValidationPanelProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Semantic Validation</CardTitle>
        <CardDescription>
          Builder-side preflight checks for story/runtime dependencies and
          composition constraints.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {issues.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No semantic issues detected.
          </p>
        ) : (
          issues.map((issue, index) => (
            <div
              key={`${issue.code}-${issue.path ?? "root"}-${index}`}
              className="rounded border px-3 py-2 text-sm"
            >
              <div
                className={
                  issue.severity === "error" ? "text-red-700" : "text-amber-700"
                }
              >
                [{issue.severity}] {issue.message}
              </div>
              {issue.path && (
                <div className="text-xs text-muted-foreground mt-1">
                  Path: {issue.path}
                </div>
              )}
            </div>
          ))
        )}
      </CardContent>
    </Card>
  )
}
