# Author / Proxy / Vouch — Companion & Theoretical Framework

> Companion to [persona-pages-reference.md](./persona-pages-reference.md). This document does not rewrite the reference guide — it layers theoretical framing, open design questions, and architectural direction over the existing system as documented there.

---

## The Identity Model

The system implements a three-layer identity architecture:

**User (Author)** — The root human identity. Authenticates, owns everything, sees the full graph. Never directly exposed to other participants. This is the substrate layer.

**UserPersona (Proxy)** — A discrete, independently-addressable identity that can create, connect, engage, and publish. Multiple UserPersonas per User. The mapping UserPersona→User is *invisible by default*. Linkage is only revealed through explicit, granular, per-connection grants — and those grants are directional.

**Vouch** — The system's relational intelligence layer. Observes engagement patterns across the network, computes bidirectional value, and surfaces proxy-level connection recommendations. Vouch is not a user action; it is a system process.

This is related to one of the core themes of the system, which is not represented in design:

Work.  The system enables work - what we do on it and use it for is Work.  A modification to an AgentConfig, writing a Story, updating a nodetree, a new demo - this is all Work.  Work is what is important in our system - it's the first class citizen, and Identity is not a way for Users to connect with each other - it's a way for Users to connect with the Work that other Users are doing: to learn from it, to repeat it, to extend it - to engage. 

### How Visibility Works

Given User **Joseph** with UserPersonas **Josep**, **Giuseppe**; and connections **Anna**, **Marco**, **Sam**:

| Observer | Sees User? | Sees Josep? | Sees Giuseppe? | Can infer linkage? |
|----------|-----------|-------------|----------------|-------------------|
| Anna     | ✓ (granted) | ✓ (granted) | ✗ | Knows Joseph↔Josep only |
| Marco    | ✗ | ✓ (granted) | ✗ | No linkage visible |
| Sam      | ✗ | ✗ | ✓ (granted) | No linkage visible |

No observer can infer the existence of UserPersonas they haven't been granted access to. The system maintains this invariant even under adversarial observation of the proxy-level graph.

---

## Mapping to Current Implementation

> Reference: persona-pages-reference.md § Architecture at a Glance, § Data Sources, § ADDENDUM A

### What Exists

The current `persona` table and `userpersona` junction table implement the structural skeleton of the User↔UserPersona relationship. The `PersonaLibraryService.getLibrary(owner)` pattern already models "a user's collection of personas."

The block-based page system (Identity, Bio, Domains, Traits, Qualities, Relationships) provides the *presentational* layer for a persona's public face.

### What's Missing

**Visibility/grant system.** Currently "any authenticated user can edit" (`isOwner = !!user`). The reference guide notes this needs restriction. But the target model goes far beyond creator-only permissions — it requires per-connection visibility grants with directional semantics. The current `userpersona` junction has no visibility or grant columns.

**Anonymous publication.** No current mechanism for publishing work detached from all identity. Works are currently attributable. The target model requires a publication mode where output enters the system with zero back-reference to any User or UserPersona, with an optional post-hoc "claiming" flow.

**Engagement observation.** The `event` table exists (noted in reference as "not integrated with any current components, will be used extensively in vouch and recommender systems") but has no engagement-pattern infrastructure built on top of it.

**Proxy-aware connection recommendations.** Nothing in the current system computes relational value or suggests connections. The vouch layer is an undetermined abstraction - we are not building to it, we're building the primitives, types, and structures that it will interface with.  

---

## Theoretical Lenses

Each lens identifies specific invariants and failure modes that should inform the data model.

### 1. Category Theory — Structural Foundation

The system maintains *multiple categories over the same underlying structure*.

**The total category** (system-internal): Objects are Users, UserPersonas, Works, Connections. Morphisms include User→UserPersona ownership, UserPersona→Work authorship, Connection edges between UserPersonas, and the vouch-computed recommendation morphisms.

**Per-observer fibers**: Each participant sees a *projection* of the total category. Anna's fiber includes {Joseph, Josep, Works-by-Joseph, Works-by-Josep, connections involving Joseph or Josep}. Sam's fiber includes {Giuseppe, Works-by-Giuseppe, connections involving Giuseppe}. These fibers share no overlap — and the system must guarantee this.

**The vouch process** operates in the total category (it needs the full graph to compute recommendations) but *projects results into the appropriate fiber* for each participant. This is the critical operation: computation happens at the Author level, presentation happens at the Proxy level, and information never leaks between fibers.

