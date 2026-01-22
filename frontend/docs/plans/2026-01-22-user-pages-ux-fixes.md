# User Pages UX Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete the User Pages Revamp by adding missing UX features: block toolbar (delete, reorder, visibility), RelationshipsForm, unsaved changes warning, and dynamic page header.

**Architecture:** Enhance BlockWrapper with a hover toolbar containing action buttons. Each action calls existing hook methods. Add RelationshipsForm following existing form patterns. Use `beforeunload` event for unsaved changes warning.

**Tech Stack:** React, TypeScript, shadcn/ui (AlertDialog, Button, Tooltip), lucide-react icons, react-hook-form + zod

---

## Task 1: Add Block Toolbar to BlockWrapper

**Files:**
- Modify: `frontend/src/components/Page/BlockWrapper.tsx`

**Step 1: Update BlockWrapper with toolbar and extended props**

The BlockWrapper needs to accept new callback props and render a floating toolbar on hover in edit mode.

```tsx
// src/components/Page/BlockWrapper.tsx

import {
  ArrowDown,
  ArrowUp,
  Eye,
  EyeOff,
  Trash2,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"

interface BlockWrapperProps {
  blockId: string
  isEditing: boolean
  isSelected: boolean
  isVisible?: boolean
  isFirst?: boolean
  isLast?: boolean
  onSelect: (blockId: string) => void
  onMoveUp?: (blockId: string) => void
  onMoveDown?: (blockId: string) => void
  onToggleVisibility?: (blockId: string) => void
  onDelete?: (blockId: string) => void
  children: React.ReactNode
  className?: string
}

/**
 * BlockWrapper - Wraps blocks to add click-to-select and toolbar in edit mode
 *
 * In view mode: transparent pass-through (no visual changes)
 * In edit mode: shows hover toolbar with reorder/visibility/delete actions
 * When selected: shows highlight ring
 */
export function BlockWrapper({
  blockId,
  isEditing,
  isSelected,
  isVisible = true,
  isFirst = false,
  isLast = false,
  onSelect,
  onMoveUp,
  onMoveDown,
  onToggleVisibility,
  onDelete,
  children,
  className,
}: BlockWrapperProps) {
  const handleClick = (e: React.MouseEvent) => {
    // Don't select when clicking toolbar buttons
    if ((e.target as HTMLElement).closest('[data-toolbar]')) {
      return
    }
    if (isEditing) {
      onSelect(blockId)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault()
      if (isEditing) {
        onSelect(blockId)
      }
    }
  }

  // View mode: minimal wrapper, hide if not visible
  if (!isEditing) {
    if (!isVisible) return null
    return <div className={className}>{children}</div>
  }

  // Edit mode: interactive wrapper with toolbar
  return (
    <div
      className={cn(
        "group relative rounded-lg transition-all",
        "cursor-pointer",
        // Hover effect in edit mode
        "hover:ring-2 hover:ring-muted-foreground/20",
        // Selected state
        isSelected && "ring-2 ring-primary",
        // Hidden block styling
        !isVisible && "opacity-50",
        className
      )}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      onKeyDown={handleKeyDown}
      aria-pressed={isSelected}
      aria-label="Select block for editing"
    >
      {/* Hover Toolbar */}
      <div
        data-toolbar
        className={cn(
          "absolute -top-3 right-2 z-10",
          "flex items-center gap-1 p-1 rounded-md",
          "bg-background border shadow-sm",
          "opacity-0 group-hover:opacity-100 transition-opacity",
          // Always show when selected
          isSelected && "opacity-100"
        )}
      >
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={() => onMoveUp?.(blockId)}
              disabled={isFirst}
              aria-label="Move block up"
            >
              <ArrowUp className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>Move up</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={() => onMoveDown?.(blockId)}
              disabled={isLast}
              aria-label="Move block down"
            >
              <ArrowDown className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>Move down</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={() => onToggleVisibility?.(blockId)}
              aria-label={isVisible ? "Hide block" : "Show block"}
            >
              {isVisible ? (
                <Eye className="h-4 w-4" />
              ) : (
                <EyeOff className="h-4 w-4" />
              )}
            </Button>
          </TooltipTrigger>
          <TooltipContent>{isVisible ? "Hide" : "Show"}</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 text-destructive hover:text-destructive"
              onClick={() => onDelete?.(blockId)}
              aria-label="Delete block"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>Delete</TooltipContent>
        </Tooltip>
      </div>

      {children}
    </div>
  )
}
```

