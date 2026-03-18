import { useState } from "react"

import type { WorkspaceFlavour } from "@/client"
import type { CreateWorkspaceFormInput } from "@/hooks/useWorkspaces"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"

export interface WorkspaceCreatePanelProps {
  isSubmitting: boolean
  onCreate: (input: CreateWorkspaceFormInput) => Promise<void>
}

const FLAVOURS: WorkspaceFlavour[] = ["base", "dev", "python", "node", "jupyter"]

export function WorkspaceCreatePanel({
  isSubmitting,
  onCreate,
}: WorkspaceCreatePanelProps) {
  const [name, setName] = useState("")
  const [flavour, setFlavour] = useState<WorkspaceFlavour>("dev")
  const [kind, setKind] = useState("ephemeral")
  const [repoUrl, setRepoUrl] = useState("")
  const [sshPubkey, setSshPubkey] = useState("")
  const [envVarsText, setEnvVarsText] = useState("")

  const submit = async () => {
    if (!name.trim()) return
    await onCreate({
      name,
      flavour,
      kind,
      repoUrl,
      sshPubkey,
      envVarsText,
    })
    setName("")
    setRepoUrl("")
    setSshPubkey("")
    setEnvVarsText("")
    setFlavour("dev")
    setKind("ephemeral")
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Provision a Workspace</CardTitle>
        <CardDescription>
          Create a new kennel-backed environment for local validation and frontend wiring.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="workspace-name">Name</Label>
          <Input
            id="workspace-name"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Kennel Validation Box"
          />
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div className="space-y-1.5">
            <Label>Flavour</Label>
            <Select value={flavour} onValueChange={(value) => setFlavour(value as WorkspaceFlavour)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {FLAVOURS.map((item) => (
                  <SelectItem key={item} value={item}>
                    {item}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label>Kind</Label>
            <Select value={kind} onValueChange={setKind}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ephemeral">ephemeral</SelectItem>
                <SelectItem value="persistent">persistent</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="workspace-repo">Repository URL</Label>
          <Input
            id="workspace-repo"
            value={repoUrl}
            onChange={(event) => setRepoUrl(event.target.value)}
            placeholder="https://github.com/example/repo.git"
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="workspace-ssh-key">SSH Public Key</Label>
          <Textarea
            id="workspace-ssh-key"
            value={sshPubkey}
            onChange={(event) => setSshPubkey(event.target.value)}
            placeholder="ssh-ed25519 AAAA..."
            rows={4}
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="workspace-env-vars">Environment Variables</Label>
          <Textarea
            id="workspace-env-vars"
            value={envVarsText}
            onChange={(event) => setEnvVarsText(event.target.value)}
            placeholder={"API_BASE_URL=http://localhost:8000\nFEATURE_FLAG=true"}
            rows={4}
          />
          <p className="text-xs text-muted-foreground">
            Use one `KEY=value` pair per line.
          </p>
        </div>

        <Button onClick={submit} disabled={isSubmitting || !name.trim()} className="w-full">
          {isSubmitting ? "Provisioning..." : "Create Workspace"}
        </Button>
      </CardContent>
    </Card>
  )
}
