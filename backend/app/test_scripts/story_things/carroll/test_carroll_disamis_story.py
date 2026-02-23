#!/usr/bin/env python3
"""
Carroll Disamis Story - Figure 3 Syllogisms

This script creates a story demonstrating the Disamis syllogism (IAI-3),
which introduces FIGURE 3 - where the middle term is SUBJECT in both premises.

    Major Premise:  "Some musicians are mathematicians"    (I proposition: Some M are P)
    Minor Premise:  "All musicians read sheet music"       (A proposition: All M are S)
    Conclusion:     "Some who read sheet music are mathematicians" (I proposition: Some S are P)

KEY CONCEPTS INTRODUCED:
- Figure 3: M-P, M-S → S-P (middle term is subject in both premises)
- Figure 3 CONSTRAINT: Can only yield PARTICULAR conclusions (I or O), never universal (A or E)
- This is because the minor term (S) is never distributed in Figure 3
- Existential import: reasoning from overlap existence to conclusion existence

=============================================================================
ARCHETYPES, PERSONAS, TRAITS, AND QUALITIES TO CREATE
=============================================================================

ARCHETYPES (Categories/Sets):
-----------------------------
1. "Musicians" (Middle Term - M)
   - Description: "Those who create, perform, or study music"
   - Some members are also mathematicians (by major premise)
   - All members read sheet music (by minor premise)

2. "Mathematicians" (Major Term - P)
   - Description: "Those who study numbers, patterns, and abstract structures"
   - Some members are also musicians (by major premise)
   - Known for logical, analytical thinking

3. "Sheet Music Readers" (Minor Term - S)
   - Description: "Those who can read and interpret musical notation"
   - All musicians belong to this group (by minor premise)
   - Includes some who are mathematicians (by conclusion)

TRAITS (Properties):
--------------------
1. "Musical Ability"
   - Description: "Can create, perform, or understand music"
   - Links: ALL Musicians → have this trait
   - Some who read sheet music have this at professional level

2. "Mathematical Thinking"
   - Description: "Understands patterns, logic, and abstract relationships"
   - Links: ALL Mathematicians → have this trait
   - Links: SOME Musicians → have this trait (the overlap group)

3. "Reads Musical Notation"
   - Description: "Can interpret the symbols and structure of written music"
   - Links: ALL Musicians → have this trait (by minor premise)
   - Links: SOME Sheet Music Readers → may not be professional musicians

PERSONAS (Individuals):
-----------------------
1. "Johann Sebastian Bach"
   - Description: "Baroque composer known for mathematical precision in music"
   - Member of: Musicians, Mathematicians (famous overlap example)
   - Traits: Musical Ability, Mathematical Thinking, Reads Musical Notation

2. "Leonhard Euler"
   - Description: "Swiss mathematician who wrote on music theory"
   - Member of: Mathematicians, (arguably Musicians through theory)
   - Historical figure connecting mathematics and music

3. "Clara Schumann"  
   - Description: "Virtuoso pianist and composer"
   - Member of: Musicians, Sheet Music Readers
   - May or may not have mathematical inclinations (individual variation)

=============================================================================

Usage:
    python test_carroll_disamis_story.py
    python test_carroll_disamis_story.py --verbose
    python test_carroll_disamis_story.py --cleanup

Output:
    test_results_carroll_disamis.json
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
RESULTS_FILE = "test_results_carroll_disamis.json"

# Test results tracking
test_results = {
    "test_suite": "Carroll Disamis Story (IAI-3)",
    "start_time": None,
    "end_time": None,
    "story_id": None,
    "node_ids": {},
    "choice_ids": {},
    "state_variable_ids": {},
    "success": False,
    "errors": []
}


class DisamistoryBuilder:
    """Builds a Disamis syllogism story demonstrating Figure 3 reasoning."""

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
        """Build the complete Disamis syllogism story."""

        # =====================================================================
        # STEP 1: CREATE THE STORY
        # =====================================================================
        self.log("\n📖 Creating story...")

        story = self.create_story(
            title="The Conservatory's Paradox: A Study in Figure 3",
            description="""Disamis syllogism (IAI-3) - introducing FIGURE 3 reasoning.

STRUCTURE:
- Major (I): Some musicians are mathematicians
- Minor (A): All musicians read sheet music  
- Conclusion (I): Some who read sheet music are mathematicians

FIGURE 3 INNOVATION: The middle term "musicians" appears as SUBJECT in both 
premises (M-P, M-S). This creates unique constraints on possible conclusions.

FIGURE 3 CONSTRAINT: Can ONLY yield particular conclusions (I or O), never 
universal ones (A or E). This is because the minor term is never distributed 
in Figure 3, preventing universal claims about it.