*Open question:* What is the functor that describes the "claiming" operation — when a user attaches a UserPersona to an anonymous work? This changes the fiber for every observer who has access to that UserPersona, retroactively. Is this a natural transformation between the pre-claim and post-claim fiber categories?

### 2. Covering Spaces (Topology) — Privacy Model (NOT CURRENT WORK - covered in Vouch, prior to launch.)

The User is the base space. UserPersonas are sheets of a covering. Each observer sees only the sheets they've been granted access to. The projection map (UserPersona→User) exists but is hidden.

The vouch system performs **path-lifting**: it observes a path of engagement in the base space (User-level behavioral pattern) and lifts it to the appropriate sheet (UserPersona) for each observer.

The well-developed theory of *when sheets of a covering can be distinguished* maps directly to privacy guarantees. If two UserPersonas are sheets over the same User, what observables could an adversary use to determine they share a base point?

*Open question — potential sheet-distinguishing attacks:*
- Timing correlations (Giuseppe and Josep never post simultaneously)
- Stylistic fingerprinting (behavioral analysis across UserPersonas)
- Engagement pattern analysis (both UserPersonas engage with the same niche content)
- Network topology (shared connection neighborhoods, even without shared connections)

These are the **information flow** invariants we need to verify.

### 3. Information Flow Theory — Security Invariant: VOUCH centric

The core property, stated formally: **observing the proxy-level graph, all published works, all engagement patterns, and all vouch recommendations visible to an observer should give that observer zero additional bits about the User-level mapping** beyond what they've been explicitly granted.

