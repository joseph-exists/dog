# TinyFoot Data Model Documentation

This document provides a comprehensive explanation of the TinyFoot data model, including all entities, relationships, and design decisions.

## Core Model Overview

The TinyFoot data model is designed to support interactive storytelling with several interconnected components:

1. **User System**: Authentication and authorization with standard user management
2. **Story System**: Interactive choice-based narratives with branching paths
3. **Character System**: Complex character modeling with Archetypes, Personas, Traits, and Qualities
4. **State Management**: Event-driven state changes and condition tracking

## User System

### User Model

The `User` model represents application users with authentication capabilities.

- **Primary fields**: id, email, hashed_password, full_name, is_active, is_superuser
- **Relationships**:
  - One-to-many with Items (example relationship model)
  - One-to-many with Stories (users create and own stories)
  - One-to-many with StoryPlays (tracking user gameplay sessions)

## Story System

The story system enables creation and playthrough of interactive narratives.

### Story Model

The `Story` model is the top-level container for interactive narratives.

The main container that represents a complete choose-your-own-adventure game. Stories are owned by users and contain nodes.

- **Primary fields**: id, title, description, is_published, created_at, updated_at, owner_id
- **Relationships**:
  - Many-to-one with User (owner relationship)
  - One-to-many with StoryNode (all content nodes in the story)
  - Many-to-many with Tag (for categorization)
  - One-to-many with StoryPlay (gameplay sessions)

### StoryNode Model

The `StoryNode` model represents individual screens or steps in an interactive story.

Each node can have different types (text, image, paradox, graph, calendly) specified by the node_type field and can contain additional metadata specific to that type. This supports the various features mentioned in the requirements.

- **Primary fields**: id, title, content, node_type, is_start_node, is_end_node, metadata, story_id, created_at, updated_at
- **Node Types**: text, image, choice, paradox, graph, calendly, etc.
- **Relationships**:
  - Many-to-one with Story
  - One-to-many with NodeChoice (as source node)
  - Many-to-many with other StoryNodes (via NodeChoice)
  - One-to-many with PlayState (tracking node visits)

### NodeChoice Model

The `NodeChoice` model represents narrative branches connecting story nodes.

Represents the choices available from one node to another, creating the branching narrative structure. Choices can set state variables and require specific state conditions, enabling complex interactive storytelling.

- **Primary fields**: id, text, order, from_node_id, to_node_id, requires_state, sets_state
- **Relationships**:
  - Many-to-one with StoryNode (from_node)
  - Many-to-one with StoryNode (to_node)

### Tag Model

The `Tag` model enables story categorization and filtering.

Tags allow for organization and categorization of stories, implemented with a many-to-many relationship between stories and tags.

- **Primary fields**: id, name, color
- **Relationships**:
  - Many-to-many with Story (via StoryToTag link model)

## Gameplay State Management

### StoryPlay Model

The `StoryPlay` model tracks individual playthroughs of stories.
- which nodes have been visited and any state associated with each node visit
- state_data JSON fields allow for storing arbitrary data needed for the game logic


- **Primary fields**: id, player_name, is_completed, state_data, created_at, updated_at, story_id, user_id
- **Relationships**:
  - Many-to-one with Story
  - Many-to-one with User (optional)
  - One-to-many with PlayState (tracking node visits)

### PlayState Model

The `PlayState` model records node visits during story playthroughs.

- **Primary fields**: id, visited_at, state_data, play_id, node_id
- **Relationships**:
  - Many-to-one with StoryPlay
  - Many-to-one with StoryNode

## Character System

The character system models complex characters with configurable properties.

### Archetype Model

The `Archetype` model represents character templates with predefined traits and qualities.

- **Primary fields**: id, name, description, created_at
- **Relationships**:
  - Many-to-many with Trait (via ArchetypeTraitLink)
  - One-to-many with Persona (via ArchetypePersonaLink)
  - Many-to-many with Quality (via ArchetypeQualityLink)

### Persona Model

The `Persona` model represents specific character instances that can inherit from archetypes.

- **Primary fields**: id, name, description, created_at
- **Relationships**:
  - Many-to-many with Archetype (via ArchetypePersonaLink)
  - Many-to-many with Trait (via PersonaTraitLink)
  - Many-to-many with Quality (via PersonaQualityLink)

### Trait Model

The `Trait` model represents character attributes that can trigger quality changes.

- **Primary fields**: id, name, description, created_at
- **Relationships**:
  - Many-to-many with Archetype (via ArchetypeTraitLink)
  - Many-to-many with Persona (via PersonaTraitLink)
  - Many-to-many with Quality (via QualityTraitLink)

### Quality Model

