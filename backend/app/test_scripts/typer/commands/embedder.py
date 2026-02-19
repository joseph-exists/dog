"""
Embedder Query Commands

Typer wrappers around embedder vector query utilities.
"""
from __future__ import annotations

import asyncio
import json
import os
from typing import Annotated

import typer

try:
    from backend.app.test_scripts.embedder.utils import api_embedder_query, embedded_code_query
except ModuleNotFoundError:
    from app.test_scripts.embedder.utils import api_embedder_query, embedded_code_query


app = typer.Typer(help="Embedding query commands for API/OpenAPI and embedded code chunks")


def _parse_csv(value: str | None) -> list[str] | None:
    if not value:
        return None
    parts = [item.strip() for item in value.split(",")]
    values = [item for item in parts if item]
    return values or None


def _require_openai_api_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        typer.secho("OPENAI_API_KEY is required to embed the query text", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)


@app.command("api-query")
def api_query(
    query: Annotated[str, typer.Option("--query", help="Natural language query text.")],
    db_uri: Annotated[
        str | None,
        typer.Option("--db-uri", help="Database URI (defaults to DATABASE_URL/ASYNC_DATABASE_URL)."),
    ] = None,
    table: Annotated[str, typer.Option("--table", help="Target table name.")] = api_embedder_query.DEFAULT_TABLE_NAME,
    top_k: Annotated[int, typer.Option("--top-k", help="Number of nearest chunks to return.")] = 5,
    model: Annotated[str, typer.Option("--model", help="Embedding model name.")] = api_embedder_query.DEFAULT_EMBEDDING_MODEL,
    dimensions: Annotated[int, typer.Option("--dimensions", help="Embedding vector dimensions.")] = api_embedder_query.DEFAULT_EMBEDDING_DIMENSIONS,
    service: Annotated[str | None, typer.Option("--service", help="Optional OpenAPI service/title filter.")] = None,
    version: Annotated[str | None, typer.Option("--version", help="Optional OpenAPI version filter.")] = None,
    tags: Annotated[str | None, typer.Option("--tags", help="Optional comma-separated tag names.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output JSON instead of plain text.")] = False,
    chunk_chars: Annotated[int, typer.Option("--chunk-chars", help="Max chars for chunk text in text mode.")] = 300,
) -> None:
    """Query OpenAPI embeddings stored in Postgres pgvector."""
    _require_openai_api_key()

    resolved_db_uri = db_uri or api_embedder_query._resolve_default_db_uri()
    if not resolved_db_uri:
        typer.secho(
            "Database URI is required. Pass --db-uri or set DATABASE_URL/ASYNC_DATABASE_URL",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)
    if top_k <= 0:
        typer.secho("--top-k must be > 0", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    if chunk_chars < 0:
        typer.secho("--chunk-chars must be >= 0", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    rows = asyncio.run(
        api_embedder_query.search_openapi_embeddings(
            db_uri=resolved_db_uri,
            table_name=table,
            query=query,
            top_k=top_k,
            model=model,
            dimensions=dimensions,
            service=service,
            version=version,
            tags=_parse_csv(tags),
        )
    )

    if json_output:
        typer.echo(json.dumps([dict(row) for row in rows], indent=2, default=str))
        return

    api_embedder_query._render_text(rows=rows, chunk_chars=chunk_chars)


@app.command("code-query")
def code_query(
    query: Annotated[str, typer.Option("--query", help="Natural language query text.")],
    db_uri: Annotated[
        str | None,
        typer.Option("--db-uri", help="Database URI (defaults to DATABASE_URL/ASYNC_DATABASE_URL)."),
    ] = None,
    table: Annotated[str, typer.Option("--table", help="Target table name.")] = embedded_code_query.DEFAULT_TABLE_NAME,
    top_k: Annotated[int, typer.Option("--top-k", help="Number of nearest chunks to return.")] = 5,
    model: Annotated[str, typer.Option("--model", help="Embedding model name.")] = embedded_code_query.DEFAULT_EMBEDDING_MODEL,
    dimensions: Annotated[int, typer.Option("--dimensions", help="Embedding vector dimensions.")] = embedded_code_query.DEFAULT_EMBEDDING_DIMENSIONS,
    corpus: Annotated[str | None, typer.Option("--corpus", help="Optional corpus filter (for example: exported).")] = None,
    kinds: Annotated[str | None, typer.Option("--kinds", help="Optional comma-separated kinds.")] = None,
    symbol_like: Annotated[str | None, typer.Option("--symbol-like", help="Optional symbol substring filter.")] = None,
    source_files: Annotated[str | None, typer.Option("--source-files", help="Optional comma-separated source files.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output JSON instead of plain text.")] = False,
    chunk_chars: Annotated[int, typer.Option("--chunk-chars", help="Max chars for snippet text in text mode.")] = 500,
) -> None:
    """Query embedded SDK/types/schema chunks stored in Postgres pgvector."""
    _require_openai_api_key()

    resolved_db_uri = db_uri or embedded_code_query._resolve_default_db_uri()
    if not resolved_db_uri:
        typer.secho(
            "Database URI is required. Pass --db-uri or set DATABASE_URL/ASYNC_DATABASE_URL",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)
    if top_k <= 0:
        typer.secho("--top-k must be > 0", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    if chunk_chars < 0:
        typer.secho("--chunk-chars must be >= 0", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    rows = asyncio.run(
        embedded_code_query.search_code_embeddings(
            db_uri=resolved_db_uri,
            table_name=table,
            query=query,
            top_k=top_k,
            model=model,
            dimensions=dimensions,
            corpus=corpus,
            kinds=_parse_csv(kinds),
            symbol_like=symbol_like,
            source_files=_parse_csv(source_files),
        )
    )

    if json_output:
        typer.echo(json.dumps([dict(row) for row in rows], indent=2, default=str))
        return

    embedded_code_query._render_text(rows=rows, chunk_chars=chunk_chars)
