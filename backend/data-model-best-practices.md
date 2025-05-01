# SQLModel, Pydantic, and Alembic Best Practices for Relationship Definitions

SQLModel combines SQLAlchemy's ORM functionality with Pydantic's validation capabilities, creating a unique approach to handling model relationships.

## SQLModel Relationship Definition Best Practices

SQLModel offers multiple approaches to defining relationships, but when dealing with circular references, here are the best practices:

### 1. Using String-Based Forward References

SQLModel supports string-based forward references for type hints in relationships:

```python
class Archetype(ArchetypeBase, table=True):
    # Fields...
    traits: list["Trait"] = Relationship(
        back_populates="archetypes",
        link_model=ArchetypeTraitLink,
    )
```

This tells Python's type checker about the relationship without requiring Trait to be fully defined yet.

### 2. Post-Definition Relationship Binding

This approach (defining relationships after all classes) is fully compatible with SQLModel and is actually recommended in the SQLModel documentation for complex circular relationships. For example:

```python
# First define all classes
class Archetype(ArchetypeBase, table=True):
    # Fields only...

class Trait(TraitBase, table=True):
    # Fields only...

# Then add relationships
Archetype.traits = Relationship(
    back_populates="archetypes",
    link_model=ArchetypeTraitLink,
)
```

This pattern ensures all classes exist before they're referenced in relationships.

## Integration with Pydantic

Pydantic provides the validation layer in SQLModel. Some key considerations:

1. **Type Hints**: Pydantic uses type hints to generate validators. With post-definition relationships, you maintain type checking for IDE support using string-based forward references.

2. **Schema Generation**: Pydantic's schema generation will properly include the relationships defined after class declaration.

3. **Model Structure**: The Pydantic part of SQLModel primarily cares about field definitions and validation rules, not relationship definitions, so post-defined relationships don't interfere with validation logic.

## Alembic Migration Considerations

Alembic generates migrations based on the SQLAlchemy metadata, which includes all relationships regardless of how they're defined. Some key points:

1. **Table Detection**: Alembic detects tables and relationships from SQLAlchemy metadata, so it doesn't matter if relationships are defined within or after class definitions.

2. **Migration Generation**: When running `alembic revision --autogenerate`, Alembic compares the current database schema with your model definitions. It will correctly capture all relationships, including those defined after class declarations.

3. **Schema Updates**: Any changes to relationships (like adding cascade behavior) will be properly detected when generating new migrations.

## Real-World Example from SQLModel Documentation

SQLModel's official documentation recommends similar approaches for circular references. Here's an adaptation of their example:

```python
class Team(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    # No relationships defined here

class Hero(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    team_id: int = Field(default=None, foreign_key="team.id")
    # No relationships defined here

# Add relationships after model declarations
Team.heroes = Relationship(back_populates="team")
Hero.team = Relationship(back_populates="heroes")
```

## Best Practices for TinyFoot

1. **Use String-Based Forward References for Type Hints**: Keep proper type hinting in your model definitions but use string-based references:

   ```python
   traits: list["Trait"]
   ```

2. **Define Field-Only Models First**: Define all models with their fields and foreign keys but without relationship attributes.

3. **Add Relationships After All Models**: Add all relationship attributes after all models are fully defined.

4. **Keep Creation/Update/Response Models Simple**: These don't need relationships, so they can be defined anywhere after their base classes.

5. **Document Your Choices and Reasons**: Add thorough inline comments explaining how you are following these patterns so future developers understand the organization.

This approach is fully compatible with SQLModel, Pydantic, and Alembic, and follows recommended practices for handling circular relationships in complex models.