**Step 2: Verify lint passes**

Run: `cd frontend && npm run lint -- --filter BlockWrapper`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/components/Page/BlockWrapper.tsx
git commit -m "feat(page-editor): add hover toolbar to BlockWrapper with reorder/visibility/delete"
```

---

## Task 2: Wire Up BlockWrapper Actions in PageShell

**Files:**
- Modify: `frontend/src/components/Page/PageShell.tsx`

**Step 1: Add helper functions and pass props to BlockWrapper**

Update PageShell to compute block positions and pass the new callbacks to BlockWrapper.

```tsx
// In PageShell.tsx, update the imports and destructure from usePageEditor:
const {
  blocks,
  isLoading,
  isEditing,
  isDirty,
  isSaving,
  selectedBlockId,
  selectedBlock,
  startEditing,
  cancelEditing,
  save,
  selectBlock,
  updateBlockContent,
  addBlock,
  removeBlock,           // Add this
  reorderBlocks,         // Add this
  toggleBlockVisibility, // Add this
} = usePageEditor(entityType, entityId)

// Add these helper functions before renderBlock:

const handleMoveBlock = (blockId: string, direction: "up" | "down") => {
  if (!blocks) return

  const block = blocks.find((b) => b.id === blockId)
  if (!block) return

  const columnBlocks = blocks
    .filter((b) => b.column === block.column)
    .sort((a, b) => a.order - b.order)

  const currentIndex = columnBlocks.findIndex((b) => b.id === blockId)
  if (currentIndex === -1) return

  const newIndex = direction === "up" ? currentIndex - 1 : currentIndex + 1
  if (newIndex < 0 || newIndex >= columnBlocks.length) return

  // Swap positions in the ordered array
  const newOrder = columnBlocks.map((b) => b.id!)
  ;[newOrder[currentIndex], newOrder[newIndex]] = [newOrder[newIndex], newOrder[currentIndex]]

  reorderBlocks(block.column, newOrder)
}

const getBlockPosition = (blockId: string) => {
  if (!blocks) return { isFirst: true, isLast: true }

  const block = blocks.find((b) => b.id === blockId)
  if (!block) return { isFirst: true, isLast: true }

  const columnBlocks = blocks
    .filter((b) => b.column === block.column)
    .sort((a, b) => a.order - b.order)

  const index = columnBlocks.findIndex((b) => b.id === blockId)
  return {
    isFirst: index === 0,
    isLast: index === columnBlocks.length - 1,
  }
}

// Update the renderBlock function's BlockWrapper:
const renderBlock = (block: TemplateBlock): React.ReactNode => {
  // ... existing config/content extraction ...

  const { isFirst, isLast } = getBlockPosition(block.id ?? "")

  return (
    <BlockWrapper
      blockId={block.id ?? ""}
      isEditing={isEditing}
      isSelected={selectedBlockId === block.id}
      isVisible={block.visibility !== "hidden"}
      isFirst={isFirst}
      isLast={isLast}
      onSelect={selectBlock}
      onMoveUp={(id) => handleMoveBlock(id, "up")}
      onMoveDown={(id) => handleMoveBlock(id, "down")}
      onToggleVisibility={toggleBlockVisibility}
      onDelete={removeBlock}
    >
      {blockContent}
    </BlockWrapper>
  )
}
```

**Step 2: Verify lint passes**

Run: `cd frontend && npm run lint`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/components/Page/PageShell.tsx
git commit -m "feat(page-editor): wire up block toolbar actions in PageShell"
```

