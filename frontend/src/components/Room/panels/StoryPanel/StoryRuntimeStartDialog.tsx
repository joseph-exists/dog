/**
 * StoryRuntimeStartDialog
 *
 * Dialog for starting or replacing a room runtime.
 * Handles persona selection and, when needed, creating a new story + room.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { Loader2 } from "lucide-react"
import { type FormEvent, useEffect, useMemo, useState } from "react"
import type { ApiError } from "@/client"
import {
  CatalogService,
  PersonasService,
  StoriesService,
  UserPersonasService,
} from "@/client"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
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
import { showErrorToast, showSuccessToast } from "@/hooks/useCustomToast"
import { RoomRuntimeService } from "@/services/roomRuntimeService"
import { RoomService } from "@/services/roomService"
import { handleError } from "@/utils"

interface StoryRuntimeStartDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  roomTitle: string | null
  roomStoryId: string | null
  isStarting: boolean
  onStartRuntime: (params: {
    userPersonaId: string
    storyVersion?: number | null
  }) => Promise<void>
}

export function StoryRuntimeStartDialog({
  open,
  onOpenChange,
  roomTitle,
  roomStoryId,
  isStarting,
  onStartRuntime,
}: StoryRuntimeStartDialogProps) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [selectedPersonaId, setSelectedPersonaId] = useState<string>("")
  const [storyVersionInput, setStoryVersionInput] = useState<string>("")
  const [newStoryTitle, setNewStoryTitle] = useState<string>(
    roomTitle?.trim() || "Untitled Room Story",
  )

  const { data: personasData, isLoading: isLoadingPersonas } = useQuery({
    queryKey: ["user-personas"],
    queryFn: () => UserPersonasService.readUserPersonas(),
  })

  useEffect(() => {
    if (!selectedPersonaId && personasData?.data?.length) {
      setSelectedPersonaId(personasData.data[0].id)
    }
  }, [personasData, selectedPersonaId])

  const { data: catalogStory } = useQuery({
    queryKey: ["catalog", roomStoryId],
    queryFn: () =>
      CatalogService.readCatalogStory({ storyId: roomStoryId as string }),
    enabled: Boolean(roomStoryId),
  })

  const defaultStoryVersion = useMemo(() => {
    if (!catalogStory) return ""
    return String(
      catalogStory.published_version || catalogStory.current_version,
    )
  }, [catalogStory])

  const { mutateAsync: createStoryAndRoom, isPending: isCreatingRoom } =
    useMutation({
      mutationFn: async () => {
        const story = await StoriesService.createStory({
          requestBody: { title: newStoryTitle.trim() || "Untitled Room Story" },
        })
        const room = await RoomService.createRoom({
          title: roomTitle || story.title,
          story_id: story.id,
        })
        await RoomRuntimeService.startRuntime(room.room_id, {
          user_persona_id: selectedPersonaId,
          story_version: null,
          expected_revision: null,
        })
        return room.room_id
      },
      onSuccess: (newRoomId) => {
        showSuccessToast("Story created. Runtime started in a new room.")
        onOpenChange(false)
        navigate({ to: "/r/$roomId", params: { roomId: newRoomId } })
      },
      onError: (err: ApiError) => {
        handleError.call(showErrorToast, err)
      },
    })

  const { mutateAsync: createBasicPersona, isPending: isCreatingPersona } =
    useMutation({
      mutationFn: async () => {
        const personaName = roomTitle?.trim()
          ? `${roomTitle.trim()} Persona`
          : "Default Persona"
        const persona = await PersonasService.createPersona({
          requestBody: { name: personaName },
        })
        const userPersona = await UserPersonasService.createUserPersona({
          requestBody: {
            persona_id: persona.id,
            nickname: personaName,
          },
        })
        return userPersona.id
      },
      onSuccess: async (userPersonaId) => {
        await queryClient.invalidateQueries({ queryKey: ["user-personas"] })
        setSelectedPersonaId(userPersonaId)
        showSuccessToast("Persona created for this user.")
      },
      onError: (err: ApiError) => {
        handleError.call(showErrorToast, err)
      },
    })

  const canSubmitPersona = Boolean(selectedPersonaId) && !isLoadingPersonas

  const canStartExistingRoom =
    Boolean(roomStoryId) && canSubmitPersona && !isStarting

  const canCreateRoom = !roomStoryId && canSubmitPersona && !isCreatingRoom

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    if (!selectedPersonaId) return

    if (!roomStoryId) {
      await createStoryAndRoom()
      return
    }

    const storyVersion =
      storyVersionInput.trim() !== ""
        ? Number(storyVersionInput)
        : defaultStoryVersion
          ? Number(defaultStoryVersion)
          : null

    await onStartRuntime({
      userPersonaId: selectedPersonaId,
      storyVersion: Number.isNaN(storyVersion as number) ? null : storyVersion,
    })
    showSuccessToast("Story runtime started.")
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Start Story Runtime</DialogTitle>
            <DialogDescription>
              Select a persona to start the shared runtime for this room.
            </DialogDescription>
          </DialogHeader>

          <div className="flex flex-col gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="persona_id">
                Persona <span className="text-destructive">*</span>
              </Label>
              <Select
                value={selectedPersonaId}
                onValueChange={setSelectedPersonaId}
              >
                <SelectTrigger id="persona_id">
                  <SelectValue
                    placeholder={
                      isLoadingPersonas
                        ? "Loading personas..."
                        : "Select a persona"
                    }
                  />
                </SelectTrigger>
                <SelectContent>
                  {(personasData?.data || []).map((persona) => (
                    <SelectItem key={persona.id} value={persona.id}>
                      {persona.nickname || persona.persona_id}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {!isLoadingPersonas && (personasData?.data.length ?? 0) === 0 && (
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">
                    No personas found. Create one to continue.
                  </p>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      void createBasicPersona()
                    }}
                    disabled={isCreatingPersona}
                  >
                    {isCreatingPersona && (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    )}
                    Create basic persona
                  </Button>
                </div>
              )}
            </div>

            {roomStoryId ? (
              <div className="space-y-2">
                <Label htmlFor="story_version">Story Version</Label>
                <Input
                  id="story_version"
                  type="number"
                  min={1}
                  placeholder={defaultStoryVersion || "Latest"}
                  value={storyVersionInput}
                  onChange={(event) => setStoryVersionInput(event.target.value)}
                />
                {catalogStory && (
                  <p className="text-xs text-muted-foreground">
                    Using catalog story: {catalogStory.title}
                  </p>
                )}
              </div>
            ) : (
              <div className="space-y-2">
                <Label htmlFor="story_title">New Story Title</Label>
                <Input
                  id="story_title"
                  value={newStoryTitle}
                  onChange={(event) => setNewStoryTitle(event.target.value)}
                  placeholder="Room story title"
                />
                <p className="text-xs text-muted-foreground">
                  This room has no story linked. A new story and room will be
                  created.
                </p>
              </div>
            )}
          </div>

          <DialogFooter>
            <DialogClose asChild>
              <Button type="button" variant="outline">
                Cancel
              </Button>
            </DialogClose>
            <Button
              type="submit"
              disabled={!canStartExistingRoom && !canCreateRoom}
            >
              {(isStarting || isCreatingRoom) && (
                <Loader2 className="h-4 w-4 animate-spin" />
              )}
              {roomStoryId ? "Start Runtime" : "Create Story + Room"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
