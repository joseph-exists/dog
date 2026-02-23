#!/usr/bin/env python3
"""
Carroll Syllogism Story - Sample Implementation

This script creates a sample story demonstrating Lewis Carroll's symbolic logic
using the existing choice/state system. It implements the classic syllogism:

    Major Premise:  "All men are mortal"        (A proposition: All M are P)
    Minor Premise:  "Socrates is a man"         (A proposition: S is M)
    Conclusion:     "Socrates is mortal"        (Valid inference: S is P)

The story guides the player through establishing premises and deriving
the valid conclusion, while also presenting invalid inference options
to teach fallacy recognition.

=============================================================================
ARCHETYPES, PERSONAS, TRAITS, AND QUALITIES TO CREATE
=============================================================================

These entities represent the domain content being reasoned about.
They should be created before running this script (or could be created
programmatically as shown in commented sections).

ARCHETYPES (Categories/Sets):
-----------------------------
1. "Men" (or "Humans")
   - Description: "The set of all human beings"
   - Represents the MIDDLE TERM in our syllogism

2. "Mortals"
   - Description: "The set of all beings subject to death"
   - Represents the MAJOR TERM (predicate of conclusion)

3. "Immortals"
   - Description: "The set of beings not subject to death"
   - Represents the CONTRADICTORY of Mortals (for fallacy examples)

4. "Philosophers"
   - Description: "The set of all lovers of wisdom"
   - For extended syllogism chains (sorites)

TRAITS (Properties):
--------------------
1. "Subject to Death"
   - Description: "Will eventually cease to live"
   - Links Archetypes: Men → has this, Mortals → defined by this
   - This shared trait establishes: Men ⊆ Mortals

2. "Capable of Reason"
   - Description: "Possesses rational thought"
   - Links Archetypes: Men → has this, Philosophers → has this

3. "Eternal"
   - Description: "Exists outside of time, cannot die"
   - Links Archetypes: Immortals → has this
   - CONFLICTS WITH: "Subject to Death"

PERSONAS (Individuals):
-----------------------
1. "Socrates"
   - Description: "Greek philosopher, 470-399 BCE"
   - Member of Archetypes: Men, Philosophers
   - Represents the MINOR TERM (subject of conclusion)

2. "Zeus"
   - Description: "King of the Greek gods"
   - Member of Archetypes: Immortals
   - Counter-example for invalid inferences

QUALITIES (Derived Properties):
-------------------------------
1. "Wisdom"
   - Description: "Deep understanding and good judgment"
   - Derived from: Trait "Capable of Reason" + experience
   - Auto-enabled for: Philosophers

=============================================================================

Usage:
    python test_carroll_syllogism_story.py
    python test_carroll_syllogism_story.py --verbose
    python test_carroll_syllogism_story.py --cleanup  # Delete created story

Output:
    test_results_carroll_syllogism.json
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
RESULTS_FILE = "test_results_carroll_syllogism.json"

# Test results tracking
test_results = {
    "test_suite": "Carroll Syllogism Story Creation",
    "start_time": None,
    "end_time": None,
    "story_id": None,
    "node_ids": {},
    "choice_ids": {},
    "state_variable_ids": {},
    "success": False,
    "errors": []
}


class CarrollStoryBuilder:
    """Builds a Carroll-style syllogism story."""

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
    # API Helper Methods
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
        """Build the complete syllogism story."""

        # =====================================================================
        # STEP 1: CREATE THE STORY
        # =====================================================================
        #
        # The story title and description set the context for the logical
        # exercise. This is a teaching story about syllogistic reasoning.
        #
        self.log("\n📖 Creating story...")

        story = self.create_story(
            title="The Mortality of Socrates: A Lesson in Logic",
            description="""An interactive exploration of classical syllogistic reasoning.

You will learn to construct valid logical arguments by establishing premises
and deriving conclusions. This story demonstrates the famous syllogism that
proves Socrates' mortality through deductive reasoning.

