#!/usr/bin/env python3
"""
Carroll Camestres Story - Figure 2 Syllogisms

This script creates a story demonstrating the Camestres syllogism (AEE-2),
which introduces FIGURE 2 - where the middle term is PREDICATE in both premises.

    Major Premise:  "All insects have six legs"      (A proposition: All S are M)
    Minor Premise:  "No arachnids have six legs"     (E proposition: No P are M)
    Conclusion:     "No arachnids are insects"       (E proposition: No P are S)

KEY CONCEPTS INTRODUCED:
- Figure 2: P-M, S-M → S-P (middle term is predicate in both premises)
- Figure 2 specializes in PROVING DISJOINTNESS: when two categories relate 
  differently to the same middle term, Figure 2 proves they're separate
- Term arrangement matters: same terms, different figure = different reasoning
- Distribution patterns change across figures

=============================================================================
ARCHETYPES, PERSONAS, TRAITS, AND QUALITIES TO CREATE
=============================================================================

ARCHETYPES (Categories/Sets):
-----------------------------
1. "Insects" (Minor Term - S)
   - Description: "Six-legged arthropods with three body segments"
   - All members have the trait "Six Legs" (by major premise)
   - Disjoint from Arachnids (by conclusion)

2. "Arachnids" (Major Term - P) 
   - Description: "Eight-legged arthropods with two body segments"
   - No members have "Six Legs" trait (by minor premise)
   - Examples: spiders, scorpions, ticks

3. "Six Legs" (Middle Term - M)
   - Description: "Having exactly six limbs for locomotion"
   - This is actually a TRAIT, but functions as middle term
   - Possessed by ALL insects, NO arachnids

TRAITS (Properties):
--------------------
1. "Six Legs"
   - Description: "Possesses exactly six limbs"
   - Links: ALL Insects → have this trait
   - Links: NO Arachnids → have this trait
   - This trait distribution creates the disjointness

2. "Eight Legs" 
   - Description: "Possesses exactly eight limbs"
   - Links: ALL Arachnids → have this trait
   - CONFLICTS WITH: "Six Legs" (mutually exclusive)

3. "Arthropod"
   - Description: "Segmented body with jointed legs and exoskeleton"
   - Links: Both Insects AND Arachnids → share this broader trait
   - Shows they're related but distinct categories

PERSONAS (Individuals):
-----------------------
1. "Charlotte" (a Garden Spider)
   - Description: "Common orb weaver spider"
   - Member of: Arachnids
   - Has trait: Eight Legs
   - NOT member of: Insects

2. "Buzz" (a Honeybee)
   - Description: "Worker honeybee"
   - Member of: Insects
   - Has trait: Six Legs
   - NOT member of: Arachnids

3. "Tick" (a Blood-feeding Tick)
   - Description: "Parasitic arachnid"
   - Member of: Arachnids
   - Has trait: Eight Legs (though sometimes hard to count!)
   - Edge case for discussion

=============================================================================

Usage:
    python test_carroll_camestres_story.py
    python test_carroll_camestres_story.py --verbose
    python test_carroll_camestres_story.py --cleanup

Output:
    test_results_carroll_camestres.json
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
RESULTS_FILE = "test_results_carroll_camestres.json"

# Test results tracking
test_results = {
    "test_suite": "Carroll Camestres Story (AEE-2)",
    "start_time": None,
    "end_time": None,
    "story_id": None,
    "node_ids": {},
    "choice_ids": {},
    "state_variable_ids": {},
    "success": False,
    "errors": []
}


class CamestresStoryBuilder:
    """Builds a Camestres syllogism story demonstrating Figure 2 reasoning."""

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
        """Build the complete Camestres syllogism story."""

        # =====================================================================
        # STEP 1: CREATE THE STORY
        # =====================================================================
        self.log("\n📖 Creating story...")

        story = self.create_story(
            title="The Naturalist's Discovery: A Study in Figure 2",
            description="""Camestres syllogism (AEE-2) - introducing FIGURE 2 reasoning.

STRUCTURE:
- Major (A): All insects have six legs
- Minor (E): No arachnids have six legs
- Conclusion (E): No arachnids are insects

FIGURE 2 INNOVATION: The middle term "six legs" appears as PREDICATE in both 
premises (P-M, S-M). This creates a fundamentally different reasoning pattern 
from Figure 1.

FIGURE 2 SPECIALIZATION: When two categories relate DIFFERENTLY to the same 
middle term, Figure 2 lets you prove they're DISJOINT. This is the figure 
for proving things are separate.

