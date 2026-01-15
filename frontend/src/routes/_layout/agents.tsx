/**
 * My Agents Page
 *
 * Dashboard for managing personal agents.
 * Users can create, edit, and delete their agents.
 */

import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { BotIcon, ExternalLinkIcon, Loader2Icon, TrashIcon } from "lucide-react"
import { Suspense, useState } from "react"

import type { ApiError } from "@/client/core/ApiError"
import { AgentsService } from "@/client/sdk.gen"
import type { AgentConfigPublic } from "@/client/types.gen"
import AgentAvatar from "@/components/Agents/AgentAvatar"
import { AgentModeBadge, AgentScopeBadge } from "@/components/Agents/AgentBadge"
import CreateAgentDialog from "@/components/Agents/CreateAgentDialog"
import EditAgentDialog from "@/components/Agents/EditAgentDialog"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import useCustomToast from "@/hooks/useCustomToast"
import type { ParticipationMode } from "@/components/Agents/AgentBadge"

function getAgentsQueryOptions() {
  return {
    queryFn: () => AgentsService.listAgents({ skip: 0, limit: 100 }),
    queryKey: ["agents"],
  }
}

export const Route = createFileRoute("/_layout/agents")({
  component: AgentsPage,
  head: () => ({
    meta: [
      {
        title: "My Agents - TinyFoot",
      },
    ],
  }),
})

function AgentCardSkeleton() {
  return (
    <Card>
      <CardHeader className="flex flex-row items-start gap-4">
        <Skeleton className="size-12 rounded-full" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-4 w-48" />
        </div>
      </CardHeader>
      <CardContent>
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4 mt-2" />
      </CardContent>
    </Card>
  )
}

function PendingAgents() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <AgentCardSkeleton />
      <AgentCardSkeleton />
      <AgentCardSkeleton />
    </div>
  )
}

function DeleteAgentButton({ agent }: { agent: AgentConfigPublic }) {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const mutation = useMutation({
    mutationFn: () => AgentsService.deleteAgent({ agentId: agent.id }),
    onSuccess: () => {
      showSuccessToast(`Agent "${agent.name}" deleted successfully.`)
      setIsOpen(false)
    },
    onError: (err: ApiError) => {
      const message =
        (err.body as { detail?: string })?.detail || "Failed to delete agent"
      showErrorToast(message)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["agents"] })
    },
  })

  return (
    <AlertDialog open={isOpen} onOpenChange={setIsOpen}>
      <AlertDialogTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="text-muted-foreground hover:text-destructive hover:bg-destructive/10"
        >
          <TrashIcon className="size-4" />
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Agent</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to delete "{agent.name}"? This action cannot
            be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={mutation.isPending}>
            Cancel
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {mutation.isPending && (
              <Loader2Icon className="size-4 animate-spin" />
            )}
            Delete
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}

function AgentCard({ agent }: { agent: AgentConfigPublic }) {
  const isPersonal = agent.scope === "personal"

  return (
    <Card className="flex flex-col group">
      <CardHeader className="flex flex-row items-start gap-4 pb-2">
        <Link to="/agent/$agentId" params={{ agentId: agent.id }}>
          <AgentAvatar name={agent.name} size="lg" className="transition-transform group-hover:scale-105" />
        </Link>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <Link
              to="/agent/$agentId"
              params={{ agentId: agent.id }}
              className="hover:underline"
            >
              <CardTitle className="text-lg truncate">{agent.name}</CardTitle>
            </Link>
            {agent.scope && (
              <AgentScopeBadge
                scope={agent.scope as "system" | "personal"}
                className="shrink-0"
              />
            )}
          </div>
          <CardDescription className="font-mono text-xs">
            @{agent.slug}
          </CardDescription>
        </div>
        <Link
          to="/agent/$agentId"
          params={{ agentId: agent.id }}
          className="opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <Button variant="ghost" size="icon" className="size-8">
            <ExternalLinkIcon className="size-4" />
          </Button>
        </Link>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col gap-4">
        {agent.description && (
          <p className="text-sm text-muted-foreground line-clamp-2">
            {agent.description}
          </p>
        )}

        <div className="flex flex-wrap gap-2 mt-auto">
          {agent.participation_mode && (
            <AgentModeBadge
              mode={agent.participation_mode as ParticipationMode}
            />
          )}
          {agent.model_name && (
            <Badge variant="outline" className="font-mono text-xs">
              {agent.model_name.split(":").pop()}
            </Badge>
          )}
          {!agent.is_enabled && (
            <Badge variant="secondary" className="text-muted-foreground">
              Disabled
            </Badge>
          )}
        </div>

        {/* Actions - only show for personal agents */}
        {isPersonal && (
          <div className="flex items-center gap-2 pt-2 border-t">
            <EditAgentDialog agent={agent} className="flex-1" />
            <DeleteAgentButton agent={agent} />
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function AgentsListContent() {
  const { data: agents } = useSuspenseQuery(getAgentsQueryOptions())

  // Separate personal and system agents
  const personalAgents = agents.data.filter((a) => a.scope === "personal")
  const systemAgents = agents.data.filter((a) => a.scope === "system")

  if (agents.data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-muted p-4 mb-4">
          <BotIcon className="size-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">No agents yet</h3>
        <p className="text-muted-foreground mb-4">
          Create your first personal agent to get started
        </p>
        <CreateAgentDialog />
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Personal Agents */}
      {personalAgents.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-4">My Agents</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {personalAgents.map((agent) => (
              <AgentCard key={agent.id} agent={agent} />
            ))}
          </div>
        </section>
      )}

      {/* System Agents */}
      {systemAgents.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-4 text-muted-foreground">
            System Agents
          </h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {systemAgents.map((agent) => (
              <AgentCard key={agent.id} agent={agent} />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}

function AgentsList() {
  return (
    <Suspense fallback={<PendingAgents />}>
      <AgentsListContent />
    </Suspense>
  )
}

function AgentsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Agents</h1>
          <p className="text-muted-foreground">
            Create and manage your personal AI agents
          </p>
        </div>
        <CreateAgentDialog />
      </div>
      <AgentsList />
    </div>
  )
}
