# Data Model Rules (SQLModel + Pydantic v2)


-# SQLModel, Pydantic, and Alembic Best Practices for Relationship Definitions
-
-SQLModel combines SQLAlchemy's ORM functionality with Pydantic's validation capabilities, creating a unique approach to handling model relationships.
-
-## SQLModel Relationship Definition Best Practices
-
-SQLModel offers multiple approaches to defining relationships, but when dealing with circular references, here are the best practices:
-
-### 1. Using String-Based Forward References
-
-SQLModel supports string-based forward references for type hints in relationships:
-
-```python
-class Archetype(ArchetypeBase, table=True):
-    # Fields...
-    traits: list["Trait"] = Relationship(
-        back_populates="archetypes",
-        link_model=ArchetypeTraitLink,
-    )
-```
-
-This tells Python's type checker about the relationship without requiring Trait to be fully defined yet.
-
-### 2. Post-Definition Relationship Binding
-
-This approach (defining relationships after all classes) is fully compatible with SQLModel and is actually recommended in the SQLModel documentation for complex circular relationships. For example:
-
-```python
-# First define all classes
-class Archetype(ArchetypeBase, table=True):
-    # Fields only...
-
-class Trait(TraitBase, table=True):
-    # Fields only...
-
-# Then add relationships
-Archetype.traits = Relationship(
-    back_populates="archetypes",
-    link_model=ArchetypeTraitLink,
-)
-```
-
-This pattern ensures all classes exist before they're referenced in relationships.
-
-## Integration with Pydantic
-
-Pydantic provides the validation layer in SQLModel. Some key considerations:
-
-1. **Type Hints**: Pydantic uses type hints to generate validators. With post-definition relationships, you maintain type checking for IDE support using string-based forward references.
-
-2. **Schema Generation**: Pydantic's schema generation will properly include the relationships defined after class declaration.
-
-3. **Model Structure**: The Pydantic part of SQLModel primarily cares about field definitions and validation rules, not relationship definitions, so post-defined relationships don't interfere with validation logic.
-
-## Alembic Migration Considerations
-
-Alembic generates migrations based on the SQLAlchemy metadata, which includes all relationships regardless of how they're defined. Some key points:
-
-1. **Table Detection**: Alembic detects tables and relationships from SQLAlchemy metadata, so it doesn't matter if relationships are defined within or after class definitions.
-
-2. **Migration Generation**: When running `alembic revision --autogenerate`, Alembic compares the current database schema with your model definitions. It will correctly capture all relationships, including those defined after class declarations.
-
-3. **Schema Updates**: Any changes to relationships (like adding cascade behavior) will be properly detected when generating new migrations.
-
-## Real-World Example from SQLModel Documentation
-
-SQLModel's official documentation recommends similar approaches for circular references. Here's an adaptation of their example:
-
-```python
-class Team(SQLModel, table=True):
-    id: int = Field(default=None, primary_key=True)
-    name: str
-    # No relationships defined here
-
-class Hero(SQLModel, table=True):
-    id: int = Field(default=None, primary_key=True)
-    name: str
-    team_id: int = Field(default=None, foreign_key="team.id")
-    # No relationships defined here
-
-# Add relationships after model declarations
-Team.heroes = Relationship(back_populates="team")
-Hero.team = Relationship(back_populates="heroes")
-```
-
-## Best Practices for TinyFoot
-
-1. **Use String-Based Forward References for Type Hints**: Keep proper type hinting in your model definitions but use string-based references:
-
-   ```python
-   traits: list["Trait"]
-   ```
-
-2. **Define Field-Only Models First**: Define all models with their fields and foreign keys but without relationship attributes.
-
-3. **Add Relationships After All Models**: Add all relationship attributes after all models are fully defined.
-
-4. **Keep Creation/Update/Response Models Simple**: These don't need relationships, so they can be defined anywhere after their base classes.
-
-5. **Document Your Choices and Reasons**: Add thorough inline comments explaining how you are following these patterns so future developers understand the organization.
-
-This approach is fully compatible with SQLModel, Pydantic, and Alembic, and follows recommended practices for handling circular relationships in complex models.


The rest of this document was written by someone who didn't understand the beauty of the universe and the aesthetics of a lovely engineering experience. We need to rewrite it posthaste - and add quotes from philosophers, poets, architects, and artists.


