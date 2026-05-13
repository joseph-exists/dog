# Lewis Carroll Symbolic Logic Implementation Plan

## Executive Summary

This plan details how to implement Lewis Carroll's symbolic logic within the existing TinyFoot story system, using **minimal structural changes** by creatively reinterpreting existing data models as logical constructs.

**Core Insight**: Carroll's logic is fundamentally about **sets, membership, and inference rules**. Our existing Archetype/Persona/Trait/Quality system already models set relationships. The ConditionalLogic extension already provides the operators needed for propositional reasoning.

---

## 1. Carroll's Logic: Core Concepts Mapped to Our System

### 1.1 Propositions (A, E, I, O)

Carroll uses four proposition types, each expressible in our system:

| Type | Form | Meaning | Our Mapping |
|------|------|---------|-------------|
| **A** | "All S are P" | Universal affirmative (S ⊆ P) | Archetype-Trait inheritance |
| **E** | "No S are P" | Universal negative (S ∩ P = ∅) | Archetype exclusion via trait conflict |
| **I** | "Some S are P" | Particular affirmative (S ∩ P ≠ ∅) | At least one Persona has both traits |
| **O** | "Some S are not P" | Particular negative (S ⊄ P) | At least one Persona lacks trait |

**Mapping Strategy**:

| Carroll Concept | TinyFoot Model | Relationship |
|-----------------|----------------|--------------|
| **Universal set** | All Archetypes | Universe of discourse |
| **Subject term (S)** | Archetype | A category/class |
| **Predicate term (P)** | Trait or Quality | A property |
| **Individual** | Persona | Instance of category |
| **Proposition truth** | `requires_state` check | Evaluated at runtime |

### 1.2 Syllogisms as Story Branches

A syllogism has the structure:
```
Premise 1: All M are P    (Major premise)
Premise 2: All S are M    (Minor premise)
Conclusion: All S are P   (Derived)
```

**In our story system**:

```
Node A (Premise 1): Player learns "All warriors are brave"
  → sets_state: { warriors_are_brave: true }

Node B (Premise 2): Player learns "All knights are warriors"
  → requires_state: { warriors_are_brave: true }  // Must have premise 1
  → sets_state: { knights_are_warriors: true }

Node C (Conclusion): Player can deduce "All knights are brave"
  → requires_state: {
      $and: [
        { warriors_are_brave: true },
        { knights_are_warriors: true }
      ]
    }
  → sets_state: { knights_are_brave: true }  // Valid inference!
```

### 1.3 Terms and Distribution

Carroll's rules require tracking which terms are "distributed" (refer to all members of a class):

| Context | Distributed? | Example |
|---------|--------------|---------|
| Subject of A | Yes | "**All cats** are mammals" |
| Predicate of A | No | "All cats are **mammals**" |
| Subject of E | Yes | "**No cats** are fish" |
| Predicate of E | Yes | "No cats are **fish**" |
| Subject of I | No | "**Some cats** are black" |
| Predicate of I | No | "Some cats are **black**" |
| Subject of O | No | "**Some cats** are not black" |
| Predicate of O | Yes | "Some cats are not **black**" |

**Implementation**: Track distribution as metadata in state variables (see Section 4.2).

---

## 2. Creative Mapping of Existing Structures

### 2.1 Archetypes as Set Categories

**Current Model** (`models.py:945-952`):
```python
class Archetype(ArchetypeBase, table=True):
    id: uuid.UUID
    name: str  # e.g., "Warriors", "Scholars", "Merchants"
    description: str
```

**Carroll Interpretation**:
- Each Archetype represents a **class/set** in the universe of discourse
- Archetype name = Set label (S, P, M in syllogistic terms)
- The collection of all Archetypes = Universal set

**Usage for Propositions**:
```
Archetype "Mortals"     → Set of all mortal beings
Archetype "Philosophers" → Set of all philosophers
Archetype "Greeks"       → Set of all Greeks

Proposition: "All Greeks are Mortals"
  → ArchetypeTraitLink: Greeks → has_trait("mortality")
  → ArchetypeTraitLink: Mortals → has_trait("mortality")
  → Inference: Greeks ⊆ Mortals (via shared trait)
```

### 2.2 Personas as Set Members (Individuals)

**Current Model** (`models.py:956-963`):
```python
class Persona(PersonaBase, table=True):
    id: uuid.UUID
    name: str  # e.g., "Socrates", "Aristotle"
```

