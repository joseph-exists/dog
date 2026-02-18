# Story Presentation System Design

> **Status:** Outline / Working Draft
> **Purpose:** Define how Authors apply visual themes to Stories and Nodes for Viewers

---
TODO: we need to decompose this into a set of interdependent pieces so that we can maintain focus.


## Part 1: The Use Case

### 1.1 The Author's Journey

An Author has created a Story using our system. The Story exercises the full engine:
(including but not limited to)
- HTML forms with SVG backgrounds
- Code snippets with syntax highlighting
- directory structure (as code snippet)
- interactive text entry field (either primitive or expanded CLI) 
- State machines with branching paths
- Rich narrative content
- Interactive decision points

Now the Author wants to **beautify** this interactive story — making it as visually compelling for Viewers as it is functionally interesting.

### 1.2 What the Author Needs

<!-- TODO: Define the Author's requirements -->
- [ ] Set a cohesive visual identity for the entire Story
- [ ] Set cohesive visual identities for types within that Story (all CLI windows are X, all HTML forms use the framer-snappy override)
- [ ] Override that identity for specific Nodes/types that need distinct treatment
- [ ] Preview how Viewers will experience the themed Story
- [ ] Adjust themes without breaking content or logic

### 1.3 What the Viewer Experiences

<!-- TODO: Define the Viewer's experience -->
- [ ] A visually coherent journey through the Story
- [ ] Appropriate visual treatment for different content types
- [ ] Smooth transitions between themed contexts
- [ ] Accessibility and readability maintained throughout

---

## Part 2: The Ontology

### 2.1 Entity Hierarchy

```
Story (root)
├── Story Metadata
│   ├── title, description, author
│   └── story_presentation (theme binding)
│
├── Node (many)
│   ├── Node Metadata (josep-note: assume a new Node type for multi-type - we will use ContentFormat='unknown' for this purpose until we're ready to qualify.)
│   │   ├── type, position, connections
│   │   └── node_presentation (override)
│   │
│   └── Node Content (varies by type)
│       ├── narrative text
│       ├── code blocks
│       ├── form definitions
│       ├── media references
│       └── state machine definitions
│
└── Story State (runtime)
    ├── current_node
    ├── history
    └── variables
```

### 2.2 Presentation Scope Definitions

<!-- TODO: Define each scope precisely -->

| Scope | Owned By | Applies To | Overridden By |
|-------|----------|------------|---------------|
| **Story Presentation** | Author | All nodes in story | Node Presentation |
| **Node Presentation** | Author | Single node | (nothing — most specific) |
| **Viewer Preferences** | Viewer | Their view | ??? |

### 2.3 Open Questions: Scope & Authority

<!-- TODO: Resolve these design questions -->

1. **Can Viewers override Author themes?**
- josep-response: yes, with limits - imposed by Author & System.

An Author can choose whether the Viewer of a Story can override the Story presentation. 
System toggle (*exists, tested, proven, but not currently integrated) that drops a set of objects into Application
level theme defaults.  This is for the cases where a User needs to specify accessibility, or where a set of users
can't use a specific set of fonts, or where only a set of users can use a certain visualization library.
* for this implementation - we focus on the Author toggle capacity at the Story level for yes/no.
* we do not look at how a Viewer might do that yet - only the Author.




2. **What is the cascade order?**
   - Option A: `Story → Node → Viewer`
   - Option B: `Viewer → Story → Node`
   - Option C: `Story → Node`, Viewer applies post-processing

josep-response: please help me understand these distinctions - potentially with a concise example story/node/viewer set that 
walks through how these options would impact it?  I think I may be confused about 'Viewer' as 'reader of story' vs 'author using the viewer while editing the story' vs 'the StoryView viewer'


3. **How do Node types influence presentation?**
   - Does a "code" node have different default tokens than a "narrative" node?
    it might.  an author might want to have the following:

    a: intro node with a highly stylized animation/text/whatever
    b: secondary node with three parts: 
        a text block (using font, highlights, outlines and an image background)
        a code block (using a different font, shiki hints, etc)
        an interactive text entry field with an output window
        
    c: a third node with plain text and buttons.   

    - Are there type-specific presentation schemas?
        yes. assume client exported types, schemas, and sdks for presentation enablement.
        these exist, and a significant number have been exported. we need to pause for each potential addition
        and review where it should live, how it should be exported, and what affordances we need from a specific presentation schema.
        we will support types registries on the frontend as well.
---

## Part 3: Content Types & Their Presentation Needs

### 3.1 Content Type Inventory

<!-- TODO: Enumerate all node content types -->

