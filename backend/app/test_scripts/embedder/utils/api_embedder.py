from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import asyncpg
from openai import AsyncOpenAI

DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_EMBEDDING_DIMENSIONS = 1536
DEFAULT_TABLE_NAME = "api_areas"
IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(slots=True)
class OpenApiTagChunk:
    tag_name: str
    tag_description: str | None
    chunk_text: str
    service: str | None
    version: str | None


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"


def _normalize_db_uri(uri: str) -> str:
    if uri.startswith("postgresql+asyncpg://"):
        return uri.replace("postgresql+asyncpg://", "postgresql://", 1)
    if uri.startswith("postgresql+psycopg://"):
        return uri.replace("postgresql+psycopg://", "postgresql://", 1)
    return uri


def _resolve_default_db_uri() -> str | None:
    env_uri = (
        os.getenv("DEVEMBED_ASYNC_DATABASE_URL")
        or os.getenv("DEVEMBED_DATABASE_URL")
        or os.getenv("ASYNC_DATABASE_URL")
        or os.getenv("DATABASE_URL")
    )
    if env_uri:
        return _prefer_devembed_db(env_uri)

    try:
        from app.core.config import settings

        return _prefer_devembed_db(str(settings.ASYNC_SQLALCHEMY_DATABASE_URI))
    except Exception:
        return None


def _prefer_devembed_db(uri: str) -> str:
    parts = urlsplit(uri)
    if not parts.scheme.startswith("postgresql"):
        return uri

    path = parts.path or ""
    if path in {"", "/"}:
        new_path = "/devembed"
    else:
        prefix, _sep, _db_name = path.rpartition("/")
        new_path = f"{prefix}/devembed" if prefix else "/devembed"

    return urlunsplit((parts.scheme, parts.netloc, new_path, parts.query, parts.fragment))


def _validate_identifier(name: str) -> str:
    if not IDENTIFIER_RE.match(name):
        raise ValueError(f"Invalid SQL identifier: {name}")
    return name


def extract_tag_chunks_from_openapi(spec_json_path: Path) -> list[OpenApiTagChunk]:
    with spec_json_path.open("r", encoding="utf-8") as handle:
        spec: dict[str, Any] = json.load(handle)

    info = spec.get("info", {})
    service = info.get("title")
    version = info.get("version")

    tag_index = {
        tag.get("name"): tag
        for tag in spec.get("tags", [])
        if isinstance(tag, dict) and tag.get("name")
    }

    tag_ops: dict[str, list[dict[str, Any]]] = {}
    for path, path_ops in spec.get("paths", {}).items():
        if not isinstance(path_ops, dict):
            continue

        for method, op in path_ops.items():
            if not isinstance(op, dict):
                continue

            tags = op.get("tags") or ["untagged"]
            for tag_name in tags:
                tag_ops.setdefault(tag_name, []).append(
                    {
                        "path": path,
                        "method": str(method).upper(),
                        "summary": op.get("summary"),
                        "description": op.get("description") or "",
                    }
                )

    chunks: list[OpenApiTagChunk] = []
    for tag_name, operations in sorted(tag_ops.items()):
        tag_info = tag_index.get(tag_name, {})
        tag_description = tag_info.get("description")

        lines = [
            f"API AREA: {tag_name}",
            f"DESCRIPTION: {tag_description or '(no description)'}",
            "",
            "OPERATIONS:",
        ]

        for op in operations:
            summary = op.get("summary") or op.get("description") or "No summary"
            lines.append(f"- {op['method']} {op['path']}: {summary}")

        chunks.append(
            OpenApiTagChunk(
                tag_name=tag_name,
                tag_description=tag_description,
                chunk_text="\n".join(lines),
                service=service,
                version=version,
            )
        )

    return chunks


async def _embed_chunk(
    *,
    client: AsyncOpenAI,
    chunk: OpenApiTagChunk,
    model: str,
    dimensions: int,
) -> tuple[OpenApiTagChunk, list[float]]:
    response = await client.embeddings.create(
        model=model,
        input=chunk.chunk_text,
        dimensions=dimensions,
    )
    return chunk, response.data[0].embedding


