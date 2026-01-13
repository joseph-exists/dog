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

### Add Node

```bash
python main.py stories add-node STORY_ID --title "Node Title" --content "Node content..." --start
```

**Arguments:**
- `STORY_ID` - The story UUID

**Options:**
- `--title, -t TEXT` - Node title (required)
- `--content, -c TEXT` - Node content (required)
- `--start` - Mark as start node
- `--end` - Mark as end node
- `--verbose, -v` - Show debug output

**Example:**
```bash
# Add start node
python main.py stories add-node abc123 \
  --title "Forest Entrance" \
  --content "You stand at the entrance of a dark forest..." \
  --start

# Add regular node
python main.py stories add-node abc123 \
  --title "The Clearing" \
  --content "You emerge into a moonlit clearing..."

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
- `--verbose, -v` - Show debug output

**Example:**
```bash
python main.py stories add-choice node1-uuid node2-uuid \
  --text "Take the shadowy path" \
  --order 0
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