LOGICAL STRUCTURE:
- Major Premise (Universal): All men are mortal
- Minor Premise (Singular): Socrates is a man
- Conclusion (Derived): Therefore, Socrates is mortal

This is a valid syllogism in the form AAA-1 (Barbara), one of the foundational
patterns of Aristotelian logic later formalized by Lewis Carroll.

DOMAIN ENTITIES REFERENCED:
- Archetype "Men": The category of human beings
- Archetype "Mortals": The category of beings subject to death
- Persona "Socrates": An individual member of the Men category
- Trait "Subject to Death": The defining property of Mortals"""
        )
        self.story_id = story["id"]
        test_results["story_id"] = self.story_id
        self.log(f"  Created story: {self.story_id}")

        # =====================================================================
        # STEP 2: DEFINE STATE SCHEMA
        # =====================================================================
        #
        # State variables track the logical progress through the syllogism.
        # They represent:
        # - Which premises have been established
        # - The logical structure (figure, mood)
        # - The validity of attempted conclusions
        # - Any fallacies committed
        #
        # MAPPING TO ARCHETYPES/TRAITS:
        # - "all_men_are_mortal" represents: ArchetypeTraitLink(Men → Subject to Death)
        # - "socrates_is_a_man" represents: ArchetypePersonaLink(Socrates → Men)
        # - "socrates_is_mortal" represents: PersonaTraitLink(Socrates → Subject to Death)
        #
        self.log("\n📋 Creating state schema...")

        # ---------------------------------------------------------------------
        # Premise tracking variables
        # These correspond to establishing relationships between Archetypes/Personas
        # ---------------------------------------------------------------------

        self.state_vars["major_premise"] = self.create_state_variable(
            key="all_men_are_mortal",
            value_type="boolean",
            default_value=False,
            category="premises",
            description="Major premise established: All M are P (All men are mortal). "
                       "In domain terms: Archetype 'Men' has Trait 'Subject to Death', "
                       "which is the defining trait of Archetype 'Mortals'. "
                       "Therefore Men ⊆ Mortals."
        )
        self.debug(f"Created: all_men_are_mortal")

        self.state_vars["minor_premise"] = self.create_state_variable(
            key="socrates_is_a_man",
            value_type="boolean",
            default_value=False,
            category="premises",
            description="Minor premise established: S is M (Socrates is a man). "
                       "In domain terms: Persona 'Socrates' is linked to Archetype 'Men' "
                       "via ArchetypePersonaLink."
        )
        self.debug(f"Created: socrates_is_a_man")

        # ---------------------------------------------------------------------
        # Syllogism structure tracking
        # These track the formal logical structure being used
        # ---------------------------------------------------------------------

        self.state_vars["figure"] = self.create_state_variable(
            key="syllogism_figure",
            value_type="enum",
            enum_values=["figure_1", "figure_2", "figure_3", "figure_4"],
            default_value="figure_1",
            category="structure",
            description="Syllogism figure (arrangement of middle term). "
                       "Figure 1: M-P, S-M ∴ S-P (most natural form)"
        )
        self.debug(f"Created: syllogism_figure")

        self.state_vars["mood"] = self.create_state_variable(
            key="syllogism_mood",
            value_type="string",
            default_value="",
            category="structure",
            description="Syllogism mood (combination of proposition types). "
                       "AAA = Barbara (All-All-All), the mood we're demonstrating."
        )
        self.debug(f"Created: syllogism_mood")

        # ---------------------------------------------------------------------
        # Conclusion and validity tracking
        # These track the player's reasoning attempts
        # ---------------------------------------------------------------------

        self.state_vars["conclusion"] = self.create_state_variable(
            key="socrates_is_mortal",
            value_type="boolean",
            default_value=False,
            category="conclusions",
            description="Conclusion derived: S is P (Socrates is mortal). "
                       "In domain terms: Persona 'Socrates' inherits Trait 'Subject to Death' "
                       "via the chain: Socrates → Men → Subject to Death."
        )
        self.debug(f"Created: socrates_is_mortal")

        self.state_vars["valid"] = self.create_state_variable(
            key="conclusion_valid",
            value_type="boolean",
            default_value=False,
            category="validation",
            description="Whether the derived conclusion follows validly from premises"
        )
        self.debug(f"Created: conclusion_valid")

        self.state_vars["fallacy"] = self.create_state_variable(
            key="fallacy_committed",
            value_type="enum",
            enum_values=["none", "affirming_consequent", "denying_antecedent",
                        "undistributed_middle", "hasty_generalization", "non_sequitur"],
            default_value="none",
            category="validation",
            description="Type of logical fallacy committed, if any"
        )
        self.debug(f"Created: fallacy_committed")

        # ---------------------------------------------------------------------
        # Extended tracking for teaching purposes
        # ---------------------------------------------------------------------

        self.state_vars["understood_universals"] = self.create_state_variable(
            key="understood_universal_propositions",
            value_type="boolean",
            default_value=False,
            category="learning",
            description="Player understands universal (A/E) propositions"
        )
        self.debug(f"Created: understood_universal_propositions")

        self.state_vars["term_roles"] = self.create_state_variable(
            key="identified_term_roles",
            value_type="boolean",
            default_value=False,
            category="learning",
            description="Player identified Subject, Predicate, and Middle terms"
        )
        self.debug(f"Created: identified_term_roles")

        self.log(f"  Created {len(self.state_vars)} state variables")

        # =====================================================================
        # STEP 3: CREATE STORY NODES
        # =====================================================================
        #
        # Each node represents a stage in the logical reasoning process.
        # The content explains both the story and the underlying logic.
        #
        self.log("\n📝 Creating story nodes...")

        # ---------------------------------------------------------------------
        # INTRODUCTION NODE (Start)
        # Sets the scene and introduces the logical challenge
        # ---------------------------------------------------------------------

        self.nodes["intro"] = self.create_node(
            title="The Agora of Athens",
            content="""# The Agora of Athens, 399 BCE

