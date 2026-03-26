import { ArrowDown, ArrowUp, Eye, EyeOff, LayoutPanelLeft } from "lucide-react"
import { useEffect, useMemo, useState } from "react"
import {
  InteractivePreview,
  type PreviewPanel,
} from "@/components/Page/InteractivePreview"
import type { PanelProminence } from "@/components/Page/registry/panelTypes"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { useIsMobile } from "@/hooks/use-mobile"
import { cn } from "@/lib/utils"
import type { DemoPanelLayoutItem } from "./demoPanelLayoutCustomization"

interface DemoPanelLayoutDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  items: DemoPanelLayoutItem[]
  onApply: (items: DemoPanelLayoutItem[]) => void
  onReset: () => void
  canReset: boolean
}

function moveItem(
  items: DemoPanelLayoutItem[],
  panelId: string,
  direction: -1 | 1,
): DemoPanelLayoutItem[] {
  const index = items.findIndex((item) => item.id === panelId)
  if (index === -1) return items
  const targetIndex = index + direction
  if (targetIndex < 0 || targetIndex >= items.length) return items
  const next = [...items]
  const [moved] = next.splice(index, 1)
  next.splice(targetIndex, 0, moved)
  return next
}

function updateItem(
  items: DemoPanelLayoutItem[],
  panelId: string,
  mutate: (item: DemoPanelLayoutItem) => DemoPanelLayoutItem,
): DemoPanelLayoutItem[] {
  return items.map((item) => (item.id === panelId ? mutate(item) : item))
}

function groupVisibleItemsFirst(
  items: DemoPanelLayoutItem[],
): DemoPanelLayoutItem[] {
  return [
    ...items.filter((item) => !item.hidden),
    ...items.filter((item) => item.hidden),
  ]
}

