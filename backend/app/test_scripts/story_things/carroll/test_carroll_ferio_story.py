#!/usr/bin/env python3
"""
Carroll Ferio Story - Particular Negative Propositions

This script creates a story demonstrating the Ferio syllogism (EIO-1),
which introduces the O PROPOSITION (particular negative: "Some X are not Y").

    Major Premise:  "No poets are scientists"           (E proposition: No M are P)
    Minor Premise:  "Some dreamers are poets"           (I proposition: Some S are M)
    Conclusion:     "Some dreamers are not scientists"  (O proposition: Some S are not P)

KEY CONCEPTS INTRODUCED:
- O propositions: Particular Negative ("Some X are not Y")
- PARTIAL EXCLUSION: asserts at least one X is NOT in Y
- Distribution in O: predicate distributed, subject not distributed
- Non-convertibility: O propositions cannot be simply converted (unlike I)

=============================================================================
ARCHETYPES, PERSONAS, TRAITS, AND QUALITIES TO CREATE
=============================================================================

These entities represent the domain content being reasoned about.
They should be created before running this script (or could be created
programmatically as shown in commented sections).

ARCHETYPES (Categories/Sets):
-----------------------------
1. "Poets" (Middle Term - M)
   - Description: "Creative writers who express ideas and emotions through verse"
   - Represents artistic, intuitive, emotional thinking
   - Disjoint from Scientists (by major premise)

2. "Scientists" (Major Term - P)
   - Description: "Researchers who study the natural world through systematic observation"
   - Represents analytical, empirical, logical thinking
   - Disjoint from Poets (defining the major premise)

3. "Dreamers" (Minor Term - S)
   - Description: "Visionaries and imaginative thinkers"
   - Contains both poets and non-poets
   - Only SOME dreamers are asserted to be non-scientists

TRAITS (Properties):
--------------------
1. "Creative Expression"
   - Description: "Expresses ideas through artistic means"
   - Links Archetypes: Poets → has this
   - Associated with intuitive, emotional thinking

2. "Empirical Method"
   - Description: "Studies reality through observation and experimentation"
   - Links Archetypes: Scientists → has this
   - CONFLICTS WITH: "Creative Expression" (by major premise)

3. "Visionary Thinking"
   - Description: "Imagines possibilities beyond current reality"
   - Links Archetypes: Dreamers → has this, Poets → has this

PERSONAS (Individuals):
-----------------------
1. "William Blake"
   - Description: "English poet and painter, 1757-1827"
   - Member of Archetypes: Dreamers, Poets
   - NOT member of: Scientists
   - Example of dreamer-poet who is not a scientist

2. "Charles Darwin"
   - Description: "Naturalist who developed the theory of evolution"
   - Member of Archetypes: Scientists
   - NOT member of: Poets, Dreamers (conventional view)

3. "Leonardo da Vinci"
   - Description: "Renaissance polymath - artist, inventor, scientist"
   - Counter-example: Could be classified as both creative and empirical
   - Useful for exploring edge cases

=============================================================================

Usage:
    python test_carroll_ferio_story.py
    python test_carroll_ferio_story.py --verbose
    python test_carroll_ferio_story.py --cleanup  # Delete created story

Output:
    test_results_carroll_ferio.json
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
RESULTS_FILE = "test_results_carroll_ferio.json"

# Test results tracking
test_results = {
    "test_suite": "Carroll Ferio Story (EIO-1)",
    "start_time": None,
    "end_time": None,
    "story_id": None,
    "node_ids": {},
    "choice_ids": {},
    "state_variable_ids": {},
    "success": False,
    "errors": []
}


class FerioStoryBuilder:
    """Builds a Ferio syllogism story demonstrating O propositions (particular negative)."""

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
        """Build the complete Ferio syllogism story."""

        # =====================================================================
        # STEP 1: CREATE THE STORY
        # =====================================================================
        #
        # The story title and description set the context for the logical
        # exercise. This introduces the O proposition - the particular negative.
        #
        self.log("\n📖 Creating story...")

        story = self.create_story(
            title="The Dreamer's Paradox: A Study in Partial Exclusion",
            description="""Ferio syllogism (EIO-1) - introducing the O PROPOSITION (particular negative).

STRUCTURE:
- Major (E): No poets are scientists
- Minor (I): Some dreamers are poets  
- Conclusion (O): Some dreamers are not scientists

THE O PROPOSITION: "Some X are not Y" asserts PARTIAL EXCLUSION - at least one X 
is NOT in Y. This is the subtlest of the four proposition types, distributing only 
the predicate, not the subject.

