import {
  closestCenter,
  DndContext,
  type DragEndEvent,
  KeyboardSensor,
  MouseSensor,
  TouchSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core"
import {
  SortableContext,
  arrayMove,
  horizontalListSortingStrategy,
  sortableKeyboardCoordinates,
  useSortable,
} from "@dnd-kit/sortable"
import { CSS } from "@dnd-kit/utilities"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  Loader2,
  Pin,
  PinOff,
  RefreshCcw,
  Search,
  Sparkles,
  Star,
} from "lucide-react"
import { useEffect, useMemo, useState } from "react"
import { LlmCatalogService } from "@/client/sdk.gen"
import type { LLMModelPublic } from "@/client/types.gen"
import { BlockContainer } from "@/components/Page/primitives"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import { PinnedModelChip } from "./PinnedModelChip"

type ModelWithPin = LLMModelPublic & {
  is_pinned?: boolean
  pin_sort_order?: number | null
}

interface ModelPinListProps {
  providerId: string
  providerName: string
  shouldHighlightPins?: boolean
}

type ModelFilter = "all" | "pinned" | "default" | "vision"

function normalizeModelResponse(value: unknown): ModelWithPin[] {
  if (
    value &&
    typeof value === "object" &&
    "data" in value &&
    Array.isArray((value as { data?: unknown }).data)
  ) {
    return (value as { data: ModelWithPin[] }).data
  }

  return []
}

function SortablePinnedModelChip({ model }: { model: ModelWithPin }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({
      id: model.id,
    })

  return (
    <div
      ref={setNodeRef}
      style={{
        transform: CSS.Transform.toString(transform),
        transition,
      }}
    >
      <PinnedModelChip
        model={model}
        dragHandleProps={{
          ...attributes,
          ...listeners,
        }}
        isDragging={isDragging}
      />
    </div>
  )
}

