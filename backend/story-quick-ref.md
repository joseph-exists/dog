# Quick Reference Guide - Story System API

## Authoring Endpoints (Story Templates)

### Stories
```http
# List stories
GET /stories?skip=0&limit=10

# Get single story
GET /stories/{story_id}

# Get start node (helper)
GET /stories/{story_id}/start-node

# Create story
POST /stories
{
  "title": "My Adventure",
  "description": "An epic tale"
}

# Update story
PUT /stories/{story_id}
{
  "title": "Updated Title"
}

# Delete story
DELETE /stories/{story_id}
```

### Story Nodes
```http
# List nodes
GET /storynodes?skip=0&limit=100

# Get single node
GET /storynodes/{node_id}

# Create node
POST /storynodes
{
  "story_id": "uuid",
  "story_version": 1,
  "title": "Chapter One",
  "content": "You wake up in a dark forest...",
  "node_type": "text",
  "is_start_node": true,
  "is_end_node": false
}

# Update node
PUT /storynodes/{node_id}
{
  "title": "Chapter One (Revised)"
}

# Delete node
DELETE /storynodes/{node_id}
```

### Node Choices
```http
# List choices for a node
GET /storynodes/{node_id}/choices

# Create choice
POST /storynodes/{node_id}/choices
{
  "from_node_id": "uuid",
  "to_node_id": "uuid",
  "text": "Enter the cave",
  "order": 1,
  "requires_state": {"has_torch": true},
  "sets_state": {"visited_cave": true}
}

# Update choice
PUT /storynodes/{node_id}/choices/{choice_id}
{
  "text": "Enter the dark cave",
  "order": 2
}

# Delete choice
DELETE /storynodes/{node_id}/choices/{choice_id}
```

---

## Playing Endpoints (Player Instances)

### Story Progress
```http
# List player's story instances
GET /user-personas/{persona_id}/stories

# Get specific instance
GET /user-personas/{persona_id}/stories/{story_id}

# Start new story
POST /user-personas/{persona_id}/stories/{story_id}
# (No body needed - locks to current_version automatically)

# Update progress (admin/debug)
PUT /user-personas/{persona_id}/stories/{story_id}
{
  "current_node_id": "uuid",
  "story_state": {"key": "value"}
}
```

### Navigation
```http
# Get current position
GET /user-personas/{persona_id}/stories/{story_id}/current-node

Response:
{
  "node": {
    "id": "uuid",
    "title": "Chapter One",
    "content": "You wake up...",
    ...
  },
  "available_choices": [
    {
      "id": "uuid",
      "text": "Enter the cave",
      "from_node_id": "uuid",
      "to_node_id": "uuid",
      ...
    }
  ],
  "story_state": {
    "has_torch": true,
    "visited_cave": false
  }
}

# Make a choice
POST /user-personas/{persona_id}/stories/{story_id}/choices/{choice_id}
# (No body needed)
```

---

## Response Models

