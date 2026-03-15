# TinyFoot CLI Commands

Quick reference for available commands in the TinyFoot CLI.

## Story Commands

All story management operations for creating and managing CYOA stories.

### Create Story

```bash
python main.py stories create "Story Title" --desc "Description" --verbose
```

**Options:**
- `--desc, -d TEXT` - Story description (optional)
- `--verbose, -v` - Show debug output

**Example:**
```bash
python main.py stories create "The Enchanted Forest" --desc "A mystical adventure story"
```

### List Stories

```bash
python main.py stories list --limit 10 --json
```

**Options:**
- `--limit INTEGER` - Max stories to list (default: 10)
- `--offset INTEGER` - Pagination offset (default: 0)
- `--json` - Output as JSON for scripting

**Example:**
```bash
# Human-readable list
python main.py stories list --limit 5

# JSON output for scripts
python main.py stories list --json
```

### Get Story Details

```bash
python main.py stories get STORY_ID --json
```

**Arguments:**
- `STORY_ID` - The story UUID

**Options:**
- `--json` - Output as JSON

**Example:**
```bash
python main.py stories get abc123-def456-789
```

### Publish Story

```bash
python main.py stories publish STORY_ID --verbose
```

**Arguments:**
- `STORY_ID` - The story UUID to publish

**Options:**
- `--verbose, -v` - Show debug output

**Example:**
```bash
python main.py stories publish abc123-def456-789
```

### Unpublish Story

```bash
python main.py stories unpublish STORY_ID --verbose
```

**Arguments:**
- `STORY_ID` - The story UUID to unpublish

**Options:**
- `--verbose, -v` - Show debug output

### Create New Story Version

```bash
python main.py stories new-version STORY_ID --json
```

**Arguments:**
- `STORY_ID` - The story UUID

**Options:**
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

### Update Story

```bash
python main.py stories update STORY_ID --title "New Title" --desc "New desc"
```

**Arguments:**
- `STORY_ID` - The story UUID

**Options:**
- `--title TEXT` - New story title
- `--desc, -d TEXT` - New story description
- `--content-format TEXT` - Content format (e.g. text, markdown)
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

### Delete Story

```bash
python main.py stories delete STORY_ID --force
```

**Arguments:**
- `STORY_ID` - The story UUID

**Options:**
- `--force, -f` - Skip confirmation prompt

### Add Node

```bash
python main.py stories add-node STORY_ID --title "Node Title" --content "Node content..." --start
```

**Arguments:**
- `STORY_ID` - The story UUID

**Options:**
- `--title, -t TEXT` - Node title (required)
- `--content, -c TEXT` - Node content (required)
- `--version, -V INTEGER` - Story version (default: 1)
- `--node-type TEXT` - Node type tag (optional)
- `--content-format TEXT` - Content format (e.g. text, markdown)
- `--start` - Mark as start node
- `--end` - Mark as end node
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

**Example:**
```bash
# Add start node
python main.py stories add-node abc123 \
  --title "Forest Entrance" \
  --content "You stand at the entrance of a dark forest..." \
  --start --node-type "text" --content-format "text"

# Add regular node
python main.py stories add-node abc123 \
  --title "The Clearing" \
  --content "You emerge into a moonlit clearing..." --version 2

# Add end node
python main.py stories add-node abc123 \
  --title "Victory" \
  --content "You have successfully completed your quest!" \
  --end
```

### Add Choice

```bash
python main.py stories add-choice FROM_NODE_ID TO_NODE_ID --text "Choice text"
```

**Arguments:**
- `FROM_NODE_ID` - Source node UUID
- `TO_NODE_ID` - Destination node UUID

**Options:**
- `--text, -t TEXT` - Choice text (required)
- `--order, -o INTEGER` - Choice order (default: 0)
- `--requires-state TEXT` - JSON object of required state conditions
- `--sets-state TEXT` - JSON object of state mutations
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

**Example:**
```bash
python main.py stories add-choice node1-uuid node2-uuid \
  --text "Take the shadowy path" \
  --order 0 \
  --requires-state '{"has_sword": true}' \
  --sets-state '{"courage": 1}'

### List Nodes

```bash
python main.py stories list-nodes STORY_ID --version 1 --json
```

**Arguments:**
- `STORY_ID` - The story UUID

**Options:**
- `--version, -v INTEGER` - Story version filter
- `--limit INTEGER` - Max nodes to list (default: 50)
- `--offset INTEGER` - Pagination offset (default: 0)
- `--json` - Output as JSON

### Get Node

```bash
python main.py stories get-node NODE_ID --json
```

**Arguments:**
- `NODE_ID` - The node UUID

**Options:**
- `--json` - Output as JSON

### Update Node

```bash
python main.py stories update-node NODE_ID --title "New Title" --node-type "combat"
```

**Arguments:**
- `NODE_ID` - The node UUID

**Options:**
- `--title, -t TEXT` - Node title
- `--content, -c TEXT` - Node content
- `--node-type TEXT` - Node type tag
- `--content-format TEXT` - Content format (e.g. text, markdown)
- `--start/--no-start` - Set start node flag
- `--end/--no-end` - Set end node flag
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

### Delete Node

```bash
python main.py stories delete-node NODE_ID --force
```

**Arguments:**
- `NODE_ID` - The node UUID

**Options:**
- `--force, -f` - Skip confirmation prompt

### List Choices

```bash
python main.py stories list-choices --story-id STORY_ID --json
```

**Options:**
- `--story-id TEXT` - Filter by story
- `--node-id TEXT` - Filter by node
- `--limit INTEGER` - Max choices to list (default: 50)
- `--offset INTEGER` - Pagination offset (default: 0)
- `--json` - Output as JSON

### Get Choice

```bash
python main.py stories get-choice CHOICE_ID --json
```

**Arguments:**
- `CHOICE_ID` - The choice UUID

**Options:**
- `--json` - Output as JSON

### Update Choice

```bash
python main.py stories update-choice CHOICE_ID --text "New text" --order 1
```

**Arguments:**
- `CHOICE_ID` - The choice UUID

**Options:**
- `--text, -t TEXT` - Choice text
- `--order, -o INTEGER` - Choice order
- `--to-node-id TEXT` - Destination node ID
- `--requires-state TEXT` - JSON object of required state conditions
- `--sets-state TEXT` - JSON object of state mutations
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

### Delete Choice

```bash
python main.py stories delete-choice CHOICE_ID --force
```

**Arguments:**
- `CHOICE_ID` - The choice UUID

**Options:**
- `--force, -f` - Skip confirmation prompt

### Get Start Node

```bash
python main.py stories start-node STORY_ID --version 1 --json
```

**Arguments:**
- `STORY_ID` - The story UUID

**Options:**
- `--version, -v INTEGER` - Story version filter
- `--json` - Output as JSON
```

### List Rooms for Story

```bash
python main.py stories list-rooms STORY_ID --limit 10 --json
```

**Arguments:**
- `STORY_ID` - The story UUID

**Options:**
- `--limit INTEGER` - Max rooms to list (default: 10)
- `--offset INTEGER` - Pagination offset (default: 0)
- `--json` - Output as JSON for scripting

**Example:**
```bash
# Human-readable list
python main.py stories list-rooms abc123

# JSON output for scripts
python main.py stories list-rooms abc123 --json
```

### Create Room

```bash
python main.py stories create-room STORY_ID --title "Room Title"
```

**Arguments:**
- `STORY_ID` - The story UUID

**Options:**
- `--title, -t TEXT` - Room title (required)
- `--verbose, -v` - Show debug output

**Example:**
```bash
python main.py stories create-room abc123 --title "Adventure Lobby"
```

## State Schema Commands

Commands for managing story state variables (schema definition for `sets_state` and `requires_state` in choices).

### List State Variables

```bash
python main.py stories list-state-vars STORY_ID --version 1 --json
```

**Arguments:**
- `STORY_ID` - The story UUID

**Options:**
- `--version, -v INTEGER` - Story version (default: 1)
- `--json` - Output as JSON for scripting

**Example:**
```bash
# Human-readable list (grouped by category)
python main.py stories list-state-vars abc123

# JSON output
python main.py stories list-state-vars abc123 --json
```

### Add State Variable

```bash
python main.py stories add-state-var STORY_ID --key KEY --type TYPE [OPTIONS]
```

**Arguments:**
- `STORY_ID` - The story UUID

**Options:**
- `--key, -k TEXT` - Variable key/name (required)
- `--type, -t TEXT` - Value type: `boolean`, `number`, `string`, `enum` (required)
- `--default, -d TEXT` - Default value
- `--enum-values, -e TEXT` - Comma-separated enum values (required for enum type)
- `--desc TEXT` - Description
- `--category, -c TEXT` - Category for grouping
- `--version, -v INTEGER` - Story version (default: 1)
- `--verbose` - Show debug output

