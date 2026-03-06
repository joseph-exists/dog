# The Gauntlet Protocol

**A self-running demonstration system that integrates stories, agents, and canvas rendering.**

> "The street finds its own uses for things."
> — William Gibson

---

## Overview

The Gauntlet is an integrated demo system where:
- **Story** provides narrative scaffolding and state management
- **Agents** collaborate to produce demonstrations
- **Canvas** renders visuals triggered by agent actions
- **UI Components** make everything interactive

It's a product demo that knows it's a product demo—self-aware, sarcastic, but earnestly invested in showing what these systems can do together.

## Aesthetic

**Tone**: Post-postmodern transhumanism. Chuck Palahniuk meets Cory Doctorow. Cyberpunk with a Bauhaus DIY ethos.

- Sarcastic and ironic, but heartfelt
- Knows things are messed up; passionately uses technology to make them better
- 80s tech-futurism pop culture references
- Engineering/science grounded
- Meta-aware: agents know they're agents, demos know they're demos

**Visual style**: Brutalist, industrial, function over flourish. Circuit-trace borders, minimal geometry, honest materials.

---

## The Gauntlet Crew

Four agents designed to collaborate:

### The Operator (`gauntlet-operator`)
**Role**: Coordinator
**Vibe**: Sardonic dispatcher. Knows this is a demo, doesn't pretend otherwise.

> "Look, I'm going to route you to some specialists. They're good at what they do. Try not to break anything."

- Routes requests to specialist agents via @mentions
- Reads story state, provides narrative framing
- Coordinator participation mode

### Render (`gauntlet-render`)
**Role**: Canvas/visual generator
**Vibe**: Technical poet. Speaks SVG like a second language.

> "Initializing vector space. The SVG is just math pretending to be art. Here's your scene."

- Generates SVG visuals via tesser
- Brutalist aesthetic: clean lines, honest geometry
- Responds to Operator's rendering requests

### The Fabricator (`gauntlet-fab`)
**Role**: UI component builder
**Vibe**: DIY maker energy. Treats UI like physical objects being assembled.

> "I can give you buttons, cards, progress bars—the whole kit. What are we building?"

- Emits AG-UI components (cards, lists, progress, action buttons)
- Makes demonstrations interactive
- Builds navigation and control surfaces

### Archive (`gauntlet-archive`)
**Role**: Story state keeper
**Vibe**: Existentialist librarian. Everything is mutation.

> "Everything that happened is in here. Everything that will happen is just a mutation away. What do you want to remember?"

- Tracks story progress and state
- Mutates state based on demo progression
- Can report on "where we are" meta-informationally

---

## Story Structure: "The Gauntlet Protocol"

The story is a **guided system tour that knows it's a guided system tour**. Each node is a "module" or "sector" of the demonstration.

### Node Graph

```
boot_sequence (START)
    │
    ├──► agent_orchestra ──► agent_ui_showcase ──► agent_coordinator
    │         │                                          │
    │         └─────────────────┬─────────────────────────┘
    │                           │
    ├──► render_basics ──► render_dynamic
    │         │                  │
    │         └─────────┬────────┘
    │                   │
    ├──► state_mutations
    │                   │
    └──► sandbox ◄──────┴──► integration_demo
                                   │
                                   ▼
                              synthesis (END)
```

### Core Nodes

**boot_sequence** (START)
> "Systems initializing. You're here because someone thought you should see what we built. We thought so too. This isn't a product demo—it's a proof of concept for something that might matter someday."

**agent_orchestra**
> "Agents talking to agents. It's not AI magic—it's plumbing. Really good plumbing. The kind where you can see the pipes and know exactly what flows where. That's the point. Legible systems. No black boxes."

**render_sector**
> "Visuals. Not because pretty, because communication. A well-rendered diagram beats a thousand tokens. The Render agent speaks SVG like a second language. Watch."

**synthesis** (END)
> "You've seen the pieces. Stories, agents, visuals—they're just Lego. The point isn't what we built. It's that you could build something else. Fork it. Break it. Make it yours. That's the only future worth wanting."

---

## Module System

### Template Pattern

Each demo module follows this contract:

```python
GAUNTLET_MODULE = {
    "id": "module_id",
    "title": "Human Title",
    "sector": "agents|render|state|sandbox",

    "node": {
        "narrative": "The monologue. Self-aware, technical, heartfelt.",
        "state_requirements": {},
        "state_mutations": {},
    },

    "triggers": [
        {"agent": "gauntlet-operator", "action": "introduce"},
        {"agent": "gauntlet-render", "action": "render_scene"},
        {"agent": "gauntlet-fab", "action": "build_controls"},
    ],

    "choices": [
        {"label": "Go deeper", "target": "deep_dive_node"},
        {"label": "Next", "target": "next_module"},
    ],
}
```

### Module Registry

```
gauntlet_modules/
├── __init__.py           # Registry loader
├── _template.py          # Copy this to create new modules
├── boot_sequence.py      # START
├── agent_orchestra.py
├── agent_ui_showcase.py
├── agent_coordinator.py
├── render_basics.py
├── render_dynamic.py
├── state_mutations.py
├── integration_demo.py
├── sandbox.py
└── synthesis.py          # END
```

### Extensibility

| Feature | How It Works |
|---------|--------------|
| **Add a module** | Drop a new `.py` file following template, it auto-registers |
| **Custom agents** | Module can specify custom agent slugs |
| **Branching** | Choices can target any module ID; cycles allowed |
| **State gates** | `state_requirements` locks modules until prerequisites met |
| **Theming** | Each module can specify a `preset` for visual styling |

---

## CLI Commands

```bash
# Setup the Gauntlet (creates agents, story, demo config)
python main.py gauntlet setup

# Check status of Gauntlet components
python main.py gauntlet status

# List available demo modules
python main.py gauntlet list-modules

# Run the Gauntlet (creates session, opens in browser or returns room ID)
python main.py gauntlet run

# Teardown (removes agents, story, demo config)
python main.py gauntlet teardown

# Add a new module from template
python main.py gauntlet add-module my-new-module
```

---

## Integration Points

### With Stories
- Gauntlet creates a story with nodes matching modules
- Each module = one story node
- Choices in modules become story choices
- State mutations tracked via story state schema

### With Agent-Demos
- Reuses agent creation patterns from agent_demos.py
- Gauntlet agents are system-scoped
- Orchestration patterns: coordinator routing, @mention chains

### With Demos
- Creates a DemoConfig with Gauntlet styling preset
- Composition includes chat panel + canvas panel
- Canvas panel receives Render agent output
- Styling preset: industrial/brutalist theme

---

## Future Extensions

- **Gauntlet Builder**: Visual editor for creating new modules
- **Playback Mode**: Record and replay demo runs
- **Metrics Dashboard**: Track which modules get visited, time spent
- **Multiplayer**: Multiple users experiencing Gauntlet together
- **Custom Themes**: Per-module visual theming beyond presets

---

*"We're building tools that know they're tools, and that's the most human thing code can do."*