DOMAIN: Victorian artistic quarter exploring the tension between creative expression 
and empirical method, using the figures of poets, scientists, and dreamers to 
demonstrate logical relationships."""
        )
        self.story_id = story["id"]
        test_results["story_id"] = self.story_id
        self.log(f"  Created story: {self.story_id}")

        # =====================================================================
        # STEP 2: DEFINE STATE SCHEMA
        # =====================================================================
        #
        # State variables track the logical progress through the Ferio syllogism.
        # They represent:
        # - Which premises have been established (E and I propositions)
        # - The new O proposition understanding
        # - The logical structure (figure 1, mood EIO)
        # - Fallacies specific to O propositions
        #
        self.log("\n📋 Creating state schema...")

        # ---------------------------------------------------------------------
        # Premise tracking variables
        # These correspond to establishing relationships between domain entities
        # ---------------------------------------------------------------------

        self.state_vars["major_premise"] = self.create_state_variable(
            key="no_poets_are_scientists",
            value_type="boolean",
            default_value=False,
            category="premises",
            description="Major premise (E): No M are P (No poets are scientists). "
                       "Asserts disjointness: Poets ∩ Scientists = ∅. "
                       "Domain: Trait 'Creative Expression' (Poets) CONFLICTS WITH "
                       "'Empirical Method' (Scientists)."
        )
        self.debug("Created: no_poets_are_scientists")

        self.state_vars["minor_premise"] = self.create_state_variable(
            key="some_dreamers_are_poets",
            value_type="boolean",
            default_value=False,
            category="premises",
            description="Minor premise (I): Some S are M (Some dreamers are poets). "
                       "Asserts overlap: Dreamers ∩ Poets ≠ ∅. "
                       "Domain: Some members of Archetype 'Dreamers' are also in 'Poets'."
        )
        self.debug("Created: some_dreamers_are_poets")

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
                       "Figure 1: M-P, S-M ∴ S-P (same as Barbara, Celarent, Darii)"
        )
        self.debug("Created: syllogism_figure")

        self.state_vars["mood"] = self.create_state_variable(
            key="syllogism_mood",
            value_type="string",
            default_value="",
            category="structure",
            description="Syllogism mood (combination of proposition types). "
                       "EIO = Ferio (Universal Negative - Particular Affirmative - Particular Negative)"
        )
        self.debug("Created: syllogism_mood")

        self.state_vars["proposition_types"] = self.create_state_variable(
            key="proposition_types_seen",
            value_type="string",
            default_value="",
            category="structure",
            description="Track E, I, O progression through story to complete the type inventory"
        )
        self.debug("Created: proposition_types_seen")

        # ---------------------------------------------------------------------
        # Conclusion and validity tracking
        # These track the player's reasoning attempts and understanding of O
        # ---------------------------------------------------------------------

        self.state_vars["conclusion"] = self.create_state_variable(
            key="some_dreamers_not_scientists",
            value_type="boolean",
            default_value=False,
            category="conclusions",
            description="Valid conclusion (O): Some S are not P (Some dreamers are not scientists). "
                       "Domain: At least one member of 'Dreamers' is NOT in 'Scientists' due to "
                       "the conflict between Creative Expression and Empirical Method traits."
        )
        self.debug("Created: some_dreamers_not_scientists")

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
            enum_values=["none", "illicit_conversion_O", "universal_from_particular", 
                        "affirmative_from_negative", "existential_import", "non_sequitur"],
            default_value="none",
            category="validation",
            description="Type of logical fallacy committed, if any. Includes O-specific fallacies."
        )
        self.debug("Created: fallacy_committed")

        # ---------------------------------------------------------------------
        # Learning progress tracking - O proposition understanding
        # ---------------------------------------------------------------------

        self.state_vars["understands_O"] = self.create_state_variable(
            key="understands_O_proposition",
            value_type="boolean",
            default_value=False,
            category="learning",
            description="Player understands particular negative propositions: 'Some X are not Y'"
        )
        self.debug("Created: understands_O_proposition")

        self.state_vars["understands_partial_exclusion"] = self.create_state_variable(
            key="understands_partial_exclusion",
            value_type="boolean",
            default_value=False,
            category="learning",
            description="Player grasps that O asserts SOME are excluded, not ALL"
        )
        self.debug("Created: understands_partial_exclusion")

        self.state_vars["understands_O_distribution"] = self.create_state_variable(
            key="understands_O_distribution",
            value_type="boolean",
            default_value=False,
            category="learning",
            description="Player knows O distributes predicate but not subject"
        )
        self.debug("Created: understands_O_distribution")

        self.state_vars["completed_proposition_types"] = self.create_state_variable(
            key="completed_all_proposition_types",
            value_type="boolean",
            default_value=False,
            category="learning",
            description="Player has seen all four proposition types: A, E, I, O"
        )
        self.debug("Created: completed_all_proposition_types")

        self.log(f"  Created {len(self.state_vars)} state variables")

        # =====================================================================
        # STEP 3: CREATE STORY NODES
        # =====================================================================
        #
        # Each node represents a stage in the logical reasoning process.
        # The content explains both the story and the underlying logic,
        # with special focus on introducing the O proposition concept.
        #
        self.log("\n📝 Creating story nodes...")

        # ---------------------------------------------------------------------
        # INTRODUCTION NODE (Start)
        # Sets the scene in Victorian artistic quarter
        # ---------------------------------------------------------------------

        self.nodes["intro"] = self.create_node(
            title="The Artistic Quarter",
            content="""# The Artistic Quarter, London 1875

You find yourself wandering through the bohemian quarter of Victorian London,
where artists' studios line cobblestone streets and the scent of oil paint 
mingles with coffee from literary cafes.

Through a window, you observe a heated debate between two figures:

A **poet** with ink-stained fingers gestures passionately: *"Science reduces 
the world to cold equations! It murders beauty with analysis!"*

