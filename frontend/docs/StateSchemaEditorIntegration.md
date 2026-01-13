# State Schema Editor Integration Reference Card

## Overview

Integrate the StoryStateVariable schema management into the story authoring workflow. Authors can define typed variables (boolean, number, string, enum) that are validated at publish time.

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           StoryEditor                                    │
├──────────────┬─────────────────────────────┬────────────────────────────┤
│  NodeTree    │       NodeEditor            │     PropertiesPanel        │
│              │                             │                            │
│              │  ┌─────────────────────┐    │  [Manage Variables] ──────┐│
│              │  │    ChoiceEditor     │    │                           ││
│              │  │  ┌───────────────┐  │    │  State Variables: 5       ││
│              │  │  │ StateCondition│  │    │  ⚠ 2 undefined            ││
│              │  │  │ Editor        │◄─┼────┼──schema autocomplete      ││
│              │  │  └───────────────┘  │    │                           ││
│              │  └─────────────────────┘    │                           ││
└──────────────┴─────────────────────────────┴────────────────────────────┘
                                                         │
                                              ┌──────────▼──────────┐
                                              │  StateSchemaDrawer  │
                                              │  ┌────────────────┐ │
                                              │  │ StateSchema    │ │
                                              │  │ Editor         │ │
                                              │  │ (table + CRUD) │ │
                                              │  └────────────────┘ │
                                              └─────────────────────┘
```

---

## Components to Create

### 1. StateSchemaEditor

**Location**: `frontend/src/components/Stories/StoryEditor/StateSchema/StateSchemaEditor.tsx`

**Purpose**: Table displaying all state variables with add/edit/delete actions

**Props**:
```typescript
interface StateSchemaEditorProps {
  storyId: string
  version: number
  isReadOnly?: boolean  // true when viewing published version
}
```

**Features**:
- Table columns: Key, Type, Default, Category, Actions
- Group by category (collapsible sections)
- Add Variable button → opens modal
- Edit/Delete actions per row
- Empty state with helpful message

**Hooks to use**:
- `useStateSchema(storyId, version)` - fetch variables
- `useCreateStateVariable(storyId, version)` - create
- `useUpdateStateVariable(storyId, version)` - update
- `useDeleteStateVariable(storyId, version)` - delete

---

### 2. StateVariableModal

**Location**: `frontend/src/components/Stories/StoryEditor/StateSchema/StateVariableModal.tsx`

**Purpose**: Modal form for creating/editing a state variable

**Props**:
```typescript
interface StateVariableModalProps {
  storyId: string
  version: number
  variable?: StoryStateVariablePublic  // if provided, edit mode
  isOpen: boolean
  onClose: () => void
}
```

**Form Fields**:
| Field | Type | Validation |
|-------|------|------------|
| key | Input | Required, 1-100 chars, no spaces |
| value_type | Select | boolean, number, string, enum |
| default_value | Dynamic | Based on value_type |
| enum_values | TagInput | Required if type=enum |
| category | Input | Optional, 1-100 chars |
| description | Textarea | Optional, max 500 chars |

**Conditional Logic**:
- Show `enum_values` field only when `value_type === "enum"`
- Show appropriate default_value input based on type:
  - boolean → Checkbox
  - number → Number input
  - string → Text input
  - enum → Select from enum_values

---

### 3. StateSchemaDrawer

**Location**: `frontend/src/components/Stories/StoryEditor/StateSchema/StateSchemaDrawer.tsx`

**Purpose**: Slide-out drawer containing StateSchemaEditor

**Props**:
```typescript
interface StateSchemaDrawerProps {
  storyId: string
  version: number
  isOpen: boolean
  onClose: () => void
  isReadOnly?: boolean
}
```

**Layout**:
```
┌─────────────────────────────────┐
│ State Variables          [X]   │
├─────────────────────────────────┤
│ Define variables that can be   │
│ used in choice conditions.     │
│                                │
│ [+ Add Variable]               │
│                                │
│ ┌─────────────────────────────┐│
│ │ StateSchemaEditor           ││
│ │ (table)                     ││
│ └─────────────────────────────┘│
│                                │
│ ─────────────────────────────  │
│ Validation Summary             │
│ ✓ All variables defined        │
│   OR                           │
│ ⚠ 2 undefined variables used   │
└─────────────────────────────────┘
```

---

### 4. Enhanced StateConditionEditor

**Location**: `frontend/src/components/Stories/shared/StateConditionEditor.tsx` (modify existing)

**New Props**:
```typescript
interface StateConditionEditorProps {
  label: string
  value: Record<string, unknown> | null
  onChange: (value: Record<string, unknown> | null) => void
  schema?: StoryStateVariablePublic[]  // NEW: optional schema for autocomplete
}
```

**Enhancements**:
1. Key input becomes Combobox with schema keys as suggestions
2. When key matches schema variable:
   - Auto-detect value type
   - Show appropriate value input (checkbox/number/text/select)
3. Warning badge for keys not in schema
4. Tooltip showing variable description from schema

---

## Files to Modify

### PropertiesPanel.tsx

**Add to imports**:
```typescript
import { useStateSchema, useValidateStateSchema } from "@/hooks/stories/useStateSchema"
import StateSchemaDrawer from "../StateSchema/StateSchemaDrawer"
```

**Add state**:
```typescript
const [isSchemaDrawerOpen, setIsSchemaDrawerOpen] = useState(false)
const { data: schemaData } = useStateSchema(story.id, story.current_version)
const { data: validationData } = useValidateStateSchema(story.id, story.current_version)
```

**Add section after "Node Statistics"**:
```tsx
<Separator />