DOMAIN: Victorian natural history museum exploring arthropod classification, 
demonstrating how structural differences (leg count) determine taxonomic 
boundaries."""
        )
        self.story_id = story["id"]
        test_results["story_id"] = self.story_id
        self.log(f"  Created story: {self.story_id}")

        # =====================================================================
        # STEP 2: DEFINE STATE SCHEMA  
        # =====================================================================
        self.log("\n📋 Creating state schema...")

        # ---------------------------------------------------------------------
        # Premise tracking - note the Figure 2 structure
        # ---------------------------------------------------------------------

        self.state_vars["major_premise"] = self.create_state_variable(
            key="all_insects_have_six_legs",
            value_type="boolean",
            default_value=False,
            category="premises",
            description="Major premise (A): All S are M (All insects have six legs). "
                       "Domain: All members of Archetype 'Insects' possess Trait 'Six Legs'."
        )
        self.debug("Created: all_insects_have_six_legs")

        self.state_vars["minor_premise"] = self.create_state_variable(
            key="no_arachnids_have_six_legs", 
            value_type="boolean",
            default_value=False,
            category="premises",
            description="Minor premise (E): No P are M (No arachnids have six legs). "
                       "Domain: No members of Archetype 'Arachnids' possess Trait 'Six Legs'."
        )
        self.debug("Created: no_arachnids_have_six_legs")

        # ---------------------------------------------------------------------
        # Figure 2 structure tracking - NEW CONCEPT
        # ---------------------------------------------------------------------

        self.state_vars["figure"] = self.create_state_variable(
            key="syllogism_figure",
            value_type="enum",
            enum_values=["figure_1", "figure_2", "figure_3", "figure_4"],
            default_value="figure_2",
            category="structure",
            description="Figure 2: P-M, S-M ∴ P-S pattern. Middle term is PREDICATE in both premises."
        )
        self.debug("Created: syllogism_figure")

        self.state_vars["mood"] = self.create_state_variable(
            key="syllogism_mood",
            value_type="string",
            default_value="",
            category="structure",
            description="Syllogism mood: AEE for Camestres (All-None-None)"
        )
        self.debug("Created: syllogism_mood")

        self.state_vars["middle_term_position"] = self.create_state_variable(
            key="understands_middle_term_position",
            value_type="boolean",
            default_value=False,
            category="structure",
            description="Player understands that Figure 2 has middle term as predicate in both premises"
        )
        self.debug("Created: understands_middle_term_position")

        # ---------------------------------------------------------------------
        # Conclusion and validation tracking
        # ---------------------------------------------------------------------

        self.state_vars["conclusion"] = self.create_state_variable(
            key="no_arachnids_are_insects",
            value_type="boolean",
            default_value=False,
            category="conclusions", 
            description="Valid conclusion (E): No P are S (No arachnids are insects). "
                       "Domain: Archetypes 'Arachnids' and 'Insects' are disjoint due to "
                       "different relationships to Trait 'Six Legs'."
        )
        self.debug("Created: no_arachnids_are_insects")

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
            enum_values=["none", "undistributed_middle", "illicit_major", 
                        "illicit_minor", "affirmative_from_negative", "non_sequitur"],
            default_value="none",
            category="validation",
            description="Type of logical fallacy committed, if any"
        )
        self.debug("Created: fallacy_committed")

        # ---------------------------------------------------------------------
        # Learning progress tracking - Figure 2 concepts
        # ---------------------------------------------------------------------

        self.state_vars["understands_figure_2"] = self.create_state_variable(
            key="understands_figure_2_reasoning",
            value_type="boolean",
            default_value=False,
            category="learning",
            description="Player understands Figure 2 specializes in proving disjointness"
        )
        self.debug("Created: understands_figure_2_reasoning")

        self.state_vars["understands_term_arrangement"] = self.create_state_variable(
            key="understands_term_arrangement_matters",
            value_type="boolean", 
            default_value=False,
            category="learning",
            description="Player grasps that term position affects reasoning pattern"
        )
        self.debug("Created: understands_term_arrangement_matters")

        self.state_vars["different_from_figure_1"] = self.create_state_variable(
            key="distinguishes_from_figure_1",
            value_type="boolean",
            default_value=False,
            category="learning",
            description="Player sees how Figure 2 differs from Figure 1 patterns"
        )
        self.debug("Created: distinguishes_from_figure_1")

        self.log(f"  Created {len(self.state_vars)} state variables")

        # =====================================================================
        # STEP 3: CREATE STORY NODES
        # =====================================================================
        self.log("\n📝 Creating story nodes...")

        # ---------------------------------------------------------------------
        # INTRODUCTION NODE (Start) - Natural History Museum
        # ---------------------------------------------------------------------

        self.nodes["intro"] = self.create_node(
            title="The Natural History Museum",
            content="""# The Natural History Museum, London 1880

