#!/usr/bin/env python3
"""
Carroll Fresison Story - Figure 4 Syllogisms

This script creates a story demonstrating the Fresison syllogism (EIO-4),
which introduces FIGURE 4 - the controversial "artificial" figure.

    Major Premise:  "No fish live on land"                    (E proposition: No M are P)
    Minor Premise:  "Some ocean creatures are fish"           (I proposition: Some S are M)
    Conclusion:     "Some ocean creatures do not live on land" (O proposition: Some S are not P)

KEY CONCEPTS INTRODUCED:
- FIGURE 4: Middle term is predicate of major, subject of minor (P-M, M-S ∴ S-P)
- Historical controversy: Not recognized by Aristotle, considered "artificial"
- Convertibility debate: Can all Figure 4 syllogisms be reduced to other figures?
- "Unnatural" reasoning: Figure 4 feels backwards compared to Figures 1-3

=============================================================================
ARCHETYPES, PERSONAS, TRAITS, AND QUALITIES TO CREATE
=============================================================================

ARCHETYPES (Categories/Sets):
-----------------------------
1. "Fish" (Middle Term - M)
   - Description: "Aquatic vertebrates with gills and fins"
   - NO members have "Land Habitat" trait (by major premise)
   - SOME ocean creatures are members of this set (by minor premise)

2. "Ocean Creatures" (Minor Term - S)  
   - Description: "Various life forms dwelling in marine environments"
   - Some members are Fish (by minor premise)
   - Therefore some do NOT have "Land Habitat" (by conclusion)

3. "Land Habitat" (Major Term - P)
   - Description: "Living primarily on terrestrial surfaces"
   - NO Fish possess this trait (by major premise)
   - NOT possessed by some Ocean Creatures (by conclusion)

TRAITS (Properties):
--------------------
1. "Land Habitat"
   - Description: "Adapted for life on terrestrial surfaces"
   - Links: NO Fish → possess this trait (universal negative)
   - Links: NOT all Ocean Creatures → some lack this trait

2. "Aquatic Adaptation"
   - Description: "Specialized for underwater life"
   - Links: Fish → universally possess this trait
   - Links: Ocean Creatures → many possess this trait

3. "Gill Respiration"
   - Description: "Breathing through gill structures"
   - Links: Fish → defining characteristic
   - Distinguishes aquatic vs. terrestrial life forms

PERSONAS (Individuals):
-----------------------
1. "Nautilus" (a Cephalopod)
   - Description: "Ocean mollusk with spiral shell"
   - Member of: Ocean Creatures
   - NOT member of: Fish (lacks vertebrae)
   - Traits: Aquatic Adaptation, NOT Land Habitat, NOT Gill Respiration

2. "Tuna" (a Marine Fish)
   - Description: "Large pelagic fish, swift ocean predator"
   - Member of: Ocean Creatures, Fish
   - Traits: Aquatic Adaptation, Gill Respiration, NOT Land Habitat

3. "Seagull" (a Coastal Bird)
   - Description: "Shore bird that feeds from ocean"
   - Member of: Ocean-related creatures (but not Ocean Creatures proper)
   - NOT member of: Fish
   - Traits: Land Habitat (nests on land), can exploit ocean resources

=============================================================================

Usage:
    python test_carroll_fresison_story.py
    python test_carroll_fresison_story.py --verbose
    python test_carroll_fresison_story.py --cleanup

Output:
    test_results_carroll_fresison.json
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
RESULTS_FILE = "test_results_carroll_fresison.json"

# Test results tracking
test_results = {
    "test_suite": "Carroll Fresison Story (EIO-4)",
    "start_time": None,
    "end_time": None,
    "story_id": None,
    "node_ids": {},
    "choice_ids": {},
    "state_variable_ids": {},
    "success": False,
    "errors": []
}


class FresisonStoryBuilder:
    """Builds a Fresison syllogism story demonstrating Figure 4 reasoning."""

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
        """Build the complete Fresison syllogism story."""

        # =====================================================================
        # STEP 1: CREATE THE STORY
        # =====================================================================
        self.log("\n📖 Creating story...")

        story = self.create_story(
            title="The Maritime Debate: A Figure 4 Controversy",
            description="""Fresison syllogism (EIO-4) - introducing FIGURE 4, the controversial "artificial" figure.

STRUCTURE:
- Major (E): No fish live on land
- Minor (I): Some ocean creatures are fish  
- Conclusion (O): Some ocean creatures do not live on land

FIGURE 4'S CONTROVERSY: Not recognized by Aristotle, considered "artificial" 
by many logicians. The middle term arrangement (P-M, M-S ∴ S-P) feels 
"backwards" compared to natural reasoning patterns.

HISTORICAL DEBATE: Can all Figure 4 syllogisms be reduced to other figures 
through premise conversion? Is Figure 4 a genuine logical form or merely 
a notational convenience?

