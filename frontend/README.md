# Dog Frontend

The frontend is a Vite + React + TypeScript application using TanStack Router, TanStack Query, Tailwind, Radix/shadcn-style primitives, generated OpenAPI client code, and Playwright tests.

It provides the main console for stories, rooms, demos, personas, agents, projects, pages, repos, workspaces, themes, and admin/settings workflows.

## Requirements

- Node.js matching `frontend/.nvmrc`, when present.
- npm.
- Backend available at `VITE_API_URL` (`http://localhost:8000` in the default local Docker workflow).

## Run In Docker

From the repo root:

```bash
docker compose up -d --build frontend
```

Open `http://localhost:5173`.

## Run Locally

Keep the backend and supporting services in Docker, then run Vite locally:

```bash
docker compose stop frontend
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

To point at a different API, set `VITE_API_URL` in `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

## Scripts

```bash
npm run dev
npm run typecheck
npm run build
npm run build:strict
npm run lint
npm run test:unit
npm run test:e2e
npm run generate-client
```

`npm run lint` currently runs Biome with write/unsafe fixes enabled. Review changes before committing.

## Code Map

- `src/routes/`: TanStack Router routes.
- `src/components/`: feature and primitive UI components.
- `src/hooks/`: API and state hooks.
- `src/client/`: generated OpenAPI client.
- `src/components/Demo/`: demo builder/runtime UI.
- `src/components/Story/`: story list/editor/shell UI.
- `tests/`: Playwright end-to-end tests.
- `tests-unit/`: Playwright component/unit-style tests.

## Generated Client

When backend OpenAPI changes:

```bash
./scripts/generate-client.sh
```

Or manually:

```bash
cd frontend
npm run generate-client
```

The manual path expects an `openapi.json` in the frontend project root.

## Playwright

Run against the Docker test profile:

```bash
docker compose --profile test run --rm playwright npx playwright test
```

Run locally from `frontend/` when the stack is already available:

```bash
npm run test:e2e
npm run test:e2e:ui
```

## Related Docs

- [../development.md](../development.md)
- [../docs/affordances/](../docs/affordances/)
- [../docs/demos/](../docs/demos/)
- [../docs/user-ui-customization/](../docs/user-ui-customization/)