**Examples:**
```bash
# Boolean variable
python main.py stories add-state-var abc123 --key has_sword --type boolean --default false

# Number variable with category
python main.py stories add-state-var abc123 --key courage --type number --default 0 --category stats

# String variable
python main.py stories add-state-var abc123 --key player_name --type string --default "Adventurer"

# Enum variable
python main.py stories add-state-var abc123 --key faction --type enum \
  --enum-values "rebel,empire,neutral" --default neutral --category alignment
```

### Update State Variable

```bash
python main.py stories update-state-var STORY_ID VAR_ID [OPTIONS]
```

**Arguments:**
- `STORY_ID` - The story UUID
- `VAR_ID` - The variable UUID to update

**Options:**
- `--key, -k TEXT` - New variable key
- `--default, -d TEXT` - New default value
- `--enum-values, -e TEXT` - New enum values (comma-separated)
- `--desc TEXT` - New description
- `--category, -c TEXT` - New category
- `--version, -v INTEGER` - Story version (default: 1)
- `--verbose` - Show debug output

**Example:**
```bash
# Update description
python main.py stories update-state-var abc123 var456 --desc "Player's courage level (0-100)"

# Update default and category
python main.py stories update-state-var abc123 var456 --default 50 --category "attributes"

# Add enum option
python main.py stories update-state-var abc123 var456 --enum-values "easy,medium,hard,nightmare"
```

### Delete State Variable

```bash
python main.py stories delete-state-var STORY_ID VAR_ID
```

**Arguments:**
- `STORY_ID` - The story UUID
- `VAR_ID` - The variable UUID to delete

**Options:**
- `--version, -v INTEGER` - Story version (default: 1)
- `--force, -f` - Skip confirmation prompt

**Example:**
```bash
# With confirmation
python main.py stories delete-state-var abc123 var456

# Skip confirmation
python main.py stories delete-state-var abc123 var456 --force
```

### Validate State Schema

```bash
python main.py stories validate-state-schema STORY_ID --version 1
```

Checks for undefined variables in choices. Use this before publishing to ensure all state variables used in `sets_state` and `requires_state` are properly defined in the schema.

**Arguments:**
- `STORY_ID` - The story UUID

**Options:**
- `--version, -v INTEGER` - Story version (default: 1)
- `--json` - Output as JSON for scripting

**Exit Codes:**
- `0` - Valid (all variables defined)
- `1` - Invalid (undefined variables found)

**Example:**
```bash
# Human-readable validation report
python main.py stories validate-state-schema abc123

# JSON output for CI/CD
python main.py stories validate-state-schema abc123 --json

# Check specific version
python main.py stories validate-state-schema abc123 --version 2
```

## Story Requirements Commands

### List Requirements

```bash
python main.py stories list-requirements STORY_ID --json
```

**Arguments:**
- `STORY_ID` - The story UUID

**Options:**
- `--json` - Output as JSON

### Add Requirement

```bash
python main.py stories add-requirement STORY_ID --type quality --target-id UUID --desc "Optional"
```

**Arguments:**
- `STORY_ID` - The story UUID

**Options:**
- `--type, -t TEXT` - Requirement type
- `--target-id TEXT` - Target UUID
- `--desc, -d TEXT` - Requirement description
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

### Delete Requirement

```bash
python main.py stories delete-requirement STORY_ID REQUIREMENT_ID --force
```

**Arguments:**
- `STORY_ID` - The story UUID
- `REQUIREMENT_ID` - The requirement UUID

**Options:**
- `--force, -f` - Skip confirmation prompt

## Story Progress Commands

Use these to play/test stories and inspect state transitions.

### List Progress

```bash
python main.py stories list-progress USER_PERSONA_ID --json
```

**Arguments:**
- `USER_PERSONA_ID` - The user persona UUID

**Options:**
- `--limit INTEGER` - Max items to list (default: 20)
- `--offset INTEGER` - Pagination offset (default: 0)
- `--json` - Output as JSON

### Get Progress

```bash
python main.py stories get-progress USER_PERSONA_ID STORY_ID --json
```

### Create Progress

```bash
python main.py stories create-progress USER_PERSONA_ID STORY_ID
```

### Update Progress (Admin/Debug)

```bash
python main.py stories update-progress USER_PERSONA_ID STORY_ID \
  --story-state '{"has_key": true}' --head-version 3
```

### Current Node

```bash
python main.py stories current-node USER_PERSONA_ID STORY_ID --json
```

### Make Choice

```bash
python main.py stories make-choice USER_PERSONA_ID STORY_ID CHOICE_ID
```

### Validate State

```bash
python main.py stories validate-state USER_PERSONA_ID STORY_ID --json
```

### Undo / Jump

```bash
python main.py stories undo USER_PERSONA_ID STORY_ID
python main.py stories jump USER_PERSONA_ID STORY_ID --expected-head-version 3 --choice-id CHOICE_ID
```

### Timeline / Snapshots

```bash
python main.py stories timeline USER_PERSONA_ID STORY_ID --json
python main.py stories snapshots USER_PERSONA_ID STORY_ID --json
python main.py stories create-snapshot USER_PERSONA_ID STORY_ID
```

**Sample Output (Invalid):**
```
🔍 State Schema Validation (v1):

  ❌ INVALID - Undefined variables found!

  Defined Variables (2):
    • has_sword
    • courage

  Used in Choices (4):
    ✓ has_sword
    ✓ courage
    ✗ undefined_var
    ✗ missing_flag

  ⚠️  Undefined Variables (2):
    • undefined_var
    • missing_flag

  Errors (2):
    • 'undefined_var' in sets_state
      Choice: "Take the mysterious path..."
      Node: Forest Entrance
    • 'missing_flag' in requires_state
      Choice: "Enter the cave..."
      Node: Dark Cave
```

## Persona & Character Commands

Manage archetypes, traits, qualities, personas, and user-personas.

### Create Archetype

```bash
python main.py personas create-archetype "Archetype Name" --desc "Description"
```

**Options:**
- `--desc, -d TEXT` - Archetype description (optional)
- `--verbose, -v` - Show debug output

**Example:**
```bash
python main.py personas create-archetype "The Warrior" --desc "Brave and strong"
```

### List Archetypes

```bash
python main.py personas list-archetypes --limit 20
```

**Options:**
- `--limit INTEGER` - Max archetypes to list (default: 20)
- `--offset INTEGER` - Pagination offset (default: 0)
- `--json` - Output as JSON

### Create Trait

```bash
python main.py personas create-trait "Trait Name" --desc "Description"
```

**Options:**
- `--desc, -d TEXT` - Trait description (optional)
- `--archetype, -a TEXT` - Archetype ID to associate with (optional)
- `--verbose, -v` - Show debug output

**Example:**
```bash
python main.py personas create-trait "Brave" --desc "Faces danger without fear"
python main.py personas create-trait "Analytical" --archetype abc123
```

### List Traits

```bash
python main.py personas list-traits --limit 50
```

**Options:**
- `--limit INTEGER` - Max traits to list (default: 50)
- `--offset INTEGER` - Pagination offset (default: 0)
- `--json` - Output as JSON

### Create Quality

```bash
python main.py personas create-quality "Quality Name" --desc "Description"
```

**Options:**
- `--desc, -d TEXT` - Quality description (optional)
- `--verbose, -v` - Show debug output

**Example:**
```bash
python main.py personas create-quality "Strength" --desc "Physical power"
```

### List Qualities

```bash
python main.py personas list-qualities --limit 20
```

**Options:**
- `--limit INTEGER` - Max qualities to list (default: 20)
- `--offset INTEGER` - Pagination offset (default: 0)
- `--json` - Output as JSON

### Create Persona

```bash
python main.py personas create-persona "Persona Name" --desc "Description"
```

**Options:**
- `--desc, -d TEXT` - Persona description (optional)
- `--verbose, -v` - Show debug output

**Example:**
```bash
python main.py personas create-persona "The Wanderer" --desc "A lone traveler"
```

### Create Persona from Archetype

```bash
python main.py personas create-persona-from-archetype ARCHETYPE_ID --name "Persona Name"
```

**Arguments:**
- `ARCHETYPE_ID` - The archetype UUID to inherit traits from

**Options:**
- `--name, -n TEXT` - Persona name (required)
- `--desc, -d TEXT` - Persona description (optional)
- `--long-desc, -l TEXT` - Long description (optional)
- `--verbose, -v` - Show debug output

**Example:**
```bash
python main.py personas create-persona-from-archetype abc123 \
  --name "The Sage" \
  --desc "Seeks wisdom and truth" \
  --long-desc "A wise character who values knowledge above all else"
```

### List Personas

```bash
python main.py personas list-personas --limit 50
```

**Options:**
- `--limit INTEGER` - Max personas to list (default: 50)
- `--offset INTEGER` - Pagination offset (default: 0)
- `--json` - Output as JSON

### Get Persona

```bash
python main.py personas get-persona PERSONA_ID
```

**Arguments:**
- `PERSONA_ID` - The persona UUID

**Options:**
- `--json` - Output as JSON

**Example:**
```bash
python main.py personas get-persona abc123
```

### Create User-Persona

