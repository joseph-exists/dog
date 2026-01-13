# Data Templates

Common data structures for populating TinyFoot.

## Archetype Template

```python
ARCHETYPE = {
    "name": "The [Name]",
    "description": "[Core motivation and behavior]",
    "traits": [
        {"name": "[Trait1]", "description": "[What it means]"},
        {"name": "[Trait2]", "description": "[What it means]"},
        {"name": "[Trait3]", "description": "[What it means]"}
    ],
    "personas": [
        {"name": "The [Persona1]", "description": "[Variation of archetype]"},
        {"name": "The [Persona2]", "description": "[Variation of archetype]"},
        {"name": "The [Persona3]", "description": "[Variation of archetype]"}
    ]
}
```

## Story Template

```python
STORY = {
    "title": "[Story Title]",
    "description": "[Brief summary]",
    "state_schema": [
        {"key": "has_item", "type": "boolean", "default": False, "category": "inventory"},
        {"key": "score", "type": "number", "default": 0, "category": "stats"},
        {"key": "faction", "type": "enum", "enum_values": ["a", "b", "c"], "default": "a"}
    ],
    "nodes": [
        {"title": "Start", "content": "...", "is_start": True},
        {"title": "Middle", "content": "..."},
        {"title": "End", "content": "...", "is_end": True}
    ],
    "choices": [
        {"from": "Start", "to": "Middle", "text": "Continue", "sets_state": {"score": 10}},
        {"from": "Middle", "to": "End", "text": "Finish", "requires_state": {"score": 10}}
    ]
}
```

## Conflict Group Template

```python
CONFLICT = {
    "name": "[Conflict Name]",
    "type": "contradictory",  # or "contrary", "subcontrary"
    "reason": "[Why these traits conflict]",
    "traits": [
        {"name": "[Trait A]", "description": "[...]"},
        {"name": "[Trait B]", "description": "[...]"}
    ]
}
```

## Conflict Types

| Type | Meaning | Members |
|------|---------|---------|
| `contradictory` | Exactly one must be true | 2 |
| `contrary` | At most one can be true | 2+ |
| `subcontrary` | At least one must be true | 2+ |

## Quality Template

```python
QUALITIES = [
    {"name": "Strength", "description": "Physical power"},
    {"name": "Intelligence", "description": "Mental acuity"},
    {"name": "Charisma", "description": "Social influence"},
    {"name": "Wisdom", "description": "Good judgment"},
    {"name": "Agility", "description": "Quick reflexes"}
]
```

## Room Setup Template

```python
ROOM = {
    "title": "[Room Name]",
    "story_id": "[optional]",
    "participants": [
        {"id": "[user_id]", "type": "user", "role": "owner"},
        {"id": "StoryAdvisor", "type": "agent", "role": "member"}
    ]
}
```

## CSV Format for Attribute Assignment

```csv
funny,serious,mysterious
adventurous,cautious,bold
creative,analytical,practical
```

Each cell is one attribute. Use with `assign_persona_attributes.py`.