### StoryPublic
```json
{
  "id": "uuid",
  "title": "string",
  "description": "string",
  "owner_id": "uuid",
  "current_version": 1,
  "published_version": null,
  "is_published": false,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

### StoryNodePublic
```json
{
  "id": "uuid",
  "story_id": "uuid",
  "story_version": 1,
  "title": "string",
  "content": "string",
  "node_type": "text",
  "is_start_node": false,
  "is_end_node": false,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

### NodeChoicePublic
```json
{
  "id": "uuid",
  "from_node_id": "uuid",
  "to_node_id": "uuid",
  "text": "string",
  "order": 0,
  "requires_state": {"key": "value"},
  "sets_state": {"key": "value"}
}
```

### UserStoryProgressPublic
```json
{
  "id": "uuid",
  "user_persona_id": "uuid",
  "story_id": "uuid",
  "story_version": 1,
  "current_node_id": "uuid",
  "is_completed": false,
  "story_state": {"key": "value"},
  "started_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

### CurrentNodePublic
```json
{
  "node": StoryNodePublic,
  "available_choices": [NodeChoicePublic],
  "story_state": {"key": "value"}
}
```

---

## Common Workflows

### Author Creates a Story
```bash
# 1. Create story
POST /stories
→ Get story_id, current_version=1

# 2. Create start node
POST /storynodes
{
  "story_id": "{story_id}",
  "story_version": 1,
  "is_start_node": true,
  ...
}
→ Get start_node_id

# 3. Create more nodes
POST /storynodes (multiple times)
→ Get node_id for each

# 4. Create choices connecting nodes
POST /storynodes/{from_node_id}/choices
{
  "from_node_id": "{from_node_id}",
  "to_node_id": "{to_node_id}",
  ...
}

# 5. Test with start-node helper
GET /stories/{story_id}/start-node
→ Verify start node is correct
```

### Player Plays a Story
```bash
# 1. Start story
POST /user-personas/{persona_id}/stories/{story_id}
→ Creates progress, sets current_node to start node

# 2. Get current position
GET /user-personas/{persona_id}/stories/{story_id}/current-node
→ See current node and available choices

# 3. Make choice
POST /user-personas/{persona_id}/stories/{story_id}/choices/{choice_id}
→ Updates state, moves to next node

# 4. Repeat steps 2-3 until story complete
GET .../current-node
POST .../choices/{choice_id}
GET .../current-node
...

# 5. Check completion
GET /user-personas/{persona_id}/stories/{story_id}
→ is_completed: true when end node reached
```

---

## State Management Examples

### Conditional Choices
```json
// Choice only available if player has torch
{
  "text": "Light the torch and enter",
  "requires_state": {
    "has_torch": true
  }
}

// Choice only available in specific chapter
{
  "text": "Return to village",
  "requires_state": {
    "current_chapter": "forest"
  }
}

// Multiple requirements (all must be true)
{
  "text": "Use the key on the door",
  "requires_state": {
    "has_key": true,
    "found_door": true
  }
}
```

### State Changes
```json
// Simple flag
{
  "text": "Pick up the torch",
  "sets_state": {
    "has_torch": true
  }
}

// Multiple changes
{
  "text": "Drink the potion",
  "sets_state": {
    "has_health_potion": false,
    "health": 100
  }
}

// Progress tracking
{
  "text": "Complete the quest",
  "sets_state": {
    "quest_complete": true,
    "current_chapter": "epilogue",
    "gold": 500
  }
}
```

---

## Error Codes

### 400 - Bad Request
- Not enough permissions
- Cannot create node for non-current version
- Choice doesn't belong to current node
- Invalid node/version mismatch
- Progress already exists for this story

### 403 - Forbidden
- User persona doesn't meet story requirements
- Choice requirements not met in story state

### 404 - Not Found
- Story not found
- StoryNode not found
- NodeChoice not found
- UserPersona not found
- UserStoryProgress not found
- Start node not found

### 500 - Internal Server Error
- No start node found for story version

---

## CRUD Functions Available

```python
# User persona verification
crud.get_user_persona(session, id, user_id)

# Progress operations
crud.get_user_story_progress(session, user_persona_id, story_id)
crud.get_user_story_progresses(session, user_persona_id, skip, limit)
crud.create_user_story_progress(session, progress_in)
crud.update_user_story_progress(session, db_progress, progress_in)

# Logic operations
crud.get_available_choices(session, node_id, story_state)
crud.check_story_requirements(session, user_persona_id, story_id)
```

---

## Tips & Best Practices

### For Authors
- Always mark one node as `is_start_node` per story version
- Use `order` field to control choice display sequence
- Test state logic with different paths through the story
- Keep `requires_state` simple (AND logic only)
- Document your state keys somewhere

### For Players
- Check `available_choices` before assuming a choice exists
- Watch for `is_completed` flag when reaching end
- `story_state` grows over time - it's your save game

### For Developers
- Version lock happens at progress creation - immutable after
- State merging is shallow (update, not deep merge)
- Choice filtering happens in `get_available_choices()`
- All operations validate permissions
- Cascade deletes handle cleanup automatically