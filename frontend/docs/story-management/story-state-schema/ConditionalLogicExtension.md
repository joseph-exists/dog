# Conditional Logic Extension Plan

## Overview

Extend the story conditional logic system to support comparison operators, logical operators, and state mutations beyond simple equality/assignment.

---

## Current State

### Data Structure
```typescript
// Simple equality only
requires_state: { gold: 10, has_key: true }
sets_state: { gold: 0, visited: true }
```

### Player Logic
```typescript
// requires_state: equality check
Object.entries(requires_state).every(([key, value]) => playerState[key] === value)

// sets_state: simple merge
setPlayerState(prev => ({ ...prev, ...sets_state }))
```

---

## Proposed Extension

### New Data Structure

Support three value formats for each key:

```typescript
type ConditionValue =
  | primitive                    // Simple equality (backward compatible)
  | { $op: operator, value: V }  // Operator syntax
  | { $expr: string }            // Expression syntax (advanced)

type MutationValue =
  | primitive                    // Simple set (backward compatible)
  | { $op: operator, value: V }  // Operator syntax
```

### Supported Operators

#### Comparison Operators (requires_state)

| Operator | Meaning | Example |
|----------|---------|---------|
| `$eq` | Equals | `{ $eq: 10 }` |
| `$ne` | Not equals | `{ $ne: 0 }` |
| `$gt` | Greater than | `{ $gt: 5 }` |
| `$gte` | Greater than or equal | `{ $gte: 10 }` |
| `$lt` | Less than | `{ $lt: 100 }` |
| `$lte` | Less than or equal | `{ $lte: 50 }` |
| `$in` | In array | `{ $in: ["red", "blue"] }` |
| `$nin` | Not in array | `{ $nin: ["dead", "fled"] }` |
| `$exists` | Variable exists | `{ $exists: true }` |

#### Mutation Operators (sets_state)

| Operator | Meaning | Example |
|----------|---------|---------|
| `$set` | Set value (explicit) | `{ $set: 10 }` |
| `$inc` | Increment | `{ $inc: 5 }` |
| `$dec` | Decrement | `{ $dec: 1 }` |
| `$toggle` | Toggle boolean | `{ $toggle: true }` |
| `$unset` | Remove variable | `{ $unset: true }` |

#### Logical Operators (requires_state only)

| Operator | Meaning | Example |
|----------|---------|---------|
| `$and` | All conditions true | `{ $and: [{...}, {...}] }` |
| `$or` | Any condition true | `{ $or: [{...}, {...}] }` |
| `$not` | Negate condition | `{ $not: { key: value } }` |

### Examples

```typescript
// Example 1: Buy item (costs 10 gold, requires 10+ gold)
requires_state: {
  gold: { $gte: 10 }
}
sets_state: {
  gold: { $dec: 10 },
  has_sword: true
}

// Example 2: Conditional dialogue (branching based on reputation)
requires_state: {
  reputation: { $gte: 50 },
  faction: { $in: ["knights", "merchants"] }
}

// Example 3: Either/or condition
requires_state: {
  $or: [
    { has_key: true },
    { lockpick_skill: { $gte: 5 } }
  ]
}

// Example 4: Complex condition with AND/OR
requires_state: {
  $and: [
    { is_alive: true },
    { $or: [
      { has_sword: true },
      { has_axe: true }
    ]}
  ]
}
```

---

## Implementation Phases

### Phase 1: Core Evaluator Functions

**Location**: `frontend/src/utils/stateConditions.ts`

```typescript
// Evaluate a condition against player state
export function evaluateCondition(
  condition: ConditionValue,
  key: string,
  state: Record<string, unknown>
): boolean

// Evaluate full requires_state object
export function evaluateRequiresState(
  requires: Record<string, unknown> | null,
  state: Record<string, unknown>
): boolean

// Apply a mutation to state
export function applyMutation(
  mutation: MutationValue,
  key: string,
  currentValue: unknown
): unknown

// Apply full sets_state object
export function applySetsState(
  sets: Record<string, unknown> | null,
  state: Record<string, unknown>
): Record<string, unknown>
```