You find yourself in the bustling marketplace of ancient Athens. Philosophers
debate in the shade of colonnaded walkways, merchants hawk their wares, and
citizens gather to discuss the affairs of the polis.

Near the Stoa Poikile, you notice a crowd gathered around an elderly man with
a distinctive broad nose and penetrating gaze. This is **Socrates**, the
famous philosopher, engaged in his usual practice of questioning assumptions.

A young student approaches you.

*"Stranger, you seem thoughtful. Tell me, do you know how to prove that
Socrates will one day die? It seems obvious, yet the proof requires careful
reasoning. Would you like to learn the art of the syllogism?"*

---

**LOGICAL CONTEXT:**
- We will construct a valid syllogism (logical argument)
- Our goal: Prove that Socrates is mortal
- Method: Establish premises, then derive the conclusion

**DOMAIN ENTITIES IN PLAY:**
- *Archetype "Men"*: The category Socrates belongs to
- *Archetype "Mortals"*: The category we want to prove Socrates belongs to
- *Persona "Socrates"*: The individual we're reasoning about
- *Trait "Subject to Death"*: The property that defines mortality""",
            is_start=True
        )
        self.debug(f"Created node: intro")

        # ---------------------------------------------------------------------
        # MAJOR PREMISE NODE
        # Establishes: All men are mortal (A proposition)
        # Domain: Links Archetype "Men" to Trait "Subject to Death"
        # ---------------------------------------------------------------------

        self.nodes["major_premise"] = self.create_node(
            title="The Universal Truth",
            content="""# The Universal Truth

The student leads you to a quiet corner where an old philosopher sits.

*"First,"* the philosopher begins, *"we must establish what we know to be
universally true about men."*

He gestures to the graves visible beyond the city walls.

*"Consider: Every man who has ever lived has eventually died. Every man
living now will someday die. This is not mere observation—it is the nature
of mankind."*

He draws in the dust:

```
┌─────────────────────────────────────────┐
│           MAJOR PREMISE                 │
│                                         │
│   "All men are mortal"                  │
│                                         │
│   Logical form: All M are P             │
│   - M (Middle term) = Men               │
│   - P (Major term) = Mortal             │
│                                         │
│   This is an A proposition:             │
│   Universal Affirmative                 │
│   The subject (Men) is DISTRIBUTED      │
│   (refers to ALL members of the class)  │
└─────────────────────────────────────────┘
```

*"Do you accept this premise?"*

---

**DOMAIN MAPPING:**
- This premise asserts: `ArchetypeTraitLink(archetype="Men", trait="Subject to Death")`
- The trait "Subject to Death" is what DEFINES the Archetype "Mortals"
- Therefore: Men ⊆ Mortals (Men is a subset of Mortals)

**STATE CHANGE:**
Accepting this establishes: `all_men_are_mortal = true`"""
        )
        self.debug(f"Created node: major_premise")

        # ---------------------------------------------------------------------
        # MINOR PREMISE NODE
        # Establishes: Socrates is a man (Singular proposition)
        # Domain: Links Persona "Socrates" to Archetype "Men"
        # ---------------------------------------------------------------------

        self.nodes["minor_premise"] = self.create_node(
            title="The Particular Instance",
            content="""# The Particular Instance

With the universal truth established, the philosopher continues.

*"Now we need a particular fact—something true about a specific individual.
Look at Socrates there."*

You observe Socrates: he walks on two legs, speaks and reasons, was born of
a mother, and has aged over the years. Every sign indicates his humanity.

*"Socrates is a man. This is our minor premise."*

```
┌─────────────────────────────────────────┐
│           MINOR PREMISE                 │
│                                         │
│   "Socrates is a man"                   │
│                                         │
│   Logical form: S is M                  │
│   - S (Minor term) = Socrates           │
│   - M (Middle term) = Men               │
│                                         │
│   This connects our individual (S)      │
│   to the category (M) from our          │
│   major premise.                        │
│                                         │
│   The Middle Term (Men) now appears     │
│   in BOTH premises—this is essential!   │
└─────────────────────────────────────────┘
```

*"With both premises established, what can we conclude?"*

---

**DOMAIN MAPPING:**
- This premise asserts: `ArchetypePersonaLink(persona="Socrates", archetype="Men")`
- Socrates is now established as a member of the set "Men"

**STATE CHANGE:**
Accepting this establishes: `socrates_is_a_man = true`

**LOGICAL STRUCTURE SO FAR:**
- Major: All M are P ✓ (All men are mortal)
- Minor: S is M ✓ (Socrates is a man)
- Conclusion: S is P ? (Socrates is mortal) — TO BE DERIVED"""
        )
        self.debug(f"Created node: minor_premise")

        # ---------------------------------------------------------------------
        # CONCLUSION OPTIONS NODE
        # Player must choose the correct conclusion or commit a fallacy
        # ---------------------------------------------------------------------

        self.nodes["conclusion_options"] = self.create_node(
            title="The Moment of Inference",
            content="""# The Moment of Inference

The philosopher looks at you expectantly.

*"You have accepted two truths:*
1. *All men are mortal*
2. *Socrates is a man*

*"Now, using these premises alone—no additional assumptions—what conclusion
MUST follow? Be careful! Many students make errors here."*

```
┌─────────────────────────────────────────┐
│         SYLLOGISM STRUCTURE             │
│                                         │
│   Major Premise: All M are P            │
│                  (All men are mortal)   │
│                                         │
│   Minor Premise: S is M                 │
│                  (Socrates is a man)    │
│                                         │
│   ════════════════════════════════════  │
│                                         │
│   Conclusion: ???                       │
│               (What follows?)           │
│                                         │
│   Valid conclusions must:               │
│   - Use only terms from the premises    │
│   - Follow the rules of inference       │
│   - Not introduce new information       │
└─────────────────────────────────────────┘
```

---

**CHOICE POINT:**
The player must select the correct conclusion. Wrong choices lead to fallacy
explanations, teaching through error.

