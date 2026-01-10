import type { StoryNodePublic, NodeChoicePublic } from "@/client"

export interface TreeNode {
  node: StoryNodePublic
  children: TreeNode[]
  level: number
  isExpanded: boolean
}

/**
 * Builds a hierarchical tree structure from nodes and choices
 * Starts from the start node and recursively builds the tree
 */
export function buildNodeTree(
  nodes: StoryNodePublic[],
  choices: NodeChoicePublic[]
): TreeNode | null {
  const startNode = nodes.find((n) => n.is_start_node)
  if (!startNode) return null

  // Build adjacency map: nodeId -> choices from that node
  const adjacencyMap = new Map<string, NodeChoicePublic[]>()
  choices.forEach((choice) => {
    const existing = adjacencyMap.get(choice.from_node_id) || []
    existing.push(choice)
    adjacencyMap.set(choice.from_node_id, existing)
  })

  // Sort choices by order
  adjacencyMap.forEach((choiceList) => {
    choiceList.sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
  })

  const visited = new Set<string>()

  function buildSubtree(node: StoryNodePublic, level: number): TreeNode {
    visited.add(node.id)

    const children: TreeNode[] = []
    const outgoingChoices = adjacencyMap.get(node.id) || []

    for (const choice of outgoingChoices) {
      // Avoid infinite loops - don't revisit nodes
      if (!visited.has(choice.to_node_id)) {
        const childNode = nodes.find((n) => n.id === choice.to_node_id)
        if (childNode) {
          children.push(buildSubtree(childNode, level + 1))
        }
      }
    }

    return {
      node,
      children,
      level,
      isExpanded: true, // Default to expanded
    }
  }

  return buildSubtree(startNode, 0)
}

/**
 * Flattens the tree into a linear array for rendering
 * Respects the expanded/collapsed state
 */
export function flattenTree(tree: TreeNode | null): TreeNode[] {
  if (!tree) return []

  const result: TreeNode[] = []

  function traverse(node: TreeNode) {
    result.push(node)
    if (node.isExpanded) {
      node.children.forEach(traverse)
    }
  }

  traverse(tree)
  return result
}

/**
 * Toggles the expanded state of a node in the tree
 */
export function toggleNodeExpansion(
  tree: TreeNode | null,
  nodeId: string
): TreeNode | null {
  if (!tree) return null

  function toggle(node: TreeNode): TreeNode {
    if (node.node.id === nodeId) {
      return { ...node, isExpanded: !node.isExpanded }
    }
    return {
      ...node,
      children: node.children.map(toggle),
    }
  }

  return toggle(tree)
}

/**
 * Finds all node IDs in the path from root to a specific node
 * Used for highlighting the active path
 */
export function findPathToNode(
  tree: TreeNode | null,
  nodeId: string
): string[] {
  if (!tree) return []

  function search(node: TreeNode, path: string[]): string[] | null {
    const currentPath = [...path, node.node.id]

    if (node.node.id === nodeId) {
      return currentPath
    }

    for (const child of node.children) {
      const foundPath = search(child, currentPath)
      if (foundPath) return foundPath
    }

    return null
  }

  return search(tree, []) || []
}

/**
 * Gets all orphaned nodes (nodes not in the tree)
 */
export function getOrphanedNodes(
  nodes: StoryNodePublic[],
  tree: TreeNode | null
): StoryNodePublic[] {
  if (!tree) return nodes

  const nodesInTree = new Set<string>()

  function traverse(node: TreeNode) {
    nodesInTree.add(node.node.id)
    node.children.forEach(traverse)
  }

  traverse(tree)

  return nodes.filter((node) => !nodesInTree.has(node.id))
}