DOMAIN: Victorian music conservatory exploring the famous connection between 
musical and mathematical thinking, demonstrating existential reasoning patterns."""
        )
        self.story_id = story["id"]
        test_results["story_id"] = self.story_id
        self.log(f"  Created story: {self.story_id}")

        # =====================================================================
        # STEP 2: DEFINE STATE SCHEMA
        # =====================================================================
        self.log("\n📋 Creating state schema...")

        # ---------------------------------------------------------------------
        # Premise tracking - note the Figure 3 structure
        # ---------------------------------------------------------------------

        self.state_vars["major_premise"] = self.create_state_variable(
            key="some_musicians_are_mathematicians",
            value_type="boolean",
            default_value=False,
            category="premises",
            description="Major premise (I): Some M are P (Some musicians are mathematicians). "
                       "Asserts overlap: Musicians ∩ Mathematicians ≠ ∅. "
                       "Domain: Some members of Archetype 'Musicians' also belong to 'Mathematicians'."
        )
        self.debug("Created: some_musicians_are_mathematicians")

        self.state_vars["minor_premise"] = self.create_state_variable(
            key="all_musicians_read_sheet_music",
            value_type="boolean", 
            default_value=False,
            category="premises",
            description="Minor premise (A): All M are S (All musicians read sheet music). "
                       "Asserts universal trait: Musicians ⊆ {Sheet Music Readers}. "
                       "Domain: All members of Archetype 'Musicians' possess Trait 'Reads Musical Notation'."
        )
        self.debug("Created: all_musicians_read_sheet_music")

        # ---------------------------------------------------------------------
        # Figure 3 structure tracking - NEW CONCEPT
        # ---------------------------------------------------------------------

        self.state_vars["figure"] = self.create_state_variable(
            key="syllogism_figure",
            value_type="enum",
            enum_values=["figure_1", "figure_2", "figure_3", "figure_4"],
            default_value="figure_3",
            category="structure",
            description="Figure 3: M-P, M-S ∴ S-P pattern. Middle term is SUBJECT in both premises."
        )
        self.debug("Created: syllogism_figure")

        self.state_vars["mood"] = self.create_state_variable(
            key="syllogism_mood",
            value_type="string",
            default_value="",
            category="structure",
            description="Syllogism mood: IAI for Disamis (Some-All-Some)"
        )
        self.debug("Created: syllogism_mood")

        self.state_vars["figure_3_constraint"] = self.create_state_variable(
            key="understands_figure_3_constraint",
            value_type="boolean",
            default_value=False,
            category="structure", 
            description="Player understands Figure 3 can only yield particular conclusions"
        )
        self.debug("Created: understands_figure_3_constraint")

        # ---------------------------------------------------------------------
        # Conclusion and validation tracking
        # ---------------------------------------------------------------------

        self.state_vars["conclusion"] = self.create_state_variable(
            key="some_sheet_music_readers_are_mathematicians",
            value_type="boolean",
            default_value=False,
            category="conclusions",
            description="Valid conclusion (I): Some S are P (Some sheet music readers are mathematicians). "
                       "Domain: The musician-mathematicians also read sheet music, creating overlap "
                       "between 'Sheet Music Readers' and 'Mathematicians'."
        )
        self.debug("Created: some_sheet_music_readers_are_mathematicians")

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
            enum_values=["none", "illicit_minor", "universal_from_particular", 
                        "existential_fallacy", "undistributed_middle", "non_sequitur"],
            default_value="none",
            category="validation",
            description="Type of logical fallacy committed, if any"
        )
        self.debug("Created: fallacy_committed")

        # ---------------------------------------------------------------------
        # Learning progress tracking - Figure 3 concepts
        # ---------------------------------------------------------------------

        self.state_vars["understands_figure_3"] = self.create_state_variable(
            key="understands_figure_3_reasoning",
            value_type="boolean",
            default_value=False,
            category="learning",
            description="Player understands Figure 3's middle-term-as-subject pattern"
        )
        self.debug("Created: understands_figure_3_reasoning")

        self.state_vars["understands_particular_only"] = self.create_state_variable(
            key="understands_particular_conclusions_only",
            value_type="boolean",
            default_value=False,
            category="learning",
            description="Player grasps why Figure 3 cannot yield universal conclusions"
        )
        self.debug("Created: understands_particular_conclusions_only")

        self.state_vars["understands_existential_import"] = self.create_state_variable(
            key="understands_existential_import",
            value_type="boolean",
            default_value=False,
            category="learning",
            description="Player understands reasoning from existence of overlap to conclusion"
        )
        self.debug("Created: understands_existential_import")

        self.state_vars["music_math_connection"] = self.create_state_variable(
            key="music_math_connection",
            value_type="boolean",
            default_value=False,
            category="learning",
            description="Player sees the historical/cultural connection between music and mathematics"
        )
        self.debug("Created: appreciates_music_mathematics_connection")

        self.log(f"  Created {len(self.state_vars)} state variables")

        # =====================================================================
        # STEP 3: CREATE STORY NODES
        # =====================================================================
        self.log("\n📝 Creating story nodes...")

        # ---------------------------------------------------------------------
        # INTRODUCTION NODE (Start) - Music Conservatory
        # ---------------------------------------------------------------------

        self.nodes["intro"] = self.create_node(
            title="The Royal Conservatory of Music",
            content="""# The Royal Conservatory of Music, London 1885