function LayoutEditorBody({
  items,
  onChange,
}: {
  items: DemoPanelLayoutItem[]
  onChange: (items: DemoPanelLayoutItem[]) => void
}) {
  const visibleItems = items.filter((item) => !item.hidden)
  const hiddenItems = items.filter((item) => item.hidden)
  const previewPanels = useMemo<PreviewPanel[]>(
    () =>
      visibleItems.map((item) => ({
        id: item.id,
        kind: item.kind,
        prominence: item.prominence,
      })),
    [visibleItems],
  )

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h4 className="text-sm font-medium">Visible Panels</h4>
        <p className="text-sm text-muted-foreground">
          Reorder visible panels by dragging. Use prominence to move a panel
          between the main workspace and the auxiliary stack.
        </p>
        <div className="rounded-lg border bg-muted/20 p-4">
          <InteractivePreview
            panels={previewPanels}
            onReorder={(panels) => {
              const panelIds = panels.map((panel) => panel.id)
              const reorderedVisible = panelIds
                .map((panelId) =>
                  visibleItems.find((item) => item.id === panelId),
                )
                .filter((item): item is DemoPanelLayoutItem => Boolean(item))
              onChange([...reorderedVisible, ...hiddenItems])
            }}
            onRemove={(panelId) =>
              onChange(
                groupVisibleItemsFirst(
                  updateItem(items, panelId, (item) => ({
                    ...item,
                    hidden: true,
                  })),
                ),
              )
            }
          />
        </div>
      </div>

      <div className="space-y-3">
        <h4 className="text-sm font-medium">Panel Settings</h4>
        <div className="space-y-2">
          {visibleItems.map((item, index) => (
            <div
              key={item.id}
              className="flex flex-col gap-3 rounded-lg border p-3 sm:flex-row sm:items-center"
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="truncate text-sm font-medium">
                    {item.title}
                  </span>
                  <Badge variant="secondary" className="text-[10px] uppercase">
                    {item.kind}
                  </Badge>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <Select
                  value={item.prominence}
                  onValueChange={(value: PanelProminence) =>
                    onChange(
                      groupVisibleItemsFirst(
                        updateItem(items, item.id, (current) => ({
                          ...current,
                          prominence: value,
                        })),
                      ),
                    )
                  }
                >
                  <SelectTrigger className="h-8 w-[140px]">
                    <SelectValue placeholder="Prominence" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="primary">Primary</SelectItem>
                    <SelectItem value="auxiliary">Auxiliary</SelectItem>
                  </SelectContent>
                </Select>

                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => onChange(moveItem(items, item.id, -1))}
                  disabled={index === 0}
                >
                  <ArrowUp className="h-4 w-4" />
                  <span className="sr-only">Move up</span>
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => onChange(moveItem(items, item.id, 1))}
                  disabled={index === visibleItems.length - 1}
                >
                  <ArrowDown className="h-4 w-4" />
                  <span className="sr-only">Move down</span>
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    onChange(
                      groupVisibleItemsFirst(
                        updateItem(items, item.id, (current) => ({
                          ...current,
                          hidden: true,
                        })),
                      ),
                    )
                  }
                >
                  <EyeOff className="mr-2 h-4 w-4" />
                  Hide
                </Button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="space-y-3">
        <h4 className="text-sm font-medium">Hidden Panels</h4>
        {hiddenItems.length === 0 ? (
          <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
            All authored panels are visible.
          </div>
        ) : (
          <div className="space-y-2">
            {hiddenItems.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between rounded-lg border border-dashed p-3"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="truncate text-sm font-medium">
                      {item.title}
                    </span>
                    <Badge variant="outline" className="text-[10px] uppercase">
                      {item.kind}
                    </Badge>
                  </div>
                </div>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    onChange(
                      groupVisibleItemsFirst(
                        updateItem(items, item.id, (current) => ({
                          ...current,
                          hidden: false,
                        })),
                      ),
                    )
                  }
                >
                  <Eye className="mr-2 h-4 w-4" />
                  Show
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export function DemoPanelLayoutDialog({
  open,
  onOpenChange,
  items,
  onApply,
  onReset,
  canReset,
}: DemoPanelLayoutDialogProps) {
  const isMobile = useIsMobile()
  const [draftItems, setDraftItems] = useState(items)

  useEffect(() => {
    if (!open) return
    setDraftItems(items)
  }, [items, open])

  const content = (
    <>
      <div
        className={cn(
          "overflow-y-auto px-1",
          isMobile ? "max-h-[65vh]" : "max-h-[70vh]",
        )}
      >
        <LayoutEditorBody items={draftItems} onChange={setDraftItems} />
      </div>
      <div className="flex items-center justify-between gap-2">
        <Button
          type="button"
          variant="ghost"
          onClick={onReset}
          disabled={!canReset}
        >
          Reset to Demo Default
        </Button>
        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
          >
            Cancel
          </Button>
          <Button type="button" onClick={() => onApply(draftItems)}>
            Apply Layout
          </Button>
        </div>
      </div>
    </>
  )

  if (isMobile) {
    return (
      <Sheet open={open} onOpenChange={onOpenChange}>
        <SheetContent side="bottom" className="h-[85vh]">
          <SheetHeader>
            <SheetTitle className="flex items-center gap-2">
              <LayoutPanelLeft className="h-4 w-4" />
              Customize Layout
            </SheetTitle>
            <SheetDescription>
              Manage the visible demo panels for your current view. Changes stay
              local to this demo on this device.
            </SheetDescription>
          </SheetHeader>
          <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-hidden px-4 pb-2">
            {content}
          </div>
        </SheetContent>
      </Sheet>
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-4xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <LayoutPanelLeft className="h-4 w-4" />
            Customize Layout
          </DialogTitle>
          <DialogDescription>
            Manage the visible demo panels for your current view. Changes stay
            local to this demo on this device.
          </DialogDescription>
        </DialogHeader>
        <div className="flex min-h-0 flex-col gap-4">{content}</div>
      </DialogContent>
    </Dialog>
  )
}
