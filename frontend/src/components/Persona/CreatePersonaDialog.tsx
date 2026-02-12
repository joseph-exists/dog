// src/components/Persona/CreatePersonaDialog.tsx

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Loader2Icon, PlusIcon, Smile } from "lucide-react"
import { useState } from "react"

import type { PersonaCreate, PersonaPublic } from "@/client"
import { ArchetypesService, PersonasService } from "@/client"
import type { ApiError } from "@/client/core/ApiError"
import { Button } from "@/components/ui/button"
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"

interface CreatePersonaDialogProps {
  trigger?: React.ReactNode
  onSuccess?: (persona: PersonaPublic) => void
  className?: string
}

export default function CreatePersonaDialog({
  trigger,
  onSuccess,
  className,
}: CreatePersonaDialogProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [generalDomain, setGeneralDomain] = useState("")
  const [specificDomain, setSpecificDomain] = useState("")
  const [archetypeId, setArchetypeId] = useState<string | null>(null)
  const queryClient = useQueryClient()

  const { data: archetypes } = useQuery({
    queryKey: ["archetypes"],
    queryFn: () => ArchetypesService.readArchetypes({ limit: 100 }),
    enabled: isOpen,
  })

  const handleOpenChange = (open: boolean) => {
    setIsOpen(open)
    if (!open) {
      setName("")
      setDescription("")
      setGeneralDomain("")
      setSpecificDomain("")
      setArchetypeId(null)
    }
  }

  const createMutation = useMutation({
    mutationFn: (data: PersonaCreate) =>
      PersonasService.createPersona({ requestBody: data }),
    onSuccess: (created) => {
      showSuccessToast(`Persona "${created.name}" created`)
      handleOpenChange(false)
      onSuccess?.(created)
    },
    onError: (err: ApiError) => {
      const message =
        (err.body as { detail?: string })?.detail || "Failed to create persona"
      showErrorToast(message)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["personas"] })
    },
  })

  const fromArchetypeMutation = useMutation({
    mutationFn: (data: { archetypeId: string; body: PersonaCreate }) =>
      PersonasService.createPersonaFromArchetype({
        archetypeId: data.archetypeId,
        requestBody: data.body,
      }),
    onSuccess: (created) => {
      showSuccessToast(
        `Persona "${created.name}" created from archetype (traits inherited)`,
      )
      handleOpenChange(false)
      onSuccess?.(created)
    },
    onError: (err: ApiError) => {
      const message =
        (err.body as { detail?: string })?.detail ||
        "Failed to create persona from archetype"
      showErrorToast(message)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["personas"] })
    },
  })

  const isPending = createMutation.isPending || fromArchetypeMutation.isPending

  const handleSubmit = () => {
    if (!name.trim()) {
      showErrorToast("Persona name is required")
      return
    }

    const payload: PersonaCreate = {
      name: name.trim(),
      description: description.trim() || null,
      general_domain: generalDomain.trim() || null,
      specific_domain: specificDomain.trim() || null,
    }

    if (archetypeId) {
      fromArchetypeMutation.mutate({ archetypeId, body: payload })
    } else {
      createMutation.mutate(payload)
    }
  }

  const isValid = name.trim().length > 0
  const archetypeList = archetypes?.data ?? []

  const defaultTrigger = (
    <Button className={className}>
      <PlusIcon className="size-4" />
      Create Persona
    </Button>
  )

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>{trigger || defaultTrigger}</DialogTrigger>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Smile className="size-5" />
            Create Persona
          </DialogTitle>
          <DialogDescription>
            Create a new persona with name, description, and domain expertise.
            Optionally start from an archetype to inherit traits and qualities.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          {archetypeList.length > 0 && (
            <div className="space-y-2">
              <Label htmlFor="persona-archetype">
                Start from Archetype{" "}
                <span className="text-muted-foreground text-xs">
                  (optional)
                </span>
              </Label>
              <Select
                value={archetypeId ?? "none"}
                onValueChange={(v) => setArchetypeId(v === "none" ? null : v)}
              >
                <SelectTrigger id="persona-archetype">
                  <SelectValue placeholder="No archetype (blank persona)" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">
                    No archetype (blank persona)
                  </SelectItem>
                  {archetypeList.map((a) => (
                    <SelectItem key={a.id} value={a.id}>
                      {a.name}
                      {a.description && (
                        <span className="text-muted-foreground ml-2 text-xs">
                          — {a.description}
                        </span>
                      )}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {archetypeId && (
                <p className="text-xs text-muted-foreground">
                  Traits and qualities from this archetype will be inherited.
                </p>
              )}
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="persona-name">
              Name <span className="text-destructive">*</span>
            </Label>
            <Input
              id="persona-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Creative Writer"
              maxLength={100}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="persona-description">Description</Label>
            <Textarea
              id="persona-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Short description of this persona..."
              maxLength={300}
              className="min-h-[80px]"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="persona-general-domain">General Domain</Label>
              <Input
                id="persona-general-domain"
                value={generalDomain}
                onChange={(e) => setGeneralDomain(e.target.value)}
                placeholder="e.g. Arts"
                maxLength={100}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="persona-specific-domain">Specific Domain</Label>
              <Input
                id="persona-specific-domain"
                value={specificDomain}
                onChange={(e) => setSpecificDomain(e.target.value)}
                placeholder="e.g. Fiction Writing"
                maxLength={100}
              />
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => handleOpenChange(false)}
            disabled={isPending}
          >
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!isValid || isPending}>
            {isPending && <Loader2Icon className="size-4 animate-spin" />}
            {archetypeId ? "Create from Archetype" : "Create Persona"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
