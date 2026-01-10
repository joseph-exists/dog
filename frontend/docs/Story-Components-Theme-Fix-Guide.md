# Story Components Theme Fix Guide

## Problem
Story components are showing white backgrounds instead of respecting the application's dark theme.

## Root Cause
Hardcoded color values (especially `bg="white"`, `bg="gray.50"`, and light text colors) are overriding the theme defaults.

## Quick Fix Checklist

### 1. Remove Hardcoded Background Colors

**REMOVE these props:**
- `bg="white"` → Remove entirely or use `bg="bg"`
- `bg="gray.50"` → Remove entirely or use `bg="bg.subtle"`
- `borderColor="gray.200"` → Remove entirely or use `borderColor="border"`

**Example Fix:**
```tsx
// BEFORE (wrong - hardcoded white)
<Box bg="white" borderColor="gray.200">

// AFTER (correct - respects theme)
<Box bg="bg" borderColor="border">
// OR simply remove bg entirely if default is fine
<Box>
```

### 2. Fix Text Colors

**REMOVE these props:**
- `color="gray.600"` → Use `color="fg.muted"` or remove
- `color="gray.500"` → Use `color="fg.subtle"` or remove
- Hard-coded light colors

**Example Fix:**
```tsx
// BEFORE
<Text color="gray.600">Description</Text>

// AFTER
<Text color="fg.muted">Description</Text>
```

### 3. Common Component Patterns

#### Box/Container Components
```tsx
// BEFORE
<Box bg="white" borderColor="gray.200" p={4}>

// AFTER
<Box borderColor="border" p={4}>
// The bg will default to transparent and respect parent theme
```

#### Empty States
```tsx
// BEFORE
<EmptyState.Root bg="gray.50">

// AFTER
<EmptyState.Root>
// Let it use default theming
```

#### Panels/Sections
```tsx
// BEFORE
<Box bg="gray.50" borderRight="1px" borderColor="gray.200">

// AFTER
<Box bg="bg.subtle" borderRight="1px" borderColor="border">
```

#### Cards
```tsx
// BEFORE
<Card.Root>
  <Card.Body bg="white">

// AFTER
<Card.Root>
  <Card.Body>
// Card has default theming built-in
```

### 4. Semantic Color Tokens (Use These!)

| Use Case | Token |
|----------|-------|
| Default background | `bg` |
| Subtle background | `bg.subtle` |
| Emphasized background | `bg.emphasized` |
| Border | `border` |
| Text (normal) | `fg` |
| Text (muted) | `fg.muted` |
| Text (subtle) | `fg.subtle` |

### 5. Files to Fix

Check these files and apply the patterns above:

1. **StoryEditor.tsx**
   - Remove `bg="white"` from header
   - Remove `bg="gray.50"` from left/right panels
   - Change to `bg="bg.subtle"` or remove

2. **NodeEditor.tsx**
   - Remove `bg="white"` from main container
   - Content box: change `bg="gray.50"` to `bg="bg.subtle"`
   - Text colors: use semantic tokens

3. **NodeTree.tsx**
   - Remove `bg="gray.50"`
   - Use default or `bg="bg.subtle"`

4. **PropertiesPanel.tsx**
   - Remove `bg="gray.50"`
   - Text colors: use `color="fg.muted"` instead of `color="gray.600"`

5. **StoryList.tsx**
   - Cards should use default theming
   - Remove any hardcoded white backgrounds

6. **StoryCard.tsx**
   - Remove `bg="white"` from Card
   - Let Card component use its default theming

7. **PublishModal.tsx**
   - Check for `bg="orange.50"`, `bg="green.50"`, etc.
   - These can stay for visual emphasis but verify they work in dark mode
   - Or use semantic equivalents

### 6. Search and Replace Commands

Run these to find problematic patterns:

```bash
# Find hardcoded white backgrounds
grep -r 'bg="white"' src/components/Stories/

# Find hardcoded gray backgrounds
grep -r 'bg="gray\.' src/components/Stories/

# Find hardcoded gray text colors
grep -r 'color="gray\.' src/components/Stories/

# Find hardcoded border colors
grep -r 'borderColor="gray\.' src/components/Stories/
```

### 7. Testing Your Fixes

After making changes:
1. Check the app in light mode - should still look good
2. Switch to dark mode - backgrounds should be dark, text should be light
3. Verify all text is readable
4. Check that borders are visible but subtle

### 8. Example Before/After

**StoryEditor.tsx Before:**
```tsx
<Box borderBottomWidth="1px" borderColor="gray.200" bg="white">
  <Box bg="gray.50" borderRight="1px" borderColor="gray.200">
    <NodeTree />
  </Box>
  <Box overflowY="auto" bg="white">
    <NodeEditor />
  </Box>
</Box>
```

**StoryEditor.tsx After:**
```tsx
<Box borderBottomWidth="1px" borderColor="border">
  <Box bg="bg.subtle" borderRight="1px" borderColor="border">
    <NodeTree />
  </Box>
  <Box overflowY="auto">
    <NodeEditor />
  </Box>
</Box>
```

## Quick Reference: Color Mapping

| Old (Light Mode Only) | New (Theme-Aware) |
|----------------------|-------------------|
| `bg="white"` | Remove or `bg="bg"` |
| `bg="gray.50"` | `bg="bg.subtle"` |
| `bg="gray.100"` | `bg="bg.muted"` |
| `color="gray.600"` | `color="fg.muted"` |
| `color="gray.500"` | `color="fg.subtle"` |
| `borderColor="gray.200"` | `borderColor="border"` |
| `borderColor="gray.300"` | `borderColor="border.emphasized"` |

## Priority Order for Fixing

1. **StoryEditor.tsx** - Main layout (highest visibility)
2. **NodeEditor.tsx** - Content area
3. **PropertiesPanel.tsx** - Right panel
4. **NodeTree.tsx** - Left panel
5. **StoryCard.tsx** - List view
6. All other Story components

Start from the top and work down for maximum visual improvement.
