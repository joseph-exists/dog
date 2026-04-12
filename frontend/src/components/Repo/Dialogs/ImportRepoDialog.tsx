import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { FolderPlusIcon, Loader2Icon, PlusIcon } from "lucide-react"
import { useState } from "react"
import type { ApiError } from "@/client/core/ApiError"
import { UserReposService } from "@/client/sdk.gen"
import type { UserRepoProvisionRequest } from "@/client/types.gen"
import { repoQueryKeys } from "@/components/Repo/hooks"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
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
import { Textarea } from "@/components/ui/textarea"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"

interface ImportRepoDialogProps {
  trigger?: React.ReactNode
}

const initialFormState = {
  source_repo_url: "",
  display_name: "",
  slug: "",
  description: "",
  is_private: true,
}

export function ImportRepoDialog({ trigger }: ImportRepoDialogProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [form, setForm] = useState(initialFormState)
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const handleOpenChange = (open: boolean) => {
    setIsOpen(open)
    if (!open) {
      setForm(initialFormState)
    }
  }

  const importMutation = useMutation({
    mutationFn: (requestBody: UserRepoProvisionRequest) =>
      UserReposService.createUserRepo({ requestBody }),
    onSuccess: async (repo) => {
      showSuccessToast(`Repository "${repo.display_name}" queued for import.`)
      await queryClient.invalidateQueries({ queryKey: repoQueryKeys.all })
      handleOpenChange(false)
      navigate({
        to: "/repo/$repoId",
        params: { repoId: repo.id },
      })
    },
    onError: (error: ApiError) => {
      const detail =
        (error.body as { detail?: string | string[] })?.detail ??
        "Repository import failed."
      showErrorToast(Array.isArray(detail) ? detail.join(", ") : detail)
    },
  })

  const handleSubmit = () => {
    const sourceUrl = form.source_repo_url.trim()
    if (!sourceUrl) {
      showErrorToast("Repository URL is required.")
      return
    }

    // if (!sourceUrl.startsWith("https://")) {
    //   showErrorToast("Repository URL must use HTTPS.")
    //   return
    // }

    importMutation.mutate({
      source_repo_url: sourceUrl,
      display_name: form.display_name.trim() || null,
      slug: form.slug.trim() || null,
      description: form.description.trim() || null,
      is_private: form.is_private,
    })
  }

  const defaultTrigger = (
    <Button>
      <PlusIcon className="size-4" />
      Import Repository
    </Button>
  )

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>{trigger || defaultTrigger}</DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FolderPlusIcon className="size-5" />
            Import Repository
          </DialogTitle>
          <DialogDescription>
            Add an external repository to the platform workspace. Import
            runs asynchronously after submission.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-2 md:grid-cols-2">
          <div className="space-y-2 md:col-span-2">
            <Label htmlFor="repo-source-url">
              Source repository URL <span className="text-destructive">*</span>
            </Label>
            <Input
              id="repo-source-url"
              value={form.source_repo_url}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  source_repo_url: event.target.value,
                }))
              }
              placeholder="https://github.com/example/project.git"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="repo-display-name">Display name</Label>
            <Input
              id="repo-display-name"
              value={form.display_name}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  display_name: event.target.value,
                }))
              }
              placeholder="Project name"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="repo-slug">Slug override</Label>
            <Input
              id="repo-slug"
              value={form.slug}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  slug: event.target.value,
                }))
              }
              placeholder="project-name"
            />
          </div>

          <div className="space-y-2 md:col-span-2">
            <Label htmlFor="repo-description">Description</Label>
            <Textarea
              id="repo-description"
              value={form.description}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  description: event.target.value,
                }))
              }
              placeholder="What is this repository for?"
              className="min-h-24"
            />
          </div>

          <label
            htmlFor="repo-private"
            className="flex items-start gap-3 rounded-xl border p-3 md:col-span-2"
          >
            <Checkbox
              id="repo-private"
              checked={form.is_private}
              onCheckedChange={(checked) =>
                setForm((current) => ({
                  ...current,
                  is_private: checked === true,
                }))
              }
            />
            <div className="space-y-1">
              <div className="text-sm font-medium">Keep repository private</div>
              <div className="text-sm text-muted-foreground">
                Privacy is set on the managed platform repo, not the external
                source.
              </div>
            </div>
          </label>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => handleOpenChange(false)}
            disabled={importMutation.isPending}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!form.source_repo_url.trim() || importMutation.isPending}
          >
            {importMutation.isPending && (
              <Loader2Icon className="size-4 animate-spin" />
            )}
            Start Import
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
