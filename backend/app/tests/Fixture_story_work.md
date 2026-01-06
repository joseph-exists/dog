  Problem 1: Fixture Story is Too Short

  Looking at the db_story_with_progress fixture (conftest.py:463-586), it creates:
  - 5 nodes (Start → Node2 → Node3 → Node4 → Node5)
  - 4 choices connecting them in a linear path
  - Node5 is an end node (no outgoing choices)

  The test tries to make 25 choices, but the loop breaks after 4 choices when it hits the end node:
  if not current_node["available_choices"]:
      break  # End node reached

  So the test only makes 4 choices, never reaching the 10-choice threshold for snapshot creation.

  Problem 2: No Snapshots Created

  Even if we made 10+ choices, it appears 0 snapshots were created, suggesting:
  1. The automatic snapshot creation logic may not be implemented yet, OR
  2. The snapshot logic exists but isn't being triggered correctly

  Solution A: Create a Longer Test Story Fixture (Recommended)

  Create a new fixture specifically for event sourcing tests that need many choices:

  @pytest.fixture(scope="function")
  def db_story_with_long_path(db: Session) -> tuple[Story, UserStoryProgress]:
      """Create a story with 50+ nodes for testing snapshots."""
      # Similar to db_story_with_progress, but create 50+ nodes in sequence
      # This allows tests to make 40+ choices to test snapshot intervals

 Solution B: Make Story Nodes Loop or Branch

 Create new fixtures that create story structures which allow 25+ choices:
  - Create nodes that branch and converge
  - Create a "loop" structure (though this might not fit CYOA semantics)
  - Create a very deep linear path (50+ nodes)

Solution C: Comment out specific test, migrate to new structure above once complete.