/**
 * My Agents Page
 *
 * Dashboard for managing personal agents.
 * Users can create, edit, and delete their agents.
 */

import {
  useMutation,
  useQueryClient,
  useSuspenseQuery,
} from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { BotIcon, Loader2Icon, TrashIcon } from "lucide-react"
import { Suspense, useState } from "react"

import type { ApiError } from "@/client/core/ApiError"
import AgentCard from "@/components/Agents/Display/AgentCard"
import AgentDetailDialog from "@/components/Agents/Dialogs/AgentDetailDialog"
import CreateAgentDialog from "@/components/Agents/Dialogs/CreateAgentDialog"
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
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import useCustomToast from "@/hooks/useCustomToast"
import { AgentsService } from "@/client/sdk.gen"
import type { UserAgentConfigPublic } from "@/client/types.gen"

function getAgentsQueryOptions() {
  return {
    queryFn: () => AgentsService.listAgents(),
    queryKey: ["agents"],
  }
}

export const Route = createFileRoute("/_layout/agents")({
  component: AgentsPage,
  head: () => ({
    meta: [
      {
        title: "My Agents",
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

function DeleteAgentButton({ agent }: { agent: UserAgentConfigPublic }) {
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

function AgentCardItem({ agent }: { agent: UserAgentConfigPublic }) {
  const isPersonal = agent.scope === "personal"

  return (
    <AgentCard
      id={agent.id}
      name={agent.name ?? "Agent"}
      slug={agent.slug ?? ""}
      href={`/agent/${agent.id}`}
      description={agent.description ?? ""}
      scope={(agent.scope ?? "system") as "system" | "personal"}
      participationMode={(agent.participation_mode ?? "on_mention") as any}
      isEnabled={!!agent.is_enabled}
      modelName={agent.model_name ?? ""}
      action={
        <div className="flex items-center gap-1">
          <AgentDetailDialog agentId={agent.id} className="size-7" />
          {isPersonal && <DeleteAgentButton agent={agent} />}
        </div>
      }
    />
  )
}

function AgentsListContent() {
  const { data } = useSuspenseQuery(getAgentsQueryOptions())
  const allAgents: UserAgentConfigPublic[] = data.data || []
  const personalAgents = allAgents.filter((a) => a.scope === "personal")
  const systemAgents = allAgents.filter((a) => a.scope === "system")

  if (allAgents.length === 0) {
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
              <AgentCardItem key={agent.id} agent={agent} />
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
              <AgentCardItem key={agent.id} agent={agent} />
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
