#!/usr/bin/env python3
"""
Carroll Baroco Story - Indirect Proof Syllogisms

This script creates a story demonstrating the Baroco syllogism (AOO-2),
which introduces INDIRECT PROOF via reductio ad absurdum - proof by contradiction.

    Major Premise:  "All swans in England are white"        (A proposition: All S are M)
    Minor Premise:  "Some birds in this pond are not white" (O proposition: Some P are not M)
    Conclusion:     "Some birds in this pond are not swans in England" (O proposition: Some P are not S)

KEY CONCEPTS INTRODUCED:
- INDIRECT PROOF: Baroco cannot be proven by direct methods - requires reductio ad absurdum
- Proof by contradiction: assume the opposite of what you want to prove, derive a contradiction
- Historical significance: Aristotle used Baroco to demonstrate this proof technique
- O proposition mastery: uses particular negative in both premise and conclusion

=============================================================================
ARCHETYPES, PERSONAS, TRAITS, AND QUALITIES TO CREATE
=============================================================================

ARCHETYPES (Categories/Sets):
-----------------------------
1. "English Swans" (Minor Term - S)
   - Description: "Swans found in England, traditionally all white"
   - All members have the trait "White Plumage" (by major premise)
   - Some birds in the pond are NOT these (by conclusion)

2. "Pond Birds" (Major Term - P)
   - Description: "Various waterfowl observed in this particular pond"
   - Some members do NOT have "White Plumage" (by minor premise)
   - Contains both white and non-white birds

3. "White Plumage" (Middle Term - M)
   - Description: "Having completely white feathers"
   - Possessed by ALL English swans (by major premise)
   - NOT possessed by some pond birds (by minor premise)

TRAITS (Properties):
--------------------
1. "White Plumage"
   - Description: "Completely white feathers covering the bird"
   - Links: ALL English Swans → have this trait universally
   - Links: NOT all Pond Birds → some lack this trait

2. "Waterfowl Characteristics"
   - Description: "Adapted for swimming and water environments"
   - Links: Both English Swans AND Pond Birds → share aquatic lifestyle
   - Shows they're related categories (both waterfowl)

3. "Native to England"
   - Description: "Originally from or established in England"
   - Links: English Swans → have this geographic trait
   - May or may not apply to all pond birds

PERSONAS (Individuals):
-----------------------
1. "Cygnus" (a White Swan)
   - Description: "Elegant white swan, native to England"
   - Member of: English Swans, Pond Birds (if in the pond)
   - Traits: White Plumage, Waterfowl Characteristics, Native to England

2. "Corvus" (a Black Coot)
   - Description: "Small dark waterbird with distinctive white beak"
   - Member of: Pond Birds
   - NOT member of: English Swans
   - Traits: Dark plumage (NOT white), Waterfowl Characteristics

3. "Mallard" (a Colorful Duck)
   - Description: "Duck with green head and brown body"
   - Member of: Pond Birds
   - NOT member of: English Swans
   - Traits: Mixed colored plumage (NOT white), Waterfowl Characteristics

=============================================================================

Usage:
    python test_carroll_baroco_story.py
    python test_carroll_baroco_story.py --verbose
    python test_carroll_baroco_story.py --cleanup

Output:
    test_results_carroll_baroco.json
"""

import json
import sys
import argparse
from datetime import datetime
from pathlib import Path

import requests

# Import auth helper
sys.path.append(str(Path(__file__).parent.parent))
from auth_helper import get_authenticated_session, AuthenticationError


# Configuration
BASE_URL = "http://localhost:8000/api/v1"
RESULTS_FILE = "test_results_carroll_baroco.json"

# Test results tracking
test_results = {
    "test_suite": "Carroll Baroco Story (AOO-2)",
    "start_time": None,
    "end_time": None,
    "story_id": None,
    "node_ids": {},
    "choice_ids": {},
    "state_variable_ids": {},
    "success": False,
    "errors": []
}


