# Tinyfoot Frontend: Component Development Walkthrough

This walkthrough will guide you through the process of adding components to the Tinyfoot frontend, based on the project's architecture, patterns, and best practices.

## Component Organization Overview

Tinyfoot's frontend organizes components into three main categories:

1. **Feature-specific components** (`src/components/[FeatureName]/`)
   - Components tied to specific business domains (Admin, Items, Personas, etc.)
   - Example: `src/components/Admin/AddUser.tsx`

2. **Common components** (`src/components/Common/`)
   - Shared components used across multiple features
   - Often compose UI primitives into application-specific patterns
   - Example: `src/components/Common/Navbar.tsx`

3. **UI primitives** (`src/components/ui/`)
   - Base-level UI components that implement design system fundamentals
   - Often wrap or extend Chakra UI components
   - Example: `src/components/ui/button.tsx`

## When to Add Components to Each Directory

### Feature-Specific Components (`src/components/[FeatureName]/`)

**When to use:**
- The component is specific to one feature/domain
- The component handles business logic related to a specific entity
- The component won't be reused across unrelated features

**Workflow:**

1. **Identify the feature domain**
   - If the component relates to user management → `Admin/`
   - If it relates to personas → `Personas/`
   - If it relates to items → `Items/`
   - If it relates to archetypes → `Archetypes/`

2. **Check if a directory exists for your feature**
   - If yes: add your component there
   - If no: create a new directory using PascalCase

3. **Name your component file**
   - Use PascalCase (e.g., `AddItem.tsx`, `EditUser.tsx`)
   - Name should clearly describe the component's purpose
   - For CRUD operations, prefix with action (Add, Edit, Delete, View)

4. **Create the component**
   ```tsx
   // src/components/[FeatureName]/[ComponentName].tsx
   import { useMutation, useQueryClient } from "@tanstack/react-query"
   import { useForm } from "react-hook-form"
   import { [EntityService] } from "@/client"
   import useCustomToast from "@/hooks/useCustomToast"
   // Add other imports...

   const [ComponentName] = () => {
     // Component implementation...
     return (
       // JSX
     )
   }

   export default [ComponentName]
   ```

5. **Implement data fetching with React Query**
   ```tsx
   const queryClient = useQueryClient()
   const mutation = useMutation({
     mutationFn: (data: EntityType) =>
       EntityService.createEntity({ requestBody: data }),
     onSuccess: () => {
       showSuccessToast("Entity created successfully.")
       // Reset form, close modal, etc.
     },
     onError: (err: ApiError) => {
       handleError(err)
     },
     onSettled: () => {
       queryClient.invalidateQueries({ queryKey: ["entityKey"] })
     },
   })
   ```

**Example:** Adding a "DownloadItem" component

```tsx
// src/components/Items/DownloadItem.tsx
import { useMutation } from "@tanstack/react-query"
import { ItemsService } from "@/client"
import useCustomToast from "@/hooks/useCustomToast"
import { Button } from "@chakra-ui/react"
import { FaDownload } from "react-icons/fa"

const DownloadItem = ({ itemId }: { itemId: string }) => {
  const { showSuccessToast } = useCustomToast()

  const mutation = useMutation({
    mutationFn: () => ItemsService.downloadItem({ itemId }),
    onSuccess: (data) => {
      // Handle download success
      showSuccessToast("Item downloaded successfully")
      // Logic to save the file locally
    },
    onError: (err) => {
      handleError(err)
    }
  })

  return (
    <Button
      onClick={() => mutation.mutate()}
      isLoading={mutation.isPending}
      leftIcon={<FaDownload />}
    >
      Download
    </Button>
  )
}

export default DownloadItem
```

### Common Components (`src/components/Common/`)

**When to use:**
- The component is used across multiple feature domains
- The component represents a business concept but isn't tied to a specific feature
- The component composes UI primitives into application-specific patterns

**Workflow:**

1. **Determine if the component belongs in Common**
   - Is it used in multiple features?
   - Does it represent an application-specific pattern?
   - Is it not a pure UI primitive?

2. **Name your component file**
   - Use PascalCase (e.g., `EntityCard.tsx`, `SearchBar.tsx`)
   - Names should be descriptive and reflect the component's purpose

