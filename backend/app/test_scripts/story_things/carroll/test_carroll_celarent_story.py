#!/usr/bin/env python3
"""
Carroll Celarent Story - Negative Propositions

This script creates a story demonstrating the Celarent syllogism (EAE-1),
which introduces NEGATIVE propositions (E type: "No X are Y").

    Major Premise:  "No reptiles are mammals"     (E proposition: No M are P)
    Minor Premise:  "All snakes are reptiles"     (A proposition: All S are M)
    Conclusion:     "No snakes are mammals"       (E proposition: No S are P)

KEY CONCEPTS INTRODUCED:
- E propositions: Universal Negative ("No X are Y")
- Set DISJOINTNESS: M ∩ P = ∅ (reptiles and mammals don't overlap)
- Negative conclusions from negative premises
- Distribution in negative propositions (both terms distributed in E)

=============================================================================
ARCHETYPES, PERSONAS, TRAITS, AND QUALITIES TO CREATE
=============================================================================

ARCHETYPES (Categories/Sets):
-----------------------------
1. "Reptiles"
   - Description: "Cold-blooded vertebrates with scales"
   - Represents the MIDDLE TERM (M)
   - Key property: Cold-blooded, egg-laying (mostly), scales

2. "Mammals"
   - Description: "Warm-blooded vertebrates that nurse their young"
   - Represents the MAJOR TERM (P)
   - Key property: Warm-blooded, fur/hair, live birth (mostly)

3. "Snakes"
   - Description: "Legless reptiles of the suborder Serpentes"
   - Represents the MINOR TERM (S)
   - SUBSET OF: Reptiles

4. "Birds"
   - Description: "Warm-blooded egg-laying vertebrates with feathers"
   - For comparison: Also not mammals, but not reptiles either

TRAITS (Properties):
--------------------
1. "Cold-blooded" (Ectothermic)
   - Description: "Body temperature regulated by environment"
   - Links: Reptiles → has this trait
   - CONFLICTS WITH: "Warm-blooded"

2. "Warm-blooded" (Endothermic)
   - Description: "Body temperature internally regulated"
   - Links: Mammals → has this trait
   - CONFLICTS WITH: "Cold-blooded"

3. "Has Scales"
   - Description: "Body covered in protective scales"
   - Links: Reptiles → has this, Snakes → has this

4. "Has Fur or Hair"
   - Description: "Body has hair follicles producing fur or hair"
   - Links: Mammals → has this
   - NOTE: This is a DEFINING trait of mammals

5. "Legless"
   - Description: "Has no legs"
   - Links: Snakes → has this (defines snakes among reptiles)

PERSONAS (Individuals):
-----------------------
1. "Monty" (a Python snake)
   - Description: "A ball python, common pet snake"
   - Member of: Snakes, Reptiles
   - NOT member of: Mammals

2. "Leo" (a Lion)
   - Description: "King of the jungle, an African lion"
   - Member of: Mammals
   - NOT member of: Reptiles

3. "Gex" (a Gecko)
   - Description: "A small lizard"
   - Member of: Reptiles
   - NOT member of: Snakes, Mammals

QUALITIES (Derived):
--------------------
1. "Requires External Heat"
   - Derived from: Trait "Cold-blooded"
   - Applied to: Reptiles, Snakes

=============================================================================

Usage:
    python test_carroll_celarent_story.py
    python test_carroll_celarent_story.py --verbose

Output:
    test_results_carroll_celarent.json
"""

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
RESULTS_FILE = "test_results_carroll_celarent.json"

# Test results tracking
test_results = {
    "test_suite": "Carroll Celarent Story (EAE-1)",
    "start_time": None,
    "end_time": None,
    "story_id": None,
    "node_ids": {},
    "choice_ids": {},
    "state_variable_ids": {},
    "success": False,
    "errors": []
}