async def _embed_chunks(
    *,
    chunks: list[OpenApiTagChunk],
    model: str,
    dimensions: int,
    concurrency: int,
) -> list[tuple[OpenApiTagChunk, list[float]]]:
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    semaphore = asyncio.Semaphore(concurrency)

    async def run(chunk: OpenApiTagChunk) -> tuple[OpenApiTagChunk, list[float]]:
        async with semaphore:
            return await _embed_chunk(
                client=client,
                chunk=chunk,
                model=model,
                dimensions=dimensions,
            )

    return await asyncio.gather(*(run(chunk) for chunk in chunks))


async def _ensure_schema(
    conn: asyncpg.Connection,
    *,
    table_name: str,
    dimensions: int,
) -> None:
    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    await conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id BIGSERIAL PRIMARY KEY,
            tag_name TEXT NOT NULL,
            tag_description TEXT,
            chunk_text TEXT NOT NULL,
            embedding VECTOR({dimensions}) NOT NULL,
            service TEXT,
            version TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE (service, version, tag_name)
        )
        """
    )


async def index_openapi_to_pgvector(
    *,
    spec_json_path: Path,
    db_uri: str,
    table_name: str,
    model: str,
    dimensions: int,
    concurrency: int,
    replace_existing: bool,
    ensure_schema: bool,
) -> None:
    table_name = _validate_identifier(table_name)
    chunks = extract_tag_chunks_from_openapi(spec_json_path)
    if not chunks:
        raise ValueError(f"No OpenAPI operations found in {spec_json_path}")

    embedded = await _embed_chunks(
        chunks=chunks,
        model=model,
        dimensions=dimensions,
        concurrency=concurrency,
    )

    conn = await asyncpg.connect(_normalize_db_uri(db_uri))
    try:
        async with conn.transaction():
            if ensure_schema:
                await _ensure_schema(conn, table_name=table_name, dimensions=dimensions)

            service = chunks[0].service
            version = chunks[0].version
            if replace_existing:
                await conn.execute(
                    f"DELETE FROM {table_name} WHERE service = $1 AND version = $2",
                    service,
                    version,
                )

            records = [
                (
                    chunk.tag_name,
                    chunk.tag_description,
                    chunk.chunk_text,
                    _vector_literal(embedding),
                    chunk.service,
                    chunk.version,
                )
                for chunk, embedding in embedded
            ]

            await conn.executemany(
                f"""
                INSERT INTO {table_name} (
                    tag_name,
                    tag_description,
                    chunk_text,
                    embedding,
                    service,
                    version
                )
                VALUES ($1, $2, $3, $4::vector, $5, $6)
                ON CONFLICT (service, version, tag_name)
                DO UPDATE SET
                    tag_description = EXCLUDED.tag_description,
                    chunk_text = EXCLUDED.chunk_text,
                    embedding = EXCLUDED.embedding,
                    created_at = NOW()
                """,
                records,
            )
    finally:
        await conn.close()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Embed OpenAPI tags into Postgres pgvector table.",
    )
    parser.add_argument(
        "--spec",
        type=Path,
        default=Path(__file__).with_name("openapi.json"),
        help="Path to openapi.json",
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
        "--model",
        type=str,
        default=DEFAULT_EMBEDDING_MODEL,
        help="Embedding model name.",
    )
    parser.add_argument(
        "--dimensions",
        type=int,
        default=DEFAULT_EMBEDDING_DIMENSIONS,
        help="Embedding vector dimensions.",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=5,
        help="Max concurrent embedding requests.",
    )
    parser.add_argument(
        "--no-replace",
        action="store_true",
        help="Do not delete existing rows for the same service/version before insert.",
    )
    parser.add_argument(
        "--no-ensure-schema",
        action="store_true",
        help="Assume extension/table already exist and skip schema setup.",
    )
    return parser


async def _main() -> None:
    args = _build_parser().parse_args()

    if not args.spec.exists():
        raise FileNotFoundError(f"OpenAPI spec not found: {args.spec}")

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required to generate embeddings")
    if not args.db_uri:
        raise RuntimeError(
            "Database URI is required. Pass --db-uri or set DATABASE_URL/ASYNC_DATABASE_URL"
        )

    await index_openapi_to_pgvector(
        spec_json_path=args.spec,
        db_uri=args.db_uri,
        table_name=args.table,
        model=args.model,
        dimensions=args.dimensions,
        concurrency=args.concurrency,
        replace_existing=not args.no_replace,
        ensure_schema=not args.no_ensure_schema,
    )


if __name__ == "__main__":
    asyncio.run(_main())