{/* State Variables */}
<Box>
  <Heading size="sm" mb={3}>
    State Variables
  </Heading>
  <VStack align="stretch" gap={2}>
    <HStack justify="space-between">
      <Text fontSize="sm" color="fg.muted">Defined:</Text>
      <Text fontWeight="bold">{schemaData?.count ?? 0}</Text>
    </HStack>
    {validationData && !validationData.is_valid && (
      <HStack fontSize="xs" color="orange.600">
        <FaExclamationTriangle />
        <Text>{validationData.undefined_variables.length} undefined</Text>
      </HStack>
    )}
    <Button
      size="sm"
      variant="outline"
      onClick={() => setIsSchemaDrawerOpen(true)}
    >
      Manage Variables
    </Button>
  </VStack>
</Box>
```

---

### ChoiceEditor.tsx

**Add to imports**:
```typescript
import { useStateSchema } from "@/hooks/stories/useStateSchema"
```

**Add props**:
```typescript
interface ChoiceEditorProps {
  fromNodeId: string
  availableNodes: StoryNodePublic[]
  storyId: string      // NEW
  storyVersion: number // NEW
  choice?: NodeChoicePublic
  trigger?: React.ReactNode
  onSuccess?: () => void
}
```

**Fetch schema and pass to StateConditionEditor**:
```typescript
const { data: schemaData } = useStateSchema(storyId, storyVersion)

// In render, pass schema:
<StateConditionEditor
  label="Show this choice only if:"
  value={field.value ?? null}
  onChange={field.onChange}
  schema={schemaData?.data}  // NEW
/>
```

---

## API Types Reference

```typescript
// From generated client
type StateValueType = "boolean" | "number" | "string" | "enum"

type StoryStateVariablePublic = {
  id: string
  story_id: string
  story_version: number
  key: string
  value_type: StateValueType
  default_value: unknown | null
  enum_values: string[] | null
  description: string | null
  category: string | null
}

