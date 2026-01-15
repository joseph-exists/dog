/**
 * State Condition Types and Evaluators
 *
 * Provides types and functions for conditional logic in story choices
 * and state mutations.
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
  if (!isOperatorObject(condition)) {
    return stateValue === condition
  }

  const ops = condition as OperatorCondition

  if (ops.$exists !== undefined) {
    const exists = stateValue !== undefined && stateValue !== null
    return ops.$exists ? exists : !exists
  }

  if (ops.$eq !== undefined) return stateValue === ops.$eq
  if (ops.$ne !== undefined) return stateValue !== ops.$ne

  const numValue = Number(stateValue)
  const isNumeric = typeof stateValue === "number" || !Number.isNaN(numValue)

  if (ops.$gt !== undefined) return isNumeric && numValue > ops.$gt
  if (ops.$gte !== undefined) return isNumeric && numValue >= ops.$gte
  if (ops.$lt !== undefined) return isNumeric && numValue < ops.$lt
  if (ops.$lte !== undefined) return isNumeric && numValue <= ops.$lte
  if (ops.$in !== undefined) return ops.$in.includes(stateValue as Primitive)
  if (ops.$nin !== undefined) return !ops.$nin.includes(stateValue as Primitive)

  return false
}

/**
 * Evaluate a full requires_state object against player state
 */
export function evaluateRequiresState(
  requires: StateConditions | null | undefined,
  state: Record<string, unknown>,
): boolean {
  if (!requires || Object.keys(requires).length === 0) return true

  for (const [key, condition] of Object.entries(requires)) {
    if (key === "$and") {
      const andConditions = condition as StateConditions[]
      if (!andConditions.every((c) => evaluateRequiresState(c, state)))
        return false
      continue
    }
    if (key === "$or") {
      const orConditions = condition as StateConditions[]
      if (!orConditions.some((c) => evaluateRequiresState(c, state)))
        return false
      continue
    }
    if (key === "$not") {
      if (evaluateRequiresState(condition as StateConditions, state))
        return false
      continue
    }
    if (key.startsWith("$")) continue

    const stateValue = state[key]
    if (!evaluateCondition(condition as ConditionValue, stateValue))
      return false
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
  if (!isMutationObject(mutation)) return mutation

  const ops = mutation as MutationOperation
  if (ops.$set !== undefined) return ops.$set
  if (ops.$unset) return undefined
  if (ops.$toggle) return !currentValue
  if (ops.$inc !== undefined) {
    return (typeof currentValue === "number" ? currentValue : 0) + ops.$inc
  }
  if (ops.$dec !== undefined) {
    return (typeof currentValue === "number" ? currentValue : 0) - ops.$dec
  }

  return currentValue
}

/**
 * Apply a full sets_state object to player state
 */
export function applySetsState(
  sets: StateMutations | null | undefined,
  state: Record<string, unknown>,
): Record<string, unknown> {
  if (!sets || Object.keys(sets).length === 0) return state

  const newState = { ...state }
  for (const [key, mutation] of Object.entries(sets)) {
    if (key.startsWith("$")) continue
    const newValue = applyMutation(mutation, state[key])
    if (newValue === undefined) {
      delete newState[key]
    } else {
      newState[key] = newValue
    }
  }

  return newState
}

/**
 * Extract all variable keys from a conditions object
 */
export function extractVariableKeys(
  conditions: StateConditions | null | undefined,
): Set<string> {
  const keys = new Set<string>()
  if (!conditions) return keys

  for (const [key, value] of Object.entries(conditions)) {
    if (key === "$and" || key === "$or") {
      for (const condition of value as StateConditions[]) {
        for (const k of extractVariableKeys(condition)) keys.add(k)
      }
    } else if (key === "$not") {
      for (const k of extractVariableKeys(value as StateConditions)) keys.add(k)
    } else if (!key.startsWith("$")) {
      keys.add(key)
    }
  }

  return keys
}
