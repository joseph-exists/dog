# Story Script Reference Card
## A Guide to Creating Complex Story Test Scripts

This reference card provides patterns and templates for creating sophisticated story test scripts that match the complexity and presentation standards found in the `formats/` and `carroll/` directories.

---

## Script Structure Template

### File Header Pattern
```python
#!/usr/bin/env python3
"""
[SCRIPT-ID]: [Title] - [Purpose Description]

[Detailed narrative description explaining what the story tests/demonstrates]

KEY CONCEPTS TESTED:
- [List of technical/narrative concepts being exercised]
- [Specific features being validated]

NARRATIVE THEMES:
- [Story themes and literary devices used]
- [Narrative techniques employed]

STORY STRUCTURE:
- [High-level description of branching structure]
- [State tracking mechanics]
- [Ending conditions/variations]

=============================================================================

Usage:
    python [script_name].py
    python [script_name].py --verbose

Output:
    test_results_[script_name].json
"""
```

### Core Imports & Configuration
```python
import json
import sys
import argparse
from datetime import datetime
from pathlib import Path

import requests

# Import auth helper
sys.path.append(str(Path(__file__).parent))
from auth_helper import get_authenticated_session, AuthenticationError

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
RESULTS_FILE = "test_results_[script_name].json"

# Test results tracking
test_results = {
    "test_suite": "[Test Suite Name]",
    "start_time": None,
    "end_time": None,
    "story_id": None,
    "node_ids": {},
    "choice_ids": {},
    "state_variable_ids": {},
    "success": False,
    "errors": []
}
```

---

## Builder Class Template

### Class Structure
```python
class [StoryName]Builder:
    """Builds the [Story Name] story demonstrating [key concepts]."""

    def __init__(self, session: requests.Session, verbose: bool = False):
        self.session = session
        self.verbose = verbose
        self.story_id = None
        self.nodes = {}
        self.choices = []
        self.state_vars = {}

    def log(self, message: str):
        print(f"  {message}")

    def debug(self, message: str):
        if self.verbose:
            print(f"  [DEBUG] {message}")
```

### Core API Methods (Standard Implementation)
```python
def create_story(self, title: str, description: str) -> dict:
    response = self.session.post(f"{BASE_URL}/stories", json={
        "title": title,
        "description": description,
        "current_version": 1
    })
    if response.status_code != 200:
        raise Exception(f"Failed to create story: {response.text}")
    return response.json()

def create_state_variable(self, key: str, value_type: str,
                         default_value=None, enum_values: list = None,
                         description: str = None, category: str = None) -> dict:
    payload = {
        "key": key,
        "value_type": value_type,
    }
    if default_value is not None:
        payload["default_value"] = default_value
    if enum_values:
        payload["enum_values"] = enum_values
    if description:
        payload["description"] = description
    if category:
        payload["category"] = category

    response = self.session.post(
        f"{BASE_URL}/stories/{self.story_id}/versions/1/state-schema",
        json=payload
    )
    if response.status_code != 200:
        raise Exception(f"Failed to create state variable '{key}': {response.text}")
    return response.json()

def create_node(self, title: str, content: str,
               is_start: bool = False, is_end: bool = False,
               content_format: str = "markdown") -> dict:
    response = self.session.post(f"{BASE_URL}/storynodes", json={
        "story_id": self.story_id,
        "story_version": 1,
        "title": title,
        "content": content,
        "node_type": "text",
        "content_format": content_format,
        "is_start_node": is_start,
        "is_end_node": is_end
    })
    if response.status_code != 200:
        raise Exception(f"Failed to create node '{title}': {response.text}")
    return response.json()

def create_choice(self, from_node_name: str, to_node_name: str,
                 text: str, order: int = 0,
                 requires_state: dict = None,
                 sets_state: dict = None) -> dict:
    from_node = self.nodes.get(from_node_name)
    to_node = self.nodes.get(to_node_name)

    if not from_node:
        raise Exception(f"From node '{from_node_name}' not found")
    if not to_node:
        raise Exception(f"To node '{to_node_name}' not found")

    payload = {
        "from_node_id": from_node["id"],
        "to_node_id": to_node["id"],
        "text": text,
        "order": order
    }
    if requires_state:
        payload["requires_state"] = requires_state
    if sets_state:
        payload["sets_state"] = sets_state

    response = self.session.post(f"{BASE_URL}/node-choices", json=payload)
    if response.status_code != 200:
        raise Exception(f"Failed to create choice '{text}': {response.text}")
    return response.json()

def validate_state_schema(self) -> dict:
    response = self.session.get(
        f"{BASE_URL}/stories/{self.story_id}/versions/1/state-schema/validate"
    )
    if response.status_code != 200:
        raise Exception(f"Failed to validate: {response.text}")
    return response.json()
```

---

## State Schema Patterns