**REQUIRES STATE:**
- Both premises must be established: `all_men_are_mortal` AND `socrates_is_a_man`"""
        )
        self.debug(f"Created node: conclusion_options")

        # ---------------------------------------------------------------------
        # VALID CONCLUSION NODE (Success)
        # The correct inference: Socrates is mortal
        # ---------------------------------------------------------------------

        self.nodes["valid_conclusion"] = self.create_node(
            title="The Valid Inference",
            content="""# The Valid Inference

*"Socrates is mortal,"* you declare.

The philosopher's face breaks into a warm smile.

*"Excellent! You have reasoned correctly."*

```
┌─────────────────────────────────────────┐
│           VALID SYLLOGISM               │
│              (Barbara)                  │
│                                         │
│   All men are mortal      (A)           │
│   Socrates is a man       (A)           │
│   ─────────────────────────────         │
│   ∴ Socrates is mortal    (A)           │
│                                         │
│   Form: AAA-1 (Barbara)                 │
│   Figure: 1 (M-P, S-M ∴ S-P)            │
│   Mood: AAA (All universal affirmative) │
│                                         │
│         VALID ✓                         │
└─────────────────────────────────────────┘
```

*"This is called a syllogism in BARBARA—the most fundamental valid form.
Notice how the middle term 'men' connected Socrates to mortality:*

*Socrates → Men → Mortal*

*"The chain of reasoning is unbreakable. If the premises are true, the
conclusion MUST be true. This is the power of deductive logic."*

---

**DOMAIN MAPPING:**
- The conclusion asserts: `PersonaTraitLink(persona="Socrates", trait="Subject to Death", is_inherited=True)`
- The `is_inherited=True` flag indicates this trait comes through the Archetype chain
- Chain: Socrates → (member of) Men → (has trait) Subject to Death → (defines) Mortal

**STATE CHANGE:**
- `socrates_is_mortal = true`
- `conclusion_valid = true`
- `syllogism_mood = "AAA"` (Barbara)""",
            is_end=True
        )
        self.debug(f"Created node: valid_conclusion")

        # ---------------------------------------------------------------------
        # FALLACY NODE: Affirming the Consequent
        # Invalid inference: "All mortals are men"
        # ---------------------------------------------------------------------

        self.nodes["fallacy_affirming"] = self.create_node(
            title="A Logical Misstep",
            content="""# A Logical Misstep

*"All mortals are men?"* The philosopher shakes his head sadly.

*"Ah, you have committed a fallacy—specifically, an ILLICIT CONVERSION."*

```
┌─────────────────────────────────────────┐
│              FALLACY                    │
│         Illicit Conversion              │
│                                         │
│   You tried to convert:                 │
│   "All men are mortal"                  │
│        ↓                                │
│   "All mortals are men"                 │
│                                         │
│   But A propositions cannot be simply   │
│   converted! Consider:                  │
│                                         │
│   "All dogs are mammals"  ✓             │
│   "All mammals are dogs"  ✗             │
│                                         │
│   Trees are mortal but not men!         │
│   Fish are mortal but not men!          │
└─────────────────────────────────────────┘
```

*"The set of mortals is LARGER than the set of men. Men are a subset of
mortals, not the other way around."*

---

**DOMAIN INSIGHT:**
- Men ⊆ Mortals (Men is a SUBSET of Mortals)
- But Mortals ⊄ Men (Mortals is NOT a subset of Men)
- The Archetype "Mortals" contains many members beyond "Men":
  - Animals, plants, insects—all mortal, none human

**STATE CHANGE:**
- `fallacy_committed = "affirming_consequent"`
- `conclusion_valid = false`"""
        )
        self.debug(f"Created node: fallacy_affirming")

        # ---------------------------------------------------------------------
        # FALLACY NODE: Non Sequitur
        # Invalid inference: "Socrates is wise"
        # ---------------------------------------------------------------------

        self.nodes["fallacy_non_sequitur"] = self.create_node(
            title="An Irrelevant Conclusion",
            content="""# An Irrelevant Conclusion

*"Socrates is wise?"* The philosopher looks puzzled.

*"That may well be true, but it does not FOLLOW from our premises!"*