You enter the grand hall of the Royal Conservatory, where the sounds of 
practice drift through mahogany-paneled corridors. Students move between 
classrooms carrying violin cases and sheaves of musical scores, their 
dedication to their craft evident in every focused step.

A distinguished **music professor** notices your thoughtful expression as 
you observe the bustling activity.

*"Fascinating place, isn't it? Music and mathematics have always been 
intimate companions. Did you know that some of our most gifted musicians 
are also brilliant mathematicians?"*

He gestures to various students:

**A violinist** studies a Bach invention, her eyes tracking the intricate 
mathematical patterns in the counterpoint.

**A composer** at the piano works out harmonic progressions, applying 
ratios and proportions with the precision of a geometer.

**A music theory student** analyzes the mathematical structure of a fugue, 
finding beauty in its logical architecture.

*"This raises an intriguing logical question: If some musicians possess 
mathematical minds, and all musicians must read sheet music to practice 
their art, what can we conclude about those who read sheet music?"*

---

**NEW CHALLENGE - FIGURE 3:**

Previous syllogisms used different middle term positions:
- **Figure 1** (M-P, S-M): Middle term connects by being predicate then subject  
- **Figure 2** (P-M, S-M): Middle term as predicate in both premises

**Figure 3** introduces yet another pattern (M-P, M-S):
- The middle term is **SUBJECT in BOTH premises**
- This creates unique logical constraints
- **Figure 3 can only prove "some" conclusions, never "all"**""",
            is_start=True
        )
        self.debug("Created node: intro")

        # ---------------------------------------------------------------------
        # MAJOR PREMISE NODE - Some musicians are mathematicians (I proposition)
        # ---------------------------------------------------------------------

        self.nodes["major_premise"] = self.create_node(
            title="The Musical Mathematicians",
            content="""# The Musical Mathematicians

The professor guides you to a display case showcasing famous composer-mathematicians.

*"First, let us establish a remarkable historical fact: the overlap between 
musical and mathematical genius is well-documented."*

He points to portraits and manuscripts:

- **Johann Sebastian Bach**: *"His fugues follow strict mathematical rules. 
  Each voice enters at precise intervals, creating patterns that satisfy 
  both ear and mind."*

- **Leonhard Euler**: *"The great mathematician wrote 'Tentamen novae theoriae musicae' 
  - an attempt to reduce music theory to mathematical principles."*

- **Jean-Philippe Rameau**: *"Composer and music theorist who mathematically 
  derived the principles of harmony from the overtone series."*

*"These are not isolated cases. Throughout history, we find individuals who 
excel in both domains. The pattern-recognition that makes great musicians 
often creates great mathematicians too."*

```
┌─────────────────────────────────────────┐
│           MAJOR PREMISE                 │
│         (I Proposition)                 │
│                                         │
│   "Some musicians are mathematicians"   │
│                                         │
│   Logical form: Some M are P            │
│   - M (Middle term) = Musicians         │
│   - P (Major term) = Mathematicians     │
│                                         │
│   This is an I proposition:             │
│   Particular AFFIRMATIVE                │
│                                         │
│   Musicians ∩ Mathematicians ≠ ∅        │
│                                         │
│       Musicians              Math'ns    │
│   ┌───────────────┐     ┌───────────┐   │
│   │  Performers   │     │  Analysts │   │
│   │  Composers    ╠═════╣ Theorists │   │
│   │  ●═══════════●│ ●●● │●══════════│   │
│   │   Bach ●      │     │  Euler ●  │   │
│   │  ●═══════════●│     │           │   │
│   │  Teachers     ╠═════╣ Logicians │   │
│   │               │     │           │   │
│   └───────────────┘     └───────────┘   │
│                                         │
│   The ● represent musician-mathematicians│
└─────────────────────────────────────────┘
```

*"Do you accept this premise? That some musicians possess mathematical minds?"*

---

**DOMAIN MAPPING:**
- This premise asserts: Some members of Archetype "Musicians" also belong to Archetype "Mathematicians"
- `ArchetypeOverlap(archetype_a="Musicians", archetype_b="Mathematicians", type="partial")`
- The overlap contains historical figures like Bach, Euler, Rameau

