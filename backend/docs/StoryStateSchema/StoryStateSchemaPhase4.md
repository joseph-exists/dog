## Phase 4: Database Migration

```bash
cd backend
alembic revision --autogenerate -m "Add StoryStateVariable model"
alembic upgrade head
```

---

## Phase 5: Frontend - API Client

```bash
cd frontend
npm run generate-client
```

This generates types and service methods for the new endpoints.

## Phase 5.1: Extensive test coverage: pytest tests in app/tests/ using existing framework, patterns, and fixtures.

## Phase 5.2: detailed integration tests in backend/app/test_scripts/ - needs plan and approval.

## Phase 5.5: Typer - Generate CLI commands for testing and management

see backend/app/test_scripts/typer

