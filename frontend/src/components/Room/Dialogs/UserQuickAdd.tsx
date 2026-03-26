import { Loader2Icon, PlusIcon } from "lucide-react"
import { useState } from "react"
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

interface UserQuickAddProps {
  onAdd: (userId: string) => Promise<void> | void
  buttonVariant?: "default" | "outline" | "ghost"
  buttonSize?: "default" | "sm" | "icon"
  disabled?: boolean
  className?: string
}

export default function UserQuickAdd({
  onAdd,
  buttonVariant = "outline",
  buttonSize = "sm",
  disabled = false,
  className,
}: UserQuickAddProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [userId, setUserId] = useState("")
  const [isAdding, setIsAdding] = useState(false)

  const isValid = userId.trim().length > 0

  const handleOpenChange = (open: boolean) => {
    setIsOpen(open)
    if (!open) {
      setUserId("")
      setIsAdding(false)
    }
  }

  const handleAdd = async () => {
    if (!isValid || isAdding) return
    setIsAdding(true)
    try {
      await onAdd(userId.trim())
      handleOpenChange(false)
    } finally {
      setIsAdding(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button
          variant={buttonVariant}
          size={buttonSize}
          disabled={disabled}
          className={className}
        >
          <PlusIcon className="size-4" />
          {buttonSize !== "icon" && <span>Add User</span>}
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add User to Room</DialogTitle>
          <DialogDescription>
            Enter the user ID to invite them as a room participant.
          </DialogDescription>
        </DialogHeader>

        <form
          onSubmit={(event) => {
            event.preventDefault()
            void handleAdd()
          }}
          className="space-y-4"
        >
          <div className="space-y-2">
            <Label htmlFor="user-participant-id">User ID</Label>
            <Input
              id="user-participant-id"
              placeholder="00000000-0000-0000-0000-000000000000"
              value={userId}
              onChange={(event) => setUserId(event.target.value)}
              autoComplete="off"
            />
          </div>

          <DialogFooter>
            <Button type="submit" disabled={!isValid || isAdding}>
              {isAdding ? (
                <Loader2Icon className="size-4 animate-spin" />
              ) : null}
              Add User
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
