#!/usr/bin/env python3
"""
Carroll Symbolic Logic Story: Darii Syllogism (AII-1)
=====================================================

This script creates a complete interactive story demonstrating the Darii
syllogism, which introduces PARTICULAR PROPOSITIONS - the "I" statement.

SYLLOGISM STRUCTURE (Darii - AII-1):
    Major Premise (A): All philosophers seek wisdom     (All M are P)
    Minor Premise (I): Some Greeks are philosophers     (Some S are M)
    Conclusion (I):    Some Greeks seek wisdom          (Some S are P)

NEW CONCEPT - THE I PROPOSITION (PARTICULAR AFFIRMATIVE):
=========================================================

The I proposition "Some S are P" is fundamentally different from universals:

1. EXISTENTIAL CLAIM: It asserts that AT LEAST ONE member of S is also in P
   - "Some Greeks are philosophers" = There exists at least one Greek philosopher

2. NOT DISTRIBUTED: Neither the subject nor predicate is distributed
   - We're NOT making claims about ALL Greeks
   - We're NOT making claims about ALL philosophers
   - We're only claiming an OVERLAP exists

3. QUANTITY vs QUALITY:
   - Quantity: PARTICULAR (some) vs Universal (all/none)
   - Quality: AFFIRMATIVE (are) vs Negative (are not)

   Type    Quantity    Quality     Form           Example
   ────────────────────────────────────────────────────────
   A       Universal   Affirmative All S are P    All men are mortal
   E       Universal   Negative    No S are P     No reptiles are mammals
   I       Particular  Affirmative Some S are P   Some Greeks are philosophers  ← NEW
   O       Particular  Negative    Some S aren't  Some animals aren't mammals

4. VISUAL REPRESENTATION:

   A proposition (All M are P):        I proposition (Some S are M):

   ┌──────── P ────────┐               ┌──── S ────┐  ┌──── M ────┐
   │    ┌─── M ───┐    │               │           │  │           │
   │    │         │    │               │     ╔═════╪══╪═════╗     │
   │    │         │    │               │     ║  ●  │  │     ║     │
   │    └─────────┘    │               │     ╚═════╪══╪═════╝     │
   └───────────────────┘               └───────────┘  └───────────┘
   M entirely within P                 Overlap region contains at least one •


WHY DARII IS VALID:
===================

The middle term (M = Philosophers) connects the premises:

1. All M are P → Every philosopher is in the "wisdom-seekers" set
2. Some S are M → At least one Greek is in the "philosophers" set

Since that Greek philosopher is in M, and ALL of M is in P,
that Greek must also be in P (wisdom-seekers).

    ┌─────────── Wisdom-Seekers (P) ───────────┐
    │                                          │
    │     ┌──── Philosophers (M) ────┐         │
    │     │                          │         │
    │     │    ┌── Greeks (S) ──┐    │         │
    │     │    │                │    │         │
    │     │    │    Socrates ●  │    │         │
    │     │    │    Plato ●     │    │         │
    │     │    └────────────────┘    │         │
    │     │                          │         │
    │     └──────────────────────────┘         │
    └──────────────────────────────────────────┘

    These Greek philosophers (●) are necessarily wisdom-seekers!


CRITICAL DISTINCTION - PARTICULAR CONCLUSIONS:
==============================================

The conclusion MUST be particular (I), not universal (A):

VALID:   "Some Greeks seek wisdom" (I) ✓
         - We only know about Greeks who ARE philosophers
         - We know nothing about Greeks who aren't philosophers

INVALID: "All Greeks seek wisdom" (A) ✗
         - This would require the minor premise to be universal
         - "Some Greeks are philosophers" doesn't tell us about ALL Greeks
         - A Greek who isn't a philosopher might not seek wisdom


MAPPING TO DOMAIN MODEL:
========================

Archetype: Philosophers (Middle Term - M)
- Description: Those who love and pursue wisdom through reason
- Represents the "philosophical class" in ancient Greek thought
- Fully contained within Wisdom-Seekers (by major premise)

Archetype: Wisdom-Seekers (Major Term - P)
- Description: Those who actively pursue knowledge and understanding
- Broader category containing philosophers and others
- The predicate of both premises and conclusion

Archetype: Greeks (Minor Term - S)
- Description: People of ancient Greece
- Contains both philosophers and non-philosophers
- Only SOME Greeks (the philosophers) are asserted to seek wisdom

Trait: "Loves Wisdom" (Philosophical Disposition)
- Defines the philosophical character
- Greek "philosophia" = love of wisdom

Trait: "Pursues Knowledge" (Intellectual Pursuit)
- Broader than philosophy
- Shared by scientists, scholars, etc.

Persona Examples:
- Socrates: Greek + Philosopher → necessarily seeks wisdom
- Plato: Greek + Philosopher → necessarily seeks wisdom
- Generic Athenian: Greek but status unknown → conclusion doesn't apply


FALLACIES TO EXPLORE:
=====================

1. ILLICIT MAJOR (drawing universal from particular):
   Claiming "ALL Greeks seek wisdom"
   - Violates: Can't universalize from particular premises
   - The minor premise only tells us about SOME Greeks

2. UNDISTRIBUTED MIDDLE:
   Claiming "Some Greeks are wise, Some philosophers are Greek,
            therefore some Greeks are philosophers"
   - Violates: Middle term must be distributed at least once
   - In AII-1, the major premise distributes M (All M are P)

3. EXISTENTIAL FALLACY:
   Assuming particulars imply universals
   - "Some Greeks are philosophers" doesn't mean "All Greeks are philosophers"

4. ILLICIT CONVERSION:
   Converting "Some S are M" to "Some M are S" is valid, BUT
   Converting "All M are P" to "All P are M" is NOT valid
   - Not all wisdom-seekers are philosophers!


Usage:
    python test_carroll_darii_story.py
    python test_carroll_darii_story.py --verbose
    python test_carroll_darii_story.py --cleanup  # Delete created story
"""

