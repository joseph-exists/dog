import { cn } from "@/lib/utils"
import type { WorkspaceDetailViewModel } from "@/services/workspaceService"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { WorkspaceStatusBadge } from "./WorkspaceStatusBadge"

function formatBootstrapPhase(phase: string): string {
  return phase.replaceAll("_", " ")
}

function formatServiceLabel(value: string): string {
  return value.replaceAll("_", " ")
}

function serviceKindLabel(kind: string): string {
  return kind === "agent_runtime" ? "Agent Runtime" : formatServiceLabel(kind)
}

function serviceStatusClass(status: string): string {
  if (status === "ready") return "border-emerald-500/30 bg-emerald-500/10 text-emerald-700"
  if (status === "pending") return "border-amber-500/30 bg-amber-500/10 text-amber-700"
  if (status === "failed") return "border-destructive/30 bg-destructive/10 text-destructive"
  return "border-border bg-muted/40 text-muted-foreground"
}

export function WorkspaceDetailsPanel({ workspace }: { workspace: WorkspaceDetailViewModel }) {
  const agentRuntimeServices = workspace.services.filter((service) => service.kind === "agent_runtime")
  const webServices = workspace.services.filter((service) => service.kind !== "agent_runtime")

  return (
    <Card>
      <CardHeader>
        <CardTitle>Workspace Details</CardTitle>
        <CardDescription>
          Current lifecycle state, bootstrap intent, and backend-facing operational context.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">{workspace.name}</span>
          <WorkspaceStatusBadge status={workspace.status} />
        </div>
        {workspace.failureMessage ? (
          <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
            {workspace.failureMessage}
          </div>
        ) : null}
        <dl className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-muted-foreground">Visibility</dt>
            <dd>{workspace.visibility}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Project</dt>
            <dd>{workspace.projectSummary?.name ?? "Not assigned"}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Flavour</dt>
            <dd>{workspace.flavour}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Kind</dt>
            <dd>{workspace.kind}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Kennel Name</dt>
            <dd>{workspace.kennelName ?? "Not assigned"}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Kennel Job</dt>
            <dd>{workspace.kennelJob ?? "Not assigned"}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Created</dt>
            <dd>{workspace.createdAt.toLocaleString()}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Updated</dt>
            <dd>{workspace.updatedAt.toLocaleString()}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Last Transition</dt>
            <dd>{workspace.lastTransitionAt?.toLocaleString() ?? "Not recorded"}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Terminal Status</dt>
            <dd>{workspace.terminalStatus}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Bootstrap Path</dt>
            <dd>{workspace.bootstrapWorkspacePath ?? "Default workspace path"}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Readiness</dt>
            <dd>
              {workspace.connectivitySummary ?? workspace.readinessSummary
                ? [
                    (workspace.connectivitySummary ?? workspace.readinessSummary)?.bootstrapComplete
                      ? "bootstrap ready"
                      : "bootstrap pending",
                    (workspace.connectivitySummary ?? workspace.readinessSummary)?.terminalReady
                      ? "terminal ready"
                      : "terminal pending",
                    (workspace.connectivitySummary ?? workspace.readinessSummary)?.servicesReady
                      ? "services ready"
                      : "services pending",
                  ].join(" · ")
                : "No readiness summary yet"}
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Agent Runtimes</dt>
            <dd>{agentRuntimeServices.length > 0 ? agentRuntimeServices.length : "None declared"}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Discovered Services</dt>
            <dd>
              {workspace.connectivitySummary?.serviceCount ?? workspace.readinessSummary?.serviceCount ?? 0}
              {(workspace.connectivitySummary?.serviceCount ?? workspace.readinessSummary?.serviceCount ?? 0) > 0 &&
              (workspace.connectivitySummary?.readyServiceCount ?? workspace.readinessSummary?.readyServiceCount) !== null
                ? ` (${workspace.connectivitySummary?.readyServiceCount ?? workspace.readinessSummary?.readyServiceCount} ready)`
                : ""}
            </dd>
          </div>
        </dl>
        {workspace.bootstrapIntent || workspace.bootstrapProgress ? (
          <div className="space-y-3 rounded-xl border bg-muted/20 p-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-sm font-medium">Bootstrap</div>
                <div className="text-xs text-muted-foreground">
                  Intent and execution state for repo materialization and runtime setup.
                </div>
              </div>
              {workspace.bootstrapProgress ? (
                <span className="rounded-full border bg-background px-2.5 py-1 text-xs text-muted-foreground capitalize">
                  {formatBootstrapPhase(workspace.bootstrapProgress.phase)}
                </span>
              ) : null}
            </div>

            {workspace.bootstrapProgress ? (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>{workspace.bootstrapProgress.message ?? "Preparing bootstrap execution."}</span>
                  {workspace.bootstrapProgress.stepCount ? (
                    <span>
                      {workspace.bootstrapProgress.completedSteps ?? 0}/{workspace.bootstrapProgress.stepCount} steps
                    </span>
                  ) : null}
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-border/60">
                  <div
                    className={cn(
                      "h-full rounded-full bg-foreground/80 transition-all",
                      workspace.bootstrapProgress.phase === "failed" && "bg-destructive",
                    )}
                    style={{
                      width: `${Math.round((workspace.bootstrapProgress.completionRatio ?? 0) * 100)}%`,
                    }}
                  />
                </div>
                {workspace.bootstrapProgress.failureMessage ? (
                  <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
                    {workspace.bootstrapProgress.failureMessage}
                  </div>
                ) : null}
              </div>
            ) : null}

            {workspace.bootstrapIntent ? (
              <dl className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
                <div>
                  <dt className="text-muted-foreground">Repo Source</dt>
                  <dd>
                    {workspace.bootstrapIntent.repoSource
                      ? `${workspace.bootstrapIntent.repoSource.label} · ${workspace.bootstrapIntent.repoSource.detail}`
                      : "No repo source declared"}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Install Intent</dt>
                  <dd>
                    {workspace.bootstrapIntent.installMode}
                    {workspace.bootstrapIntent.installProfile
                      ? ` · ${workspace.bootstrapIntent.installProfile}`
                      : ""}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Startup Intent</dt>
                  <dd>
                    {workspace.bootstrapIntent.startupMode === "agent_service"
                      ? "agent runtime"
                      : workspace.bootstrapIntent.startupMode}
                    {workspace.bootstrapIntent.startupProfile
                      ? ` · ${workspace.bootstrapIntent.startupProfile}`
                      : ""}
                    {workspace.bootstrapIntent.agentProfile
                      ? ` · ${workspace.bootstrapIntent.agentProfile}`
                      : ""}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Env Vars</dt>
                  <dd>{Object.keys(workspace.bootstrapIntent.envVars).length}</dd>
                </div>
              </dl>
            ) : null}

            {workspace.startedServices.length > 0 ? (
              <div className="space-y-2">
                <div className="text-sm font-medium">Started Services</div>
                <div className="flex flex-wrap gap-2">
                  {workspace.startedServices.map((service) => (
                    <span
                      key={service}
                      className="rounded-full border bg-background px-2.5 py-1 text-xs text-muted-foreground"
                    >
                      {service}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        ) : null}
        {workspace.services.length > 0 ? (
          <div className="space-y-3 rounded-xl border bg-muted/20 p-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-sm font-medium">Discovered Services</div>
                <div className="text-xs text-muted-foreground">
                  Runtime surfaces inferred from bootstrap profiles and kennel discovery.
                </div>
              </div>
              <span className="rounded-full border bg-background px-2.5 py-1 text-xs text-muted-foreground">
                {workspace.connectivitySummary?.readyServiceCount ?? workspace.readinessSummary?.readyServiceCount ?? 0}/
                {workspace.connectivitySummary?.serviceCount ?? workspace.readinessSummary?.serviceCount ?? workspace.services.length} ready
              </span>
            </div>
            {agentRuntimeServices.length > 0 ? (
              <div className="rounded-lg border bg-background/70 p-3">
                <div className="text-sm font-medium">Agent Runtime Surface</div>
                <div className="mt-1 text-xs text-muted-foreground">
                  Agent runtimes are tracked as long-running workspace processes. They may not publish a browser URL, but they still participate in readiness and future room connectivity.
                </div>
              </div>
            ) : null}
            <div className="space-y-3">
              {workspace.services.map((service) => (
                <div key={service.id} className="rounded-lg border bg-background/70 p-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <div className="text-sm font-medium">{service.label}</div>
                    <span
                      className={cn(
                        "rounded-full border px-2.5 py-1 text-xs capitalize",
                        serviceStatusClass(service.status),
                      )}
                    >
                      {service.status}
                    </span>
                    <span className="rounded-full border px-2.5 py-1 text-xs text-muted-foreground">
                      {serviceKindLabel(service.kind)}
                    </span>
                    {service.source ? (
                      <span className="rounded-full border px-2.5 py-1 text-xs text-muted-foreground">
                        {formatServiceLabel(service.source)}
                      </span>
                    ) : null}
                  </div>
                  <div className="mt-2 text-sm text-muted-foreground">
                    {service.url ? (
                      <a
                        href={service.url}
                        target="_blank"
                        rel="noreferrer"
                        className="font-medium text-foreground underline underline-offset-4"
                      >
                        {service.url}
                      </a>
                    ) : service.kind === "agent_runtime" ? (
                      "Runtime is process-backed and currently has no browser-facing endpoint."
                    ) : service.host || service.port ? (
                      `${service.protocol ?? "tcp"}://${service.host ?? "127.0.0.1"}${service.port ? `:${service.port}` : ""}${service.path ?? ""}`
                    ) : (
                      "Endpoint details are still being resolved."
                    )}
                  </div>
                  {service.readinessMessage ? (
                    <div className="mt-2 text-xs text-muted-foreground">{service.readinessMessage}</div>
                  ) : null}
                </div>
              ))}
            </div>
            {webServices.length === 0 && agentRuntimeServices.length > 0 ? (
              <div className="text-xs text-muted-foreground">
                No web endpoints are currently published. This workspace is oriented around agent runtime availability rather than browser traffic.
              </div>
            ) : null}
          </div>
        ) : null}
        {workspace.flavourHealth ? (
          <div className="space-y-3 rounded-xl border bg-muted/20 p-4">
            <div>
              <div className="text-sm font-medium">Flavour Health</div>
              <div className="text-xs text-muted-foreground">
                Operator snapshot context for the backing workspace flavour.
              </div>
            </div>
            <dl className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-muted-foreground">Snapshot Ready</dt>
                <dd>{workspace.flavourHealth.snapshotReady ? "ready" : "not ready"}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Latest Rebuild</dt>
                <dd>{workspace.flavourHealth.latestRebuildStatus ?? "No rebuild data"}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Rebuild Job</dt>
                <dd>{workspace.flavourHealth.latestRebuildJobId ?? "Not recorded"}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Flavour Key</dt>
                <dd>{workspace.flavourHealth.flavour}</dd>
              </div>
            </dl>
          </div>
        ) : null}
        <div className="space-y-2">
          <div className="text-sm font-medium">Current Action Surface</div>
          <div className="flex flex-wrap gap-2">
            {workspace.allowedActions.length > 0 ? (
              workspace.allowedActions.map((action) => (
                <span
                  key={action}
                  className="rounded-full border bg-muted/40 px-2.5 py-1 text-xs text-muted-foreground"
                >
                  {action}
                </span>
              ))
            ) : (
              <span className="text-sm text-muted-foreground">No actions currently available.</span>
            )}
          </div>
        </div>
        {Object.keys(workspace.meta).length > 0 ? (
          <div className="space-y-2">
            <div className="text-sm font-medium">Metadata</div>
            <pre className="overflow-x-auto rounded-lg border bg-muted/40 p-3 text-xs">
              {JSON.stringify(workspace.meta, null, 2)}
            </pre>
          </div>
        ) : null}
      </CardContent>
    </Card>
  )
}
