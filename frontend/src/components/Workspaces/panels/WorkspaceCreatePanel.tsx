import { useState } from "react"
import { ChevronDown } from "lucide-react"

import type { WorkspaceFlavour } from "@/client"
import { Button } from "@/components/ui/button"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
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
import type { CreateWorkspaceFormInput } from "@/hooks/useWorkspaces"
import type {
  BootstrapInstallMode,
  BootstrapRepoSourceType,
  BootstrapStartupMode,
} from "@/services/workspaceService"

export interface WorkspaceCreatePanelProps {
  isSubmitting: boolean
  onCreate: (input: CreateWorkspaceFormInput) => Promise<void>
}

const FLAVOURS: WorkspaceFlavour[] = ["base", "dev", "cuda"]
const RUNTIME_PRESETS = [
  { value: "none", label: "None" },
  { value: "codex", label: "codex" },
  { value: "claude_code", label: "claude_code" },
  { value: "hermes-agent", label: "hermes-agent" },
] as const
const INSTALL_PROFILES = ["npm", "pnpm", "yarn", "uv", "pip"] as const
const STARTUP_PROFILES = ["vite", "nextjs", "fastapi"] as const
const AGENT_PROFILES = ["codex", "claude_code", "hermes"] as const
const AGENT_PROFILE_RUNTIME_PRESET: Record<
  (typeof AGENT_PROFILES)[number],
  string
> = {
  codex: "codex",
  claude_code: "claude_code",
  hermes: "hermes-agent",
}

type RuntimeFileDraft = {
  id: string
  path: string
  content: string
}

function createRuntimeFileDraft(): RuntimeFileDraft {
  return {
    id: `runtime-file-${Math.random().toString(36).slice(2, 10)}`,
    path: "",
    content: "",
  }
}