A **scientist** in a leather apron replies calmly: *"Poetry is mere fancy—only 
empirical observation reveals truth!"*

An elderly **professor** notices your interest and approaches.

*"Ah, the eternal debate! These two represent different ways of understanding 
reality. But tell me—what of dreamers? Those visionary souls who imagine new 
possibilities?"*

He points to a third figure sketching impossible architectures.

*"Some dreamers, like that artist there, channel their visions through poetry. 
But are ALL dreamers poets? And can dreamers who ARE poets also be scientists? 
The logic is more subtle than it first appears..."*

---

**NEW CHALLENGE - THE O PROPOSITION:**

So far in your logical studies, you may have encountered:
- **A propositions**: "All X are Y" (universal affirmative)
- **E propositions**: "No X are Y" (universal negative)  
- **I propositions**: "Some X are Y" (particular affirmative)

Now we introduce the fourth and subtlest type:
- **O propositions**: "Some X are NOT Y" (particular negative)

This asserts **PARTIAL EXCLUSION** - some, but not necessarily all, 
members of X are excluded from Y.""",
            is_start=True
        )
        self.debug("Created node: intro")

        # ---------------------------------------------------------------------
        # MAJOR PREMISE NODE
        # Establishes: No poets are scientists (E proposition)
        # Domain: Creative Expression vs. Empirical Method conflict
        # ---------------------------------------------------------------------

        self.nodes["major_premise"] = self.create_node(
            title="The Great Divide",
            content="""# The Great Divide

The professor leads you to observe the debate more closely.

*"First, let us establish a fundamental truth about these two approaches to 
understanding reality."*

He gestures to the arguing figures:

**THE POET** speaks of inspiration, intuition, metaphor, and beauty. His method 
is **creative expression** - transforming inner vision into artistic form.

**THE SCIENTIST** speaks of hypotheses, experiments, measurement, and proof. 
His method is **empirical observation** - discovering truth through systematic study.

*"These are not merely different—they are fundamentally INCOMPATIBLE approaches. 
One cannot simultaneously be a pure poet AND a pure scientist. The mindsets 
exclude each other."*

```
┌─────────────────────────────────────────┐
│           MAJOR PREMISE                 │
│         (E Proposition)                 │
│                                         │
│   "No poets are scientists"             │
│                                         │
│   Logical form: No M are P              │
│   - M (Middle term) = Poets             │
│   - P (Major term) = Scientists         │
│                                         │
│   This is an E proposition:             │
│   Universal NEGATIVE                    │
│                                         │
│   Set theory: M ∩ P = ∅ (disjoint)      │
│                                         │
│   ┌─────────┐       ┌─────────┐         │
│   │  Poets  │       │Scientists│        │
│   │    ●    │   ───  │    ●    │         │
│   │ (Blake) │       │(Darwin) │         │
│   └─────────┘       └─────────┘         │
│                                         │
│   Complete separation!                  │
└─────────────────────────────────────────┘
```

*"Do you accept this premise? That the pure poet and pure scientist represent 
mutually exclusive ways of engaging with reality?"*

---

**DOMAIN MAPPING:**
- This premise asserts: Trait "Creative Expression" (Poets) CONFLICTS WITH "Empirical Method" (Scientists)
- `TraitConflict(trait_a="Creative Expression", trait_b="Empirical Method")`
- No Persona can have both traits as their primary method simultaneously"""
        )
        self.debug("Created node: major_premise")

        # ---------------------------------------------------------------------
        # MINOR PREMISE NODE
        # Establishes: Some dreamers are poets (I proposition)
        # Domain: Dreamers overlap with Poets (but not completely)
        # ---------------------------------------------------------------------

        self.nodes["minor_premise"] = self.create_node(
            title="The Dreamer's Overlap",
            content="""# The Dreamer's Overlap

The professor now directs your attention to the third figure—the dreamer 
sketching fantastic structures.

*"Now we need a particular fact about dreamers and their relationship to poetry."*

You observe various **dreamers** in the quarter:
- William Blake, sketching angels and writing verse
- A young woman painting impossible landscapes while reciting Shelley  
- An architect designing buildings that seem to float

*"Notice that some of these dreamers express their visions through POETRY. 
Blake channels his mystical dreams into verse. The woman weaves poetic imagery 
into her art."*

```
┌─────────────────────────────────────────┐
│           MINOR PREMISE                 │
│         (I Proposition)                 │
│                                         │
│   "Some dreamers are poets"             │
│                                         │
│   Logical form: Some S are M            │
│   - S (Minor term) = Dreamers           │
│   - M (Middle term) = Poets             │
│                                         │
│   This is an I proposition:             │
│   Particular AFFIRMATIVE                │
│                                         │
│       Dreamers              Poets       │
│   ┌───────────────┐     ┌───────────┐   │
│   │  Architects   │     │  Blake ●  │   │
│   │  Visionaries  ╠═════╣  Shelley  │   │
│   │  ●═══════════●│ ●●● │●══════════│   │
│   │   Blake ●     │     │  Byron    │   │
│   │  ●═══════════●│     │           │   │
│   │  Inventors    ╠═════╣  Keats    │   │
│   │               │     │           │   │
│   └───────────────┘     └───────────┘   │
│                                         │
│   The ● represent dreamer-poets         │
└─────────────────────────────────────────┘
```