DOMAIN: Victorian marine biology expedition exploring ocean diversity, 
examining the relationship between fish, ocean life, and terrestrial 
adaptation in the age of Darwin."""
        )
        self.story_id = story["id"]
        test_results["story_id"] = self.story_id
        self.log(f"  Created story: {self.story_id}")

        # =====================================================================
        # STEP 2: DEFINE STATE SCHEMA
        # =====================================================================
        self.log("\n📋 Creating state schema...")

        # ---------------------------------------------------------------------
        # Premise tracking - Figure 4 structure (P-M, M-S)
        # ---------------------------------------------------------------------

        self.state_vars["major_premise"] = self.create_state_variable(
            key="no_fish_live_on_land",
            value_type="boolean",
            default_value=False,
            category="premises",
            description="Major premise (E): No M are P (No fish live on land). "
                       "Universal negative: Fish ∩ {Land-dwelling creatures} = ∅. "
                       "Domain: NO members of Archetype 'Fish' possess Trait 'Land Habitat'."
        )
        self.debug("Created: no_fish_live_on_land")

        self.state_vars["minor_premise"] = self.create_state_variable(
            key="some_ocean_creatures_are_fish",
            value_type="boolean",
            default_value=False,
            category="premises",
            description="Minor premise (I): Some S are M (Some ocean creatures are fish). "
                       "Partial membership: Ocean Creatures ∩ Fish ≠ ∅. "
                       "Domain: Some members of Archetype 'Ocean Creatures' are also members of 'Fish'."
        )
        self.debug("Created: some_ocean_creatures_are_fish")

        # ---------------------------------------------------------------------
        # Figure 4 structure tracking - NEW CONCEPT
        # ---------------------------------------------------------------------

        self.state_vars["figure"] = self.create_state_variable(
            key="syllogism_figure",
            value_type="enum",
            enum_values=["figure_1", "figure_2", "figure_3", "figure_4"],
            default_value="figure_4",
            category="structure",
            description="Figure 4: P-M, M-S ∴ S-P pattern - the controversial 'artificial' figure"
        )
        self.debug("Created: syllogism_figure")

        self.state_vars["figure_controversy"] = self.create_state_variable(
            key="understands_figure_4_controversy",
            value_type="boolean",
            default_value=False,
            category="structure",
            description="Player understands the historical controversy around Figure 4's validity"
        )
        self.debug("Created: understands_figure_4_controversy")

        self.state_vars["term_arrangement"] = self.create_state_variable(
            key="understands_unnatural_arrangement",
            value_type="boolean",
            default_value=False,
            category="structure",
            description="Player grasps why Figure 4 feels 'backwards' or unnatural"
        )
        self.debug("Created: understands_unnatural_arrangement")

        self.state_vars["reducibility"] = self.create_state_variable(
            key="considers_reducibility",
            value_type="boolean", 
            default_value=False,
            category="structure",
            description="Player has considered whether Figure 4 can be reduced to other figures"
        )
        self.debug("Created: considers_reducibility")

        # ---------------------------------------------------------------------
        # Standard syllogism structure
        # ---------------------------------------------------------------------

        self.state_vars["mood"] = self.create_state_variable(
            key="syllogism_mood",
            value_type="string",
            default_value="",
            category="structure",
            description="Syllogism mood: EIO for Fresison (No-Some-Some not)"
        )
        self.debug("Created: syllogism_mood")

        # ---------------------------------------------------------------------
        # Conclusion and validation tracking
        # ---------------------------------------------------------------------

        self.state_vars["conclusion"] = self.create_state_variable(
            key="some_ocean_creatures_not_land_dwellers",
            value_type="boolean",
            default_value=False,
            category="conclusions",
            description="Valid conclusion (O): Some S are not P (Some ocean creatures do not live on land). "
                       "Domain: Fish members of ocean creatures cannot have land habitat due to "
                       "universal exclusion in major premise."
        )
        self.debug("Created: some_ocean_creatures_not_land_dwellers")

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
            enum_values=["none", "figure_confusion", "universal_from_particular", 
                        "negative_from_affirmative", "four_terms", "undistributed_middle"],
            default_value="none",
            category="validation",
            description="Type of logical fallacy committed, if any"
        )
        self.debug("Created: fallacy_committed")

        # ---------------------------------------------------------------------
        # Learning progress tracking - Figure 4 concepts
        # ---------------------------------------------------------------------

        self.state_vars["understands_all_figures"] = self.create_state_variable(
            key="understands_all_four_figures",
            value_type="boolean",
            default_value=False,
            category="learning",
            description="Player now understands all four syllogistic figures"
        )
        self.debug("Created: understands_all_four_figures")

        self.state_vars["historical_awareness"] = self.create_state_variable(
            key="appreciates_historical_development",
            value_type="boolean",
            default_value=False,
            category="learning",
            description="Player understands how Figure 4 was added later to Aristotelian logic"
        )
        self.debug("Created: appreciates_historical_development")

        self.state_vars["artificial_nature"] = self.create_state_variable(
            key="recognizes_artificial_nature",
            value_type="boolean",
            default_value=False,
            category="learning",
            description="Player grasps why Figure 4 is considered artificial or forced"
        )
        self.debug("Created: recognizes_artificial_nature")

        self.state_vars["fresison_mastery"] = self.create_state_variable(
            key="mastered_fresison_reasoning",
            value_type="boolean",
            default_value=False,
            category="learning",
            description="Player has mastered Figure 4 reasoning despite its controversy"
        )
        self.debug("Created: mastered_fresison_reasoning")

        self.log(f"  Created {len(self.state_vars)} state variables")

        # =====================================================================
        # STEP 3: CREATE STORY NODES
        # =====================================================================
        self.log("\n📝 Creating story nodes...")

        # ---------------------------------------------------------------------
        # INTRODUCTION NODE (Start) - Victorian Marine Biology Expedition
        # ---------------------------------------------------------------------

        self.nodes["intro"] = self.create_node(
            title="The Marine Biology Expedition",
            content="""# The Marine Biology Expedition, Plymouth 1859

You accompany a distinguished **marine biologist** to the rocky shores of 
Plymouth, where the Royal Navy's specimens from distant waters are being 
catalogued. The salty air carries the excitement of discovery in this age 
of Darwin's revolutionary thinking.