The `Quality` model represents status effects or properties that can be enabled/disabled.

- **Primary fields**: id, name, description, created_at
- **Relationships**:
  - Many-to-many with Archetype (via ArchetypeQualityLink)
  - Many-to-many with Persona (via PersonaQualityLink)
  - Many-to-many with Trait (via QualityTraitLink)
  - One-to-many with QualityEventTrigger (events that change quality state)

## Event System

The event system handles state changes based on story events.

### Event Model

The `Event` model represents triggers that can change the state of qualities.

- **Primary fields**: id, name, description, event_type, created_at
- **Relationships**:
  - One-to-many with QualityEventTrigger

### QualityEventTrigger Model

The `QualityEventTrigger` model defines how events affect qualities.

- **Primary fields**: id, quality_id, event_id, new_state, condition_json, created_at
- **Relationships**:
  - Many-to-one with Quality
  - Many-to-one with Event

## Link Models

Link models handle many-to-many relationships and store additional relationship metadata.

### ArchetypeTraitLink

- Links Archetypes and Traits
- Contains: id, archetype_id, trait_id, created_at

### ArchetypePersonaLink

- Links Archetypes and Personas
- Contains: id, archetype_id, persona_id, created_at

### ArchetypeQualityLink

- Links Archetypes and Qualities
- Contains: id, archetype_id, quality_id, created_at

### PersonaTraitLink

- Links Personas and Traits
- Contains: id, persona_id, trait_id, created_at, is_inherited, source_archetype_id

### PersonaQualityLink

- Links Personas and Qualities
- Contains: id, persona_id, quality_id, created_at, source_type, state, source_trait_id, source_archetype_id

### QualityTraitLink

- Links Qualities and Traits
- Contains: id, quality_id, trait_id, created_at, auto_enable, is_required

### StoryToTag

- Links Stories and Tags
- Contains: story_id, tag_id (composite primary key)

## Model Pattern Structure

All models follow a consistent pattern:

1. **Base Models**: Define common fields used in create, update, and table models
2. **Partial Base Models**: Define optional versions of fields for update operations
3. **Create Models**: Used for API validation when creating new entities
4. **Update Models**: Used for API validation when updating existing entities
5. **Table Models**: SQLAlchemy ORM models with database configuration
6. **Public Models**: Used for API responses
7. **Collection Models**: Used for API responses with pagination

## Relationship Management

Relationships between models are defined in two steps:

1. **Foreign Keys**: Defined within the table models
2. **Relationships**: Defined after all models are declared, to avoid circular references

This approach aligns with SQLModel best practices for handling complex model interactions.

## Enum Types

Several enumeration types are used to constrain field values:

### QualityState

- **ENABLED**: Quality is active
- **DISABLED**: Quality is inactive
- **REMOVED**: Quality is removed

### QualitySourceType

- **TRAIT_DEPENDENT**: Quality derived from a trait
- **DEFAULT**: Quality added by default
- **MANUALLY_ADDED**: Quality added manually

## Key Design Decisions

1. **UUID Primary Keys**: All entities use UUID primary keys for security and distribution
2. **Cascading Deletes**: Appropriate relationships use cascade deletion to maintain referential integrity
3. **Separation of Concerns**: Creation/update/response models separate validation from database structure
4. **Nested Relationship Loading**: Relationships use SQLAlchemy's selectin loading strategy for performance
5. **State as JSON**: Game state is stored as JSON for flexibility in state variables
6. **Event-Driven Quality Changes**: Quality state changes trigger from event system
7. **Inheritance Tracking**: Persona traits/qualities track inheritance source for transparency

## Database Usage Patterns

### Story Creation and Editing

1. Create a Story
2. Add StoryNodes to the Story
3. Link StoryNodes with NodeChoices
4. Add Tags for categorization

### Character Creation

1. Create Archetypes with predefined Traits and Qualities
2. Create Personas, optionally inheriting from Archetypes
3. Add/modify Traits for Personas
4. Define Quality states based on Traits or direct assignment

### Gameplay Tracking

1. Create StoryPlay when starting a story
2. Create PlayState entries when visiting nodes
3. Update state_data with gameplay variables

## Future Considerations

1. **Version Control**: Consider adding versioning for stories
2. **Collaborative Editing**: Adding multi-user editing capabilities
3. **Analytics Integration**: Enhancing tracking for gameplay analytics
4. **Content Management**: Additional content type support

## Schema Evolution

The schema is designed to evolve with application needs. Migrations should follow these guidelines:

1. Add new fields with default values to avoid breaking existing data
2. Use Alembic for all migrations
3. Test migrations on sample data before production deployment
4. Document schema changes in migration files