**Tests**: `frontend/src/utils/stateConditions.test.ts`

### Phase 2: Update Story Player

**Location**: `frontend/src/components/Stories/StoryPlayer/StoryPreview.tsx`

Replace simple logic with new evaluator functions:

```typescript
// Before
return Object.entries(choice.requires_state).every(([key, value]) => {
  return playerState[key] === value
})

// After
return evaluateRequiresState(choice.requires_state, playerState)
```

```typescript
// Before
setPlayerState(prev => ({ ...prev, ...choice.sets_state }))

// After
setPlayerState(prev => applySetsState(choice.sets_state, prev))
```

### Phase 3: Enhance StateConditionEditor UI

**Location**: `frontend/src/components/Stories/shared/StateConditionEditor.tsx`

#### 3.1 Add Operator Selection

For each condition entry, add operator dropdown:

```
[key input] [operator ▼] [value input]
            └── equals
                not equals
                greater than
                greater than or equal
                less than
                less than or equal
                in list
                exists
```

#### 3.2 Type-Aware Operators

- **Boolean**: Only `equals`, `not equals`, `exists`
- **Number**: All comparison operators
- **String**: `equals`, `not equals`, `in list`, `exists`
- **Enum**: `equals`, `not equals`, `in list`

#### 3.3 Mutation Mode

Different operator set for `sets_state`:

```
[key input] [mutation ▼] [value input]
            └── set to
                increment by
                decrement by
                toggle
                unset
```

### Phase 4: Logical Operators UI

Add ability to group conditions with AND/OR:

```
┌─ Show this choice only if: ─────────────────────┐
│                                                  │
│  ┌─ All of (AND) ──────────────────────────────┐│
│  │ gold      >= 10                              ││
│  │ is_alive  =  true                            ││
│  └──────────────────────────────────────────────┘│
│                                                  │
│  [+ Add condition] [+ Add group]                 │
└──────────────────────────────────────────────────┘
```

### Phase 5: Validation Integration

Update `get_undefined_variables_in_choices` CRUD function to:
- Parse operator syntax to extract variable keys
- Validate operator usage against variable types
- Report type mismatches (e.g., `$gte` on boolean)

### Phase 6: Expression Mode (Optional Advanced)

Add toggle for "Advanced: Expression mode" that allows raw expression input:

```typescript
requires_state: {
  $expr: "gold >= 10 AND (has_key OR lockpick >= 5)"
}
```

Requires:
- Expression parser
- Expression evaluator
- Syntax highlighting in editor
- Error reporting

---

## Backward Compatibility

All existing simple conditions continue to work:

```typescript
// Old format - still valid
{ gold: 10, has_key: true }

// Interpreted as
{ gold: { $eq: 10 }, has_key: { $eq: true } }
```

---

## File Changes Summary

| Phase | Files | Changes |
|-------|-------|---------|
| 1 | `utils/stateConditions.ts` | New evaluator functions |
| 1 | `utils/stateConditions.test.ts` | Unit tests |
| 2 | `StoryPlayer/StoryPreview.tsx` | Use new evaluators |
| 3 | `shared/StateConditionEditor.tsx` | Operator dropdowns |
| 4 | `shared/StateConditionEditor.tsx` | Logical grouping UI |
| 5 | `backend/app/crud.py` | Enhanced validation |
| 6 | `shared/StateConditionEditor.tsx` | Expression mode (optional) |

---

## Implementation Order

| Step | Task | Effort | Dependencies |
|------|------|--------|--------------|
| 1.1 | Create evaluateCondition function | Small | None |
| 1.2 | Create evaluateRequiresState function | Small | 1.1 |
| 1.3 | Create applyMutation function | Small | None |
| 1.4 | Create applySetsState function | Small | 1.3 |
| 1.5 | Write unit tests | Medium | 1.1-1.4 |
| 2.1 | Update StoryPreview requires_state | Small | 1.2 |
| 2.2 | Update StoryPreview sets_state | Small | 1.4 |
| 3.1 | Add operator dropdown to editor | Medium | None |
| 3.2 | Add mutation mode to editor | Medium | 3.1 |
| 3.3 | Type-aware operator filtering | Small | 3.1 |
| 4.1 | Add condition grouping UI | Large | 3.1 |
| 5.1 | Update backend validation | Medium | 1.1-1.4 |
| 6.1 | Expression parser (optional) | Large | None |
| 6.2 | Expression UI (optional) | Medium | 6.1 |