The biologist stands before a series of tanks containing creatures from 
across the world's oceans, notebook in hand.

*"The diversity of ocean life challenges our terrestrial assumptions. But 
I've encountered a logical puzzle that troubles me—one that even Aristotle 
himself never formally recognized."*

You observe the marine specimens:
- **Tuna and mackerel**: Sleek fish darting through the water
- **Nautilus shells**: Spiral-shelled cephalopods drifting gracefully  
- **Sea anemones**: Flower-like creatures anchored to rocks
- **Dolphins**: Air-breathing mammals visiting the surface

*"Here's what we know with certainty from our studies: no fish can survive 
on land—they require water for respiration and movement."*

*"Yet some of these ocean creatures are indeed fish. What does this tell 
us about where ocean creatures can and cannot live?"*

He pauses, tapping his pen thoughtfully.

*"But here's the peculiar thing—the logical structure required to answer 
this question uses what scholars call 'Figure 4'—an arrangement Aristotle 
never acknowledged. Some say it's artificial, unnecessary. Others argue 
it reveals genuine patterns of reasoning."*

---

**THE FIGURE 4 CONTROVERSY:**

Unlike the three figures we've studied:
- **Figure 1 (M-P, S-M)**: Natural subject-predicate flow
- **Figure 2 (P-M, S-M)**: Specializes in proving disjointness  
- **Figure 3 (M-P, M-S)**: Limited to particular conclusions

**Figure 4 (P-M, M-S)**: Feels "backwards"—predicate first, then subject, 
yielding a subject-predicate conclusion that seems to reverse natural reasoning.""",
            is_start=True
        )
        self.debug("Created node: intro")

        # ---------------------------------------------------------------------
        # MAJOR PREMISE NODE - No fish live on land (E proposition)
        # ---------------------------------------------------------------------

        self.nodes["major_premise"] = self.create_node(
            title="The Fundamental Constraint",
            content="""# The Fundamental Constraint

The marine biologist opens his comparative anatomy text, filled with 
detailed diagrams of respiratory and locomotory systems.

*"Let us begin with a biological absolute: no fish possess the adaptations 
necessary for terrestrial life."*

He shows you the evidence:

- **Gill Respiration**: *"Fish extract oxygen from water, not air"*
- **Fin Structure**: *"Adapted for swimming, useless for land locomotion"*
- **Body Design**: *"Streamlined for fluid dynamics, not terrestrial support"*
- **Osmoregulation**: *"Internal systems require aquatic environment"*

*"This is not a matter of preference or habitat choice—it is physiological 
impossibility. Every fish species we have studied, from the smallest minnow 
to the largest shark, shares this constraint."*

```
┌─────────────────────────────────────────┐
│           MAJOR PREMISE                 │
│         (E Proposition)                 │
│                                         │
│      "No fish live on land"             │
│                                         │
│   Logical form: No M are P              │
│   - M (Middle term) = Fish              │
│   - P (Major term*) = Land Dwellers     │
│                                         │
│   *Figure 4: Major term in major premise│
│                                         │
│   Universal exclusion:                  │
│   Fish ∩ {Land-dwelling creatures} = ∅  │
│                                         │
│   ┌────── Land Dwellers ──────┐         │
│   │                           │         │
│   │     (Mammals, birds,      │         │
│   │      reptiles, insects)   │         │
│   │                           │         │
│   │           NO FISH         │         │
│   │                           │         │
│   └───────────────────────────┘         │
│                                         │
│      ┌─── Fish ────┐                    │
│      │ All aquatic │                    │
│      │ (Completely │                    │
│      │  separate   │                    │
│      │   domain)   │                    │
│      └─────────────┘                    │
└─────────────────────────────────────────┘
```

*"This premise establishes absolute separation between fish and terrestrial 
life—a universal negative that admits no exceptions within our current 
understanding of biology."*

*"Do you accept this physiological constraint?"*

---

**DOMAIN MAPPING:**
- This premise asserts: NO members of Archetype "Fish" possess Trait "Land Habitat"
- Universal exclusion: Fish ∩ {Land-dwelling creatures} = ∅
- Biological basis: Respiratory, locomotory, and osmotic incompatibility

**FIGURE 4 NOTE:**
Notice the unusual term arrangement—we're starting with what will become 
our middle term (Fish) in relation to what will become our major term 
(Land Dwellers). This feels backwards compared to natural reasoning flow."""
        )
        self.debug("Created node: major_premise")

        # ---------------------------------------------------------------------
        # MINOR PREMISE NODE - Some ocean creatures are fish (I proposition)
        # ---------------------------------------------------------------------

        self.nodes["minor_premise"] = self.create_node(
            title="The Ocean's Diversity",
            content="""# The Ocean's Diversity

The marine biologist gestures toward the specimen tanks, where the variety 
of ocean life is on full display.

*"Now observe the remarkable diversity of ocean life—and note that some 
of these creatures are indeed fish."*

You catalog the ocean creatures:

**FISH among ocean creatures:**
- **Tuna**: *"Large predatory fish, clearly vertebrate with gills"*
- **Mackerel**: *"Schooling fish with characteristic fin structure"*  
- **Cod**: *"Bottom-dwelling fish with barbels"*

**NON-FISH among ocean creatures:**
- **Nautilus**: *"Cephalopod mollusk—no vertebrae, different respiration"*
- **Sea anemone**: *"Cnidarian—radial symmetry, no central nervous system"*
- **Dolphin**: *"Marine mammal—lungs, not gills; warm-blooded"*