Relationships:

Users own multiple stories
Stories contain multiple nodes
Nodes connect to other nodes via choices
Stories can have multiple tags
StoryPlays track game progress for specific stories
PlayStates record node visits within a specific play


Items:

Inventory for Player: a list of Items

Current Inventory for a Persona during a Story

Saved list of all Inventory that a Player has had during all previous stories
Saved list of all Inventory that a Player has had for specific Persona across all Stories
Saved list of all Inventory that a Player has had during a particular Story


Item Rarity
Item Cost
Item instance specifics based on random generation or based on the outcome of a player choice or event
Item pre-conditions (could extend Qualities, or have a sub-type of Qualities specific to Items?)
For example:  Items can only be used by Users playing with a Persona of a certain Archetype
              Items can only be used by Users if there has already been a specific QualityEventTrigger


The Persona remembers what the Player forgets
The Player carries wounds the Persona cannot see
Together they walk the same path twice
Once as participant, once as witness




Users:

There are three User types - Storytellers, Players, and Operators.

An Operator has full admin access.
A Storyteller creates or modifies Stories or Story elements.
A Player plays the Game, which has multiple stages.

A Player can become a Storyteller after meeting certain requirements.
A Storyteller is also a Player.
A Storyteller has a progression of creation, modification, and editing capacity on Stories and other Story elements based on meeting specific requirements.

A Player will play as a Persona during a particular Story.
A Player will have different Personas to choose from before they begin playing a Story.
A Player's choice of Personas is based on the Story and other conditionals that the Player and their Personas have met.
A Player can be an AI.

Example:  New Player.
A New Player selects from 3 Personas.
After selecting a Persona, they are then able to select a Story.
New Players only have one Story available to select from.
The Player chooses that Story.
If the Player quits the Story, then they go back to the beginning of the New Player loop.

If The player plays the story until the End:
  The Persona they chose is saved with their progress with that Persona.
  The Persona type that they are playing with is updated with their progress.  For example, a counter on the number of times that "Charlie the Dinosaur" has successfully played through the Intro Story.
  That Persona becomes part of their choices for all Stories where that Persona is applicable.
  Any Story Events which have an effect on the Player are saved to the Player, including time played, items found, locations visited, and the graph of their traversal through the choices.

The Player is then able to select from the Persona they previously played with or a different Persona.
The Player is given a choice of Stories based on the Player and the Persona that they have selected.

Players are always able to choose from three Personas.
Players are always shown at least one previously used Persona, after the First Story is completed.
Players are always shown at least one Persona they have not used previously.










A Player playing a Story will have different choices available based on their Persona, their Persona's Archetype, their Traits, their Qualities, and their Items.

There may be Events during a Story which effect that Player's Persona.
These effects may be scoped to only that Story, to that Player's version of that Persona for all future stories they play with that Persona,
to all new versions of that Persona, or to all versions of that Persona.

Example of limited scoping: A Player is playing a Story with a Persona "Charlie the Dinosaur" and there is an Event where the Persona steps in mud.  "Charlie the Dinosaur" has the Quality 'dirty" for the rest of the Story, unless there is another event - like swimming in a river - where they have that Quality removed. The event of the quality being applied will be saved, and the Player will be able to see that their version of the Persona of "Charlie the Dinosaur" got dirty and eventually got clean, but that Persona will not be "dirty" in the next Story.

Example of Player level Scoping: A Player is playing a Story with a Persona "Morgle the Enchanter", a Persona who is created with an Item "Magic Bag of Candy".  During that Story, the Player is able to choose to give the "Magic Bag of Candy" away.  After that choice, the Player does not have the "Magic Bag of Candy" when they play other stories.

Example of Persona level Scoping: When enough Players have completed the Story "Dancing in the Dark" with the Persona "Anna K", the Persona "Anna K" will now have the trait "Quick Notice" for all Players, even if they haven't completed the Story "Dancing in the Dark" with "Anna K."





These changes may be only to


That User will play through a Story.  That User may have the option to replay that Story after they are done.  There might be changes to the options the player has the next time they play that Story, depending on the Story and the player's choices the last time they played that Story.

The User will also be playing a larger Game, within which the Story takes place.  There will be changes to User state during the Story that effect the overall Game for that User.







This schema design accommodates all the requirements mentioned in the project documentation:

Story elements
Player choice tracking
State variables for remembering choices
Tagging system
Support for special node types (paradox, graph, calendly)
Logic game framework through the state system

The schema follows the project's conventions:

Using UUID for primary keys
Following the SQLModel patterns with base, create, update, and public models
Maintaining cascade delete relationships
Using descriptive model and field names
Including appropriate field constraints