You find yourself in the grand arthropod hall of the Natural History Museum, 
where glass cases display specimens of earth's most numerous creatures. 
Sunlight streams through tall windows, illuminating preserved insects and 
spiders in their geometric arrangements.

A distinguished **curator** approaches, her magnifying glass glinting.

*"Ah, a visitor interested in classification! Tell me, can you distinguish 
an insect from a spider at a glance?"*

She gestures to two adjacent cases:

**CASE A: INSECTS**
- Beetles with their six legs spread wide
- Butterflies with delicate six-legged forms
- Bees with their characteristic six-limbed anatomy

**CASE B: ARACHNIDS** 
- Spiders displaying their eight legs
- Scorpions with their eight-legged stance
- Ticks, small but clearly eight-legged

*"The distinction seems obvious, yet the logic behind it is profound. We use 
LEG COUNT as our key differentiator—but how does this simple trait create 
such clear categorical boundaries?"*

She taps her magnifying glass thoughtfully.

*"This is a different kind of logical puzzle than you may have encountered. 
Today we reason not about connections, but about SEPARATION. When two groups 
relate differently to the same trait, logic can prove they must be distinct."*

---

**NEW CHALLENGE - FIGURE 2:**

Previous syllogisms used **Figure 1** (M-P, S-M):
- The middle term was SUBJECT of major, PREDICATE of minor
- Pattern: "All M are P, All S are M → All S are P"

**Figure 2** uses a different arrangement (P-M, S-M):
- The middle term is **PREDICATE in BOTH premises**
- This creates a fundamentally different reasoning pattern
- **Figure 2 specializes in proving things are DIFFERENT**""",
            is_start=True
        )
        self.debug("Created node: intro")

        # ---------------------------------------------------------------------
        # MAJOR PREMISE NODE - All insects have six legs
        # ---------------------------------------------------------------------

        self.nodes["major_premise"] = self.create_node(
            title="The Insect Definition",
            content="""# The Insect Definition

The curator leads you to the insect collection, her eyes gleaming with 
scientific precision.

*"First, we establish what DEFINES an insect. Not size, not habitat, not 
diet—but a simple, countable characteristic."*

She points systematically through the cases:

- **Beetles**: Count them—six legs, always
- **Butterflies**: Six delicate legs supporting their flight
- **Bees**: Six legs for landing and gripping flowers  
- **Ants**: Six legs coordinated in perfect formation
- **Dragonflies**: Six legs, though they prefer to fly

*"Every single insect, without exception, possesses exactly six legs. This 
is not coincidence—it's the structural definition of the class Insecta."*

```
┌─────────────────────────────────────────┐
│           MAJOR PREMISE                 │
│         (A Proposition)                 │
│                                         │
│   "All insects have six legs"           │
│                                         │
│   Logical form: All S are M             │
│   - S (Minor term*) = Insects           │
│   - M (Middle term) = Six Legs          │
│                                         │
│   *Note: In Figure 2, "minor term"      │
│   appears in the MAJOR premise!         │
│                                         │
│   Every insect ∈ {creatures with 6 legs}│
│                                         │
│   ┌─────────────────┐                   │
│   │  Six Legs       │                   │
│   │  ┌───────────┐  │                   │
│   │  │ Insects   │  │                   │
│   │  │ (all of   │  │                   │
│   │  │  them)    │  │                   │
│   │  └───────────┘  │                   │
│   └─────────────────┘                   │
└─────────────────────────────────────────┘
```

*"Do you accept this taxonomic fact? That six legs universally define 
the insect category?"*

---

**DOMAIN MAPPING:**
- This premise asserts: ALL members of Archetype "Insects" possess Trait "Six Legs"
- Universal trait possession: Insects ⊆ {Six-legged creatures}
- This establishes the positive relationship: insects → six legs

**FIGURE 2 PATTERN BEGINS:**
Notice the middle term "Six Legs" appears as the PREDICATE of this premise.
This is different from Figure 1 patterns you may have seen before."""
        )
        self.debug("Created node: major_premise")

        # ---------------------------------------------------------------------
        # MINOR PREMISE NODE - No arachnids have six legs  
        # ---------------------------------------------------------------------

        self.nodes["minor_premise"] = self.create_node(
            title="The Arachnid Distinction",
            content="""# The Arachnid Distinction

The curator now guides you to the arachnid collection, her voice carrying 
the weight of scientific certainty.

*"Now observe the arachnids—spiders, scorpions, ticks. Count their legs."*

You examine the specimens carefully:

- **Garden Spider**: Eight legs in perfect symmetry
- **Scorpion**: Eight legs plus pincers (which are modified limbs)
- **Tick**: Eight tiny legs (though sometimes hard to see)
- **Tarantula**: Eight robust, hairy legs

*"Every arachnid possesses eight legs, never six. This is their defining 
structural characteristic, as universal as the six-leg rule for insects."*

```
┌─────────────────────────────────────────┐
│           MINOR PREMISE                 │
│         (E Proposition)                 │
│                                         │
│   "No arachnids have six legs"          │
│                                         │
│   Logical form: No P are M              │
│   - P (Major term*) = Arachnids         │
│   - M (Middle term) = Six Legs          │
│                                         │
│   *Note: In Figure 2, "major term"      │
│   appears in the MINOR premise!         │
│                                         │
│   Arachnids ∩ {creatures with 6 legs} = ∅│
│                                         │
│   ┌─────────────┐    ┌─────────────┐    │
│   │ Arachnids   │    │ Six Legs    │    │
│   │ (8 legs)    │ ╱  │             │    │
│   │             │╱   │             │    │
│   │ ●●●         │    │             │    │
│   └─────────────┘    └─────────────┘    │
│                                         │
│   Complete exclusion!                   │
└─────────────────────────────────────────┘
```

*"This establishes the NEGATIVE relationship: arachnids are completely 
excluded from the six-legged category."*

*"Notice something crucial: we now have TWO different relationships to 
the SAME middle term—six legs. What can we conclude about the relationship 
between insects and arachnids?"*

---

**DOMAIN MAPPING:**
- This premise asserts: NO members of Archetype "Arachnids" possess Trait "Six Legs"  
- Universal trait exclusion: Arachnids ∩ {Six-legged creatures} = ∅
- This establishes the negative relationship: arachnids → NOT six legs

**FIGURE 2 PATTERN COMPLETE:**
The middle term "Six Legs" now appears as PREDICATE in BOTH premises:
- Major: Insects → Six Legs (positive relationship)
- Minor: Arachnids → NOT Six Legs (negative relationship)

**LOGICAL STRUCTURE SO FAR:**
- Major (A): All S are M ✓ (All insects have six legs)
- Minor (E): No P are M ✓ (No arachnids have six legs)  
- Conclusion: ??? (What about insects and arachnids?)"""
        )
        self.debug("Created node: minor_premise")

        # ---------------------------------------------------------------------
        # CONCLUSION OPTIONS NODE
        # ---------------------------------------------------------------------

        self.nodes["conclusion_options"] = self.create_node(
            title="The Taxonomic Deduction",
            content="""# The Taxonomic Deduction

The curator steps back, her eyes bright with anticipation.

*"Now comes the moment of Figure 2 reasoning. You have established:*
1. *ALL insects have six legs* (positive universal relationship)
2. *NO arachnids have six legs* (negative universal relationship)

*"Two groups, one trait, opposite relationships. What does logic tell us 
about the relationship between insects and arachnids themselves?"*

```
┌─────────────────────────────────────────┐
│         SYLLOGISM STRUCTURE             │
│            (Camestres)                  │
│                                         │
│   Major (A): All S are M                │
│              (All insects have 6 legs)  │
│                                         │
│   Minor (E): No P are M                 │
│              (No arachnids have 6 legs) │
│                                         │
│   ════════════════════════════════════  │
│                                         │
│   Conclusion: ???                       │
│                                         │
│   Visual reasoning:                     │
│                                         │
│       Six Legs                          │
│   ┌─────────────────┐                   │
│   │ ┌───────────────┐ │ ← All insects   │
│   │ │   Insects     │ │   are here      │
│   │ │               │ │                 │
│   │ └───────────────┘ │                 │
│   └─────────────────┘                   │
│              ╱                          │
│      Arachnids  ← Completely excluded   │
│          ●●●       from this circle     │
│                                         │
│   If insects are INSIDE six-legs,       │
│   and arachnids are OUTSIDE six-legs,   │
│   what's the relationship between       │
│   insects and arachnids?                │
└─────────────────────────────────────────┘
```

---

**FIGURE 2 INSIGHT:**
This is the power of Figure 2—when two categories have OPPOSITE relationships 
to the same middle term, they must be completely separate from each other.

**Choose the logical conclusion:**"""
        )
        self.debug("Created node: conclusion_options")

        # ---------------------------------------------------------------------
        # VALID CONCLUSION NODE - Camestres achieved
        # ---------------------------------------------------------------------

        self.nodes["valid_conclusion"] = self.create_node(
            title="Camestres Achieved: Figure 2 Mastery",
            content="""# Camestres Achieved: Figure 2 Mastery

