# TinyFoot Backend Development Rules

This document outlines the conventions and patterns for the TinyFoot backend, which uses FastAPI, SQLModel, Redis, Pydantic, and PostgreSQL.

> **IMPORTANT**: When adding or modifying data models, ensure that you follow the database migration workflow using Alembic as described in the [Database Migrations](#database-migrations) section below.

## Key Principles

- Write concise, technical responses with accurate Python examples.
- Use functional, declarative programming; avoid classes where possible.
- Prefer iteration and modularization over code duplication.
- Use descriptive variable names with auxiliary verbs (e.g., is_active, has_permission).
- Use lowercase with underscores for directories and files (e.g., routers/user_routes.py).
- Favor named exports for routes and utility functions.
- Use UUID as primary keys for all database models.

## Project Structure

The backend follows this structure:
- `app/`: Main application package
  - `api/`: API endpoints and dependencies
    - `routes/`: Individual route modules
  - `core/`: Core configuration and setup
  - `alembic/`: Database migrations
  - `models.py`: SQLModel and Pydantic models
  - `crud.py`: CRUD operations
  - `utils.py`: Utility functions
  - `main.py`: Application entrypoint

## Python/FastAPI Patterns

- Use `def` for pure functions and `async def` for asynchronous operations.
- Use type hints for all function signatures. Prefer Pydantic models over raw dictionaries for input validation.
- For routes, use the pattern seen in existing route files.  Routes should never go in crud.py, only in an appropriately named file in the /backend/app/routes/ directory.

- Once a routes file has been added, it will be necessary to add it to the /backend/app/api/main.py.


  ```python
  @router.get("/{parameter}", response_model=ResponseModel)
  def endpoint_name(
      parameter: ParameterType,
      session: SessionDep,
      current_user: CurrentUser,
  ) -> Any:
      """
      Documentation string.
      """
      # Function logic
  ```
- Use dependency injection via `Depends()` for database sessions and user authentication.
- Follow FastAPI path operation function naming: `read_*`, `create_*`, `update_*`, `delete_*`.

## SQLModel Patterns

- Define models in `models.py` following the existing pattern:
  - Base models for shared properties
  - Create models for API input on creation
  - Update models for API input on updates
  - Database models for ORM (with `table=True`)
  - Public models for API responses
  - Collection response models (EntitiesPublic with data and count fields)

- When adding a new model follow all data-model-best-practices.md.
  1. Add all required model classes to `models.py`
  2. Create any needed CRUD operations in `crud.py`
  3. Add API routes in a new or existing file in `app/api/routes/`
  4. Include the router in `app/api/main.py` if it's a new route file
  5. Create a database migration (see [Database Migrations](#database-migrations))

- Example:
  ```python
  # Base model
  class EntityBase(SQLModel):
      name: str = Field(min_length=1, max_length=255)
      
  # Create model
  class EntityCreate(EntityBase):
      pass
      
  # Update model
  class EntityUpdate(EntityBase):
      name: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore
      
  # Database model
  class Entity(EntityBase, table=True):
      id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
      owner_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
      
  # Public model
  class EntityPublic(EntityBase):
      id: uuid.UUID
  
  # Collection response
  class EntitiesPublic(SQLModel):
      data: list[EntityPublic]
      count: int
  ```

## Error Handling

- Handle errors and edge cases at the beginning of functions.
- Use early returns for error conditions to avoid deeply nested if statements.
- Use HTTP exception with appropriate status codes:
  ```python
  if not item:
      raise HTTPException(status_code=404, detail="Item not found")
  ```
- Check permissions before performing operations.

## Database Operations

- Use SQLModel's query syntax for database operations.
- For simple lookups, use `session.get(Model, id)`.
- For more complex queries, use `select()` and `session.exec()`:
  ```python
  statement = select(Model).where(Model.field == value)
  results = session.exec(statement).all()  # or .first(), .one(), etc.
  ```
- Use transactions when multiple operations need to be atomic.
- Handle database errors appropriately.

## Authentication and Authorization

- Use the existing dependency injection pattern:
  ```python
  from app.api.deps import CurrentUser, get_current_active_superuser
  
  @router.post("/", dependencies=[Depends(get_current_active_superuser)])
  def superuser_only_endpoint(...):
      # Only accessible to superusers
  
  @router.get("/me")
  def user_endpoint(current_user: CurrentUser):
      # Accessible to authenticated users
      return current_user
  ```

## API Response Patterns

- Always use a response model for endpoints.
- For collections, use the pattern:
  ```python
  return EntityCollectionPublic(data=items, count=count)
  ```
- For success messages, use the Message model:
  ```python
  return Message(message="Operation completed successfully")
  ```



### Redis Connection Pattern

- Follow the db.py pattern for Redis connections
- Use connection pooling for efficiency:
  ```python
  from app.core.redis import get_redis

  redis = await get_redis()
  await redis.publish(channel, message)
  ```
- Configuration via settings (REDIS_HOST, REDIS_PORT)
- Docker service names (use "redis" not "localhost")

### WebSocket Patterns

- Single WebSocket connection per room at parent component
- Pass connection props to child components (avoid duplicate hooks)
- Throttle UI updates to prevent render spam:
  ```typescript
  // Buffer tokens for 50ms before updating UI
  const tokenBufferRef = useRef<string>("")
  const updateTimerRef = useRef<NodeJS.Timeout | null>(null)

  // Accumulate in buffer
  tokenBufferRef.current += token

  // Throttle UI updates
  if (updateTimerRef.current) clearTimeout(updateTimerRef.current)
  updateTimerRef.current = setTimeout(() => {
    setStreamingMessage(tokenBufferRef.current)
  }, 50)
  ```

### PydanticAI Streaming

- `stream_text()` yields **cumulative chunks**, not deltas
- Extract new content: `new_content = chunk[prev_len:]`
- Example:
  ```python
  full_response = ""
  prev_len = 0
  async with agent.run_stream(prompt) as result:
      async for chunk in result.stream_text():
          # chunk is CUMULATIVE: "Hello" → "Hello world" → "Hello world!"
          new_content = chunk[prev_len:]  # Extract only new portion
          full_response = chunk
          prev_len = len(chunk)

          await publish_token(new_content)  # Publish delta only
  ```

## Docker Networking

- NEVER MODIFY DOCKER FILES.
- Use Docker service names in docker-compose.yml
- Override config defaults with environment variables:
  ```yaml
  environment:
    - REDIS_HOST=redis  # Service name, not localhost
    - POSTGRES_SERVER=db  # Service name, not localhost
  ```
- Inside containers, `localhost` refers to the container itself

## Database Migrations

### When to Create Migrations

A new migration MUST be created whenever:

- A new model class is added to models.py
- An existing model is modified (fields added, removed, or changed)
- A relationship between models is altered
- Index or constraint configurations are changed

### Creating a Migration

After modifying the models, always follow these steps:

1. Start an interactive session in the backend container:
   ```console
   docker compose exec backend bash
   ```

2. Create a revision with an informative message:
   ```console
   alembic revision --autogenerate -m "Brief description of the changes"
   ```

3. Verify the generated migration file in `./app/alembic/versions/` to ensure it properly captures the changes

4. Apply the migration:
   ```console
   alembic upgrade head
   ```

5. Commit the new migration files to the git repository

### Migration Best Practices

- Give migrations descriptive names that clearly indicate the changes made
- Review the autogenerated migration files before applying them
- Never edit a migration that has been applied to any environment
- If a migration needs correction, create a new migration that fixes the issues
- Test migrations thoroughly in development before deploying

## Testing

- Write tests for all routes and business logic.
- Use pytest fixtures for database setup and teardown.
- Test happy paths and edge cases/error conditions.
- Keep tests isolated from one another.

## Performance Optimization

- Use asynchronous operations for I/O-bound tasks.
- For large collections, implement pagination:
  ```python
  @router.get("/")
  def read_items(session: SessionDep, skip: int = 0, limit: int = 100):
      # Paginated response
  ```
- Use appropriate database indexing via SQLModel Field parameters.

## Documentation

- Use docstrings for all public functions, especially API endpoints.
- Use type hints consistently for better IDE support and self-documentation.
- Keep the OpenAPI documentation updated through FastAPI's automatic tools.

## Workflow for Adding New Features

When adding a new feature that requires data models:

1. Define models in `models.py`
   - Base model with common fields
   - Create/Update models for input validation
   - Database model with table=True
   - Public model for API responses
   - Collection response model if needed

2. Create Alembic migration
   - Run `alembic revision --autogenerate -m "Add NewFeature model"`
   - Review the generated migration
   - Apply with `alembic upgrade head`

3. Add CRUD operations in `crud.py`

4. Create API routes in `app/api/routes/`

5. Register the router in `app/api/main.py` if it's a new module

6. Write tests in `app/tests/`

## Final Considerations

- Follow PEP 8 style guidelines for code formatting.
- Favor readability over cleverness.
- Be consistent with the existing codebase patterns.
- Use the dependency injection system consistently.
- Ensure all routes are properly tagged for OpenAPI documentation.
- Always create and apply Alembic migrations when changing models.