import json
import sys
import argparse
import requests
from pathlib import Path

# Import auth helper
sys.path.append(str(Path(__file__).parent))
from auth_helper import get_authenticated_session

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
RESULTS_FILE = "test_results_carroll_darii.json"

# Test results tracking
test_results = {
    "test_suite": "Carroll Darii Story (AII-1)",
    "start_time": None,
    "end_time": None,
    "story_id": None,
    "node_ids": {},
    "choice_ids": {},
    "state_variable_ids": {},
    "success": False,
    "errors": []
}


class DariiStoryBuilder:
    """Builds a Darii syllogism story demonstrating particular propositions."""

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

    def create_choice(self, from_node_id: str, to_node_id: str, text: str,
                      requires_state: dict = None, sets_state: dict = None,
                      order: int = 0) -> dict:
        payload = {
            "from_node_id": from_node_id,
            "to_node_id": to_node_id,
            "text": text,
            "order": order
        }
        if requires_state:
            payload["requires_state"] = requires_state
        if sets_state:
            payload["sets_state"] = sets_state

        response = self.session.post(f"{BASE_URL}/node-choices", json=payload)
        if response.status_code != 200:
            raise Exception(f"Failed to create choice '{text}': {response.text} with payload {payload}")
        return response.json()

    # =========================================================================
    # Story Building
    # =========================================================================

    def build_story(self) -> bool:
        """Build the complete Darii syllogism story."""

        # =====================================================================
        # STEP 1: CREATE THE STORY
        # =====================================================================
        self.log("\n📖 Creating story...")

        story = self.create_story(
            title="The Wisdom of the Greeks: A Study in Particulars",
            description="""Darii syllogism (AII-1) - introducing PARTICULAR propositions.

STRUCTURE:
- Major (A): All philosophers seek wisdom
- Minor (I): Some Greeks are philosophers
- Conclusion (I): Some Greeks seek wisdom

THE I PROPOSITION: "Some X are Y" asserts EXISTENCE of overlap - at least one X is Y.
Neither term is distributed (we claim nothing about ALL members).

The conclusion must be PARTICULAR - we only know about Greeks who ARE philosophers."""
        )
        self.story_id = story["id"]
        test_results["story_id"] = self.story_id
        self.log(f"  Created story: {self.story_id}")

        # =====================================================================
        # STEP 2: DEFINE STATE SCHEMA
        # =====================================================================
        self.log("\n📋 Creating state schema...")

        # ---------------------------------------------------------------------
        # Premise tracking - note the particular proposition
        # ---------------------------------------------------------------------

        self.state_vars["major_premise"] = self.create_state_variable(
            key="all_philosophers_seek_wisdom",
            value_type="boolean",
            default_value=False,
            category="premises",
            description="Major premise (A): All philosophers seek wisdom - universal affirmative"
        )

        self.state_vars["minor_premise"] = self.create_state_variable(
            key="some_greeks_are_philosophers",
            value_type="boolean",
            default_value=False,
            category="premises",
            description="Minor premise (I): Some Greeks are philosophers - PARTICULAR affirmative"
        )

        # ---------------------------------------------------------------------
        # Proposition type understanding
        # ---------------------------------------------------------------------

        self.state_vars["understands_particular"] = self.create_state_variable(
            key="understands_particular_proposition",
            value_type="boolean",
            default_value=False,
            category="understanding",
            description="Player understands 'some' (I proposition) vs 'all' (A proposition)"
        )

        self.state_vars["understands_distribution"] = self.create_state_variable(
            key="understands_distribution",
            value_type="boolean",
            default_value=False,
            category="understanding",
            description="Player understands that I propositions don't distribute either term"
        )

        # ---------------------------------------------------------------------
        # Syllogism structure tracking (Figure 1)
        # ---------------------------------------------------------------------

        self.state_vars["syllogism_figure"] = self.create_state_variable(
            key="syllogism_figure",
            value_type="enum",
            default_value="unknown",
            enum_values=["unknown", "figure_1", "figure_2", "figure_3", "figure_4"],
            category="structure",
            description="Figure determined by position of middle term (M-P, S-M = Figure 1)"
        )

        self.state_vars["syllogism_mood"] = self.create_state_variable(
            key="syllogism_mood",
            value_type="enum",
            default_value="unknown",
            enum_values=["unknown", "AII", "AAA", "EAE", "AEE", "other"],
            category="structure",
            description="Mood determined by proposition types (A-I-I = Darii)"
        )

        # ---------------------------------------------------------------------
        # Conclusion tracking
        # ---------------------------------------------------------------------

        self.state_vars["valid_conclusion"] = self.create_state_variable(
            key="valid_conclusion_reached",
            value_type="boolean",
            default_value=False,
            category="conclusions",
            description="Player correctly concluded 'Some Greeks seek wisdom' (I proposition)"
        )

        self.state_vars["attempted_universal"] = self.create_state_variable(
            key="attempted_universal_conclusion",
            value_type="boolean",
            default_value=False,
            category="fallacies",
            description="Player incorrectly tried 'All Greeks seek wisdom' (illicit major)"
        )

        self.state_vars["fallacy_count"] = self.create_state_variable(
            key="particular_fallacy_count",
            value_type="number",
            default_value=0,
            category="fallacies",
            description="Number of fallacies committed related to particular/universal confusion"
        )

        # ---------------------------------------------------------------------
        # Learning progress
        # ---------------------------------------------------------------------

        self.state_vars["examples_seen"] = self.create_state_variable(
            key="greek_philosopher_examples",
            value_type="number",
            default_value=0,
            category="progress",
            description="Number of Greek philosopher examples encountered (Socrates, Plato, etc.)"
        )

        self.state_vars["completed"] = self.create_state_variable(
            key="story_completed",
            value_type="boolean",
            default_value=False,
            category="progress",
            description="Story completed with valid syllogistic reasoning"
        )

        test_results["state_variable_ids"] = {
            k: v["id"] for k, v in self.state_vars.items()
        }
        self.log(f"  Created {len(self.state_vars)} state variables")

        # =====================================================================
        # STEP 3: CREATE STORY NODES
        # =====================================================================
        self.log("\n📝 Creating story nodes...")

        # ---------------------------------------------------------------------
        # Node 1: Introduction - The Question of Greek Wisdom
        # ---------------------------------------------------------------------
        self.nodes["intro"] = self.create_node(
            title="The Question of Greek Wisdom",
            content="""# The Academy's Inquiry

You stand in the groves of the Academy, where Plato once taught.
A visiting scholar poses a question that has puzzled many:

**"Do the Greeks seek wisdom?"**

The question seems simple, but the answer requires careful logical analysis.
We cannot simply observe every Greek who ever lived. Instead, we must
reason from what we KNOW to what we can CONCLUDE.

You recall two established truths:

1. **All philosophers seek wisdom** - This is the very definition of
   philosophy: the love (philo-) of wisdom (sophia).

2. **Some Greeks are philosophers** - History attests to this: Socrates,
   Plato, Aristotle, and others devoted their lives to philosophical inquiry.

From these premises, what can we logically conclude about Greeks and wisdom?

*This introduces a new type of proposition: the PARTICULAR statement "Some X are Y"*
""",
            is_start=True
        )

        # ---------------------------------------------------------------------
        # Node 2: Major Premise - All Philosophers Seek Wisdom
        # ---------------------------------------------------------------------
        self.nodes["major_premise"] = self.create_node(
            title="The Nature of Philosophy",
            content="""# Major Premise: All Philosophers Seek Wisdom

**"All philosophers seek wisdom"** (A proposition: All M are P)

This is a **UNIVERSAL AFFIRMATIVE** - it makes a claim about EVERY member
of a class:

```
┌─────────── Wisdom-Seekers ───────────┐
│                                      │
│     ┌──── Philosophers ────┐         │
│     │   Socrates           │         │
│     │   Plato              │         │
│     │   Aristotle          │         │
│     │   Confucius          │         │
│     │   ...every one       │         │
│     └──────────────────────┘         │
│                                      │
│   (Scientists, scholars, etc.)       │
└──────────────────────────────────────┘
```

The term "philosopher" is **DISTRIBUTED** - we assert something about
ALL philosophers without exception.

**Why is this true?** By definition! The Greek word "philosophia" means
"love of wisdom." One cannot be a philosopher without seeking wisdom.

This premise alone tells us nothing about Greeks specifically...
"""
        )

        # ---------------------------------------------------------------------
        # Node 3: Minor Premise - Some Greeks Are Philosophers (KEY NODE)
        # ---------------------------------------------------------------------
        self.nodes["minor_premise"] = self.create_node(
            title="The Particular Proposition",
            content="""# Minor Premise: Some Greeks Are Philosophers

**"Some Greeks are philosophers"** (I proposition: Some S are M)

⚠️ **NEW CONCEPT: THE PARTICULAR PROPOSITION**

Unlike "All X are Y" which covers every member, "Some X are Y" only claims
that **at least one** member of X is also in Y.

```
        Greeks                    Philosophers
    ┌───────────────┐         ┌───────────────┐
    │               │         │               │
    │  Farmers      │         │    Lao Tzu    │
    │  Soldiers     ╠═════════╣   Confucius   │
    │  ══════════●  │ overlap │ ●═══════════  │
    │   Socrates ●  │  zone   │ ●  Plato      │
    │  ══════════●  │         │ ●═══════════  │
    │  Merchants    ╠═════════╣   Buddha      │
    │  Artists      │         │               │
    │               │         │               │
    └───────────────┘         └───────────────┘

    The ● symbols represent Greek philosophers
    (individuals who are in BOTH sets)
```

**Critical Understanding:**

1. **"Some" means ≥ 1**: At least one Greek is a philosopher
2. **NOT distributed**: We claim nothing about ALL Greeks
3. **NOT distributed**: We claim nothing about ALL philosophers
4. **Existential**: We assert these individuals EXIST

We know Socrates, Plato, and Aristotle were Greeks AND philosophers.
The overlap is historically verified.

What can we conclude from our two premises?
"""
        )

        # ---------------------------------------------------------------------
        # Node 4: Conclusion Options - The Critical Choice
        # ---------------------------------------------------------------------
        self.nodes["conclusion_options"] = self.create_node(
            title="Drawing the Conclusion",
            content="""# What Follows Logically?

We have established:
- **Major**: All philosophers seek wisdom (A: All M are P)
- **Minor**: Some Greeks are philosophers (I: Some S are M)

```
┌─────────── Wisdom-Seekers (P) ───────────┐
│                                          │
│     ┌──── Philosophers (M) ────┐         │
│     │                          │         │
│     │   ┌─ Greeks (S) ─┐       │         │
│     │   │   ●●●        │       │         │
│     │   │ (Socrates,   │       │         │
│     │   │  Plato...)   │       │         │
│     │   └──────────────┘       │         │
│     │                          │         │
│     └──────────────────────────┘         │
│                                          │
└──────────────────────────────────────────┘
```

The Greek philosophers (●) are inside Philosophers,
which is entirely inside Wisdom-Seekers.

**Therefore, those Greek philosophers must also be wisdom-seekers!**

But how should we phrase this conclusion?

Choose the logically valid conclusion:
"""
        )

        # ---------------------------------------------------------------------
        # Node 5: Valid Conclusion - Some Greeks Seek Wisdom
        # ---------------------------------------------------------------------
        self.nodes["valid_conclusion"] = self.create_node(
            title="Valid Conclusion: Some Greeks Seek Wisdom",
            content="""# ✓ Correct: "Some Greeks seek wisdom"

**Conclusion (I proposition): Some Greeks seek wisdom** (Some S are P)

This is the ONLY valid conclusion, and it must be PARTICULAR (I), not
universal (A).

**Why "Some" and not "All"?**

```
The Logic Chain:
────────────────
1. ALL philosophers seek wisdom     → Every philosopher is in P
2. SOME Greeks are philosophers     → At least one Greek is in M
3. ∴ SOME Greeks seek wisdom        → Those Greeks (in M) are in P
         │
         └── We can ONLY conclude about Greeks who ARE philosophers!
```

**What about other Greeks?**

```
    ┌────────────── Greeks ──────────────┐
    │                                    │
    │   ┌─ Greek Philosophers ─┐         │
    │   │   Socrates ✓         │         │
    │   │   Plato ✓            │ → These seek wisdom (proven)
    │   │   Aristotle ✓        │
    │   └──────────────────────┘         │
    │                                    │
    │   Other Greeks:                    │
    │   • Greek soldiers        ?        │
    │   • Greek farmers         ? → Unknown! Our premises say nothing
    │   • Greek merchants       ?    about non-philosopher Greeks
    │                                    │
    └────────────────────────────────────┘
```

**The Darii Pattern (AII-1):**
- Major (A): Universal about the middle term
- Minor (I): Particular connecting minor to middle
- Conclusion (I): Particular connecting minor to major

This is one of the 24 valid syllogistic forms identified by Aristotle!

You have successfully navigated particular propositions and drawn the
only valid conclusion from these premises.
""",
            is_end=True
        )

        # ---------------------------------------------------------------------
        # Node 6: Fallacy - Universal Conclusion (Illicit Major)
        # ---------------------------------------------------------------------
        self.nodes["fallacy_universal"] = self.create_node(
            title="Fallacy: Illicit Major",
            content="""# ✗ Fallacy: "All Greeks seek wisdom"

You attempted a **UNIVERSAL** conclusion from a **PARTICULAR** premise.

**Why this fails:**

```
Your claim: "ALL Greeks seek wisdom"
            ↑↑↑
            This requires information about EVERY Greek

But your premise only said: "SOME Greeks are philosophers"
                             ↑↑↑↑
                             This only tells us about SOME Greeks
```

**The Illicit Major Fallacy:**

You've tried to **extend** the conclusion beyond what the premises support:

```
    ┌────────────── Greeks ──────────────┐
    │                                    │
    │   ┌─ Philosophers ─┐               │
    │   │   ✓ ✓ ✓        │ ← We know these seek wisdom
    │   └────────────────┘               │
    │                                    │
    │   ? ? ? ? ? ? ?                    │
    │   ↑                                │
    │   What about these Greeks?         │
    │   The premises tell us NOTHING!    │
    └────────────────────────────────────┘
```

**Counter-example:**
- Premise: Some Greeks are philosophers
- Premise: All philosophers seek wisdom
- Invalid: ALL Greeks seek wisdom

But what about a Greek soldier who never studied philosophy?
Our premises don't guarantee he seeks wisdom!

**Remember:** A particular premise (I or O) can only yield a
particular conclusion (I or O), never a universal (A or E).
"""
        )

        # ---------------------------------------------------------------------
        # Node 7: Fallacy - Negative Conclusion (Quality Error)
        # ---------------------------------------------------------------------
        self.nodes["fallacy_negative"] = self.create_node(
            title="Fallacy: Drawing Negative from Affirmatives",
            content="""# ✗ Fallacy: "No Greeks seek wisdom" or "Some Greeks don't..."

You attempted a **NEGATIVE** conclusion from **AFFIRMATIVE** premises.

**Why this fails:**

```
Premise 1: All philosophers seek wisdom     (AFFIRMATIVE)
Premise 2: Some Greeks are philosophers     (AFFIRMATIVE)
                                            ───────────────
Your claim: Negative conclusion?            IMPOSSIBLE!
```

**The Rule:** From two affirmative premises, only an affirmative
conclusion can follow.

```
Both premises establish CONNECTIONS:
• Philosophers → Wisdom-seekers  (connected)
• Greeks → Philosophers          (some connected)

There is NO premise establishing DISCONNECTION!
```

**Think of it this way:**

```
    A ── connects to ── B
    C ── connects to ── A (some)

    ∴ C ── connects to ── B (those same some)

    You CANNOT conclude: C ── disconnected from ── B
```

The affirmative premises create a chain of connection.
To conclude disconnection, you would need a negative premise.

**Valid negative conclusions require negative premises:**
- E proposition: No X are Y
- O proposition: Some X are not Y

Return and choose the valid affirmative, particular conclusion.
"""
        )

        # ---------------------------------------------------------------------
        # Node 8: Fallacy - Existential Confusion
        # ---------------------------------------------------------------------
        self.nodes["fallacy_existential"] = self.create_node(
            title="Fallacy: Existential Confusion",
            content="""# ✗ Fallacy: Confusing Existence and Universality

You've made an error related to **EXISTENTIAL IMPORT**.

**The Particular Proposition's Meaning:**

"Some Greeks are philosophers" asserts:
- **There EXISTS** at least one Greek who is a philosopher ✓
- **NOT** that "Greek" and "philosopher" are equivalent
- **NOT** that most/many/majority are philosophers
- **NOT** that all Greeks have the potential to be philosophers

```
"Some" in logic:      "Some" in everyday speech:
─────────────────     ──────────────────────────
≥ 1 (at least one)    Often implies "a notable
                      portion" or "several"

Precise: ∃x(Greek(x) ∧ Philosopher(x))
         "There exists an x such that x is Greek and x is a philosopher"
```

**Common Confusions:**

1. **"Some" → "Most"**: Logical "some" doesn't imply frequency
2. **"Some" → "Any"**: Not the same as "any given Greek might be..."
3. **"Some" → "Typical"**: Not making claims about typical Greeks

**The Valid Reasoning:**

```
We know ∃ Greek philosophers (Socrates, Plato, Aristotle)
                  ↓
Those specific individuals seek wisdom (by major premise)
                  ↓
∴ ∃ Greeks who seek wisdom (those same individuals)
```

We're tracking the SAME individuals through the syllogism,
not making probability claims about random Greeks.
"""
        )

        # ---------------------------------------------------------------------
        # Node 9: Retry Node
        # ---------------------------------------------------------------------
        self.nodes["retry"] = self.create_node(
            title="Return to the Argument",
            content="""# Consider the Argument Again

The error has been explained. Let's return to the logical choice.

**Remember the premises:**
1. **All** philosophers seek wisdom (universal about philosophers)
2. **Some** Greeks are philosophers (particular about Greeks)

**Key insight:** The conclusion must be **particular** (some), not
**universal** (all), because our knowledge of Greeks is limited to
those who are philosophers.

We can only conclude about the Greeks we KNOW are philosophers.

Return to make the valid inference.
"""
        )

        # ---------------------------------------------------------------------
        # Node 10: Deep Dive - Understanding Distribution
        # ---------------------------------------------------------------------
        self.nodes["distribution_explained"] = self.create_node(
            title="Understanding Distribution",
            content="""# Distribution in Syllogistic Logic

**Distribution** = whether a term refers to ALL members of its class

**A proposition: "All M are P"**
```
"All philosophers seek wisdom"
     ↑                   ↑
     M is DISTRIBUTED    P is NOT distributed
     (all philosophers)  (not all wisdom-seekers)
```

**I proposition: "Some S are M"**
```
"Some Greeks are philosophers"
      ↑                  ↑
      S is NOT           M is NOT distributed
      distributed        (not all philosophers)
      (not all Greeks)
```

**Why does distribution matter?**

To validly conclude something about ALL of a term, that term must
be distributed in at least one premise.

```
Our syllogism:
─────────────
Major: All [M]+ are P        M distributed, P not distributed
Minor: Some S are [M]-       Neither S nor M distributed here
─────────────────────────────────────────────────────────────
Valid: Some S are P          ✓ S stays undistributed (some)
                             ✓ P stays undistributed

Invalid: All S are P         ✗ S was never distributed!
                               Can't universalize about S
```

This is why we can only conclude "SOME Greeks seek wisdom" -
the term "Greeks" was never distributed in any premise.
"""
        )

        test_results["node_ids"] = {k: v["id"] for k, v in self.nodes.items()}
        self.log(f"  Created {len(self.nodes)} nodes")

        # =====================================================================
        # STEP 4: CREATE CHOICES (EDGES)
        # =====================================================================
        self.log("\n🔀 Creating choices...")

        self.log(f" intro then id {(self.nodes["intro"]["id"])} nodes")
        self.log(f"major premise then id {(self.nodes["major_premise"]["id"])} nodes")

        # From intro to major premise
        self.choices.append(self.create_choice(
            from_node_id=self.nodes["intro"]["id"],
            to_node_id=self.nodes["major_premise"]["id"],
            text="Begin with the major (first) premise",
            order=0
        ))

        # Option to skip to distribution explanation
        self.choices.append(self.create_choice(
            from_node_id=self.nodes["intro"]["id"],
            to_node_id=self.nodes["distribution_explained"]["id"],
            text="First, explain 'distribution' in logic",
            order=1
        ))

        # From distribution explanation back to major premise
        self.choices.append(self.create_choice(
            from_node_id=self.nodes["distribution_explained"]["id"],
            to_node_id=self.nodes["major_premise"]["id"],
            text="Now examine the premises",
            sets_state={
                "$set": {"understands_distribution": True}
            },
            order=0
        ))

        # From major premise to minor premise
        self.choices.append(self.create_choice(
            from_node_id=self.nodes["major_premise"]["id"],
            to_node_id=self.nodes["minor_premise"]["id"],
            text="Accept this premise and continue",
            sets_state={
                "$set": {
                    "all_philosophers_seek_wisdom": True,
                    "syllogism_mood": "AII"
                }
            },
            order=0
        ))

        # From minor premise to conclusion options
        self.choices.append(self.create_choice(
            from_node_id=self.nodes["minor_premise"]["id"],
            to_node_id=self.nodes["conclusion_options"]["id"],
            text="I understand - proceed to draw a conclusion",
            sets_state={
                "$set": {
                    "some_greeks_are_philosophers": True,
                    "understands_particular_proposition": True,
                    "syllogism_figure": "figure_1"
                },
                "$inc": {"greek_philosopher_examples": 3}  # Socrates, Plato, Aristotle mentioned
            },
            order=0
        ))

        # From conclusion options - VALID choice
        self.choices.append(self.create_choice(
            from_node_id=self.nodes["conclusion_options"]["id"],
            to_node_id=self.nodes["valid_conclusion"]["id"],
            text="\"Some Greeks seek wisdom\" (particular affirmative)",
            requires_state={
                "$and": [
                    {"all_philosophers_seek_wisdom": {"$eq": True}},
                    {"some_greeks_are_philosophers": {"$eq": True}}
                ]
            },
            sets_state={
                "$set": {
                    "valid_conclusion_reached": True,
                    "story_completed": True
                }
            },
            order=0
        ))

        # From conclusion options - FALLACY: Universal conclusion
        self.choices.append(self.create_choice(
            from_node_id=self.nodes["conclusion_options"]["id"],
            to_node_id=self.nodes["fallacy_universal"]["id"],
            text="\"All Greeks seek wisdom\" (universal affirmative)",
            sets_state={
                "$set": {"attempted_universal_conclusion": True},
                "$inc": {"particular_fallacy_count": 1}
            },
            order=1
        ))

        # From conclusion options - FALLACY: Negative conclusion
        self.choices.append(self.create_choice(
            from_node_id=self.nodes["conclusion_options"]["id"],
            to_node_id=self.nodes["fallacy_negative"]["id"],
            text="\"No Greeks seek wisdom\" (negative conclusion)",
            sets_state={
                "$inc": {"particular_fallacy_count": 1}
            },
            order=2
        ))

        # From conclusion options - FALLACY: Existential confusion
        self.choices.append(self.create_choice(
            from_node_id=self.nodes["conclusion_options"]["id"],
            to_node_id=self.nodes["fallacy_existential"]["id"],
            text="\"Greeks and philosophers are the same\"",
            sets_state={
                "$inc": {"particular_fallacy_count": 1}
            },
            order=3
        ))

        # From fallacy nodes back to retry
        for fallacy_key in ["fallacy_universal", "fallacy_negative", "fallacy_existential"]:
            self.choices.append(self.create_choice(
                from_node_id=self.nodes[fallacy_key]["id"],
                to_node_id=self.nodes["retry"]["id"],
                text="I understand the error",
                order=0
            ))

        # From retry back to conclusion options
        self.choices.append(self.create_choice(
            from_node_id=self.nodes["retry"]["id"],
            to_node_id=self.nodes["conclusion_options"]["id"],
            text="Try again",
            order=0
        ))

        test_results["choice_ids"] = [c["id"] for c in self.choices]
        self.log(f"  Created {len(self.choices)} choices")

        # =====================================================================
        # STEP 5: VALIDATE STATE SCHEMA
        # =====================================================================
        self.log("\n✅ Validating state schema...")

        response = self.session.get(
            f"{BASE_URL}/stories/{self.story_id}/versions/1/state-schema/validate"
        )
        if response.status_code == 200:
            validation = response.json()
            if validation.get("is_valid"):
                self.log("  Schema is VALID - all variables defined!")
            else:
                self.log(f"  Schema INVALID: {validation.get('undefined_variables')}")
                return False
        else:
            self.log(f"  Validation request failed: {response.text}")
            return False

        return True