```bash
python main.py personas create-user-persona PERSONA_ID
```

**Arguments:**
- `PERSONA_ID` - The persona template UUID

**Options:**
- `--verbose, -v` - Show debug output

**Example:**
```bash
# Create a user-persona from a template
python main.py personas create-user-persona abc123
```

### List User-Personas

```bash
python main.py personas list-user-personas --limit 50
```

**Options:**
- `--limit INTEGER` - Max user-personas to list (default: 50)
- `--offset INTEGER` - Pagination offset (default: 0)
- `--json` - Output as JSON

**Example:**
```bash
python main.py personas list-user-personas
```

### Get User-Persona

```bash
python main.py personas get-user-persona USER_PERSONA_ID
```

**Arguments:**
- `USER_PERSONA_ID` - The user-persona UUID

**Options:**
- `--json` - Output as JSON

**Example:**
```bash
python main.py personas get-user-persona abc123
```

## Room Commands

Manage chat rooms, participants, and messages.

### Create Room

```bash
python main.py rooms create "Room Title" --story abc123
```

**Arguments:**
- `TITLE` - Room title

**Options:**
- `--story, -s TEXT` - Story ID to associate with room (optional)
- `--verbose, -v` - Show debug output

**Example:**
```bash
python main.py rooms create "Adventure Room"
python main.py rooms create "Story Discussion" --story abc123
```

### List Rooms

```bash
python main.py rooms list --limit 20
```

**Options:**
- `--limit INTEGER` - Max rooms to list (default: 20)
- `--offset INTEGER` - Pagination offset (default: 0)
- `--json` - Output as JSON

**Example:**
```bash
python main.py rooms list --limit 10
```

### Get Room

```bash
python main.py rooms get ROOM_ID
```

**Arguments:**
- `ROOM_ID` - The room UUID

**Options:**
- `--json` - Output as JSON

**Example:**
```bash
python main.py rooms get abc123
```

### Update Room

```bash
python main.py rooms update ROOM_ID --title "New Title"
```

**Arguments:**
- `ROOM_ID` - The room UUID

**Options:**
- `--title, -t TEXT` - New room title (required)
- `--verbose, -v` - Show debug output

**Example:**
```bash
python main.py rooms update abc123 --title "Updated Room Name"
```

### Delete Room

```bash
python main.py rooms delete ROOM_ID
```

**Arguments:**
- `ROOM_ID` - The room UUID

**Options:**
- `--force, -f` - Skip confirmation prompt

**Example:**
```bash
python main.py rooms delete abc123
python main.py rooms delete abc123 --force
```

### Add Participant

```bash
python main.py rooms add-participant ROOM_ID PARTICIPANT_ID --type TYPE --role ROLE
```

**Arguments:**
- `ROOM_ID` - The room UUID
- `PARTICIPANT_ID` - User ID or agent name

**Options:**
- `--type, -t TEXT` - Participant type: `user` or `agent` (default: user)
- `--role, -r TEXT` - Role: `owner`, `member`, or `observer` (default: member)
- `--verbose, -v` - Show debug output

**Example:**
```bash
# Add user as member
python main.py rooms add-participant abc123 user456 --type user --role member

# Add agent as member
python main.py rooms add-participant abc123 StoryAdvisor --type agent --role member

# Add user as owner
python main.py rooms add-participant abc123 user789 --type user --role owner
```

### List Participants

```bash
python main.py rooms list-participants ROOM_ID
```

**Arguments:**
- `ROOM_ID` - The room UUID

**Options:**
- `--json` - Output as JSON

**Example:**
```bash
python main.py rooms list-participants abc123
```

### Change Participant Role

```bash
python main.py rooms change-role ROOM_ID PARTICIPANT_ID NEW_ROLE
```

**Arguments:**
- `ROOM_ID` - The room UUID
- `PARTICIPANT_ID` - Participant ID
- `NEW_ROLE` - New role: `owner`, `member`, or `observer`

**Options:**
- `--verbose, -v` - Show debug output

**Example:**
```bash
python main.py rooms change-role abc123 user456 owner
```

### Remove Participant

```bash
python main.py rooms remove-participant ROOM_ID PARTICIPANT_ID
```

**Arguments:**
- `ROOM_ID` - The room UUID
- `PARTICIPANT_ID` - Participant ID

**Options:**
- `--force, -f` - Skip confirmation prompt

**Example:**
```bash
python main.py rooms remove-participant abc123 user456
python main.py rooms remove-participant abc123 user456 --force
```

### Send Message

```bash
python main.py rooms send-message ROOM_ID "Message content"
```

**Arguments:**
- `ROOM_ID` - The room UUID
- `CONTENT` - Message content

**Options:**
- `--verbose, -v` - Show debug output

**Example:**
```bash
python main.py rooms send-message abc123 "Hello, everyone!"
```

### List Messages

```bash
python main.py rooms list-messages ROOM_ID --limit 20
```

**Arguments:**
- `ROOM_ID` - The room UUID

**Options:**
- `--limit INTEGER` - Max messages to list (default: 20)
- `--before TEXT` - Cursor: messages before this timestamp (for pagination)
- `--json` - Output as JSON

**Example:**
```bash
python main.py rooms list-messages abc123 --limit 10
python main.py rooms list-messages abc123 --before "2024-01-01T12:00:00"
```

## Room Runtime Commands

These mirror the room runtime endpoints used for shared story runs.

### Read Runtime

```bash
python main.py rooms runtime-get ROOM_ID --json
```

### Initialize Runtime

```bash
python main.py rooms runtime-put ROOM_ID --user-persona-id USER_PERSONA_ID --story-version 2
```

### Advance / Rewind / Reset

```bash
python main.py rooms runtime-advance ROOM_ID --choice-id CHOICE_ID
python main.py rooms runtime-rewind ROOM_ID --target-choice-id CHOICE_ID
python main.py rooms runtime-reset ROOM_ID
```

## Agent Commands

Manage agent configurations in the agent registry system. Supports full CRUD operations with tiered access control (personal vs system scope).

### List Agents

```bash
python main.py agents list --scope system --limit 20
```

List all agent configurations. Users see system agents + their own personal agents. Admins see all.

**Options:**
- `--scope, -s TEXT` - Filter by scope: `system` or `personal`
- `--limit INTEGER` - Max agents to list (default: 20)
- `--skip INTEGER` - Pagination offset (default: 0)
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

**Examples:**
```bash
python main.py agents list
python main.py agents list --scope system
python main.py agents list --scope personal --json
```

### List Available Agents

```bash
python main.py agents list-available
```

List agents available for room participation (enabled system agents only).

**Options:**
- `--json` - Output as JSON

**Examples:**
```bash
python main.py agents list-available
python main.py agents list-available --json
```

### Get Agent

```bash
python main.py agents get AGENT_ID
```

Get detailed agent configuration by UUID.

**Arguments:**
- `AGENT_ID` - The agent UUID

**Options:**
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

**Example:**
```bash
python main.py agents get 550e8400-e29b-41d4-a716-446655440000
```

### Create Agent

```bash
python main.py agents create "Agent Name" agent-slug [OPTIONS]
```

Create a new agent configuration. Users can create personal agents. Only admins can create system agents.

The API uses a discriminated union based on `provider_type`. Different provider types have different required fields.

**Arguments:**
- `NAME` - Display name for the agent
- `SLUG` - Unique identifier/slug

**Options:**
- `--provider, -t TEXT` - Provider type: `openai` (default), `openai_compatible`
- `--desc, -d TEXT` - Agent description (required for openai provider)
- `--prompt, -p TEXT` - System prompt (required for all providers)
- `--model-name TEXT` - Friendly model name (default: "friendly model name")
- `--model-id TEXT` - Model UUID from catalog
- `--scope, -s TEXT` - Scope: `personal` or `system` (default: personal)
- `--mode TEXT` - Participation mode: `always`, `on_mention`, `manual` (default: on_mention)
- `--coordinator/--no-coordinator` - Process messages first (default: no)
- `--max-iterations INTEGER` - Max LLM requests per run (default: 10)
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

**Provider Types:**
| Type | Required Fields | Notes |
|------|-----------------|-------|
| `openai` | `--desc`, `--prompt` | Standard OpenAI provider |
| `openai_compatible` | `--prompt` | OpenAI-compatible APIs (prompt max 5000 chars) |

**Examples:**
```bash
# Create a personal agent (openai provider - default)
python main.py agents create "My Helper" my-helper \
  --desc "A helpful assistant" \
  --prompt "You are a helpful AI assistant."

# Create with openai_compatible provider
python main.py agents create "Local LLM" local-bot \
  --provider openai_compatible \
  --prompt "You are a helpful assistant running locally."

# Create with all options
python main.py agents create "Story Bot" story-bot \
  --provider openai \
  --desc "A creative storyteller" \
  --prompt "You are a creative storytelling assistant..." \
  --mode always \
  --coordinator \
  --max-iterations 20

# Create system agent (admin only)
python main.py agents create "Global Advisor" global-advisor \
  --desc "System-wide advisor" \
  --prompt "You are a wise advisor." \
  --scope system
```

