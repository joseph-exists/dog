# Branching Stories E2E Test Suite

Comprehensive end-to-end tests for multibranching CYOA stories with state management, conditional branching, room integration, and publishing workflows.

## Overview

This test suite creates and validates four complete branching story scenarios that test all aspects of the CYOA system identified in `BRANCH_TESTS.md`:

1. **The Enchanted Forest** - Basic branching with 3 paths
2. **The Dragon's Hoard** - State-conditional branching
3. **The Time Traveler's Dilemma** - Deep branching (3 levels)
4. **The Detective's Case** - State accumulation and conditional endings

## Features Tested

### ✅ True Story Branching
- Multiple author-defined choices from same node
- Different choices lead to different nodes
- Each path has unique subsequent options
- State changes differ based on branch taken

### ✅ State Management
- **State Changes** (`sets_state`) - Choices modify story state
- **State Conditionals** (`requires_state`) - Choices gated by state
- **State Accumulation** - Multiple choices build up state over time
- **Complex State Logic** - Combinations of state determine outcomes

### ✅ Story Publishing
- Stories are published before gameplay
- Published stories become immutable
- Version control validation

### ✅ Room Integration
- Stories associated with rooms via `story_id`
- Rooms created for each test story
- Room-story relationship validation

### ✅ UserPersona Integration
- Stories assigned to personas
- Progress tracking per persona
- Multiple personas can play same story with independent state

## Test Stories

### Story 1: The Enchanted Forest
**Concept:** A mystical forest with three distinct paths

**Structure:**
```
Start: Forest Entrance (3 choices)
├─ Shadow Path → Shadow Guardian (END)
├─ Sunlit Grove → Nature's Friend (END)
└─ Arcane Gateway → Arcane Master (END)
```

**Tests:**
- Basic 3-way branching
- Simple state tracking (`path`, `courage`, `kindness`, `wisdom`)
- All 3 paths lead to different endings
- State persistence across choices

**Story Elements:**
- Dark/mysterious shadow path with transformation
- Nature/harmony path with magical wildlife
- Arcane/magic path with ancient knowledge

### Story 2: The Dragon's Hoard
**Concept:** Navigate a dragon's lair using different approaches

**Structure:**
```
Start: Dragon's Lair Entrance (3 approaches)
├─ Strength Approach → Inside Lair
│  ├─ Warrior's Challenge
│  │  ├─ Fight → Victor's Spoils (END)
│  │  └─ Alliance → Warrior's Wisdom (END)
├─ Stealth Approach → Inside Lair
│  ├─ Shadow Thief
│  │  ├─ Escape → Master Thief (END)
│  │  └─ Greedy → Thief's Bargain (END)
└─ Diplomacy Approach → Inside Lair
   └─ Diplomatic Approach → Dragon's Friend (END)
```

**Tests:**
- State-conditional branching (`requires_state`)
- Same node shows different choices based on approach
- 6 different endings based on path combinations
- Complex state tracking (`approach`, `warrior_spirit`, `shadow_affinity`, `wisdom`)

**Story Elements:**
- Warrior path with combat or honor choices
- Stealth path with escape or risk decisions
- Diplomatic path with wisdom and respect

### Story 3: The Time Traveler's Dilemma
**Concept:** Time travel across three historical eras

**Structure:**
```
Start: The Time Machine (3 eras)
├─ Medieval (1350 AD)
│  ├─ Knight Path → Tournament → Knighted Hero (END)
│  └─ Scholar Path → Library → Keeper of Knowledge (END)
├─ Wild West (1880 AD)
│  ├─ Lawman Path → Sheriff → Hero of the West (END)
│  └─ Outlaw Path → Gang → Legend of the West (END)
└─ Ancient Egypt (2500 BC)
   ├─ Priest Path → Temple → Divine Visitor (END)
   └─ Builder Path → Pyramids → Master Builder (END)
```

**Tests:**
- Deep branching (3 decision layers)
- Era selection → Role selection → Outcome
- 6 unique endings
- Complex nested state (`era`, `time_period`, `role`, `outcome`)
- State inheritance across decision layers

**Story Elements:**
- Medieval: Knighthood or scholarship in castle setting
- Wild West: Law enforcement or outlaws in frontier town
- Ancient Egypt: Divine worship or architectural mastery

### Story 4: The Detective's Case
**Concept:** Murder mystery with clue-based deduction

