/**
 * Agent Detail Page
 *
 * Full page view for a single agent with:
 * - Agent header with avatar and metadata
 * - Tabs for Overview, System Prompt, Settings
 * - Clone button for system agents
 * - Edit capability for personal agents
 */

import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"
import {
  ArrowLeftIcon,
  FileTextIcon,
  SettingsIcon,
  AlertCircleIcon,
} from "lucide-react"
import { Suspense } from "react"

import { AgentsService } from "@/client/sdk.gen"
import {
  AgentAvatar,
  AgentCloneButton,
  AgentModeBadge,
  AgentProviderSelector,
  AgentScopeBadge,
  AgentStatusBadge,
  EditAgentDialog,
  type ParticipationMode,
} from "@/components/Agents"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export const Route = createFileRoute("/_layout/agent/$agentId")({
  component: AgentDetailPage,
  head: () => ({
    meta: [{ title: "Agent Details - TinyFoot" }],
  }),
})

function AgentDetailSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header skeleton */}
      <div className="flex items-start gap-6">
        <Skeleton className="size-24 rounded-full" />
        <div className="flex-1 space-y-3">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-32" />
          <div className="flex gap-2">
            <Skeleton className="h-6 w-20" />
            <Skeleton className="h-6 w-24" />
          </div>
        </div>
      </div>
      {/* Tabs skeleton */}
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-64 w-full" />
    </div>
  )
}

function AgentDetailContent({ agentId }: { agentId: string }) {
  const navigate = useNavigate()

  const {
    data: agent,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["agent", agentId],
    queryFn: () => AgentsService.getAgent({ agentId }),
  })

  if (isLoading) {
    return <AgentDetailSkeleton />
  }

  if (error || !agent) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-destructive/10 p-4 mb-4">
          <AlertCircleIcon className="size-8 text-destructive" />
        </div>
        <h3 className="text-lg font-semibold">Agent not found</h3>
        <p className="text-muted-foreground mb-4">
          This agent doesn't exist or you don't have access to it.
        </p>
        <Button variant="outline" onClick={() => navigate({ to: "/agents" })}>
          <ArrowLeftIcon className="size-4" />
          Back to Agents
        </Button>
      </div>
    )
  }

  const isPersonal = agent.scope === "personal"
  const isSystem = agent.scope === "system"

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink asChild>
              <Link to="/agents">Agents</Link>
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>{agent.name}</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      {/* Agent Header */}
      <div className="flex items-start gap-6">
        <AgentAvatar name={agent.name} size="xl" />

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl font-bold tracking-tight">{agent.name}</h1>
            {agent.scope && (
              <AgentScopeBadge scope={agent.scope as "system" | "personal"} />
            )}
            <AgentStatusBadge isEnabled={agent.is_enabled ?? true} />
          </div>

          <p className="text-muted-foreground font-mono text-sm mt-1">
            @{agent.slug}
          </p>

          {agent.description && (
            <p className="text-muted-foreground mt-2 max-w-2xl">
              {agent.description}
            </p>
          )}

          <div className="flex items-center gap-2 mt-4 flex-wrap">
            {agent.participation_mode && (
              <AgentModeBadge
                mode={agent.participation_mode as ParticipationMode}
              />
            )}
            {agent.model_name && (
              <span className="text-xs px-2 py-1 rounded-md bg-muted font-mono">
                {agent.model_name}
              </span>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 shrink-0">
          {isSystem && (
            <AgentCloneButton
              agent={agent}
              onSuccess={(newAgent) =>
                navigate({ to: "/agent/$agentId", params: { agentId: newAgent.id } })
              }
            />
          )}
          {isPersonal && <EditAgentDialog agent={agent} />}
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="overview" className="w-full">
        <TabsList>
          <TabsTrigger value="overview">
            <FileTextIcon className="size-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="prompt">System Prompt</TabsTrigger>
          <TabsTrigger value="my-settings">
            <SettingsIcon className="size-4" />
            My Settings
          </TabsTrigger>
          {isPersonal && (
            <TabsTrigger value="settings">
              <SettingsIcon className="size-4" />
              Agent Settings
            </TabsTrigger>
          )}
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="mt-6">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Created
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-lg font-semibold">
                  {new Date(agent.created_at).toLocaleDateString()}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Last Updated
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-lg font-semibold">
                  {agent.updated_at
                    ? new Date(agent.updated_at).toLocaleDateString()
                    : "Never"}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Version
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-lg font-semibold">v{agent.version}</p>
              </CardContent>
            </Card>

            {agent.owner_id && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    Owner
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-lg font-semibold font-mono text-sm truncate">
                    {agent.owner_id}
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* System Prompt Tab */}
        <TabsContent value="prompt" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>System Prompt</CardTitle>
            </CardHeader>
            <CardContent>
              {agent.system_prompt ? (
                <div className="p-4 rounded-md bg-muted font-mono text-sm whitespace-pre-wrap max-h-[500px] overflow-y-auto">
                  {agent.system_prompt}
                </div>
              ) : (
                <p className="text-muted-foreground italic">
                  No system prompt configured
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* My Settings Tab (User's provider preferences for this agent) */}
        <TabsContent value="my-settings" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>My Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <p className="text-muted-foreground">
                Configure your personal settings for this agent. These settings only
                affect how the agent works for you.
              </p>

              {agent.model_name && (
                <AgentProviderSelector
                  agentId={agent.id}
                  modelName={agent.model_name}
                />
              )}

              {!agent.model_name && (
                <p className="text-sm text-muted-foreground italic">
                  This agent doesn't have a model configured, so provider selection
                  is not available.
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Settings Tab (Personal agents only) */}
        {isPersonal && (
          <TabsContent value="settings" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Agent Settings</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-muted-foreground">
                  Use the Edit button above to modify this agent's settings.
                </p>

                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">
                      Model
                    </p>
                    <p className="font-mono">{agent.model_name || "Default"}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">
                      Participation Mode
                    </p>
                    <p>{agent.participation_mode || "on_mention"}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">
                      Status
                    </p>
                    <p>{agent.is_enabled ? "Enabled" : "Disabled"}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">
                      Scope
                    </p>
                    <p className="capitalize">{agent.scope}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        )}
      </Tabs>
    </div>
  )
}

function AgentDetailPage() {
  const { agentId } = Route.useParams()

  return (
    <Suspense fallback={<AgentDetailSkeleton />}>
      <AgentDetailContent agentId={agentId} />
    </Suspense>
  )
}