```
┌─────────────────────────────────────────┐
│              FALLACY                    │
│           Non Sequitur                  │
│     ("It does not follow")              │
│                                         │
│   Premises:                             │
│   - All men are mortal                  │
│   - Socrates is a man                   │
│                                         │
│   Your conclusion:                      │
│   - Socrates is wise                    │
│                                         │
│   The term "wise" appears NOWHERE       │
│   in our premises! We cannot conclude   │
│   anything about wisdom from premises   │
│   about mortality.                      │
└─────────────────────────────────────────┘
```

*"A valid conclusion must use only the terms present in the premises:*
- *Major term: Mortal*
- *Minor term: Socrates*
- *Middle term: Man*

*Wisdom is none of these!"*

---

**DOMAIN INSIGHT:**
- "Wisdom" would be a separate Trait, unrelated to this syllogism
- Persona "Socrates" might have Trait "Wise" (via Archetype "Philosophers")
- But that's a DIFFERENT logical chain, not derivable from these premises

**STATE CHANGE:**
- `fallacy_committed = "non_sequitur"`
- `conclusion_valid = false`"""
        )
        self.debug(f"Created node: fallacy_non_sequitur")

        # ---------------------------------------------------------------------
        # RETRY NODE
        # Allows player to try again after committing a fallacy
        # ---------------------------------------------------------------------

        self.nodes["retry"] = self.create_node(
            title="Try Again",
            content="""# A Second Chance

The philosopher offers an encouraging smile.

*"Logic is learned through error as much as success. Now that you understand
your mistake, let us return to the moment of inference.*

*Remember:*
- *All men are mortal (our major premise)*
- *Socrates is a man (our minor premise)*

*What conclusion follows from THESE premises, using ONLY the terms they
contain?"*

---

**LOGICAL HINT:**
The conclusion must:
1. Have "Socrates" as its subject (the minor term)
2. Have "mortal" as its predicate (the major term)
3. Not include "men" (the middle term is eliminated in the conclusion)

