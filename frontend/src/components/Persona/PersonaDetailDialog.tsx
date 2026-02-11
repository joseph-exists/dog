// src/components/Persona/PersonaDetailDialog.tsx

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import {
  ExternalLinkIcon,
  EyeIcon,
  Globe,
  Loader2Icon,
  PencilIcon,
  Smile,
} from "lucide-react"
import { useState } from "react"

import type { PersonaUpdate } from "@/client"
import { PersonasService } from "@/client"
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
import { Textarea } from "@/components/ui/textarea"
import { showSuccessToast, showErrorToast } from "@/hooks/useCustomToast"

interface PersonaDetailDialogProps {
  personaId: string
  trigger?: React.ReactNode
  className?: string
}

/** Read-only view of persona details */
function PersonaViewContent({
  persona,
}: {
  persona: {
    name: string
    description?: string | null
    long_description?: string | null
    general_domain?: string | null
    specific_domain?: string | null
    general_domain_high?: string | null
    specific_domain_high?: string | null
  }
}) {
  const hasDomains =
    persona.general_domain ||
    persona.specific_domain ||
    persona.general_domain_high ||
    persona.specific_domain_high

  return (
    <div className="space-y-4">
      {persona.description && (
        <div className="space-y-1">
          <p className="text-sm font-medium text-muted-foreground">
            Description
          </p>
          <p className="text-sm">{persona.description}</p>
        </div>
      )}

      {persona.long_description && (
        <div className="space-y-1">
          <p className="text-sm font-medium text-muted-foreground">
            Long Description
          </p>
          <div className="p-3 rounded-md bg-muted text-sm whitespace-pre-wrap max-h-[150px] overflow-y-auto">
            {persona.long_description}
          </div>
        </div>
      )}

      {hasDomains && (
        <div className="space-y-1">
          <p className="text-sm font-medium text-muted-foreground">Domains</p>
          <div className="flex flex-wrap gap-2">
            {persona.general_domain_high && (
              <DomainBadge label={persona.general_domain_high} variant="high" />
            )}
            {persona.specific_domain_high && (
              <DomainBadge
                label={persona.specific_domain_high}
                variant="high"
              />
            )}
            {persona.general_domain && (
              <DomainBadge label={persona.general_domain} variant="general" />
            )}
            {persona.specific_domain && (
              <DomainBadge label={persona.specific_domain} variant="specific" />
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function DomainBadge({
  label,
  variant,
}: {
  label: string
  variant: "high" | "general" | "specific"
}) {
  const variantClasses = {
    high: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300",
    general: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
    specific:
      "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300",
  }

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${variantClasses[variant]}`}
    >
      <Globe className="size-3" />
      {label}
    </span>
  )
}

/** Inline edit form for persona fields */
function PersonaEditForm({
  initial,
  onChange,
}: {
  initial: {
    name: string
    description: string
    general_domain: string
    specific_domain: string
  }
  onChange: (data: {
    name: string
    description: string
    general_domain: string
    specific_domain: string
  }) => void
}) {
  const [name, setName] = useState(initial.name)
  const [description, setDescription] = useState(initial.description)
  const [generalDomain, setGeneralDomain] = useState(initial.general_domain)
  const [specificDomain, setSpecificDomain] = useState(initial.specific_domain)

  const emitChange = (overrides: Partial<typeof initial> = {}) => {
    onChange({
      name,
      description,
      general_domain: generalDomain,
      specific_domain: specificDomain,
      ...overrides,
    })
  }

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="persona-edit-name">
          Name <span className="text-destructive">*</span>
        </Label>
        <Input
          id="persona-edit-name"
          value={name}
          onChange={(e) => {
            setName(e.target.value)
            emitChange({ name: e.target.value })
          }}
          placeholder="Persona name"
          maxLength={100}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="persona-edit-description">Description</Label>
        <Textarea
          id="persona-edit-description"
          value={description}
          onChange={(e) => {
            setDescription(e.target.value)
            emitChange({ description: e.target.value })
          }}
          placeholder="Short description..."
          maxLength={300}
          className="min-h-[80px]"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="persona-edit-general-domain">General Domain</Label>
          <Input
            id="persona-edit-general-domain"
            value={generalDomain}
            onChange={(e) => {
              setGeneralDomain(e.target.value)
              emitChange({ general_domain: e.target.value })
            }}
            placeholder="e.g. Arts"
            maxLength={100}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="persona-edit-specific-domain">Specific Domain</Label>
          <Input
            id="persona-edit-specific-domain"
            value={specificDomain}
            onChange={(e) => {
              setSpecificDomain(e.target.value)
              emitChange({ specific_domain: e.target.value })
            }}
            placeholder="e.g. Fiction"
            maxLength={100}
          />
        </div>
      </div>
    </div>
  )
}

export default function PersonaDetailDialog({
  personaId,
  trigger,
  className,
}: PersonaDetailDialogProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [mode, setMode] = useState<"view" | "edit">("view")
  const [formData, setFormData] = useState<{
    name: string
    description: string
    general_domain: string
    specific_domain: string
  } | null>(null)
  const queryClient = useQueryClient()
  

  const { data: persona, isLoading } = useQuery({
    queryKey: ["persona", personaId],
    queryFn: () => PersonasService.readPersona({ id: personaId }),
    enabled: isOpen,
  })

  const handleOpenChange = (open: boolean) => {
    setIsOpen(open)
    if (!open) {
      setMode("view")
      setFormData(null)
    }
  }

  const mutation = useMutation({
    mutationFn: (data: PersonaUpdate) =>
      PersonasService.updatePersona({ id: personaId, requestBody: data }),
    onSuccess: (updated) => {
      showSuccessToast(`Persona "${updated.name}" updated`)
      setMode("view")
      setFormData(null)
    },
    onError: (err: ApiError) => {
      const message =
        (err.body as { detail?: string })?.detail || "Failed to update persona"
      showErrorToast(message)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["personas"] })
      queryClient.invalidateQueries({ queryKey: ["persona", personaId] })
    },
  })

  const handleSubmit = () => {
    if (!formData || !persona) return

    if (!formData.name.trim()) {
      showErrorToast("Persona name is required")
      return
    }

    // Only send changed fields
    const payload: PersonaUpdate = {}

    if (formData.name.trim() !== persona.name) {
      payload.name = formData.name.trim()
    }
    if (
      (formData.description.trim() || null) !== (persona.description || null)
    ) {
      payload.description = formData.description.trim() || null
    }
    if (
      (formData.general_domain.trim() || null) !==
      (persona.general_domain || null)
    ) {
      payload.general_domain = formData.general_domain.trim() || null
    }
    if (
      (formData.specific_domain.trim() || null) !==
      (persona.specific_domain || null)
    ) {
      payload.specific_domain = formData.specific_domain.trim() || null
    }

    if (Object.keys(payload).length === 0) {
      showErrorToast("No changes to save")
      return
    }

    mutation.mutate(payload)
  }

  const isValid = formData?.name.trim()

  const defaultTrigger = (
    <Button variant="ghost" size="icon" className={className}>
      <EyeIcon className="size-4" />
    </Button>
  )

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>{trigger || defaultTrigger}</DialogTrigger>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        {isLoading || !persona ? (
          <div className="flex items-center justify-center py-8">
            <Loader2Icon className="size-6 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-pink-100 dark:bg-pink-900/30">
                  <Smile className="size-4 text-pink-600 dark:text-pink-300" />
                </div>
                <span className="truncate">{persona.name}</span>
              </DialogTitle>
              <DialogDescription>
                {mode === "view"
                  ? "Persona details and domains"
                  : "Update persona information"}
              </DialogDescription>
            </DialogHeader>

            {mode === "view" ? (
              <PersonaViewContent persona={persona} />
            ) : (
              <PersonaEditForm
                initial={{
                  name: persona.name,
                  description: persona.description ?? "",
                  general_domain: persona.general_domain ?? "",
                  specific_domain: persona.specific_domain ?? "",
                }}
                onChange={setFormData}
              />
            )}

            <DialogFooter>
              {mode === "view" ? (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setMode("edit")}
                  >
                    <PencilIcon className="size-4" />
                    Edit
                  </Button>
                  <Button variant="outline" size="sm" asChild>
                    <Link
                      to="/persona/$personaId"
                      params={{ personaId }}
                      onClick={() => handleOpenChange(false)}
                    >
                      <ExternalLinkIcon className="size-4" />
                      View Page
                    </Link>
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handleOpenChange(false)}
                  >
                    Close
                  </Button>
                </>
              ) : (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setMode("view")
                      setFormData(null)
                    }}
                    disabled={mutation.isPending}
                  >
                    Cancel
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleSubmit}
                    disabled={!isValid || mutation.isPending}
                  >
                    {mutation.isPending && (
                      <Loader2Icon className="size-4 animate-spin" />
                    )}
                    Save Changes
                  </Button>
                </>
              )}
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