### Update Agent

```bash
python main.py agents update AGENT_ID [OPTIONS]
```

Update an agent configuration. Only provide fields you want to change.

**Arguments:**
- `AGENT_ID` - The agent UUID to update

**Options:**
- `--name, -n TEXT` - New display name
- `--desc, -d TEXT` - New description
- `--model, -m TEXT` - New model name
- `--prompt, -p TEXT` - New system prompt
- `--mode TEXT` - New participation mode
- `--enabled/--disabled` - Enable or disable the agent
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

**Examples:**
```bash
# Update name and description
python main.py agents update abc123 --name "Updated Name" --desc "New description"

# Disable an agent
python main.py agents update abc123 --disabled

# Change model and prompt
python main.py agents update abc123 --model openai:gpt-4o --prompt "New system prompt..."
```

### Delete Agent

```bash
python main.py agents delete AGENT_ID
```

Delete an agent configuration (with confirmation).

**Arguments:**
- `AGENT_ID` - The agent UUID to delete

**Options:**
- `--force, -f` - Skip confirmation prompt
- `--verbose, -v` - Show debug output

**Examples:**
```bash
python main.py agents delete abc123
python main.py agents delete abc123 --force
```

### Enable Agent

```bash
python main.py agents enable AGENT_ID
```

Enable an agent (shortcut for `update --enabled`).

**Arguments:**
- `AGENT_ID` - The agent UUID

**Example:**
```bash
python main.py agents enable abc123
```

### Disable Agent

```bash
python main.py agents disable AGENT_ID
```

Disable an agent (shortcut for `update --disabled`).

**Arguments:**
- `AGENT_ID` - The agent UUID

**Example:**
```bash
python main.py agents disable abc123
```

## LLM Catalog Commands

Manage your LLM provider configurations and browse the model catalog.

**Important Architecture Concepts:**

| Concept | Description |
|---------|-------------|
| **Provider Type** | Catalog entry (e.g., "openai", "anthropic") - system-defined |
| **User Access Provider** | YOUR config with API key linked to a provider type |
| **Model** | Available LLM models (gpt-4o, claude-3-opus) linked to provider types |

### List Provider Types

```bash
python main.py catalog types [OPTIONS]
```

List all available provider types (openai, anthropic, etc.). Use this to find the ID when creating a provider config.

**Options:**
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

**Examples:**
```bash
python main.py catalog types
python main.py catalog types --json
```

### Get Provider Type by UUID

```bash
python main.py catalog type PROVIDER_TYPE_ID [OPTIONS]
```

Get details for a specific provider type by UUID.

**Arguments:**
- `PROVIDER_TYPE_ID` - The provider type UUID

**Options:**
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

**Example:**
```bash
python main.py catalog type 673f1787-8474-4e1c-986c-8e19f14c989c
```

### Get Provider Type by Name

```bash
python main.py catalog type-by-name NAME [OPTIONS]
```

Look up a provider type by name (e.g., "openai", "anthropic").

**Arguments:**
- `NAME` - Provider type name

**Options:**
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

**Examples:**
```bash
python main.py catalog type-by-name openai
python main.py catalog type-by-name anthropic --json
```

### List Your Providers

```bash
python main.py catalog providers [OPTIONS]
```

List your configured LLM providers (your API keys and settings).

**Options:**
- `--limit INTEGER` - Max items to list (default: 50)
- `--skip INTEGER` - Pagination offset
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

**Examples:**
```bash
python main.py catalog providers
python main.py catalog providers --json
```

### Get Your Provider

```bash
python main.py catalog provider PROVIDER_ID [OPTIONS]
```

Get details of your specific provider configuration.

**Arguments:**
- `PROVIDER_ID` - Your provider config UUID

**Options:**
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

**Example:**
```bash
python main.py catalog provider abc123
```

### Create Provider

```bash
python main.py catalog create-provider NAME --type TYPE -k API_KEY [OPTIONS]
```

Create a new LLM provider configuration with your API key. The API key is encrypted at rest.

**Arguments:**
- `NAME` - Friendly name for this config

**Options:**
- `--type, -t TEXT` - Provider type name (e.g., "openai") or UUID **(required)**
- `--api-key, -k TEXT` - API key (will prompt securely if not provided) **(required)**
- `--base-url, -u TEXT` - Custom base URL (for self-hosted/Azure)
- `--desc, -d TEXT` - Description
- `--default/--no-default` - Set as your default provider
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

**Examples:**
```bash
# By provider type name (will look up UUID automatically)
python main.py catalog create-provider "My OpenAI" --type openai -k sk-xxx

# By provider type UUID
python main.py catalog create-provider "My Claude" \
    --type 008dc763-4309-43cd-ba5f-1eb1323a0964 -k sk-xxx

# With custom endpoint (for Azure, self-hosted, etc.)
python main.py catalog create-provider "Azure OpenAI" \
    --type openai \
    --base-url https://my-resource.openai.azure.com \
    -k xxx

# Interactive API key prompt (more secure - hides input)
python main.py catalog create-provider "My Provider" --type openai
# (will prompt for API key)
```

### Update Provider

```bash
python main.py catalog update-provider PROVIDER_ID [OPTIONS]
```

Update your LLM provider configuration. Only provide fields you want to change.

**Arguments:**
- `PROVIDER_ID` - Provider config UUID to update

**Options:**
- `--name, -n TEXT` - New name
- `--api-key, -k TEXT` - New API key (will be encrypted)
- `--base-url, -u TEXT` - New base URL
- `--desc, -d TEXT` - New description
- `--enabled/--disabled` - Enable or disable
- `--default/--no-default` - Set as default
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

**Examples:**
```bash
python main.py catalog update-provider abc123 --name "Renamed Provider"
python main.py catalog update-provider abc123 --api-key NEW_KEY
python main.py catalog update-provider abc123 --disabled
python main.py catalog update-provider abc123 --default
```

### Delete Provider

```bash
python main.py catalog delete-provider PROVIDER_ID [OPTIONS]
```

Delete your LLM provider configuration. ⚠️ This also deletes the stored API key!

**Arguments:**
- `PROVIDER_ID` - Provider config UUID to delete

**Options:**
- `--force, -f` - Skip confirmation prompt
- `--verbose, -v` - Show debug output

**Examples:**
```bash
python main.py catalog delete-provider abc123
python main.py catalog delete-provider abc123 --force
```

### List All Models

```bash
python main.py catalog models [OPTIONS]
```

List all available LLM models in the catalog.

**Options:**
- `--limit INTEGER` - Max items to list (default: 100)
- `--skip INTEGER` - Pagination offset
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

**Examples:**
```bash
python main.py catalog models
python main.py catalog models --limit 20
python main.py catalog models --json
```

### List Models for Your Provider

```bash
python main.py catalog provider-models PROVIDER_ID [OPTIONS]
```

List models compatible with one of your configured providers.

**Arguments:**
- `PROVIDER_ID` - Your provider config UUID

**Options:**
- `--limit INTEGER` - Max items to list (default: 100)
- `--skip INTEGER` - Pagination offset
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

**Examples:**
```bash
python main.py catalog provider-models abc123
python main.py catalog provider-models abc123 --json
```

### Get Model Details

```bash
python main.py catalog model MODEL_UUID [OPTIONS]
```

Get detailed information about a specific model.

**Arguments:**
- `MODEL_UUID` - Model UUID from catalog

**Options:**
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

**Examples:**
```bash
python main.py catalog model <uuid>
python main.py catalog model <uuid> --json
```

---

## Model Admin Commands (Superuser Only)

These commands modify the model catalog and require superuser privileges. Regular users will receive 403 Forbidden errors.

### Create Model

```bash
python main.py catalog create-model MODEL_ID DISPLAY_NAME --provider TYPE [OPTIONS]
```

Create a new LLM model in the catalog.

**Arguments:**
- `MODEL_ID` - Model identifier as the API expects (e.g., 'gpt-4o-mini', 'claude-3-haiku')
- `DISPLAY_NAME` - Human-friendly name (e.g., 'GPT 4o Mini')

**Options:**
- `--provider, -p TEXT` - Provider type name or UUID **(required)**
- `--desc, -d TEXT` - Model description
- `--context, -c INTEGER` - Context window size in tokens
- `--vision/--no-vision` - Supports image input
- `--tools/--no-tools` - Supports function calling
- `--streaming/--no-streaming` - Supports streaming
- `--json-mode/--no-json-mode` - Supports JSON output mode
- `--default/--no-default` - Mark as default (cheapest) model for provider
- `--enabled/--disabled` - Enable or disable (default: enabled)
- `--sort, -s INTEGER` - Sort order within provider (lower = first)
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

