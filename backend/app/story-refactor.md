# Story System Refactor: Versioned Templates with Player Instances

## Core Philosophy

Stories are **versioned templates** authored once and played many times. Authors evolve their work through versions; players lock to a version when they begin. No player ever experiences mid-game changes to their adventure.

---

## Three Namespaces, Three Concerns

### 1. AUTHORING - Content Creation
**Who:** Story creators  
**What:** Draft, edit, version, and publish adventure templates

**Key Entities:**
- `Story` - The adventure container (title, description, owner_id, current_version, is_published)
- `StoryNode` - Immutable scene templates tied to a story_version (content, node_type, is_start_node, is_end_node)
- `NodeChoice` - Decision branches (text, from_node_id, to_node_id, requires_state, sets_state)

**Contract:**
- Unpublished Stories are mutable playgrounds
- Publishing locks the current version, increments version number
- Edits after publishing create a new draft version
- StoryNodes belong to specific story_version (composite key or denormalized)
- Authors can have v1 (published), v2 (published), v3 (draft) simultaneously

**Authorization:**
- Only owner_id can edit/publish their Stories
- Superusers can moderate published content

---

### 2. DISCOVERY - Finding Adventures
**Who:** All users browsing for new experiences  
**What:** Browse, filter, and preview published Stories

**Key Entities:**
- Published `Story` records (filtering on is_published=true)
- Story metadata, tags, requirements
- Preview of starting scenario

**Contract:**
- Only published Stories appear in catalog
- Users see latest published version by default
- Can view version history and start any published version
- Requirements checked before allowing start (StoryRequirement system)

**Authorization:**
- Public read access to published Stories
- Requirements gate who can start (persona qualities/traits)

---

### 3. PLAYING - Active Journeys
**Who:** Players experiencing adventures  
**What:** Navigate choices, accumulate state, progress through locked story versions

**Key Entities:**
- `UserStoryProgress` - The player's instance (user_persona_id, story_id, story_version, current_node_id, story_state, is_completed)
- `UserNodeChoice` - Historical record of decisions (choice_text, from_node_id, to_node_id, state_changes, choice_time)
- Referenced (not copied) StoryNodes from the locked version

**Contract:**
- Starting a Story creates UserStoryProgress locked to story_version
- Player navigates through template nodes via current_node_id pointer
- story_state dict accumulates as choices apply sets_state
- NodeChoice.requires_state gates which choices appear
- Reaching is_end_node marks is_completed
- Template nodes remain shared/referenced across all players

**State Flow:**
1. Player at node N sees available NodeChoices
2. Filter choices by requires_state against current story_state
3. Player selects choice C
4. Create UserNodeChoice record (historical breadcrumb)
5. Apply C.sets_state to UserStoryProgress.story_state
6. Update current_node_id to C.to_node_id
7. Repeat

**Authorization:**
- Players can only modify their own UserStoryProgress
- Players read template StoryNodes for their locked version
- No write access to template data

---

## Data Model Handoffs

### Author → Published Catalog
**Trigger:** Author calls `/stories/{id}/publish`  
**Effect:**
- Story.is_published = true
- Story.published_version = Story.current_version
- Story.current_version increments (new draft space)
- Template nodes for published_version become read-only

### Catalog → Player Instance
**Trigger:** Player calls `/catalog/{story_id}/start`  
**Effect:**
- Verify StoryRequirements against player's UserPersona
- Create UserStoryProgress(story_version=Story.published_version)
- Set current_node_id to story's is_start_node
- Initialize empty story_state dict
- Return player to their new journey

### Player Navigation Loop
**Trigger:** Player calls `/journeys/{progress_id}/choose/{choice_id}`  
**Effect:**
- Validate choice belongs to current_node_id
- Validate choice.requires_state against story_state
- Record UserNodeChoice
- Merge choice.sets_state into story_state
- Advance current_node_id
- Check if new node is_end_node → mark completed

---

## Key Architectural Decisions

**Versioning Strategy:**
- Story.current_version (int) - what authors are editing
- Story.published_version (int) - what players see in catalog
- StoryNode.story_version (int) - which version this node belongs to
- UserStoryProgress.story_version (int) - locked at creation

**No Copying, Just References:**
- UserStoryProgress stores only: current position, accumulated state, history
- StoryNodes remain single source of truth per version
- Efficient storage, clear ownership

**State as Accumulator:**
- UserStoryProgress.story_state is the "game variables" dict
- Grows via merge from each NodeChoice.sets_state
- Gates available choices via NodeChoice.requires_state
- Enables branching, unlocks, conditional content

**Immutability Boundaries:**
- Published StoryNodes: immutable (or make new version)
- Draft StoryNodes: fully mutable
- UserStoryProgress: owned mutation by player only

---

## Route Organization

```
/stories/*              # Authoring namespace
/catalog/*              # Discovery namespace  
/journeys/*             # Playing namespace
```

Each namespace has clear ownership, permissions, and concerns. No more confusion about whether an endpoint is for creators or players.