This is a **noninterference** property from security research. It needs to hold not just at rest (the data model doesn't leak) but *dynamically* (the system's behavior over time doesn't leak).

*Implication for the event system:* The `event` table (reference guide § ADDENDUM A) will be central to vouch computation. Event streams must be processed in a way that doesn't create observable side-channels. If Giuseppe's engagement with a work triggers a vouch recommendation to someone in Josep's network, that recommendation must not reveal that the trigger came from the same User.

### 4. Mechanism Design — Vouch Integrity

The vouch system must resist **Goodhart's Law**: the moment users understand what behaviors the system rewards, they optimize for the metric rather than the authentic behavior.

Current recommender systems solve this by not caring (engagement is engagement, authentic or performed — all monetizable). This system cannot afford that shortcut because the vouch signal's value *depends on its authenticity*.

Design implications:
- The evaluation function should be opaque or at minimum not directly gameable
- Bidirectional weighting means unilateral gaming is structurally harder (you can't manufacture the other party's engagement)
- The transitive trust signal (Anna↔Naheed informing a recommendation to Joseph) is deliberately *not revealed* — this prevents social-graph gaming where users strategically connect to bridge nodes

*critical question:* How do we handle cold-start? A new User with no engagement history has no vouch signal. A new UserPersona has no behavioral cluster for proxy-routing. What's the bootstrapping path that doesn't compromise the model?

Answer: new users require a 'vouchment' from an existing user.  there is not an open door to the walled garden.

### 5. Game Theory — Mutual De-anonymization

The anonymous publication + engagement + optional reveal process is a **coordination game**. Both parties benefit from mutual revelation (they can form a connection), but premature unilateral revelation has asymmetric risk (you've exposed yourself without reciprocity).

The system should structure this so that:
- Revelation is always simultaneous (neither party sees the other's identity until both have opted in)
- The cost of non-revelation is low (you can still engage with the work)
- The benefit of mutual revelation scales with existing engagement quality (vouch signal)

*Open question:* Is there a mechanism analogous to a **commitment scheme** — where both parties commit to reveal before either sees the result? This prevents the "peek and retreat" problem.

This is an interesting case where we want to think about the affordances of the different paths.  Why does person A *need* person B's identity to expose their own identity to Person B?  There's the feeling of a fallacy embedded here, and i'm unsure where it lives.

### 6. Semiotics — The Barthes Foundation

The proxy system is a semiotic architecture: the signifier (UserPersona) is deliberately detached from the signified (User), and meaning is constructed at the point of engagement rather than at the point of authorship.

This has concrete design implications. When a work is published anonymously, it exists as **pure text** — no author-function. Engagement with that work is engagement with the work itself, not with the author's reputation, social position, or identity. The optional "claiming" process *reattaches the author-function* — but now the work has an independent engagement history that preceded that attachment.

This connects to the reference guide's own note about domains:

> *"If one way we're thinking about the affordance of personas is to enable movement through different affordances of being — so a person/agent/etc isn't stuck in an interpellated approximation of 'who they are and what they are capable of and what they have to do to survive' — then telling a person to choose their domains feels counterproductive."*
> — persona-pages-reference.md, DomainsBlock note

The domain model should emerge from behavior (tagging, weighted tagging) rather than being declared. This is the Barthes principle applied to self-description: the persona is what it *does*, not what it *claims to be*. The system observes and tags; the user adjusts and refines.

---

## Refactoring Vectors — From Current to Target


### 1. `userpersona` → Visibility-Aware Junction

The current `userpersona` table links a User to a Persona. It needs to become an enabling substrate for:

- Ownership (this User created/controls this UserPersona)

- Grants (this User has revealed this UserPersona to Connection X)

- Grant directionality (Anna can see Joseph↔Josep; this doesn't mean Josep can see Anna's proxies)

*Category theory lens:* This table defines which objects appear in each observer's fiber.

### 2. `persona` → Behavioral Identity

Per the reference guide's own notes, the domain columns (`general_domain`, `specific_domain`, etc.) are being refactored. The target is a tag-based, weighted, emergent identity model rather than a hierarchical declaration.

The `tag` table (reference guide § ADDENDUM A) currently only links to stories (`storytotag`). Extending tags to personas, works, and engagement events is a prerequisite for both behavioral identity and vouch computation.

*Semiotics lens:* Tags should be system-observed and user-adjustable, not user-declared-and-fixed. The persona's identity is a living document, not a form submission.

### 3. Anonymous Publication Layer

A new concept: **Work** (or whatever we name it) — a unit of published output that can exist in the system without any identity attachment. It needs:
- A content payload
- An engagement surface (others can interact with it)
- An optional, revocable identity attachment (claiming)
- An engagement history that persists independently of identity attachment

*Information flow lens:* The act of claiming must not retroactively compromise the engagement history. If Naheed engaged with an anonymous work and the author later claims it as Giuseppe, Naheed should not be able to use timing data from the anonymous period to correlate Giuseppe with other UserPersonas.

### 4. Event → Engagement Signal Pipeline

The `event` table becomes the raw input for vouch computation. The pipeline needs:
- Event capture (what happened, who was involved at the UserPersona level, when, in what context)
- Aggregation (per-dyad engagement scoring, bidirectional weighting)
- Recommendation generation (proxy-aware, privacy-preserving)
- Presentation (surfaced in the appropriate fiber for each observer)

*Mechanism design lens:* The aggregation function should weight *diversity* of engagement (across contexts, over time) over *volume*. This makes gaming harder — you can't just spam interactions.

### 5. Vouch Recommendation Engine

The system process that ties it all together. It operates on the total category, projects into fibers, and must satisfy the noninterference property at every step.

*Covering space lens:* The recommendation "connect with Naheed through Giuseppe↔Aloysius" is a lifted path — the system found a connection in the base space and presented it on the correct sheets for both observers. Neither observer learns anything about the other's sheets.

---

## Open Questions Inventory

Collected from above and from the reference guide's inline notes:

| # | Domain | Question |
|---|--------|----------|
| 1 | Category Theory | What is the formal description of the "claiming" operation as a functor/natural transformation between fiber categories? |
| 2 | Information Flow | What are the full set of side-channel attacks against the noninterference property? (timing, stylistic, topological, engagement-pattern) |
| 3 | Mechanism Design | How does vouch handle cold-start for new Users and new UserPersonas? |
| 4 | Game Theory | What commitment scheme governs mutual de-anonymization? Simultaneous reveal? Escrow? |
| 5 | Semiotics / Data Model | How do tags replace hierarchical domains? What's the weighting model? Who/what generates tags — system observation, user action, or both? |
| 6 | Data Model | What is a "Work"? How does it relate to current content objects (stories, pages)? Is it a new entity or a generalization? |
| 7 | Data Model | How does the grant/visibility model extend to agents? (reference guide notes agent_personas as existing) |
| 8 | Mechanism Design | What signals constitute "engagement quality" vs "engagement volume" in vouch computation? |
| 9 | Architecture | How does the event pipeline avoid creating observable side-channels between UserPersonas sharing a User? |
| 10 | Reference Guide | The `persona` domain columns are flagged for refactoring — does the tag-based model fully replace them, or is there a transitional hybrid? |

---

## What's Next

This document is a living companion. As we work through vouch protocols, mutual de-anonymization mechanics, and the event pipeline, sections will deepen. The theoretical lenses should be tested against implementation decisions — if a design choice violates a lens's invariant, that's a signal to reconsider.

The immediate next conversations are likely:
1. Data model for grants/visibility on `userpersona`
2. The "Work" entity and anonymous publication flow
3. Event capture schema and vouch aggregation
4. Mutual de-anonymization protocol design