● Stories Domain Deep Dive Analysis

  Documentation Quality: ✅ Good
  Doc: OutlineStoryAuthoring.md
  Purpose: Comprehensive implementation guide with domain concepts, use cases, architecture
  Quality: Excellent
  ────────────────────────────────────────
  Doc: story-author-editor-flow.md
  Purpose: Feature completion checklist for StoryPreview
  Quality: Good
  ────────────────────────────────────────
  Doc: story-state-schema/StoryStateSchema.md
  Purpose: Full-stack implementation plan
  Quality: Excellent
  ────────────────────────────────────────
  Doc: story-state-schema/ConditionalLogicExtension.md
  Purpose: Conditional logic design
  Quality: Good
  ────────────────────────────────────────
  Doc: from-legacy-*.md
  Purpose: Migration notes
  Quality: Reference only
  The docs are well-structured with domain concepts clearly explained (versioning, lifecycle states, etc.).

  ---
  Implementation Overview

  Scale: 21 components, 7 hooks

  src/components/Stories/
  ├── StoryList/           (3 files) - List, Card, CreateModal
  ├── StoryEditor/         (10 files)
  │   ├── NodeTree/        (2 files) - Tree, TreeItem
  │   ├── NodeEditor/      (4 files) - Editor, Form, Modal, ChoiceEditor
  │   └── StateSchema/     (3 files) - Editor, Dialog, Sheet
  ├── StoryPlayer/         (1 file) - StoryPreview
  ├── PublishWorkflow/     (2 files) - Modal, ValidationSummary
  ├── shared/              (4 files) - Editors, Toolbar, StateConditionEditor
  └── dialogs/             (1 file) - CreateStoryDialog

  src/hooks/stories/       (7 files)

  ---
  Compliance Analysis
  ┌────────────────────────┬────────────────┬─────────────────────────────────────────────┐
  │          Rule          │     Status     │                   Details                   │
  ├────────────────────────┼────────────────┼─────────────────────────────────────────────┤
  │ JSDoc Documentation    │ ⚠️ Partial     │ Components have it, hooks mostly missing    │
  ├────────────────────────┼────────────────┼─────────────────────────────────────────────┤
  │ TypeScript Interfaces  │ ✅ Pass        │ Props interfaces defined                    │
  ├────────────────────────┼────────────────┼─────────────────────────────────────────────┤
  │ Error Handling Pattern │ ⚠️ Issue       │ Module-level hook call in useStories.ts:15  │
  ├────────────────────────┼────────────────┼─────────────────────────────────────────────┤
  │ Query Keys             │ ✅ Pass        │ Hierarchical: ["stories", storyId, "nodes"] │
  ├────────────────────────┼────────────────┼─────────────────────────────────────────────┤
  │ Default Exports        │ ✅ Pass        │ Consistent                                  │
  ├────────────────────────┼────────────────┼─────────────────────────────────────────────┤
  │ Component Size (<300)  │ ❌ Violations  │ 3 files over limit                          │
  ├────────────────────────┼────────────────┼─────────────────────────────────────────────┤
  │ Import Order           │ ⚠️ Mixed       │ Some files have incorrect order             │
  ├────────────────────────┼────────────────┼─────────────────────────────────────────────┤
  │ ViewModels             │ ❌ Not used    │ Direct SDK types throughout                 │
  ├────────────────────────┼────────────────┼─────────────────────────────────────────────┤
  │ No Frontend Processing │ ⚠️ Intentional │ Validation logic with monitoring note       │
  ├────────────────────────┼────────────────┼─────────────────────────────────────────────┤
  │ Barrel Export          │ ❌ Missing     │ No index.ts for Stories (Agents has one)    │
  └────────────────────────┴────────────────┴─────────────────────────────────────────────┘
  ---
  Critical Issues

  1. Component Size Violations
  ┌─────────────────────────┬───────┬─────────┐
  │          File           │ Lines │ Over By │
  ├─────────────────────────┼───────┼─────────┤
  │ StateSchemaEditor.tsx   │ 384   │ 84      │
  ├─────────────────────────┼───────┼─────────┤
  │ ChoiceEditor.tsx        │ 362   │ 62      │
  ├─────────────────────────┼───────┼─────────┤
  │ StateVariableDialog.tsx │ 352   │ 52      │
  └─────────────────────────┴───────┴─────────┘
  2. Module-Level Hook Call (Anti-pattern)

  useStories.ts:15:
  // ❌ Called outside component - will break React rules
  const { showErrorToast } = useCustomToast()

  export const useCreateStory = () => {
    // Uses showErrorToast from module scope
  }

  Should be:
  export const useCreateStory = () => {
    const { showErrorToast } = useCustomToast()  // ✅ Inside hook
    // ...
  }

  3. Frontend Processing (Intentional)

  storyValidation.ts has a comment acknowledging this:
  // let's leave this here for now. I'm interested in monitoring its
  // performance, even though it's not strictly best practice. we do
  // have validation on the server...

  This includes:
  - Graph building (buildNodeGraph)
  - BFS traversal (findReachableNodes)
  - Validation logic (validateStoryForPublish)

  StoryCard.tsx also has date formatting:
  const formatDate = (dateString: string) => {
    // 15 lines of date transformation
  }

  4. No Barrel Export

  Unlike Agents which has a clean index.ts:
  // Agents has:
  import { AgentCard, AgentAvatar, ... } from "@/components/Agents"

  // Stories requires:
  import StoryCard from "@/components/Stories/StoryList/StoryCard"
  import StoryEditor from "@/components/Stories/StoryEditor/StoryEditor"
  // etc.

  ---
  Import Order Issues

  StoryEditor.tsx - Wrong order:
  import { useNavigate } from "@tanstack/react-router"  // Router before Query
  import { AlertTriangle, ... } from "lucide-react"      // Icons before React
  import { useState } from "react"

  Should be:
  import { useState } from "react"
  import { useNavigate } from "@tanstack/react-router"
  import { AlertTriangle, ... } from "lucide-react"

  ChoiceEditor.tsx - Correct pattern:
  import { zodResolver } from "@hookform/resolvers/zod"
  import { Trash2 } from "lucide-react"
  import { useEffect, useState } from "react"
  import { useForm } from "react-hook-form"

  ---
  ViewModels Assessment

  Stories uses raw SDK types throughout:
  - StoryPublic
  - StoryNodePublic
  - NodeChoicePublic
  - StoryStateVariablePublic

  Transformation happening in components:
  - StoryCard.tsx:111-123 - Date formatting
  - StoryCard.tsx:64-92 - Status badge logic
  - useStoryEditor.ts:31-36 - Node filtering by version

  These could move to a service layer, but per our earlier discussion, the pattern is acceptable for simpler domains.

  ---
  Recommendations

  High Priority:
  1. Fix module-level hook call in useStories.ts - This is a React rules violation
  2. Refactor oversized components - Extract sub-components from the 3 files over 300 lines

  Medium Priority:
  3. Add barrel export - Create src/components/Stories/index.ts
  4. Add JSDoc to hooks - useStoryEditor, useStoryNodes, etc. lack documentation
  5. Standardize import order - Several files have inconsistent ordering

  Low Priority / Acceptable:
  6. Frontend validation - Intentionally kept for performance monitoring, has server-side backup
  7. ViewModels - Current pattern is acceptable given minimal transformations

  ---
  Summary
  ┌────────────────────┬───────┐
  │       Aspect       │ Score │
  ├────────────────────┼───────┤
  │ Documentation      │ 8/10  │
  ├────────────────────┼───────┤
  │ Component Quality  │ 6/10  │
  ├────────────────────┼───────┤
  │ Pattern Compliance │ 5/10  │
  └────────────────────┴───────┘
  Main gaps:
  1. Module-level hook call (bug)
  2. 3 oversized components
  3. Missing barrel export
  4. Missing JSDoc on hooks

  The Stories domain is more complex than Agents and shows more pattern drift, likely due to being developed over a longer period
   with more contributors.