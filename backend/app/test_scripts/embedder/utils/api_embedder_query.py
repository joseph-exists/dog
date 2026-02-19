from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
from pathlib import Path
from typing import Any

import asyncpg
from openai import AsyncOpenAI

DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_EMBEDDING_DIMENSIONS = 1536
DEFAULT_TABLE_NAME = "api_areas"
IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _load_typer_env() -> None:
    env_path = Path(__file__).resolve().parents[2] / "typer" / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        # Backward compatibility: previous file format was a raw API key line.
        if "=" not in line:
            os.environ.setdefault("OPENAI_API_KEY", line)
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and value:
            os.environ.setdefault(key, value)


_load_typer_env()


def _parse_csv(value: str | None) -> list[str] | None:
    if not value:
        return None
    items = [item.strip() for item in value.split(",")]
    filtered = [item for item in items if item]
    return filtered or None


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"


def _normalize_db_uri(uri: str) -> str:
    if uri.startswith("postgresql+asyncpg://"):
        return uri.replace("postgresql+asyncpg://", "postgresql://", 1)
    if uri.startswith("postgresql+psycopg://"):
        return uri.replace("postgresql+psycopg://", "postgresql://", 1)
    return uri


def _resolve_default_db_uri() -> str | None:
    env_uri = os.getenv("ASYNC_DATABASE_URL") or os.getenv("DATABASE_URL")
    if env_uri:
        return env_uri

    try:
        from app.core.config import settings

        return str(settings.ASYNC_SQLALCHEMY_DATABASE_URI)
    except Exception:
        return None


def _validate_identifier(name: str) -> str:
    if not IDENTIFIER_RE.match(name):
        raise ValueError(f"Invalid SQL identifier: {name}")
    return name


async def _embed_query(*, query: str, model: str, dimensions: int) -> list[float]:
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = await client.embeddings.create(
        model=model,
        input=query,
        dimensions=dimensions,
    )
    return response.data[0].embedding


async def search_openapi_embeddings(
    *,
    db_uri: str,
    table_name: str,
    query: str,
    top_k: int,
    model: str,
    dimensions: int,
    service: str | None,
    version: str | None,
    tags: list[str] | None,
) -> list[asyncpg.Record]:
    table_name = _validate_identifier(table_name)
    query_embedding = await _embed_query(query=query, model=model, dimensions=dimensions)
    vector = _vector_literal(query_embedding)

    filters: list[str] = []
    params: list[Any] = [vector]

    if service:
        params.append(service)
        filters.append(f"service = ${len(params)}")
    if version:
        params.append(version)
        filters.append(f"version = ${len(params)}")
    if tags:
        params.append(tags)
        filters.append(f"tag_name = ANY(${len(params)}::text[])")

    where_sql = f"WHERE {' AND '.join(filters)}" if filters else ""
    params.append(top_k)

    sql = f"""
        SELECT
            tag_name,
            tag_description,
            service,
            version,
            chunk_text,
            embedding <=> $1::vector AS distance
        FROM {table_name}
        {where_sql}
        ORDER BY distance ASC
        LIMIT ${len(params)}
    """

    conn = await asyncpg.connect(_normalize_db_uri(db_uri))
    try:
        return await conn.fetch(sql, *params)
    finally:
        await conn.close()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Query OpenAPI embeddings stored in Postgres pgvector.",
    )
    parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="Natural language query text.",
    )
    parser.add_argument(
        "--db-uri",
        type=str,
        default=_resolve_default_db_uri(),
        help="Database URI (defaults to app settings).",
    )
    parser.add_argument(
        "--table",
        type=str,
        default=DEFAULT_TABLE_NAME,
        help="Target table name.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of nearest chunks to return.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_EMBEDDING_MODEL,
        help="Embedding model name for the query embedding.",
    )
    parser.add_argument(
        "--dimensions",
        type=int,
        default=DEFAULT_EMBEDDING_DIMENSIONS,
        help="Embedding vector dimensions.",
    )
    parser.add_argument(
        "--service",
        type=str,
        default=None,
        help="Optional service/title filter from openapi.info.title.",
    )
    parser.add_argument(
        "--version",
        type=str,
        default=None,
        help="Optional OpenAPI version filter from openapi.info.version.",
    )
    parser.add_argument(
        "--tags",
        type=str,
        default=None,
        help="Optional comma-separated list of tag names to restrict search.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON instead of plain text.",
    )
    parser.add_argument(
        "--chunk-chars",
        type=int,
        default=300,
        help="Max chunk_text chars to print in text mode (0 for full chunk).",
    )
    return parser


def _render_text(rows: list[asyncpg.Record], chunk_chars: int) -> None:
    if not rows:
        print("No matches found.")
        return

    for idx, row in enumerate(rows, start=1):
        chunk_text = row["chunk_text"]
        if chunk_chars > 0:
            chunk_text = chunk_text[:chunk_chars]
            if len(row["chunk_text"]) > chunk_chars:
                chunk_text += "..."

        print(f"[{idx}] tag={row['tag_name']} distance={row['distance']:.6f}")
        print(f"    service={row['service']} version={row['version']}")
        if row["tag_description"]:
            print(f"    tag_description={row['tag_description']}")
        print(f"    chunk={chunk_text}")
        print("")


async def _main() -> None:
    args = _build_parser().parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required to embed the query text")
    if not args.db_uri:
        raise RuntimeError(
            "Database URI is required. Pass --db-uri or set DATABASE_URL/ASYNC_DATABASE_URL"
        )
    if args.top_k <= 0:
        raise ValueError("--top-k must be > 0")
    if args.chunk_chars < 0:
        raise ValueError("--chunk-chars must be >= 0")

    rows = await search_openapi_embeddings(
        db_uri=args.db_uri,
        table_name=args.table,
        query=args.query,
        top_k=args.top_k,
        model=args.model,
        dimensions=args.dimensions,
        service=args.service,
        version=args.version,
        tags=_parse_csv(args.tags),
    )

    if args.json:
        print(json.dumps([dict(row) for row in rows], indent=2, default=str))
        return

    _render_text(rows=rows, chunk_chars=args.chunk_chars)


if __name__ == "__main__":
    asyncio.run(_main())