**Carroll Interpretation**:
- Each Persona is an **individual** that can belong to multiple sets
- `ArchetypePersonaLink` → Set membership ("Socrates is a Greek")
- `PersonaTraitLink` → Property assertion ("Socrates is mortal")

**The Classic Syllogism**:
```
Premise 1: "All men are mortal"
  → Archetype "Men" has Trait "Mortal"
  → ArchetypeTraitLink(archetype="Men", trait="Mortal")

Premise 2: "Socrates is a man"
  → Persona "Socrates" linked to Archetype "Men"
  → ArchetypePersonaLink(archetype="Men", persona="Socrates")

Conclusion: "Socrates is mortal"
  → PersonaTraitLink(persona="Socrates", trait="Mortal", is_inherited=True)
```

### 2.3 Traits as Predicates

**Current Model** (`models.py:976-983`):
```python
class Trait(TraitBase, table=True):
    id: uuid.UUID
    name: str  # "Mortal", "Brave", "Wise", "Foolish"
    description: str
```

**Carroll Interpretation**:
- Traits are **predicates** that can be affirmed or denied of sets
- Trait presence = Affirmative predication
- Trait absence = Negative predication
- Trait conflicts = Logical contradictions

**Implementing Contradictories**:
```python
# Add to trait metadata or via QualityTraitLink:
Trait "Mortal" conflicts_with Trait "Immortal"
Trait "Brave" conflicts_with Trait "Cowardly"

# In story state:
requires_state: {
  $not: { has_trait_cowardly: true }  // Cannot have contradictory
}
```

### 2.4 Qualities as Derived Properties

**Current Model** (`models.py:966-973`):
```python
class Quality(QualityBase, table=True):
    id: uuid.UUID
    name: str  # "Wisdom", "Courage"
```

**Carroll Interpretation**:
- Qualities are **inferred properties** derived from trait combinations
- `QualityTraitLink` models the inference rule: "If trait X, then quality Y"
- This maps to Carroll's **rules of inference**

**Example**:
```
QualityTraitLink(trait="Philosophical", quality="Wisdom", auto_enable=True)

Rule: If persona has trait "Philosophical" → persona gains quality "Wisdom"

In Carroll terms: "All philosophers are wise" (A proposition)
```

### 2.5 Link Tables as Logical Relations

| Link Table | Carroll Meaning | Example |
|------------|-----------------|---------|
| `ArchetypeTraitLink` | "All X have property Y" | All Warriors are Brave |
| `ArchetypePersonaLink` | "Individual X is member of set Y" | Socrates is a Man |
| `PersonaTraitLink` | "Individual X has property Y" | Socrates is Mortal |
| `ArchetypeQualityLink` | "All X have quality Y" (inferred) | All Scholars have Wisdom |
| `QualityTraitLink` | "Property X implies quality Y" | Brave → Courage |

---

## 3. State Schema for Propositional Logic

### 3.1 Proposition State Variables

Define state variables that represent proposition truth values:

```python
# StoryStateVariable definitions for a Carroll story:

# Propositions (named by their logical content)
{ key: "all_men_are_mortal", value_type: "boolean", category: "premises" }
{ key: "socrates_is_a_man", value_type: "boolean", category: "premises" }
{ key: "socrates_is_mortal", value_type: "boolean", category: "conclusions" }

# Term membership tracking
{ key: "subject_term", value_type: "enum", enum_values: ["men", "greeks", "philosophers"] }
{ key: "predicate_term", value_type: "enum", enum_values: ["mortal", "wise", "foolish"] }
{ key: "middle_term", value_type: "enum", enum_values: ["men", "philosophers"] }
```

### 3.2 Distribution Tracking

Track term distribution for validity checking:

```python
# State variables for syllogism validity
{ key: "middle_term_distributed", value_type: "boolean", category: "validity" }
{ key: "conclusion_valid", value_type: "boolean", category: "validity" }

# Syllogism figure tracking
{ key: "syllogism_figure", value_type: "enum",
  enum_values: ["figure_1", "figure_2", "figure_3", "figure_4"],
  category: "structure" }
```

### 3.3 Mood Tracking

The "mood" is the combination of proposition types (AAA, EAE, etc.):