*"No arachnids are insects,"* you declare with confidence.

The curator's face lights up with scholarly delight.

*"Magnificent! You have mastered CAMESTRES and unlocked the power of Figure 2 reasoning!"*

```
┌─────────────────────────────────────────┐
│           VALID SYLLOGISM               │
│            (Camestres)                  │
│                                         │
│   All insects have six legs      (A)    │
│   No arachnids have six legs     (E)    │
│   ────────────────────────────────      │
│   ∴ No arachnids are insects     (E)    │
│                                         │
│   Form: AEE-2 (Camestres)               │
│   Figure: 2 (P-M, S-M ∴ P-S)            │
│   Mood: AEE                             │
│                                         │
│         VALID ✓                         │
└─────────────────────────────────────────┘
```

*"Observe the beautiful logic: Since ALL insects possess six legs, and 
NO arachnids possess six legs, these two groups cannot possibly overlap. 
The middle term—six legs—creates a perfect boundary between them."*

**FIGURE 2 EXPLAINED:**

*"You have discovered why Figure 2 is special:*

**SPECIALIZES IN DISJOINTNESS**: Figure 2 excels at proving categories are 
completely separate. When two groups relate OPPOSITELY to the same trait, 
Figure 2 proves they're disjoint.

**TERM ARRANGEMENT MATTERS**: The middle term appearing as predicate in both 
premises creates this specific reasoning pattern. Same terms in Figure 1 
arrangement wouldn't work the same way.

**DISTRIBUTION PATTERN**: Notice how the terms distribute:
- Major premise: 'Insects' distributed, 'Six Legs' not distributed  
- Minor premise: Both 'Arachnids' and 'Six Legs' distributed
- Conclusion: Both terms distributed (as required for E propositions)

```
    The Figure Comparison:
    ────────────────────
    Figure 1: Proves CONNECTIONS (A ⊆ B ⊆ C → A ⊆ C)
    Figure 2: Proves SEPARATIONS (A ⊆ C, B ∩ C = ∅ → A ∩ B = ∅)
```

*"This is why taxonomists love Figure 2—it's perfect for establishing 
clear categorical boundaries in biological classification!"*

---

**DOMAIN MAPPING:**
- Conclusion establishes: Archetypes "Arachnids" and "Insects" are disjoint
- The trait difference (Six Legs vs. Eight Legs) creates categorical separation
- No individual can be both an arachnid AND an insect simultaneously

**CAMESTRES IN THE LOGICAL TRADITION:**
- One of Aristotle's original valid forms
- The standard example of Figure 2 reasoning  
- Foundation for biological and scientific classification systems""",
            is_end=True
        )
        self.debug("Created node: valid_conclusion")

        # ---------------------------------------------------------------------
        # FALLACY NODE: Undistributed Middle
        # ---------------------------------------------------------------------

        self.nodes["fallacy_undistributed"] = self.create_node(
            title="The Distribution Error",
            content="""# The Distribution Error

*"Some insects are arachnids?"* The curator looks puzzled.

*"Ah, you've committed the fallacy of UNDISTRIBUTED MIDDLE—though it's 
subtle in Figure 2!"*

```
┌─────────────────────────────────────────┐
│              FALLACY                    │
│        Undistributed Middle             │
│                                         │
│   Your reasoning attempted:             │
│   "Some insects have six legs,          │
│    Some arachnids have six legs,        │
│    Therefore some overlap exists"       │
│                                         │
│   But our premises were UNIVERSAL:      │
│   ALL insects have six legs (not some)  │
│   NO arachnids have six legs (not some) │
│                                         │
│   The middle term "six legs" IS         │
│   properly distributed in our premises: │
│   - Major: distributed as predicate     │
│   - Minor: distributed in E proposition │
│                                         │
│   Your error was weakening universal    │
│   premises to particular ones!          │
└─────────────────────────────────────────┘
```

*"In Figure 2, the middle term IS distributed correctly:*

**DISTRIBUTION ANALYSIS:**
- Major premise: "All insects have six legs"
  - 'Insects' distributed (subject of A)
  - 'Six legs' NOT distributed (predicate of A)
- Minor premise: "No arachnids have six legs"  
  - 'Arachnids' distributed (subject of E)
  - 'Six legs' distributed (predicate of E)

The middle term 'Six legs' appears distributed in the minor premise, satisfying 
the distribution requirement.

**THE REAL ERROR:**
You changed our UNIVERSAL premises to particular ones:
- We said: ALL insects have six legs
- We said: NO arachnids have six legs  
- These create complete separation, not partial overlap

---

