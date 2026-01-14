# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Architecture

This application has the following structure:

### Backend (FastAPI + SQLModel + PostgreSQL)

- **Location**: `backend/`
- **Framework**: FastAPI with SQLModel for ORM
- **Database**: PostgreSQL with Alembic migrations
- **Key files**:
  - `backend/app/main.py` - FastAPI application entry point
  - `backend/app/models.py` - SQLModel database models 
  - `backend/app/api/routes/` - API endpoint definitions
  - `backend/app/crud.py` - Database CRUD operations
  - `backend/app/core/` - Core configuration, database setup

### System Architecture


### Domain Models

### Frontend (React + TypeScript + Vite)

- **Location**: `frontend/`
- **Framework**: React with TypeScript, Vite build tool
- **UI Library**: Chakra UI
- **State Management**: TanStack Query + TanStack Router
- **Key directories**:
  - `frontend/src/components/` - React components organized by feature
  - `frontend/src/routes/` - TanStack Router route definitions
  - `frontend/src/client/` - Auto-generated API client from OpenAPI spec
  - `frontend/src/hooks/` - Custom React hooks

## Development Commands

### Backend Development

```bash
cd backend
uv sync                    # Install dependencies (uses uv for fast dependency management)
source .venv/bin/activate  # Activate virtual environment (Linux/Mac)
fastapi dev app/main.py    # Run development server (auto-reload enabled)
pytest app/tests/         # Run tests directly
pytest -v app/tests/test_specific.py::test_function  # Run single test
alembic current           # Check current migration
alembic history           # View migration history
ruff check app/           # Run linter
ruff format app/          # Format code
mypy app/                 # Type checking
```

### Frontend Development

```bash
cd frontend
npm install               # Install dependencies
npm run dev              # Start development server (http://localhost:5173)
npm run build            # Build for production
npm run lint             # Run Biome linter
npm run generate-client  # Generate API client from OpenAPI spec
npx playwright test      # Run E2E tests
```

### Full Stack Development

```bash
docker compose watch     # Start entire stack with hot reload
docker compose up -d     # Start stack in background
docker compose logs backend  # View backend logs
docker compose exec backend bash  # Access backend container
```

## Code Generation and Linting

### Backend

- **Linting**: Uses Ruff (configured in `pyproject.toml`)
- **Type checking**: MyPy with strict mode
- **Testing**: Pytest with coverage reporting
- **Pre-commit hooks**: Configured for automatic formatting and linting

### Frontend

- **Linting**: Biome (configured in `biome.json`)
- **Type checking**: TypeScript with strict configuration
- **Testing**: Playwright for E2E tests
- **API Client**: Auto-generated from backend OpenAPI spec using `@hey-api/openapi-ts`

## Database and Migrations

- Database models defined in `backend/app/models.py` using SQLModel
- Migrations managed with Alembic
- **CRITICAL**: Always have user create migrations after model changes: `alembic revision --autogenerate -m "description"`
- Always have user apply migrations: `alembic upgrade head`
- Migration files stored in `backend/app/alembic/versions/`
- **Never edit applied migrations** - create new ones to fix issues

## Key Development Patterns

### Authentication

- JWT-based authentication implemented
- User management with superuser capabilities
- Password hashing with bcrypt
- Email-based password recovery

### API Structure

- RESTful API with OpenAPI/Swagger documentation at `/docs`
- CRUD operations centralized in `backend/app/crud.py`
- Route handlers in `backend/app/api/routes/`
- Automatic client generation for frontend (npm run generate-client)

### Frontend Patterns

- Component organization by feature in `components/` directory
- Custom hooks for API interactions in `hooks/`
- TanStack Router for client-side routing

## Testing

### Backend Tests

- Location: `backend/app/tests/`
- Test with running stack: `docker compose exec backend bash scripts/tests-start.sh`

### Frontend Tests

- E2E tests with Playwright in `frontend/tests/`
- Requires running backend: `docker compose up -d --wait backend`
- Run: `npx playwright test`
- UI mode: `npx playwright test --ui`

## Environment Configuration

