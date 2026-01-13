/**
 * State Condition Evaluators
 *
 * Provides functions to evaluate conditional logic for story choices
 * and apply state mutations.
 *
 * Supports:
 * - Simple equality (backward compatible): { key: value }
 * - Comparison operators: { key: { $gte: 10 } }
 * - Logical operators: { $and: [...] }, { $or: [...] }, { $not: {...} }
 * - Mutation operators: { key: { $inc: 5 } }, { key: { $toggle: true } }
 */

// Type definitions
export type Primitive = string | number | boolean | null | undefined

export type ComparisonOperator =
  | "$eq"
  | "$ne"
  | "$gt"
  | "$gte"
  | "$lt"
  | "$lte"
  | "$in"
  | "$nin"
  | "$exists"

export type MutationOperator = "$set" | "$inc" | "$dec" | "$toggle" | "$unset"

export type LogicalOperator = "$and" | "$or" | "$not"

export interface OperatorCondition {
  $eq?: Primitive
  $ne?: Primitive
  $gt?: number
  $gte?: number
  $lt?: number
  $lte?: number
  $in?: Primitive[]
  $nin?: Primitive[]
  $exists?: boolean
}

export interface MutationOperation {
  $set?: Primitive
  $inc?: number
  $dec?: number
  $toggle?: boolean
  $unset?: boolean
}

export type ConditionValue = Primitive | OperatorCondition

export type StateConditions = Record<string, ConditionValue> & {
  $and?: StateConditions[]
  $or?: StateConditions[]
  $not?: StateConditions
}

export type StateMutations = Record<string, Primitive | MutationOperation>

// Helper to check if value is an operator object
function isOperatorObject(value: unknown): value is OperatorCondition {
  if (typeof value !== "object" || value === null) return false
  const keys = Object.keys(value)
  return keys.length > 0 && keys.every((k) => k.startsWith("$"))
}

function isMutationObject(value: unknown): value is MutationOperation {
  if (typeof value !== "object" || value === null) return false
  const keys = Object.keys(value)
  const mutationOps = ["$set", "$inc", "$dec", "$toggle", "$unset"]
  return keys.length > 0 && keys.some((k) => mutationOps.includes(k))
}

/**
 * Evaluate a single condition against a value from player state
 */
export function evaluateCondition(
  condition: ConditionValue,
  stateValue: unknown,
): boolean {
  // Simple equality (backward compatible)
  if (!isOperatorObject(condition)) {
    return stateValue === condition
  }

  // Operator-based condition
  const ops = condition as OperatorCondition

  // $exists - check if variable is defined
  if (ops.$exists !== undefined) {
    const exists = stateValue !== undefined && stateValue !== null
    return ops.$exists ? exists : !exists
  }

  // $eq - equals
  if (ops.$eq !== undefined) {
    return stateValue === ops.$eq
  }

  // $ne - not equals
  if (ops.$ne !== undefined) {
    return stateValue !== ops.$ne
  }

  // Numeric comparisons
  const numValue = Number(stateValue)
  const isNumeric = typeof stateValue === "number" || !isNaN(numValue)

  // $gt - greater than
  if (ops.$gt !== undefined) {
    if (!isNumeric) return false
    return numValue > ops.$gt
  }

  // $gte - greater than or equal
  if (ops.$gte !== undefined) {
    if (!isNumeric) return false
    return numValue >= ops.$gte
  }

  // $lt - less than
  if (ops.$lt !== undefined) {
    if (!isNumeric) return false
    return numValue < ops.$lt
  }

  // $lte - less than or equal
  if (ops.$lte !== undefined) {
    if (!isNumeric) return false
    return numValue <= ops.$lte
  }

  // $in - value in array
  if (ops.$in !== undefined) {
    return ops.$in.includes(stateValue as Primitive)
  }

  // $nin - value not in array
  if (ops.$nin !== undefined) {
    return !ops.$nin.includes(stateValue as Primitive)
  }

  // Unknown operator - default to false
  return false
}

/**
 * Evaluate a full requires_state object against player state
 * Supports logical operators ($and, $or, $not)
 */