**DOMAIN INSIGHT:**
- The trait "Six Legs" universally defines insects
- The trait "Six Legs" is universally absent from arachnids
- This creates categorical impossibility of overlap
- No creature can simultaneously have and not have six legs"""
        )
        self.debug("Created node: fallacy_undistributed")

        # ---------------------------------------------------------------------
        # FALLACY NODE: Illicit Major
        # ---------------------------------------------------------------------

        self.nodes["fallacy_illicit_major"] = self.create_node(
            title="The Term Distribution Error",
            content="""# The Term Distribution Error

*"All arachnids are insects?"* The curator shakes her head.

*"You've committed ILLICIT MAJOR—drawing a conclusion about a term that 
wasn't properly distributed in the premises!"*

```
┌─────────────────────────────────────────┐
│              FALLACY                    │
│           Illicit Major                 │
│                                         │
│   Your conclusion: "All arachnids       │
│   are insects" (or similar universal    │
│   statement about arachnids)            │
│                                         │
│   But in our premises, "arachnids"      │
│   (the major term) was only             │
│   distributed in the MINOR premise:     │
│                                         │
│   Major: "All insects have six legs"    │
│   - Arachnids not mentioned here        │
│                                         │
│   Minor: "No arachnids have six legs"   │
│   - Arachnids distributed here ✓        │
│                                         │
│   Rule: To make a universal claim       │
│   about a term in the conclusion,       │
│   that term must be distributed in      │
│   at least one premise.                 │
│                                         │
│   Arachnids ARE distributed (minor      │
│   premise), so the error is elsewhere...│
└─────────────────────────────────────────┘
```

*"Wait, let me reconsider—arachnids ARE distributed in the minor premise. 
The real issue might be the QUALITY of your conclusion.*

**FIGURE 2 REASONING CHECK:**
- All insects → six legs (positive relationship)
- No arachnids → six legs (negative relationship)
- These OPPOSITE relationships to the middle term...
- Must yield a NEGATIVE conclusion about the relationship between insects and arachnids

**THE LOGICAL CHAIN:**
- Insects are IN the six-leg category
- Arachnids are OUT of the six-leg category  
- Therefore: Insects and arachnids are SEPARATE (negative conclusion)

An AFFIRMATIVE conclusion contradicts this separation pattern.

---

**DOMAIN INSIGHT:**
The structural differences (6 legs vs. 8 legs) create biological impossibility 
of category overlap. No creature can be both an insect and an arachnid."""
        )
        self.debug("Created node: fallacy_illicit_major")

        # ---------------------------------------------------------------------
        # FALLACY NODE: Affirmative from Negative
        # ---------------------------------------------------------------------

        self.nodes["fallacy_affirmative"] = self.create_node(
            title="The Quality Contradiction",
            content="""# The Quality Contradiction

*"Some arachnids are insects?"* The curator looks concerned.

*"You've attempted to draw an AFFIRMATIVE conclusion when the premises 
force a NEGATIVE one!"*

```
┌─────────────────────────────────────────┐
│              FALLACY                    │
│    Affirmative from Negative Premise    │
│                                         │
│   Our minor premise is NEGATIVE:        │
│   "NO arachnids have six legs" (E)      │
│                                         │
│   In syllogistic logic:                 │
│   From negative premises,               │
│   only negative conclusions follow.     │
│                                         │
│   The negative premise creates          │
│   SEPARATION, not connection.           │
│                                         │
│   Think about it:                       │
│   Insects ⊆ {six-legged creatures}      │
│   Arachnids ∩ {six-legged creatures} = ∅│
│                                         │
│   This pattern creates DISJOINTNESS     │
│   between insects and arachnids,        │
│   not overlap!                          │
└─────────────────────────────────────────┘
```

*"Here's why Figure 2 forces a negative conclusion:*

**THE SEPARATION PATTERN:**
- Group A (insects) is INCLUDED in middle term (six legs)
- Group B (arachnids) is EXCLUDED from middle term (six legs)
- This creates complete SEPARATION between A and B

**BIOLOGICAL REALITY:**
The trait differences are mutually exclusive:
- Six legs ↔ Eight legs (cannot have both)
- Insect body plan ↔ Arachnid body plan (different architectures)
- These structural differences make overlap impossible

**QUALITY RULE:**
When one premise is negative (E or O), the conclusion must be negative.
The negative premise 'breaks' any potential connection between the terms.

---

**DOMAIN INSIGHT:**
Nature's structural constraints create logical constraints. When body plans 
are incompatible (6-leg vs. 8-leg architecture), categories become mutually 
exclusive."""
        )
        self.debug("Created node: fallacy_affirmative")

        # ---------------------------------------------------------------------
        # RETRY NODE
        # ---------------------------------------------------------------------

        self.nodes["retry"] = self.create_node(
            title="Reconsider the Classification",
            content="""# Reconsider the Classification