**Examples:**
```bash
# Create a basic model
python main.py catalog create-model gpt-4o-mini "GPT 4o Mini" --provider openai

# Create with full capabilities
python main.py catalog create-model claude-3-5-sonnet "Claude 3.5 Sonnet" \
    --provider anthropic \
    --desc "Most intelligent Claude model" \
    --context 200000 \
    --vision \
    --tools \
    --streaming \
    --json-mode

# Create as default model for provider
python main.py catalog create-model gpt-4o-mini "GPT 4o Mini" \
    --provider openai \
    --default \
    --desc "Fast and affordable"
```

### Update Model

```bash
python main.py catalog update-model MODEL_UUID [OPTIONS]
```

Update an existing LLM model. Only provide fields you want to change.

**Arguments:**
- `MODEL_UUID` - Model UUID to update

**Options:**
- `--model-id TEXT` - New model identifier
- `--name, -n TEXT` - New display name
- `--desc, -d TEXT` - New description
- `--context, -c INTEGER` - New context window size
- `--vision/--no-vision` - Update vision capability
- `--tools/--no-tools` - Update function calling capability
- `--streaming/--no-streaming` - Update streaming capability
- `--json-mode/--no-json-mode` - Update JSON mode capability
- `--default/--no-default` - Set as default
- `--enabled/--disabled` - Enable or disable
- `--deprecated/--not-deprecated` - Mark as deprecated
- `--sort, -s INTEGER` - New sort order
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

**Examples:**
```bash
# Update display name
python main.py catalog update-model <uuid> --name "GPT 4o (Latest)"

# Add capabilities
python main.py catalog update-model <uuid> --vision --tools

# Deprecate a model (still works but shows warning)
python main.py catalog update-model <uuid> --deprecated

# Disable a model (no longer available)
python main.py catalog update-model <uuid> --disabled
```

### Delete Model

```bash
python main.py catalog delete-model MODEL_UUID [OPTIONS]
```

Delete an LLM model from the catalog.

⚠️ **Warning:** This is permanent and may affect agents using this model!

**Arguments:**
- `MODEL_UUID` - Model UUID to delete

**Options:**
- `--force, -f` - Skip confirmation prompt
- `--verbose, -v` - Show debug output

**Examples:**
```bash
python main.py catalog delete-model <uuid>
python main.py catalog delete-model <uuid> --force
```

### Enable Model

```bash
python main.py catalog enable-model MODEL_UUID
```

Enable a model (shortcut for `update-model --enabled`).

### Disable Model

```bash
python main.py catalog disable-model MODEL_UUID
```

Disable a model (shortcut for `update-model --disabled`).

### Deprecate Model

```bash
python main.py catalog deprecate-model MODEL_UUID
```

Mark a model as deprecated. Deprecated models still work but show warnings.

---

## Bulk Import/Export & Search Commands (Superuser Only)

Commands for managing the model catalog at scale. Import from CSV, export for backup, and search/filter models.

### Export Models to CSV

```bash
python main.py catalog export-models [OUTPUT_FILE] [OPTIONS]
```

Export the model catalog to CSV format for backup or editing.

**Arguments:**
- `OUTPUT_FILE` - Output filename (default: llm_models_export.csv)

**Options:**
- `--provider, -p TEXT` - Filter by provider name (openai, anthropic, etc.)
- `--enabled-only` - Only export enabled models
- `--verbose, -v` - Show debug output

**CSV Columns:**
`model_id`, `display_name`, `description`, `provider_name`, `context_window`, `supports_vision`, `supports_tools`, `supports_streaming`, `supports_json_mode`, `is_default`, `is_enabled`, `is_deprecated`, `sort_order`

**Examples:**
```bash
# Export all models
python main.py catalog export-models

# Export to specific file
python main.py catalog export-models backup_2024.csv

# Export only OpenAI models
python main.py catalog export-models openai_models.csv --provider openai

# Export only enabled models
python main.py catalog export-models active_models.csv --enabled-only
```

### Import Models from CSV

```bash
python main.py catalog import-models CSV_FILE [OPTIONS]
```

Import models from CSV file. Supports dry-run mode to preview changes before applying.

**Arguments:**
- `CSV_FILE` - Path to CSV file to import

**Options:**
- `--dry-run` - Preview changes without applying them
- `--update/--no-update` - Update existing models (default: skip existing)
- `--verbose, -v` - Show debug output

**Behavior:**
- **New models**: Created with all specified fields
- **Existing models** (by `model_id` + `provider`):
  - `--no-update` (default): Skipped with warning
  - `--update`: Updated with new values from CSV

**CSV Format:**
Same columns as export. Provider can be name (e.g., "OpenAI") or UUID.

**Examples:**
```bash
# Preview import (no changes made)
python main.py catalog import-models new_models.csv --dry-run

# Import, skip existing models
python main.py catalog import-models new_models.csv

# Import and update existing models
python main.py catalog import-models updated_models.csv --update

# Verbose mode for troubleshooting
python main.py catalog import-models models.csv --dry-run --verbose
```

**Sample CSV:**
```csv
model_id,display_name,description,provider_name,context_window,supports_vision,supports_tools,supports_streaming,supports_json_mode,is_default,is_enabled,is_deprecated,sort_order
gpt-4o-mini,"GPT 4o Mini","Fast and affordable",OpenAI,128000,true,true,true,true,true,true,false,10
claude-3-haiku,"Claude 3 Haiku","Fast Claude model",Anthropic,200000,true,true,true,true,false,true,false,30
```

### Export Template CSV

```bash
python main.py catalog template [OUTPUT_FILE] [OPTIONS]
```

Generate an empty CSV template with all columns and example rows.

**Arguments:**
- `OUTPUT_FILE` - Output filename (default: llm_models_template.csv)

**Options:**
- `--verbose, -v` - Show debug output

**Example:**
```bash
python main.py catalog template
python main.py catalog template my_models.csv
```

The template includes example rows showing proper formatting for each provider type.

### Search Models

```bash
python main.py catalog search [OPTIONS]
```

Search and filter models with multiple criteria.

**Options:**
- `--query, -q TEXT` - Search in model_id and display_name
- `--provider, -p TEXT` - Filter by provider name
- `--vision/--no-vision` - Filter by vision capability
- `--tools/--no-tools` - Filter by function calling capability
- `--enabled/--disabled` - Filter by enabled status
- `--deprecated/--not-deprecated` - Filter by deprecation status
- `--min-context INTEGER` - Minimum context window size
- `--limit INTEGER` - Max results (default: 50)
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

**Examples:**
```bash
# Search by name
python main.py catalog search --query "gpt"

# Find all vision-capable models
python main.py catalog search --vision

# Find OpenAI models with function calling
python main.py catalog search --provider openai --tools

# Find high-context models (100k+)
python main.py catalog search --min-context 100000

# Find deprecated models
python main.py catalog search --deprecated

# Combine filters
python main.py catalog search --provider anthropic --vision --enabled --min-context 100000

# JSON output for scripting
python main.py catalog search --query "claude" --json | jq '.[] | .display_name'
```

### Catalog Statistics

```bash
python main.py catalog stats [OPTIONS]
```

Show aggregate statistics about the model catalog.

**Options:**
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

**Output includes:**
- Total model count
- Models per provider
- Enabled vs disabled count
- Deprecated model count
- Capability breakdown (vision, tools, streaming, JSON mode)
- Context window statistics (min/max/average)

**Examples:**
```bash
python main.py catalog stats
python main.py catalog stats --json
```

**Sample Output:**
```
📊 LLM Catalog Statistics

  Total Models: 42

  By Provider:
    • OpenAI: 12
    • Anthropic: 8
    • Google: 6
    • Mistral: 4
    • ...

  Status:
    • Enabled: 38
    • Disabled: 4
    • Deprecated: 2

  Capabilities:
    • Vision: 18 (43%)
    • Function Calling: 24 (57%)
    • Streaming: 40 (95%)
    • JSON Mode: 22 (52%)

  Context Windows:
    • Min: 4,096 tokens
    • Max: 2,000,000 tokens
    • Average: 128,000 tokens
```

---

### Typical Workflow

```bash
# 1. See what provider types are available
python main.py catalog types

# 2. Create a provider config with your API key
python main.py catalog create-provider "My OpenAI" --type openai -k sk-xxx --default

# 3. List your configured providers
python main.py catalog providers

# 4. See what models are available for your provider
python main.py catalog provider-models <your-provider-uuid>

# 5. Use a model UUID when creating agents
python main.py agents create "My Agent" my-agent \
    --desc "My agent" \
    --prompt "You are helpful" \
    --model-id <model-uuid>
```

### Admin: Bulk Model Management Workflow

```bash
# 1. Export current catalog for backup
python main.py catalog export-models backup_before_changes.csv

# 2. Check catalog statistics
python main.py catalog stats

# 3. Generate a template to add new models
python main.py catalog template new_models.csv

# 4. Edit new_models.csv with your models...

# 5. Preview import (dry run)
python main.py catalog import-models new_models.csv --dry-run

# 6. Import the models
python main.py catalog import-models new_models.csv

# 7. Search to verify models were added
python main.py catalog search --query "new-model-name"

# 8. Export updated catalog for documentation
python main.py catalog export-models catalog_v2.csv
```