**FIGURE 3 PATTERN BEGINS:**
Notice that "Musicians" appears as the SUBJECT of this premise. In Figure 3, 
the middle term will be the subject of BOTH premises."""
        )
        self.debug("Created node: major_premise")

        # ---------------------------------------------------------------------
        # MINOR PREMISE NODE - All musicians read sheet music (A proposition)
        # ---------------------------------------------------------------------

        self.nodes["minor_premise"] = self.create_node(
            title="The Universal Skill",
            content="""# The Universal Skill

The professor now leads you through the practice rooms, where the sound 
of students working through their exercises fills the air.

*"Now observe something fundamental about musical training: every musician, 
without exception, must master the skill of reading sheet music."*

You watch as students of all levels engage with written notation:

- **Beginners** slowly decode simple melodies, finger by finger
- **Intermediate students** sight-read increasingly complex passages
- **Advanced performers** interpret sophisticated scores with fluency
- **Composers** write their own intricate musical ideas in notation

*"From the humblest student to the greatest virtuoso, all musicians share 
this essential skill. You cannot truly be a musician without being able 
to read the language of musical notation."*

```
┌─────────────────────────────────────────┐
│           MINOR PREMISE                 │
│         (A Proposition)                 │
│                                         │
│   "All musicians read sheet music"      │
│                                         │
│   Logical form: All M are S             │
│   - M (Middle term) = Musicians         │
│   - S (Minor term) = Sheet Music Readers│
│                                         │
│   This is an A proposition:             │
│   Universal AFFIRMATIVE                 │
│                                         │
│   Musicians ⊆ {Sheet Music Readers}     │
│                                         │
│   ┌─────────── Sheet Music Readers ─────┐
│   │                                     │
│   │      ┌──── Musicians ────┐          │
│   │      │   All of them     │          │
│   │      │  (Bach, Clara,    │          │
│   │      │   students...)    │          │
│   │      │                   │          │
│   │      └───────────────────┘          │
│   │                                     │
│   │  (Plus non-musician readers)        │
│   └─────────────────────────────────────┘
│                                         │
│   Every musician is inside the larger   │
│   circle of sheet music readers         │
└─────────────────────────────────────────┘
```

*"This skill is the gateway to musical literacy. Notice that 'Musicians' 
again appears as the SUBJECT of our premise."*

*"With these two facts established, what can we conclude about the 
relationship between sheet music readers and mathematicians?"*

---

**DOMAIN MAPPING:**
- This premise asserts: ALL members of Archetype "Musicians" possess Trait "Reads Musical Notation"
- Universal trait possession: Musicians ⊆ {Sheet Music Readers}
- Musicians are entirely contained within the broader category of those who read sheet music

**FIGURE 3 PATTERN COMPLETE:**
The middle term "Musicians" now appears as SUBJECT in BOTH premises:
- Major: Musicians → some are Mathematicians (partial relationship)
- Minor: Musicians → all read Sheet Music (universal relationship)

**LOGICAL STRUCTURE SO FAR:**
- Major (I): Some M are P ✓ (Some musicians are mathematicians)
- Minor (A): All M are S ✓ (All musicians read sheet music)
- Conclusion: ??? (What about sheet music readers and mathematicians?)"""
        )
        self.debug("Created node: minor_premise")

        # ---------------------------------------------------------------------
        # CONCLUSION OPTIONS NODE
        # ---------------------------------------------------------------------

        self.nodes["conclusion_options"] = self.create_node(
            title="The Figure 3 Deduction",
            content="""# The Figure 3 Deduction

The professor pauses thoughtfully, his eyes gleaming with intellectual excitement.

*"Now we reach the heart of Figure 3 reasoning. You have established:*
1. *Some musicians are mathematicians* (partial overlap exists)
2. *All musicians read sheet music* (complete inclusion)

*"The question becomes: what can we validly conclude about those who 
read sheet music and their relationship to mathematics?"*

```
┌─────────────────────────────────────────┐
│         SYLLOGISM STRUCTURE             │
│             (Disamis)                   │
│                                         │
│   Major (I): Some M are P               │
│              (Some musicians are math.) │
│                                         │
│   Minor (A): All M are S                │
│              (All musicians read music) │
│                                         │
│   ════════════════════════════════════  │
│                                         │
│   Conclusion: ???                       │
│                                         │
│   Visual reasoning:                     │
│                                         │
│   ┌──── Sheet Music Readers (S) ──────┐ │
│   │                                   │ │
│   │    ┌──── Musicians (M) ─────┐     │ │
│   │    │                        │     │ │
│   │    │  ┌── Math Musicians ──┐ │     │ │
│   │    │  │ Bach, Euler...    │ │ ←─── These individuals
│   │    │  │ ●●●               │ │      exist!
│   │    │  └───────────────────┘ │     │ │
│   │    │                        │     │ │
│   │    │ (Other musicians)      │     │ │
│   │    └────────────────────────┘     │ │
│   │                                   │ │
│   │  (Non-musician sheet readers)     │ │
│   └───────────────────────────────────┘ │
│                                         │
│   The musician-mathematicians ARE       │
│   also sheet music readers!             │
└─────────────────────────────────────────┘
```

