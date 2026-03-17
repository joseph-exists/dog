import { useMemo, useState } from "react"
import type { SvgAssetCreatePrivate } from "@/client"
import { useCreatePrivateSvg } from "@/hooks/useSvgs"
import { showErrorToast } from "@/hooks/useCustomToast"
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

export function CreateSvgDialog() {
  const createMutation = useCreatePrivateSvg()
  const [open, setOpen] = useState(false)
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [svgMarkup, setSvgMarkup] = useState("")
  const [metadataJson, setMetadataJson] = useState("{}")

  const isValid = useMemo(() => {
    return Boolean(name.trim()) && Boolean(svgMarkup.trim())
  }, [name, svgMarkup])

  const handleCreate = async () => {
    let metadata: Record<string, unknown> = {}
    try {
      const parsed = JSON.parse(metadataJson || "{}")
      if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
        throw new Error("metadata must be a JSON object")
      }
      metadata = parsed as Record<string, unknown>
    } catch (error) {
      showErrorToast(
        error instanceof Error
          ? `Invalid metadata JSON: ${error.message}`
          : "Invalid metadata JSON",
      )
      return
    }

    const payload: SvgAssetCreatePrivate = {
      visibility: "private",
      name: name.trim(),
      description: description.trim() || null,
      svg_markup: svgMarkup,
      metadata_json: metadata,
    }
    await createMutation.mutateAsync(payload)
    setOpen(false)
    setName("")
    setDescription("")
    setSvgMarkup("")
    setMetadataJson("{}")
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>Create SVG</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Create SVG Asset</DialogTitle>
          <DialogDescription>
            Paste SVG markup and optional metadata to create a private library asset.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          <div className="space-y-1.5">
            <Label>Name</Label>
            <Input
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="mist-field-0001"
            />
          </div>
          <div className="space-y-1.5">
            <Label>Description</Label>
            <Input
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Optional context for discoverability"
            />
          </div>
          <div className="space-y-1.5">
            <Label>SVG Markup</Label>
            <Textarea
              value={svgMarkup}
              onChange={(event) => setSvgMarkup(event.target.value)}
              className="min-h-44 font-mono text-xs"
              placeholder='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"></svg>'
            />
          </div>
          <div className="space-y-1.5">
            <Label>Metadata JSON</Label>
            <Textarea
              value={metadataJson}
              onChange={(event) => setMetadataJson(event.target.value)}
              className="min-h-28 font-mono text-xs"
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleCreate}
            disabled={!isValid || createMutation.isPending}
          >
            {createMutation.isPending ? "Creating..." : "Create"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