### Admin: Model Maintenance Workflow

```bash
# Find deprecated models that need attention
python main.py catalog search --deprecated

# Find disabled models
python main.py catalog search --disabled

# Update models from edited CSV (updates existing, adds new)
python main.py catalog import-models updated_models.csv --update --dry-run
python main.py catalog import-models updated_models.csv --update

# Export provider-specific catalog
python main.py catalog export-models openai_only.csv --provider openai
```

## User Commands

Get information about the current user and their associated data.

### Current User Info

```bash
python main.py users me
```

Shows detailed information about the current authenticated user, including email, full name, and account status.

**Options:**
- `--json` - Output as JSON

**Example:**
```bash
python main.py users me
python main.py users me --json
```

### Quick User Identification

```bash
python main.py users whoami
```

Quick command to show just the current user's email and ID.

**Example:**
```bash
python main.py users whoami
```

### My Rooms

```bash
python main.py users my-rooms --limit 10
```

List all rooms where the current user is a participant.

**Options:**
- `--limit INTEGER` - Max rooms to list (default: 10)
- `--offset INTEGER` - Pagination offset (default: 0)
- `--json` - Output as JSON

**Example:**
```bash
python main.py users my-rooms
python main.py users my-rooms --limit 20 --json
```

### My User-Personas

```bash
python main.py users my-personas
```

List all user-personas belonging to the current user.

**Options:**
- `--limit INTEGER` - Max personas to list (default: 20)
- `--offset INTEGER` - Pagination offset (default: 0)
- `--json` - Output as JSON

**Example:**
```bash
python main.py users my-personas
python main.py users my-personas --json
```

### My Stories

```bash
python main.py users my-stories
```

List all stories created by the current user.

**Options:**
- `--limit INTEGER` - Max stories to list (default: 10)
- `--offset INTEGER` - Pagination offset (default: 0)
- `--json` - Output as JSON

**Example:**
```bash
python main.py users my-stories
python main.py users my-stories --limit 5
```

### My Story Progress

```bash
python main.py users my-progress USER_PERSONA_ID STORY_ID
```

Get the current story progress for a specific user-persona and story combination.

**Arguments:**
- `USER_PERSONA_ID` - The user-persona UUID
- `STORY_ID` - The story UUID

**Options:**
- `--json` - Output as JSON

**Example:**
```bash
python main.py users my-progress persona123 story456
python main.py users my-progress persona123 story456 --json
```

### My Story Timeline

```bash
python main.py users my-timeline USER_PERSONA_ID STORY_ID
```

Get the complete story timeline (history of choices made) for a specific user-persona and story.

**Arguments:**
- `USER_PERSONA_ID` - The user-persona UUID
- `STORY_ID` - The story UUID

**Options:**
- `--json` - Output as JSON

**Example:**
```bash
python main.py users my-timeline persona123 story456
python main.py users my-timeline persona123 story456 --json
```

### User Summary

```bash
python main.py users summary
```

Get an aggregate summary of all user data - stories, personas, rooms, and story progress.

**Options:**
- `--json` - Output as JSON

**Example:**
```bash
python main.py users summary
python main.py users summary --json
```

## Trait Conflict Commands

Commands for managing trait conflict groups for Carroll logic implementation. Supports modeling logical contradictions (contradictory, contrary, subcontrary).

### Create Conflict Group

```bash
python main.py conflicts create-group "Group Name" --type TYPE [OPTIONS]
```

**Arguments:**
- `NAME` - Name of the conflict group

**Options:**
- `--type, -t TEXT` - Conflict type: `contradictory`, `contrary`, `subcontrary` (default: contradictory)
- `--desc, -d TEXT` - Description
- `--reason, -r TEXT` - Explanation of why these traits conflict
- `--traits TEXT` - Comma-separated trait IDs to add as initial members
- `--verbose, -v` - Show debug output

**Conflict Types:**
- `contradictory`: Exactly one must be true (e.g., Mortal/Immortal)
- `contrary`: At most one can be true (e.g., Hot/Warm/Cold)
- `subcontrary`: At least one must be true

**Examples:**
```bash
# Create a contradictory group (binary)
python main.py conflicts create-group "Mortality" --type contradictory \
  --reason "A being cannot be both mortal and immortal"

# Create a contrary group with initial members
python main.py conflicts create-group "Temperature" --type contrary \
  --desc "Temperature states" --traits "trait1,trait2,trait3"
```

### List Conflict Groups

```bash
python main.py conflicts list-groups [OPTIONS]
```

**Options:**
- `--limit INTEGER` - Max groups to list (default: 20)
- `--offset INTEGER` - Pagination offset (default: 0)
- `--type, -t TEXT` - Filter by conflict type
- `--json` - Output as JSON

**Examples:**
```bash
python main.py conflicts list-groups
python main.py conflicts list-groups --type contradictory
python main.py conflicts list-groups --json
```

### Get Conflict Group

```bash
python main.py conflicts get-group GROUP_ID [OPTIONS]
```

**Arguments:**
- `GROUP_ID` - The conflict group UUID

**Options:**
- `--json` - Output as JSON

### Update Conflict Group

```bash
python main.py conflicts update-group GROUP_ID [OPTIONS]
```

**Arguments:**
- `GROUP_ID` - The conflict group UUID

**Options:**
- `--name, -n TEXT` - New name
- `--type, -t TEXT` - New conflict type
- `--desc, -d TEXT` - New description
- `--reason, -r TEXT` - New reason
- `--verbose, -v` - Show debug output

**Example:**
```bash
python main.py conflicts update-group abc123 --name "Updated Name" --reason "New reason"
```

### Delete Conflict Group

```bash
python main.py conflicts delete-group GROUP_ID [OPTIONS]
```

**Arguments:**
- `GROUP_ID` - The conflict group UUID

**Options:**
- `--force, -f` - Skip confirmation prompt

### List Group Members

```bash
python main.py conflicts list-members GROUP_ID [OPTIONS]
```

**Arguments:**
- `GROUP_ID` - The conflict group UUID

**Options:**
- `--json` - Output as JSON

### Add Member to Group

```bash
python main.py conflicts add-member GROUP_ID TRAIT_ID [OPTIONS]
```

**Arguments:**
- `GROUP_ID` - The conflict group UUID
- `TRAIT_ID` - The trait UUID to add

**Options:**
- `--verbose, -v` - Show debug output

**Example:**
```bash
python main.py conflicts add-member group123 trait456
```

### Remove Member from Group

```bash
python main.py conflicts remove-member GROUP_ID TRAIT_ID [OPTIONS]
```

**Arguments:**
- `GROUP_ID` - The conflict group UUID
- `TRAIT_ID` - The trait UUID to remove

**Options:**
- `--force, -f` - Skip confirmation prompt

### Check Persona Conflicts

```bash
python main.py conflicts check-persona PERSONA_ID --trait TRAIT_ID [OPTIONS]
```

Check if adding a trait to a persona would create a logical conflict.

**Arguments:**
- `PERSONA_ID` - The persona UUID

**Options:**
- `--trait, -t TEXT` - Trait ID to check for conflicts (required)
- `--json` - Output as JSON

**Exit Codes:**
- `0` - No conflicts (safe to add trait)
- `1` - Conflicts detected

**Example:**
```bash
python main.py conflicts check-persona persona123 --trait trait456
```

### Check Archetype Conflicts

```bash
python main.py conflicts check-archetype ARCHETYPE_ID --trait TRAIT_ID [OPTIONS]
```

Check if adding a trait to an archetype would create a logical conflict.

**Arguments:**
- `ARCHETYPE_ID` - The archetype UUID

**Options:**
- `--trait, -t TEXT` - Trait ID to check for conflicts (required)
- `--json` - Output as JSON

### Find Groups by Trait

```bash
python main.py conflicts by-trait TRAIT_ID [OPTIONS]
```

Get all conflict groups containing a specific trait.

**Arguments:**
- `TRAIT_ID` - The trait UUID

**Options:**
- `--json` - Output as JSON

**Example:**
```bash
python main.py conflicts by-trait trait123
```

### Validate Group Cardinality

```bash
python main.py conflicts validate GROUP_ID [OPTIONS]
```

Validate that a conflict group has appropriate member count for its type.

**Arguments:**
- `GROUP_ID` - The conflict group UUID

**Options:**
- `--json` - Output as JSON

**Exit Codes:**
- `0` - Valid
- `1` - Invalid (wrong member count for type)

**Example:**
```bash
python main.py conflicts validate abc123
```

## Page Layout Commands

Commands for managing persisted page layouts for entities.

### List Pages

```bash
python main.py pages list [OPTIONS]
```

Search persisted page layouts with filtering.

**Options:**
- `--type, -t TEXT` - Filter by entity type
- `--entity-id, -e TEXT` - Filter by entity ID
- `--type-prefix TEXT` - Filter by entity type prefix
- `--id-prefix TEXT` - Filter by entity ID prefix
- `--limit INTEGER` - Maximum items to list (default: 20)
- `--skip INTEGER` - Pagination offset (default: 0)
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