class CelarentStoryBuilder:
    """Builds a Celarent syllogism story demonstrating negative propositions."""

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

    # =========================================================================
    # API Helper Methods
    # =========================================================================

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
                    is_start: bool = False, is_end: bool = False) -> dict:
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

    # =========================================================================
    # Story Building
    # =========================================================================

    def build_story(self):
        """Build the Celarent syllogism story."""

        # =====================================================================
        # STEP 1: CREATE THE STORY
        # =====================================================================
        self.log("\n📖 Creating story...")

        story = self.create_story(
            title="The Serpent's Classification: A Study in Negation",
            description="""Celarent syllogism (EAE-1) - introducing UNIVERSAL NEGATIVE propositions.

STRUCTURE:
- Major (E): No reptiles are mammals
- Minor (A): All snakes are reptiles
- Conclusion (E): No snakes are mammals

THE E PROPOSITION: "No X are Y" asserts sets are DISJOINT (no overlap).
Reptiles ∩ Mammals = ∅

Both terms distributed in E: we assert something about ALL reptiles AND ALL mammals.

DOMAIN: Archetypes (Reptiles, Mammals, Snakes) with conflicting traits (Cold-blooded vs Warm-blooded) demonstrate set relationships."""
        )
        self.story_id = story["id"]
        test_results["story_id"] = self.story_id
        self.log(f"  Created story: {self.story_id}")

        # =====================================================================
        # STEP 2: DEFINE STATE SCHEMA
        # =====================================================================
        self.log("\n📋 Creating state schema...")

        # ---------------------------------------------------------------------
        # Premise tracking - note the negative proposition
        # ---------------------------------------------------------------------

        self.state_vars["major_premise"] = self.create_state_variable(
            key="no_reptiles_are_mammals",
            value_type="boolean",
            default_value=False,
            category="premises",
            description="Major premise (E proposition): No M are P. "
                       "Asserts set disjointness: Reptiles ∩ Mammals = ∅. "
                       "Domain: Archetype 'Reptiles' has Trait 'Cold-blooded' which "
                       "CONFLICTS WITH 'Warm-blooded' (defining trait of Mammals)."
        )
        self.debug("Created: no_reptiles_are_mammals")

        self.state_vars["minor_premise"] = self.create_state_variable(
            key="all_snakes_are_reptiles",
            value_type="boolean",
            default_value=False,
            category="premises",
            description="Minor premise (A proposition): All S are M. "
                       "Asserts subset relation: Snakes ⊆ Reptiles. "
                       "Domain: Archetype 'Snakes' linked to Archetype 'Reptiles' "
                       "via shared traits and ArchetypePersonaLink inheritance."
        )
        self.debug("Created: all_snakes_are_reptiles")

        # ---------------------------------------------------------------------
        # Logical structure tracking
        # ---------------------------------------------------------------------

        self.state_vars["major_type"] = self.create_state_variable(
            key="major_premise_type",
            value_type="enum",
            enum_values=["A", "E", "I", "O"],
            default_value="E",
            category="structure",
            description="Type of major premise. E = Universal Negative (No X are Y)"
        )

        self.state_vars["minor_type"] = self.create_state_variable(
            key="minor_premise_type",
            value_type="enum",
            enum_values=["A", "E", "I", "O"],
            default_value="A",
            category="structure",
            description="Type of minor premise. A = Universal Affirmative (All X are Y)"
        )

        self.state_vars["mood"] = self.create_state_variable(
            key="syllogism_mood",
            value_type="string",
            default_value="",
            category="structure",
            description="Complete mood: EAE for Celarent"
        )

        self.state_vars["figure"] = self.create_state_variable(
            key="syllogism_figure",
            value_type="enum",
            enum_values=["figure_1", "figure_2", "figure_3", "figure_4"],
            default_value="figure_1",
            category="structure",
            description="Figure 1: M-P, S-M pattern"
        )

        # ---------------------------------------------------------------------
        # Conclusion and validity tracking
        # ---------------------------------------------------------------------

        self.state_vars["conclusion"] = self.create_state_variable(
            key="no_snakes_are_mammals",
            value_type="boolean",
            default_value=False,
            category="conclusions",
            description="Valid conclusion (E proposition): No S are P. "
                       "Domain: Persona in Archetype 'Snakes' cannot also be in 'Mammals' "
                       "because the defining traits conflict."
        )

        self.state_vars["valid"] = self.create_state_variable(
            key="conclusion_valid",
            value_type="boolean",
            default_value=False,
            category="validation",
            description="Whether the conclusion follows validly"
        )

        self.state_vars["fallacy"] = self.create_state_variable(
            key="fallacy_committed",
            value_type="enum",
            enum_values=["none", "affirmative_from_negative", "wrong_term",
                        "particular_from_universal", "non_sequitur", "hasty_generalization"],
            default_value="none",
            category="validation",
            description="Type of fallacy committed, if any"
        )

        # ---------------------------------------------------------------------
        # Learning progress tracking
        # ---------------------------------------------------------------------

        self.state_vars["understands_negation"] = self.create_state_variable(
            key="understands_negative_propositions",
            value_type="boolean",
            default_value=False,
            category="learning",
            description="Player understands E propositions and set disjointness"
        )

        self.state_vars["understands_distribution"] = self.create_state_variable(
            key="understands_distribution",
            value_type="boolean",
            default_value=False,
            category="learning",
            description="Player understands that E distributes both terms"
        )

        self.log(f"  Created {len(self.state_vars)} state variables")

        # =====================================================================
        # STEP 3: CREATE STORY NODES
        # =====================================================================
        self.log("\n📝 Creating story nodes...")

        # ---------------------------------------------------------------------
        # INTRODUCTION NODE
        # ---------------------------------------------------------------------

        self.nodes["intro"] = self.create_node(
            title="The Natural History Museum",
            content="""# The Natural History Museum

You find yourself in the grand hall of a Victorian natural history museum.
Glass cases display specimens from across the animal kingdom: preserved snakes
coiled in jars, taxidermied mammals posed in lifelike stances, and detailed
anatomical diagrams covering the walls.

A curator in a tweed jacket approaches, adjusting her spectacles.

*"Ah, a visitor interested in taxonomy! Tell me, do you know how to PROVE
that a snake can never be a mammal? It seems obvious, yet the logical proof
requires understanding NEGATIVE propositions."*

She gestures to a diagram showing the classification of vertebrates.

*"We must reason about what things are NOT, not just what they ARE.
Would you like to learn the art of logical negation?"*

---

**NEW CONCEPT: NEGATIVE PROPOSITIONS**

So far you may have seen propositions like:
- "All X are Y" (Universal Affirmative - type A)

Now we introduce:
- **"No X are Y"** (Universal Negative - type E)

This asserts that two sets are COMPLETELY SEPARATE:

```
    ┌─────────┐     ┌─────────┐
    │ Reptiles│     │ Mammals │
    │    ●    │     │    ●    │
    │         │     │         │
    └─────────┘     └─────────┘

    No overlap! Reptiles ∩ Mammals = ∅
```

**DOMAIN ENTITIES:**
- *Archetype "Reptiles"*: Has Trait "Cold-blooded"
- *Archetype "Mammals"*: Has Trait "Warm-blooded"
- These traits CONFLICT - nothing can have both!""",
            is_start=True
        )
        self.debug("Created node: intro")

        # ---------------------------------------------------------------------
        # MAJOR PREMISE NODE - The E Proposition
        # ---------------------------------------------------------------------

        self.nodes["major_premise"] = self.create_node(
            title="The Fundamental Division",
            content="""# The Fundamental Division

The curator leads you to a display showing the evolutionary tree of vertebrates.

*"First, we must establish a fundamental truth about the animal kingdom.
Consider what SEPARATES reptiles from mammals."*

She points to the characteristics listed:

**REPTILES:**
- Cold-blooded (ectothermic)
- Scales covering the body
- Most lay eggs
- Examples: snakes, lizards, crocodiles

**MAMMALS:**
- Warm-blooded (endothermic)
- Fur or hair on body
- Nurse young with milk
- Examples: lions, whales, humans

*"These are not just different—they are MUTUALLY EXCLUSIVE categories.
An animal cannot be both cold-blooded and warm-blooded. Therefore..."*

```
┌─────────────────────────────────────────┐
│           MAJOR PREMISE                 │
│         (E Proposition)                 │
│                                         │
│   "No reptiles are mammals"             │
│                                         │
│   Logical form: No M are P              │
│   - M (Middle term) = Reptiles          │
│   - P (Major term) = Mammals            │
│                                         │
│   This is an E proposition:             │
│   Universal NEGATIVE                    │
│                                         │
│   BOTH terms are DISTRIBUTED:           │
│   - ALL reptiles are excluded           │
│   - ALL mammals are excluded            │
│                                         │
│   Set theory: M ∩ P = ∅ (disjoint)      │
└─────────────────────────────────────────┘
```

*"Do you accept this premise?"*

---

**DOMAIN MAPPING:**
- This premise asserts: Trait "Cold-blooded" (Reptiles) CONFLICTS WITH "Warm-blooded" (Mammals)
- `TraitConflict(trait_a="Cold-blooded", trait_b="Warm-blooded", conflict_type="contradictory")`
- Any Persona cannot have both conflicting traits

**KEY INSIGHT - E PROPOSITIONS:**
Unlike A propositions where only the subject is distributed,
E propositions distribute BOTH subject and predicate:
- "No reptiles are mammals" = "No mammals are reptiles" (convertible!)"""
        )
        self.debug("Created node: major_premise")

        # ---------------------------------------------------------------------
        # MINOR PREMISE NODE - The A Proposition (subset)
        # ---------------------------------------------------------------------

        self.nodes["minor_premise"] = self.create_node(
            title="The Serpent's Place",
            content="""# The Serpent's Place

The curator moves to a case displaying various snake specimens.

*"Now we need a particular fact about snakes. Observe these specimens."*

She indicates their features:
- Scales covering the entire body ✓
- Cold-blooded metabolism ✓
- Egg-laying (most species) ✓
- No legs (unique to snakes among reptiles)

*"Snakes possess ALL the defining characteristics of reptiles.
They are not merely SIMILAR to reptiles—they ARE reptiles.
Every single snake, without exception, is classified as a reptile."*

```
┌─────────────────────────────────────────┐
│           MINOR PREMISE                 │
│         (A Proposition)                 │
│                                         │
│   "All snakes are reptiles"             │
│                                         │
│   Logical form: All S are M             │
│   - S (Minor term) = Snakes             │
│   - M (Middle term) = Reptiles          │
│                                         │
│   This is an A proposition:             │
│   Universal AFFIRMATIVE                 │
│                                         │
│   Set theory: S ⊆ M (subset)            │
│                                         │
│       ┌─────────────────┐               │
│       │    Reptiles     │               │
│       │   ┌─────────┐   │               │
│       │   │ Snakes  │   │               │
│       │   └─────────┘   │               │
│       └─────────────────┘               │
└─────────────────────────────────────────┘
```

*"With both premises established, what can we conclude about snakes?"*

---

**DOMAIN MAPPING:**
- Archetype "Snakes" is a SUBSET of Archetype "Reptiles"
- `ArchetypePersonaLink`: Any Persona in "Snakes" inherits from "Reptiles"
- Snakes inherit the Trait "Cold-blooded" from Reptiles

**LOGICAL STRUCTURE SO FAR:**
- Major (E): No M are P ✓ (No reptiles are mammals)
- Minor (A): All S are M ✓ (All snakes are reptiles)
- Conclusion: ??? (What about snakes and mammals?)"""
        )
        self.debug("Created node: minor_premise")

        # ---------------------------------------------------------------------
        # CONCLUSION OPTIONS NODE
        # ---------------------------------------------------------------------

        self.nodes["conclusion_options"] = self.create_node(
            title="The Logical Conclusion",
            content="""# The Logical Conclusion

The curator looks at you expectantly.

*"You have established two truths:*
1. *No reptiles are mammals* (E: complete separation)
2. *All snakes are reptiles* (A: complete inclusion)

*"Now, what can we VALIDLY conclude about snakes and mammals?"*

```
┌─────────────────────────────────────────┐
│         SYLLOGISM STRUCTURE             │
│              (Celarent)                 │
│                                         │
│   Major (E): No M are P                 │
│              (No reptiles are mammals)  │
│                                         │
│   Minor (A): All S are M                │
│              (All snakes are reptiles)  │
│                                         │
│   ════════════════════════════════════  │
│                                         │
│   Conclusion: ???                       │
│                                         │
│   Visual reasoning:                     │
│                                         │
│   ┌─────────┐       ┌─────────┐         │
│   │Reptiles │       │ Mammals │         │
│   │ ┌─────┐ │       │         │         │
│   │ │Snake│ │       │         │         │
│   │ └─────┘ │       │         │         │
│   └─────────┘       └─────────┘         │
│                                         │
│   If snakes are INSIDE reptiles,        │
│   and reptiles are OUTSIDE mammals...   │
│   Then snakes must be ___ mammals?      │
└─────────────────────────────────────────┘
```

---

**CRITICAL THINKING POINT:**
The conclusion must:
1. Connect the MINOR term (Snakes) to the MAJOR term (Mammals)
2. Respect the NEGATIVE nature of the major premise
3. Not introduce terms not present in the premises"""
        )
        self.debug("Created node: conclusion_options")

        # ---------------------------------------------------------------------
        # VALID CONCLUSION NODE
        # ---------------------------------------------------------------------

        self.nodes["valid_conclusion"] = self.create_node(
            title="Celarent Achieved",
            content="""# Celarent Achieved

*"No snakes are mammals,"* you declare.

The curator beams with approval.

*"Excellent! You have mastered the Celarent syllogism!"*

```
┌─────────────────────────────────────────┐
│           VALID SYLLOGISM               │
│             (Celarent)                  │
│                                         │
│   No reptiles are mammals     (E)       │
│   All snakes are reptiles     (A)       │
│   ─────────────────────────────         │
│   ∴ No snakes are mammals     (E)       │
│                                         │
│   Form: EAE-1 (Celarent)                │
│   Figure: 1 (M-P, S-M ∴ S-P)            │
│   Mood: EAE                             │
│                                         │
│         VALID ✓                         │
└─────────────────────────────────────────┘
```

*"Notice the beautiful logic: since snakes are ENTIRELY WITHIN the reptile
category, and reptiles are ENTIRELY OUTSIDE the mammal category, snakes
must also be ENTIRELY OUTSIDE the mammal category."*

```
    ┌───────────────┐         ┌───────────┐
    │   Reptiles    │         │  Mammals  │
    │  ┌─────────┐  │         │           │
    │  │ Snakes  │  │   ───   │           │
    │  └─────────┘  │         │           │
    └───────────────┘         └───────────┘

    The gap between sets is preserved!
```

*"This is Celarent—one of the fundamental valid syllogisms known since
Aristotle. You have proven, through pure logic, that no snake can ever
be classified as a mammal."*

---

**DOMAIN MAPPING:**
- Conclusion establishes: Any Persona in "Snakes" CANNOT be in "Mammals"
- This follows from: Snakes → Reptiles → (conflict) → Mammals
- The chain of TraitConflict prevents any snake from having mammal traits

**WHY THE CONCLUSION MUST BE NEGATIVE:**
- The major premise is negative (No M are P)
- From negative premises, only negative conclusions can follow
- This is a fundamental rule of syllogistic logic""",
            is_end=True
        )
        self.debug("Created node: valid_conclusion")

        # ---------------------------------------------------------------------
        # FALLACY: Affirmative from Negative
        # ---------------------------------------------------------------------

        self.nodes["fallacy_affirmative"] = self.create_node(
            title="The Affirmative Error",
            content="""# The Affirmative Error

*"Some snakes are mammals?"* The curator shakes her head.

*"Ah, you have committed a fundamental error: drawing an AFFIRMATIVE
conclusion from a NEGATIVE premise!"*

```
┌─────────────────────────────────────────┐
│              FALLACY                    │
│    Affirmative from Negative Premise    │
│                                         │
│   Our major premise was NEGATIVE:       │
│   "NO reptiles are mammals"             │
│                                         │
│   This tells us about EXCLUSION,        │
│   not about INCLUSION.                  │
│                                         │
│   You cannot conclude that something    │
│   IS something when your evidence       │
│   only tells you what it IS NOT.        │
│                                         │
│   RULE: From a negative premise,        │
│   only negative conclusions follow.     │
└─────────────────────────────────────────┘
```

*"Think about it: we established that reptiles and mammals are SEPARATE.
How could we possibly conclude that snakes, which are reptiles, have
ANY membership in the mammal category?"*

---

**DOMAIN INSIGHT:**
- The TraitConflict between "Cold-blooded" and "Warm-blooded" is absolute
- No Persona can have both traits
- Therefore, no member of "Snakes" can be a member of "Mammals"
- Affirmative conclusions ("Some X are Y") require affirmative evidence"""
        )
        self.debug("Created node: fallacy_affirmative")

        # ---------------------------------------------------------------------
        # FALLACY: Wrong Term
        # ---------------------------------------------------------------------

        self.nodes["fallacy_wrong_term"] = self.create_node(
            title="The Misplaced Conclusion",
            content="""# The Misplaced Conclusion

*"No reptiles are snakes?"* The curator looks puzzled, then laughs gently.

*"That's backwards! And also wrong—snakes ARE reptiles!"*

```
┌─────────────────────────────────────────┐
│              FALLACY                    │
│         Misidentified Terms             │
│                                         │
│   You confused the terms:               │
│                                         │
│   - Snakes (S) = Minor term             │
│   - Reptiles (M) = Middle term          │
│   - Mammals (P) = Major term            │
│                                         │
│   The conclusion must connect:          │
│   S (snakes) to P (mammals)             │
│                                         │
│   NOT S to M, which was already         │
│   stated in the minor premise!          │
│                                         │
│   "All snakes ARE reptiles"             │
│   So "No reptiles are snakes" is        │
│   doubly wrong—it contradicts our       │
│   premise AND uses wrong terms.         │
└─────────────────────────────────────────┘
```

*"The middle term (reptiles) should disappear in the conclusion.
It served its purpose: connecting snakes to the exclusion from mammals."*

---

**LOGICAL STRUCTURE REVIEW:**
```
Major: No [M=Reptiles] are [P=Mammals]
Minor: All [S=Snakes] are [M=Reptiles]
─────────────────────────────────────
Conclusion must be: [S=Snakes] ___ [P=Mammals]

The middle term (M) is eliminated!
```"""
        )
        self.debug("Created node: fallacy_wrong_term")

        # ---------------------------------------------------------------------
        # FALLACY: Non Sequitur
        # ---------------------------------------------------------------------

        self.nodes["fallacy_non_sequitur"] = self.create_node(
            title="The Irrelevant Conclusion",
            content="""# The Irrelevant Conclusion

*"Snakes are dangerous?"* The curator sighs.

*"Perhaps some are, but that has nothing to do with our premises!"*

```
┌─────────────────────────────────────────┐
│              FALLACY                    │
│           Non Sequitur                  │
│     ("It does not follow")              │
│                                         │
│   Premises:                             │
│   - No reptiles are mammals             │
│   - All snakes are reptiles             │
│                                         │
│   Your conclusion:                      │
│   - Snakes are dangerous                │
│                                         │
│   The term "dangerous" appears          │
│   NOWHERE in our premises!              │
│                                         │
│   We can only conclude things about:    │
│   - Snakes (minor term)                 │
│   - Mammals (major term)                │
│                                         │
│   NOT about danger, venom, or any       │
│   other property not mentioned.         │
└─────────────────────────────────────────┘
```

*"Logic requires discipline. We must conclude only what the premises
support, nothing more."*

---

**DOMAIN INSIGHT:**
- "Dangerous" would be a separate Trait
- It's not linked to our current syllogism about biological classification
- We might know snakes can be dangerous, but that's different knowledge
- Valid conclusions must use ONLY terms from the premises"""
        )
        self.debug("Created node: fallacy_non_sequitur")

        # ---------------------------------------------------------------------
        # RETRY NODE
        # ---------------------------------------------------------------------

        self.nodes["retry"] = self.create_node(
            title="A Second Attempt",
            content="""# A Second Attempt

The curator offers an encouraging smile.

*"Logic is a skill developed through practice. Let's review what we know:*

**Premise 1 (E):** No reptiles are mammals
- Reptiles and mammals are COMPLETELY SEPARATE categories
- They share NO members

**Premise 2 (A):** All snakes are reptiles
- Snakes are ENTIRELY WITHIN the reptile category
- Every snake is a reptile

*"Now, if snakes are inside a category (reptiles) that is completely
outside another category (mammals), where must snakes be relative
to mammals?"*

```
    ┌─────────────┐           ┌─────────────┐
    │  Reptiles   │           │   Mammals   │
    │  ┌───────┐  │    ───    │             │
    │  │Snakes │  │           │             │
    │  └───────┘  │           │             │
    └─────────────┘           └─────────────┘

    The answer is visually clear!
```

*"What is the relationship between snakes and mammals?"*"""
        )
        self.debug("Created node: retry")

        # ---------------------------------------------------------------------
        # SKIP PREMISES NODE
        # ---------------------------------------------------------------------

        self.nodes["skip_fallacy"] = self.create_node(
            title="Jumping to Conclusions",
            content="""# Jumping to Conclusions

You attempt to classify snakes immediately, but the curator stops you.

*"Wait! You cannot determine the relationship between snakes and mammals
without first establishing the intermediate facts."*

```
┌─────────────────────────────────────────┐
│              FALLACY                    │
│       Hasty Generalization              │
│                                         │
│   To prove snakes aren't mammals,       │
│   we need to establish:                 │
│                                         │
│   1. The relationship between           │
│      reptiles and mammals               │
│      (Are they separate? Overlapping?)  │
│                                         │
│   2. The relationship between           │
│      snakes and reptiles                │
│      (Are snakes a type of reptile?)    │
│                                         │
│   Only THEN can we deduce the           │
│   relationship between snakes           │
│   and mammals.                          │
└─────────────────────────────────────────┘
```

*"Let us proceed properly, starting with the fundamental division
between reptiles and mammals..."*"""
        )
        self.debug("Created node: skip_fallacy")

        self.log(f"  Created {len(self.nodes)} nodes")
        test_results["node_ids"] = {name: node["id"] for name, node in self.nodes.items()}

        # =====================================================================
        # STEP 4: CREATE CHOICES
        # =====================================================================
        self.log("\n🔀 Creating choices...")

        # ---------------------------------------------------------------------
        # FROM: intro
        # ---------------------------------------------------------------------

        self.choices.append(self.create_choice(
            from_node_name="intro",
            to_node_name="major_premise",
            text="\"Yes, teach me about negative propositions. What separates reptiles from mammals?\"",
            order=0,
            sets_state={
                "understands_negative_propositions": False
            }
        ))
        self.debug("Created choice: intro → major_premise")

        self.choices.append(self.create_choice(
            from_node_name="intro",
            to_node_name="skip_fallacy",
            text="\"I already know snakes aren't mammals. It's obvious!\"",
            order=1,
            sets_state={
                "fallacy_committed": "hasty_generalization"
            }
        ))
        self.debug("Created choice: intro → skip_fallacy")

        # ---------------------------------------------------------------------
        # FROM: major_premise
        # ---------------------------------------------------------------------

        self.choices.append(self.create_choice(
            from_node_name="major_premise",
            to_node_name="minor_premise",
            text="\"I accept this. No reptile can be a mammal—they are fundamentally different.\"",
            order=0,
            sets_state={
                # LOGICAL STATE: Establishes No M are P (E proposition)
                # DOMAIN: TraitConflict(Cold-blooded, Warm-blooded)
                "no_reptiles_are_mammals": True,
                "understands_negative_propositions": True,
                "understands_distribution": True,
                "syllogism_mood": "E"
            }
        ))
        self.debug("Created choice: major_premise → minor_premise")

        # ---------------------------------------------------------------------
        # FROM: minor_premise
        # ---------------------------------------------------------------------

        self.choices.append(self.create_choice(
            from_node_name="minor_premise",
            to_node_name="conclusion_options",
            text="\"I accept this too. Snakes have all the characteristics of reptiles.\"",
            order=0,
            requires_state={
                "no_reptiles_are_mammals": True
            },
            sets_state={
                # LOGICAL STATE: Establishes All S are M (A proposition)
                # DOMAIN: Snakes ⊆ Reptiles via ArchetypePersonaLink
                "all_snakes_are_reptiles": True,
                "syllogism_mood": "EA"
            }
        ))
        self.debug("Created choice: minor_premise → conclusion_options")

        # ---------------------------------------------------------------------
        # FROM: conclusion_options - THE CRITICAL CHOICES
        # ---------------------------------------------------------------------

        # VALID: No snakes are mammals (E conclusion)
        self.choices.append(self.create_choice(
            from_node_name="conclusion_options",
            to_node_name="valid_conclusion",
            text="\"Therefore, no snakes are mammals.\"",
            order=0,
            requires_state={
                "$and": [
                    {"no_reptiles_are_mammals": True},
                    {"all_snakes_are_reptiles": True}
                ]
            },
            sets_state={
                # VALID CONCLUSION: No S are P
                # DOMAIN: Snakes cannot have Mammal traits due to TraitConflict chain
                "no_snakes_are_mammals": True,
                "conclusion_valid": True,
                "syllogism_mood": "EAE",
                "fallacy_committed": "none"
            }
        ))
        self.debug("Created choice: conclusion_options → valid_conclusion (CORRECT)")

        # FALLACY: Some snakes are mammals (affirmative from negative)
        self.choices.append(self.create_choice(
            from_node_name="conclusion_options",
            to_node_name="fallacy_affirmative",
            text="\"Therefore, some snakes are mammals.\"",
            order=1,
            requires_state={
                "$and": [
                    {"no_reptiles_are_mammals": True},
                    {"all_snakes_are_reptiles": True}
                ]
            },
            sets_state={
                "conclusion_valid": False,
                "fallacy_committed": "affirmative_from_negative"
            }
        ))
        self.debug("Created choice: conclusion_options → fallacy_affirmative")

        # FALLACY: No reptiles are snakes (wrong terms)
        self.choices.append(self.create_choice(
            from_node_name="conclusion_options",
            to_node_name="fallacy_wrong_term",
            text="\"Therefore, no reptiles are snakes.\"",
            order=2,
            requires_state={
                "$and": [
                    {"no_reptiles_are_mammals": True},
                    {"all_snakes_are_reptiles": True}
                ]
            },
            sets_state={
                "conclusion_valid": False,
                "fallacy_committed": "wrong_term"
            }
        ))
        self.debug("Created choice: conclusion_options → fallacy_wrong_term")

        # FALLACY: Snakes are dangerous (non sequitur)
        self.choices.append(self.create_choice(
            from_node_name="conclusion_options",
            to_node_name="fallacy_non_sequitur",
            text="\"Therefore, snakes are dangerous.\"",
            order=3,
            requires_state={
                "$and": [
                    {"no_reptiles_are_mammals": True},
                    {"all_snakes_are_reptiles": True}
                ]
            },
            sets_state={
                "conclusion_valid": False,
                "fallacy_committed": "non_sequitur"
            }
        ))
        self.debug("Created choice: conclusion_options → fallacy_non_sequitur")

        # ---------------------------------------------------------------------
        # FROM: fallacy nodes → retry
        # ---------------------------------------------------------------------

        self.choices.append(self.create_choice(
            from_node_name="fallacy_affirmative",
            to_node_name="retry",
            text="\"I see—I need a negative conclusion. Let me try again.\"",
            order=0,
            sets_state={"fallacy_committed": "none"}
        ))

        self.choices.append(self.create_choice(
            from_node_name="fallacy_wrong_term",
            to_node_name="retry",
            text="\"I confused the terms. Let me reconsider.\"",
            order=0,
            sets_state={"fallacy_committed": "none"}
        ))

        self.choices.append(self.create_choice(
            from_node_name="fallacy_non_sequitur",
            to_node_name="retry",
            text="\"You're right—I must stick to the terms in the premises.\"",
            order=0,
            sets_state={"fallacy_committed": "none"}
        ))

        self.choices.append(self.create_choice(
            from_node_name="skip_fallacy",
            to_node_name="major_premise",
            text="\"You're right. Let me learn the proper reasoning.\"",
            order=0,
            sets_state={"fallacy_committed": "none"}
        ))

        # ---------------------------------------------------------------------
        # FROM: retry → back to conclusion_options
        # ---------------------------------------------------------------------

        self.choices.append(self.create_choice(
            from_node_name="retry",
            to_node_name="conclusion_options",
            text="\"I understand now. Let me state the conclusion.\"",
            order=0,
            requires_state={
                "$and": [
                    {"no_reptiles_are_mammals": True},
                    {"all_snakes_are_reptiles": True}
                ]
            }
        ))

        self.log(f"  Created {len(self.choices)} choices")
        test_results["choice_ids"] = [c["id"] for c in self.choices]

        # =====================================================================
        # STEP 5: VALIDATE
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
        description="Create a Celarent syllogism story"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    test_results["start_time"] = datetime.now().isoformat()

    print("\n" + "=" * 70)
    print("  CARROLL CELARENT STORY BUILDER")
    print("  Demonstrating negative propositions (EAE-1)")
    print("=" * 70)

    try:
        session = get_authenticated_session()
        print(f"\n✓ Authenticated successfully")

        builder = CelarentStoryBuilder(session, verbose=args.verbose)
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
        print("  │   ├─→ major_premise (E: No reptiles are mammals)")
        print("  │   │     └─→ minor_premise (A: All snakes are reptiles)")
        print("  │   │           └─→ conclusion_options")
        print("  │   │                 ├─→ valid_conclusion (E: No snakes are mammals) ✓")
        print("  │   │                 ├─→ fallacy_affirmative → retry")
        print("  │   │                 ├─→ fallacy_wrong_term → retry")
        print("  │   │                 └─→ fallacy_non_sequitur → retry")
        print("  │   └─→ skip_fallacy → major_premise")
        print("  └─────────────────────────────────────────────")

        print(f"\n  Play the story at:")
        print(f"  http://localhost:5173/story/{builder.story_id}")

        test_results["success"] = is_valid
        test_results["end_time"] = datetime.now().isoformat()

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
