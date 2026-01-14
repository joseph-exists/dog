# Chakra → Tailwind Conversion Example

## Before: Chakra UI Component

```tsx
// Message.tsx - BEFORE (Chakra)
import { Box, HStack, Text } from "@chakra-ui/react"

const Message = ({ message, isStreaming = false }) => {
  return (
    <Box
      position="relative"
      alignSelf={message.sender_type === "user" ? "flex-end" : "flex-start"}
      maxW="70%"
      p={3}
      borderRadius="md"
      bg={
        message.is_own_message
          ? "blue.600"
          : message.sender_type === "agent"
            ? "gray.200"
            : "blue.500"
      }
      color={message.sender_type === "agent" ? "black" : "white"}
      _dark={{
        bg: message.is_own_message
          ? "blue.700"
          : message.sender_type === "agent"
            ? "gray.700"
            : "blue.600",
        color: "white",
      }}
      wordBreak="break-word"
      borderWidth={isStreaming ? 2 : 0}
      borderColor={isStreaming ? "blue.400" : "transparent"}
    >
      <Text fontSize="xs" opacity={0.8} mb={1} fontWeight="medium">
        {message.sender_name}
      </Text>

      <HStack gap={2} mb={2} flexWrap="wrap">
        {/* badges */}
      </HStack>

      <Text whiteSpace="pre-wrap">{message.content}</Text>

      <Text fontSize="xs" opacity={0.6} mt={1}>
        {formatTimestamp(message.created_at)}
      </Text>
    </Box>
  )
}
```

## After: Tailwind + shadcn

```tsx
// Message.tsx - AFTER (Tailwind)
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"

interface MessageProps {
  message: MessageViewModel
  isStreaming?: boolean
}

const Message = ({ message, isStreaming = false }: MessageProps) => {
  // Compute style variants
  const isOwnMessage = message.is_own_message
  const isAgent = message.sender_type === "agent"

  return (
    <div
      className={cn(
        // Base layout
        "relative max-w-[70%] p-3 rounded-md break-words",
        // Alignment based on sender
        isAgent ? "self-start" : "self-end",
        // Background colors
        isOwnMessage
          ? "bg-primary text-primary-foreground"
          : isAgent
            ? "bg-muted text-foreground"
            : "bg-primary/90 text-primary-foreground",
        // Streaming animation
        isStreaming && "border-2 border-primary/50 animate-pulse"
      )}
    >
      {/* Sender name */}
      <p className="text-xs opacity-80 mb-1 font-medium">
        {message.sender_name}
        {isStreaming && (
          <span className="ml-2 text-xs opacity-60">typing...</span>
        )}
      </p>

      {/* Status badges */}
      <div className="flex gap-2 mb-2 flex-wrap">
        {/* Use shadcn Badge */}
      </div>

      {/* Message content */}
      <p className="whitespace-pre-wrap">{message.content}</p>

      {/* Timestamp */}
      <p className="text-xs opacity-60 mt-1">
        {isStreaming ? "streaming..." : formatTimestamp(message.created_at)}
      </p>
    </div>
  )
}

export default Message
```

## Conversion Mapping Applied

| Chakra | Tailwind | Notes |
|--------|----------|-------|
| `<Box>` | `<div>` | Basic container |
| `<HStack gap={2}>` | `<div className="flex gap-2">` | Flex row |
| `<Text>` | `<p>` or `<span>` | Semantic HTML |
| `position="relative"` | `relative` | Position utility |
| `alignSelf="flex-end"` | `self-end` | Flexbox alignment |
| `maxW="70%"` | `max-w-[70%]` | Arbitrary value |
| `p={3}` | `p-3` | Spacing scale |
| `borderRadius="md"` | `rounded-md` | Border radius |
| `bg="blue.600"` | `bg-primary` | Semantic color |
| `bg="gray.200"` | `bg-muted` | Semantic color |
| `color="white"` | `text-primary-foreground` | Semantic text |
| `_dark={{ bg: "gray.700" }}` | (automatic via CSS vars) | No need - handled by theme |
| `wordBreak="break-word"` | `break-words` | Text wrapping |
| `fontSize="xs"` | `text-xs` | Font size |
| `opacity={0.8}` | `opacity-80` | Opacity |
| `mb={1}` | `mb-1` | Margin |
| `fontWeight="medium"` | `font-medium` | Font weight |
| `whiteSpace="pre-wrap"` | `whitespace-pre-wrap` | Whitespace |
| `borderWidth={2}` (conditional) | `border-2` via cn() | Conditional class |
| `as="span"` | Just use `<span>` | Direct element |

## Key Principles

### 1. Use Semantic Colors
```tsx
// ❌ Don't use specific colors
"bg-blue-600"
"text-gray-400"

// ✅ Use semantic tokens
"bg-primary"
"text-muted-foreground"
```

### 2. Dark Mode is Automatic
```tsx
// ❌ Don't manually specify dark variants for themed colors
"bg-blue-600 dark:bg-blue-700"

// ✅ Semantic colors auto-switch
"bg-primary"  // Works in both light and dark
```

### 3. Use cn() for Conditionals
```tsx
// ❌ Don't use ternary in className string
className={`p-4 ${isActive ? "bg-blue-500" : "bg-gray-200"}`}

// ✅ Use cn() helper
className={cn(
  "p-4",
  isActive ? "bg-primary" : "bg-muted"
)}
```

### 4. Use Arbitrary Values Sparingly
```tsx
// ✅ Prefer Tailwind scale values
"max-w-md"     // 28rem
"w-64"         // 16rem
"gap-4"        // 1rem

// ⚠️ Use arbitrary only when needed
"max-w-[70%]"  // Specific percentage
"h-[calc(100vh-4rem)]"  // Complex calc
```

### 5. Remove Unnecessary Wrappers
```tsx
// ❌ Chakra often needs wrappers
<Box>
  <Flex>
    <Text>Hello</Text>
  </Flex>
</Box>

// ✅ Tailwind can combine
<div className="flex">
  <p>Hello</p>
</div>
```