**Examples:**
```bash
python main.py pages list
python main.py pages list --type story
python main.py pages list --type-prefix room --json
```

### Get Page Layout

```bash
python main.py pages get ENTITY_TYPE ENTITY_ID [OPTIONS]
```

Get the page layout for a specific entity.

**Arguments:**
- `ENTITY_TYPE` - Entity type (e.g. 'story', 'room')
- `ENTITY_ID` - Entity ID

**Options:**
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

**Examples:**
```bash
python main.py pages get story abc123
python main.py pages get room def456 --json
```

### Upsert Page Layout

```bash
python main.py pages upsert ENTITY_TYPE ENTITY_ID [OPTIONS]
```

Create or overwrite a page layout for an entity.

**Arguments:**
- `ENTITY_TYPE` - Entity type (e.g. 'story', 'room')
- `ENTITY_ID` - Entity ID

**Options:**
- `--file, -f TEXT` - JSON file containing layout_json array
- `--layout, -l TEXT` - Inline JSON string for layout_json
- `--version INTEGER` - Layout version
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

**Examples:**
```bash
python main.py pages upsert story abc123 --file layout.json
python main.py pages upsert room def456 --layout '[{"type":"chat","position":0}]'
```

### Update Page

```bash
python main.py pages update PAGE_ID [OPTIONS]
```

Update an existing page layout by page ID.

**Arguments:**
- `PAGE_ID` - The page UUID

**Options:**
- `--file, -f TEXT` - JSON file containing layout_json array
- `--layout, -l TEXT` - Inline JSON string for layout_json
- `--version INTEGER` - Layout version
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

**Examples:**
```bash
python main.py pages update abc123 --file updated_layout.json
python main.py pages update abc123 --layout '[{"type":"chat","position":1}]'
```

### Delete Page

```bash
python main.py pages delete PAGE_ID [OPTIONS]
```

Delete a persisted page layout.

**Arguments:**
- `PAGE_ID` - The page UUID

**Options:**
- `--force, -f` - Skip confirmation prompt
- `--verbose, -v` - Show debug output

**Examples:**
```bash
python main.py pages delete abc123
python main.py pages delete abc123 --force
```

## Preset Commands

Commands for browsing available panel presets. No authentication required.

### List Presets

```bash
python main.py presets list [OPTIONS]
```

List all available panel presets (system presets).

**Options:**
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

**Examples:**
```bash
python main.py presets list
python main.py presets list --json
python main.py presets list -v
```

### Get Preset

```bash
python main.py presets get PRESET_ID [OPTIONS]
```

Get details of a specific preset.

**Arguments:**
- `PRESET_ID` - The preset ID

**Options:**
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

**Examples:**
```bash
python main.py presets get my-preset
python main.py presets get my-preset --json
```

## Panel Commands

Commands for managing room panel configurations. Supports resolved panels, room defaults, and per-user overrides.

### Get Resolved Panels

```bash
python main.py panels get ROOM_ID [OPTIONS]
```

Get resolved panel configuration for current user. Returns the effective panels based on user override or room/type defaults.

**Arguments:**
- `ROOM_ID` - The room UUID

**Options:**
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

**Examples:**
```bash
python main.py panels get abc123
python main.py panels get abc123 --json
```

### Get Room Default Panels

```bash
python main.py panels get-defaults ROOM_ID [OPTIONS]
```

Get room's default panel configuration (set by owner).

**Arguments:**
- `ROOM_ID` - The room UUID

**Options:**
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

**Examples:**
```bash
python main.py panels get-defaults abc123
python main.py panels get-defaults abc123 --json
```

### Set Room Default Panels

```bash
python main.py panels set-defaults ROOM_ID [OPTIONS]
```

Update room's default panel configuration. Only room owner can modify.

**Arguments:**
- `ROOM_ID` - The room UUID

**Options:**
- `--file, -f TEXT` - JSON file containing panels array
- `--panels, -p TEXT` - Inline JSON string for panels
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

**Examples:**
```bash
python main.py panels set-defaults abc123 --file panels.json
python main.py panels set-defaults abc123 --panels '[{"type":"chat"},{"type":"info"}]'
```

### Get My Panel Config

```bash
python main.py panels my-config ROOM_ID [OPTIONS]
```

Get your panel configuration override for a room.

**Arguments:**
- `ROOM_ID` - The room UUID

**Options:**
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

**Examples:**
```bash
python main.py panels my-config abc123
python main.py panels my-config abc123 --json
```

### Set My Panel Config

```bash
python main.py panels set-my-config ROOM_ID [OPTIONS]
```

Update your panel configuration for a room. Use `--use-defaults` to follow room defaults, or `--custom` with panel data for a personal override.

**Arguments:**
- `ROOM_ID` - The room UUID

**Options:**
- `--use-defaults/--custom` - Use room defaults or custom panels (default: use-defaults)
- `--file, -f TEXT` - JSON file containing panels array
- `--panels, -p TEXT` - Inline JSON string for panels
- `--json` - Output as JSON
- `--verbose, -v` - Show debug output

**Examples:**
```bash
# Use room defaults
python main.py panels set-my-config abc123 --use-defaults

# Set custom panels
python main.py panels set-my-config abc123 --custom --file my_panels.json
python main.py panels set-my-config abc123 --custom --panels '[{"type":"chat"}]'
```

## Demo Commands

Example commands from wonka.py for testing.

### Hello

```bash
python main.py demo hello NAME
```

**Example:**
```bash
python main.py demo hello "World"
```

### Goodbye

```bash
python main.py demo goodbye NAME --formal
```

**Options:**
- `--formal` - Use formal goodbye

**Example:**
```bash
python main.py demo goodbye "Alice" --formal
```

## General Commands

### Version

```bash
python main.py version
```

Shows CLI version information.

### Help

```bash
# Show all commands
python main.py --help

# Show help for specific command group
python main.py stories --help

# Show help for specific command
python main.py stories create --help
```

## Common Patterns

### Creating a Character System

```bash
# 1. Create an archetype
python main.py personas create-archetype "The Warrior" \
  --desc "Brave and strong, faces challenges head-on"

# Save archetype ID, e.g. archetype123

# 2. Create traits for the archetype
python main.py personas create-trait "Brave" \
  --desc "Faces danger without fear" \
  --archetype archetype123

python main.py personas create-trait "Strong" \
  --desc "Possesses great physical power" \
  --archetype archetype123

python main.py personas create-trait "Honorable" \
  --desc "Lives by a code of honor" \
  --archetype archetype123

# 3. Create qualities (universal attributes)
python main.py personas create-quality "Strength" --desc "Physical power"
python main.py personas create-quality "Courage" --desc "Mental fortitude"

# 4. Create personas from the archetype (inherits traits)
python main.py personas create-persona-from-archetype archetype123 \
  --name "The Knight" \
  --desc "A noble warrior who protects the innocent"

python main.py personas create-persona-from-archetype archetype123 \
  --name "The Champion" \
  --desc "A legendary fighter who never backs down"

# Save persona IDs, e.g. persona1, persona2

# 5. Create user-personas for gameplay
python main.py personas create-user-persona persona1
# Save user-persona ID for use in stories, e.g. user_persona123
```

### Creating and Using a Room

```bash
# 1. Create a room (with optional story association)
python main.py rooms create "Adventure Chat" --story story123

# Save room ID, e.g. room123

# 2. Add participants
python main.py rooms add-participant room123 user456 --type user --role member
python main.py rooms add-participant room123 StoryAdvisor --type agent --role member

# 3. List participants
python main.py rooms list-participants room123

# 4. Send messages
python main.py rooms send-message room123 "Welcome to the adventure!"
python main.py rooms send-message room123 "Let's begin our quest"

# 5. View messages
python main.py rooms list-messages room123 --limit 10

# 6. Change participant role (make user an owner)
python main.py rooms change-role room123 user456 owner

# 7. Update room details
python main.py rooms update room123 --title "Epic Adventure Chat"
```

### Creating a Complete Story

```bash
# 1. Create the story
python main.py stories create "The Adventure" --desc "An epic journey"

# Save the story ID from output, e.g. abc123

# 2. Add start node
python main.py stories add-node abc123 \
  --title "The Beginning" \
  --content "Your journey starts here..." \
  --start

# Save node ID, e.g. node1

# 3. Add another node
python main.py stories add-node abc123 \
  --title "The Challenge" \
  --content "You face a difficult choice..."

# Save node ID, e.g. node2

# 4. Connect nodes with a choice
python main.py stories add-choice node1 node2 \
  --text "Begin the adventure"

# 5. Add ending node
python main.py stories add-node abc123 \
  --title "The End" \
  --content "Your journey concludes..." \
  --end

# Save node ID, e.g. node3

# 6. Connect to ending
python main.py stories add-choice node2 node3 \
  --text "Complete the quest"

# 7. Publish the story
python main.py stories publish abc123

# 8. Create a room for the story
python main.py stories create-room abc123 --title "Adventure Room"
```