*"But notice—NOT ALL dreamers are poets. Some dreamers are architects, 
inventors, or visionaries who don't express themselves through verse."*

*"So we have established: some dreamers ARE poets. What can we now conclude 
about dreamers and scientists?"*

---

**DOMAIN MAPPING:**
- This premise asserts: Some members of Archetype "Dreamers" are also in Archetype "Poets"
- `ArchetypeOverlap(archetype_a="Dreamers", archetype_b="Poets", type="partial")`
- The overlap contains individuals like Blake, Shelley who are both dreamers AND poets

**LOGICAL STRUCTURE SO FAR:**
- Major (E): No M are P ✓ (No poets are scientists)
- Minor (I): Some S are M ✓ (Some dreamers are poets)
- Conclusion: ??? (What about dreamers and scientists?)"""
        )
        self.debug("Created node: minor_premise")

        # ---------------------------------------------------------------------
        # CONCLUSION OPTIONS NODE
        # Player must choose the correct O proposition conclusion
        # ---------------------------------------------------------------------

        self.nodes["conclusion_options"] = self.create_node(
            title="The Moment of Logical Deduction",
            content="""# The Moment of Logical Deduction

The professor looks at you with keen interest.

*"Now comes the crucial reasoning step. You have established two truths:*
1. *No poets are scientists* (complete separation)
2. *Some dreamers are poets* (partial overlap)

*"What follows logically about the relationship between dreamers and scientists?"*

```
┌─────────────────────────────────────────┐
│         SYLLOGISM STRUCTURE             │
│              (Ferio)                    │
│                                         │
│   Major (E): No M are P                 │
│              (No poets are scientists)  │
│                                         │
│   Minor (I): Some S are M               │
│              (Some dreamers are poets)  │
│                                         │
│   ════════════════════════════════════  │
│                                         │
│   Conclusion: ???                       │
│                                         │
│   Visual reasoning:                     │
│                                         │
│   ┌─────────┐       ┌─────────┐         │
│   │ Poets   │  ───  │Scientists│        │
│   │  ╔══════╪═══╗   │         │         │
│   │  ║ ●●●  │   ║   │         │         │
│   │  ╚══════╪═══╝   │         │         │
│   └─────────┘       └─────────┘         │
│       ↑                                 │
│   Dreamer-poets                         │
│   (Blake, Shelley...)                   │
│                                         │
│   If these dreamers are in the poet     │
│   circle, and the poet circle is        │
│   completely separate from scientists.. │
│   Where are these dreamers relative     │
│   to scientists?                        │
└─────────────────────────────────────────┘
```

---

**CRITICAL THINKING POINT:**
- The middle term (Poets) connects dreamers to the exclusion from scientists
- Some dreamers → Poets → completely outside Scientists  
- Therefore: those same dreamers must be... ?

**Choose your conclusion carefully!**"""
        )
        self.debug("Created node: conclusion_options")

        # ---------------------------------------------------------------------
        # VALID CONCLUSION NODE (Success)
        # The correct O proposition: Some dreamers are not scientists
        # ---------------------------------------------------------------------

        self.nodes["valid_conclusion"] = self.create_node(
            title="Ferio Achieved: The O Proposition",
            content="""# Ferio Achieved: The O Proposition

*"Some dreamers are not scientists,"* you declare.

The professor's eyes light up with approval.

*"Magnificent! You have mastered the FERIO syllogism and discovered the fourth 
type of proposition—the particular negative!"*

```
┌─────────────────────────────────────────┐
│           VALID SYLLOGISM               │
│             (Ferio)                     │
│                                         │
│   No poets are scientists       (E)     │
│   Some dreamers are poets        (I)    │
│   ──────────────────────────────────    │
│   ∴ Some dreamers are not scientists (O)│
│                                         │
│   Form: EIO-1 (Ferio)                   │
│   Figure: 1 (M-P, S-M ∴ S-P)            │
│   Mood: EIO                             │
│                                         │
│         VALID ✓                         │
└─────────────────────────────────────────┘
```

*"Notice the beautiful logic: Since some dreamers ARE poets, and ALL poets 
are excluded from being scientists, those same dreamers must also be excluded 
from being scientists."*

**THE O PROPOSITION EXPLAINED:**

*"Your conclusion—'Some dreamers are not scientists'—introduces the O proposition. 
This is FUNDAMENTALLY different from the other types:*

**PARTIAL EXCLUSION**: Unlike "No dreamers are scientists" (E), the O proposition 
asserts that SOME (at least one) but not necessarily ALL dreamers are excluded.

**ASYMMETRIC**: Unlike I propositions, O propositions are NOT convertible. 
"Some dreamers are not scientists" does NOT mean "Some scientists are not dreamers."