```python
{ key: "major_premise_type", value_type: "enum", enum_values: ["A", "E", "I", "O"] }
{ key: "minor_premise_type", value_type: "enum", enum_values: ["A", "E", "I", "O"] }
{ key: "conclusion_type", value_type: "enum", enum_values: ["A", "E", "I", "O"] }

# Combined mood (e.g., "AAA" = Barbara, "EAE" = Celarent)
{ key: "syllogism_mood", value_type: "string", category: "structure" }
```

---

## 4. Conditional Logic for Inference Rules

### 4.1 Using Existing Operators for Logic

The ConditionalLogicExtension (`frontend/docs/ConditionalLogicExtension.md:48-79`) already provides:

| Operator | Logic Use | Example |
|----------|-----------|---------|
| `$and` | Conjunction (∧) | Both premises must be true |
| `$or` | Disjunction (∨) | Alternative conclusions |
| `$not` | Negation (¬) | "Not P" |
| `$eq` | Identity | Proposition is true |
| `$ne` | Non-identity | Proposition is false |
| `$in` | Set membership | Term is in valid set |

### 4.2 Implementing Syllogistic Validity

**Valid Syllogism Example (Barbara - AAA-1)**:
```
Major: All M are P  (All philosophers are mortal)
Minor: All S are M  (All Greeks are philosophers)
∴ Conclusion: All S are P  (All Greeks are mortal)
```

**Choice Implementation**:
```typescript
// Choice: "Deduce the conclusion"
{
  requires_state: {
    $and: [
      { major_premise_established: true },
      { minor_premise_established: true },
      { syllogism_figure: "figure_1" },
      { syllogism_mood: { $in: ["AAA", "EAE", "AII", "EIO"] } } // Valid moods for Figure 1
    ]
  },
  sets_state: {
    conclusion_valid: true,
    all_S_are_P: true  // The derived proposition
  }
}
```

### 4.3 Detecting Invalid Syllogisms (Fallacies)

**Invalid Example (Undistributed Middle)**:
```
Major: All P are M  (All dogs are mammals)
Minor: All S are M  (All cats are mammals)
× Conclusion: All S are P  (All cats are dogs) - INVALID!
```

**Implementation**:
```typescript
// Choice: "Attempt invalid conclusion"
{
  requires_state: {
    $and: [
      { major_premise_established: true },
      { minor_premise_established: true },
      { middle_term_distributed: false }  // UNDISTRIBUTED!
    ]
  },
  sets_state: {
    attempted_invalid_inference: true,
    fallacy_type: "undistributed_middle",
    conclusion_valid: false
  },
  // This choice leads to a "fallacy detected" node
}
```

---

## 5. Story Structure for Carroll Logic

### 5.1 Diagram-Based Navigation (Venn/Euler)

Carroll used diagrams extensively. We can represent these as story branches:

```
                    [Start: Empty Diagram]
                            |
              +-------------+-------------+
              |                           |
    [Add Circle S]              [Add Circle P]
              |                           |
              +-------------+-------------+
                            |
                    [Intersection Node]
                            |
              +-------------+-------------+
              |             |             |
         [S ⊆ P]      [S ∩ P ≠ ∅]    [S ∩ P = ∅]
         (All S       (Some S        (No S
          are P)       are P)         are P)
```

**Node Types for Diagram Stories**:
- `diagram_state` nodes: Show current diagram
- `add_set` choices: Add a circle/set to diagram
- `mark_region` choices: Mark regions as empty/occupied
- `conclusion` nodes: Derive valid conclusions

### 5.2 Paradox Stories

Carroll loved paradoxes. These are perfect for branching narratives:

**The Barbershop Paradox**:
```
Node: "Allen, Brown, and Carr run a barbershop..."

Choice 1: "Assume Allen is out"
  → sets_state: { allen_out: true }
  → leads to deduction chain

Choice 2: "Assume Allen is in"
  → sets_state: { allen_in: true }
  → leads to contradiction

Final Node: requires_state: { $or: [{ contradiction: true }, { paradox_resolved: true }] }
```

### 5.3 Progressive Deduction Chains

Build syllogisms step by step:

```
[Node 1: Establish Universe]
"We shall reason about creatures..."
  → sets_state: { universe: "creatures" }

[Node 2: First Premise]
"All dragons breathe fire"
  requires: { universe: "creatures" }
  → sets_state: { premise_1: "all_dragons_breathe_fire" }

[Node 3: Second Premise]
"No fire-breathers are arctic animals"
  requires: { premise_1: { $exists: true } }
  → sets_state: { premise_2: "no_fire_breathers_arctic" }

[Node 4: Derive Conclusion]
"Therefore..."
  requires: { $and: [
    { premise_1: { $exists: true } },
    { premise_2: { $exists: true } }
  ]}

  Choice A: "No dragons are arctic animals" → VALID
  Choice B: "Some dragons are not arctic" → INVALID (wrong mood)
  Choice C: "All arctic animals are dragons" → INVALID (illicit conversion)
```

---

## 6. Mapping Archetypes to Categorical Sets

### 6.1 Creating Set Relationships

To model "All S are P" using Archetypes:

```python
# Create Archetypes as sets
archetype_S = Archetype(name="Greeks")
archetype_P = Archetype(name="Mortals")

# Create a shared Trait that defines the relationship
trait_mortality = Trait(name="Subject to Death")

# Link both Archetypes to this trait
ArchetypeTraitLink(archetype_id=archetype_S.id, trait_id=trait_mortality.id)
ArchetypeTraitLink(archetype_id=archetype_P.id, trait_id=trait_mortality.id)

# Now "Greeks" and "Mortals" share property "Subject to Death"
# This represents: Greeks ⊆ Mortals (via shared defining trait)
```

### 6.2 Personas as Proof Witnesses

For particular propositions ("Some S are P"):

```python
# To prove "Some Greeks are philosophers"
persona_socrates = Persona(name="Socrates")

# Socrates is both Greek and a Philosopher
ArchetypePersonaLink(archetype_id=archetype_greeks.id, persona_id=persona_socrates.id)
ArchetypePersonaLink(archetype_id=archetype_philosophers.id, persona_id=persona_socrates.id)

# Socrates is the "witness" that proves the particular proposition
```

### 6.3 Using StoryRequirement for Logic Gates

The `StoryRequirement` model can gate story access based on logical conditions:

```python
# A story about advanced syllogisms requires understanding of premises
StoryRequirement(
    story_id=advanced_story.id,
    requirement_type="trait",
    target_id=trait_logical_training.id,
    description="Must understand basic logic"
)
```

---

## 7. Implementation Complexity Analysis

### 7.1 Low Complexity (Use Existing Structures As-Is)

| Feature | Existing Support | Notes |
|---------|------------------|-------|
| Binary propositions | `boolean` state variables | Direct use |
| AND/OR conditions | `$and`, `$or` operators | Implemented |
| Set membership via traits | `PersonaTraitLink` | Existing |
| Inheritance | `is_inherited` flag on links | Existing |
| Category grouping | `category` on StateVariable | Existing |

### 7.2 Medium Complexity (Minor Extensions)

| Feature | Required Change | Effort |
|---------|-----------------|--------|
| Contradictory traits | Add `conflicts_with` field to Trait | Small |
| Distribution tracking | State variable convention | Config only |
| Mood validation | Custom validation function | Medium |
| Diagram rendering | Frontend component | Medium |

### 7.3 Higher Complexity (New Functionality)

| Feature | Required Change | Effort |
|---------|-----------------|--------|
| Automatic inference engine | New service layer | Large |
| Proof tree visualization | New frontend component | Large |
| Paradox detection | Complex validation logic | Medium-Large |
| Multi-premise chaining | Extended state management | Medium |

---

## 8. Recommended Implementation Phases

### Phase 1: Foundation (Minimal Changes)

**Goal**: Create Carroll-style stories using only existing features.

1. **Define naming conventions** for state variables:
   - `prop_all_X_are_Y` for A propositions
   - `prop_no_X_are_Y` for E propositions
   - `prop_some_X_are_Y` for I propositions
   - `prop_some_X_are_not_Y` for O propositions

2. **Create template Archetypes** for logical categories:
   ```
   Archetype: "Logical Terms"
   └── Trait: "Subject Term"
   └── Trait: "Predicate Term"
   └── Trait: "Middle Term"
   ```

3. **Build sample syllogism story** using existing choice/state system

4. **Document patterns** in a Carroll Story Authoring Guide

**Files Changed**: None (documentation + data only)

### Phase 2: Enhanced Validation

**Goal**: Add validity checking for syllogisms.

1. **Add validation utility** (`utils/syllogismValidator.ts`):
   ```typescript
   function validateSyllogism(
     majorType: 'A'|'E'|'I'|'O',
     minorType: 'A'|'E'|'I'|'O',
     conclusionType: 'A'|'E'|'I'|'O',
     figure: 1|2|3|4
   ): { valid: boolean; fallacy?: string }
   ```