class BarocoStoryBuilder:
    """Builds a Baroco syllogism story demonstrating indirect proof via reductio ad absurdum."""

    def __init__(self, session: requests.Session, verbose: bool = False):
        self.session = session
        self.verbose = verbose
        self.story_id = None
        self.nodes = {}  # name -> node data
        self.choices = []  # list of created choices
        self.state_vars = {}  # key -> variable data

    def log(self, message: str):
        """Print message."""
        print(f"  {message}")

    def debug(self, message: str):
        """Print debug message if verbose."""
        if self.verbose:
            print(f"  [DEBUG] {message}")

    # =========================================================================
    # API Helper Methods (identical to other Carroll scripts)
    # =========================================================================

    def create_story(self, title: str, description: str) -> dict:
        """Create the story container."""
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
        """Create a state schema variable."""
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
                    is_start: bool = False, is_end: bool = False) -> dict:
        """Create a story node."""
        response = self.session.post(f"{BASE_URL}/storynodes", json={
            "story_id": self.story_id,
            "story_version": 1,
            "title": title,
            "content": content,
            "node_type": "text",
            "content_format": "markdown",
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
        """Create a choice between nodes."""
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
        """Validate state schema against choices."""
        response = self.session.get(
            f"{BASE_URL}/stories/{self.story_id}/versions/1/state-schema/validate"
        )
        if response.status_code != 200:
            raise Exception(f"Failed to validate: {response.text}")
        return response.json()

    # =========================================================================
    # Story Building
    # =========================================================================

    def build_story(self):
        """Build the complete Baroco syllogism story."""

        # =====================================================================
        # STEP 1: CREATE THE STORY
        # =====================================================================
        self.log("\n📖 Creating story...")

        story = self.create_story(
            title="The Pond Paradox: A Study in Indirect Proof",
            description="""Baroco syllogism (AOO-2) - introducing INDIRECT PROOF via reductio ad absurdum.

STRUCTURE:
- Major (A): All swans in England are white
- Minor (O): Some birds in this pond are not white
- Conclusion (O): Some birds in this pond are not swans in England

BAROCO'S UNIQUENESS: Cannot be proven by direct methods like Barbara, Celarent, 
or Darii. Instead requires REDUCTIO AD ABSURDUM - proof by contradiction.

INDIRECT PROOF METHOD: Assume the opposite of what you want to prove, then 
show this assumption leads to a logical contradiction. When the assumption 
fails, the original conclusion must be true.

DOMAIN: Victorian ornithological expedition examining waterfowl diversity, 
using the famous "all swans are white" example that was later overturned 
by the discovery of black swans in Australia."""
        )
        self.story_id = story["id"]
        test_results["story_id"] = self.story_id
        self.log(f"  Created story: {self.story_id}")

        # =====================================================================
        # STEP 2: DEFINE STATE SCHEMA
        # =====================================================================
        self.log("\n📋 Creating state schema...")

        # ---------------------------------------------------------------------
        # Premise tracking - note the Figure 2 structure with O proposition
        # ---------------------------------------------------------------------

        self.state_vars["major_premise"] = self.create_state_variable(
            key="all_english_swans_are_white",
            value_type="boolean",
            default_value=False,
            category="premises",
            description="Major premise (A): All S are M (All English swans are white). "
                       "Universal trait possession: English Swans ⊆ {White-plumaged birds}. "
                       "Domain: All members of Archetype 'English Swans' possess Trait 'White Plumage'."
        )
        self.debug("Created: all_english_swans_are_white")

        self.state_vars["minor_premise"] = self.create_state_variable(
            key="some_pond_birds_not_white",
            value_type="boolean",
            default_value=False,
            category="premises",
            description="Minor premise (O): Some P are not M (Some pond birds are not white). "
                       "Partial exclusion: Pond Birds ∩ {White-plumaged birds} ≠ Pond Birds. "
                       "Domain: Some members of Archetype 'Pond Birds' do NOT possess Trait 'White Plumage'."
        )
        self.debug("Created: some_pond_birds_not_white")

        # ---------------------------------------------------------------------
        # Indirect proof tracking - NEW CONCEPT
        # ---------------------------------------------------------------------

        self.state_vars["proof_method"] = self.create_state_variable(
            key="proof_method_used",
            value_type="enum",
            enum_values=["unknown", "direct", "indirect", "reductio_ad_absurdum"],
            default_value="unknown",
            category="structure",
            description="Method of proof: Baroco requires indirect proof via contradiction"
        )
        self.debug("Created: proof_method_used")

        self.state_vars["assumption_made"] = self.create_state_variable(
            key="contrary_assumption",
            value_type="boolean",
            default_value=False,
            category="structure",
            description="Whether player has made the contrary assumption for reductio ad absurdum"
        )
        self.debug("Created: contrary_assumption")

        self.state_vars["contradiction_found"] = self.create_state_variable(
            key="contradiction_discovered",
            value_type="boolean",
            default_value=False,
            category="structure",
            description="Whether the logical contradiction has been identified"
        )
        self.debug("Created: contradiction_discovered")

        # ---------------------------------------------------------------------
        # Syllogism structure - Figure 2 with special properties
        # ---------------------------------------------------------------------

        self.state_vars["figure"] = self.create_state_variable(
            key="syllogism_figure",
            value_type="enum",
            enum_values=["figure_1", "figure_2", "figure_3", "figure_4"],
            default_value="figure_2",
            category="structure",
            description="Figure 2: S-M, P-M ∴ P-S pattern, but requires indirect proof unlike Camestres"
        )
        self.debug("Created: syllogism_figure")

        self.state_vars["mood"] = self.create_state_variable(
            key="syllogism_mood",
            value_type="string",
            default_value="",
            category="structure",
            description="Syllogism mood: AOO for Baroco (All-Some not-Some not)"
        )
        self.debug("Created: syllogism_mood")

        # ---------------------------------------------------------------------
        # Conclusion and validation tracking
        # ---------------------------------------------------------------------

        self.state_vars["conclusion"] = self.create_state_variable(
            key="some_pond_birds_not_english_swans",
            value_type="boolean",
            default_value=False,
            category="conclusions",
            description="Valid conclusion (O): Some P are not S (Some pond birds are not English swans). "
                       "Domain: Non-white pond birds cannot be English swans due to the universal "
                       "white plumage requirement for English swans."
        )
        self.debug("Created: some_pond_birds_not_english_swans")

        self.state_vars["valid"] = self.create_state_variable(
            key="conclusion_valid",
            value_type="boolean",
            default_value=False,
            category="validation",
            description="Whether the derived conclusion follows validly from premises"
        )
        self.debug("Created: conclusion_valid")

        self.state_vars["fallacy"] = self.create_state_variable(
            key="fallacy_committed",
            value_type="enum",
            enum_values=["none", "direct_proof_attempt", "universal_from_particular", 
                        "affirmative_from_negative", "existential_import_error", "non_sequitur"],
            default_value="none",
            category="validation",
            description="Type of logical fallacy committed, if any"
        )
        self.debug("Created: fallacy_committed")

        # ---------------------------------------------------------------------
        # Learning progress tracking - indirect proof concepts
        # ---------------------------------------------------------------------

        self.state_vars["understands_indirect_proof"] = self.create_state_variable(
            key="understands_indirect_proof",
            value_type="boolean",
            default_value=False,
            category="learning",
            description="Player understands the concept of proof by contradiction"
        )
        self.debug("Created: understands_indirect_proof")

        self.state_vars["understands_reductio"] = self.create_state_variable(
            key="understands_reductio_ad_absurdum",
            value_type="boolean",
            default_value=False,
            category="learning",
            description="Player grasps the reductio ad absurdum technique"
        )
        self.debug("Created: understands_reductio_ad_absurdum")

        self.state_vars["historical_context"] = self.create_state_variable(
            key="appreciates_historical_context",
            value_type="boolean",
            default_value=False,
            category="learning",
            description="Player understands historical significance of swan whiteness example"
        )
        self.debug("Created: appreciates_historical_context")

        self.state_vars["baroco_mastery"] = self.create_state_variable(
            key="mastered_baroco_reasoning",
            value_type="boolean",
            default_value=False,
            category="learning",
            description="Player has mastered Baroco's indirect proof technique"
        )
        self.debug("Created: mastered_baroco_reasoning")

        self.log(f"  Created {len(self.state_vars)} state variables")

        # =====================================================================
        # STEP 3: CREATE STORY NODES
        # =====================================================================
        self.log("\n📝 Creating story nodes...")

        # ---------------------------------------------------------------------
        # INTRODUCTION NODE (Start) - Victorian Ornithological Expedition
        # ---------------------------------------------------------------------

        self.nodes["intro"] = self.create_node(
            title="The Ornithological Expedition",
            content="""# The Ornithological Expedition, England 1859

You join a distinguished **ornithologist** on the banks of a secluded English 
pond, part of a comprehensive study of British waterfowl. The morning mist 
rises from the still water as various birds glide across its surface.

The ornithologist adjusts his field glasses and points to the water.

*"Observe the diversity of our avian visitors this morning. But I'm troubled 
by a logical puzzle that requires... unconventional reasoning."*

You scan the pond and note:
- Several **elegant white swans** drifting gracefully near the far shore
- A **black coot** with distinctive white beak paddling among the reeds  
- **Brown and green mallards** dabbling for food in the shallows
- Other **dark-feathered waterfowl** of various species

*"Here's what we know with certainty: every swan in England has white plumage. 
This has been observed and documented for centuries—it's a universal truth 
of English ornithology."*

*"Yet clearly, some birds in this very pond are NOT white. The question becomes: 
what can we conclude about the relationship between these pond birds and 
English swans?"*

He pauses thoughtfully.

*"But here's where it gets interesting—this particular logical puzzle cannot 
be solved by our usual direct reasoning methods. We must employ a technique 
Aristotle called 'reductio ad absurdum'—proof by contradiction."*

---

**NEW CHALLENGE - INDIRECT PROOF:**

Unlike previous syllogisms that used direct reasoning:
- **Direct proof**: Establish premises, follow logical rules → conclusion
- **Indirect proof**: Assume opposite of desired conclusion, show it leads to contradiction

**Baroco's uniqueness**: Cannot be reduced to simpler forms like Barbara or Celarent. 
It requires the sophisticated technique of **reductio ad absurdum**.""",
            is_start=True
        )
        self.debug("Created node: intro")

        # ---------------------------------------------------------------------
        # MAJOR PREMISE NODE - All English swans are white (A proposition)
        # ---------------------------------------------------------------------

        self.nodes["major_premise"] = self.create_node(
            title="The Swan Tradition",
            content="""# The Swan Tradition

The ornithologist opens his well-worn field journal, pages filled with decades 
of careful observations.

*"Let us begin with established ornithological fact: every swan that inhabits 
England possesses completely white plumage."*

He shows you detailed illustrations and notes:

- **Mute Swans**: *"The iconic species of English rivers and ponds—pure white"*
- **Whooper Swans**: *"Winter visitors from Iceland—brilliant white plumage"* 
- **Bewick's Swans**: *"Smaller migrants—also uniformly white"*

*"This is not mere observation, but centuries of documented evidence. From 
medieval bestiaries to modern taxonomic studies, English swans are universally 
white. No exceptions have ever been recorded."*

```
┌─────────────────────────────────────────┐
│           MAJOR PREMISE                 │
│         (A Proposition)                 │
│                                         │
│   "All swans in England are white"      │
│                                         │
│   Logical form: All S are M             │
│   - S (Minor term*) = English Swans     │
│   - M (Middle term) = White Plumage     │
│                                         │
│   *Figure 2: Minor term in major premise│
│                                         │
│   Universal trait possession:           │
│   English Swans ⊆ {White-plumed birds}  │
│                                         │
│   ┌─────── White Plumage ──────┐        │
│   │                            │        │
│   │  ┌─── English Swans ───┐   │        │
│   │  │ All of them         │   │        │
│   │  │ (Mute, Whooper,     │   │        │
│   │  │  Bewick's...)       │   │        │
│   │  └─────────────────────┘   │        │
│   │                            │        │
│   │ (Other white birds exist)  │        │
│   └────────────────────────────┘        │
└─────────────────────────────────────────┘
```

*"This premise is historically significant—before the discovery of black swans 
in Australia, 'all swans are white' was considered a perfect example of 
universal truth."*

*"Do you accept this premise about English swan plumage?"*

---

**DOMAIN MAPPING:**
- This premise asserts: ALL members of Archetype "English Swans" possess Trait "White Plumage"
- Universal trait possession: English Swans ⊆ {White-plumed birds}
- No exceptions within the geographic constraint of England

**HISTORICAL CONTEXT:**
The "white swan" assumption was famously overturned when black swans were 
discovered in Australia, becoming a classic example of how empirical 
generalizations can be falsified by new evidence."""
        )
        self.debug("Created node: major_premise")

        # ---------------------------------------------------------------------
        # MINOR PREMISE NODE - Some pond birds are not white (O proposition)
        # ---------------------------------------------------------------------

        self.nodes["minor_premise"] = self.create_node(
            title="The Pond's Diversity",
            content="""# The Pond's Diversity

The ornithologist gestures across the water, where the varied waterfowl 
continue their morning activities.

*"Now observe the undeniable evidence before us: some birds in this pond 
are clearly NOT white."*

You note the non-white birds:

- **Black Coot**: *"Dark plumage with white beak—definitely not white"*
- **Mallard Drakes**: *"Iridescent green heads and brown bodies"*
- **Moorhens**: *"Dark slate coloring with red beaks"*
- **Various ducks**: *"Mottled browns, grays, and patterns"*

*"These are not rare exceptions or unusual lighting—they are genuinely 
non-white birds sharing this habitat with the white swans."*

```
┌─────────────────────────────────────────┐
│           MINOR PREMISE                 │
│         (O Proposition)                 │
│                                         │
│   "Some birds in this pond are not      │
│    white"                               │
│                                         │
│   Logical form: Some P are not M        │
│   - P (Major term*) = Pond Birds        │
│   - M (Middle term) = White Plumage     │
│                                         │
│   *Figure 2: Major term in minor premise│
│                                         │
│   Partial exclusion: Some pond birds    │
│   are OUTSIDE the white plumage set     │
│                                         │
│       Pond Birds                        │
│   ┌─────────────────┐                   │
│   │ ●●● (Coots,     │     ┌─ White ─┐   │
│   │  Moorhens,      │  ╱  │Plumage │   │
│   │  Mallards...)   │╱    │        │   │
│   │                 │     └────────┘   │
│   │ ○○○ (White swans│                  │
│   │  & other white  │                  │
│   │  waterbirds)    │                  │
│   └─────────────────┘                  │
│                                         │
│   ● = Non-white pond birds             │
│   ○ = White pond birds                 │
└─────────────────────────────────────────┘
```

*"This O proposition—'Some pond birds are not white'—is crucial for what 
follows. It establishes that not ALL pond birds share the white plumage trait."*

*"Now we face the logical challenge: what can we conclude about the relationship 
between these pond birds and English swans? But remember—direct reasoning 
won't work here. We need Aristotle's method of contradiction."*

---

**DOMAIN MAPPING:**
- This premise asserts: Some members of Archetype "Pond Birds" do NOT possess Trait "White Plumage"
- Partial exclusion: Pond Birds ∩ {Non-white birds} ≠ ∅
- The pond contains both white birds (swans) and non-white birds (coots, ducks, etc.)

**LOGICAL STRUCTURE SO FAR:**
- Major (A): All S are M ✓ (All English swans are white)
- Minor (O): Some P are not M ✓ (Some pond birds are not white)
- Conclusion: ??? (What about pond birds and English swans?)

**THE INDIRECT PROOF CHALLENGE:**
Unlike Barbara, Celarent, or Darii, this cannot be solved by following 
direct logical rules. We must use reductio ad absurdum."""
        )
        self.debug("Created node: minor_premise")

        # ---------------------------------------------------------------------
        # INDIRECT PROOF EXPLANATION NODE
        # ---------------------------------------------------------------------

        self.nodes["indirect_method"] = self.create_node(
            title="The Method of Contradiction",
            content="""# The Method of Contradiction

The ornithologist sets down his field glasses and turns to face you directly.

*"Before we proceed, you must understand why this puzzle requires a different 
approach. Baroco—as Aristotle named this form—cannot be proven by the direct 
methods that work for other syllogisms."*

*"Instead, we use REDUCTIO AD ABSURDUM—proof by contradiction. Here's how:*

**STEP 1: Assume the Opposite**
We temporarily assume the OPPOSITE of what we want to prove, just to see what happens.

**STEP 2: Follow the Logic** 
We combine this assumption with our known premises and see where the logic leads.

**STEP 3: Find the Contradiction**
If our assumption leads to a logical impossibility, then our assumption must be false.

**STEP 4: Conclude the Truth**
If the assumption is false, then the OPPOSITE of our assumption must be true.

```
┌─────────────────────────────────────────┐
│        REDUCTIO AD ABSURDUM             │
│                                         │
│   Known Premises:                       │
│   • All English swans are white         │
│   • Some pond birds are not white       │
│                                         │
│   What we want to prove:                │
│   • Some pond birds are not English     │
│     swans                               │
│                                         │
│   Reductio method:                      │
│   1. Assume OPPOSITE: "ALL pond birds   │
│      ARE English swans"                 │
│   2. Combine with premises...           │
│   3. Derive contradiction...            │
│   4. Therefore assumption is FALSE      │
│   5. So opposite must be TRUE           │
└─────────────────────────────────────────┘
```

*"This technique was revolutionary in ancient mathematics and logic. When 
direct proof fails, contradiction often succeeds."*

*"Shall we apply this method to our pond puzzle?"*

---

**HISTORICAL SIGNIFICANCE:**
Reductio ad absurdum was used by ancient Greek mathematicians to prove 
fundamental theorems, such as the irrationality of √2 and the infinity of prime numbers.

**WHY BAROCO NEEDS THIS:**
The combination A-O-O (All-Some not-Some not) creates logical relationships 
that don't reduce to simpler patterns, requiring the sophisticated technique 
of proof by contradiction."""
        )
        self.debug("Created node: indirect_method")

        # ---------------------------------------------------------------------
        # ASSUMPTION NODE - Make the contrary assumption
        # ---------------------------------------------------------------------

        self.nodes["make_assumption"] = self.create_node(
            title="The Contrary Assumption",
            content="""# The Contrary Assumption

The ornithologist nods approvingly at your willingness to try the indirect method.

*"Excellent! Now, what we ultimately want to prove is that 'Some pond birds 
are not English swans.' But for reductio ad absurdum, we must assume the 
OPPOSITE of this."*

*"The opposite of 'Some pond birds are not English swans' is 'ALL pond birds 
ARE English swans.' Let us temporarily assume this—not because we believe it, 
but to see where the logic leads."*

**OUR TEMPORARY ASSUMPTION:** *"All birds in this pond are English swans."*

```
┌─────────────────────────────────────────┐
│       ASSUMPTION FOR REDUCTIO           │
│                                         │
│   "All pond birds are English swans"    │
│                                         │
│   This means:                           │
│   • The black coot is an English swan   │
│   • The brown mallards are English swans│
│   • The dark moorhens are English swans │
│   • Every bird in the pond is an        │
│     English swan                        │
│                                         │
│   We don't BELIEVE this assumption—     │
│   we're testing it!                     │
└─────────────────────────────────────────┘
```

*"Now, let's combine this assumption with what we know to be true and see 
what happens..."*

*"If ALL pond birds are English swans, and we know that ALL English swans 
are white, then what must be true about ALL pond birds?"*

---

**THE LOGICAL CHAIN BEGINS:**
1. **Assumption**: All pond birds are English swans
2. **Known premise**: All English swans are white  
3. **Therefore**: All pond birds must be white

*"Do you see where this is leading? We're about to derive something that 
contradicts our direct observation..."*"""
        )
        self.debug("Created node: make_assumption")

        # ---------------------------------------------------------------------
        # CONTRADICTION NODE - Discover the logical impossibility
        # ---------------------------------------------------------------------

        self.nodes["find_contradiction"] = self.create_node(
            title="The Logical Impossibility",
            content="""# The Logical Impossibility

The ornithologist's eyes gleam with the satisfaction of logical discovery.

*"Now watch what happens when we follow our assumption to its logical conclusion!"*

**THE LOGICAL CHAIN:**
1. **Our assumption**: All pond birds are English swans
2. **Known premise**: All English swans are white
3. **Therefore**: All pond birds must be white

*"But wait! This contradicts our direct observation!"*

**THE CONTRADICTION:**
- Our logic says: **All pond birds must be white**
- Our observation says: **Some pond birds are NOT white** (coots, mallards, etc.)

```
┌─────────────────────────────────────────┐
│          CONTRADICTION FOUND!           │
│                                         │
│   From our assumption & premises:       │
│   → "All pond birds are white"          │
│                                         │
│   From direct observation:              │
│   → "Some pond birds are NOT white"     │
│                                         │
│          ⚡ IMPOSSIBLE! ⚡               │
│                                         │
│   Both cannot be true simultaneously.   │
│   Logic has led us to impossibility.    │
│                                         │
│   Therefore our ASSUMPTION must be      │
│   FALSE!                                │
└─────────────────────────────────────────┘
```

*"This is the power of reductio ad absurdum! When an assumption leads to 
contradiction, we know the assumption must be false."*

*"If our assumption 'All pond birds are English swans' is false, then its 
opposite must be true: 'Some pond birds are NOT English swans.'"*

*"We have proven our conclusion indirectly—by showing that denying it leads 
to logical impossibility!"*

---

**THE REDUCTIO IS COMPLETE:**
✗ Assumption: "All pond birds are English swans" → LEADS TO CONTRADICTION
✓ Therefore: "Some pond birds are not English swans" → MUST BE TRUE

**BAROCO ACHIEVED:**
- Major: All English swans are white (A)
- Minor: Some pond birds are not white (O)  
- Conclusion: Some pond birds are not English swans (O)

*"This is why Baroco required indirect proof—the logical relationship between 
A and O propositions creates patterns that direct methods cannot resolve!"*"""
        )
        self.debug("Created node: find_contradiction")

        # ---------------------------------------------------------------------
        # VALID CONCLUSION NODE - Baroco mastery achieved
        # ---------------------------------------------------------------------

        self.nodes["valid_conclusion"] = self.create_node(
            title="Baroco Mastery: Indirect Proof Achieved",
            content="""# Baroco Mastery: Indirect Proof Achieved

*"Some birds in this pond are not English swans,"* you conclude with the 
satisfaction of having mastered indirect reasoning.

The ornithologist beams with scholarly pride.

*"Magnificent! You have conquered BAROCO and mastered the art of reductio ad absurdum!"*

```
┌─────────────────────────────────────────┐
│           VALID SYLLOGISM               │
│             (Baroco)                    │
│                                         │
│   All English swans are white     (A)   │
│   Some pond birds are not white   (O)   │
│   ─────────────────────────────────      │
│   ∴ Some pond birds are not       (O)   │
│     English swans                       │
│                                         │
│   Form: AOO-2 (Baroco)                  │
│   Figure: 2 (S-M, P-M ∴ P-S)            │
│   Mood: AOO                             │
│   Method: INDIRECT PROOF ⚡              │
│                                         │
│         VALID ✓                         │
└─────────────────────────────────────────┘
```

*"Observe what we've accomplished through indirect reasoning:*

**DIRECT METHOD IMPOSSIBLE**: Unlike Barbara (AAA) or Celarent (EAE), Baroco 
cannot be reduced to simpler logical forms using direct proof techniques.

**REDUCTIO AD ABSURDUM SUCCESSFUL**: By assuming the opposite of our desired 
conclusion, we derived a logical contradiction, proving our conclusion must be true.

**HISTORICAL SIGNIFICANCE**: You've used the same technique Aristotle employed 
to demonstrate that some syllogisms require indirect proof—a foundational 
insight in logical methodology.

**PRACTICAL APPLICATION**: The non-white birds (coots, mallards, moorhens) 
in our pond cannot be English swans precisely because English swan identity 
requires white plumage, which they lack.

```
    The Proof Method Comparison:
    ──────────────────────────
    Barbara (AAA-1):  Direct proof ✓
    Celarent (EAE-1): Direct proof ✓  
    Darii (AII-1):    Direct proof ✓
    Ferio (EIO-1):    Direct proof ✓
    Camestres (AEE-2): Direct proof ✓
    Disamis (IAI-3):  Direct proof ✓
    Baroco (AOO-2):   INDIRECT PROOF ONLY ⚡
```

*"Baroco stands apart in the syllogistic tradition—it cannot be 'reduced' to 
Figure 1 forms through simple conversions. It demands the full sophistication 
of proof by contradiction."*

---

**DOMAIN MAPPING:**
- Conclusion establishes: Some members of "Pond Birds" are NOT members of "English Swans"
- Specifically: non-white pond birds (coots, mallards, etc.) are excluded from English swan category
- The reasoning: lacking the required white plumage trait disqualifies them from swan identity

**BAROCO IN THE LOGICAL TRADITION:**
- One of only two syllogisms requiring indirect proof (along with Bocardo)
- Historical significance in demonstrating logical methodology
- Foundation for understanding proof techniques in mathematics and philosophy

You have achieved mastery over one of logic's most sophisticated forms!""",
            is_end=True
        )
        self.debug("Created node: valid_conclusion")

        # ---------------------------------------------------------------------
        # FALLACY NODE: Direct proof attempt
        # ---------------------------------------------------------------------

        self.nodes["fallacy_direct_attempt"] = self.create_node(
            title="The Direct Method Failure",
            content="""# The Direct Method Failure

*"No pond birds are English swans?"* The ornithologist shakes his head.

*"You've attempted to use DIRECT reasoning on a syllogism that requires 
INDIRECT proof! This is a fundamental methodological error."*

```
┌─────────────────────────────────────────┐
│              FALLACY                    │
│      Direct Proof Attempt              │
│                                         │
│   Your reasoning:                       │
│   • All English swans are white         │
│   • Some pond birds are not white       │
│   • Therefore: No pond birds are        │
│     English swans                       │
│                                         │
│   Problems:                             │
│   1. You've made the conclusion         │
│      UNIVERSAL (No = All are not)       │
│   2. You've used direct reasoning       │
│      on a form that REQUIRES indirect   │
│   3. You've ignored the white swans     │
│      that ARE in the pond              │
└─────────────────────────────────────────┘
```

*"The issue is twofold:*

**METHODOLOGICAL ERROR**: Baroco cannot be proven directly. The combination 
A-O-O creates logical relationships that don't reduce to simple patterns. 
You MUST use reductio ad absurdum.

**QUANTIFICATION ERROR**: Your conclusion 'No pond birds are English swans' 
is too strong. Look at the pond—there ARE white swans present! They are 
both pond birds AND English swans.

**THE CORRECT REASONING:**
- Some pond birds are non-white (coots, ducks, moorhens)
- These specific non-white birds cannot be English swans  
- But the white swans in the pond remain English swans
- Therefore: SOME pond birds are not English swans (not ALL)

```
    Pond Bird Analysis:
    ─────────────────
    White swans in pond:    ARE English swans ✓
    Black coots in pond:    NOT English swans ✗
    Brown mallards in pond: NOT English swans ✗
    Other dark birds:       NOT English swans ✗
    
    Result: SOME pond birds are not English swans
```

*"You must abandon direct reasoning and embrace the indirect method. Assume 
the opposite of what you want to prove, then find the contradiction!"*

---

**METHODOLOGICAL LESSON:**
Not all logical forms yield to direct proof. Baroco and Bocardo specifically 
require indirect methods, teaching us that proof techniques must match the 
logical structure of the problem."""
        )
        self.debug("Created node: fallacy_direct_attempt")

        # ---------------------------------------------------------------------
        # FALLACY NODE: Universal conclusion
        # ---------------------------------------------------------------------

        self.nodes["fallacy_universal"] = self.create_node(
            title="The Overgeneralization Error",
            content="""# The Overgeneralization Error

*"All pond birds are English swans?"* The ornithologist looks puzzled.

*"You've committed a double error—wrong direction AND wrong method!"*

```
┌─────────────────────────────────────────┐
│              FALLACY                    │
│       Universal Overgeneralization     │
│                                         │
│   Your conclusion: "All pond birds      │
│   are English swans" (A)                │
│                                         │
│   But this contradicts our DIRECT       │
│   observation:                          │
│                                         │
│   • We SEE black coots in the pond      │
│   • We SEE brown mallards in the pond   │  
│   • We SEE dark moorhens in the pond    │
│                                         │
│   These are clearly NOT white, so       │
│   they cannot ALL be English swans!     │
│                                         │
│   Plus: You're using direct reasoning   │
│   when indirect proof is required.      │
└─────────────────────────────────────────┘
```

*"This error reveals a misunderstanding of both the evidence and the method:*

**EMPIRICAL CONTRADICTION**: Your conclusion directly contradicts observable 
evidence. The non-white birds in the pond cannot be English swans because 
English swans are universally white.

**METHODOLOGICAL ERROR**: Even if the evidence supported your conclusion, 
you've used direct reasoning on Baroco, which requires reductio ad absurdum.

**THE OBSERVABLE REALITY:**
Look at the pond right now:
- White swans: Could be English swans ✓
- Black coots: Cannot be English swans ✗ (wrong color)
- Brown ducks: Cannot be English swans ✗ (wrong color)  
- Dark moorhens: Cannot be English swans ✗ (wrong color)

**CORRECT LOGICAL APPROACH:**
1. Make the contrary assumption (for reductio)
2. Derive the contradiction with observed evidence
3. Conclude that some (not all) pond birds are not English swans

*"Remember: logic must align with observation. When we see non-white birds, 
we cannot conclude they are members of a universally white species!"*

---

**LESSON IN EVIDENCE:**
Logical reasoning must respect empirical evidence. When conclusions contradict 
direct observation, the reasoning method or premises must be re-examined."""
        )
        self.debug("Created node: fallacy_universal")

        # ---------------------------------------------------------------------
        # RETRY NODE
        # ---------------------------------------------------------------------

        self.nodes["retry"] = self.create_node(
            title="Reconsider the Method",
            content="""# Reconsider the Method

The ornithologist offers a patient, encouraging smile.

*"Indirect proof takes practice—even Aristotle's students struggled with it. 
Let's review what makes Baroco special and why it requires reductio ad absurdum."*

**OUR ESTABLISHED FACTS:**
- **Major premise**: All English swans are white (no exceptions)
- **Minor premise**: Some pond birds are not white (we see them!)

**THE CHALLENGE:**
What can we conclude about the relationship between pond birds and English swans?

**WHY DIRECT PROOF FAILS:**
The pattern A-O-O (All, Some-not, Some-not) cannot be reduced to simpler 
syllogistic forms. Unlike Barbara or Celarent, there's no direct logical 
pathway from premises to conclusion.

**THE INDIRECT SOLUTION:**
```
    Reductio Ad Absurdum Method:
    ──────────────────────────
    
    1. ASSUME THE OPPOSITE of what we want to prove
       (Assume: "All pond birds ARE English swans")
    
    2. COMBINE with known premises  
       (If all pond birds are English swans,
        and all English swans are white,
        then all pond birds must be white)
    
    3. FIND THE CONTRADICTION
       (But we observe non-white pond birds!)
    
    4. REJECT THE ASSUMPTION
       (If assumption leads to impossibility,
        assumption must be false)
    
    5. CONCLUDE THE OPPOSITE
       (Therefore: Some pond birds are NOT English swans)
```

*"The beauty of reductio is that it proves things indirectly by showing that 
denying them leads to logical impossibility."*

*"Ready to try the indirect method properly?"*

---

**METHODOLOGICAL INSIGHT:**
Some truths cannot be reached by direct path—they must be discovered by 
eliminating impossibilities. This is the essence of proof by contradiction."""
        )
        self.debug("Created node: retry")

        # ---------------------------------------------------------------------
        # SKIP PREMISES NODE
        # ---------------------------------------------------------------------

        self.nodes["skip_fallacy"] = self.create_node(
            title="The Hasty Judgment",
            content="""# The Hasty Judgment

You begin to make claims about the birds and their classifications, but the 
ornithologist holds up his hand.

*"Patience! We cannot draw conclusions about these complex relationships 
without first establishing our logical foundations systematically."*

```
┌─────────────────────────────────────────┐
│              FALLACY                    │
│       Hasty Generalization              │
│                                         │
│   To determine the relationship between │
│   pond birds and English swans, we      │
│   must establish:                       │
│                                         │
│   1. What universal traits define       │
│      English swans?                     │
│      (Plumage color? Geographic origin?)│
│                                         │
│   2. What is the actual diversity       │
│      of birds in this pond?             │
│      (All white? Some non-white?)       │
│                                         │
│   3. What method of proof is            │
│      appropriate for this logical       │
│      structure?                         │
│      (Direct reasoning? Indirect?)      │
│                                         │
│   Only with systematic analysis can     │
│   we reach valid conclusions.           │
└─────────────────────────────────────────┘
```

*"This is not a simple identification exercise—it's a sophisticated logical 
puzzle that requires understanding both empirical evidence AND proof methodology."*

*"Let us begin by establishing what we know with certainty about English swan 
characteristics, based on centuries of ornithological observation..."*

---

**METHODOLOGICAL IMPORTANCE:**
Logical conclusions must be grounded in established premises and appropriate 
proof techniques. Hasty judgments bypass the systematic reasoning that 
ensures validity.

**THE SYSTEMATIC APPROACH:**
1. Establish universal premise about English swans
2. Observe particular facts about pond birds  
3. Determine appropriate proof method (direct vs. indirect)
4. Apply method correctly to reach valid conclusion"""
        )
        self.debug("Created node: skip_fallacy")

        self.log(f"  Created {len(self.nodes)} nodes")
        test_results["node_ids"] = {name: node["id"] for name, node in self.nodes.items()}

        # =====================================================================
        # STEP 4: CREATE CHOICES
        # =====================================================================
        self.log("\n🔀 Creating choices...")

        # FROM: intro
        self.choices.append(self.create_choice(
            from_node_name="intro",
            to_node_name="major_premise",
            text="\"Tell me about English swan characteristics and this indirect proof method.\"",
            order=0,
            sets_state={
                "understands_indirect_proof": False,
                "understands_reductio_ad_absurdum": False,
                "appreciates_historical_context": False
            }
        ))
        self.debug("Created choice: intro → major_premise")

        self.choices.append(self.create_choice(
            from_node_name="intro",
            to_node_name="skip_fallacy",
            text="\"Obviously the dark birds aren't swans - they're completely different!\"",
            order=1,
            sets_state={
                "fallacy_committed": "hasty_generalization"
            }
        ))
        self.debug("Created choice: intro → skip_fallacy")

        # FROM: major_premise
        self.choices.append(self.create_choice(
            from_node_name="major_premise",
            to_node_name="minor_premise",
            text="\"I accept this - English swans are universally white based on centuries of observation.\"",
            order=0,
            sets_state={
                "all_english_swans_are_white": True,
                "syllogism_mood": "A",
                "appreciates_historical_context": True
            }
        ))
        self.debug("Created choice: major_premise → minor_premise")

        # FROM: minor_premise
        self.choices.append(self.create_choice(
            from_node_name="minor_premise",
            to_node_name="indirect_method",
            text="\"I see the non-white birds clearly. But why can't we use direct reasoning here?\"",
            order=0,
            requires_state={"all_english_swans_are_white": True},
            sets_state={
                "some_pond_birds_not_white": True,
                "syllogism_mood": "AO",
                "syllogism_figure": "figure_2"
            }
        ))
        self.debug("Created choice: minor_premise → indirect_method")

        # FROM: indirect_method
        self.choices.append(self.create_choice(
            from_node_name="indirect_method",
            to_node_name="make_assumption",
            text="\"I'm ready to try reductio ad absurdum. What assumption do we make?\"",
            order=0,
            requires_state={
                "$and": [
                    {"all_english_swans_are_white": True},
                    {"some_pond_birds_not_white": True}
                ]
            },
            sets_state={
                "understands_indirect_proof": True,
                "proof_method_used": "reductio_ad_absurdum"
            }
        ))
        self.debug("Created choice: indirect_method → make_assumption")

        # FROM: make_assumption
        self.choices.append(self.create_choice(
            from_node_name="make_assumption",
            to_node_name="find_contradiction",
            text="\"I see - if all pond birds were English swans, then all pond birds would be white!\"",
            order=0,
            requires_state={"proof_method_used": "reductio_ad_absurdum"},
            sets_state={
                "contrary_assumption": True,
                "understands_reductio_ad_absurdum": True
            }
        ))
        self.debug("Created choice: make_assumption → find_contradiction")

        # FROM: find_contradiction
        self.choices.append(self.create_choice(
            from_node_name="find_contradiction",
            to_node_name="valid_conclusion",
            text="\"The contradiction proves our assumption false - so some pond birds are not English swans!\"",
            order=0,
            requires_state={
                "$and": [
                    {"contrary_assumption": True},
                    {"understands_reductio_ad_absurdum": True}
                ]
            },
            sets_state={
                "some_pond_birds_not_english_swans": True,
                "conclusion_valid": True,
                "syllogism_mood": "AOO",
                "contradiction_discovered": True,
                "mastered_baroco_reasoning": True,
                "fallacy_committed": "none"
            }
        ))
        self.debug("Created choice: find_contradiction → valid_conclusion (CORRECT)")

        # Alternative paths with fallacies from minor_premise
        self.choices.append(self.create_choice(
            from_node_name="minor_premise",
            to_node_name="fallacy_direct_attempt",
            text="\"Therefore, no pond birds are English swans.\"",
            order=1,
            requires_state={"all_english_swans_are_white": True},
            sets_state={
                "some_pond_birds_not_white": True,
                "conclusion_valid": False,
                "fallacy_committed": "direct_proof_attempt"
            }
        ))
        self.debug("Created choice: minor_premise → fallacy_direct_attempt")

        self.choices.append(self.create_choice(
            from_node_name="minor_premise",
            to_node_name="fallacy_universal",
            text="\"Therefore, all pond birds are English swans.\"",
            order=2,
            requires_state={"all_english_swans_are_white": True},
            sets_state={
                "some_pond_birds_not_white": True,
                "conclusion_valid": False,
                "fallacy_committed": "universal_from_particular"
            }
        ))
        self.debug("Created choice: minor_premise → fallacy_universal")

        # FROM: fallacy nodes to retry
        for fallacy_node in ["fallacy_direct_attempt", "fallacy_universal"]:
            self.choices.append(self.create_choice(
                from_node_name=fallacy_node,
                to_node_name="retry",
                text="\"I see my error - let me learn the proper indirect method.\"",
                order=0,
                sets_state={"fallacy_committed": "none"}
            ))
            self.debug(f"Created choice: {fallacy_node} → retry")

        self.choices.append(self.create_choice(
            from_node_name="skip_fallacy",
            to_node_name="major_premise",
            text="\"You're right - let me establish the premises systematically first.\"",
            order=0,
            sets_state={"fallacy_committed": "none"}
        ))
        self.debug("Created choice: skip_fallacy → major_premise")

        # FROM: retry back to indirect method
        self.choices.append(self.create_choice(
            from_node_name="retry",
            to_node_name="indirect_method",
            text="\"Now I understand why indirect proof is necessary - let me try reductio ad absurdum.\"",
            order=0,
            requires_state={
                "$and": [
                    {"all_english_swans_are_white": True},
                    {"some_pond_birds_not_white": True}
                ]
            }
        ))
        self.debug("Created choice: retry → indirect_method")

        self.log(f"  Created {len(self.choices)} choices")
        test_results["choice_ids"] = [c["id"] for c in self.choices]

        # =====================================================================
        # STEP 5: VALIDATE STATE SCHEMA
        # =====================================================================
        self.log("\n✅ Validating state schema...")

        validation = self.validate_state_schema()

        if validation.get("is_valid"):
            self.log("  Schema is VALID - all variables defined!")
        else:
            self.log("  Schema has issues:")
            for error in validation.get("errors", []):
                self.log(f"    - {error.get('variable_key')} in {error.get('used_in')}")

        return validation.get("is_valid", False)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create a Carroll Baroco syllogism demonstration story"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--cleanup", action="store_true", help="Delete created story")
    args = parser.parse_args()

    test_results["start_time"] = datetime.now().isoformat()

    print("\n" + "=" * 70)
    print("  CARROLL BAROCO STORY BUILDER")
    print("  Creating a demonstration of indirect proof via reductio ad absurdum (AOO-2)")
    print("=" * 70)

    try:
        # Get authenticated session
        session = get_authenticated_session()
        print(f"\n✓ Authenticated successfully")

        # Create the story builder
        builder = BarocoStoryBuilder(session, verbose=args.verbose)

        # Build the story
        is_valid = builder.build_story()

        # Summary
        print("\n" + "=" * 70)
        print("  STORY CREATION COMPLETE")
        print("=" * 70)
        print(f"\n  Story ID: {builder.story_id}")
        print(f"  Nodes created: {len(builder.nodes)}")
        print(f"  Choices created: {len(builder.choices)}")
        print(f"  State variables: {len(builder.state_vars)}")
        print(f"  Schema valid: {'Yes' if is_valid else 'No'}")

        print("\n  Node Structure:")
        print("  ┌─ intro (START)")
        print("  │   ├─→ major_premise (A: All English swans are white)")
        print("  │   │     └─→ minor_premise (O: Some pond birds are not white)")
        print("  │   │           ├─→ indirect_method")
        print("  │   │           │     └─→ make_assumption")
        print("  │   │           │           └─→ find_contradiction")
        print("  │   │           │                 └─→ valid_conclusion (REDUCTIO SUCCESS) ✓")
        print("  │   │           ├─→ fallacy_direct_attempt → retry")
        print("  │   │           └─→ fallacy_universal → retry")
        print("  │   └─→ skip_fallacy → major_premise")
        print("  └─────────────────────────────────────────────")

        print(f"\n  NEW CONCEPT INTRODUCED:")
        print(f"  🆕 Indirect proof via reductio ad absurdum")
        print(f"  🆕 Proof by contradiction methodology")
        print(f"  🆕 Baroco: the irreducible syllogism")
        print(f"  🆕 Historical significance of swan whiteness example")

        print(f"\n  Play the story at:")
        print(f"  http://localhost:5173/story/{builder.story_id}")

        test_results["success"] = is_valid
        test_results["end_time"] = datetime.now().isoformat()

        # Save results
        with open(RESULTS_FILE, "w") as f:
            json.dump(test_results, f, indent=2)
        print(f"\n  Results saved to: {RESULTS_FILE}")

        print("=" * 70 + "\n")

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