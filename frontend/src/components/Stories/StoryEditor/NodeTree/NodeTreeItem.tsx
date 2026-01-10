import { Box, HStack, Icon, Text } from "@chakra-ui/react"
import { FaFlag, FaTrophy, FaFileAlt, FaGripVertical } from "react-icons/fa"
import { useSortable } from "@dnd-kit/sortable"
import { CSS } from "@dnd-kit/utilities"

import type { StoryNodePublic } from "@/client"

interface NodeTreeItemProps {
  node: StoryNodePublic
  isSelected: boolean
  onClick: () => void
  level: number
}

const NodeTreeItem = ({ node, isSelected, onClick, level }: NodeTreeItemProps) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: node.id,
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  // Determine icon based on node type
  const getIcon = () => {
    if (node.is_start_node) return FaFlag
    if (node.is_end_node) return FaTrophy
    return FaFileAlt
  }

  // Determine icon color
  const getIconColor = () => {
    if (node.is_start_node) return "green.500"
    if (node.is_end_node) return "red.500"
    return "fg.muted"
  }

  return (
    <Box ref={setNodeRef} style={style}>
      <Box
        p={2}
        borderRadius="md"
        bg={isSelected ? "blue.subtle" : "transparent"}
        _hover={{ bg: isSelected ? "blue.subtle" : "bg.muted" }}
        cursor="pointer"
        onClick={onClick}
        transition="all 0.2s"
        borderWidth="1px"
        borderColor={isSelected ? "blue.solid" : "border"}
        opacity={level > 0 ? 0.95 : 1}
      >
        <HStack gap={2} align="center">
          {/* Drag Handle */}
          <Icon
            as={FaGripVertical}
            color="fg.subtle"
            boxSize={3}
            cursor="grab"
            _active={{ cursor: "grabbing" }}
            {...attributes}
            {...listeners}
          />

          {/* Node Icon */}
          <Icon as={getIcon()} color={getIconColor()} boxSize={4} flexShrink={0} />

          {/* Node Title */}
          <Text fontWeight={isSelected ? "bold" : "normal"} fontSize="sm" flex={1} truncate>
            {node.title}
          </Text>
        </HStack>
      </Box>
    </Box>
  )
}

export default NodeTreeItem
