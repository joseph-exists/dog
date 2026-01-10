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