---

## Testing Checklist

### Unit Tests (Phase 1)
- [ ] evaluateCondition with each operator
- [ ] evaluateRequiresState with mixed conditions
- [ ] applyMutation with each operator
- [ ] applySetsState with mixed mutations
- [ ] Backward compatibility with simple format

### Integration Tests (Phase 2)
- [ ] Story player shows/hides choices correctly
- [ ] State mutations apply correctly
- [ ] Complex conditions evaluate correctly

### UI Tests (Phases 3-4)
- [ ] Operator dropdown shows correct options per type
- [ ] Value input adapts to operator (e.g., array for $in)
- [ ] Logical grouping creates correct structure
- [ ] JSON preview shows correct output

---

## Notes

- Phase 6 (expressions) is optional - structured operators cover most use cases
- Consider adding "templates" for common patterns (buy item, check stat, etc.)
- Backend validation should warn but not block (soft validation)
- All changes must be backward compatible with existing stories

---

## Implementation Status

**Last Updated: 2026-01-11**

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1: Core Evaluators | COMPLETE | `src/utils/stateConditions.ts` |
| Phase 2: StoryPreview Update | COMPLETE | Using new evaluators |
| Phase 3: Operator UI | COMPLETE | Comparison + mutation operators |
| Phase 4: Logical Grouping | COMPLETE | AND/OR group UI with nesting support |
| Phase 5: Backend Validation | PENDING | Deferred - frontend only |
| Phase 6: Expression Mode | PENDING | Optional advanced feature |

### Files Created

| File | Purpose |
|------|---------|
| `src/utils/stateConditions.ts` | Core evaluator functions |

### Files Modified

| File | Changes |
|------|---------|
| `src/components/Stories/StoryPlayer/StoryPreview.tsx` | Use evaluateRequiresState and applySetsState |
| `src/components/Stories/shared/StateConditionEditor.tsx` | Operator dropdowns, mode-aware operators |
| `src/components/Stories/StoryEditor/NodeEditor/ChoiceEditor.tsx` | Pass mode prop to editors |

### Supported Operators (Implemented)

**Comparison (requires_state):**
- `equals` (simple value or `$eq`)
- `not equals` (`$ne`)
- `>`, `>=`, `<`, `<=` (`$gt`, `$gte`, `$lt`, `$lte`)
- `in list` (`$in`)
- `exists` (`$exists`)

**Mutation (sets_state):**
- `set to` (simple value or `$set`)
- `increment by` (`$inc`)
- `decrement by` (`$dec`)
- `toggle` (`$toggle`)
- `unset` (`$unset`)

### Logical Grouping (Phase 4)

The StateConditionEditor now supports AND/OR groups for `requires_state` conditions:

**UI Features:**
- Top-level conditions are implicitly AND (all must be true)
- "Add OR Group" button creates a visual group of alternative conditions
- Groups can be toggled between "Any of" (OR) and "All of" (AND)
- Each group is rendered in a bordered card for visual distinction
- Groups can contain multiple conditions with the same operators as top-level

**Example Generated JSON:**
```typescript
{
  gold: { $gte: 10 },           // Must have 10+ gold
  is_alive: true,               // AND must be alive
  $or: [                        // AND must have either:
    { has_key: true },          //   - a key, OR
    { lockpick: { $gte: 5 } }   //   - lockpick skill 5+
  ]
}
```

**Design Decisions:**
- Groups only available in `requires` mode (not `sets`)
- Limited to 2 levels of nesting (root + one group level) for simplicity
- Empty groups are automatically removed
- Duplicate key detection works across all entries and groups

### Backward Compatibility

All existing simple conditions continue to work without changes.