*"The ocean contains an extraordinary mixture of life forms, but we must be 
precise about which are fish and which are not."*

```
┌─────────────────────────────────────────┐
│           MINOR PREMISE                 │
│         (I Proposition)                 │
│                                         │
│   "Some ocean creatures are fish"       │
│                                         │
│   Logical form: Some S are M            │
│   - S (Minor term*) = Ocean Creatures   │
│   - M (Middle term) = Fish              │
│                                         │
│   *Figure 4: Minor term in minor premise│
│                                         │
│   Partial membership: Ocean Creatures   │
│   ∩ Fish ≠ ∅                           │
│                                         │
│      Ocean Creatures                    │
│   ┌─────────────────────┐               │
│   │ ○○○ Fish            │               │
│   │ (Tuna, mackerel,    │               │
│   │  cod, sharks...)    │               │
│   │                     │               │
│   │ ●●● Non-fish        │               │
│   │ (Mollusks, mammals, │               │
│   │  cnidarians...)     │               │
│   └─────────────────────┘               │
│                                         │
│   ○ = Fish among ocean creatures        │
│   ● = Non-fish ocean creatures          │
└─────────────────────────────────────────┘
```

*"This I proposition—'Some ocean creatures are fish'—establishes the crucial 
overlap. The ocean is not exclusively fish, but fish are definitely present 
among its inhabitants."*

*"Now we face the Figure 4 challenge: what can we conclude about ocean 
creatures and land-dwelling capability?"*

---

**DOMAIN MAPPING:**
- This premise asserts: Some members of Archetype "Ocean Creatures" are also members of "Fish"
- Partial membership: Ocean Creatures ∩ Fish ≠ ∅
- Biological reality: Fish represent a subset of total ocean biodiversity

**FIGURE 4 STRUCTURE SO FAR:**
- Major (E): No M are P ✓ (No fish live on land)
- Minor (I): Some S are M ✓ (Some ocean creatures are fish)
- Conclusion: ??? (What about ocean creatures and land dwelling?)

**THE UNNATURAL FLOW:**
Notice how we reasoned P-M (land-fish), then S-M (ocean-fish), to reach 
S-P (ocean-land). This feels backwards compared to the natural subject-predicate 
progression of Figure 1!"""
        )
        self.debug("Created node: minor_premise")

        # ---------------------------------------------------------------------
        # FIGURE 4 EXPLANATION NODE - The controversial structure
        # ---------------------------------------------------------------------

        self.nodes["figure_4_explanation"] = self.create_node(
            title="The Controversial Figure",
            content="""# The Controversial Figure

The marine biologist sets down his specimens and turns to face you directly, 
his expression both excited and troubled.

*"Before we conclude, you must understand why this reasoning pattern troubles 
philosophers of logic. We are using Figure 4—the figure Aristotle never 
formally recognized."*

**THE FOUR FIGURES COMPARED:**

```
┌─────────────────────────────────────────┐
│            THE FOUR FIGURES             │
│                                         │
│  Figure 1 (M-P, S-M → S-P)             │
│  "Natural": Subject flows to predicate  │
│  Example: All M are P                   │
│           All S are M                   │
│           ∴ All S are P                 │
│                                         │
│  Figure 2 (P-M, S-M → S-P)             │
│  "Disjoint": Proves differences         │
│                                         │
│  Figure 3 (M-P, M-S → S-P)             │
│  "Particular": Only particular conclusions│
│                                         │
│  Figure 4 (P-M, M-S → S-P) ⚡          │
│  "Artificial": Feels backwards          │
│  Our case: No P are M                   │
│            Some S are M                 │
│            ∴ Some S are not P           │
└─────────────────────────────────────────┘
```

*"Figure 4 was added to Aristotelian logic much later. Many scholars argue 
it's unnecessary—that every Figure 4 syllogism can be converted to another 
figure through premise manipulation."*

**THE CONTROVERSY:**

**CRITICS argue:** *"Figure 4 is artificial. You could convert 'No fish live on land' 
to 'No land-dwellers are fish' and use Figure 1 instead!"*

**DEFENDERS respond:** *"But that changes the natural expression of the thought. 
Sometimes Figure 4 captures how we actually reason!"*

**THE QUESTION:** *Is Figure 4 a genuine logical structure, or merely a 
notational convenience that obscures clearer reasoning patterns?*

*"What do you think? Should we proceed with this 'backwards' reasoning, 
or does it feel too unnatural?"*

---

**WHY FIGURE 4 FEELS UNNATURAL:**
- We start with major term (Land) before introducing minor term (Ocean Creatures)
- The middle term (Fish) connects them, but in reverse order
- The conclusion flows back from minor to major, opposite to Figure 1's flow

