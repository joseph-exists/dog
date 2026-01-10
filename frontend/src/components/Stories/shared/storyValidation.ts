import type { StoryNodePublic, NodeChoicePublic } from "@/client"

export interface ValidationResult {
  isValid: boolean
  errors: string[]
  warnings: string[]
}

/**
 * Builds an adjacency list (graph) from choices
 * Maps: node_id -> array of destination node_ids
 */
export function buildNodeGraph(
  choices: NodeChoicePublic[]
): Map<string, string[]> {
  const graph = new Map<string, string[]>()

  choices.forEach((choice) => {
    const destinations = graph.get(choice.from_node_id) || []
    destinations.push(choice.to_node_id)
    graph.set(choice.from_node_id, destinations)
  })

  return graph
}

/**
 * Finds all nodes reachable from start node using BFS
 */
export function findReachableNodes(
  startNodeId: string,
  graph: Map<string, string[]>
): Set<string> {
  const visited = new Set<string>()
  const queue: string[] = [startNodeId]

  while (queue.length > 0) {
    const current = queue.shift()!
    visited.add(current)

    // Get outgoing edges from current node
    const destinations = graph.get(current) || []
    destinations.forEach((destId) => {
      if (!visited.has(destId) && !queue.includes(destId)) {
        queue.push(destId)
      }
    })
  }

  return visited
}

/**
 * Validates a story is ready for publishing
 * Checks for structural integrity, start/end nodes, and reachability
 */
export function validateStoryForPublish(
  // story: StoryPublic,
  nodes: StoryNodePublic[],
  choices: NodeChoicePublic[]
): ValidationResult {
  const errors: string[] = []
  const warnings: string[] = []

  // Check 1: Must have at least one node
  if (nodes.length === 0) {
    errors.push("Story must have at least one node")
    return { isValid: false, errors, warnings }
  }

  // Check 2: Must have exactly one start node
  const startNodes = nodes.filter((n) => n.is_start_node)
  if (startNodes.length === 0) {
    errors.push("Story must have exactly one start node")
  } else if (startNodes.length > 1) {
    errors.push(`Story has ${startNodes.length} start nodes, but must have exactly one`)
  }

  // Check 3: Must have at least one end node
  const endNodes = nodes.filter((n) => n.is_end_node)
  if (endNodes.length === 0) {
    errors.push("Story must have at least one end node")
  }

  // Check 4: All choices must have valid target nodes in same version
  const nodeIds = new Set(nodes.map((n) => n.id))
  choices.forEach((choice) => {
    if (!nodeIds.has(choice.to_node_id)) {
      errors.push(
        `Choice "${choice.text}" points to non-existent or wrong-version node`
      )
    }
  })

  // If we have errors so far, return early
  if (errors.length > 0) {
    return { isValid: false, errors, warnings }
  }

  // Check 5: All nodes should be reachable from start (warning only)
  const startNode = startNodes[0]
  const graph = buildNodeGraph(choices)
  const reachableNodes = findReachableNodes(startNode.id, graph)

  const orphanedNodes = nodes.filter(
    (node) => !reachableNodes.has(node.id) && node.id !== startNode.id
  )

  if (orphanedNodes.length > 0) {
    warnings.push(
      `${orphanedNodes.length} orphan node(s) detected (not reachable from start): ${orphanedNodes
        .map((n) => `"${n.title}"`)
        .join(", ")}`
    )
  }

  // Check 6: All non-end nodes should have at least one outgoing choice (warning)
  const nonEndNodes = nodes.filter((n) => !n.is_end_node)
  nonEndNodes.forEach((node) => {
    const outgoingChoices = choices.filter((c) => c.from_node_id === node.id)
    if (outgoingChoices.length === 0) {
      warnings.push(`Node "${node.title}" has no outgoing choices (dead end)`)
    }
  })

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
  }
}
