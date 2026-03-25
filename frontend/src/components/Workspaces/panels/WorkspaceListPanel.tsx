import { Link } from "@tanstack/react-router"
import { ArrowUpRight, TerminalSquare } from "lucide-react"

import { cn } from "@/lib/utils"
import type { WorkspaceListItemViewModel } from "@/services/workspaceService"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { WorkspaceStatusBadge } from "./WorkspaceStatusBadge"

export interface WorkspaceListPanelProps {
  workspaces: WorkspaceListItemViewModel[]
  isLoading: boolean
  error?: Error | null
}

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

export function WorkspaceListPanel({
  workspaces,
  isLoading,
  error,
}: WorkspaceListPanelProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Workspace Fleet</CardTitle>
        <CardDescription>
          Track provisioning, open ready environments, and keep an eye on lifecycle state.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-20 w-full rounded-xl" />
            <Skeleton className="h-20 w-full rounded-xl" />
            <Skeleton className="h-20 w-full rounded-xl" />
          </div>
        ) : null}

        {error ? (
          <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
            {error.message}
          </div>
        ) : null}

        {!isLoading && !error && workspaces.length === 0 ? (
          <div className="rounded-xl border border-dashed p-8 text-center">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full border bg-card">
              <TerminalSquare className="h-5 w-5 text-muted-foreground" />
            </div>
            <h3 className="text-sm font-medium">No workspaces yet</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              Provision a workspace to start validating the kennel integration flow.
            </p>
          </div>
        ) : null}

        {!isLoading && !error && workspaces.length > 0 ? (
          <div className="space-y-3">
            {workspaces.map((workspace) => {
              const agentRuntime = workspace.services.find((service) => service.kind === "agent_runtime")
              const primaryWebService = workspace.services.find((service) => service.url)
              return (
              <div
                key={workspace.id}
                className="flex flex-col gap-3 rounded-xl border bg-card/60 p-4 md:flex-row md:items-center md:justify-between"
              >
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <div className="font-medium">{workspace.name}</div>
                    <WorkspaceStatusBadge status={workspace.status} />
                    {workspace.projectSummary ? (
                      <span className="rounded-full border px-2.5 py-0.5 text-xs text-muted-foreground">
                        Project: {workspace.projectSummary.name}
                      </span>
                    ) : null}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {workspace.flavour} · {workspace.kind} · updated{" "}
                    {workspace.updatedAt.toLocaleString()}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Visibility: {workspace.visibility} · Terminal: {workspace.terminalStatus}
                  </div>
                  {agentRuntime ? (
                    <div className="flex flex-wrap items-center gap-2 text-xs">
                      <span className="rounded-full border bg-background px-2 py-0.5 text-muted-foreground">
                        Agent runtime: {agentRuntime.label}
                      </span>
                      <span className={cn("rounded-full border px-2 py-0.5 capitalize", serviceStatusClass(agentRuntime.status))}>
                        {agentRuntime.status}
                      </span>
                    </div>
                  ) : null}
                  {workspace.connectivitySummary || workspace.services.length > 0 ? (
                    <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                      <span>
                        Services ready:{" "}
                        {workspace.connectivitySummary?.readyServiceCount ??
                          workspace.readinessSummary?.readyServiceCount ??
                          workspace.services.filter((service) => service.status === "ready").length}
                        /
                        {workspace.connectivitySummary?.serviceCount ??
                          workspace.readinessSummary?.serviceCount ??
                          workspace.services.length}
                      </span>
                      {workspace.connectivitySummary?.terminalReady ? <span>· terminal ready</span> : null}
                      {workspace.flavourHealth ? (
                        <>
                          <span>·</span>
                          <span>
                            flavour snapshot {workspace.flavourHealth.snapshotReady ? "ready" : "pending"}
                          </span>
                        </>
                      ) : null}
                    </div>
                  ) : null}
                  {workspace.bootstrapIntent || workspace.bootstrapProgress ? (
                    <div className="space-y-2 rounded-lg border bg-muted/20 p-3">
                      <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                        {workspace.bootstrapIntent?.repoSource ? (
                          <span>
                            {workspace.bootstrapIntent.repoSource.label}: {workspace.bootstrapIntent.repoSource.detail}
                          </span>
                        ) : (
                          <span>Clean environment bootstrap</span>
                        )}
                        {workspace.bootstrapProgress ? (
                          <>
                            <span>·</span>
                            <span className="capitalize">
                              {formatBootstrapPhase(workspace.bootstrapProgress.phase)}
                            </span>
                          </>
                        ) : null}
                      </div>
                      {workspace.bootstrapProgress ? (
                        <>
                          <div className="text-sm text-muted-foreground">
                            {workspace.bootstrapProgress.message ?? "Bootstrap status available."}
                          </div>
                          {workspace.bootstrapProgress.stepCount ? (
                            <div className="space-y-1">
                              <div className="h-1.5 overflow-hidden rounded-full bg-border/60">
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
                              <div className="text-xs text-muted-foreground">
                                {workspace.bootstrapProgress.completedSteps ?? 0}/
                                {workspace.bootstrapProgress.stepCount} steps
                              </div>
                            </div>
                          ) : null}
                        </>
                      ) : null}
                      {workspace.startedServices.length > 0 ? (
                        <div className="flex flex-wrap gap-2">
                          {workspace.startedServices.map((service) => (
                            <span
                              key={service}
                              className="rounded-full border bg-background px-2 py-0.5 text-xs text-muted-foreground"
                            >
                              {service}
                            </span>
                          ))}
                        </div>
                      ) : null}
                    </div>
                  ) : null}
                  {workspace.services.length > 0 ? (
                    <div className="space-y-2 rounded-lg border bg-muted/20 p-3">
                      <div className="text-xs text-muted-foreground">
                        {agentRuntime ? "Discovered runtime surfaces" : "Discovered runtime services"}
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {workspace.services.slice(0, 3).map((service) => (
                          <span
                            key={service.id}
                            className={cn(
                              "rounded-full border px-2 py-0.5 text-xs",
                              serviceStatusClass(service.status),
                            )}
                          >
                            {service.label} · {serviceKindLabel(service.kind)} · {formatServiceLabel(service.status)}
                          </span>
                        ))}
                        {workspace.services.length > 3 ? (
                          <span className="rounded-full border bg-background px-2 py-0.5 text-xs text-muted-foreground">
                            +{workspace.services.length - 3} more
                          </span>
                        ) : null}
                      </div>
                      {primaryWebService?.url ? (
                        <div className="text-sm text-muted-foreground">
                          Primary web endpoint:{" "}
                          <a
                            href={primaryWebService.url}
                            target="_blank"
                            rel="noreferrer"
                            className="font-medium text-foreground underline underline-offset-4"
                          >
                            {primaryWebService.url}
                          </a>
                        </div>
                      ) : agentRuntime ? (
                        <div className="text-sm text-muted-foreground">
                          Agent runtime readiness is tracked through discovery even when no browser-facing endpoint is published.
                        </div>
                      ) : null}
                    </div>
                  ) : null}
                  {workspace.failureMessage ? (
                    <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
                      {workspace.failureMessage}
                    </div>
                  ) : null}
                </div>
                <Button asChild variant="outline" size="sm" className="w-fit">
                  <Link
                    to="/workspace/$workspaceId"
                    params={{ workspaceId: workspace.id }}
                  >
                    Open Details
                    <ArrowUpRight className="ml-2 h-4 w-4" />
                  </Link>
                </Button>
              </div>
              )
            })}
          </div>
        ) : null}
      </CardContent>
    </Card>
  )
}
