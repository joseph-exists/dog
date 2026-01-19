# Component, Hook, and Service Patterns

## Table of Contents
- [Component Structure](#component-structure)
- [TanStack Query Hooks](#tanstack-query-hooks)
- [Service Layer](#service-layer)
- [Forms](#forms)
- [Layout Patterns](#layout-patterns)
- [Common UI Patterns](#common-ui-patterns)

---

## Component Structure

```tsx
import { cn } from "@/lib/utils"

interface ComponentProps {
  className?: string
  children?: React.ReactNode
}

export function Component({ className, children }: ComponentProps) {
  return (
    <div className={cn("base-classes", className)}>
      {children}
    </div>
  )
}
```

---

## TanStack Query Hooks

### Basic Hook Pattern

```tsx
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { SomeService } from "@/client"
import { handleError } from "@/utils"
import useCustomToast from "./useCustomToast"

export function useSomething(id: string) {
  const queryClient = useQueryClient()
  const { showErrorToast } = useCustomToast()

  const { data, isLoading, error } = useQuery({
    queryKey: ["something", id],
    queryFn: () => SomeService.getSomething({ id }),
    enabled: !!id,
  })

  const updateMutation = useMutation({
    mutationFn: (data: UpdateData) =>
      SomeService.updateSomething({ id, requestBody: data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["something", id] })
    },
    onError: (error) => handleError(error, showErrorToast),
  })

  return {
    data,
    isLoading,
    error,
    update: updateMutation.mutate,
    isUpdating: updateMutation.isPending,
  }
}
```

### Query Key Conventions

```tsx
["rooms"]                         // All rooms
["rooms", roomId]                 // Single room
["rooms", roomId, "messages"]     // Room messages
["rooms", roomId, "participants"] // Room participants
["stories"]                       // All stories
["stories", storyId]              // Single story
["stories", storyId, "nodes"]     // Story nodes
["currentUser"]                   // Auth user
```

---

## Service Layer

Services transform backend DTOs to frontend ViewModels:

```tsx
// services/featureService.ts
import { FeatureService as ApiService, type FeaturePublic } from "@/client"

// ViewModel - optimized for UI
export interface FeatureViewModel {
  id: string
  title: string
  createdAt: Date  // Parsed from ISO string
}

// Transform function
function transformFeature(dto: FeaturePublic): FeatureViewModel {
  return {
    id: dto.id,
    title: dto.title ?? "Untitled",
    createdAt: new Date(dto.created_at),
  }
}

// Service object
export const FeatureService = {
  async list(): Promise<FeatureViewModel[]> {
    const response = await ApiService.listFeatures({})
    return response.data.map(transformFeature)
  },

  async get(id: string): Promise<FeatureViewModel> {
    const response = await ApiService.getFeature({ id })
    return transformFeature(response)
  },
}
```

---

## Forms

### react-hook-form + zod + shadcn

```tsx
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Form, FormControl, FormField, FormItem, FormLabel, FormMessage,
} from "@/components/ui/form"

const schema = z.object({
  title: z.string().min(1, "Required").max(100),
})

type FormData = z.infer<typeof schema>

function MyForm() {
  const form = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { title: "" },
  })

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="title"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Title</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button type="submit">Submit</Button>
      </form>
    </Form>
  )
}
```

---

## Layout Patterns

### Page Layout

```tsx
<div className="container mx-auto py-6 space-y-6">
  <header className="flex items-center justify-between">
    <h1 className="text-2xl font-bold">Page Title</h1>
    <Button>Action</Button>
  </header>
  <main>{/* Content */}</main>
</div>
```

### Responsive Grid

```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  {items.map(item => <Card key={item.id} />)}
</div>
```

### Split Layout (Sidebar)

```tsx
<div className="flex h-[calc(100vh-4rem)]">
  <aside className="w-64 border-r p-4">{/* Sidebar */}</aside>
  <main className="flex-1 overflow-auto p-4">{/* Content */}</main>
</div>
```

---

## Common UI Patterns

### Loading State

```tsx
import { Skeleton } from "@/components/ui/skeleton"

{isLoading ? (
  <div className="space-y-2">
    <Skeleton className="h-4 w-full" />
    <Skeleton className="h-4 w-3/4" />
  </div>
) : (
  <Content />
)}
```

### Empty State

```tsx
<div className="flex flex-col items-center justify-center py-12 text-center">
  <Icon className="h-12 w-12 text-muted-foreground mb-4" />
  <h3 className="text-lg font-medium">No items yet</h3>
  <p className="text-sm text-muted-foreground mb-4">
    Get started by creating your first item.
  </p>
  <Button>Create Item</Button>
</div>
```

### Confirmation Dialog

```tsx
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader,
  AlertDialogTitle, AlertDialogTrigger,
} from "@/components/ui/alert-dialog"

<AlertDialog>
  <AlertDialogTrigger asChild>
    <Button variant="destructive">Delete</Button>
  </AlertDialogTrigger>
  <AlertDialogContent>
    <AlertDialogHeader>
      <AlertDialogTitle>Are you sure?</AlertDialogTitle>
      <AlertDialogDescription>This action cannot be undone.</AlertDialogDescription>
    </AlertDialogHeader>
    <AlertDialogFooter>
      <AlertDialogCancel>Cancel</AlertDialogCancel>
      <AlertDialogAction onClick={handleDelete}>Delete</AlertDialogAction>
    </AlertDialogFooter>
  </AlertDialogContent>
</AlertDialog>
```

### Dialog (Modal)

```tsx
import {
  Dialog, DialogContent, DialogDescription, DialogFooter,
  DialogHeader, DialogTitle, DialogTrigger,
} from "@/components/ui/dialog"

<Dialog open={open} onOpenChange={setOpen}>
  <DialogTrigger asChild>
    <Button>Open</Button>
  </DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Title</DialogTitle>
      <DialogDescription>Description</DialogDescription>
    </DialogHeader>
    {/* Content */}
    <DialogFooter>
      <Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
      <Button onClick={handleSubmit}>Confirm</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

### Select

```tsx
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select"

<Select value={value} onValueChange={setValue}>
  <SelectTrigger>
    <SelectValue placeholder="Select..." />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="option1">Option 1</SelectItem>
    <SelectItem value="option2">Option 2</SelectItem>
  </SelectContent>
</Select>
```

### Card

```tsx
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"

<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
    <CardDescription>Description</CardDescription>
  </CardHeader>
  <CardContent>{/* Content */}</CardContent>
  <CardFooter>{/* Actions */}</CardFooter>
</Card>
```

### Icons (Lucide)

```tsx
import { MessageSquare, Settings, Trash2, Plus } from "lucide-react"

<MessageSquare className="h-4 w-4" />
<Button size="icon"><Plus className="h-4 w-4" /></Button>
```