### Creating a Story with State Schema

```bash
# 1. Create the story
python main.py stories create "The Dragon's Lair" --desc "A branching adventure with state"
# Save story ID: abc123

# 2. Define state variables FIRST (schema)
python main.py stories add-state-var abc123 --key has_sword --type boolean --default false --category inventory
python main.py stories add-state-var abc123 --key courage --type number --default 0 --category stats
python main.py stories add-state-var abc123 --key approach --type enum \
  --enum-values "stealth,combat,diplomacy" --category choices

# 3. Verify schema
python main.py stories list-state-vars abc123

# 4. Add nodes
python main.py stories add-node abc123 --title "Cave Entrance" --content "You stand before the dragon's lair..." --start
# node1

python main.py stories add-node abc123 --title "Armory" --content "An old armory..."
# node2

python main.py stories add-node abc123 --title "Dragon Chamber" --content "The dragon awaits..."
# node3

python main.py stories add-node abc123 --title "Victory" --content "You have succeeded!" --end
# node4

# 5. Add choices with state (using schema-defined variables)
python main.py stories add-choice node1 node2 --text "Search for weapons"
# Note: In the API, you would add sets_state: {"has_sword": true, "courage": 10}

python main.py stories add-choice node2 node3 --text "Enter the chamber"
# Note: In the API, you would add requires_state: {"has_sword": true}

python main.py stories add-choice node3 node4 --text "Face the dragon"
# Note: In the API, you would add requires_state: {"courage": 10}, sets_state: {"approach": "combat"}

# 6. Validate schema before publishing
python main.py stories validate-state-schema abc123

# 7. If valid, publish
python main.py stories publish abc123
```

### CI/CD Validation Workflow

```bash
#!/bin/bash
# pre-publish-check.sh - Run before publishing stories

STORY_ID=$1

# Validate state schema
if ! python main.py stories validate-state-schema $STORY_ID --json > /dev/null 2>&1; then
    echo "❌ State schema validation failed!"
    python main.py stories validate-state-schema $STORY_ID
    exit 1
fi

echo "✅ State schema valid"

# Publish
python main.py stories publish $STORY_ID
```

### Setting Up Carroll Logic Conflicts

Use trait conflicts to model logical contradictions for Carroll-style syllogism stories.

```bash
# 1. Create traits that will conflict
python main.py personas create-trait "Mortal" --desc "Subject to death"
# Save trait ID: mortal_trait

python main.py personas create-trait "Immortal" --desc "Not subject to death"
# Save trait ID: immortal_trait

# 2. Create a contradictory conflict group
python main.py conflicts create-group "Mortality Contradiction" \
  --type contradictory \
  --reason "A being cannot be both mortal and immortal - these are logical contradictories"

# Save group ID: mortality_group

# 3. Add traits to the conflict group
python main.py conflicts add-member $mortality_group $mortal_trait
python main.py conflicts add-member $mortality_group $immortal_trait

# 4. Validate the group has correct cardinality
python main.py conflicts validate $mortality_group
# Should show: VALID (contradictory with 2 members)

# 5. Create an archetype with one of the traits
python main.py personas create-archetype "Humans" --desc "Mortal beings"
# Save archetype ID: humans_archetype

# Note: When adding Mortal trait to Humans archetype via API,
# the conflict check will prevent adding Immortal later

# 6. Check before adding a conflicting trait
python main.py conflicts check-archetype $humans_archetype --trait $immortal_trait
# Should show: CONFLICT DETECTED!

# 7. View all groups a trait participates in
python main.py conflicts by-trait $mortal_trait
```

**Example: Celarent Syllogism Setup (No reptiles are mammals)**

```bash
# Create the conflicting traits
python main.py personas create-trait "Cold-blooded" --desc "Ectothermic metabolism"
python main.py personas create-trait "Warm-blooded" --desc "Endothermic metabolism"

# Create the conflict group
python main.py conflicts create-group "Thermoregulation" \
  --type contradictory \
  --reason "Cold-blooded and warm-blooded are mutually exclusive metabolic strategies"

# Add members and validate
python main.py conflicts add-member $group_id $cold_blooded_id
python main.py conflicts add-member $group_id $warm_blooded_id
python main.py conflicts validate $group_id
```

### JSON Output for Scripting

```bash
# Get story data and parse with jq
python main.py stories get abc123 --json | jq '.title'

# List all published stories
python main.py stories list --json | jq '.data[] | select(.is_published == true)'

# Count total stories
python main.py stories list --json | jq '.count'
```

### Verbose Mode for Debugging

```bash
# See all HTTP requests and responses
python main.py stories create "Test" --verbose
python main.py stories publish abc123 --verbose
```

## Tips

### Saving IDs

When creating resources, save the IDs for later use:

```bash
# Create story and capture ID
python main.py stories create "My Story" --json > story.json
STORY_ID=$(cat story.json | jq -r '.id')

# Use the ID in subsequent commands
python main.py stories add-node $STORY_ID --title "Start" --content "..." --start
```

### Checking Status

```bash
# Check if story exists
python main.py stories get abc123

# List recent stories
python main.py stories list --limit 5
```

### Troubleshooting

```bash
# Test authentication
python auth_helper.py

# Show debug output
python main.py stories create "Test" --verbose

# Get detailed error messages
python main.py stories publish bad-id-here
```

## SVG Commands

Commands for managing and bulk-populating the `/svgs` library with deterministic combinatoric generation.

### List SVG Assets

```bash
python main.py svgs list --limit 25
python main.py svgs list --visibility private --json
```

**Options:**
- `--limit INTEGER` - Max assets to list (default: 50)
- `--skip INTEGER` - Pagination offset (default: 0)
- `--visibility TEXT` - Filter by `private` or `public`
- `--json` - Output as JSON

### Get SVG Asset

```bash
python main.py svgs get SVG_ID
python main.py svgs get SVG_ID --json
```

### Create Private SVG

```bash
# From file
python main.py svgs create-private "grid-wave-01" --svg-file ./my_asset.svg --desc "hero background"

# Inline SVG
python main.py svgs create-private "inline-test" --svg '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"></svg>'
```

**Options:**
- `--svg-file PATH` - Read SVG markup from a file
- `--svg TEXT` - Inline SVG markup (mutually exclusive with `--svg-file`)
- `--desc, -d TEXT` - Optional description
- `--metadata TEXT` - JSON object string for `metadata_json`

### Create Public Copy from Private

```bash
python main.py svgs copy-public PRIVATE_SVG_ID --name "public-grid-wave-01"
```

**Options:**
- `--name TEXT` - Optional display name override
- `--desc TEXT` - Optional description override
- `--metadata TEXT` - JSON object string to override metadata

### Patch SVG Asset

```bash
python main.py svgs patch SVG_ID --name "renamed-asset"
python main.py svgs patch SVG_ID --svg-file ./updated.svg --metadata '{"tag":"v2"}'
python main.py svgs patch SVG_ID --visibility public --source-private-id PRIVATE_SVG_ID
```

### Delete SVG Asset

```bash
python main.py svgs delete SVG_ID --force
```

### Build Generation Plan

```bash
python main.py svgs plan \
  --count 1000 \
  --seed 20260315 \
  --output app/test_scripts/render_things/svg_library_plan.json
```

Produces a deterministic plan with:
- Pairwise core coverage rows
- Style-family quotas (`organic`, `geometric`, `glitch`, `minimal`, `atmospheric`, `diagrammatic`)
- Hero and safe utility tiers

### Seed SVG Library

```bash
# Dry run first (recommended)
python main.py svgs seed --plan app/test_scripts/render_things/svg_library_plan.json --dry-run -v

# Actual population run
python main.py svgs seed \
  --plan app/test_scripts/render_things/svg_library_plan.json \
  --name-prefix svg-lib \
  --public-copy-ratio 0.1 \
  --manifest-out app/test_scripts/render_things/svg_library_seed_report.json
```

**Recommended Batch Sizes**
- Local smoke: `--count 50` to `--count 200`
- Staging population: `--count 500` to `--count 2000`
- Large runs: split into repeated batches and review each manifest before continuing

### SVG Smoke Test Script

```bash
# Local validation only (no API writes)
python app/test_scripts/render_things/test_svg_library_population.py --count 24 --seed 20260315

# Live API smoke (creates, patches, copies, lists, optional cleanup)
python app/test_scripts/render_things/test_svg_library_population.py --post --create-count 5 --cleanup
```

## Authentication

All commands automatically handle authentication using credentials from `test.env`:

```bash
# test.env format
TEST_USER_EMAIL=test@example.com
TEST_USER_PASSWORD=yourpassword
```

Test authentication with:
```bash
python auth_helper.py
```

## Next Steps

See `REFERENCE.md` for:
- How to add new commands
- Advanced patterns
- Error handling
- Testing commands

See `README.md` for:
- Setup instructions
- Development workflow
- Troubleshooting