### Basic State Variables
```python
# Progress tracking
self.state_vars["progress_counter"] = self.create_state_variable(
    key="pages_read",
    value_type="number",
    default_value=0,
    category="progress",
    description="Number of sections completed"
)

# Enum-based choices
self.state_vars["path_chosen"] = self.create_state_variable(
    key="initial_path",
    value_type="enum",
    enum_values=["path_a", "path_b", "path_c", "none"],
    default_value="none",
    category="choice",
    description="Which path the player chose first"
)

# Boolean flags
self.state_vars["discovery_made"] = self.create_state_variable(
    key="found_secret",
    value_type="boolean",
    default_value=False,
    category="discovery",
    description="Player discovered the hidden element"
)
```

### Complex State Logic Patterns
```python
# AND conditions
requires_state={
    "$and": [
        {"pages_read": {"$gte": 3}},
        {"found_secret": True}
    ]
}

# OR conditions  
requires_state={
    "$or": [
        {"initial_path": "path_a"},
        {"initial_path": "path_b"}
    ]
}

# Value matching
requires_state={
    "character_type": {"$in": ["scholar", "warrior"]}
}

# Negation
requires_state={
    "failed_attempt": {"$ne": True}
}
```

---

## Content Format Patterns

### Markdown Content (Standard)
```python
content = """# Chapter Title

**Bold text** for emphasis and important discoveries.
*Italic text* for thoughts, doubts, and uncertainties.
~~Strikethrough~~ for revised or abandoned ideas.

> Blockquotes for quoted material, inscriptions, or other voices.

## Subsection

- Bulleted lists for inventories
- Or observations
- Multiple items

1. Numbered lists for sequences
2. Or procedures
3. Step-by-step actions

---

*Horizontal rules separate major sections or indicate passage of time.*

**Key Discovery:** Important information that affects the story state.

![Description of image](image-reference.png)
*Caption explaining the diegetic meaning of the image*
"""
```

### HTML Content (Advanced Formatting)
```python
content = """<article class="report" data-classification="restricted">

<header>
  <h1>Document Title &mdash; Subtitle</h1>
  <p class="classification">RESTRICTED // EYES ONLY</p>
</header>

<section>
  <h2>Data Analysis</h2>
  <table class="data-table" data-source="collection-system">
    <thead>
      <tr>
        <th rowspan="2">Item</th>
        <th colspan="2">Analysis</th>
        <th rowspan="2">Status</th>
      </tr>
      <tr>
        <th>Primary</th>
        <th>Secondary</th>
      </tr>
    </thead>
    <tbody>
      <tr data-priority="high">
        <td>Critical Data Point</td>
        <td>Initial Assessment</td>
        <td>Corroborating Evidence</td>
        <td><span style="color:#c00;">URGENT</span></td>
      </tr>
    </tbody>
  </table>
</section>

<!-- Inline SVG for diagrams -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 200">
  <rect x="10" y="10" width="100" height="50" fill="#ddd"/>
  <text x="60" y="40" text-anchor="middle">Node A</text>
  <line x1="110" y1="35" x2="200" y2="35" stroke="#333"/>
</svg>

</article>"""
```

---

## Branching Patterns

### Linear Progression with State Accumulation
```python
# Node A → Node B → Node C → Ending
# Each choice adds to state

self.create_choice(
    from_node_name="node_a",
    to_node_name="node_b", 
    text="Investigate the library",
    sets_state={
        "locations_visited": 1,
        "knowledge_level": 1,
        "found_clue_library": True
    }
)
```

### Branching with Convergence
```python
# Multiple paths lead to same decision point
# State affects available choices at convergence

self.create_choice(
    from_node_name="path_a_end",
    to_node_name="decision_point",
    text="Approach the council",
    sets_state={"approach_method": "diplomatic"}
)

self.create_choice(
    from_node_name="path_b_end", 
    to_node_name="decision_point",
    text="Approach the council",
    sets_state={"approach_method": "forceful"}
)

# At decision_point, choices depend on approach_method
self.create_choice(
    from_node_name="decision_point",
    to_node_name="diplomatic_ending",
    text="Present your credentials",
    requires_state={"approach_method": "diplomatic"}
)
```

### Conditional Branching Networks
```python
# Complex state requirements for story progression

self.create_choice(
    from_node_name="investigation_hub",
    to_node_name="secret_revelation",
    text="Connect the evidence pieces",
    requires_state={
        "$and": [
            {"clues_found": {"$gte": 3}},
            {"$or": [
                {"investigation_skill": {"$gte": 2}},
                {"has_mentor_guidance": True}
            ]},
            {"trust_level": {"$ne": "suspicious"}}
        ]
    },
    sets_state={
        "major_revelation": True,
        "story_phase": "climax"
    }
)
```

---

## Testing & Validation Patterns

