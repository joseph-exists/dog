import { createFileRoute, Link } from "@tanstack/react-router"
import { FolderKanban, Plus, Sparkles } from "lucide-react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import { Textarea } from "@/components/ui/textarea"
import { useCreateProject, useProjectsList } from "@/hooks/useProjects"

export const Route = createFileRoute("/_layout/projects")({
  component: ProjectsPage,
  head: () => ({
    meta: [{ title: "Projects" }],
  }),
})

function ProjectsPage() {
  const { data, isLoading, error } = useProjectsList()
  const createProject = useCreateProject()
  const [open, setOpen] = useState(false)
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")

  const projects = data ?? []

  const submitCreate = async () => {
    if (!name.trim()) return
    await createProject.mutateAsync({
      name: name.trim(),
      description: description.trim() || null,
    })
    setName("")
    setDescription("")
    setOpen(false)
  }

  return (
    <div className="container mx-auto max-w-7xl py-8 space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Projects</h1>
          <p className="text-sm text-muted-foreground">
            Organize shared stories, demos, rooms, repos, and collaborators.
          </p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              New Project
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Project</DialogTitle>
              <DialogDescription>
                Start a new collaboration container and add resources afterward.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-3 py-2">
              <div className="space-y-1.5">
                <Label htmlFor="project-name">Name</Label>
                <Input
                  id="project-name"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  placeholder="Platform Alpha"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="project-description">Description</Label>
                <Textarea
                  id="project-description"
                  value={description}
                  onChange={(event) => setDescription(event.target.value)}
                  placeholder="Optional context and goals for this project"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={submitCreate}
                disabled={createProject.isPending || !name.trim()}
              >
                Create
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          <Skeleton className="h-36 rounded-xl" />
          <Skeleton className="h-36 rounded-xl" />
          <Skeleton className="h-36 rounded-xl" />
        </div>
      ) : null}

      {error ? (
        <Card>
          <CardHeader>
            <CardTitle>Failed to load projects</CardTitle>
            <CardDescription>{error.message}</CardDescription>
          </CardHeader>
        </Card>
      ) : null}

      {!isLoading && !error && projects.length === 0 ? (
        <Card>
          <CardHeader className="items-center text-center">
            <div className="rounded-full bg-muted p-3">
              <FolderKanban className="h-6 w-6 text-muted-foreground" />
            </div>
            <CardTitle>No projects yet</CardTitle>
            <CardDescription>
              Create your first project to start managing associations across
              stories, demos, rooms, and repos.
            </CardDescription>
          </CardHeader>
        </Card>
      ) : null}

      {!isLoading && !error && projects.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <Link
              key={project.id}
              to="/project/$projectId"
              params={{ projectId: project.id }}
              className="block"
            >
              <Card className="h-full transition-colors hover:border-primary/50">
                <CardHeader>
                  <CardTitle className="line-clamp-1">{project.name}</CardTitle>
                  <CardDescription className="line-clamp-2">
                    {project.description || "No description"}
                  </CardDescription>
                </CardHeader>
                <CardContent className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>{new Date(project.updated_at).toLocaleString()}</span>
                  <span className="inline-flex items-center gap-1">
                    <Sparkles className="h-3 w-3" />
                    Open
                  </span>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      ) : null}
    </div>
  )
}