---

**FIGURE 3 INSIGHT:**
The power of Figure 3 lies in **existential reasoning**: when we know some 
Ms are Ps, and ALL Ms are Ss, then those same M-P individuals must also 
be Ss. Therefore, some Ss are Ps.

**CRITICAL CONSTRAINT:**
Figure 3 can ONLY yield particular conclusions! The minor term (Sheet Music 
Readers) is never distributed, so we cannot make universal claims about ALL 
sheet music readers.

**Choose the logical conclusion:**"""
        )
        self.debug("Created node: conclusion_options")

        # ---------------------------------------------------------------------
        # VALID CONCLUSION NODE - Disamis achieved
        # ---------------------------------------------------------------------

        self.nodes["valid_conclusion"] = self.create_node(
            title="Disamis Achieved: Figure 3 Mastery",
            content="""# Disamis Achieved: Figure 3 Mastery

*"Some who read sheet music are mathematicians,"* you conclude thoughtfully.

The professor's face brightens with scholarly delight.

*"Magnificent! You have mastered DISAMIS and unlocked the secrets of Figure 3 reasoning!"*

```
┌─────────────────────────────────────────┐
│           VALID SYLLOGISM               │
│             (Disamis)                   │
│                                         │
│   Some musicians are mathematicians (I) │
│   All musicians read sheet music    (A) │
│   ─────────────────────────────────────  │
│   ∴ Some sheet music readers are    (I) │
│     mathematicians                      │
│                                         │
│   Form: IAI-3 (Disamis)                 │
│   Figure: 3 (M-P, M-S ∴ S-P)            │
│   Mood: IAI                             │
│                                         │
│         VALID ✓                         │
└─────────────────────────────────────────┘
```

*"Observe the elegant logic: The musician-mathematicians like Bach and Euler 
necessarily possess ALL the traits of musicians—including the ability to 
read sheet music. Therefore, within the community of sheet music readers, 
we find these mathematical minds."*

**FIGURE 3 EXPLAINED:**

*"You have discovered Figure 3's unique characteristics:*

**SUBJECT-SUBJECT PATTERN**: The middle term appears as SUBJECT in both 
premises, creating a different reasoning flow from Figures 1 and 2.

**PARTICULAR CONCLUSIONS ONLY**: Figure 3 has a built-in limitation—it 
can never yield universal conclusions (A or E), only particular ones (I or O). 

**WHY THE LIMITATION?** The minor term (Sheet Music Readers) is never distributed 
in Figure 3. To make universal claims about a term, it must be distributed 
somewhere in the premises.

```
    Distribution Analysis:
    ─────────────────────
    Major: Some M are P  (Neither M nor P distributed)
    Minor: All M are S   (M distributed, S not distributed)
    
    Since S is never distributed, conclusions about 
    "ALL Sheet Music Readers" are impossible!
```

**EXISTENTIAL REASONING**: Figure 3 excels at tracking individuals through 
category memberships. The same people who are M-P must also be M-S, 
therefore some S-P.

*"This makes Figure 3 perfect for reasoning about overlapping communities 
and shared characteristics among individuals."*

---

**DOMAIN MAPPING:**
- Conclusion establishes: Some members of "Sheet Music Readers" are also "Mathematicians"
- Specifically: the musician-mathematicians (Bach, Euler, etc.) who combine all three traits
- The reasoning chain: Musical-Mathematical minds → read music → some music readers are mathematical

**DISAMIS IN THE LOGICAL TRADITION:**
- One of the valid Figure 3 forms identified by Aristotle
- Essential for reasoning about individual existence across categories
- Foundation for understanding existential import in logic""",
            is_end=True
        )
        self.debug("Created node: valid_conclusion")

        # ---------------------------------------------------------------------
        # FALLACY NODE: Universal from Particular (Illicit Minor)
        # ---------------------------------------------------------------------

        self.nodes["fallacy_universal"] = self.create_node(
            title="The Universalization Error",
            content="""# The Universalization Error

*"All who read sheet music are mathematicians?"* The professor looks concerned.

*"You've committed the fallacy of ILLICIT MINOR—attempting a universal 
conclusion when Figure 3 cannot support it!"*