### Main Function Template
```python
def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create the [Story Name] story"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    test_results["start_time"] = datetime.now().isoformat()

    print("\n" + "=" * 70)
    print(f"  [TEST SUITE NAME]")
    print(f"  [Brief Description]")
    print("=" * 70)

    try:
        session = get_authenticated_session()
        print(f"\n✓ Authenticated successfully")

        builder = [StoryName]Builder(session, verbose=args.verbose)
        is_valid = builder.build_story()

        # Summary output
        print("\n" + "=" * 70)
        print("  STORY CREATION COMPLETE")
        print("=" * 70)
        print(f"\n  Story ID: {builder.story_id}")
        print(f"  Nodes created: {len(builder.nodes)}")
        print(f"  Choices created: {len(builder.choices)}")
        print(f"  State variables: {len(builder.state_vars)}")
        print(f"  Schema valid: {'Yes' if is_valid else 'No'}")

        # Visual story structure
        print("\n  📖 STORY STRUCTURE:")
        print("  ┌─ [visual representation of story flow]")
        print("  │   ├─→ [branch descriptions]")
        print("  └─→ [ending summaries]")

        test_results["success"] = is_valid
        test_results["end_time"] = datetime.now().isoformat()

        with open(RESULTS_FILE, "w") as f:
            json.dump(test_results, f, indent=2)
        print(f"\n  📊 Results saved to: {RESULTS_FILE}")

        return 0 if is_valid else 1

    except AuthenticationError as e:
        print(f"\n❌ Authentication failed: {e}")
        test_results["errors"].append(str(e))
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        test_results["errors"].append(str(e))
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

---

## Content Quality Standards

### Narrative Content Requirements
- **No placeholder text** - All content should be complete, engaging narrative
- **Diegetic integration** - Story mechanics should feel natural within the narrative
- **Thematic coherence** - All choices and outcomes should serve the story's themes
- **Character voice** - Maintain consistent narrative voice throughout

### Technical Requirements
- **State validation** - Always validate state schema before completion
- **Error handling** - Wrap API calls with proper exception handling  
- **Logging levels** - Support both normal and verbose output modes
- **Results tracking** - Save comprehensive results to JSON file

### Format-Specific Standards

**Markdown Stories:**
- Use formatting as narrative device (italic for uncertainty, bold for revelation)
- Headers for temporal/structural divisions
- Blockquotes for other voices/documents
- Images as diegetic references

**HTML Stories:**
- Use semantic markup with meaningful CSS classes
- Data attributes for metadata that affects story logic
- Tables for structured information presentation
- SVG for diagrams and visual data

---

## Common Patterns Library

### Discovery Mechanics
```python
# Incremental discovery with revelation thresholds
sets_state={
    "discoveries_made": {"$add": 1},
    "current_location": "ancient_library"
}

requires_state={
    "discoveries_made": {"$gte": 3}
}
```

### Character Development
```python
# Skill building through choices
sets_state={
    "wisdom": {"$add": 1},
    "character_development": "philosophical"
}
```

### Multiple Ending Conditions
```python
# Different endings based on accumulated state
requires_state={
    "$and": [
        {"wisdom": {"$gte": 5}},
        {"courage": {"$gte": 3}},
        {"made_sacrifice": True}
    ]
}  # -> Heroic ending

requires_state={
    "$and": [
        {"wisdom": {"$gte": 7}},
        {"made_sacrifice": False}
    ]
}  # -> Wise withdrawal ending
```

### Loop Prevention
```python
# Prevent choice repetition
requires_state={
    "visited_location_x": {"$ne": True}
}

sets_state={
    "visited_location_x": True
}
```

---

## Script Naming Conventions

### File Naming
- `test_[category]_[specific_name]_story.py`
- Examples: `test_format_markdown_horror_story.py`, `test_logic_modal_necessity_story.py`

### Output Files
- `test_results_[category]_[specific_name].json`
- Match the script name pattern for consistency

### Story Titles
- Use descriptive, thematic titles that hint at the content
- Examples: "The Antiquarian's Journal: Fragments of Reality", "The War Room: Intelligence Assessment"

---

## Quality Checklist

Before submitting a story script, verify:

**Structure:**
- [ ] Complete file header with description and usage
- [ ] Proper import structure and configuration
- [ ] Builder class with all required methods
- [ ] Comprehensive state schema definition
- [ ] Logical branching structure with proper convergence

**Content:**
- [ ] No placeholder or lorem ipsum text
- [ ] Engaging narrative throughout
- [ ] Consistent voice and tone  
- [ ] Meaningful choice text that reflects story context
- [ ] Rich, format-appropriate content in nodes

**Technical:**
- [ ] All state variables defined before use
- [ ] State requirements properly structured
- [ ] Schema validation at end of build process
- [ ] Comprehensive error handling
- [ ] Proper results tracking and JSON output

**Testing:**
- [ ] Script runs without errors
- [ ] All state transitions work correctly
- [ ] Schema validation passes
- [ ] Results file contains complete information
- [ ] Story is playable end-to-end

---

This reference card provides the foundation for creating sophisticated story test scripts that match the complexity and presentation quality of the existing `formats/` and `carroll/` examples. Use these patterns as building blocks for more complex and specialized story testing scenarios.