The curator offers an encouraging smile.

*"Figure 2 reasoning takes practice—it's quite different from Figure 1 patterns. 
Let's review our taxonomic evidence:*

**Premise 1 (A):** All insects have six legs
- Universal POSITIVE relationship: Insects → Six legs
- Every insect possesses this trait without exception

**Premise 2 (E):** No arachnids have six legs  
- Universal NEGATIVE relationship: Arachnids → NOT six legs
- Complete exclusion from the trait

*"Now, when one group is universally INCLUDED in a trait category, and 
another group is universally EXCLUDED from that same trait category, 
what must be true about the relationship between the two groups themselves?*

```
    ┌───────────────────────────┐
    │       Six Legs            │
    │  ┌─────────────────────┐  │ ← Insects: ALL inside
    │  │      Insects        │  │
    │  │                     │  │
    │  └─────────────────────┘  │
    └───────────────────────────┘
             ╱
        Arachnids ← Completely outside
            ●●●
    
    What's the relationship between Insects and Arachnids?
```

*"Remember: Figure 2 specializes in proving SEPARATION. The conclusion 
should be NEGATIVE (expressing disjointness) and UNIVERSAL (because 
both premises make universal claims)."*

---

**LOGICAL HINT:**
- Subject: Arachnids (from the minor premise)
- Predicate: Insects (from the major premise)  
- Relationship: Complete separation (negative)
- Quantity: Universal (both premises are universal)

Form: "No P are S" → No arachnids are insects"""
        )
        self.debug("Created node: retry")

        # ---------------------------------------------------------------------
        # SKIP PREMISES NODE
        # ---------------------------------------------------------------------

        self.nodes["skip_fallacy"] = self.create_node(
            title="The Hasty Classification",
            content="""# The Hasty Classification

You begin to make taxonomic judgments, but the curator raises her hand.

*"Wait! You cannot classify creatures without first examining their 
structural characteristics systematically."*

```
┌─────────────────────────────────────────┐
│              FALLACY                    │
│       Hasty Generalization              │
│                                         │
│   To determine whether insects and      │
│   arachnids are related or separate,    │
│   we must establish:                    │
│                                         │
│   1. What structural trait defines      │
│      insects? (Leg count? Body plan?)   │
│                                         │
│   2. What structural trait defines      │
│      arachnids? (Same or different?)    │
│                                         │
│   3. Are these traits compatible        │
│      or mutually exclusive?             │
│                                         │
│   Only with this systematic evidence    │
│   can we make valid taxonomic           │
│   conclusions.                          │
└─────────────────────────────────────────┘
```

*"Biological classification requires methodical analysis of structural 
features. We cannot rely on superficial similarities or intuitive 
assumptions."*

*"Let us begin by examining what universally defines each group, starting 
with the insects and their characteristic leg count..."*

---

**DOMAIN INSIGHT:**
- Scientific classification depends on systematic trait analysis
- Structural characteristics (leg count, body segments) determine taxonomic boundaries
- Figure 2 reasoning is essential for establishing categorical separations in biology