**Structure:**
```
Start: Crime Scene (3 investigation choices)
├─ Study → finds letter + window clues
├─ Bedroom → finds medicine + poison clues
└─ Garden → finds footprints + blood clues
     ↓
All paths → Making the Accusation (3 suspects)
├─ Accuse Wife
│  ├─ (with medicine + letter) → Justice Served (END)
│  └─ (without clues) → False Accusation (END)
├─ Accuse Partner
│  ├─ (with window + letter) → Justice Served (END)
│  └─ (without clues) → False Accusation (END)
└─ Accuse Maid
   ├─ (with footprints + blood) → Justice Served (END)
   └─ (without clues) → False Accusation (END)
```

**Tests:**
- State accumulation (gathering clues)
- Conditional endings based on clues collected
- Multiple `requires_state` combinations
- 6 possible endings (3 correct, 3 wrong accusations)
- Complex boolean state logic

**Story Elements:**
- Three suspects with motives
- Three investigation locations
- Clue combinations determine truth
- Detective career stakes

## Usage

### Run All Tests
```bash
python test_branching_stories.py
```

### Run with Verbose Output
```bash
python test_branching_stories.py --verbose
```

### Run Specific Story Test
```bash
# Test only The Enchanted Forest
python test_branching_stories.py --story forest

# Test only The Dragon's Hoard
python test_branching_stories.py --story dragon

# Test only The Time Traveler's Dilemma
python test_branching_stories.py --story time

# Test only The Detective's Case
python test_branching_stories.py --story detective
```

### Use Existing Persona
```bash
python test_branching_stories.py --persona-id YOUR-PERSONA-UUID
```

### Keep Created Entities (No Cleanup)
```bash
python test_branching_stories.py --no-cleanup
```

## Prerequisites

1. **Backend server running** on `http://localhost:8000`
2. **Test credentials** in `test.env` file:
   ```bash
   TEST_USER_EMAIL=test@example.com
   TEST_USER_PASSWORD=yourpassword
   ```
3. **Database migrations** applied (all CYOA phases)
4. **Python packages**: requests

## Output

### Console Output
```
======================================================================
  BRANCHING STORIES E2E TEST SUITE
  Testing multibranching CYOA stories
======================================================================

==================================================================
  Story 1: The Enchanted Forest
  Basic branching with state tracking
==================================================================
  ✅ PASSED: enchanted_forest_complete
     Successfully created and tested 3-path branching story

==================================================================
  Story 2: The Dragon's Hoard
  State-conditional branching
==================================================================
  ✅ PASSED: dragons_hoard_complete
     Successfully created and tested state-conditional branching

[... etc ...]

======================================================================
  TEST SUMMARY
======================================================================
  Stories Created: 4
  Total Tests:     4
  ✅ Passed:        4
  ❌ Failed:        0
  Success Rate:    100.0%
  Duration:        45.23s

  Results saved to: test_results_branching_stories.json

  Created Stories:
    - The Enchanted Forest
      Story ID: abc123...
      Room ID:  def456...
    - The Dragon's Hoard
      Story ID: ghi789...
      Room ID:  jkl012...
    [...]
======================================================================
```

### JSON Output File
`test_results_branching_stories.json` contains:

```json
{
  "test_suite": "Branching Stories E2E Test Suite",
  "start_time": "2026-01-08T10:30:00",
  "end_time": "2026-01-08T10:30:45",
  "duration_seconds": 45.23,
  "stories_created": [
    {
      "name": "The Enchanted Forest",
      "story_id": "abc123...",
      "room_id": "def456...",
      "branches": 3,
      "endings": 3
    },
    {
      "name": "The Dragon's Hoard",
      "story_id": "ghi789...",
      "room_id": "jkl012...",
      "branches": 3,
      "conditional_branches": 6,
      "endings": 6
    },
    {
      "name": "The Time Traveler's Dilemma",
      "story_id": "mno345...",
      "room_id": "pqr678...",
      "branches": 3,
      "sub_branches": 6,
      "depth": 3,
      "endings": 6
    },
    {
      "name": "The Detective's Case",
      "story_id": "stu901...",
      "room_id": "vwx234...",
      "investigation_paths": 3,
      "endings": 6,
      "state_complexity": "high - clue accumulation"
    }
  ],
  "total_tests": 4,
  "passed": 4,
  "failed": 0,
  "success_rate": "100.0%",
  "tests": [
    {
      "name": "enchanted_forest_complete",
      "passed": true,
      "message": "Successfully created and tested 3-path branching story",
      "details": {},
      "timestamp": "2026-01-08T10:30:15"
    },
    // ... etc
  ]
}
```

## What This Tests vs. BRANCH_TESTS.md Requirements