**HISTORICAL DEVELOPMENT:**
Aristotle recognized only three figures. Figure 4 was systematized by later 
logicians who noticed valid argument patterns that didn't fit the original schema."""
        )
        self.debug("Created node: figure_4_explanation")

        # ---------------------------------------------------------------------
        # PROCEED WITH FIGURE 4 NODE - Accept the controversial structure
        # ---------------------------------------------------------------------

        self.nodes["proceed_figure_4"] = self.create_node(
            title="Embracing the Unconventional",
            content="""# Embracing the Unconventional

The marine biologist nods approvingly at your willingness to explore 
unconventional reasoning.

*"Excellent! Sometimes truth emerges through patterns that feel unnatural 
at first. Let us follow Figure 4's logic wherever it leads."*

**OUR FIGURE 4 SYLLOGISM:**
- **Major (E)**: No fish live on land
- **Minor (I)**: Some ocean creatures are fish
- **Conclusion**: ???

*"Now, if some ocean creatures are fish, and no fish can live on land, 
what must be true about those particular ocean creatures that are fish?"*

```
┌─────────────────────────────────────────┐
│         FIGURE 4 REASONING              │
│                                         │
│   Step 1: No fish live on land          │
│   (Universal exclusion of fish from     │
│   terrestrial habitat)                  │
│                                         │
│   Step 2: Some ocean creatures are fish │
│   (Partial overlap: ocean life includes │
│   fish among other forms)               │
│                                         │
│   Step 3: Therefore...?                 │
│   Those ocean creatures that ARE fish   │
│   must inherit fish's constraint!       │
│                                         │
│   If fish cannot live on land,          │
│   and some ocean creatures are fish,    │
│   then some ocean creatures cannot      │
│   live on land.                         │
└─────────────────────────────────────────┘
```

*"The logic flows through the middle term—fish—which connects our premises 
in this unusual arrangement. The fish in the ocean inherit all of fish's 
constraints, including the inability to survive on land."*

*"Can you state the conclusion that follows from this Figure 4 reasoning?"*

---

**THE FIGURE 4 FLOW:**
1. **Major premise** links middle term (Fish) to major term (Land Habitat): No connection
2. **Minor premise** links minor term (Ocean Creatures) to middle term (Fish): Partial connection  
3. **Conclusion** must link minor term (Ocean Creatures) to major term (Land Habitat): ???

**LOGICAL NECESSITY:**
If some ocean creatures share the identity "fish," they must share fish's 
properties—including the constraint against terrestrial life."""
        )
        self.debug("Created node: proceed_figure_4")

        # ---------------------------------------------------------------------
        # VALID CONCLUSION NODE - Fresison mastery achieved
        # ---------------------------------------------------------------------

        self.nodes["valid_conclusion"] = self.create_node(
            title="Fresison Mastery: The Artificial Made Natural",
            content="""# Fresison Mastery: The Artificial Made Natural

*"Some ocean creatures do not live on land,"* you conclude, having navigated 
the backwards logic of Figure 4.

The marine biologist beams with scholarly satisfaction.

*"Magnificent! You have mastered FRESISON and conquered the controversial Figure 4!"*

```
┌─────────────────────────────────────────┐
│           VALID SYLLOGISM               │
│             (Fresison)                  │
│                                         │
│   No fish live on land            (E)   │
│   Some ocean creatures are fish   (I)   │
│   ─────────────────────────────────      │
│   ∴ Some ocean creatures do not   (O)   │
│     live on land                        │
│                                         │
│   Form: EIO-4 (Fresison)                │
│   Figure: 4 (P-M, M-S ∴ S-P)            │
│   Mood: EIO                             │
│   Status: CONTROVERSIAL ⚡               │
│                                         │
│         VALID ✓                         │
└─────────────────────────────────────────┘
```

*"Observe what we've accomplished with this artificial figure:*

**COMPLETE FIGURE MASTERY**: You now understand all four figures of syllogistic logic:
- Figure 1: Natural subject-predicate flow
- Figure 2: Specializes in proving disjointness  
- Figure 3: Limited to particular conclusions
- Figure 4: The controversial "backwards" arrangement

**BIOLOGICAL INSIGHT**: The fish among ocean creatures inherit fish's constraints. 
Tuna, mackerel, and sharks cannot survive on land, regardless of their ocean 
habitat. The conclusion captures a real biological truth.

**HISTORICAL PERSPECTIVE**: You've engaged with a centuries-old debate about 
logical necessity versus notational convenience. Figure 4 may feel artificial, 
but it validly captures certain reasoning patterns.

```
    Complete Syllogistic Mastery:
    ─────────────────────────
    Barbara (AAA-1):   Figure 1 ✓
    Celarent (EAE-1):  Figure 1 ✓
    Darii (AII-1):     Figure 1 ✓
    Ferio (EIO-1):     Figure 1 ✓
    Camestres (AEE-2): Figure 2 ✓
    Baroco (AOO-2):    Figure 2 ✓
    Disamis (IAI-3):   Figure 3 ✓
    Fresison (EIO-4):  Figure 4 ✓ [ARTIFICIAL]
```

*"Fresison completes your understanding of syllogistic figures, though the 
debate about Figure 4's legitimacy continues. Some say it's unnecessary—that 
'No fish live on land' converts to 'No land-dwellers are fish,' yielding a 
Figure 1 syllogism instead."*

*"But you've proven that even artificial structures can capture valid reasoning!"*

---

**DOMAIN MAPPING:**
- Conclusion establishes: Some members of "Ocean Creatures" do NOT possess "Land Habitat"
- Specifically: Fish among ocean creatures (tuna, sharks, etc.) cannot be terrestrial
- Biological reality: Aquatic adaptations preclude terrestrial survival

**FRESISON IN LOGICAL HISTORY:**
- Completes the four-figure system developed after Aristotle
- Tests the boundaries between genuine logic and notational artifacts
- Demonstrates that "unnatural" reasoning patterns can still be valid

You have conquered the most controversial syllogism in classical logic!""",
            is_end=True
        )
        self.debug("Created node: valid_conclusion")

        # ---------------------------------------------------------------------
        # FALLACY NODE: Figure confusion
        # ---------------------------------------------------------------------

        self.nodes["fallacy_figure_confusion"] = self.create_node(
            title="The Figure Mix-Up",
            content="""# The Figure Mix-Up

*"All ocean creatures live on land?"* The marine biologist looks confused 
and concerned.

*"You've made a fundamental error in handling Figure 4's unusual structure! 
This conclusion contradicts both logical validity and biological reality."*

```
┌─────────────────────────────────────────┐
│              FALLACY                    │
│          Figure Confusion               │
│                                         │
│   Your reasoning seems to be:           │
│   • No fish live on land               │
│   • Some ocean creatures are fish       │
│   • Therefore: All ocean creatures      │
│     live on land                        │
│                                         │
│   Problems:                             │
│   1. You've reached an AFFIRMATIVE      │
│      conclusion from a NEGATIVE premise │
│   2. You've made a UNIVERSAL conclusion │
│      from PARTICULAR evidence           │
│   3. You've contradicted the major      │
│      premise about fish constraints     │
└─────────────────────────────────────────┘
```

*"This error reveals the danger of Figure 4's unnatural arrangement. When 
terms flow backwards, it's easy to lose track of logical relationships!"*

**WHAT WENT WRONG:**
- **Negative premise ignored**: Your conclusion is affirmative, but we have 
  "No fish live on land" as a premise—negative premises yield negative conclusions.
- **Universal from particular**: You concluded "All ocean creatures..." but 
  our minor premise only claims "Some ocean creatures are fish."
- **Biological impossibility**: Fish (which include some ocean creatures) 
  cannot live on land, so ocean creatures cannot all be terrestrial.

**FIGURE 4 GUIDANCE:**
Figure 4's backwards flow makes it crucial to track:
1. What the middle term (Fish) can and cannot do
2. Which ocean creatures share that middle term identity
3. How those shared constraints flow to the conclusion

*"The correct reasoning: if fish cannot live on land, and some ocean creatures 
are fish, then SOME ocean creatures cannot live on land—not all can!"*

---

**METHODOLOGICAL LESSON:**
Figure 4's artificial structure requires extra care. The backwards reasoning 
flow can lead to errors in tracking term relationships and logical constraints."""
        )
        self.debug("Created node: fallacy_figure_confusion")

        # ---------------------------------------------------------------------
        # FALLACY NODE: Dismiss Figure 4
        # ---------------------------------------------------------------------

        self.nodes["fallacy_dismiss_figure_4"] = self.create_node(
            title="The Dismissal Error",
            content="""# The Dismissal Error

*"Figure 4 is nonsense—let's ignore it?"* The marine biologist shakes his head.

*"I understand the temptation to dismiss Figure 4 as artificial, but that 
would be a scholarly error. Valid reasoning patterns exist regardless of 
whether they feel natural to us!"*

```
┌─────────────────────────────────────────┐
│              FALLACY                    │
│       Dismissing Valid Structure        │
│                                         │
│   The dismissal error assumes:          │
│   • If a logical form feels unnatural,  │
│     it must be invalid                  │
│   • Only "comfortable" reasoning        │
│     patterns are worth studying         │
│   • Historical late development means   │
│     logical invalidity                  │
│                                         │
│   But this confuses:                    │
│   - Psychological comfort with validity │
│   - Historical accident with logical   │
│     necessity                           │
│   - Notational convenience with truth  │
└─────────────────────────────────────────┘
```

*"The history of logic is full of initially uncomfortable ideas that proved 
essential:*

**EXAMPLES OF INITIALLY 'UNNATURAL' LOGICAL ADVANCES:**
- **Zero**: Ancient mathematicians resisted the concept of 'nothing as something'
- **Negative numbers**: 'Less than nothing' seemed impossible
- **Imaginary numbers**: Still called 'imaginary' despite mathematical utility
- **Non-Euclidean geometry**: Violated 'common sense' about parallel lines

*"Figure 4 may feel backwards, but the test is validity, not comfort."*

**THE CHALLENGE REMAINS:**
We still need to determine what follows from:
- No fish live on land
- Some ocean creatures are fish

*"Rather than dismissing the structure, let's work through it systematically. 
Even if Figure 4 is ultimately reducible to other figures, the reduction 
itself is instructive!"*

---

**METHODOLOGICAL PRINCIPLE:**
Logical validity is independent of psychological comfort. Forms of reasoning 
that feel artificial may still capture genuine patterns of inference.

**THE SCHOLARLY APPROACH:**
Engage with controversial structures before dismissing them. Understanding 
why something feels artificial often reveals important insights about both 
logic and human reasoning preferences."""
        )
        self.debug("Created node: fallacy_dismiss_figure_4")

        # ---------------------------------------------------------------------
        # CONVERSION ATTEMPT NODE - Try to reduce to another figure
        # ---------------------------------------------------------------------

        self.nodes["conversion_attempt"] = self.create_node(
            title="The Reduction Attempt",
            content="""# The Reduction Attempt

*"Let's convert this to Figure 1 instead!"* you suggest, attempting to avoid 
Figure 4's uncomfortable backwards flow.

The marine biologist nods thoughtfully.

*"An excellent instinct! Many logicians argue that Figure 4 is unnecessary 
because it can be reduced to other figures. Let's attempt the conversion 
and see what happens."*

**CONVERSION STRATEGY:**
Convert "No fish live on land" to "No land-dwellers are fish"

**ATTEMPTED FIGURE 1 RECONSTRUCTION:**
- Major: No land-dwellers are fish (E - converted from original)
- Minor: Some ocean creatures are fish (I - unchanged)
- Middle term: Fish
- Conclusion: ???

*"But wait—this creates a problem! In Figure 1, we need S-M in the minor 
premise, but we have 'Some ocean creatures are fish' (S are M), not 'Some 
fish are ocean creatures' (M are S)."*

```
┌─────────────────────────────────────────┐
│         CONVERSION COMPLICATIONS        │
│                                         │
│   Original Figure 4:                    │
│   Major (E): No fish live on land       │
│   Minor (I): Some ocean creatures       │
│              are fish                   │
│                                         │
│   Attempted Figure 1 conversion:        │
│   Major (E): No land-dwellers are fish  │
│   Minor (I): Some fish are ocean        │
│              creatures (CONVERTED?)     │
│                                         │
│   Problem: Does "Some ocean creatures   │
│   are fish" convert to "Some fish are   │
│   ocean creatures"?                     │
│                                         │
│   Answer: YES for I propositions!       │
│   But now we need different terms...    │
└─────────────────────────────────────────┘
```

*"Actually, I propositions do convert validly—'Some A are B' becomes 'Some B are A.' 
So we could say 'Some fish are ocean creatures.' But notice how this changes 
the natural expression of our biological knowledge!"*

*"We naturally think 'Some ocean creatures are fish' (ocean contains fish) 
rather than 'Some fish are ocean creatures' (fish found in ocean). The 
conversion is valid but feels forced."*

*"This reveals Figure 4's purpose—sometimes it captures the natural flow 
of our thinking better than converted alternatives!"*

---

**THE REDUCTION DEBATE:**
- **Formal equivalence**: Figure 4 can often be reduced to other figures
- **Natural expression**: The reduction may distort how we naturally frame the problem
- **Cognitive reality**: Figure 4 might reflect genuine patterns in human reasoning

*"Should we proceed with Figure 4 as naturally expressed, or use the 
converted Figure 1 version? Both are logically valid!"*"""
        )
        self.debug("Created node: conversion_attempt")

        # ---------------------------------------------------------------------
        # RETRY NODE
        # ---------------------------------------------------------------------

        self.nodes["retry"] = self.create_node(
            title="Reconsidering Figure 4",
            content="""# Reconsidering Figure 4

The marine biologist offers a patient, encouraging smile.

*"Figure 4's backwards arrangement challenges even experienced logicians. 
Let's review why this unusual structure still produces valid reasoning."*

**OUR ESTABLISHED PREMISES:**
- **Major premise**: No fish live on land (absolute biological constraint)
- **Minor premise**: Some ocean creatures are fish (partial overlap)

**THE FIGURE 4 STRUCTURE:**
Unlike natural Figure 1 flow (M-P, S-M → S-P), we have:
- P-M: No [Land Habitat] are possessed by [Fish]
- M-S: Some [Ocean Creatures] are [Fish]  
- S-P: Some [Ocean Creatures] do not have [Land Habitat]

**WHY IT WORKS:**
```
    Figure 4 Logic Flow:
    ──────────────────
    
    1. Fish are EXCLUDED from land habitat
       (Universal negative constraint)
    
    2. Some ocean creatures ARE fish
       (Share fish identity and constraints)
    
    3. Therefore: Those ocean creatures that are fish
       inherit fish's exclusion from land habitat
    
    4. Conclusion: Some ocean creatures 
       (the fish ones) do not live on land
```

*"The middle term—fish—carries constraints from the major premise into the 
minor premise. Ocean creatures that are fish inherit all of fish's properties, 
including the inability to survive terrestrially."*

*"Ready to trace through Figure 4's logic properly?"*

---

**METHODOLOGICAL INSIGHT:**
Figure 4's validity doesn't depend on feeling natural. The logical relationships 
are sound even when the term arrangement feels backwards or artificial."""
        )
        self.debug("Created node: retry")

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
            text="\"Tell me about these biological constraints and Figure 4's controversy.\"",
            order=0,
            sets_state={
                "understands_figure_4_controversy": False,
                "understands_unnatural_arrangement": False
            }
        ))
        self.debug("Created choice: intro → major_premise")

        # FROM: major_premise
        self.choices.append(self.create_choice(
            from_node_name="major_premise",
            to_node_name="minor_premise",
            text="\"I accept this - fish are physiologically constrained to aquatic environments.\"",
            order=0,
            sets_state={
                "no_fish_live_on_land": True,
                "syllogism_mood": "E"
            }
        ))
        self.debug("Created choice: major_premise → minor_premise")

        # FROM: minor_premise
        self.choices.append(self.create_choice(
            from_node_name="minor_premise",
            to_node_name="figure_4_explanation",
            text="\"I see the ocean's diversity, but why is this reasoning pattern controversial?\"",
            order=0,
            requires_state={"no_fish_live_on_land": True},
            sets_state={
                "some_ocean_creatures_are_fish": True,
                "syllogism_mood": "EI",
                "syllogism_figure": "figure_4"
            }
        ))
        self.debug("Created choice: minor_premise → figure_4_explanation")

        # FROM: figure_4_explanation
        self.choices.append(self.create_choice(
            from_node_name="figure_4_explanation",
            to_node_name="proceed_figure_4",
            text="\"Figure 4 may be controversial, but let's see where this backwards reasoning leads.\"",
            order=0,
            requires_state={
                "$and": [
                    {"no_fish_live_on_land": True},
                    {"some_ocean_creatures_are_fish": True}
                ]
            },
            sets_state={
                "understands_figure_4_controversy": True,
                "understands_unnatural_arrangement": True,
                "considers_reducibility": False
            }
        ))
        self.debug("Created choice: figure_4_explanation → proceed_figure_4")

        self.choices.append(self.create_choice(
            from_node_name="figure_4_explanation",
            to_node_name="conversion_attempt",
            text="\"This feels too artificial - can't we convert this to Figure 1 instead?\"",
            order=1,
            requires_state={
                "$and": [
                    {"no_fish_live_on_land": True},
                    {"some_ocean_creatures_are_fish": True}
                ]
            },
            sets_state={
                "understands_figure_4_controversy": True,
                "considers_reducibility": True
            }
        ))
        self.debug("Created choice: figure_4_explanation → conversion_attempt")

        self.choices.append(self.create_choice(
            from_node_name="figure_4_explanation",
            to_node_name="fallacy_dismiss_figure_4",
            text="\"Figure 4 is artificial nonsense - let's ignore it completely.\"",
            order=2,
            sets_state={
                "fallacy_committed": "figure_confusion",
                "understands_figure_4_controversy": False
            }
        ))
        self.debug("Created choice: figure_4_explanation → fallacy_dismiss_figure_4")

        # FROM: proceed_figure_4
        self.choices.append(self.create_choice(
            from_node_name="proceed_figure_4",
            to_node_name="valid_conclusion",
            text="\"Some ocean creatures do not live on land - the fish inherit fish's constraints!\"",
            order=0,
            requires_state={
                "$and": [
                    {"understands_figure_4_controversy": True},
                    {"understands_unnatural_arrangement": True}
                ]
            },
            sets_state={
                "some_ocean_creatures_not_land_dwellers": True,
                "conclusion_valid": True,
                "syllogism_mood": "EIO",
                "understands_all_four_figures": True,
                "fresison_mastery": True,
                "appreciates_historical_development": True,
                "recognizes_artificial_nature": True,
                "fallacy_committed": "none"
            }
        ))
        self.debug("Created choice: proceed_figure_4 → valid_conclusion (CORRECT)")

        self.choices.append(self.create_choice(
            from_node_name="proceed_figure_4",
            to_node_name="fallacy_figure_confusion",
            text="\"Therefore, all ocean creatures live on land.\"",
            order=1,
            sets_state={
                "conclusion_valid": False,
                "fallacy_committed": "universal_from_particular"
            }
        ))
        self.debug("Created choice: proceed_figure_4 → fallacy_figure_confusion")

        # FROM: conversion_attempt  
        self.choices.append(self.create_choice(
            from_node_name="conversion_attempt",
            to_node_name="proceed_figure_4",
            text="\"The conversion works but feels forced - let's use Figure 4 as naturally expressed.\"",
            order=0,
            sets_state={
                "considers_reducibility": True,
                "recognizes_artificial_nature": True
            }
        ))
        self.debug("Created choice: conversion_attempt → proceed_figure_4")

        # FROM: fallacy nodes to retry
        for fallacy_node in ["fallacy_figure_confusion", "fallacy_dismiss_figure_4"]:
            self.choices.append(self.create_choice(
                from_node_name=fallacy_node,
                to_node_name="retry",
                text="\"I see my error - let me approach Figure 4 more carefully.\"",
                order=0,
                sets_state={"fallacy_committed": "none"}
            ))
            self.debug(f"Created choice: {fallacy_node} → retry")

        # FROM: retry back to proceed
        self.choices.append(self.create_choice(
            from_node_name="retry",
            to_node_name="proceed_figure_4",
            text="\"Now I understand - Figure 4's backwards structure still produces valid reasoning.\"",
            order=0,
            requires_state={
                "$and": [
                    {"no_fish_live_on_land": True},
                    {"some_ocean_creatures_are_fish": True}
                ]
            },
            sets_state={
                "understands_figure_4_controversy": True,
                "understands_unnatural_arrangement": True
            }
        ))
        self.debug("Created choice: retry → proceed_figure_4")

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
        description="Create a Carroll Fresison syllogism demonstration story"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--cleanup", action="store_true", help="Delete created story")
    args = parser.parse_args()

    test_results["start_time"] = datetime.now().isoformat()

    print("\n" + "=" * 70)
    print("  CARROLL FRESISON STORY BUILDER")
    print("  Creating a demonstration of Figure 4 reasoning - the controversial 'artificial' figure (EIO-4)")
    print("=" * 70)

    try:
        # Get authenticated session
        session = get_authenticated_session()
        print(f"\n✓ Authenticated successfully")

        # Create the story builder
        builder = FresisonStoryBuilder(session, verbose=args.verbose)

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
        print("  │   └─→ major_premise (E: No fish live on land)")
        print("  │         └─→ minor_premise (I: Some ocean creatures are fish)")
        print("  │               └─→ figure_4_explanation")
        print("  │                     ├─→ proceed_figure_4")
        print("  │                     │     └─→ valid_conclusion (FIGURE 4 SUCCESS) ✓")
        print("  │                     │     └─→ fallacy_figure_confusion → retry")
        print("  │                     ├─→ conversion_attempt → proceed_figure_4")
        print("  │                     └─→ fallacy_dismiss_figure_4 → retry")
        print("  └─────────────────────────────────────────────────────────")

        print(f"\n  NEW CONCEPT INTRODUCED:")
        print(f"  🆕 Figure 4: The controversial 'artificial' figure")
        print(f"  🆕 P-M, M-S ∴ S-P reasoning pattern")  
        print(f"  🆕 Historical debate about logical necessity vs. convenience")
        print(f"  🆕 Complete four-figure syllogistic mastery")

        print(f"\n  Play the story at:")
        print(f"  http://localhost:5173/stories/{builder.story_id}/play")

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