**THE SYSTEMATIC APPROACH:**
1. Establish universal traits for first category (major premise)
2. Establish universal traits for second category (minor premise)
3. THEN derive the taxonomic relationship (conclusion)"""
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
            text="\"Teach me how leg count determines taxonomic boundaries.\"",
            order=0,
            sets_state={
                "understands_figure_2_reasoning": False,
                "understands_term_arrangement_matters": False
            }
        ))
        self.debug("Created choice: intro → major_premise")

        self.choices.append(self.create_choice(
            from_node_name="intro", 
            to_node_name="skip_fallacy",
            text="\"Obviously spiders aren't insects - they look completely different!\"",
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
            text="\"I accept this - all insects have exactly six legs.\"",
            order=0,
            sets_state={
                "all_insects_have_six_legs": True,
                "syllogism_mood": "A",
                "understands_middle_term_position": True
            }
        ))
        self.debug("Created choice: major_premise → minor_premise")

        # FROM: minor_premise
        self.choices.append(self.create_choice(
            from_node_name="minor_premise",
            to_node_name="conclusion_options",
            text="\"I see - arachnids are completely excluded from the six-leg category.\"",
            order=0,
            requires_state={"all_insects_have_six_legs": True},
            sets_state={
                "no_arachnids_have_six_legs": True,
                "syllogism_mood": "AE",
                "syllogism_figure": "figure_2",
                "understands_term_arrangement_matters": True,
                "distinguishes_from_figure_1": True
            }
        ))
        self.debug("Created choice: minor_premise → conclusion_options")

        # FROM: conclusion_options - VALID conclusion
        self.choices.append(self.create_choice(
            from_node_name="conclusion_options",
            to_node_name="valid_conclusion",
            text="\"Therefore, no arachnids are insects.\"",
            order=0,
            requires_state={
                "$and": [
                    {"all_insects_have_six_legs": True},
                    {"no_arachnids_have_six_legs": True}
                ]
            },
            sets_state={
                "no_arachnids_are_insects": True,
                "conclusion_valid": True,
                "syllogism_mood": "AEE",
                "understands_figure_2_reasoning": True,
                "fallacy_committed": "none"
            }
        ))
        self.debug("Created choice: conclusion_options → valid_conclusion (CORRECT)")

        # FALLACY choices
        self.choices.append(self.create_choice(
            from_node_name="conclusion_options",
            to_node_name="fallacy_undistributed",
            text="\"Therefore, some insects are arachnids.\"",
            order=1,
            requires_state={
                "$and": [
                    {"all_insects_have_six_legs": True},
                    {"no_arachnids_have_six_legs": True}
                ]
            },
            sets_state={
                "conclusion_valid": False,
                "fallacy_committed": "undistributed_middle"
            }
        ))
        self.debug("Created choice: conclusion_options → fallacy_undistributed")

        self.choices.append(self.create_choice(
            from_node_name="conclusion_options",
            to_node_name="fallacy_affirmative", 
            text="\"Therefore, some arachnids are insects.\"",
            order=2,
            requires_state={
                "$and": [
                    {"all_insects_have_six_legs": True},
                    {"no_arachnids_have_six_legs": True}
                ]
            },
            sets_state={
                "conclusion_valid": False,
                "fallacy_committed": "affirmative_from_negative"
            }
        ))
        self.debug("Created choice: conclusion_options → fallacy_affirmative")

        # FROM: fallacy nodes to retry
        for fallacy_node in ["fallacy_undistributed", "fallacy_affirmative"]:
            self.choices.append(self.create_choice(
                from_node_name=fallacy_node,
                to_node_name="retry",
                text="\"I understand my error - let me reconsider.\"",
                order=0,
                sets_state={"fallacy_committed": "none"}
            ))
            self.debug(f"Created choice: {fallacy_node} → retry")

        self.choices.append(self.create_choice(
            from_node_name="skip_fallacy",
            to_node_name="major_premise", 
            text="\"You're right - let me examine the structural evidence systematically.\"",
            order=0,
            sets_state={"fallacy_committed": "none"}
        ))
        self.debug("Created choice: skip_fallacy → major_premise")

        # FROM: retry back to conclusion
        self.choices.append(self.create_choice(
            from_node_name="retry",
            to_node_name="conclusion_options",
            text="\"Now I understand Figure 2 reasoning - let me draw the correct conclusion.\"",
            order=0,
            requires_state={
                "$and": [
                    {"all_insects_have_six_legs": True},
                    {"no_arachnids_have_six_legs": True}
                ]
            }
        ))
        self.debug("Created choice: retry → conclusion_options")

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
        description="Create a Carroll Camestres syllogism demonstration story"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--cleanup", action="store_true", help="Delete created story")
    args = parser.parse_args()

    test_results["start_time"] = datetime.now().isoformat()

    print("\n" + "=" * 70)
    print("  CARROLL CAMESTRES STORY BUILDER")
    print("  Creating a demonstration of Figure 2 reasoning (AEE-2)")
    print("=" * 70)

    try:
        # Get authenticated session
        session = get_authenticated_session()
        print(f"\n✓ Authenticated successfully")

        # Create the story builder
        builder = CamestresStoryBuilder(session, verbose=args.verbose)

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
        print("  │   ├─→ major_premise (A: All insects have six legs)")
        print("  │   │     └─→ minor_premise (E: No arachnids have six legs)")
        print("  │   │           └─→ conclusion_options")
        print("  │   │                 ├─→ valid_conclusion (E: No arachnids are insects) ✓")
        print("  │   │                 ├─→ fallacy_undistributed → retry")
        print("  │   │                 └─→ fallacy_affirmative → retry")
        print("  │   └─→ skip_fallacy → major_premise")
        print("  └─────────────────────────────────────────────")

        print(f"\n  NEW CONCEPT INTRODUCED:")
        print(f"  🆕 Figure 2 reasoning: P-M, S-M ∴ P-S")
        print(f"  🆕 Middle term as predicate in both premises")
        print(f"  🆕 Figure 2 specializes in proving disjointness")
        print(f"  🆕 Term arrangement affects reasoning pattern")

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