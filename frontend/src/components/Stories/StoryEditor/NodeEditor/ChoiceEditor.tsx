/**
 * ChoiceEditor - Dialog for creating/editing story node choices
 *
 * Features:
 * - Choice text input
 * - Target node selector
 * - Requires state conditions (using StateConditionEditor)
 * - Sets state modifications (using StateConditionEditor)
 * - Delete choice
 */

import { zodResolver } from "@hookform/resolvers/zod"
import { Trash2 } from "lucide-react"
import { useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"
import type {
  NodeChoicePublic,
  StoryNodePublic,
  StoryStateVariablePublic,
} from "@/client"
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
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import {
  Dialog,
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
import {
  useCreateChoice,
  useDeleteChoice,
  useUpdateChoice,
} from "@/hooks/stories/useNodeChoices"
import StateConditionEditor from "../../shared/StateConditionEditor"

const choiceSchema = z.object({
  text: z.string().min(1, "Choice text is required"),
  to_node_id: z.string().min(1, "Target node is required"),
})

type ChoiceFormData = z.infer<typeof choiceSchema>

interface ChoiceEditorProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  fromNodeId: string
  choiceId?: string
  choice?: NodeChoicePublic
  availableNodes: StoryNodePublic[]
  storyId: string
  schema?: StoryStateVariablePublic[]
}

const ChoiceEditor = ({
  open,
  onOpenChange,
  fromNodeId,
  choiceId,
  choice,
  availableNodes,
  schema,
}: ChoiceEditorProps) => {
  const isEditing = !!choiceId && !!choice

  // State condition management
  const [requiresState, setRequiresState] = useState<Record<
    string,
    unknown
  > | null>(null)
  const [setsState, setSetsState] = useState<Record<string, unknown> | null>(
    null,
  )
  const [showRequiresState, setShowRequiresState] = useState(false)
  const [showSetsState, setShowSetsState] = useState(false)

  // Mutations
  const createChoice = useCreateChoice()
  const updateChoice = useUpdateChoice(fromNodeId)
  const deleteChoice = useDeleteChoice(fromNodeId)

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<ChoiceFormData>({
    resolver: zodResolver(choiceSchema),
    defaultValues: {
      text: "",
      to_node_id: "",
    },
  })

  const selectedTargetId = watch("to_node_id")

  // Initialize form when editing
  useEffect(() => {
    if (isEditing && choice) {
      reset({
        text: choice.text,
        to_node_id: choice.to_node_id,
      })

      // Initialize requires_state
      if (
        choice.requires_state &&
        Object.keys(choice.requires_state).length > 0
      ) {
        setRequiresState(choice.requires_state as Record<string, unknown>)
        setShowRequiresState(true)
      } else {
        setRequiresState(null)
        setShowRequiresState(false)
      }

      // Initialize sets_state
      if (choice.sets_state && Object.keys(choice.sets_state).length > 0) {
        setSetsState(choice.sets_state as Record<string, unknown>)
        setShowSetsState(true)
      } else {
        setSetsState(null)
        setShowSetsState(false)
      }
    }
  }, [isEditing, choice, reset])

  const onSubmit = async (data: ChoiceFormData) => {
    if (isEditing) {
      await updateChoice.mutateAsync({
        choiceId: choiceId,
        data: {
          text: data.text,
          to_node_id: data.to_node_id,
          requires_state: requiresState,
          sets_state: setsState,
        },
      })
    } else {
      await createChoice.mutateAsync({
        text: data.text,
        from_node_id: fromNodeId,
        to_node_id: data.to_node_id,
        requires_state: requiresState,
        sets_state: setsState,
      })
    }

    handleClose()
  }

  const handleDelete = async () => {
    if (choiceId) {
      await deleteChoice.mutateAsync(choiceId)
      handleClose()
    }
  }

  const handleClose = () => {
    reset({ text: "", to_node_id: "" })
    setRequiresState(null)
    setSetsState(null)
    setShowRequiresState(false)
    setShowSetsState(false)
    onOpenChange(false)
  }

  // Filter out the current node from targets
  const targetNodes = availableNodes.filter((n) => n.id !== fromNodeId)

  // Count conditions for display
  const requiresStateCount = requiresState
    ? Object.keys(requiresState).length
    : 0
  const setsStateCount = setsState ? Object.keys(setsState).length : 0

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {isEditing ? "Edit Choice" : "Create Choice"}
          </DialogTitle>
          <DialogDescription>
            {isEditing
              ? "Modify the choice text and target node"
              : "Add a new choice that leads to another node"}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Choice Text */}
          <div className="space-y-2">
            <Label htmlFor="text">Choice Text</Label>
            <Input
              id="text"
              placeholder="What the player sees..."
              {...register("text")}
            />
            {errors.text && (
              <p className="text-destructive text-sm">{errors.text.message}</p>
            )}
          </div>

          {/* Target Node */}
          <div className="space-y-2">
            <Label htmlFor="to_node_id">Target Node</Label>
            <Select
              value={selectedTargetId}
              onValueChange={(val) => setValue("to_node_id", val)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select target node" />
              </SelectTrigger>
              <SelectContent>
                {targetNodes.map((node) => (
                  <SelectItem key={node.id} value={node.id}>
                    {node.title || "Untitled"}
                    {node.is_end_node && " (End)"}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.to_node_id && (
              <p className="text-destructive text-sm">
                {errors.to_node_id.message}
              </p>
            )}
          </div>

          {/* Requires State Section */}
          <Collapsible
            open={showRequiresState}
            onOpenChange={setShowRequiresState}
          >
            <CollapsibleTrigger asChild>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="w-full justify-between"
              >
                Requires State ({requiresStateCount})
                <span className="text-xs text-muted-foreground">
                  {showRequiresState ? "Hide" : "Show"}
                </span>
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent className="pt-2">
              <div className="p-3 bg-muted/50 rounded-md">
                <StateConditionEditor
                  value={requiresState}
                  onChange={setRequiresState}
                  label="Conditions for this choice to appear"
                  mode="requires"
                  schema={schema}
                />
              </div>
            </CollapsibleContent>
          </Collapsible>

          {/* Sets State Section */}
          <Collapsible open={showSetsState} onOpenChange={setShowSetsState}>
            <CollapsibleTrigger asChild>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="w-full justify-between"
              >
                Sets State ({setsStateCount})
                <span className="text-xs text-muted-foreground">
                  {showSetsState ? "Hide" : "Show"}
                </span>
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent className="pt-2">
              <div className="p-3 bg-muted/50 rounded-md">
                <StateConditionEditor
                  value={setsState}
                  onChange={setSetsState}
                  label="State changes when this choice is selected"
                  mode="sets"
                  schema={schema}
                />
              </div>
            </CollapsibleContent>
          </Collapsible>

          <DialogFooter className="gap-2">
            {isEditing && (
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button type="button" variant="destructive" size="sm">
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Delete Choice</AlertDialogTitle>
                    <AlertDialogDescription>
                      Are you sure you want to delete this choice? This action
                      cannot be undone.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction onClick={handleDelete}>
                      Delete
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            )}
            <div className="flex-1" />
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting
                ? "Saving..."
                : isEditing
                  ? "Save Changes"
                  : "Create Choice"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default ChoiceEditor