type StateSchemaValidationResult = {
  is_valid: boolean
  errors: StateSchemaValidationError[]
  defined_variables: string[]
  used_variables: string[]
  undefined_variables: string[]
}
```

---

## Implementation Checklist

| Step | Task | Files |
|------|------|-------|
| 1 | Create StateVariableModal | `StateSchema/StateVariableModal.tsx` |
| 2 | Create StateSchemaEditor | `StateSchema/StateSchemaEditor.tsx` |
| 3 | Create StateSchemaDrawer | `StateSchema/StateSchemaDrawer.tsx` |
| 4 | Add drawer trigger to PropertiesPanel | `PropertiesPanel/PropertiesPanel.tsx` |
| 5 | Enhance StateConditionEditor | `shared/StateConditionEditor.tsx` |
| 6 | Pass schema to ChoiceEditor | `NodeEditor/ChoiceEditor.tsx` |
| 7 | Update validation display | `PropertiesPanel/PropertiesPanel.tsx` |

---

## Testing Checklist

- [ ] Can create a new state variable
- [ ] Can edit an existing state variable
- [ ] Can delete a state variable
- [ ] Enum type requires enum_values
- [ ] Cannot edit published version variables
- [ ] StateConditionEditor shows autocomplete suggestions
- [ ] StateConditionEditor shows warning for undefined keys
- [ ] Validation shows undefined variable count
- [ ] Variables copied when creating new version

---

## Patterns to Follow

**Existing patterns to reference**:
- `ChoiceEditor.tsx` - Modal with react-hook-form
- `useStoryNodes.ts` - CRUD mutation hooks pattern
- `NodeTree.tsx` - Collapsible sections

**Chakra UI components to use**:
- `DrawerRoot`, `DrawerContent`, etc. from `@/components/ui/drawer`
- `DialogRoot`, `DialogContent`, etc. from `@/components/ui/dialog`
- `Table` for variable list
- `Field` from `@/components/ui/field`
- `Combobox` or `Select` for autocomplete (check existing usage)

---

## Notes

- State schema is versioned per `story_version`
- Published versions are read-only
- Validation is a soft block (can force publish with `force=true`)
- Schema is copied when creating new version from published

---

## Implementation Status

**Completed: 2024-01-11**

| Step | Task | Status | Files Created/Modified |
|------|------|--------|------------------------|
| 1 | Create StateVariableModal | DONE | `StateSchema/StateVariableModal.tsx` |
| 2 | Create StateSchemaEditor | DONE | `StateSchema/StateSchemaEditor.tsx` |
| 3 | Create StateSchemaDrawer | DONE | `StateSchema/StateSchemaDrawer.tsx` |
| 4 | Create index.ts for exports | DONE | `StateSchema/index.ts` |
| 5 | Add drawer trigger to PropertiesPanel | DONE | `PropertiesPanel/PropertiesPanel.tsx` |
| 6 | Enhance StateConditionEditor | DONE | `shared/StateConditionEditor.tsx` |
| 7 | Pass schema to ChoiceEditor | DONE | `NodeEditor/ChoiceEditor.tsx` |
| 8 | Update NodeEditor props | DONE | `NodeEditor/NodeEditor.tsx` |

---

## Deviations from Plan

### 1. Key Autocomplete Implementation

**Plan**: Use Combobox component for key autocomplete
**Implementation**: Used HTML5 `<datalist>` with native `<Input list={...}>` attribute

**Rationale**: No existing Combobox component in the codebase. HTML5 datalist provides native browser autocomplete with minimal code and good UX. This is simpler and more maintainable.

**Validation**: Works across modern browsers, provides autocomplete suggestions when typing.

### 2. Type Selector for Schema-Defined Variables

**Plan**: Disable type selector when variable is in schema
**Implementation**: Show a colored Badge instead of disabled select

**Rationale**: Chakra UI's `NativeSelectField` doesn't support the `disabled` prop. Using a Badge provides clear visual indication that the type is locked by the schema, and uses the same color scheme as the StateSchemaEditor for consistency.

**Validation**: Type is locked for schema-defined variables, users see colored badge matching variable type.

### 3. Added Validation Hook

**Plan**: Not explicitly specified
**Implementation**: Added `useValidateStateSchema` hook for fetching validation status

**Rationale**: Required for showing validation summary in drawer and PropertiesPanel. Follows same pattern as other hooks.

### 4. Index File for Exports

**Plan**: Not specified
**Implementation**: Created `StateSchema/index.ts` for cleaner imports

**Rationale**: Follows project convention, enables `import { StateSchemaDrawer } from "../StateSchema"` pattern.

---

## Files Created

| File | Purpose |
|------|---------|
| `src/components/Stories/StoryEditor/StateSchema/StateVariableModal.tsx` | Add/edit variable form modal |
| `src/components/Stories/StoryEditor/StateSchema/StateSchemaEditor.tsx` | Variable table with CRUD |
| `src/components/Stories/StoryEditor/StateSchema/StateSchemaDrawer.tsx` | Slide-out drawer wrapper |
| `src/components/Stories/StoryEditor/StateSchema/index.ts` | Module exports |
| `src/hooks/stories/useStateSchema.ts` | Query/mutation hooks |

## Files Modified

| File | Changes |
|------|---------|
| `src/components/Stories/StoryEditor/PropertiesPanel/PropertiesPanel.tsx` | Added State Variables section, drawer trigger |
| `src/components/Stories/shared/StateConditionEditor.tsx` | Added schema prop, autocomplete, type auto-detection, warnings |
| `src/components/Stories/StoryEditor/NodeEditor/ChoiceEditor.tsx` | Added storyId/storyVersion props, schema fetch |
| `src/components/Stories/StoryEditor/NodeEditor/NodeEditor.tsx` | Pass storyVersion to ChoiceEditor |