```
┌─────────────────────────────────────────┐
│              FALLACY                    │
│            Illicit Minor                │
│                                         │
│   Your conclusion: "ALL sheet music     │
│   readers are mathematicians" (A)       │
│                                         │
│   But the minor term "sheet music       │
│   readers" is NEVER distributed in      │
│   our premises:                         │
│                                         │
│   Major: Some musicians are math'ns     │
│   - "Sheet music readers" not mentioned │
│                                         │
│   Minor: All musicians read sheet music │
│   - "Sheet music readers" is predicate  │
│   - NOT distributed (predicate of A)    │
│                                         │
│   RULE: Cannot make universal claims    │
│   about undistributed terms!            │
└─────────────────────────────────────────┘
```

*"This is Figure 3's fundamental constraint: it can NEVER yield universal 
conclusions because the minor term is structurally undistributed.*

**THE LOGICAL LIMITATION:**

Consider what we actually know:
- **Some** musicians are mathematicians (not all)
- **All** musicians read sheet music
- Therefore: **Some** (not all) sheet music readers are mathematicians

**COUNTER-EXAMPLE:**
What about music teachers who read sheet music but focus on pedagogy rather 
than mathematical theory? What about church organists who read music but 
never study mathematics? Our premises tell us nothing about these individuals!

```
    ┌─────── Sheet Music Readers ──────┐
    │                                  │
    │  ┌─ Musicians ─┐                 │
    │  │ ┌Math Musicians┐ ← These are  │
    │  │ │ ●●●          │   mathematicians
    │  │ └─────────────┘  │             │
    │  │                  │             │
    │  │ (Other musicians)│ ← Unknown   │
    │  └──────────────────┘             │
    │                                   │
    │  Music teachers, students, etc. ← Unknown
    └───────────────────────────────────┘
```

**DOMAIN INSIGHT:**
- Only a subset of musicians have mathematical inclinations
- Many people read sheet music without being mathematicians
- Figure 3 reasoning respects these limitations by yielding only particular conclusions

---

**FIGURE 3 RULE:**
The structure M-P, M-S ∴ S-P can only prove "Some S are P" or "Some S are not P", 
never "All S are P" or "No S are P"."""
        )
        self.debug("Created node: fallacy_universal")

        # ---------------------------------------------------------------------
        # FALLACY NODE: Existential Fallacy
        # ---------------------------------------------------------------------

        self.nodes["fallacy_existential"] = self.create_node(
            title="The Existence Error",
            content="""# The Existence Error

*"No sheet music readers are mathematicians?"* The professor shakes his head.

*"You've committed an EXISTENTIAL FALLACY—denying the very existence that 
our premises establish!"*

```
┌─────────────────────────────────────────┐
│              FALLACY                    │
│          Existential Fallacy            │
│                                         │
│   Your conclusion: "NO sheet music      │
│   readers are mathematicians" (E)       │
│                                         │
│   But our premises ESTABLISH that       │
│   such individuals exist:               │
│                                         │
│   1. Some musicians are mathematicians  │
│   2. All musicians read sheet music     │
│                                         │
│   Therefore: Those musician-            │
│   mathematicians DO read sheet music!   │
│                                         │
│   You cannot conclude that no such      │
│   overlap exists when we've proven      │
│   it DOES exist!                        │
└─────────────────────────────────────────┘
```

*"This violates the very essence of Figure 3 reasoning:*

**THE EXISTENCE CHAIN:**
- We know Bach, Euler, and others are musician-mathematicians (by major premise)
- We know ALL musicians read sheet music (by minor premise)  
- Therefore: Bach and Euler (and others like them) are sheet-music-reading mathematicians

**CONCRETE PROOF:**
Walk into any music conservatory and you'll find composers studying both 
harmonic theory and mathematical ratios, performers analyzing rhythmic 
patterns with mathematical precision, and theorists who are explicitly 
trained in both domains.

```
    Historical Examples:
    ───────────────────
    Bach: Musician ✓ Mathematician ✓ Sheet Music Reader ✓
    Euler: Mathematician ✓ Music Theorist ✓ Notation Reader ✓
    Rameau: Composer ✓ Math Theorist ✓ Score Writer ✓
    
    These individuals prove the overlap exists!
```

**WHY THE NEGATIVE IS IMPOSSIBLE:**
Figure 3 reasoning is fundamentally EXISTENTIAL—it tracks the same individuals 
across different category memberships. When the premises establish existence, 
the conclusion must acknowledge that existence.

---

**DOMAIN INSIGHT:**
The historical and cultural connection between music and mathematics is well-documented. 
Denying this connection contradicts both logical reasoning and empirical evidence."""
        )
        self.debug("Created node: fallacy_existential")

        # ---------------------------------------------------------------------
        # RETRY NODE
        # ---------------------------------------------------------------------

        self.nodes["retry"] = self.create_node(
            title="Reconsider the Musical Logic",
            content="""# Reconsider the Musical Logic