| Content Type | Presentation Concerns | Theme Tokens Needed |
|--------------|----------------------|---------------------|
| **Narrative Text** | Typography, spacing, readability | `--foreground`, `--background`, font tokens |
| **Code Snippet** | Syntax highlighting, monospace | Syntax theme tokens (Shiki) |
| **HTML Form** | Input styling, button colors | Form-specific tokens |
| **SVG Background** | Color fills, stroke colors | SVG variable injection? |
| **State Machine Viz** | Node colors, edge colors, labels | Diagram tokens |
| **Media (image/video)** | Borders, captions, overlays | Media container tokens |
| **Decision Point** | Button styling, hover states | Interactive tokens |

josep-response: we should map these to the existing types and schemas.


### 3.2 The Syntax Theme Question

<!-- TODO: Define syntax theme integration -->

- How does the Story's card/page theme relate to syntax highlighting?
- Do we need a separate `syntax` slot at the Story level?
- How does Shiki theme selection work within a Node?

josep-response: syntax highlighting will happen at the furthest level down the tree, so it will take precedence over everything above it.
this means that shiki formatting will *always* 'win' over any other themes being applied.


### 3.3 The Form Styling Question

<!-- TODO: Define form presentation -->

josep-response: forms are 'less special' than some of the other types here.  pause on forms and circle back
after some other pieces are resolved - our answers will more than likely be directly informed by those more
complicated components.  if we solve forms first, then we'll solve more complex components with respect to forms -
and that's the wrong order.


- Forms have their own visual language (inputs, buttons, validation)
- How much should the Story theme influence form appearance?
- Do we need form-specific tokens or rely on CSS variable inheritance?

---

## Part 4: The Cascade Architecture

### 4.1 Resolution at Render Time

<!-- TODO: Define the resolution algorithm -->

```
When rendering Node N in Story S for Viewer V:

1. Start with system defaults
2. Apply S.story_presentation (if set)
3. Apply N.node_presentation (if set)
4. Apply V.viewer_preferences (if allowed)
5. Apply content-type-specific defaults (code, form, etc.)
6. Render with resolved tokens
```

Yes.  This is aligned with my understanding.

### 4.2 Token Categories for Stories

<!-- TODO: Define which token categories apply -->

| Category | Story Level | Node Level | Notes |
|----------|-------------|------------|-------|
| Page theme | ✓ | ? | Background, overall surface |
| Card theme | ✓ | ✓ | Content container styling |
| Syntax theme | ✓ | ✓ | Code blocks |
| Motion theme | ✓ | ✓ | Transitions, animations |
| Typography | ✓ | ✓ | Fonts, sizes, spacing |

### 4.3 Binding Types for Stories

this already exists - bindings, pref binding, and context key structures - we will add this to the technical spec when we're ready

<!-- TODO: Define binding semantics -->

- **Authored Binding**: Author sets theme for Story/Node (persisted with entity)
- **User Preference Binding**: Viewer's default (persisted with user)
- **Context Key Structure**: How do we key Story and Node contexts?

```
Possible context keys:
  "story:{story_id}"
  "story:{story_id}/node:{node_id}"
  "story:{story_id}/node:*"
  "story:*/node:{node_type}"
```

---

## Part 5: The Authoring Workflow

### 5.1 Setting Story-Level Presentation

<!-- TODO: Define the UI/UX for story theming -->

**Where in the interface?**
- [X] Story settings/metadata panel
- [X] Dedicated "Presentation" tab in StoryEditor
- [X] Theme picker in story header

**What can the Author configure?**
- [X] Page theme (background, overall mood)
- [X] Card theme (content container default)
- [X] Syntax theme (code block default)
- [X] Motion theme (transitions)
- [X] Custom tokens (brand colors, etc.)

### 5.2 Setting Node-Level Overrides

<!-- TODO: Define per-node customization -->

**Where in the interface?**
- [X] NodeEditor panel (existing)
- [X] Node context menu
- [X] Node inspector sidebar
- new functionality will need to be implemented here, once we've solidified the design.


**What can the Author override?**
- [X] Full theme swap (select different theme)
- [X] Token tweaks (adjust specific values)
- [X] Content-type-specific settings

and more. 

### 5.3 Preview & Validation

<!-- TODO: Define preview capabilities -->

- How does the Author preview themed nodes?
 - josep-note:in the StoryEditor/StoryPreview - panels exist for this now.
- How do they see the cascade in action?
 - josep-note: same as above
- What warnings/errors for accessibility issues?
    - josep-note: we're relying on the system overrides here.  Authors of nodes do not need to ensure accessibility for all users - we do.
    so a node as the author creates it may not adhere to accessibility guidelines - if a user needs a story to be accessible, that will be set outside of the story,
    and their viewer will override all applied themes with their own settings.  

---

## Part 6: The Viewing Experience

### 6.1 StoryPlayer Theme Application

