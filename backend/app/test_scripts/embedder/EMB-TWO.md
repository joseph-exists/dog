# Embedder Query Reference Card

## Purpose
Use this card to run embedder semantic queries reliably and diagnose failures fast.

## What Queries Do
- `api_embedder_query.py`: searches OpenAPI tag chunks in `api_areas`.
- `embedded_code_query.py`: searches SDK/types/schema chunks in `api_code_chunks`.
- Both generate a query embedding first, then do pgvector similarity search.

## Required Inputs
- `OPENAI_API_KEY` must be set.
- A reachable Postgres URI for `devembed`.
- Indexed data must already exist in `api_areas` or `api_code_chunks`.

## DB URI Rules (Most Common Failure Source)
- Running on host: use `localhost`.
- Running inside `docker compose exec backend`: use `db` (not `localhost`).

Examples:
- Host URI: `postgresql+asyncpg://postgres:postgres@localhost:5432/devembed`
- Container URI: `postgresql+asyncpg://postgres:postgres@db:5432/devembed`

## Known Defaults
- Embedder utilities now prefer `devembed` by default.
- Resolution order:
1. `DEVEMBED_ASYNC_DATABASE_URL`
2. `DEVEMBED_DATABASE_URL`
3. `ASYNC_DATABASE_URL`
4. `DATABASE_URL`
5. App settings fallback (rewritten to `devembed`)

## Working Commands
- Host run:
```bash
cd /home/josep/dogbert/dog/backend
source .venv/bin/activate
python app/test_scripts/embedder/utils/api_embedder_query.py \
  --query "how many users are there?" \
  --db-uri "postgresql+asyncpg://postgres:postgres@localhost:5432/devembed"
```

- Container run:
```bash
cd /home/josep/dogbert/dog
docker compose exec -T backend bash -lc \
'cd /app/app/test_scripts/embedder/utils && /app/.venv/bin/python api_embedder_query.py \
  --query "how many users are there?" \
  --db-uri "postgresql+asyncpg://postgres:postgres@db:5432/devembed"'
```

## Fast Failure Map
- Error: `Connect call failed ('127.0.0.1', 5432)` inside container.
  - Cause: used `localhost` in container.
  - Fix: change DB host to `db`.

- Error: `OPENAI_API_KEY is required to embed the query text`.
  - Cause: key not exported in current runtime.
  - Fix: export key in that shell/container environment.

- Output is empty or irrelevant.
  - Cause: embeddings not indexed yet, wrong table, or weak query.
  - Fix: run embedder indexing first, verify table (`api_areas` or `api_code_chunks`), tune `--top-k` and filters.

- Command appears to hang.
  - Cause: blocked network/API call or stalled DB route.
  - Fix: rerun in container with explicit `--db-uri`, verify OpenAI egress and DB reachability.

## Quick Health Checks
- DB reachable:
```bash
psql "postgresql://postgres:postgres@localhost:5432/devembed" -c "select current_database();"
```

- Tables exist:
```bash
psql "postgresql://postgres:postgres@localhost:5432/devembed" -c "\dt public.api_*"
```