---

## Task 3: Add Delete Confirmation Dialog

**Files:**
- Modify: `frontend/src/components/Page/BlockWrapper.tsx`

**Step 1: Add AlertDialog for delete confirmation**

Wrap the delete action in an AlertDialog to prevent accidental deletions.

```tsx
// Add to imports in BlockWrapper.tsx:
import { useState } from "react"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"

// Inside the BlockWrapper component, add state:
const [showDeleteDialog, setShowDeleteDialog] = useState(false)

// Replace the delete button's onClick:
onClick={() => setShowDeleteDialog(true)}

// Add the AlertDialog after the toolbar div, still inside the wrapper:
<AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
  <AlertDialogContent>
    <AlertDialogHeader>
      <AlertDialogTitle>Delete Block</AlertDialogTitle>
      <AlertDialogDescription>
        Are you sure you want to delete this block? This action cannot be undone.
      </AlertDialogDescription>
    </AlertDialogHeader>
    <AlertDialogFooter>
      <AlertDialogCancel>Cancel</AlertDialogCancel>
      <AlertDialogAction
        onClick={() => {
          onDelete?.(blockId)
          setShowDeleteDialog(false)
        }}
        className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
      >
        Delete
      </AlertDialogAction>
    </AlertDialogFooter>
  </AlertDialogContent>
</AlertDialog>
```

**Step 2: Verify lint passes**

Run: `cd frontend && npm run lint`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/components/Page/BlockWrapper.tsx
git commit -m "feat(page-editor): add delete confirmation dialog"
```

---

## Task 4: Create RelationshipsForm

**Files:**
- Create: `frontend/src/components/Page/editor/forms/RelationshipsForm.tsx`
- Modify: `frontend/src/components/Page/editor/forms/index.ts`

**Step 1: Create RelationshipsForm component**

```tsx
// src/components/Page/editor/forms/RelationshipsForm.tsx
import { useEffect, useRef } from "react"
import { useForm, useFieldArray } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Plus, Trash2 } from "lucide-react"
import type {
  RelationshipsContent,
  RelationshipsBlockConfig,
  RelationshipItem,
} from "@/components/Page/blocks"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { entityTypes } from "@/components/Page/registry"

const relationshipItemSchema = z.object({
  id: z.string(),
  typeId: z.string().min(1, "Entity type is required"),
  name: z.string().min(1, "Name is required"),
  avatarUrl: z.string().optional(),
  badges: z.array(z.string()).optional(),
  relationshipTypeId: z.string().min(1, "Relationship type is required"),
})

const schema = z.object({
  items: z.array(relationshipItemSchema),
})

type RelationshipsFormData = z.infer<typeof schema>

// Common relationship types for the dropdown
const relationshipTypeOptions = [
  { value: "friend", label: "Friend" },
  { value: "colleague", label: "Colleague" },
  { value: "mentor", label: "Mentor" },
  { value: "mentee", label: "Mentee" },
  { value: "collaborator", label: "Collaborator" },
  { value: "member", label: "Member" },
  { value: "creator", label: "Creator" },
  { value: "other", label: "Other" },
]

interface RelationshipsFormProps {
  content: RelationshipsContent
  config: RelationshipsBlockConfig
  onSave: (content: RelationshipsContent) => void
  onCancel: () => void
}

function generateId(): string {
  return crypto.randomUUID()
}

