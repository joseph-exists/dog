 


 Phase 6:


  ★ Insight ─────────────────────────────────────
  StateConditionEditor design decisions:
  - Dual-mode architecture: The same component handles both requires_state (conditions) and sets_state (mutations) by swapping operator sets
  - Type coercion: Values are automatically converted based on variable type (string→number for numeric ops, etc.)
  - Schema integration: When a schema is provided, variables get autocomplete, type badges, and undefined warnings
  - Logical groups: Only enabled in "requires" mode since mutations don't need OR/AND grouping
  ─────────────────────────────────────────────────

  Summary of Phase 6 Changes

  Files Created

  src/utils/stateConditions.ts
  - Type definitions for operators (ComparisonOperator, MutationOperator, StateConditions, etc.)
  - Runtime evaluation functions (evaluateCondition, evaluateRequiresState, applyMutation, applySetsState)
  - Utility functions (extractVariableKeys)

  src/components/Stories/shared/StateConditionEditor.tsx
  - ~450 lines of comprehensive state condition editing UI
  - Features implemented:
    - Mode-based operator selection (comparison vs mutation operators)
    - Condition row management with key/operator/value
    - Logical groups ($and/$or) for complex conditions
    - Type-aware value inputs (boolean select, number input, enum dropdown)
    - Schema autocomplete integration
    - Duplicate key detection (red border)
    - Undefined variable warnings (orange border + icon)
    - JSON preview toggle

  Updated Files

  src/components/Stories/StoryEditor/NodeEditor/ChoiceEditor.tsx
  - Replaced simple key-value state entries with full StateConditionEditor integration
  - Added optional schema prop for variable autocomplete
  - Collapsible sections for requires/sets state



  ★ Insight ─────────────────────────────────────
  Debouncing in text editors:
  - Debouncing prevents excessive function calls during rapid typing
  - Default 0ms in RichTextEditor (immediate) for the NodeEditorForm auto-save use case
  - Default 300ms in TiptapEditor (standalone) for typical use cases
  - The timer is properly cleaned up on unmount to prevent memory leaks
  ─────────────────────────────────────────────────

  Phase 7 Final Status
  ┌────────────────────────┬─────────────┬──────────────────────────────────────────────────────────────────────────┐
  │          Task          │   Status    │                              Implementation                              │
  ├────────────────────────┼─────────────┼──────────────────────────────────────────────────────────────────────────┤
  │ 7.1 RichTextEditor.tsx │ ✅ Complete │ Toolbar + editor, min-height 300px, debounce support                     │
  ├────────────────────────┼─────────────┼──────────────────────────────────────────────────────────────────────────┤
  │ 7.2 TiptapToolbar.tsx  │ ✅ Complete │ Bold, italic, strike, code, H1-H3, lists, quote, code block, link, image │
  ├────────────────────────┼─────────────┼──────────────────────────────────────────────────────────────────────────┤
  │ 7.3 TiptapEditor.tsx   │ ✅ Complete │ Standalone editor, editable toggle, debounced onChange (300ms default)   │
  └────────────────────────┴─────────────┴──────────────────────────────────────────────────────────────────────────┘
  Files in src/components/Stories/shared/
  ┌──────────────────────────┬───────────────────────────────────────────────┐
  │           File           │                    Purpose                    │
  ├──────────────────────────┼───────────────────────────────────────────────┤
  │ RichTextEditor.tsx       │ Full editor with toolbar (for NodeEditorForm) │
  ├──────────────────────────┼───────────────────────────────────────────────┤
  │ TiptapEditor.tsx         │ Bare editor without toolbar (for embedding)   │
  ├──────────────────────────┼───────────────────────────────────────────────┤
  │ TiptapToolbar.tsx        │ Formatting toolbar component                  │
  ├──────────────────────────┼───────────────────────────────────────────────┤
  │ StateConditionEditor.tsx │ State conditions/mutations editor             │
  └──────────────────────────┴───────────────────────────────────────────────┘
  Key Features Added

  - Debounced onChange: Both editors now support optional debouncing via debounceMs prop
  - Dynamic editable toggle: Editors respond to editable prop changes at runtime
  - Timer cleanup: Proper cleanup on component unmount prevents memory leaks
  - SSR compatibility: immediatelyRender: false prevents hydration mismatches

