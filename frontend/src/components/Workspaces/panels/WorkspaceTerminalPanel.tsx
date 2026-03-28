import { ChevronDown } from "lucide-react"
import { TerminalPanel } from "@/components/Terminal"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import type {
  WorkspaceDetailViewModel,
  WorkspaceTerminalDescriptor,
} from "@/services/workspaceService"

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

export interface WorkspaceTerminalPanelProps {
  workspace: WorkspaceDetailViewModel
  terminal: WorkspaceTerminalDescriptor | null
  isLoadingTerminal: boolean
  terminalError?: Error | null
  onRequestTerminal: () => Promise<unknown>
}

export function WorkspaceTerminalPanel({
  workspace,
  terminal,
  isLoadingTerminal,
  terminalError,
  onRequestTerminal,
}: WorkspaceTerminalPanelProps) {
  const agentRuntimeServices = workspace.services.filter(
    (service) => service.kind === "agent_runtime",
  )
  const accessSummary =
    workspace.accessLevel === "manage"
      ? "You can request terminal access and manage this workspace from the current account."
      : workspace.canOpenTerminal
        ? "This workspace is available through your current project access, and terminal use is allowed."
        : "This workspace is visible in your current access scope, but terminal access is not available from this account."

  return (
    <Collapsible
      defaultOpen={true}
      className="overflow-hidden rounded-xl border bg-card"
    >
      <CollapsibleTrigger className="group flex w-full items-center justify-between border-b px-4 py-3">
        <span className="text-sm font-medium">Terminal</span>
        <ChevronDown className="h-4 w-4 text-muted-foreground transition-transform duration-200 group-data-[state=open]:rotate-180" />
      </CollapsibleTrigger>
      <CollapsibleContent>
        <TerminalPanel
          terminalUrl={terminal?.terminalUrl ?? null}
          canRequestTerminal={workspace.canOpenTerminal}
          isRequestingTerminal={isLoadingTerminal}
          terminalError={terminalError}
          onRequestTerminal={onRequestTerminal}
          className="rounded-none border-none"
          metadata={
            <div className="space-y-3">
              <div className="rounded-xl border bg-muted/30 p-4 text-sm">
                Workspace status:{" "}
                <span className="font-medium">{workspace.status}</span>
                <span className="mx-2 text-muted-foreground">·</span>
                Terminal status:{" "}
                <span className="font-medium">{workspace.terminalStatus}</span>
                <span className="mx-2 text-muted-foreground">·</span>
                Access:{" "}
                <span className="font-medium">{workspace.accessLevel}</span>
                {workspace.connectivitySummary ? (
                  <>
                    <span className="mx-2 text-muted-foreground">·</span>
                    Services:{" "}
                    <span className="font-medium">
                      {workspace.connectivitySummary.readyServiceCount ?? 0}/
                      {workspace.connectivitySummary.serviceCount ?? 0} ready
                    </span>
                  </>
                ) : null}
                {workspace.bootstrapProgress ? (
                  <>
                    <span className="mx-2 text-muted-foreground">·</span>
                    Bootstrap phase:{" "}
                    <span className="font-medium">
                      {workspace.bootstrapProgress.phase}
                    </span>
                  </>
                ) : null}
              </div>

              <div className="rounded-lg border bg-muted/20 p-4 text-sm text-muted-foreground">
                {accessSummary}
              </div>

              {workspace.failureMessage ? (
                <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
                  {workspace.failureMessage}
                </div>
              ) : null}

              {workspace.bootstrapProgress?.message ? (
                <div className="rounded-lg border bg-muted/20 p-4 text-sm text-muted-foreground">
                  {workspace.bootstrapProgress.message}
                </div>
              ) : null}

              {workspace.startedServices.length > 0 ? (
                <div className="rounded-lg border bg-muted/20 p-4 text-sm">
                  <div className="mb-2 font-medium">Started Services</div>
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

              {agentRuntimeServices.length > 0 ? (
                <div className="rounded-lg border bg-muted/20 p-4 text-sm">
                  <div className="mb-2 font-medium">Agent Runtime Status</div>
                  <div className="space-y-2">
                    {agentRuntimeServices.map((service) => (
                      <div
                        key={service.id}
                        className="rounded-lg border bg-background/80 p-3"
                      >
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-medium">{service.label}</span>
                          <span
                            className={`rounded-full border px-2.5 py-1 text-xs capitalize ${serviceStatusClass(service.status)}`}
                          >
                            {service.status}
                          </span>
                          <span className="rounded-full border bg-background px-2.5 py-1 text-xs text-muted-foreground">
                            {serviceKindLabel(service.kind)}
                          </span>
                        </div>
                        <div className="mt-2 text-xs text-muted-foreground">
                          {service.readinessMessage ??
                            "Agent runtime discovery is active. This runtime may be available for room connectivity even when it does not publish a browser endpoint."}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}

              {workspace.services.length > 0 ? (
                <div className="rounded-lg border bg-muted/20 p-4 text-sm">
                  <div className="mb-2 font-medium">Discovered Services</div>
                  <div className="space-y-2">
                    {workspace.services.map((service) => (
                      <div
                        key={service.id}
                        className="flex flex-col gap-2 rounded-lg border bg-background/80 p-3 sm:flex-row sm:items-center sm:justify-between"
                      >
                        <div className="space-y-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-medium">{service.label}</span>
                            <span
                              className={`rounded-full border px-2.5 py-1 text-xs capitalize ${serviceStatusClass(service.status)}`}
                            >
                              {service.status}
                            </span>
                            <span className="rounded-full border bg-background px-2.5 py-1 text-xs text-muted-foreground">
                              {serviceKindLabel(service.kind)}
                            </span>
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {service.readinessMessage ??
                              (service.url
                                ? "Service endpoint is available."
                                : "Endpoint discovery is still resolving.")}
                          </div>
                        </div>
                        {service.url ? (
                          <a
                            href={service.url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-sm font-medium underline underline-offset-4"
                          >
                            Open service
                          </a>
                        ) : service.kind === "agent_runtime" ? (
                          <div className="text-xs text-muted-foreground">
                            No browser endpoint published. Use terminal access
                            and later room connectivity surfaces to interact
                            with this runtime.
                          </div>
                        ) : (
                          <div className="text-xs text-muted-foreground">
                            {service.host || service.port
                              ? `${service.protocol ?? "tcp"}://${service.host ?? "127.0.0.1"}${service.port ? `:${service.port}` : ""}${service.path ?? ""}`
                              : "No endpoint published yet"}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}

              {!workspace.canOpenTerminal ? (
                <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
                  {workspace.bootstrapProgress?.phase === "failed"
                    ? "Terminal access is currently withheld because bootstrap failed before the workspace reached a terminal-ready state."
                    : "Terminal access becomes available when the backend exposes the `request_terminal` action for this workspace."}
                </div>
              ) : null}

              {terminal ? (
                <div className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-3">
                  <div>
                    <div className="text-muted-foreground">Protocol</div>
                    <div>{terminal.protocol}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Host</div>
                    <div>{terminal.host}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">
                      Connection Model
                    </div>
                    <div>
                      {terminal.isDirectConnection ? "direct" : "proxied"}
                    </div>
                  </div>
                </div>
              ) : null}
            </div>
          }
        />
      </CollapsibleContent>
    </Collapsible>
  )
}
