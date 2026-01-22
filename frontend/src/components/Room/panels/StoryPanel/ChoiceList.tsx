/**
 * ChoiceList
 *
 * Renders available choices with loading and disable states.
 */

import type { ChoiceViewModel } from "@/services/roomRuntimeService"
import { ChoiceItem } from "./ChoiceItem"

interface ChoiceListProps {
  choices: ChoiceViewModel[]
  isDisabled?: boolean
  pendingChoiceId?: string | null
  onSelect: (choice: ChoiceViewModel) => void
}

export function ChoiceList({
  choices,
  isDisabled = false,
  pendingChoiceId = null,
  onSelect,
}: ChoiceListProps) {
  if (choices.length === 0) {
    return (
      <div className="rounded-md border border-dashed p-4 text-sm text-muted-foreground">
        No available choices.
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      {choices.map((choice) => (
        <ChoiceItem
          key={choice.id}
          choice={choice}
          isAvailable={!isDisabled && choice.isAvailable}
          isLoading={pendingChoiceId === choice.id}
          onSelect={onSelect}
          variant="button"
        />
      ))}
    </div>
  )
}