<!-- TODO: Define runtime theme application -->

josep-response: pause for now

- When does theme resolution happen?
- How are CSS variables applied to the player?
- What's the performance consideration?

### 6.2 Transitions Between Nodes

<!-- TODO: Define transition behavior -->

- What happens visually when moving between differently-themed nodes?
- Instant switch vs. animated transition?
- Does Motion theme control this?

### 6.3 Viewer Accessibility Options

<!-- TODO: Define viewer controls -->

josep-response: pause on this for now. viewer accessibility is not handled by the Author.

- Can viewers adjust font size?
- Can viewers enable high contrast?
- Can viewers disable animations?
- How do these interact with Author themes?

---

## Part 7: Data Model Considerations

* pause - we will review when we get to this point.  these already exist.* 

### 7.1 Story Model Extensions

<!-- TODO: Define schema additions -->



```python
# Conceptual — not final
class Story:
    # ... existing fields ...
    presentation: StoryPresentation | None  # New field

class StoryPresentation:
    page_theme_id: UUID | None
    card_theme_id: UUID | None
    syntax_theme_id: UUID | None
    motion_theme_id: UUID | None
    custom_tokens: dict[str, Any] | None
```

### 7.2 Node Model Extensions

<!-- TODO: Define node presentation -->

```python
# Conceptual — not final
class Node:
    # ... existing fields ...
    presentation: NodePresentation | None  # Override

class NodePresentation:
    theme_id: UUID | None           # Full theme swap
    token_overrides: dict | None    # Specific tweaks
    decoration_hint: str | None     # Typography style
```

### 7.3 Theme Binding Integration

<!-- TODO: Define how existing binding system applies -->

- Do we use the existing ThemeBinding model?
- New binding_type for authored story bindings?
- Context key conventions for story/node

---

## Part 8: Implementation Phases

### Phase 1: Story-Level Theming
<!-- TODO: Define MVP scope -->
- [ ] Add presentation field to Story model
- [ ] StoryEditor UI for theme selection
- [ ] StoryPlayer applies story theme

### Phase 2: Node-Level Overrides
<!-- TODO: Define node override scope -->
- [ ] Add presentation field to Node model
- [ ] NodeEditor UI for theme override
- [ ] Cascade resolution in player

### Phase 3: Content-Type Integration
<!-- TODO: Define content-specific theming -->
- [ ] Syntax theme integration with Shiki
- [ ] Form styling token support
- [ ] SVG variable injection

### Phase 4: Viewer Preferences
<!-- TODO: Define viewer customization -->
- [ ] Viewer accessibility settings
- [ ] Preference vs. Author theme resolution
- [ ] Persistence of viewer preferences

---

## Part 9: Reference Integration

### 9.1 Related Documentation

- [Card Themes Technical Reference](../frontend/src/components/Agents/docs/CARD-THEMES-REFERENCE.md)
- [Agent Card Presentation Guide](../frontend/src/components/Agents/docs/AGENT-CARD-PRESENTATION-GUIDE.md)
- [Theme Cascade Architecture](../frontend/src/components/Common/Themes/CASCADING-THEMES.md)

### 9.2 Existing Code References

<!-- TODO: Map to existing implementation -->

| Concern | Current Location | Notes |
|---------|------------------|-------|
| Story model | `backend/app/models.py` | Needs presentation field |
| Node model | `backend/app/models.py` | Needs presentation field |
| StoryEditor | `frontend/src/components/Story/StoryEditor/` | Add theme panel |
| NodeEditor | `frontend/src/components/Story/StoryEditor/NodeEditor/` | Add override UI |
| StoryPlayer | `frontend/src/components/Story/StoryPlayer/` | Apply themes |
| Theme resolution | `frontend/src/hooks/useThemeBinding.ts` | Extend for story context |

---

## Appendix A: Open Questions Log

<!-- Capture questions as they arise -->

| # | Question | Status | Resolution |
|---|----------|--------|------------|
| 1 | Can Viewers override Author themes? | Open | |
| 2 | How do node types get default presentations? | Open | |
| 3 | What's the context key format for stories? | Open | |
| 4 | How does syntax theme relate to card theme? | Open | |
| 5 | Should presentation be inline or binding-based? | Open | |

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **Author** | User who creates and edits Stories |
| **Viewer** | User who experiences/plays Stories |
| **Story Presentation** | Theme configuration at the Story level |
| **Node Presentation** | Theme override at the Node level |
| **Cascade** | The resolution order from general to specific |
| **Token** | A CSS variable value (e.g., `--card: oklch(...)`) |
| **Slot** | A theme category (page, card, syntax, motion) |

---

## Revision History

| Date | Author | Changes |
|------|--------|---------|
| 2026-02-18 | Claude | Initial outline created |