- Main config in `.env` file
- Development overrides in `docker-compose.override.yml`
- Key variables: `SECRET_KEY`, `FIRST_SUPERUSER_PASSWORD`, `POSTGRES_PASSWORD`
- Generate secret keys: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

## Backend Development Rules

### Critical Principles

- **Use UUID as primary keys** for all database models
- **Always create Alembic migrations** when adding/modifying models
- **Use functional, declarative programming** - avoid classes where possible
- **No new dependencies** without approval - use existing libraries
- **Follow existing patterns** in the codebase strictly

### Model Definition Patterns

Models in `backend/app/models.py` follow specific structures.

**Model Pattern Structure**:

1. **Base models** - Shared properties (e.g., `NoteBaseEnhanced`)
2. **Create models** - API input validation (e.g., `NoteCreateEnhanced`)
3. **Update models** - API update validation (e.g., `NoteUpdateEnhanced`)
4. **Database models** - ORM with `table=True` (e.g., `NoteEnhanced`)
5. **Public models** - API responses (e.g., `NotePublicEnhanced`)
6. **Collection models** - Paginated responses (e.g., `NotesPublicEnhanced`)

**Complex Models**:

- **Relationship Bindings** Complex post-definition relationship setup

### SQLModel Relationships

- **Use string-based forward references**: `list["Item"]` not `list[Item]`
- **Simple relationships**: Define inline in model
- **Complex circular relationships**: Use post-definition binding at end of file
- **Always specify cascade behavior**: `cascade_delete=True` where appropriate

```python
# Simple inline relationship
class User(UserBase, table=True):
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)

# Complex post-definition binding (at end of models.py)
User.complex_relationships: list["RelatedModel"] = Relationship(...)
```

### API Route Patterns

Routes go in `backend/app/api/routes/` (never in crud.py):

```python
@router.get("/{parameter}", response_model=ResponseModel)
def endpoint_name(
    parameter: ParameterType,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Documentation string."""
    # Function logic
```

### Database Operations

- Use `session.get(Model, id)` for simple lookups
- Use `select().where()` for complex queries
- Handle errors early with `HTTPException(status_code=404, detail="Not found")`
- Check permissions before operations

### Authentication Patterns

```python
from app.api.deps import CurrentUser, get_current_active_superuser

@router.post("/", dependencies=[Depends(get_current_active_superuser)])
def superuser_only_endpoint(): ...

@router.get("/")
def user_endpoint(current_user: CurrentUser): ...
```

### Workflow for New Features

1. Define models in `models.py` (Base → Create → Update → Database → Public → Collection)
2. User needs to Create migration: `alembic revision --autogenerate -m "Add Feature"`
3. User needs to Apply migration: `alembic upgrade head`
4. Add CRUD operations in `crud.py`
5. Create routes in `app/api/routes/feature.py`
6. Register router in `app/api/main.py` (see current pattern with prefix/tags)
7. Write tests in `app/tests/`
8. Create standalone test scripts in app/test_scripts
9. Typer CLI integration in app/test_scripts/typer
10. Documentation updates

### Context-Specific Development Patterns

**Agent Development Patterns**:

**UI Component Development Patterns**:

**Story System**:

**Chat Room System**:

**Persona, Archetype, Traits, and Qualities System**:

**Events System**:


## Docker and Deployment

- Development: `docker compose watch` for hot reloading
- Production: `docker compose -f docker-compose.yml up -d`
- Traefik proxy configuration for production deployment
- GitHub Actions workflows configured for CI/CD

## Domain Context & Important Notes


### Current Development Status


### Key Implementation Decisions

- **UUID Primary Keys**: All entities use UUIDs instead of integer IDs
- **Post-definition Relationships**: Complex relationships defined at end of `models.py` due to circular dependencies


### Development Workflow Notes

- **Always run migrations**: This codebase has frequent schema changes
- **Test coverage**: Uses pytest with coverage reporting (`scripts/test.sh`)
- **Strict typing**: MyPy with strict mode enabled
- **Functional patterns**: Prefer functions over classes where possible
- **Follow existing patterns**: Complex codebase with established patterns - maintain consistency
