Analysis: Branching Node Choice Test Coverage

  After reviewing the test suite, I've identified a critical gap in test coverage for true story branching.

  Current State

  Fixture Structure (db_story_with_progress in conftest.py:403-586):
  - Creates a linear story: Start → Node2 → Node3 → Node4 → Node5
  - Each node has exactly ONE choice to the next node
  - No branching paths at all

  Test Patterns Across All Files:
  # Every test does this:
  choice_id = response.json()["available_choices"][0]["id"]  # Always [0]
  - No test ever accesses available_choices[1]
  - No test verifies len(available_choices) > 1
  - No test takes different paths from the same starting point

  "Branching" Tests (test_petri_timeline.py):
  - test_make_choice_after_undo_creates_branch - Tests abandoned branches (undo → new choice)
  - test_timeline_shows_active_path_only - Tests abandoned branches (undo → new choice)
  - These test navigation-created branches, NOT author-defined story branching

  What's Missing

  No tests for true CYOA branching where:
  1. ✗ A node has 2+ author-defined choices leading to different nodes
  2. ✗ User sees multiple available_choices and picks one
  3. ✗ Different choices lead to different subsequent nodes with different options
  4. ✗ State changes differ based on which branch is taken
  5. ✗ Undo from different branches returns to the same branch point with all options still available

  Recommended Test Cases

  You should add tests that verify:

  Test 1: Story with True Branching

  Start Node
  ├─ Choice A → "Go Left" → Left Branch Node → (more choices specific to left path)
  └─ Choice B → "Go Right" → Right Branch Node → (more choices specific to right path)

  What to test:
  - At Start Node, len(available_choices) == 2
  - Taking "Go Left" leads to Left Branch Node
  - Taking "Go Right" leads to Right Branch Node
  - Left Branch Node has different choices than Right Branch Node
  - State changes from "Go Left" vs "Go Right" are different

  Test 2: Multiple Choices with Different Outcomes

  - User makes Choice A from Node 1 → reaches Node A
  - Different user makes Choice B from Node 1 → reaches Node B
  - Verify Node A and Node B have different available_choices
  - Verify story_state differs based on choice made

  Test 3: Undo from Branch Still Shows All Branches

  - User at Start Node with choices A, B, C
  - User picks Choice A → reaches Node A
  - User undos back to Start Node
  - Verify all 3 choices (A, B, C) are still available
  - User picks Choice B → reaches Node B (different from Node A)

  Test 4: Deep Branching

  Start
  ├─ A → Node_A
  │   ├─ A1 → Node_A1
  │   └─ A2 → Node_A2
  └─ B → Node_B
      ├─ B1 → Node_B1
      └─ B2 → Node_B2
  - Verify state replay works correctly regardless of which path taken
  - Verify timeline shows correct path (e.g., Start → A → A2)

  Fixture Needed

  You'll need a new fixture like db_story_with_branching:
  Start Node (id: start_id)
  ├─ Choice "left" → Left Node → Choice "left_continue" → Left End
  └─ Choice "right" → Right Node → Choice "right_continue" → Right End

  Recommendation

  Create a new test file: test_story_branching.py with:
  1. New fixture db_story_with_branching that creates a tree structure (not linear)
  2. Tests that verify multiple choices are available
  3. Tests that verify different choices lead to different outcomes
  4. Tests that verify undo/jump work correctly with branching
  5. Tests that verify state replay works correctly for any branch