3. **Create the component**
   ```tsx
   // src/components/Common/[ComponentName].tsx
   import { /* UI components */ } from "@chakra-ui/react"
   // Import UI primitives from src/components/ui if needed

   const [ComponentName] = ({ /* props */ }) => {
     // Component implementation...
     return (
       // JSX that often composes UI primitives or Chakra components
     )
   }

   export default [ComponentName]
   ```

4. **Avoid data fetching in Common components if possible**
   - Common components should be presentational or accept data as props
   - If data fetching is required, consider creating a container component in the feature directory

**Example:** Adding a "FilterBar" common component

```tsx
// src/components/Common/FilterBar.tsx
import { useState } from "react"
import {
  Flex, Input, Select, IconButton, Box, Text
} from "@chakra-ui/react"
import { FaFilter, FaSearch, FaTimes } from "react-icons/fa"

type FilterOption = {
  label: string
  value: string
}

type FilterBarProps = {
  filterOptions: FilterOption[]
  onFilterChange: (filter: string, searchTerm: string) => void
}

const FilterBar = ({ filterOptions, onFilterChange }: FilterBarProps) => {
  const [filter, setFilter] = useState("")
  const [searchTerm, setSearchTerm] = useState("")

  const handleSearch = () => {
    onFilterChange(filter, searchTerm)
  }

  const clearFilters = () => {
    setFilter("")
    setSearchTerm("")
    onFilterChange("", "")
  }

  return (
    <Flex gap={4} mb={4} alignItems="center" flexWrap="wrap">
      <Text fontWeight="medium">Filter:</Text>
      <Select
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        placeholder="Select filter"
        maxW="200px"
      >
        {filterOptions.map(option => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </Select>

      <Input
        placeholder="Search..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        maxW="300px"
      />

      <IconButton
        icon={<FaSearch />}
        aria-label="Search"
        onClick={handleSearch}
      />

      <IconButton
        icon={<FaTimes />}
        aria-label="Clear filters"
        onClick={clearFilters}
      />
    </Flex>
  )
}

export default FilterBar
```

### UI Primitives (`src/components/ui/`)

**When to use:**
- The component is a low-level UI building block
- The component implements design system fundamentals
- The component extends or wraps Chakra UI components to provide app-specific styling
- The component will be reused across multiple features and common components

**Workflow:**

1. **Determine if the component belongs in UI**
   - Is it a fundamental UI building block?
   - Will it be used across many components?
   - Does it implement design system principles?

2. **Name your component file**
   - Use kebab-case (e.g., `data-table.tsx`, `avatar-group.tsx`)
   - Names should reflect the elemental nature of the component

3. **Create the component**
   ```tsx
   // src/components/ui/[component-name].tsx
   import {
     Box,
     type BoxProps,
     // Other Chakra components
   } from "@chakra-ui/react"

   export interface [ComponentName]Props extends BoxProps {
     // Additional props
   }

   export const [ComponentName] = ({
     children,
     ...props
   }: [ComponentName]Props) => {
     return (
       <Box
         // Base styling
         {...props}
       >
         {children}
       </Box>
     )
   }
   ```

4. **Export for use in other components**
   - Export the component directly, not as default
   - Export types and interfaces for props

**Example:** Adding a "status-badge" UI component

```tsx
// src/components/ui/status-badge.tsx
import {
  Badge,
  type BadgeProps
} from "@chakra-ui/react"
import { ReactNode } from "react"

export type StatusVariant =
  | "success"
  | "error"
  | "warning"
  | "info"
  | "pending"

export interface StatusBadgeProps extends Omit<BadgeProps, "colorScheme"> {
  variant: StatusVariant
  children: ReactNode
}

const variantMap: Record<StatusVariant, { bg: string; color: string }> = {
  success: { bg: "green.100", color: "green.800" },
  error: { bg: "red.100", color: "red.800" },
  warning: { bg: "orange.100", color: "orange.800" },
  info: { bg: "blue.100", color: "blue.800" },
  pending: { bg: "gray.100", color: "gray.800" },
}

export const StatusBadge = ({
  variant,
  children,
  ...props
}: StatusBadgeProps) => {
  const { bg, color } = variantMap[variant]

  return (
    <Badge
      px={2}
      py={1}
      borderRadius="full"
      bg={bg}
      color={color}
      fontWeight="medium"
      {...props}
    >
      {children}
    </Badge>
  )
}
```