The professor offers an encouraging smile.

*"Figure 3 reasoning requires understanding both its power and its limitations. 
Let's review our musical evidence:*

**Premise 1 (I):** Some musicians are mathematicians
- **Partial overlap**: Historical examples like Bach, Euler, Rameau
- **Existential claim**: These individuals definitely exist

**Premise 2 (A):** All musicians read sheet music
- **Universal requirement**: Every musician must have this skill
- **No exceptions**: From beginners to virtuosos

*"Now, think about those individuals who are BOTH musicians AND mathematicians. 
Since they are musicians, what must also be true about their musical literacy?"*

```
    The Individual Tracking:
    ──────────────────────
    
    Bach: Musician ✓ → Therefore reads sheet music ✓
          Mathematician ✓ → Mathematical mind ✓
          
    So Bach is: Sheet Music Reader ✓ AND Mathematician ✓
    
    Same logic applies to Euler, Rameau, and others...
```

*"The key insight: Figure 3 tracks the SAME INDIVIDUALS through different 
category memberships. We follow musician-mathematicians into the broader 
category of sheet music readers."*

**FIGURE 3 CONSTRAINT REMINDER:**
Since the minor term (Sheet Music Readers) is never distributed, we can only 
make **particular** claims about them, never **universal** ones.

---

**LOGICAL HINT:**
- Subject: Some sheet music readers (the musician-mathematician subset)
- Predicate: Mathematicians
- Relationship: Partial overlap (some, not all)
- Quantity: Particular (because Figure 3 cannot yield universals)

Form: "Some S are P" → Some sheet music readers are mathematicians"""
        )
        self.debug("Created node: retry")

        # ---------------------------------------------------------------------
        # SKIP PREMISES NODE
        # ---------------------------------------------------------------------

        self.nodes["skip_fallacy"] = self.create_node(
            title="The Hasty Assumption",
            content="""# The Hasty Assumption

You begin to draw conclusions about musicians and mathematicians, but the 
professor raises his hand.

*"Wait! We cannot make claims about these relationships without first 
establishing the logical connections systematically."*

```
┌─────────────────────────────────────────┐
│              FALLACY                    │
│       Hasty Generalization              │
│                                         │
│   To determine the relationship between │
│   sheet music readers and               │
│   mathematicians, we must establish:    │
│                                         │
│   1. Is there any connection between    │
│      musicians and mathematics?         │
│      (Historical? Cultural? Cognitive?) │
│                                         │
│   2. What universal skills do all       │
│      musicians possess?                 │
│      (Sheet music reading? Performance?)│
│                                         │
│   Only with these logical foundations   │
│   can we reason about broader           │
│   implications for music literacy       │
│   and mathematical thinking.            │
└─────────────────────────────────────────┘
```

*"The relationship between music and mathematics is profound but requires 
careful logical analysis. We cannot rely on casual observations or cultural 
stereotypes."*

*"Let us begin by examining whether any musicians throughout history have 
demonstrated mathematical abilities..."*

---

**DOMAIN INSIGHT:**
- The music-mathematics connection is well-documented but requires systematic evidence
- Musical training involves pattern recognition, ratio understanding, and logical thinking
- Figure 3 reasoning helps us trace individuals across overlapping intellectual domains

