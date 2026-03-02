import type { UserPageBuilderIssue } from "./userPageBuilderSchema"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

interface UserPageBuilderValidationPanelProps {
  issues: UserPageBuilderIssue[]
}

export function UserPageBuilderValidationPanel({
  issues,
}: UserPageBuilderValidationPanelProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Builder Validation</CardTitle>
        <CardDescription>
          Cross-surface checks for persona, work, audience, and relation
          references.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {issues.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No builder issues detected.
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
                <div className="mt-1 text-xs text-muted-foreground">
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