## Decision Tree for Component Placement

Use this decision tree to determine where to place your component:

1. **Is this component a UI primitive or design system element?**
   - **YES** → Place in `src/components/ui/`
   - **NO** → Continue to step 2

2. **Is this component used across multiple features?**
   - **YES** → Place in `src/components/Common/`
   - **NO** → Continue to step 3

3. **Which business domain does this component relate to?**
   - Admin/User Management → `src/components/Admin/`
   - Items → `src/components/Items/`
   - Personas → `src/components/Personas/`
   - Archetypes → `src/components/Archetypes/`
   - User Settings → `src/components/UserSettings/`
   - None of the above → Consider creating a new feature directory

## Best Practices for Component Development

### Component Structure

1. **Imports section:**
   ```tsx
   // React and hooks
   import { useState, useEffect } from "react"

   // External libraries
   import { useQuery, useMutation } from "@tanstack/react-query"
   import { useForm } from "react-hook-form"

   // Internal utilities
   import { handleError } from "@/utils"
   import useCustomToast from "@/hooks/useCustomToast"

   // API services
   import { EntityService } from "@/client"

   // UI components (Chakra first, then custom UI components)
   import { Button, Input, VStack } from "@chakra-ui/react"
   import { Field } from "../ui/field"
   ```

2. **Component definition:**
   ```tsx
   const ComponentName = ({ prop1, prop2 }: ComponentProps) => {
     // State, hooks, and logic

     // Event handlers

     // Render
     return (
       // JSX
     )
   }

   export default ComponentName
   ```

### Form Implementation Pattern

```tsx
const MyFormComponent = () => {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

  const {
    control,
    register,
    handleSubmit,
    reset,
    formState: { errors, isValid, isSubmitting },
  } = useForm<FormType>({
    mode: "onBlur",
    defaultValues: {
      field1: "",
      field2: "",
    },
  })

  const mutation = useMutation({
    mutationFn: (data: FormType) =>
      EntityService.createEntity({ requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Entity created successfully.")
      reset()
      // Close modal or navigate if needed
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["entities"] })
    },
  })

  const onSubmit = (data: FormType) => {
    mutation.mutate(data)
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <VStack spacing={4}>
        <Field
          required
          label="Field 1"
          invalid={!!errors.field1}
          errorText={errors.field1?.message}
        >
          <Input
            {...register("field1", {
              required: "Field 1 is required",
            })}
            placeholder="Enter field 1"
          />
        </Field>

        {/* More fields */}

        <Button
          type="submit"
          disabled={!isValid}
          loading={isSubmitting}
        >
          Submit
        </Button>
      </VStack>
    </form>
  )
}
```

### Dialog/Modal Pattern

```tsx
const EntityActionComponent = () => {
  const [isOpen, setIsOpen] = useState(false)

  // Component logic...

  return (
    <DialogRoot
      size={{ base: "xs", md: "md" }}
      placement="center"
      open={isOpen}
      onOpenChange={({ open }) => setIsOpen(open)}
    >
      <DialogTrigger asChild>
        <Button>Open Dialog</Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Dialog Title</DialogTitle>
          </DialogHeader>
          <DialogBody>
            {/* Form fields */}
          </DialogBody>
          <DialogFooter gap={2}>
            <DialogActionTrigger asChild>
              <Button variant="subtle" colorPalette="gray">
                Cancel
              </Button>
            </DialogActionTrigger>
            <Button type="submit" disabled={!isValid}>
              Save
            </Button>
          </DialogFooter>
        </form>
        <DialogCloseTrigger />
      </DialogContent>
    </DialogRoot>
  )
}
```

## Summary

By following this walkthrough and component organization strategy, you'll:

1. Maintain consistency with the existing codebase
2. Create maintainable, reusable components
3. Keep related logic together in the appropriate directories
4. Enable other developers to quickly find and understand your components

Remember to consider the purpose, reusability, and domain-specificity of your component when deciding where to place it. When in doubt, review similar existing components for guidance on structure and organization.