**THE SYSTEMATIC APPROACH:**
1. Establish partial overlap between first two categories (major premise)
2. Establish universal relationship involving the middle term (minor premise)
3. THEN derive what we can conclude about the remaining relationship (conclusion)"""
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
            text="\"Tell me about the connection between musical and mathematical minds.\"",
            order=0,
            sets_state={
                "understands_figure_3_reasoning": False,
                "understands_particular_conclusions_only": False,
                "music_math_connection": False
            }
        ))
        self.debug("Created choice: intro → major_premise")

        self.choices.append(self.create_choice(
            from_node_name="intro",
            to_node_name="skip_fallacy",
            text="\"Obviously musicians and mathematicians are completely different types of people!\"",
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
            text="\"I accept this - the historical examples clearly show some musicians are mathematical.\"",
            order=0,
            sets_state={
                "some_musicians_are_mathematicians": True,
                "syllogism_mood": "I",
                "music_math_connection": True
            }
        ))
        self.debug("Created choice: major_premise → minor_premise")

        # FROM: minor_premise
        self.choices.append(self.create_choice(
            from_node_name="minor_premise",
            to_node_name="conclusion_options", 
            text="\"I understand - all musicians must master musical notation.\"",
            order=0,
            requires_state={"some_musicians_are_mathematicians": True},
            sets_state={
                "all_musicians_read_sheet_music": True,
                "syllogism_mood": "IA",
                "syllogism_figure": "figure_3",
                "understands_figure_3_reasoning": True
            }
        ))
        self.debug("Created choice: minor_premise → conclusion_options")

        # FROM: conclusion_options - VALID conclusion
        self.choices.append(self.create_choice(
            from_node_name="conclusion_options",
            to_node_name="valid_conclusion",
            text="\"Therefore, some who read sheet music are mathematicians.\"",
            order=0,
            requires_state={
                "$and": [
                    {"some_musicians_are_mathematicians": True},
                    {"all_musicians_read_sheet_music": True}
                ]
            },
            sets_state={
                "some_sheet_music_readers_are_mathematicians": True,
                "conclusion_valid": True,
                "syllogism_mood": "IAI",
                "understands_figure_3_constraint": True,
                "understands_particular_conclusions_only": True,
                "understands_existential_import": True,
                "fallacy_committed": "none"
            }
        ))
        self.debug("Created choice: conclusion_options → valid_conclusion (CORRECT)")

        # FALLACY: Universal conclusion
        self.choices.append(self.create_choice(
            from_node_name="conclusion_options",
            to_node_name="fallacy_universal",
            text="\"Therefore, all who read sheet music are mathematicians.\"",
            order=1,
            requires_state={
                "$and": [
                    {"some_musicians_are_mathematicians": True},
                    {"all_musicians_read_sheet_music": True}
                ]
            },
            sets_state={
                "conclusion_valid": False,
                "fallacy_committed": "illicit_minor"
            }
        ))
        self.debug("Created choice: conclusion_options → fallacy_universal")

        # FALLACY: Existential fallacy
        self.choices.append(self.create_choice(
            from_node_name="conclusion_options",
            to_node_name="fallacy_existential",
            text="\"Therefore, no sheet music readers are mathematicians.\"",
            order=2,
            requires_state={
                "$and": [
                    {"some_musicians_are_mathematicians": True},
                    {"all_musicians_read_sheet_music": True}
                ]
            },
            sets_state={
                "conclusion_valid": False,
                "fallacy_committed": "existential_fallacy"
            }
        ))
        self.debug("Created choice: conclusion_options → fallacy_existential")

        # FROM: fallacy nodes to retry
        for fallacy_node in ["fallacy_universal", "fallacy_existential"]:
            self.choices.append(self.create_choice(
                from_node_name=fallacy_node,
                to_node_name="retry",
                text="\"I see my error - let me reconsider Figure 3's constraints.\"",
                order=0,
                sets_state={"fallacy_committed": "none"}
            ))
            self.debug(f"Created choice: {fallacy_node} → retry")

        self.choices.append(self.create_choice(
            from_node_name="skip_fallacy",
            to_node_name="major_premise",
            text="\"You're right - let me examine the evidence for musical-mathematical connections.\"",
            order=0,
            sets_state={"fallacy_committed": "none"}
        ))
        self.debug("Created choice: skip_fallacy → major_premise")

        # FROM: retry back to conclusion
        self.choices.append(self.create_choice(
            from_node_name="retry",
            to_node_name="conclusion_options",
            text="\"Now I understand Figure 3 reasoning - let me draw the correct particular conclusion.\"",
            order=0,
            requires_state={
                "$and": [
                    {"some_musicians_are_mathematicians": True},
                    {"all_musicians_read_sheet_music": True}
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
        description="Create a Carroll Disamis syllogism demonstration story"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--cleanup", action="store_true", help="Delete created story")
    args = parser.parse_args()

    test_results["start_time"] = datetime.now().isoformat()

    print("\n" + "=" * 70)
    print("  CARROLL DISAMIS STORY BUILDER")
    print("  Creating a demonstration of Figure 3 reasoning (IAI-3)")
    print("=" * 70)

    try:
        # Get authenticated session
        session = get_authenticated_session()
        print(f"\n✓ Authenticated successfully")

        # Create the story builder
        builder = DisamistoryBuilder(session, verbose=args.verbose)

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
        print("  │   ├─→ major_premise (I: Some musicians are mathematicians)")
        print("  │   │     └─→ minor_premise (A: All musicians read sheet music)")
        print("  │   │           └─→ conclusion_options")
        print("  │   │                 ├─→ valid_conclusion (I: Some sheet music readers are mathematicians) ✓")
        print("  │   │                 ├─→ fallacy_universal (illicit minor) → retry")
        print("  │   │                 └─→ fallacy_existential → retry")
        print("  │   └─→ skip_fallacy → major_premise")
        print("  └─────────────────────────────────────────────")

        print(f"\n  NEW CONCEPT INTRODUCED:")
        print(f"  🆕 Figure 3 reasoning: M-P, M-S ∴ S-P")
        print(f"  🆕 Middle term as subject in both premises")
        print(f"  🆕 Figure 3 constraint: only particular conclusions possible")
        print(f"  🆕 Existential reasoning across category memberships")

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