def authenticate(session: requests.Session) -> bool:
    """Authenticate and get access token."""
    print("🔐 authenticating...")

    session = get_authenticated_session()
    response = session.post(
    print("\n✓ Authenticated successfully")
    )

    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

    token_data = response.json()
    access_token = token_data.get("access_token")

    if not access_token:
        print("❌ No access token in response")
        return False

    session.headers.update({"Authorization": f"Bearer {access_token}"})
    print("✅ Login successful! Token obtained.")
    return True


def cleanup_story(session: requests.Session, story_id: str) -> bool:
    """Delete a story and all associated data."""
    print(f"\n🗑️  Deleting story {story_id}...")

    response = session.delete(f"{BASE_URL}/stories/{story_id}")

    if response.status_code == 200:
        print("✅ Story deleted successfully")
        return True
    else:
        print(f"❌ Failed to delete story: {response.text}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Carroll Darii Syllogism Story Builder")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--cleanup", type=str, help="Delete story with given ID")
    args = parser.parse_args()

    print("=" * 70)
    print("  CARROLL DARII STORY BUILDER")
    print("  Demonstrating particular propositions (AII-1)")
    print("=" * 70)

    session = get_authenticated_session()

    print("\n✓ Authenticated successfully")

    # Handle cleanup mode
    if args.cleanup:
        success = cleanup_story(session, args.cleanup)
        sys.exit(0 if success else 1)

    # Build the story
    builder = DariiStoryBuilder(session, verbose=args.verbose)

    try:
        is_valid = builder.build_story()
        test_results["success"] = is_valid

    except Exception as e:
        print(f"\n❌ Error: {e}")
        test_results["errors"].append(str(e))
        test_results["success"] = False

    # Print summary
    print("\n" + "=" * 70)
    print("  STORY CREATION COMPLETE")
    print("=" * 70)
    print(f"""
  Story ID: {test_results['story_id']}
  Nodes created: {len(test_results['node_ids'])}
  Choices created: {len(test_results['choice_ids'])}
  State variables: {len(test_results['state_variable_ids'])}
  Schema valid: {'Yes' if test_results['success'] else 'No'}

  Node Structure:
  ┌─ intro (START)
  │   ├─→ major_premise (A: All philosophers seek wisdom)
  │   │     └─→ minor_premise (I: Some Greeks are philosophers)
  │   │           └─→ conclusion_options
  │   │                 ├─→ valid_conclusion (I: Some Greeks seek wisdom) ✓
  │   │                 ├─→ fallacy_universal (illicit major) → retry
  │   │                 ├─→ fallacy_negative (quality error) → retry
  │   │                 └─→ fallacy_existential → retry
  │   └─→ distribution_explained → major_premise
  └─────────────────────────────────────────────

  Play the story at:
  http://localhost:5173/stories/{test_results['story_id']}/play

  Results saved to: test_results_carroll_darii.json
""")
    print("=" * 70)

    # Save results
    results_path = Path(__file__).parent / "test_results_carroll_darii.json"
    with open(results_path, "w") as f:
        json.dump(test_results, f, indent=2, default=str)


if __name__ == "__main__":
    main()