2. **Extend StateConditionEditor** with "Syllogism Mode" toggle

3. **Add mood/figure dropdowns** for structured input

**Files Changed**:
- New: `frontend/src/utils/syllogismValidator.ts`
- Modified: `frontend/src/components/Stories/shared/StateConditionEditor.tsx`

### Phase 3: Trait Conflicts (Contradictories)

**Goal**: Model logical contradictions.

1. **Add TraitConflict model**:
   ```python
   class TraitConflict(SQLModel, table=True):
       trait_a_id: uuid.UUID  # e.g., "Mortal"
       trait_b_id: uuid.UUID  # e.g., "Immortal"
       conflict_type: str     # "contradictory" or "contrary"
   ```

2. **Update validation** to check for conflicting traits in persona

3. **Story effect**: Choices that would create contradiction are blocked

**Files Changed**:
- Modified: `backend/app/models.py` (new model)
- New migration
- Modified: `backend/app/crud.py` (conflict checking)

### Phase 4: Diagram Visualization

**Goal**: Visual representation of Carroll's diagrams.

1. **Create VennDiagram component**:
   ```typescript
   <VennDiagram
     sets={["S", "P", "M"]}
     regions={[
       { id: "S_only", marked: "empty" },
       { id: "SP_intersection", marked: "occupied" }
     ]}
   />
   ```

2. **Add diagram node type** to story authoring

3. **Animate diagram changes** as player makes deductions

**Files Changed**:
- New: `frontend/src/components/Stories/StoryPlayer/VennDiagram.tsx`
- Modified: `frontend/src/components/Stories/StoryPlayer/StoryPreview.tsx`

### Phase 5: Inference Engine (Advanced)

**Goal**: Automatic deduction from premises.

1. **Create inference service**:
   ```python
   def derive_conclusions(premises: list[Proposition]) -> list[Proposition]:
       # Implements Barbara, Celarent, etc.
       pass
   ```

2. **Integrate with story progression**

3. **Support for sorites** (chain syllogisms)

---

## 9. Cross-Reference Matrix

| Carroll Concept | Primary Model | Secondary Model | State Variable | Operator |
|-----------------|---------------|-----------------|----------------|----------|
| Universal Affirmative (A) | ArchetypeTraitLink | - | `prop_all_X_are_Y: boolean` | `$eq: true` |
| Universal Negative (E) | TraitConflict (new) | ArchetypeTraitLink | `prop_no_X_are_Y: boolean` | `$eq: true` |
| Particular Affirmative (I) | PersonaTraitLink | ArchetypePersonaLink | `prop_some_X_are_Y: boolean` | `$exists: true` |
| Particular Negative (O) | PersonaTraitLink (absence) | - | `prop_some_X_not_Y: boolean` | `$not: {...}` |
| Middle Term | Trait (shared) | - | `middle_term: enum` | `$in: [...]` |
| Distribution | - | - | `term_X_distributed: boolean` | `$eq: true` |
| Syllogism Figure | - | - | `figure: enum` | `$eq: "figure_1"` |
| Syllogism Mood | - | - | `mood: string` | `$in: ["AAA",...]` |
| Valid Conclusion | NodeChoice.sets_state | - | `conclusion_valid: boolean` | (set on valid path) |
| Fallacy | NodeChoice (leads to fallacy node) | - | `fallacy_type: enum` | (set on invalid path) |
| Contradiction | TraitConflict | - | `contradiction: boolean` | `$and: [{A}, {not A}]` |
| Proof Witness | Persona | PersonaTraitLink | `witness_exists: boolean` | `$exists: true` |

---

## 10. Example: Complete Carroll Story

### Story: "The Game of Logic - Level 1"

**State Schema**:
```json
{
  "variables": [
    { "key": "established_premise_1", "type": "boolean", "category": "premises" },
    { "key": "established_premise_2", "type": "boolean", "category": "premises" },
    { "key": "attempted_conclusion", "type": "string", "category": "conclusions" },
    { "key": "conclusion_valid", "type": "boolean", "category": "validation" },
    { "key": "fallacy_committed", "type": "string", "category": "validation", "enum_values": ["none", "undistributed_middle", "illicit_major", "illicit_minor"] }
  ]
}
```

**Story Nodes**:

```
[Start Node: "The Puzzle"]
Content: "Consider these facts about students and scholars..."
Choices:
  → "Learn the first premise" (no requirements)
  → "Skip to conclusion" (leads to fallacy)

[Node: "First Premise"]
Content: "All dedicated students are scholars."
sets_state: { established_premise_1: true, premise_1_type: "A" }
Choices:
  → "Learn the second premise"
  → "Try to conclude now" (leads to fallacy - missing premise)

[Node: "Second Premise"]
Content: "Maria is a dedicated student."
requires_state: { established_premise_1: true }
sets_state: { established_premise_2: true, premise_2_type: "A" }
Choices:
  → "What can we conclude about Maria?"

[Node: "Conclusion Options"]
requires_state: { $and: [{ established_premise_1: true }, { established_premise_2: true }] }
Choices:
  → "Maria is a scholar"
      sets_state: { attempted_conclusion: "valid", conclusion_valid: true }
      → leads to [Victory Node]
  → "All scholars are Maria"
      sets_state: { attempted_conclusion: "illicit_conversion", fallacy_committed: "illicit_major" }
      → leads to [Fallacy Explanation Node]
  → "Some students are not Maria"
      sets_state: { attempted_conclusion: "non_sequitur", fallacy_committed: "other" }
      → leads to [Fallacy Explanation Node]

[Victory Node]
requires_state: { conclusion_valid: true }
Content: "Excellent! You have correctly applied Barbara (AAA-1)!"
is_end_node: true

[Fallacy Explanation Node]
requires_state: { fallacy_committed: { $ne: "none" } }
Content: "That conclusion doesn't follow. Here's why: [explains based on fallacy_committed]"
Choices:
  → "Try again" → back to Conclusion Options
```

---

## 11. Summary: Minimal Change Strategy

### What We Use As-Is:
- `Archetype` as logical set/class
- `Persona` as individual/instance
- `Trait` as predicate/property
- `ArchetypeTraitLink` as "All X are Y"
- `PersonaTraitLink` as "X is Y"
- `StoryStateVariable` for proposition tracking
- `requires_state/$and/$or` for premise combinations
- `sets_state` for deriving conclusions

### What We Add (Minimal):
1. **Naming conventions** for state variables (documentation)
2. **Syllogism validator function** (frontend utility)
3. **TraitConflict model** (optional, for contradictories)
4. **Diagram component** (optional, for visualization)

### What We Defer:
- Full inference engine (complex, not needed for authored stories)
- Automated proof checking (can be done manually via story structure)
- Natural language parsing (Carroll's examples are already structured)

---

## 12. Next Steps

1. **Create sample Carroll story** using current system (validation of approach)
2. **Document authoring patterns** for logic-based stories
3. **Implement syllogism validator** (Phase 2)
4. **Gather feedback** on complexity and usability
5. **Iterate** based on actual story authoring experience

---

## Appendix A: Valid Syllogism Moods by Figure

| Figure 1 | Figure 2 | Figure 3 | Figure 4 |
|----------|----------|----------|----------|
| AAA (Barbara) | EAE (Cesare) | IAI (Disamis) | AEE (Camenes) |
| EAE (Celarent) | AEE (Camestres) | AII (Datisi) | IAI (Dimaris) |
| AII (Darii) | EIO (Festino) | OAO (Bocardo) | EIO (Fresison) |
| EIO (Ferio) | AOO (Baroco) | EIO (Ferison) | |

## Appendix B: Fallacy Types

| Fallacy | Description | Detection |
|---------|-------------|-----------|
| Undistributed Middle | Middle term not distributed in either premise | Check distribution flags |
| Illicit Major | Major term distributed in conclusion but not premise | Compare distribution |
| Illicit Minor | Minor term distributed in conclusion but not premise | Compare distribution |
| Exclusive Premises | Both premises are negative | Count E/O premises |
| Affirmative Conclusion from Negative | Negative premise with affirmative conclusion | Check types |
| Existential Fallacy | Universal conclusion from universal premises about empty set | Requires existence check |

## Appendix C: Reference Documents

- `frontend/docs/ConditionalsCarrollStoryIntegration.md` - Initial Carroll integration concept
- `frontend/docs/ConditionalLogicExtension.md` - Operator implementation details
- `backend/app/models.py` - Data model definitions
- `backend/docs/StoryStateSchema/StoryStateSchemaCompleted.md` - State variable system