export function evaluateRequiresState(
  requires: StateConditions | null | undefined,
  state: Record<string, unknown>,
): boolean {
  // No conditions = always true
  if (!requires || Object.keys(requires).length === 0) {
    return true
  }

  // Process each key in the conditions
  for (const [key, condition] of Object.entries(requires)) {
    // Handle logical operators
    if (key === "$and") {
      const andConditions = condition as StateConditions[]
      const allTrue = andConditions.every((c) =>
        evaluateRequiresState(c, state),
      )
      if (!allTrue) return false
      continue
    }

    if (key === "$or") {
      const orConditions = condition as StateConditions[]
      const anyTrue = orConditions.some((c) => evaluateRequiresState(c, state))
      if (!anyTrue) return false
      continue
    }

    if (key === "$not") {
      const notCondition = condition as StateConditions
      if (evaluateRequiresState(notCondition, state)) return false
      continue
    }

    // Skip other $ prefixed keys (reserved for future use)
    if (key.startsWith("$")) continue

    // Regular variable condition
    const stateValue = state[key]
    if (!evaluateCondition(condition as ConditionValue, stateValue)) {
      return false
    }
  }

  return true
}

/**
 * Apply a single mutation to a value
 */
export function applyMutation(
  mutation: Primitive | MutationOperation,
  currentValue: unknown,
): unknown {
  // Simple set (backward compatible)
  if (!isMutationObject(mutation)) {
    return mutation
  }

  const ops = mutation as MutationOperation

  // $set - explicit set
  if (ops.$set !== undefined) {
    return ops.$set
  }

  // $unset - remove (return undefined)
  if (ops.$unset) {
    return undefined
  }

  // $toggle - flip boolean
  if (ops.$toggle) {
    return !currentValue
  }

  // $inc - increment number
  if (ops.$inc !== undefined) {
    const current = typeof currentValue === "number" ? currentValue : 0
    return current + ops.$inc
  }

  // $dec - decrement number
  if (ops.$dec !== undefined) {
    const current = typeof currentValue === "number" ? currentValue : 0
    return current - ops.$dec
  }

  // Unknown mutation - return current value unchanged
  return currentValue
}

/**
 * Apply a full sets_state object to player state
 * Returns a new state object (does not mutate input)
 */
export function applySetsState(
  sets: StateMutations | null | undefined,
  state: Record<string, unknown>,
): Record<string, unknown> {
  // No mutations = return state unchanged
  if (!sets || Object.keys(sets).length === 0) {
    return state
  }

  const newState = { ...state }

  for (const [key, mutation] of Object.entries(sets)) {
    // Skip $ prefixed keys (reserved)
    if (key.startsWith("$")) continue

    const newValue = applyMutation(mutation, state[key])

    if (newValue === undefined) {
      // $unset - remove the key
      delete newState[key]
    } else {
      newState[key] = newValue
    }
  }

  return newState
}

/**
 * Extract all variable keys from a conditions object
 * Useful for validation (finding undefined variables)
 */
export function extractVariableKeys(
  conditions: StateConditions | null | undefined,
): Set<string> {
  const keys = new Set<string>()

  if (!conditions) return keys

  for (const [key, value] of Object.entries(conditions)) {
    if (key === "$and" || key === "$or") {
      const nested = value as StateConditions[]
      for (const condition of nested) {
        for (const k of extractVariableKeys(condition)) {
          keys.add(k)
        }
      }
    } else if (key === "$not") {
      for (const k of extractVariableKeys(value as StateConditions)) {
        keys.add(k)
      }
    } else if (!key.startsWith("$")) {
      keys.add(key)
    }
  }

  return keys
}

/**
 * Check if a condition uses any operators (vs simple equality)
 */
export function hasOperators(
  conditions: StateConditions | null | undefined,
): boolean {
  if (!conditions) return false

  for (const [key, value] of Object.entries(conditions)) {
    if (key.startsWith("$")) return true
    if (isOperatorObject(value)) return true
  }

  return false
}

/**
 * Convert simple equality to explicit $eq operator
 * Useful for consistent UI representation
 */
export function normalizeCondition(condition: ConditionValue): OperatorCondition {
  if (isOperatorObject(condition)) {
    return condition
  }
  return { $eq: condition }
}

/**
 * Convert operator condition back to simple form if possible
 * Useful for cleaner JSON storage
 */
export function simplifyCondition(condition: OperatorCondition): ConditionValue {
  const keys = Object.keys(condition)
  if (keys.length === 1 && keys[0] === "$eq") {
    return condition.$eq as Primitive
  }
  return condition
}
