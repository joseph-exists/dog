import { useState } from "react"
import { ChevronDown } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  useIssueWorkspacePlatformServiceAccess,
  useRefreshWorkspacePlatformRuntimeProjection,
  useWorkspacePlatformRuntimeConfig,
} from "@/hooks/useWorkspaces"
import { cn } from "@/lib/utils"
import type { WorkspaceDetailViewModel } from "@/services/workspaceService"
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
  if (status === "ready")
    return "border-emerald-500/30 bg-emerald-500/10 text-emerald-700"
  if (status === "pending")
    return "border-amber-500/30 bg-amber-500/10 text-amber-700"
  if (status === "failed")
    return "border-destructive/30 bg-destructive/10 text-destructive"
  return "border-border bg-muted/40 text-muted-foreground"
}

function accessLevelLabel(
  value: WorkspaceDetailViewModel["accessLevel"],
): string {
  if (value === "manage") return "Manage"
  if (value === "use") return "Use"
  return "View"
}

function freshnessLabel(expiresAt: Date | null): string {
  if (!expiresAt) return "No expiry recorded"
  const remaining = expiresAt.getTime() - Date.now()
  if (remaining <= 0) return "Expired"
  if (remaining <= 2 * 60 * 1000) return "Expiring soon"
  return "Active"
}

function freshnessClass(expiresAt: Date | null): string {
  if (!expiresAt) return "border-border bg-muted/40 text-muted-foreground"
  const remaining = expiresAt.getTime() - Date.now()
  if (remaining <= 0) return "border-rose-500/30 bg-rose-500/10 text-rose-700"
  if (remaining <= 2 * 60 * 1000)
    return "border-amber-500/30 bg-amber-500/10 text-amber-700"
  return "border-emerald-500/30 bg-emerald-500/10 text-emerald-700"
}

