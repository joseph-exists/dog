# OpenAPI Embedder Reference

This folder contains two scripts:
- `api_embedder.py`: ingest `openapi.json` into Postgres `pgvector`
- `api_embedder_query.py`: semantic search over those embeddings
- `api_code_embedder.py`: ingest exported SDK/types/schemas into a code-focused vector table

## Requirements
- `OPENAI_API_KEY` must be set
- Postgres must have `pgvector` available
- DB URI from `--db-uri` or env (`DATABASE_URL` / `ASYNC_DATABASE_URL`)

## 1) Ingest OpenAPI into Postgres

Default run (uses local `openapi.json` in this folder):

```bash
python3 app/test_scripts/embedder/utils/api_embedder.py
```

Explicit run:

```bash
python3 app/test_scripts/embedder/utils/api_embedder.py \
  --spec app/test_scripts/embedder/utils/openapi.json \
  --db-uri "postgresql://postgres:postgres@db:5432/tinyfoot" \
  --table api_areas \
  --model text-embedding-3-small \
  --dimensions 1536
```

Useful flags:
- `--no-replace`: keep existing rows for same `(service, version)` before upsert
- `--no-ensure-schema`: skip extension/table creation
- `--concurrency 5`: max parallel embedding requests

## 2) Query embedded chunks

Basic semantic search:

```bash
python3 app/test_scripts/embedder/utils/api_embedder_query.py \
  --query "How do I create a repository?" \
  --db-uri "postgresql://USER:PASS@HOST:5432/DB"
```

Filter by service/version/tags:

```bash
python3 app/test_scripts/embedder/utils/api_embedder_query.py \
  --query "How do I create an agent?" \
  --top-k 5
```

JSON output:

```bash
python3 app/test_scripts/embedder/utils/api_embedder_query.py \
  --query "How do I create an issue?" \
  --top-k 3 \
  --json
```

Useful flags:
- `--chunk-chars 300`: truncate chunk preview in text mode (`0` = full chunk)
- `--model text-embedding-3-small`: query embedding model
- `--dimensions 1536`: query vector dimension (must match stored vectors)

## Typical workflow
1. Run `api_embedder.py` whenever `openapi.json` changes.
2. Run `api_embedder_query.py` to test retrieval quality.
3. Tune `--tags`, `--service`, and `--top-k` for better precision.

## 3) Ingest exported code corpus (SDK + types + schemas)

Default run (reads from `app/test_scripts/embedder/exported`):

```bash
python3 app/test_scripts/embedder/utils/api_code_embedder.py
```

Explicit run:

```bash
python3 app/test_scripts/embedder/utils/api_code_embedder.py \
  --source-dir app/test_scripts/embedder/exported \
  --files sdk.gen.ts,types.gen.ts,schemas.gen.ts \
  --db-uri "postgresql://postgres:postgres@db:5432/tinyfoot" \
  --table api_code_chunks \
  --corpus exported \
  --model text-embedding-3-small \
  --dimensions 1536
```

What it stores:
- `sdk.gen.ts` chunks by service method (includes JSDoc + request config)
- `types.gen.ts` chunks by exported type
- `schemas.gen.ts` chunks by exported schema const
- metadata including symbol, kind, source file, line span, and refs

Useful flags:
- `--no-replace`: keep existing rows in the same corpus and upsert by `chunk_key`
- `--no-ensure-schema`: skip extension/table creation
- `--concurrency 5`: max parallel embedding requests
- `--max-embed-chars 12000`: auto-split oversized chunks into `::partN` to avoid embedding context-limit errors