**DISTRIBUTION**: In O propositions, the PREDICATE is distributed (all scientists 
are excluded from the "some dreamers" we're discussing), but the SUBJECT is not 
(we make no claim about ALL dreamers).

```
    Complete Proposition Type Inventory:
    ───────────────────────────────────
    A: All X are Y      (universal affirmative)
    E: No X are Y       (universal negative)  
    I: Some X are Y     (particular affirmative)
    O: Some X are not Y (particular negative)  ← YOU ARE HERE!
```

*"With Ferio, you have now encountered all four proposition types! You understand 
the complete logical foundation of Aristotelian syllogisms."*

---

**DOMAIN MAPPING:**
- Conclusion establishes: Some members of "Dreamers" are NOT in "Scientists"
- Specifically: dreamer-poets (Blake, Shelley) are excluded due to trait conflict
- The chain: Some Dreamers → Poets → (conflicting traits) → excluded from Scientists

**FERIO'S PLACE IN LOGIC:**
- Completes Figure 1: With Barbara (AAA), Celarent (EAE), Darii (AII), and Ferio (EIO)
- Introduces partial exclusion reasoning
- Foundation for more complex syllogisms like Baroco and Bocardo""",
            is_end=True
        )
        self.debug("Created node: valid_conclusion")

        # ---------------------------------------------------------------------
        # FALLACY NODE: Illicit Conversion of O
        # Invalid inference: "Some scientists are not dreamers"
        # ---------------------------------------------------------------------

        self.nodes["fallacy_conversion"] = self.create_node(
            title="The Conversion Error",
            content="""# The Conversion Error

*"Some scientists are not dreamers?"* The professor shakes his head gently.

*"Ah, you have committed a subtle but crucial error—the ILLICIT CONVERSION 
of an O proposition!"*

```
┌─────────────────────────────────────────┐
│              FALLACY                    │
│       Illicit Conversion of O           │
│                                         │
│   You attempted to convert:             │
│   "Some dreamers are not scientists"    │
│           ↓                             │
│   "Some scientists are not dreamers"    │
│                                         │
│   But O propositions are NOT            │
│   convertible!                          │
│                                         │
│   Unlike I propositions:                │
│   ✓ "Some Greeks are philosophers"      │
│   ✓ "Some philosophers are Greeks"      │
│                                         │
│   O propositions are ASYMMETRIC:        │
│   ✓ "Some dreamers are not scientists"  │
│   ✗ "Some scientists are not dreamers"  │
└─────────────────────────────────────────┘
```

*"Here's why the conversion fails:*

**THE ASYMMETRY OF EXCLUSION:**

Our syllogism proves that certain dreamers (the poet-dreamers) are excluded 
from being scientists. But it tells us NOTHING about whether scientists might 
be excluded from being dreamers!

**Consider the logical chain:**
- Some dreamers → poets → (conflict) → not scientists ✓
- Scientists → ??? → not dreamers ✗ (No established connection!)

**Counter-example possibility:**
What if there existed a scientist who was ALSO a dreamer, but simply not a poet? 
Our premises don't rule this out! A scientific dreamer might dream of discoveries, 
not verses.

---

**DOMAIN INSIGHT:**
- We proved: dreamer-POETS are not scientists (due to Creative Expression vs. Empirical Method conflict)  
- We did NOT prove: scientists cannot be dreamers in other ways
- The exclusion is specific to the poet-dreamers, not all possible dreamers

**KEY LESSON:**
O propositions are directional. The exclusion flows in one direction only, 
determined by the logical structure of the premises."""
        )
        self.debug("Created node: fallacy_conversion")

        # ---------------------------------------------------------------------
        # FALLACY NODE: Universal from Particular  
        # Invalid inference: "No dreamers are scientists" or "All dreamers are not scientists"
        # ---------------------------------------------------------------------

        self.nodes["fallacy_universal"] = self.create_node(
            title="The Universalization Error",
            content="""# The Universalization Error

*"No dreamers are scientists?"* The professor looks concerned.

*"You have committed the fallacy of drawing a UNIVERSAL conclusion from a 
PARTICULAR premise!"*

```
┌─────────────────────────────────────────┐
│              FALLACY                    │
│     Universal from Particular           │
│                                         │
│   Your claim: "NO dreamers are          │
│               scientists" (E)           │
│                                         │
│   But your minor premise only said:     │
│   "SOME dreamers are poets" (I)         │
│                                         │
│   You can only conclude about the       │
│   dreamers who ARE poets, not about     │
│   ALL dreamers!                         │
│                                         │
│   ┌────── Dreamers ──────┐              │
│   │                      │              │
│   │  ┌─ Poet-dreamers ─┐  │ ← These are │
│   │  │ ✗ (not sci.)   │  │   excluded   │
│   │  └────────────────┘  │              │
│   │                      │              │
│   │  Other dreamers:     │              │
│   │  • Scientific       │ ← What about  │
│   │    dreamers?      ?  │   these?     │
│   │  • Practical        │              │
│   │    dreamers?      ?  │              │
│   └──────────────────────┘              │
└─────────────────────────────────────────┘
```

*"Our reasoning chain only covers specific dreamers:*

**WHAT WE PROVED:**
- Some dreamers are poets (premise)
- Those poet-dreamers are not scientists (because poets ≠ scientists)  
- Therefore: SOME dreamers are not scientists ✓

**WHAT WE DID NOT PROVE:**
- We know nothing about non-poet dreamers
- Could there be dreamers who dream of scientific discoveries?
- Could there be practical dreamers who use empirical methods?

**Counter-example:**
Imagine a dreamer who dreams of curing diseases and pursues that dream through 
scientific research. Our premises don't exclude this possibility!

---

**DOMAIN INSIGHT:**
- Only dreamer-poets are excluded from science (due to trait conflict)
- Other types of dreamers (scientific dreamers, practical dreamers) remain possibilities
- The Archetype "Dreamers" is broader than just the poet subset

**REMEMBER:**
From particular premises (I or O), you can only draw particular conclusions (I or O), 
never universal ones (A or E)."""
        )
        self.debug("Created node: fallacy_universal")

        # ---------------------------------------------------------------------
        # FALLACY NODE: Affirmative from Negative
        # Invalid inference: "Some dreamers are scientists"
        # ---------------------------------------------------------------------

        self.nodes["fallacy_affirmative"] = self.create_node(
            title="The Quality Error",
            content="""# The Quality Error

*"Some dreamers are scientists?"* The professor looks puzzled.

*"You have attempted to draw an AFFIRMATIVE conclusion from a NEGATIVE premise!"*

```
┌─────────────────────────────────────────┐
│              FALLACY                    │
│    Affirmative from Negative Premise    │
│                                         │
│   Your major premise was NEGATIVE:      │
│   "NO poets are scientists" (E)         │
│                                         │
│   This establishes SEPARATION,          │
│   not CONNECTION.                       │
│                                         │
│   You cannot conclude that something    │
│   IS connected when your evidence       │
│   only tells you what is NOT connected. │
│                                         │
│   RULE: From a negative premise,        │
│   only negative conclusions follow.     │
│                                         │
│   ┌─────────┐       ┌─────────┐         │
│   │ Poets   │  ───  │Scientists│        │
│   │   ●●●   │   X   │    ●    │         │
│   │(dreamers│       │         │         │
│   │ who are │       │         │         │
│   │ poets)  │       │         │         │
│   └─────────┘       └─────────┘         │
│                                         │
│   The gap shows EXCLUSION, not inclusion│
└─────────────────────────────────────────┘
```

*"Think about the logic:*

**OUR PREMISES ESTABLISH:**
1. Poets and scientists are COMPLETELY SEPARATE (E: No connection)
2. Some dreamers are IN the poet category (I: Partial membership)

**THE LOGICAL CHAIN:**
- Some dreamers → inside poet circle → outside scientist circle
- This creates EXCLUSION, not inclusion

**WHY AFFIRMATIVE FAILS:**
To conclude "Some dreamers ARE scientists," you would need:
- Either an affirmative premise connecting dreamers to scientists directly
- Or an affirmative premise connecting dreamers to some group that connects to scientists

But our major premise SEVERS the connection between the dreamer-poets and scientists!

---

**DOMAIN INSIGHT:**
- The trait conflict (Creative Expression vs. Empirical Method) creates SEPARATION
- Dreamer-poets inherit the Creative Expression trait  
- This trait CONFLICTS with the Empirical Method trait required for science
- Therefore: connection is impossible, exclusion is necessary

**QUALITY RULE:**
The "quality" (affirmative vs. negative) of your conclusion must match the pattern 
established by your premises."""
        )
        self.debug("Created node: fallacy_affirmative")

        # ---------------------------------------------------------------------
        # RETRY NODE
        # Allows player to try again after committing a fallacy
        # ---------------------------------------------------------------------

        self.nodes["retry"] = self.create_node(
            title="Reconsider the Evidence",
            content="""# Reconsider the Evidence

The professor offers an encouraging smile.

*"The O proposition is indeed the most subtle of the four types. Let us review 
what we have established:*

**Premise 1 (E):** No poets are scientists  
- Complete separation between creative and empirical approaches
- Establishes an absolute boundary

**Premise 2 (I):** Some dreamers are poets
- Partial overlap: dreamer-poets like Blake and Shelley exist
- But NOT all dreamers are poets

*"Now, given these two truths, what must be true about the relationship between 
dreamers and scientists?*

**Key insight:** The dreamers who ARE poets cannot cross the boundary into science. 
But what specific type of conclusion does this support?"

```
    ┌──────────────────┐       ┌──────────────┐
    │      Poets       │  ───  │  Scientists  │
    │   ┌───────────┐  │       │              │
    │   │ ●●●       │  │       │              │
    │   │ Dreamer-  │  │       │              │
    │   │ poets     │  │       │              │
    │   └───────────┘  │       │              │
    └──────────────────┘       └──────────────┘
           ↑
    These specific dreamers must be _____ scientists?
```

*"Remember: your conclusion should be PARTICULAR (about some, not all) and 
NEGATIVE (expressing exclusion, not inclusion)."*

---

**LOGICAL HINT:**
- Subject: Some dreamers (the poet ones)
- Predicate: Scientists  
- Relationship: Exclusion (not inclusion)
- Quantity: Particular (some, not all)

Form: "Some S are not P" → This is an O proposition!"""
        )
        self.debug("Created node: retry")

        # ---------------------------------------------------------------------
        # SKIP PREMISES NODE (Fallacy path)
        # What happens if you try to conclude without establishing premises
        # ---------------------------------------------------------------------

        self.nodes["skip_fallacy"] = self.create_node(
            title="The Hasty Conclusion",
            content="""# The Hasty Conclusion

You attempt to make a judgment about dreamers and scientists, but the professor 
raises his hand.

*"Wait! You cannot determine the relationship between dreamers and scientists 
without first establishing the intermediate logical connections."*

```
┌─────────────────────────────────────────┐
│              FALLACY                    │
│       Hasty Generalization              │
│                                         │
│   To logically prove anything about     │
│   dreamers and scientists, we need:     │
│                                         │
│   1. The relationship between           │
│      poets and scientists               │
│      (Are they compatible? Separate?)   │
│                                         │
│   2. The relationship between           │
│      dreamers and poets                 │
│      (Do any dreamers use poetry?)      │
│                                         │
│   Only THEN can we deduce the           │
│   relationship between dreamers         │
│   and scientists.                       │
└─────────────────────────────────────────┘
```

*"Logic requires methodical reasoning. We cannot leap to conclusions based on 
intuition or casual observation. Let us proceed systematically..."*

*"First, we must examine whether poets and scientists represent compatible 
or incompatible approaches to understanding reality..."*

---

**DOMAIN INSIGHT:**
- Without establishing TraitConflict(Creative Expression, Empirical Method), 
  we cannot reason about exclusion
- Without establishing ArchetypeOverlap(Dreamers, Poets), we cannot connect 
  dreamers to the conflict
- Logical chains must be built step by step

**THE SYSTEMATIC APPROACH:**
1. Establish major premise (universal relationship)
2. Establish minor premise (particular connection)  
3. THEN derive the valid conclusion"""
        )
        self.debug("Created node: skip_fallacy")

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
            text="\"Teach me about the relationship between poets and scientists.\"",
            order=0,
            # No requires_state - anyone can start
            sets_state={
                "understands_O_proposition": False,  # Will learn this
                "proposition_types_seen": ""  # Start tracking
            }
        ))
        self.debug("Created choice: intro → major_premise")

        self.choices.append(self.create_choice(
            from_node_name="intro",
            to_node_name="skip_fallacy",
            text="\"Dreamers obviously aren't scientists! They're too impractical.\"",
            order=1,
            # No requires_state - but this leads to fallacy
            sets_state={
                "fallacy_committed": "hasty_generalization"
            }
        ))
        self.debug("Created choice: intro → skip_fallacy (hasty)")

        # ---------------------------------------------------------------------
        # FROM: major_premise
        # Player accepts the E proposition about poets vs scientists
        # ---------------------------------------------------------------------

        self.choices.append(self.create_choice(
            from_node_name="major_premise",
            to_node_name="minor_premise",
            text="\"I accept this - poets and scientists represent incompatible approaches.\"",
            order=0,
            # No requires_state - this establishes the first premise
            sets_state={
                # LOGICAL STATE: Establishes No M are P (E proposition)
                # DOMAIN: TraitConflict(Creative Expression, Empirical Method)
                "no_poets_are_scientists": True,
                "proposition_types_seen": "E",  # Track E proposition
                "syllogism_mood": "E"  # First part of EIO
            }
        ))
        self.debug("Created choice: major_premise → minor_premise (accept)")

        # ---------------------------------------------------------------------
        # FROM: minor_premise
        # Player accepts the I proposition about dreamers and poets
        # ---------------------------------------------------------------------

        self.choices.append(self.create_choice(
            from_node_name="minor_premise",
            to_node_name="conclusion_options",
            text="\"I understand - some dreamers channel their visions through poetry.\"",
            order=0,
            requires_state={
                # Must have already accepted the major premise
                "no_poets_are_scientists": True
            },
            sets_state={
                # LOGICAL STATE: Establishes Some S are M (I proposition)
                # DOMAIN: ArchetypeOverlap(Dreamers, Poets)
                "some_dreamers_are_poets": True,
                "proposition_types_seen": "EI",  # Track E and I
                "syllogism_mood": "EI",  # First two parts of EIO
                "syllogism_figure": "figure_1"  # Establish Figure 1 pattern
            }
        ))
        self.debug("Created choice: minor_premise → conclusion_options (accept)")

        # ---------------------------------------------------------------------
        # FROM: conclusion_options
        # The critical choice: select the correct O proposition conclusion
        # ---------------------------------------------------------------------

        # VALID CONCLUSION: Some dreamers are not scientists (O proposition)
        self.choices.append(self.create_choice(
            from_node_name="conclusion_options",
            to_node_name="valid_conclusion",
            text="\"Therefore, some dreamers are not scientists.\"",
            order=0,
            requires_state={
                # BOTH premises must be established for valid inference
                # This models: (No M are P) ∧ (Some S are M) → (Some S are not P)
                "$and": [
                    {"no_poets_are_scientists": True},
                    {"some_dreamers_are_poets": True}
                ]
            },
            sets_state={
                # LOGICAL STATE: Derives Some S are not P (O proposition)
                # DOMAIN: Some Dreamers excluded from Scientists due to trait conflict
                "some_dreamers_not_scientists": True,
                "conclusion_valid": True,
                "syllogism_mood": "EIO",  # Complete Ferio mood
                "proposition_types_seen": "EIO",  # All three types seen
                "understands_O_proposition": True,
                "understands_partial_exclusion": True,
                "understands_O_distribution": True,
                "completed_all_proposition_types": True,  # A,E,I,O all seen across stories
                "fallacy_committed": "none"
            }
        ))
        self.debug("Created choice: conclusion_options → valid_conclusion (CORRECT)")

        # FALLACY: Illicit conversion (Some scientists are not dreamers)
        self.choices.append(self.create_choice(
            from_node_name="conclusion_options",
            to_node_name="fallacy_conversion",
            text="\"Therefore, some scientists are not dreamers.\"",
            order=1,
            requires_state={
                "$and": [
                    {"no_poets_are_scientists": True},
                    {"some_dreamers_are_poets": True}
                ]
            },
            sets_state={
                "conclusion_valid": False,
                "fallacy_committed": "illicit_conversion_O"
            }
        ))
        self.debug("Created choice: conclusion_options → fallacy_conversion")

        # FALLACY: Universal conclusion (No dreamers are scientists)
        self.choices.append(self.create_choice(
            from_node_name="conclusion_options",
            to_node_name="fallacy_universal",
            text="\"Therefore, no dreamers are scientists.\"",
            order=2,
            requires_state={
                "$and": [
                    {"no_poets_are_scientists": True},
                    {"some_dreamers_are_poets": True}
                ]
            },
            sets_state={
                "conclusion_valid": False,
                "fallacy_committed": "universal_from_particular"
            }
        ))
        self.debug("Created choice: conclusion_options → fallacy_universal")

        # FALLACY: Affirmative conclusion (Some dreamers are scientists)
        self.choices.append(self.create_choice(
            from_node_name="conclusion_options",
            to_node_name="fallacy_affirmative",
            text="\"Therefore, some dreamers are scientists.\"",
            order=3,
            requires_state={
                "$and": [
                    {"no_poets_are_scientists": True},
                    {"some_dreamers_are_poets": True}
                ]
            },
            sets_state={
                "conclusion_valid": False,
                "fallacy_committed": "affirmative_from_negative"
            }
        ))
        self.debug("Created choice: conclusion_options → fallacy_affirmative")

        # ---------------------------------------------------------------------
        # FROM: fallacy nodes
        # Allow retry after learning from mistakes
        # ---------------------------------------------------------------------

        self.choices.append(self.create_choice(
            from_node_name="fallacy_conversion",
            to_node_name="retry",
            text="\"I see - O propositions can't be converted like I propositions. Let me reconsider.\"",
            order=0,
            sets_state={
                "fallacy_committed": "none"  # Reset for retry
            }
        ))
        self.debug("Created choice: fallacy_conversion → retry")

        self.choices.append(self.create_choice(
            from_node_name="fallacy_universal",
            to_node_name="retry",
            text="\"I understand - I can only conclude about the dreamers who ARE poets.\"",
            order=0,
            sets_state={
                "fallacy_committed": "none"  # Reset for retry
            }
        ))
        self.debug("Created choice: fallacy_universal → retry")

        self.choices.append(self.create_choice(
            from_node_name="fallacy_affirmative",
            to_node_name="retry",
            text="\"Right - the negative premise creates exclusion, not inclusion.\"",
            order=0,
            sets_state={
                "fallacy_committed": "none"  # Reset for retry
            }
        ))
        self.debug("Created choice: fallacy_affirmative → retry")

        self.choices.append(self.create_choice(
            from_node_name="skip_fallacy",
            to_node_name="major_premise",
            text="\"You're right. Let me learn the systematic approach, starting with the premises.\"",
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
            text="\"I'm ready to make the correct logical deduction.\"",
            order=0,
            requires_state={
                # Premises should still be established from before
                "$and": [
                    {"no_poets_are_scientists": True},
                    {"some_dreamers_are_poets": True}
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
        # This is the validation step before the story can be used.
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
        description="Create a Carroll Ferio syllogism demonstration story"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--cleanup", action="store_true", help="Delete created story")
    args = parser.parse_args()

    test_results["start_time"] = datetime.now().isoformat()

    print("\n" + "=" * 70)
    print("  CARROLL FERIO STORY BUILDER")
    print("  Creating a demonstration of particular negative reasoning (O proposition)")
    print("=" * 70)

    try:
        # Get authenticated session
        session = get_authenticated_session()
        print(f"\n✓ Authenticated successfully")

        # Create the story builder
        builder = FerioStoryBuilder(session, verbose=args.verbose)

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
        print("  │   ├─→ major_premise (E: No poets are scientists)")
        print("  │   │     └─→ minor_premise (I: Some dreamers are poets)")
        print("  │   │           └─→ conclusion_options")
        print("  │   │                 ├─→ valid_conclusion (O: Some dreamers are not scientists) ✓")
        print("  │   │                 ├─→ fallacy_conversion (illicit conversion) → retry")
        print("  │   │                 ├─→ fallacy_universal (universal from particular) → retry")
        print("  │   │                 └─→ fallacy_affirmative (affirmative from negative) → retry")
        print("  │   └─→ skip_fallacy → major_premise")
        print("  └─────────────────────────────────────────────")

        print(f"\n  NEW CONCEPT INTRODUCED:")
        print(f"  🆕 O Proposition: \"Some X are not Y\" (particular negative)")
        print(f"  🆕 Partial exclusion reasoning")
        print(f"  🆕 Non-convertibility of O propositions")
        print(f"  🆕 All four proposition types now available: A, E, I, O")

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