export function WorkspaceDetailsPanel({
  workspace,
}: {
  workspace: WorkspaceDetailViewModel
}) {
  const [platformConsumerKind, setPlatformConsumerKind] = useState<
    "workspace_runtime" | "agent_runtime"
  >("workspace_runtime")
  const issuePlatformAccess = useIssueWorkspacePlatformServiceAccess(
    workspace.id,
  )
  const runtimeConfig = useWorkspacePlatformRuntimeConfig(workspace.id)
  const refreshRuntimeProjection = useRefreshWorkspacePlatformRuntimeProjection(
    workspace.id,
  )
  const agentRuntimeServices = workspace.services.filter(
    (service) => service.kind === "agent_runtime",
  )
  const webServices = workspace.services.filter(
    (service) => service.kind !== "agent_runtime",
  )
  const workspaceUnavailableForRuntimeAccess =
    workspace.status === "failed" ||
    workspace.status === "destroying" ||
    workspace.status === "destroyed"

  return (
    <Collapsible defaultOpen={false}>
    <Card>
      <CollapsibleTrigger className="group w-full" asChild>
        <CardHeader className="flex cursor-pointer flex-row items-start justify-between space-y-0">
          <div className="space-y-1">
            <CardTitle>Workspace Details</CardTitle>
            <CardDescription>
              Current lifecycle state, bootstrap intent, and backend-facing
              operational context.
            </CardDescription>
          </div>
          <ChevronDown className="mt-1 h-4 w-4 shrink-0 text-muted-foreground transition-transform duration-200 group-data-[state=open]:rotate-180" />
        </CardHeader>
      </CollapsibleTrigger>
      <CollapsibleContent>
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
            <dt className="text-muted-foreground">Access Level</dt>
            <dd>{accessLevelLabel(workspace.accessLevel)}</dd>
          </div>
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
            <dd>
              {workspace.lastTransitionAt?.toLocaleString() ?? "Not recorded"}
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Terminal Status</dt>
            <dd>{workspace.terminalStatus}</dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Capabilities</dt>
            <dd>
              {[
                workspace.canOpenTerminal ? "terminal" : null,
                workspace.canDiscoverServices ? "service discovery" : null,
                workspace.canManageRuntime ? "runtime management" : null,
              ]
                .filter(Boolean)
                .join(" · ") || "view only"}
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Bootstrap Path</dt>
            <dd>
              {workspace.bootstrapWorkspacePath ?? "Default workspace path"}
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Readiness</dt>
            <dd>
              {(workspace.connectivitySummary ?? workspace.readinessSummary)
                ? [
                    (
                      workspace.connectivitySummary ??
                      workspace.readinessSummary
                    )?.bootstrapComplete
                      ? "bootstrap ready"
                      : "bootstrap pending",
                    (
                      workspace.connectivitySummary ??
                      workspace.readinessSummary
                    )?.terminalReady
                      ? "terminal ready"
                      : "terminal pending",
                    (
                      workspace.connectivitySummary ??
                      workspace.readinessSummary
                    )?.servicesReady
                      ? "services ready"
                      : "services pending",
                  ].join(" · ")
                : "No readiness summary yet"}
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Agent Runtimes</dt>
            <dd>
              {agentRuntimeServices.length > 0
                ? agentRuntimeServices.length
                : "None declared"}
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Discovered Services</dt>
            <dd>
              {workspace.connectivitySummary?.serviceCount ??
                workspace.readinessSummary?.serviceCount ??
                0}
              {(workspace.connectivitySummary?.serviceCount ??
                workspace.readinessSummary?.serviceCount ??
                0) > 0 &&
              (workspace.connectivitySummary?.readyServiceCount ??
                workspace.readinessSummary?.readyServiceCount) !== null
                ? ` (${workspace.connectivitySummary?.readyServiceCount ?? workspace.readinessSummary?.readyServiceCount} ready)`
                : ""}
            </dd>
          </div>
        </dl>
        {workspace.isProjectWorkspace && workspace.accessLevel !== "manage" ? (
          <div className="rounded-lg border bg-muted/20 p-4 text-sm text-muted-foreground">
            This workspace is available through project membership. You can use
            the capabilities exposed by the backend, while runtime-destructive
            actions remain owner-scoped in the current policy pass.
          </div>
        ) : null}
        {workspace.bootstrapIntent || workspace.bootstrapProgress ? (
          <div className="space-y-3 rounded-xl border bg-muted/20 p-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-sm font-medium">Bootstrap</div>
                <div className="text-xs text-muted-foreground">
                  Intent and execution state for repo materialization and
                  runtime setup.
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
                  <span>
                    {workspace.bootstrapProgress.message ??
                      "Preparing bootstrap execution."}
                  </span>
                  {workspace.bootstrapProgress.stepCount ? (
                    <span>
                      {workspace.bootstrapProgress.completedSteps ?? 0}/
                      {workspace.bootstrapProgress.stepCount} steps
                    </span>
                  ) : null}
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-border/60">
                  <div
                    className={cn(
                      "h-full rounded-full bg-foreground/80 transition-all",
                      workspace.bootstrapProgress.phase === "failed" &&
                        "bg-destructive",
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
                  <dd>
                    {Object.keys(workspace.bootstrapIntent.envVars).length}
                  </dd>
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
                  Runtime surfaces inferred from bootstrap profiles and kennel
                  discovery.
                </div>
              </div>
              <span className="rounded-full border bg-background px-2.5 py-1 text-xs text-muted-foreground">
                {workspace.connectivitySummary?.readyServiceCount ??
                  workspace.readinessSummary?.readyServiceCount ??
                  0}
                /
                {workspace.connectivitySummary?.serviceCount ??
                  workspace.readinessSummary?.serviceCount ??
                  workspace.services.length}{" "}
                ready
              </span>
            </div>
            {agentRuntimeServices.length > 0 ? (
              <div className="rounded-lg border bg-background/70 p-3">
                <div className="text-sm font-medium">Agent Runtime Surface</div>
                <div className="mt-1 text-xs text-muted-foreground">
                  Agent runtimes are tracked as long-running workspace
                  processes. They may not publish a browser URL, but they still
                  participate in readiness and future room connectivity.
                </div>
              </div>
            ) : null}
            <div className="space-y-3">
              {workspace.services.map((service) => (
                <div
                  key={service.id}
                  className="rounded-lg border bg-background/70 p-3"
                >
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
                    <div className="mt-2 text-xs text-muted-foreground">
                      {service.readinessMessage}
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
            {webServices.length === 0 && agentRuntimeServices.length > 0 ? (
              <div className="text-xs text-muted-foreground">
                No web endpoints are currently published. This workspace is
                oriented around agent runtime availability rather than browser
                traffic.
              </div>
            ) : null}
          </div>
        ) : null}
        <div className="space-y-3 rounded-xl border bg-muted/20 p-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <div className="text-sm font-medium">Platform Service Access</div>
              <div className="text-xs text-muted-foreground">
                Inspect projected runtime access alongside the current
                backend-issued runtime config and grant surface.
              </div>
            </div>
            <div className="flex w-full flex-col gap-2 sm:w-auto sm:min-w-64">
              <Select
                value={platformConsumerKind}
                onValueChange={(value) =>
                  setPlatformConsumerKind(
                    value as "workspace_runtime" | "agent_runtime",
                  )
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="workspace_runtime">
                    Workspace Runtime
                  </SelectItem>
                  <SelectItem value="agent_runtime">Agent Runtime</SelectItem>
                </SelectContent>
              </Select>
              <Button
                type="button"
                variant="secondary"
                disabled={
                  !workspace.canDiscoverServices ||
                  issuePlatformAccess.isPending
                }
                onClick={() =>
                  issuePlatformAccess.mutate({
                    consumerKind: platformConsumerKind,
                    serviceIds: [],
                  })
                }
              >
                {issuePlatformAccess.isPending
                  ? "Issuing Grant..."
                  : "Issue Access For Enabled Services"}
              </Button>
              <Button
                type="button"
                variant="outline"
                disabled={
                  !workspace.canDiscoverServices || runtimeConfig.isPending
                }
                onClick={() =>
                  runtimeConfig.mutate({
                    consumerKind: platformConsumerKind,
                    serviceIds: [],
                  })
                }
              >
                {runtimeConfig.isPending
                  ? "Resolving Runtime Config..."
                  : "Inspect Current Runtime Config"}
              </Button>
            </div>
          </div>
          {!workspace.canDiscoverServices ? (
            <div className="rounded-lg border bg-background/70 p-3 text-sm text-muted-foreground">
              Platform-service grants become available when this workspace is in
              a service-discoverable state and your current access level
              includes discovery.
            </div>
          ) : null}
          {workspaceUnavailableForRuntimeAccess ? (
            <div className="rounded-lg border bg-background/70 p-3 text-sm text-muted-foreground">
              This workspace is no longer in a runtime-access state. Existing
              projected access should be treated as historical context, and
              fresh runtime access should be requested only after the workspace
              returns to a ready state or a replacement workspace is available.
            </div>
          ) : null}
          {workspace.platformServiceProjection.length > 0 ? (
            <div className="space-y-3">
              <div className="text-sm font-medium">
                Projected Runtime Access
              </div>
              <div className="space-y-3">
                {workspace.platformServiceProjection.map((projection) => (
                  <div
                    key={`${projection.consumerKind}-${projection.issuedAt?.toISOString() ?? "projection"}`}
                    className="rounded-lg border bg-background/70 p-3"
                  >
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                      <div className="space-y-1">
                        <div className="font-medium">
                          {projection.consumerKind.replaceAll("_", " ")}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {projection.issuedAt
                            ? `Projected ${projection.issuedAt.toLocaleString()}`
                            : "Projection timestamp unavailable"}
                          {projection.expiresAt
                            ? ` · Expires ${projection.expiresAt.toLocaleString()}`
                            : ""}
                        </div>
                        {projection.refreshedAt ? (
                          <div className="text-[11px] text-muted-foreground">
                            Last refreshed{" "}
                            {projection.refreshedAt.toLocaleString()}
                          </div>
                        ) : null}
                      </div>
                      <div className="flex items-center gap-2">
                        <span
                          className={cn(
                            "rounded-full border px-2.5 py-1 text-xs",
                            freshnessClass(projection.expiresAt),
                          )}
                        >
                          {freshnessLabel(projection.expiresAt)}
                        </span>
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          disabled={
                            !workspace.canDiscoverServices ||
                            workspaceUnavailableForRuntimeAccess ||
                            refreshRuntimeProjection.isPending
                          }
                          onClick={() =>
                            refreshRuntimeProjection.mutate({
                              consumerKind: projection.consumerKind,
                              serviceIds: projection.serviceIds,
                            })
                          }
                        >
                          {refreshRuntimeProjection.isPending
                            ? "Refreshing..."
                            : "Refresh"}
                        </Button>
                      </div>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {projection.serviceIds.length > 0 ? (
                        projection.serviceIds.map((serviceId) => (
                          <span
                            key={`${projection.consumerKind}-${serviceId}`}
                            className="rounded-full border px-2.5 py-1 text-xs text-muted-foreground"
                          >
                            {serviceId}
                          </span>
                        ))
                      ) : (
                        <span className="text-xs text-muted-foreground">
                          No projected services recorded.
                        </span>
                      )}
                    </div>
                    {projection.runtimeFilePaths.length > 0 ? (
                      <div className="mt-3 space-y-2">
                        <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                          Runtime Files
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {projection.runtimeFilePaths.map((path) => (
                            <span
                              key={`${projection.consumerKind}-${path}`}
                              className="rounded-full border bg-muted/40 px-2.5 py-1 text-xs text-muted-foreground"
                            >
                              {path}
                            </span>
                          ))}
                        </div>
                      </div>
                    ) : null}
                    {projection.injectErrors.length > 0 ? (
                      <div className="mt-3 rounded-lg border border-amber-500/30 bg-amber-500/5 p-3 text-xs text-amber-800">
                        <div className="font-medium">Projection notes</div>
                        <ul className="mt-2 list-disc space-y-1 pl-4">
                          {projection.injectErrors.map((error) => (
                            <li key={`${projection.consumerKind}-${error}`}>
                              {error}
                            </li>
                          ))}
                        </ul>
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            </div>
          ) : null}
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              variant="outline"
              disabled={
                !workspace.canDiscoverServices ||
                workspaceUnavailableForRuntimeAccess ||
                refreshRuntimeProjection.isPending
              }
              onClick={() =>
                refreshRuntimeProjection.mutate({
                  consumerKind: platformConsumerKind,
                  serviceIds: [],
                })
              }
            >
              {refreshRuntimeProjection.isPending
                ? "Refreshing Projection..."
                : "Refresh Runtime Projection"}
            </Button>
          </div>
          {runtimeConfig.data ? (
            <div className="space-y-3">
              <div className="rounded-lg border bg-background/70 p-3 text-sm">
                <div className="font-medium">
                  Current runtime config for{" "}
                  {runtimeConfig.data.consumerKind.replaceAll("_", " ")}
                </div>
                <div className="mt-1 text-xs text-muted-foreground">
                  Issued {runtimeConfig.data.issuedAt.toLocaleString()}
                  {runtimeConfig.data.expiresAt
                    ? ` · Expires ${runtimeConfig.data.expiresAt.toLocaleString()}`
                    : ""}
                </div>
              </div>
              {runtimeConfig.data.services.length > 0 ? (
                <div className="space-y-3">
                  {runtimeConfig.data.services.map((service) => (
                    <div
                      key={`runtime-${service.grantId}`}
                      className="rounded-lg border bg-background/70 p-3"
                    >
                      <div className="flex flex-wrap items-center gap-2">
                        <div className="text-sm font-medium">
                          {service.serviceId}
                        </div>
                        <span className="rounded-full border px-2.5 py-1 text-xs text-muted-foreground">
                          {service.transport}
                        </span>
                        <span className="rounded-full border px-2.5 py-1 text-xs text-muted-foreground">
                          auth {service.authMode}
                        </span>
                      </div>
                      {service.description ? (
                        <div className="mt-2 text-sm text-muted-foreground">
                          {service.description}
                        </div>
                      ) : null}
                      <div className="mt-2 text-sm">
                        <a
                          href={service.url}
                          target="_blank"
                          rel="noreferrer"
                          className="font-medium text-foreground underline underline-offset-4"
                        >
                          {service.url}
                        </a>
                      </div>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {service.tags.map((tag) => (
                          <span
                            key={`runtime-${service.grantId}-${tag}`}
                            className="rounded-full border px-2.5 py-1 text-xs text-muted-foreground"
                          >
                            {tag}
                          </span>
                        ))}
                        {service.scopes.map((scope) => (
                          <span
                            key={`runtime-${service.grantId}-scope-${scope}`}
                            className="rounded-full border bg-muted/40 px-2.5 py-1 text-xs text-muted-foreground"
                          >
                            {scope}
                          </span>
                        ))}
                      </div>
                      {Object.keys(service.scope).length > 0 ? (
                        <pre className="mt-2 overflow-x-auto rounded-lg border bg-muted/40 p-3 text-xs">
                          {JSON.stringify(service.scope, null, 2)}
                        </pre>
                      ) : null}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-lg border bg-background/70 p-3 text-sm text-muted-foreground">
                  No services are currently present in the runtime config.
                </div>
              )}
            </div>
          ) : null}
          {issuePlatformAccess.data ? (
            <div className="space-y-3">
              <div className="rounded-lg border bg-background/70 p-3 text-sm">
                <div className="font-medium">
                  Current grant for{" "}
                  {issuePlatformAccess.data.consumerKind.replaceAll("_", " ")}
                </div>
                <div className="mt-1 text-xs text-muted-foreground">
                  Issued {issuePlatformAccess.data.issuedAt.toLocaleString()}
                  {issuePlatformAccess.data.expiresAt
                    ? ` · Expires ${issuePlatformAccess.data.expiresAt.toLocaleString()}`
                    : ""}
                </div>
              </div>
              {issuePlatformAccess.data.services.length > 0 ? (
                <div className="space-y-3">
                  {issuePlatformAccess.data.services.map((service) => (
                    <div
                      key={service.grantId}
                      className="rounded-lg border bg-background/70 p-3"
                    >
                      <div className="flex flex-wrap items-center gap-2">
                        <div className="text-sm font-medium">
                          {service.serviceId}
                        </div>
                        <span className="rounded-full border px-2.5 py-1 text-xs text-muted-foreground">
                          {service.transport}
                        </span>
                        <span className="rounded-full border px-2.5 py-1 text-xs text-muted-foreground">
                          auth {service.authMode}
                        </span>
                        <span className="rounded-full border px-2.5 py-1 text-xs text-muted-foreground">
                          approval {service.requireApproval}
                        </span>
                      </div>
                      {service.description ? (
                        <div className="mt-2 text-sm text-muted-foreground">
                          {service.description}
                        </div>
                      ) : null}
                      <div className="mt-2 text-sm">
                        <a
                          href={service.url}
                          target="_blank"
                          rel="noreferrer"
                          className="font-medium text-foreground underline underline-offset-4"
                        >
                          {service.url}
                        </a>
                      </div>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {service.tags.map((tag) => (
                          <span
                            key={`${service.grantId}-${tag}`}
                            className="rounded-full border px-2.5 py-1 text-xs text-muted-foreground"
                          >
                            {tag}
                          </span>
                        ))}
                        {service.scopes.map((scope) => (
                          <span
                            key={`${service.grantId}-scope-${scope}`}
                            className="rounded-full border bg-muted/40 px-2.5 py-1 text-xs text-muted-foreground"
                          >
                            {scope}
                          </span>
                        ))}
                      </div>
                      <div className="mt-2 text-xs text-muted-foreground">
                        Grant {service.grantId}
                        {service.expiresAt
                          ? ` · Expires ${service.expiresAt.toLocaleString()}`
                          : ""}
                      </div>
                      {Object.keys(service.scope).length > 0 ? (
                        <pre className="mt-2 overflow-x-auto rounded-lg border bg-muted/40 p-3 text-xs">
                          {JSON.stringify(service.scope, null, 2)}
                        </pre>
                      ) : null}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-lg border bg-background/70 p-3 text-sm text-muted-foreground">
                  No enabled platform services were returned for this grant.
                </div>
              )}
            </div>
          ) : null}
        </div>
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
                <dd>
                  {workspace.flavourHealth.snapshotReady
                    ? "ready"
                    : "not ready"}
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Latest Rebuild</dt>
                <dd>
                  {workspace.flavourHealth.latestRebuildStatus ??
                    "No rebuild data"}
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Rebuild Job</dt>
                <dd>
                  {workspace.flavourHealth.latestRebuildJobId ?? "Not recorded"}
                </dd>
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
              <span className="text-sm text-muted-foreground">
                No actions currently available.
              </span>
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
      </CollapsibleContent>
    </Card>
    </Collapsible>
  )
}