export function WorkspaceCreatePanel({
  isSubmitting,
  onCreate,
}: WorkspaceCreatePanelProps) {
  const [name, setName] = useState("")
  const [flavour, setFlavour] = useState<WorkspaceFlavour>("dev")
  const [runtimePreset, setRuntimePreset] = useState("none")
  const [kind, setKind] = useState("ephemeral")
  const [repoSourceType, setRepoSourceType] =
    useState<BootstrapRepoSourceType>("none")
  const [repoUrl, setRepoUrl] = useState("")
  const [userRepoId, setUserRepoId] = useState("")
  const [repoRef, setRepoRef] = useState("")
  const [workspacePath, setWorkspacePath] = useState("")
  const [installMode, setInstallMode] = useState<BootstrapInstallMode>("none")
  const [installProfile, setInstallProfile] =
    useState<(typeof INSTALL_PROFILES)[number]>("npm")
  const [startupMode, setStartupMode] =
    useState<BootstrapStartupMode>("terminal_only")
  const [startupProfile, setStartupProfile] =
    useState<(typeof STARTUP_PROFILES)[number]>("vite")
  const [agentProfile, setAgentProfile] =
    useState<(typeof AGENT_PROFILES)[number]>("codex")
  const [sshPubkey, setSshPubkey] = useState("")
  const [envVarsText, setEnvVarsText] = useState("")
  const [bootstrapProfile, setBootstrapProfile] = useState("")
  const [runtimeFiles, setRuntimeFiles] = useState<RuntimeFileDraft[]>([])

  const setAgentProfileWithPreset = (
    value: (typeof AGENT_PROFILES)[number],
  ) => {
    setAgentProfile(value)
    if (runtimePreset === "none") {
      setRuntimePreset(AGENT_PROFILE_RUNTIME_PRESET[value] ?? "none")
    }
  }

  const submit = async () => {
    if (!name.trim()) return
    await onCreate({
      name,
      flavour,
      runtimePreset: runtimePreset === "none" ? undefined : runtimePreset,
      kind,
      repoSourceType,
      repoUrl,
      userRepoId,
      repoRef,
      workspacePath,
      installMode,
      installProfile: installMode === "profile" ? installProfile : undefined,
      startupMode,
      startupProfile: startupMode === "profile" ? startupProfile : undefined,
      agentProfile: startupMode === "agent_service" ? agentProfile : undefined,
      sshPubkey,
      envVarsText,
      bootstrapProfile,
      runtimeFiles: runtimeFiles.map(({ path, content }) => ({ path, content })),
    })
    setName("")
    setRuntimePreset("none")
    setRepoSourceType("none")
    setRepoUrl("")
    setUserRepoId("")
    setRepoRef("")
    setWorkspacePath("")
    setInstallMode("none")
    setInstallProfile("npm")
    setStartupMode("terminal_only")
    setStartupProfile("vite")
    setAgentProfile("codex")
    setSshPubkey("")
    setEnvVarsText("")
    setBootstrapProfile("")
    setRuntimeFiles([])
    setFlavour("dev")
    setKind("ephemeral")
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Provision a Workspace</CardTitle>
        <CardDescription>
          Create a kennel-backed environment, declare bootstrap intent, and let
          the backend own the execution plan.
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
            <Label>Runtime Preset</Label>
            <Select value={runtimePreset} onValueChange={setRuntimePreset}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {RUNTIME_PRESETS.map((preset) => (
                  <SelectItem key={preset.value} value={preset.value}>
                    {preset.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              Use a runtime preset for sane defaults. Keep flavour editable when
              you need to override the base environment.
            </p>
          </div>

          <div className="space-y-1.5">
            <Label>Flavour</Label>
            <Select
              value={flavour}
              onValueChange={(value) => setFlavour(value as WorkspaceFlavour)}
            >
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

        <div className="space-y-4 rounded-xl border bg-muted/20 p-4">
          <div className="space-y-1">
            <div className="text-sm font-medium">Bootstrap Intent</div>
            <p className="text-xs text-muted-foreground">
              Start simple, then opt into repo materialization and runtime setup
              as needed.
            </p>
          </div>

          <div className="space-y-1.5">
            <Label>Repository Source</Label>
            <Select
              value={repoSourceType}
              onValueChange={(value) =>
                setRepoSourceType(value as BootstrapRepoSourceType)
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">None</SelectItem>
                <SelectItem value="external_url">External URL</SelectItem>
                <SelectItem value="user_repo">User Repo</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {repoSourceType === "external_url" ? (
            <div className="space-y-1.5">
              <Label htmlFor="workspace-repo">Repository URL</Label>
              <Input
                id="workspace-repo"
                value={repoUrl}
                onChange={(event) => setRepoUrl(event.target.value)}
                placeholder="https://github.com/example/repo.git"
              />
            </div>
          ) : null}

          {repoSourceType === "user_repo" ? (
            <div className="space-y-1.5">
              <Label htmlFor="workspace-user-repo-id">User Repo Id</Label>
              <Input
                id="workspace-user-repo-id"
                value={userRepoId}
                onChange={(event) => setUserRepoId(event.target.value)}
                placeholder="4a8f8a1e-..."
              />
              <p className="text-xs text-muted-foreground">
                Current slice supports backend-validated user repo ids directly.
              </p>
            </div>
          ) : null}

          {repoSourceType !== "none" ? (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="workspace-repo-ref">Branch or Ref</Label>
                <Input
                  id="workspace-repo-ref"
                  value={repoRef}
                  onChange={(event) => setRepoRef(event.target.value)}
                  placeholder="main"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="workspace-path">Workspace Path</Label>
                <Input
                  id="workspace-path"
                  value={workspacePath}
                  onChange={(event) => setWorkspacePath(event.target.value)}
                  placeholder="/home/dev/workspace"
                />
              </div>
            </div>
          ) : null}

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="space-y-1.5">
              <Label>Install Intent</Label>
              <Select
                value={installMode}
                onValueChange={(value) =>
                  setInstallMode(value as BootstrapInstallMode)
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">None</SelectItem>
                  <SelectItem value="auto">Auto</SelectItem>
                  <SelectItem value="profile">Profile</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label>Startup Intent</Label>
              <Select
                value={startupMode}
                onValueChange={(value) =>
                  setStartupMode(value as BootstrapStartupMode)
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="terminal_only">Terminal Only</SelectItem>
                  <SelectItem value="profile">Profile</SelectItem>
                  <SelectItem value="agent_service">Agent Runtime</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {installMode === "profile" ||
          startupMode === "profile" ||
          startupMode === "agent_service" ? (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {installMode === "profile" ? (
                <div className="space-y-1.5">
                  <Label>Install Profile</Label>
                  <Select
                    value={installProfile}
                    onValueChange={(value) =>
                      setInstallProfile(
                        value as (typeof INSTALL_PROFILES)[number],
                      )
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {INSTALL_PROFILES.map((profile) => (
                        <SelectItem key={profile} value={profile}>
                          {profile}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              ) : null}

              {startupMode === "profile" ? (
                <div className="space-y-1.5">
                  <Label>Startup Profile</Label>
                  <Select
                    value={startupProfile}
                    onValueChange={(value) =>
                      setStartupProfile(
                        value as (typeof STARTUP_PROFILES)[number],
                      )
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {STARTUP_PROFILES.map((profile) => (
                        <SelectItem key={profile} value={profile}>
                          {profile}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              ) : null}

              {startupMode === "agent_service" ? (
                <div className="space-y-1.5">
                  <Label>Agent Runtime Profile</Label>
                  <Select
                    value={agentProfile}
                    onValueChange={(value) =>
                      setAgentProfileWithPreset(
                        value as (typeof AGENT_PROFILES)[number],
                      )
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {AGENT_PROFILES.map((profile) => (
                        <SelectItem key={profile} value={profile}>
                          {profile}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">
                    Agent runtimes are long-running workspace processes. They
                    may not publish a browser URL, but they still appear as
                    discovered runtime surfaces.
                  </p>
                  <p className="text-xs text-muted-foreground">
                    If no runtime preset is selected yet, choosing an agent
                    runtime will prefill the closest preset while keeping it
                    editable.
                  </p>
                </div>
              ) : null}
            </div>
          ) : null}

          <div className="rounded-lg border border-dashed bg-background/80 p-3 text-xs text-muted-foreground">
            {repoSourceType === "none"
              ? startupMode === "agent_service"
                ? "This workspace will come up as a clean environment and start the selected agent runtime as a first-class service."
                : "This workspace will come up as a clean environment with terminal access only."
              : repoSourceType === "external_url"
                ? startupMode === "agent_service"
                  ? "Backend will validate the external repository, materialize it into the workspace, and start the selected agent runtime."
                  : "Backend will validate the external repository, generate a bootstrap plan, and materialize it inside the workspace."
                : startupMode === "agent_service"
                  ? "Backend will validate repo ownership/readiness, materialize the repo, and start the selected agent runtime."
                  : "Backend will validate repo ownership and readiness before generating the bootstrap plan."}
          </div>
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
            placeholder={
              "API_BASE_URL=http://localhost:8000\nFEATURE_FLAG=true"
            }
            rows={4}
          />
          <p className="text-xs text-muted-foreground">
            Use one `KEY=value` pair per line.
          </p>
        </div>

        <Collapsible
          defaultOpen={false}
          className="overflow-hidden rounded-xl border bg-muted/10"
        >
          <CollapsibleTrigger className="group flex w-full items-center justify-between px-4 py-3 text-left">
            <div className="space-y-1">
              <div className="text-sm font-medium">
                Advanced Runtime Overrides
              </div>
              <div className="text-xs text-muted-foreground">
                Override or extend runtime-specific defaults when presets are
                close but not sufficient.
              </div>
            </div>
            <ChevronDown className="h-4 w-4 text-muted-foreground transition-transform duration-200 group-data-[state=open]:rotate-180" />
          </CollapsibleTrigger>
          <CollapsibleContent className="space-y-4 border-t bg-background/70 p-4">
            <div className="space-y-1.5">
              <Label htmlFor="workspace-bootstrap-profile">
                Bootstrap Profile
              </Label>
              <Input
                id="workspace-bootstrap-profile"
                value={bootstrapProfile}
                onChange={(event) => setBootstrapProfile(event.target.value)}
                placeholder="codex_app_server"
              />
              <p className="text-xs text-muted-foreground">
                Optional kennel-side bootstrap profile override.
              </p>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between gap-3">
                <div className="space-y-1">
                  <div className="text-sm font-medium">Runtime Files</div>
                  <div className="text-xs text-muted-foreground">
                    Add or override runtime-owned files by path.
                  </div>
                </div>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    setRuntimeFiles((current) => [
                      ...current,
                      createRuntimeFileDraft(),
                    ])
                  }
                >
                  Add File
                </Button>
              </div>

              {runtimeFiles.length === 0 ? (
                <div className="rounded-lg border border-dashed bg-muted/20 p-3 text-xs text-muted-foreground">
                  No runtime file overrides configured.
                </div>
              ) : null}

              {runtimeFiles.map((entry, index) => (
                <div
                  key={entry.id}
                  className="space-y-3 rounded-lg border bg-background/80 p-3"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="text-sm font-medium">
                      Runtime File {index + 1}
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        setRuntimeFiles((current) =>
                          current.filter((item) => item.id !== entry.id),
                        )
                      }
                    >
                      Remove
                    </Button>
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor={`runtime-file-path-${entry.id}`}>Path</Label>
                    <Input
                      id={`runtime-file-path-${entry.id}`}
                      value={entry.path}
                      onChange={(event) =>
                        setRuntimeFiles((current) =>
                          current.map((item) =>
                            item.id === entry.id
                              ? { ...item, path: event.target.value }
                              : item,
                          ),
                        )
                      }
                      placeholder="/home/dev/.config/runtime.json"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor={`runtime-file-content-${entry.id}`}>
                      Content
                    </Label>
                    <Textarea
                      id={`runtime-file-content-${entry.id}`}
                      value={entry.content}
                      onChange={(event) =>
                        setRuntimeFiles((current) =>
                          current.map((item) =>
                            item.id === entry.id
                              ? { ...item, content: event.target.value }
                              : item,
                          ),
                        )
                      }
                      placeholder={`{\n  "key": "value"\n}`}
                      rows={6}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CollapsibleContent>
        </Collapsible>

        <Button
          onClick={submit}
          disabled={isSubmitting || !name.trim()}
          className="w-full"
        >
          {isSubmitting ? "Provisioning..." : "Create Workspace"}
        </Button>
      </CardContent>
    </Card>
  )
}
