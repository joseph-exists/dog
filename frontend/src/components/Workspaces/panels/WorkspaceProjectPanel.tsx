import { useState } from "react"

import type { ProjectPublic } from "@/client"
import type { WorkspaceDetailViewModel } from "@/services/workspaceService"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

export interface WorkspaceProjectPanelProps {
  workspace: WorkspaceDetailViewModel
  projects: ProjectPublic[]
  isAssigning: boolean
  isDetaching: boolean
  canManageAssignment: boolean
  onAssign: (projectId: string) => Promise<unknown>
  onDetach: () => Promise<unknown>
}

export function WorkspaceProjectPanel({
  workspace,
  projects,
  isAssigning,
  isDetaching,
  canManageAssignment,
  onAssign,
  onDetach,
}: WorkspaceProjectPanelProps) {
  const [selectedProjectId, setSelectedProjectId] = useState(workspace.projectId ?? "")

  const assignDisabled =
    !selectedProjectId ||
    selectedProjectId === workspace.projectId ||
    !canManageAssignment ||
    isAssigning ||
    isDetaching
  const description = canManageAssignment
    ? "Attach this workspace to a project through the canonical project-resource relationship."
    : "This workspace's current project relationship is visible here. Assignment changes remain owner-scoped in the current policy pass."

  return (
    <Card>
      <CardHeader>
        <CardTitle>Project Assignment</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-lg border bg-muted/20 p-4 text-sm">
          <div className="font-medium">Current project</div>
          <div className="mt-1 text-muted-foreground">
            {workspace.projectSummary
              ? `${workspace.projectSummary.name} (${workspace.visibility})`
              : "This workspace is currently private and not attached to a project."}
          </div>
        </div>

        <div className="space-y-1.5">
          <Label>Assign to Project</Label>
          <Select
            value={selectedProjectId}
            onValueChange={setSelectedProjectId}
            disabled={!canManageAssignment}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select a project" />
            </SelectTrigger>
            <SelectContent>
              {projects.map((project) => (
                <SelectItem key={project.id} value={project.id}>
                  {project.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <p className="text-xs text-muted-foreground">
            Near-term rule: a workspace can belong to zero or one project.
          </p>
          {!canManageAssignment ? (
            <p className="text-xs text-muted-foreground">
              Project assignment remains owner-scoped in the current policy pass.
            </p>
          ) : null}
        </div>

        <div className="flex flex-col gap-2 sm:flex-row">
          <Button
            className="flex-1"
            disabled={assignDisabled}
            onClick={() => onAssign(selectedProjectId)}
          >
            {isAssigning ? "Assigning..." : "Assign to Project"}
          </Button>
          <Button
            variant="outline"
            className="flex-1"
            disabled={!workspace.projectId || !canManageAssignment || isAssigning || isDetaching}
            onClick={() => onDetach()}
          >
            {isDetaching ? "Removing..." : "Remove from Project"}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