## Status and Compliance Note

1. These rules define the target standard.
2. Existing models in `backend/app/models.py` may not fully comply yet.
3. New and modified models should move toward compliance unless a documented exception is approved.

## Scope

Applies to:
1. SQLModel/Pydantic model definitions in `backend/app/models.py`
2. Model validation and normalization paths used by CRUD and route layers
3. Schema behavior that impacts OpenAPI generation and typed client consumption

Does not define feature-specific migration/cutover policy or domain-specific content contracts; those belong in feature hardening plans.

## Precedence

When model-contract guidance conflicts:
1. Feature hardening plan for the active workstream
2. This file (`backend/docs/DATA_MODEL_RULES.md`)
3. General backend conventions (`backend/docs/RULES.md`)

## Core Principles

1. **Contracts are code, not comments**: semantics must be enforced by types + validators.
2. **Validation at boundaries**: incoming and merged payloads must be normalized before persistence.
3. **Declarative persistence**: persisted model data represents intent/state, not executable runtime behavior.
4. **Schema determinism**: models must produce stable, explicit OpenAPI schemas.
5. **Incremental hardening**: avoid introducing weaker patterns while refactoring legacy models.

## Model Structure Conventions

Use the layered model pattern:
1. Base model(s) for shared fields
2. Create input model(s)
3. Update/Patch input model(s)
4. Database model(s) (`table=True`)
5. Public response model(s)
6. Collection response model(s) (`data`, `count`)

Rules:
1. Public API fields must have explicit types and constraints where appropriate.
2. Avoid introducing anonymous/raw dictionaries as primary API contracts.
3. Keep relationship declarations and complex relationship wiring maintainable and explicit.

## Pydantic v2 Contract Rules

### Discriminated Modeling

1. When a domain already has a natural discriminator (for example, `kind` or `type`), model as explicit union branches.
2. Avoid non-discriminated unions for contract-critical structures.
3. Avoid a generic fallback branch as the primary path for supported production variants.

### Validation Rules

1. Use `field_validator` for field-local invariants.
2. Use `model_validator(mode="after")` for cross-field invariants.
3. Validate uniqueness and referential integrity where required by contract semantics (IDs, references, mode constraints).
4. Error messages should be specific enough to debug payload issues quickly.

### Update/Patch Semantics

1. Patch models may be partial.
2. After applying a patch, re-validate the full canonical model before persisting.
3. Do not persist partially validated merged objects.
4. Reject invalid intermediate states rather than silently coercing them.

## SQLModel Persistence Rules

1. Database storage format can remain pragmatic (including JSON/JSONB) where appropriate.
2. Persistence substrate must not replace contract validation.
3. Persisted JSON payloads must pass through typed model validation (`model_validate`) before save.
4. Avoid writing raw unvalidated payload dictionaries directly to DB fields.

## Schema and OpenAPI Hygiene

1. Model fields that define contract identity (for example discriminator fields) must remain explicit and stable.
2. Avoid patterns that obscure schema generation (dynamic field injection, ambiguous aliases).
3. Changes that affect API shape should be validated against generated OpenAPI output and client codegen.
4. Prefer additive, explicit schema evolution over implicit behavior changes.

## Anti-Degradation Guidance

Do not introduce the following in new or refactored contracts:
1. Primary payload contracts modeled as `Any` or unconstrained `dict[str, Any]`
2. Validation bypasses at CRUD/persistence boundaries
3. Hidden fallback semantics that mask invalid states
4. Implicit coupling of runtime execution behavior into persisted model fields

## Review Checklist (PR-Level)

For model changes, reviewers should confirm:
1. Contract shape is explicit and typed.
2. Discriminator-driven branches are explicit when applicable.
3. Patch/update path re-validates canonical model before persistence.
4. Validators cover critical invariants and return actionable errors.
5. OpenAPI-facing schema impact is reviewed.
6. Changes do not introduce weaker patterns than the pre-existing baseline.

## Legacy Hardening Expectations

1. Legacy models can remain temporarily non-compliant if untouched.
2. Any touched legacy contract area should be improved or explicitly documented with rationale.
3. New work must not expand legacy weak patterns into additional surfaces.