Form: S is P → "Socrates is mortal\""""
        )
        self.debug(f"Created node: retry")

        # ---------------------------------------------------------------------
        # SKIP PREMISES NODE (Fallacy path)
        # What happens if you try to conclude without establishing premises
        # ---------------------------------------------------------------------

        self.nodes["skip_fallacy"] = self.create_node(
            title="Hasty Reasoning",
            content="""# Hasty Reasoning

You attempt to reach a conclusion, but the philosopher stops you.

*"Wait! You cannot derive a conclusion without first establishing premises.
This is the fallacy of HASTY GENERALIZATION—reaching conclusions without
sufficient grounds."*

```
┌─────────────────────────────────────────┐
│              FALLACY                    │
│       Hasty Generalization              │
│                                         │
│   You tried to conclude without         │
│   establishing the necessary premises.  │
│                                         │
│   A valid syllogism requires:           │
│   1. A major premise (universal truth)  │
│   2. A minor premise (particular fact)  │
│   3. THEN the conclusion follows        │
│                                         │
│   You cannot skip steps 1 and 2!        │
└─────────────────────────────────────────┘
```

*"Let us begin properly. First, we must establish what we know about men
and mortality..."*

---

**DOMAIN INSIGHT:**
- Without establishing `ArchetypeTraitLink(Men → Subject to Death)`, we can't
  reason about mortality
- Without establishing `ArchetypePersonaLink(Socrates → Men)`, we can't connect
  Socrates to any properties of Men

**STATE CHANGE:**
- `fallacy_committed = "hasty_generalization"`"""
        )
        self.debug(f"Created node: skip_fallacy")

        self.log(f"  Created {len(self.nodes)} nodes")

        # Save node IDs to results
        test_results["node_ids"] = {name: node["id"] for name, node in self.nodes.items()}

        # =====================================================================
        # STEP 4: CREATE CHOICES (Story Branches)
        # =====================================================================
        #
        # Choices connect nodes and implement the logical flow.
        # requires_state enforces logical prerequisites.
        # sets_state records logical progress.
        #
        self.log("\n🔀 Creating choices...")

        # ---------------------------------------------------------------------
        # FROM: intro
        # Player can begin learning or try to skip ahead
        # ---------------------------------------------------------------------

        self.choices.append(self.create_choice(
            from_node_name="intro",
            to_node_name="major_premise",
            text="\"Yes, teach me the syllogism. Let us begin with the first premise.\"",
            order=0,
            # No requires_state - anyone can start
            sets_state={
                "understood_universal_propositions": False  # Will learn soon
            }
        ))
        self.debug("Created choice: intro → major_premise")

        self.choices.append(self.create_choice(
            from_node_name="intro",
            to_node_name="skip_fallacy",
            text="\"I already know Socrates is mortal. Let me prove it now!\"",
            order=1,
            # No requires_state - but this leads to fallacy
            sets_state={
                "fallacy_committed": "hasty_generalization"
            }
        ))
        self.debug("Created choice: intro → skip_fallacy (hasty)")

        # ---------------------------------------------------------------------
        # FROM: major_premise
        # Player accepts or questions the universal premise
        # ---------------------------------------------------------------------

        self.choices.append(self.create_choice(
            from_node_name="major_premise",
            to_node_name="minor_premise",
            text="\"I accept this premise. All men are indeed mortal.\"",
            order=0,
            # No requires_state - this is establishing the premise
            sets_state={
                # LOGICAL STATE: Establishes All M are P
                # DOMAIN: This represents ArchetypeTraitLink(Men → Subject to Death)
                "all_men_are_mortal": True,
                "understood_universal_propositions": True,
                "syllogism_mood": "A"  # First premise is type A
            }
        ))
        self.debug("Created choice: major_premise → minor_premise (accept)")

        # ---------------------------------------------------------------------
        # FROM: minor_premise
        # Player accepts the particular premise about Socrates
        # ---------------------------------------------------------------------

        self.choices.append(self.create_choice(
            from_node_name="minor_premise",
            to_node_name="conclusion_options",
            text="\"I accept this too. Socrates is clearly a man.\"",
            order=0,
            requires_state={
                # Must have already accepted the major premise
                "all_men_are_mortal": True
            },
            sets_state={
                # LOGICAL STATE: Establishes S is M
                # DOMAIN: This represents ArchetypePersonaLink(Socrates → Men)
                "socrates_is_a_man": True,
                "identified_term_roles": True,
                "syllogism_mood": "AA"  # Both premises are type A
            }
        ))
        self.debug("Created choice: minor_premise → conclusion_options (accept)")

        # ---------------------------------------------------------------------
        # FROM: conclusion_options
        # The critical choice: select the correct conclusion or commit fallacy
        # ---------------------------------------------------------------------

        # VALID CONCLUSION: Socrates is mortal
        self.choices.append(self.create_choice(
            from_node_name="conclusion_options",
            to_node_name="valid_conclusion",
            text="\"Therefore, Socrates is mortal.\"",
            order=0,
            requires_state={
                # BOTH premises must be established for valid inference
                # This models: (All M are P) ∧ (S is M) → (S is P)
                "$and": [
                    {"all_men_are_mortal": True},
                    {"socrates_is_a_man": True}
                ]
            },
            sets_state={
                # LOGICAL STATE: Derives S is P
                # DOMAIN: This represents PersonaTraitLink(Socrates → Subject to Death, inherited=True)
                "socrates_is_mortal": True,
                "conclusion_valid": True,
                "syllogism_mood": "AAA",  # Complete valid mood
                "fallacy_committed": "none"
            }
        ))
        self.debug("Created choice: conclusion_options → valid_conclusion (CORRECT)")

        # FALLACY: Illicit conversion (All mortals are men)
        self.choices.append(self.create_choice(
            from_node_name="conclusion_options",
            to_node_name="fallacy_affirming",
            text="\"Therefore, all mortals are men.\"",
            order=1,
            requires_state={
                "$and": [
                    {"all_men_are_mortal": True},
                    {"socrates_is_a_man": True}
                ]
            },
            sets_state={
                "conclusion_valid": False,
                "fallacy_committed": "affirming_consequent"
            }
        ))
        self.debug("Created choice: conclusion_options → fallacy_affirming")

        # FALLACY: Non sequitur (Socrates is wise)
        self.choices.append(self.create_choice(
            from_node_name="conclusion_options",
            to_node_name="fallacy_non_sequitur",
            text="\"Therefore, Socrates is wise.\"",
            order=2,
            requires_state={
                "$and": [
                    {"all_men_are_mortal": True},
                    {"socrates_is_a_man": True}
                ]
            },
            sets_state={
                "conclusion_valid": False,
                "fallacy_committed": "non_sequitur"
            }
        ))
        self.debug("Created choice: conclusion_options → fallacy_non_sequitur")

        # ---------------------------------------------------------------------
        # FROM: fallacy nodes
        # Allow retry after learning from mistakes
        # ---------------------------------------------------------------------

        self.choices.append(self.create_choice(
            from_node_name="fallacy_affirming",
            to_node_name="retry",
            text="\"I understand my error. Let me try again.\"",
            order=0,
            sets_state={
                "fallacy_committed": "none"  # Reset for retry
            }
        ))
        self.debug("Created choice: fallacy_affirming → retry")

        self.choices.append(self.create_choice(
            from_node_name="fallacy_non_sequitur",
            to_node_name="retry",
            text="\"I see—the conclusion must use terms from the premises. Let me try again.\"",
            order=0,
            sets_state={
                "fallacy_committed": "none"  # Reset for retry
            }
        ))
        self.debug("Created choice: fallacy_non_sequitur → retry")

        self.choices.append(self.create_choice(
            from_node_name="skip_fallacy",
            to_node_name="major_premise",
            text="\"You're right. Let me learn the proper method, starting with the premises.\"",
            order=0,
            sets_state={
                "fallacy_committed": "none"  # Reset
            }
        ))
        self.debug("Created choice: skip_fallacy → major_premise")

        # ---------------------------------------------------------------------
        # FROM: retry
        # Return to conclusion options with knowledge intact
        # ---------------------------------------------------------------------

        self.choices.append(self.create_choice(
            from_node_name="retry",
            to_node_name="conclusion_options",
            text="\"I'm ready to try again.\"",
            order=0,
            requires_state={
                # Premises should still be established from before
                "$and": [
                    {"all_men_are_mortal": True},
                    {"socrates_is_a_man": True}
                ]
            }
            # No sets_state - preserve existing state
        ))
        self.debug("Created choice: retry → conclusion_options")

        self.log(f"  Created {len(self.choices)} choices")

        # Save choice IDs to results
        test_results["choice_ids"] = [c["id"] for c in self.choices]

        # =====================================================================
        # STEP 5: VALIDATE STATE SCHEMA
        # =====================================================================
        #
        # Ensure all state variables used in choices are defined in the schema.
        # This is the validation step before publishing.
        #
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
        description="Create a Carroll syllogism demonstration story"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--cleanup", action="store_true", help="Delete created story")
    args = parser.parse_args()

    test_results["start_time"] = datetime.now().isoformat()

    print("\n" + "=" * 70)
    print("  CARROLL SYLLOGISM STORY BUILDER")
    print("  Creating a demonstration of classical logical reasoning")
    print("=" * 70)

    try:
        # Get authenticated session
        session = get_authenticated_session()
        print(f"\n✓ Authenticated successfully")

        # Create the story builder
        builder = CarrollStoryBuilder(session, verbose=args.verbose)

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
        print("  │   ├─→ major_premise")
        print("  │   │     └─→ minor_premise")
        print("  │   │           └─→ conclusion_options")
        print("  │   │                 ├─→ valid_conclusion (END) ✓")
        print("  │   │                 ├─→ fallacy_affirming → retry")
        print("  │   │                 └─→ fallacy_non_sequitur → retry")
        print("  │   └─→ skip_fallacy → major_premise")
        print("  └─────────────────────────────────────────────")

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