| Requirement | Status | Test Story |
|-------------|--------|------------|
| Node with 2+ choices | ✅ All | All stories |
| User sees multiple choices and picks one | ✅ All | All stories |
| Different choices → different nodes | ✅ All | All stories |
| State changes differ by branch | ✅ All | Forest, Dragon, Time |
| Undo returns with all options available | ⚠️ Manual | (Timeline tested in test_story_system.py) |
| Deep branching (branches that branch) | ✅ Yes | Time Traveler, Dragon |
| State-based conditionals | ✅ Yes | Dragon, Detective |
| State accumulation | ✅ Yes | Detective |
| Publishing workflow | ✅ All | All stories |
| Room integration | ✅ All | All stories |
| Persona assignment | ✅ All | All stories |

## Test Coverage Statistics

### Branching Complexity
- **Total Stories:** 4
- **Total Branches:** 12 initial branches
- **Total Sub-branches:** 12 additional branches
- **Total Endings:** 21 unique endings
- **Average Depth:** 2.5 decision layers
- **State Conditionals:** 15+ `requires_state` checks

### Story State Complexity
- **Simple State:** Forest (3 keys per path)
- **Medium State:** Time Traveler (4-5 keys per path)
- **Complex State:** Dragon (conditional branching)
- **Advanced State:** Detective (accumulation + combinations)

### API Endpoints Exercised
- `POST /api/v1/stories` - Story creation
- `POST /api/v1/stories/nodes` - Node creation
- `POST /api/v1/stories/choices` - Choice creation
- `POST /api/v1/stories/{id}/publish` - Publishing
- `POST /api/v1/rooms` - Room creation
- `POST /api/v1/stories/{id}/start` - Progress start
- `POST /api/v1/stories/progress/{id}/choose/{choice_id}` - Make choice
- `GET /api/v1/stories/progress/{id}/current` - Get current node

## Debugging

### Enable Verbose Mode
```bash
python test_branching_stories.py --verbose
```

Shows detailed debug info:
- Node creation confirmations
- Choice creation details
- State changes at each step
- API request/response details

### Common Issues

**"Authentication Error"**
- Check `test.env` exists with valid credentials
- Verify backend is running on port 8000
- Test auth: `python auth_helper.py`

**"Failed to publish story"**
- Ensure story has at least one start node
- Verify all choices reference valid nodes
- Check story version is correct (v1)

**"No valid choices for {approach} path"**
- Indicates `requires_state` condition not met
- Check that previous choice set required state
- Verify state keys match exactly (case-sensitive)

**"State not set correctly"**
- Check `sets_state` in choice creation
- Verify choice was actually made
- Inspect `story_state` in progress response

### Inspecting Created Stories

After running tests, use the story IDs from output:

```bash
# Get story details
curl http://localhost:8000/api/v1/stories/{story_id}

# Get all nodes
curl http://localhost:8000/api/v1/stories/{story_id}/nodes

# Get all choices
curl http://localhost:8000/api/v1/stories/{story_id}/choices

# Get room details
curl http://localhost:8000/api/v1/rooms/{room_id}
```

## Integration with Other Tests

These tests complement existing test suites:

- **test_story_system.py** - Tests timeline navigation, undo/redo, breadcrumbs
- **test_room_unit.py** - Tests room creation, participants, messages
- **Backend unit tests** - Test individual API endpoints

Together, they provide comprehensive CYOA system validation.

## Future Enhancements

Potential additions to this test suite:

1. **UserPersona Requirements Testing**
   - Stories with `StoryRequirement` conditions
   - Test persona traits/qualities gating access
   - Multiple personas with different requirements

2. **Convergent Branching**
   - Multiple paths leading to same node
   - Diamond-shaped story structures
   - State reconciliation at convergence

3. **Loop Detection**
   - Circular story paths
   - Intentional loops (return to earlier nodes)
   - Maximum choice limit testing

4. **Performance Testing**
   - Large branching stories (50+ nodes)
   - Deep nesting (10+ levels)
   - State with many keys (100+)

5. **Error Handling**
   - Invalid choice selections
   - Missing required state
   - Attempting to modify published stories

6. **Timeline Integration**
   - Test undo after branching choices
   - Test jump to specific branch points
   - Verify breadcrumbs show correct path

## Contributing

When adding new test stories:

1. **Use Real Story Content** - No placeholder text
2. **Test Specific Features** - Each story should validate distinct functionality
3. **Document State Logic** - Clearly explain state conditions
4. **Include Multiple Endings** - Demonstrate true branching
5. **Create Associated Room** - Test room integration
6. **Test Complete Playthrough** - Verify at least one full path

## Exit Codes

- **0** - All tests passed
- **1** - One or more tests failed or fatal error

## License

Part of the TinyFoot CYOA system test suite.