export function ModelPinList({
  providerId,
  providerName,
  shouldHighlightPins = false,
}: ModelPinListProps) {
  const queryClient = useQueryClient()
  const [pinnedOrder, setPinnedOrder] = useState<ModelWithPin[]>([])
  const [searchTerm, setSearchTerm] = useState("")
  const [activeFilter, setActiveFilter] = useState<ModelFilter>(
    shouldHighlightPins ? "pinned" : "all",
  )
  const sensors = useSensors(
    useSensor(MouseSensor),
    useSensor(TouchSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    }),
  )
  const modelsQuery = useQuery({
    queryKey: ["llm-catalog", "models-for-uap", providerId],
    queryFn: async () =>
      normalizeModelResponse(
        await LlmCatalogService.listModelsForUap({
          userAccessProviderId: providerId,
          includePinStatus: true,
          limit: 1000,
        }),
      ),
    enabled: Boolean(providerId),
  })

  const pinMutation = useMutation({
    mutationFn: (modelId: string) =>
      LlmCatalogService.pinModel({
        requestBody: {
          llm_model_id: modelId,
        },
      }),
    onSuccess: () => {
      showSuccessToast("Model pinned")
      queryClient.invalidateQueries({
        queryKey: ["llm-catalog", "models-for-uap", providerId],
      })
    },
    onError: handleError.bind(showErrorToast),
  })

  const unpinMutation = useMutation({
    mutationFn: (modelId: string) =>
      LlmCatalogService.unpinModel({
        llmModelId: modelId,
      }),
    onSuccess: () => {
      showSuccessToast("Model unpinned")
      queryClient.invalidateQueries({
        queryKey: ["llm-catalog", "models-for-uap", providerId],
      })
    },
    onError: handleError.bind(showErrorToast),
  })

  const models = modelsQuery.data ?? []
  const pinnedModels = useMemo(
    () =>
      models
        .filter((model) => model.is_pinned)
        .sort((a, b) => (a.pin_sort_order ?? 0) - (b.pin_sort_order ?? 0)),
    [models],
  )

  useEffect(() => {
    setPinnedOrder(pinnedModels)
  }, [pinnedModels])

  useEffect(() => {
    if (shouldHighlightPins) {
      setActiveFilter("pinned")
    }
  }, [shouldHighlightPins])

  const reorderMutation = useMutation({
    mutationFn: (orderedModels: ModelWithPin[]) =>
      LlmCatalogService.reorderPinnedModels({
        requestBody: {
          order: orderedModels.map((model, index) => ({
            llm_model_id: model.id,
            sort_order: index,
          })),
        },
      }),
    onSuccess: () => {
      showSuccessToast("Pinned model order saved")
      queryClient.invalidateQueries({
        queryKey: ["llm-catalog", "models-for-uap", providerId],
      })
    },
    onError: (
      error: Error,
      _orderedModels,
      context: { previousOrder: ModelWithPin[] } | undefined,
    ) => {
      if (context?.previousOrder) {
        setPinnedOrder(context.previousOrder)
      }
      showErrorToast(error.message || "Failed to save pinned order")
    },
    onMutate: async (orderedModels) => {
      const previousOrder = pinnedOrder
      setPinnedOrder(orderedModels)
      return { previousOrder }
    },
  })

  function handlePinnedDragEnd(event: DragEndEvent) {
    const { active, over } = event
    if (!active || !over || active.id === over.id) {
      return
    }

    setPinnedOrder((current) => {
      const oldIndex = current.findIndex((model) => model.id === active.id)
      const newIndex = current.findIndex((model) => model.id === over.id)
      if (oldIndex < 0 || newIndex < 0) {
        return current
      }

      const nextOrder = arrayMove(current, oldIndex, newIndex)
      reorderMutation.mutate(nextOrder)
      return nextOrder
    })
  }

  const filteredModels = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase()

    return models.filter((model) => {
      if (activeFilter === "pinned" && !model.is_pinned) {
        return false
      }
      if (activeFilter === "default" && !model.is_default) {
        return false
      }
      if (activeFilter === "vision" && !model.has_vision) {
        return false
      }
      if (!normalizedSearch) {
        return true
      }

      return [model.display_name, model.model_id]
        .join(" ")
        .toLowerCase()
        .includes(normalizedSearch)
    })
  }, [activeFilter, models, searchTerm])

  const summary = useMemo(
    () => ({
      total: models.length,
      pinned: models.filter((model) => model.is_pinned).length,
      defaults: models.filter((model) => model.is_default).length,
      vision: models.filter((model) => model.has_vision).length,
    }),
    [models],
  )

  return (
    <BlockContainer
      title="Available models"
      subtitle={`Models discovered for ${providerName}`}
      variant="card"
      density="default"
      headerActions={
        <Button
          variant="outline"
          size="sm"
          onClick={() => modelsQuery.refetch()}
          disabled={modelsQuery.isFetching}
        >
          {modelsQuery.isFetching ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <RefreshCcw className="h-3.5 w-3.5" />
          )}
          Refresh
        </Button>
      }
      bodyClassName="space-y-4"
    >
      <div className="flex flex-wrap gap-2">
        <Badge variant="secondary">{summary.total} total</Badge>
        <Badge variant="outline">{summary.pinned} pinned</Badge>
        <Badge variant="outline">{summary.defaults} defaults</Badge>
        <Badge variant="outline">{summary.vision} vision-ready</Badge>
      </div>

      {pinnedOrder.length > 0 ? (
        <div className="space-y-2">
          <p className="text-xs text-muted-foreground">
            Drag favorites into the order you want surfaced first.
          </p>
          <DndContext
            collisionDetection={closestCenter}
            onDragEnd={handlePinnedDragEnd}
            sensors={sensors}
          >
            <SortableContext
              items={pinnedOrder.map((model) => model.id)}
              strategy={horizontalListSortingStrategy}
            >
              <div className="flex flex-wrap gap-2">
                {pinnedOrder.map((model) => (
                  <SortablePinnedModelChip key={model.id} model={model} />
                ))}
              </div>
            </SortableContext>
          </DndContext>
          {reorderMutation.isPending ? (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Saving pinned order...
            </div>
          ) : null}
        </div>
      ) : (
        <div className="rounded-lg border border-dashed px-4 py-3 text-sm text-muted-foreground">
          No favorites pinned yet.
        </div>
      )}

      {modelsQuery.isLoading ? (
        <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Loading models...
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex flex-col gap-3 rounded-xl border bg-muted/20 p-3">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                placeholder="Search models by name or identifier"
                className="pl-9"
              />
            </div>
            <div className="flex flex-wrap gap-2">
              {(
                [
                  { key: "all", label: "All" },
                  { key: "pinned", label: "Pinned" },
                  { key: "default", label: "Default" },
                  { key: "vision", label: "Vision" },
                ] as Array<{ key: ModelFilter; label: string }>
              ).map((filter) => (
                <Button
                  key={filter.key}
                  variant={activeFilter === filter.key ? "secondary" : "outline"}
                  size="sm"
                  onClick={() => setActiveFilter(filter.key)}
                >
                  {filter.label}
                </Button>
              ))}
            </div>
          </div>

          {filteredModels.length === 0 ? (
            <div className="rounded-lg border border-dashed px-4 py-8 text-center text-sm text-muted-foreground">
              No models match the current filters.
            </div>
          ) : null}

          {filteredModels.map((model) => {
            const isPinned = Boolean(model.is_pinned)
            const isPending =
              pinMutation.isPending ||
              unpinMutation.isPending ||
              reorderMutation.isPending

            return (
              <div
                key={model.id}
                className={`flex items-center justify-between gap-3 rounded-xl border px-4 py-3 ${
                  shouldHighlightPins && !isPinned
                    ? "border-primary/30 bg-primary/5"
                    : "bg-background"
                }`}
              >
                <div className="min-w-0 space-y-1">
                  <div className="flex items-center gap-2">
                    <p className="truncate text-sm font-medium">
                      {model.display_name}
                    </p>
                    {isPinned ? (
                      <Badge variant="secondary" className="text-[10px]">
                        Pinned
                      </Badge>
                    ) : null}
                    {model.is_default ? (
                      <Star className="h-3.5 w-3.5 text-amber-500" />
                    ) : null}
                    {model.has_vision ? (
                      <Sparkles className="h-3.5 w-3.5 text-sky-500" />
                    ) : null}
                  </div>
                  <p className="truncate font-mono text-[11px] text-muted-foreground">
                    {model.model_id}
                  </p>
                </div>
                <Button
                  variant={isPinned ? "secondary" : "outline"}
                  size="sm"
                  disabled={isPending}
                  onClick={() =>
                    isPinned
                      ? unpinMutation.mutate(model.id)
                      : pinMutation.mutate(model.id)
                  }
                >
                  {isPinned ? (
                    <>
                      <PinOff className="h-3.5 w-3.5" />
                      Unpin
                    </>
                  ) : (
                    <>
                      <Pin className="h-3.5 w-3.5" />
                      Pin
                    </>
                  )}
                </Button>
              </div>
            )
          })}
        </div>
      )}
    </BlockContainer>
  )
}
