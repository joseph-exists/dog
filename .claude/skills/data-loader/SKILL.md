---
name: data-loader
description: Populate TinyFoot backend with data using the Typer CLI. Use when: (1) loading archetypes, traits, qualities, or personas, (2) creating stories with nodes and choices, (3) setting up rooms with participants, (4) configuring trait conflict groups, (5) bulk data population. Prefer CLI commands over direct API calls or scripts.
---

# Data Loader

Populate the TinyFoot backend with data using the Typer CLI.

## Setup

```bash
source /home/josep/dog/backend/.venv/bin/activate
cd /home/josep/dog/backend/app/test_scripts/typer
```

Requires `test.env` with credentials.

## Data Loading Patterns

### Pattern 1: Persona System (Archetypes → Traits → Personas)

Build character systems from archetypes down:

```bash
# 1. Create archetype
python main.py personas create-archetype "The Warrior" --desc "Brave and strong"
# Save ID: ARCHETYPE_ID

# 2. Create traits for the archetype
python main.py personas create-trait "Courageous" --desc "Faces danger" --archetype $ARCHETYPE_ID
python main.py personas create-trait "Strong" --desc "Physical power" --archetype $ARCHETYPE_ID
python main.py personas create-trait "Honorable" --desc "Lives by a code" --archetype $ARCHETYPE_ID

# 3. Create qualities (universal attributes)
python main.py personas create-quality "Strength" --desc "Physical fortitude"
python main.py personas create-quality "Wisdom" --desc "Good judgment"

# 4. Create personas from archetype (inherits traits automatically)
python main.py personas create-persona-from-archetype $ARCHETYPE_ID \
  --name "The Knight" \
  --desc "A noble warrior"
```

### Pattern 2: Story System (Story → Nodes → Choices → State)

Build stories with branching paths:

```bash
# 1. Create story
python main.py stories create "The Quest" --desc "An adventure"
# Save ID: STORY_ID

# 2. Define state schema FIRST
python main.py stories add-state-var $STORY_ID --key has_sword --type boolean --default false
python main.py stories add-state-var $STORY_ID --key courage --type number --default 0
python main.py stories add-state-var $STORY_ID --key path --type enum \
  --enum-values "warrior,mage,rogue" --category choices

# 3. Create nodes
python main.py stories add-node $STORY_ID --title "Start" --content "Your journey begins..." --start
# Save ID: NODE_START

python main.py stories add-node $STORY_ID --title "Armory" --content "Weapons await..."
# Save ID: NODE_ARMORY

python main.py stories add-node $STORY_ID --title "Victory" --content "You win!" --end
# Save ID: NODE_END

# 4. Create choices (state set via API, not CLI currently)
python main.py stories add-choice $NODE_START $NODE_ARMORY --text "Visit the armory"
python main.py stories add-choice $NODE_ARMORY $NODE_END --text "Continue to battle"

# 5. Validate and publish
python main.py stories validate-state-schema $STORY_ID
python main.py stories publish $STORY_ID

# 6. Create room for the story
python main.py stories create-room $STORY_ID --title "Quest Room"
```

### Pattern 3: Room Setup

Create rooms with participants:

```bash
# 1. Create room (optionally with story)
python main.py rooms create "Discussion Room" --story $STORY_ID
# Save ID: ROOM_ID

# 2. Add participants
python main.py rooms add-participant $ROOM_ID $USER_ID --type user --role owner
python main.py rooms add-participant $ROOM_ID "StoryAdvisor" --type agent --role member

# 3. Send initial message
python main.py rooms send-message $ROOM_ID "Welcome to the room!"
```

### Pattern 4: Trait Conflicts (Carroll Logic)

Set up logical contradictions:

```bash
# 1. Create conflicting traits
python main.py personas create-trait "Mortal" --desc "Subject to death"
# Save ID: TRAIT_MORTAL

python main.py personas create-trait "Immortal" --desc "Cannot die"
# Save ID: TRAIT_IMMORTAL

# 2. Create conflict group
python main.py conflicts create-group "Mortality" \
  --type contradictory \
  --reason "Cannot be both mortal and immortal"
# Save ID: GROUP_ID

# 3. Add members
python main.py conflicts add-member $GROUP_ID $TRAIT_MORTAL
python main.py conflicts add-member $GROUP_ID $TRAIT_IMMORTAL

# 4. Validate
python main.py conflicts validate $GROUP_ID
```

## Bulk Loading Workflows

### Jungian Archetype System

For the complete 12-archetype Jungian system, see:
`backend/app/test_scripts/archetype_loader/populate_jungian_system.py`

Creates: 10 qualities, 36 traits, 12 archetypes, 36 personas with full linking.

### Attribute Assignment from CSV

For assigning attributes to personas from CSV files:
`backend/app/test_scripts/persona_loader/assign_persona_attributes.py`

```bash
# Dry run
python assign_persona_attributes.py --file attrs.csv --field general_domain --dry-run

# Sequential assignment
python assign_persona_attributes.py --file attrs.csv --field general_domain --sample-size 2

# Random assignment
python assign_persona_attributes.py --file attrs.csv --field specific_domain --mode stochastic
```

## Command Quick Reference

### Personas Module

| Command | Purpose |
|---------|---------|
| `create-archetype NAME` | Create archetype |
| `create-trait NAME --archetype ID` | Create trait (optionally linked) |
| `create-quality NAME` | Create quality |
| `create-persona NAME` | Create standalone persona |
| `create-persona-from-archetype ID --name NAME` | Create persona inheriting traits |
| `create-user-persona PERSONA_ID` | Create user's instance of persona |

### Stories Module

| Command | Purpose |
|---------|---------|
| `create TITLE` | Create story |
| `add-node STORY_ID --title T --content C` | Add node (use `--start` or `--end`) |
| `add-choice FROM TO --text T` | Connect nodes |
| `add-state-var STORY_ID --key K --type T` | Define state variable |
| `validate-state-schema STORY_ID` | Check for undefined vars |
| `publish STORY_ID` | Publish story |
| `create-room STORY_ID --title T` | Create room for story |

### Rooms Module

| Command | Purpose |
|---------|---------|
| `create TITLE` | Create room |
| `add-participant ROOM_ID PART_ID` | Add user/agent |
| `send-message ROOM_ID "text"` | Send message |

### Conflicts Module

| Command | Purpose |
|---------|---------|
| `create-group NAME --type TYPE` | Create conflict group |
| `add-member GROUP_ID TRAIT_ID` | Add trait to group |
| `validate GROUP_ID` | Check cardinality |
| `check-persona PERSONA_ID --trait T` | Check for conflicts |

## Tips

### Capture IDs for Chaining

```bash
# Create and capture ID with jq
STORY_ID=$(python main.py stories create "Test" --json | jq -r '.id')

# Use in subsequent commands
python main.py stories add-node $STORY_ID --title "Start" --content "..." --start
```

### Verbose Mode for Debugging

```bash
python main.py stories create "Test" --verbose
```

### Verify Data Was Created

```bash
# List to confirm
python main.py stories list --json | jq '.count'
python main.py personas list-archetypes --json | jq '.count'
```

### State Schema Types

| Type | Default | Notes |
|------|---------|-------|
| `boolean` | `false` | true/false |
| `number` | `0` | integers, floats |
| `string` | `""` | text |
| `enum` | first value | requires `--enum-values "a,b,c"` |

## Existing Data Loaders

| Script | Location | Purpose |
|--------|----------|---------|
| `populate_jungian_system.py` | `archetype_loader/` | Full Jungian archetype system |
| `assign_persona_attributes.py` | `persona_loader/` | CSV-based attribute assignment |