export function RelationshipsForm({
  content,
  config: _config,
  onSave,
  onCancel,
}: RelationshipsFormProps) {
  const firstInputRef = useRef<HTMLInputElement>(null)
  const {
    register,
    handleSubmit,
    control,
    setValue,
    watch,
    formState: { errors },
  } = useForm<RelationshipsFormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      items: content.items || [],
    },
  })

  const { fields, append, remove } = useFieldArray({
    control,
    name: "items",
  })

  // Auto-focus first field on mount
  useEffect(() => {
    firstInputRef.current?.focus()
  }, [])

  const handleAddRelationship = () => {
    append({
      id: generateId(),
      typeId: "user",
      name: "",
      avatarUrl: "",
      relationshipTypeId: "friend",
    })
  }

  const onSubmit = (data: RelationshipsFormData) => {
    // Clean up empty optional fields
    const cleanedItems: RelationshipItem[] = data.items.map((item) => ({
      id: item.id,
      typeId: item.typeId,
      name: item.name,
      avatarUrl: item.avatarUrl || undefined,
      badges: item.badges?.length ? item.badges : undefined,
      relationshipTypeId: item.relationshipTypeId,
    }))
    onSave({ items: cleanedItems })
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-4 max-h-[400px] overflow-y-auto">
        {fields.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">
            No relationships added yet. Click the button below to add one.
          </p>
        ) : (
          fields.map((field, index) => (
            <div
              key={field.id}
              className="space-y-3 p-4 border rounded-lg relative"
            >
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="absolute top-2 right-2 h-7 w-7"
                onClick={() => remove(index)}
                aria-label="Remove relationship"
              >
                <Trash2 className="h-4 w-4" />
              </Button>

              <input type="hidden" {...register(`items.${index}.id`)} />

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label htmlFor={`items.${index}.typeId`}>Entity Type</Label>
                  <Select
                    value={watch(`items.${index}.typeId`)}
                    onValueChange={(value) =>
                      setValue(`items.${index}.typeId`, value)
                    }
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select type" />
                    </SelectTrigger>
                    <SelectContent>
                      {entityTypes.map((et) => (
                        <SelectItem key={et.id} value={et.id}>
                          {et.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {errors.items?.[index]?.typeId && (
                    <p className="text-sm text-destructive">
                      {errors.items[index].typeId?.message}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor={`items.${index}.relationshipTypeId`}>
                    Relationship
                  </Label>
                  <Select
                    value={watch(`items.${index}.relationshipTypeId`)}
                    onValueChange={(value) =>
                      setValue(`items.${index}.relationshipTypeId`, value)
                    }
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select relationship" />
                    </SelectTrigger>
                    <SelectContent>
                      {relationshipTypeOptions.map((rt) => (
                        <SelectItem key={rt.value} value={rt.value}>
                          {rt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {errors.items?.[index]?.relationshipTypeId && (
                    <p className="text-sm text-destructive">
                      {errors.items[index].relationshipTypeId?.message}
                    </p>
                  )}
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor={`items.${index}.name`}>
                  Name <span className="text-destructive">*</span>
                </Label>
                <Input
                  id={`items.${index}.name`}
                  {...register(`items.${index}.name`)}
                  ref={index === 0 ? firstInputRef : undefined}
                  placeholder="Entity name"
                  aria-invalid={errors.items?.[index]?.name ? "true" : undefined}
                />
                {errors.items?.[index]?.name && (
                  <p className="text-sm text-destructive">
                    {errors.items[index].name?.message}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor={`items.${index}.avatarUrl`}>
                  Avatar URL (optional)
                </Label>
                <Input
                  id={`items.${index}.avatarUrl`}
                  {...register(`items.${index}.avatarUrl`)}
                  placeholder="https://..."
                />
              </div>
            </div>
          ))
        )}
      </div>

      <Button
        type="button"
        variant="outline"
        onClick={handleAddRelationship}
        className="w-full"
      >
        <Plus className="h-4 w-4 mr-2" />
        Add Relationship
      </Button>

      <div className="flex justify-end gap-2 pt-4">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit">Save</Button>
      </div>
    </form>
  )
}
```

**Step 2: Export from index.ts**

Add to `frontend/src/components/Page/editor/forms/index.ts`:

```ts
export { RelationshipsForm } from "./RelationshipsForm"
```

**Step 3: Verify lint passes**

Run: `cd frontend && npm run lint`
Expected: No errors

**Step 4: Commit**

```bash
git add frontend/src/components/Page/editor/forms/RelationshipsForm.tsx
git add frontend/src/components/Page/editor/forms/index.ts
git commit -m "feat(page-editor): add RelationshipsForm for editing relationship blocks"
```

---

## Task 5: Wire Up RelationshipsForm in BlockEditorSheet

**Files:**
- Modify: `frontend/src/components/Page/editor/BlockEditorSheet.tsx`

**Step 1: Add RelationshipsForm case to the switch statement**

```tsx
// Add to imports:
import type {
  RelationshipsContent,
  RelationshipsBlockConfig,
} from "@/components/Page/blocks"
import { RelationshipsForm } from "./forms"

// Add case in renderForm switch:
case "relationships":
  return (
    <RelationshipsForm
      content={content as RelationshipsContent}
      config={config as RelationshipsBlockConfig}
      onSave={createSaveHandler<RelationshipsContent>(block.id)}
      onCancel={onClose}
    />
  )
```

**Step 2: Verify lint passes**

Run: `cd frontend && npm run lint`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/components/Page/editor/BlockEditorSheet.tsx
git commit -m "feat(page-editor): wire up RelationshipsForm in BlockEditorSheet"
```

---

## Task 6: Add Unsaved Changes Warning

**Files:**
- Modify: `frontend/src/components/Page/PageShell.tsx`

**Step 1: Add beforeunload handler for unsaved changes**

```tsx
// Add useEffect import if not present, then add this effect in PageShell:

import { useEffect } from "react"

// Inside PageShell component, after the usePageEditor hook:
useEffect(() => {
  const handleBeforeUnload = (e: BeforeUnloadEvent) => {
    if (isDirty) {
      e.preventDefault()
      // Modern browsers show a generic message, but we set returnValue for compatibility
      e.returnValue = "You have unsaved changes. Are you sure you want to leave?"
      return e.returnValue
    }
  }

  window.addEventListener("beforeunload", handleBeforeUnload)
  return () => window.removeEventListener("beforeunload", handleBeforeUnload)
}, [isDirty])
```

**Step 2: Verify lint passes**

Run: `cd frontend && npm run lint`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/components/Page/PageShell.tsx
git commit -m "feat(page-editor): add unsaved changes warning on page unload"
```

---

## Task 7: Fix PageHeader Entity Name Display

**Files:**
- Modify: `frontend/src/components/Page/PageShell.tsx`
- Modify: `frontend/src/components/Page/PageHeader.tsx` (if needed)

**Step 1: Check PageHeader props and pass dynamic name**

First, examine what PageHeader expects and update PageShell to compute a display name from the identity block content.

```tsx
// In PageShell.tsx, compute entity name from blocks:

const entityName = useMemo(() => {
  if (!blocks) return "Page"
  const identityBlock = blocks.find((b) => b.type === "identity")
  const name = identityBlock?.content?.name as string | undefined
  return name || "Untitled Page"
}, [blocks])

// Update the PageHeader call:
<PageHeader
  entityTypeId={entityType}
  entityName={entityName}  // Changed from hardcoded "Page"
  // ... rest of props
/>
```

**Step 2: Add useMemo import if not present**

```tsx
import { useEffect, useMemo, useState } from "react"
```

**Step 3: Verify lint passes**

Run: `cd frontend && npm run lint`
Expected: No errors

**Step 4: Commit**

```bash
git add frontend/src/components/Page/PageShell.tsx
git commit -m "feat(page-editor): display dynamic entity name in PageHeader"
```

---

## Verification Checklist

After all tasks:

- [ ] `npm run lint` passes
- [ ] `npm run build` succeeds
- [ ] Manual test: hover over block in edit mode shows toolbar
- [ ] Manual test: click up/down arrows reorders blocks
- [ ] Manual test: click eye icon toggles visibility
- [ ] Manual test: click trash icon shows confirmation, then deletes
- [ ] Manual test: click relationships block opens form
- [ ] Manual test: add relationship, save, see it rendered
- [ ] Manual test: make changes, try to close browser tab, see warning
- [ ] Manual test: page header shows name from identity block
