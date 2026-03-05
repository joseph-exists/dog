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
DEFAULT_TABLE_NAME = "api_code_chunks"
DEFAULT_CORPUS = "exported"
DEFAULT_FILES = ("sdk.gen.ts", "types.gen.ts", "schemas.gen.ts")
DEFAULT_MAX_EMBED_CHARS = 12000
IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

TYPE_DECL_RE = re.compile(
    r"(?P<doc>/\*\*[\s\S]*?\*/\s*)?export\s+type\s+(?P<name>[A-Za-z0-9_]+)\s*=",
    re.MULTILINE,
)
CLASS_RE = re.compile(r"export\s+class\s+(?P<name>[A-Za-z0-9_]+)\s*\{", re.MULTILINE)
METHOD_RE = re.compile(
    r"(?P<doc>/\*\*[\s\S]*?\*/\s*)?"
    r"(?:public\s+)?static\s+(?P<method>[A-Za-z0-9_]+)"
    r"\((?P<params>[^)]*)\)\s*:\s*(?P<return>[^{]+)\{",
    re.MULTILINE,
)
SCHEMA_RE = re.compile(
    r"export\s+const\s+(?P<name>[A-Za-z0-9_]+)\s*=\s*\{", re.MULTILINE
)
REF_RE = re.compile(r"#/components/schemas/(?P<name>[A-Za-z0-9_]+)")
JSDOC_PARAM_RE = re.compile(r"@param\s+([^\n\r]+)")
JSDOC_RET_RE = re.compile(r"@returns?\s+([^\n\r]+)")


@dataclass(slots=True)
class CodeChunk:
    chunk_key: str
    source_file: str
    symbol: str
    kind: str
    raw_text: str
    embed_text: str
    metadata: dict[str, Any]
    start_line: int
    end_line: int


def _validate_identifier(name: str) -> str:
    if not IDENTIFIER_RE.match(name):
        raise ValueError(f"Invalid SQL identifier: {name}")
    return name


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


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"


def _line_number(text: str, idx: int) -> int:
    return text.count("\n", 0, idx) + 1


def _clean_jsdoc(doc: str | None) -> str:
    if not doc:
        return ""
    lines: list[str] = []
    for raw in doc.splitlines():
        line = raw.strip()
        line = line.removeprefix("/**").removesuffix("*/").strip()
        line = line.removeprefix("*").strip()
        if line:
            lines.append(line)
    return "\n".join(lines).strip()


def _find_matching_brace(text: str, open_index: int) -> int:
    depth = 0
    quote: str | None = None
    escaped = False
    in_line_comment = False
    in_block_comment = False
    idx = open_index

    while idx < len(text):
        ch = text[idx]
        nxt = text[idx + 1] if idx + 1 < len(text) else ""

        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
            idx += 1
            continue

        if in_block_comment:
            if ch == "*" and nxt == "/":
                in_block_comment = False
                idx += 2
                continue
            idx += 1
            continue

        if quote:
            if escaped:
                escaped = False
                idx += 1
                continue
            if ch == "\\":
                escaped = True
                idx += 1
                continue
            if ch == quote:
                quote = None
            idx += 1
            continue

        if ch == "/" and nxt == "/":
            in_line_comment = True
            idx += 2
            continue
        if ch == "/" and nxt == "*":
            in_block_comment = True
            idx += 2
            continue
        if ch in {"'", '"', "`"}:
            quote = ch
            idx += 1
            continue
        if ch == "{":
            depth += 1
            idx += 1
            continue
        if ch == "}":
            depth -= 1
            if depth == 0:
                return idx
            idx += 1
            continue

        idx += 1

    raise ValueError("Unbalanced braces while parsing generated TypeScript")


def _find_type_statement_end(text: str, start_index: int) -> int:
    braces = 0
    brackets = 0
    parens = 0
    quote: str | None = None
    escaped = False
    in_line_comment = False
    in_block_comment = False
    idx = start_index

    while idx < len(text):
        ch = text[idx]
        nxt = text[idx + 1] if idx + 1 < len(text) else ""

        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
            idx += 1
            continue

        if in_block_comment:
            if ch == "*" and nxt == "/":
                in_block_comment = False
                idx += 2
                continue
            idx += 1
            continue

        if quote:
            if escaped:
                escaped = False
                idx += 1
                continue
            if ch == "\\":
                escaped = True
                idx += 1
                continue
            if ch == quote:
                quote = None
            idx += 1
            continue

        if ch == "/" and nxt == "/":
            in_line_comment = True
            idx += 2
            continue
        if ch == "/" and nxt == "*":
            in_block_comment = True
            idx += 2
            continue
        if ch in {"'", '"', "`"}:
            quote = ch
            idx += 1
            continue
        if ch == "{":
            braces += 1
            idx += 1
            continue
        if ch == "}":
            braces -= 1
            idx += 1
            continue
        if ch == "[":
            brackets += 1
            idx += 1
            continue
        if ch == "]":
            brackets -= 1
            idx += 1
            continue
        if ch == "(":
            parens += 1
            idx += 1
            continue
        if ch == ")":
            parens -= 1
            idx += 1
            continue
        if ch == ";" and braces == 0 and brackets == 0 and parens == 0:
            return idx
        idx += 1

    raise ValueError("Could not find end of type declaration")


def _extract_type_refs(raw_text: str, known_symbols: set[str]) -> list[str]:
    matches = set(re.findall(r"\b([A-Z][A-Za-z0-9_]*)\b", raw_text))
    return sorted(matches.intersection(known_symbols))


def _extract_doc_fields(doc_clean: str) -> tuple[str, list[str], str | None]:
    if not doc_clean:
        return "", [], None

    summary_lines: list[str] = []
    for line in doc_clean.splitlines():
        if line.startswith("@"):
            continue
        summary_lines.append(line)
    summary = " ".join(summary_lines).strip()

    params = [m.group(1).strip() for m in JSDOC_PARAM_RE.finditer(doc_clean)]
    ret_match = JSDOC_RET_RE.search(doc_clean)
    returns = ret_match.group(1).strip() if ret_match else None
    return summary, params, returns


def _extract_sdk_chunks(source_file: str, text: str) -> list[CodeChunk]:
    chunks: list[CodeChunk] = []

    for class_match in CLASS_RE.finditer(text):
        class_name = class_match.group("name")
        class_open = class_match.end() - 1
        class_end = _find_matching_brace(text, class_open)
        class_body = text[class_open + 1 : class_end]
        class_body_offset = class_open + 1

        for method_match in METHOD_RE.finditer(class_body):
            method_name = method_match.group("method")
            method_open = class_body_offset + method_match.end() - 1
            method_end = _find_matching_brace(text, method_open)
            method_start = class_body_offset + method_match.start()
            raw_text = text[method_start : method_end + 1]

            doc_clean = _clean_jsdoc(method_match.group("doc"))
            summary, doc_params, doc_returns = _extract_doc_fields(doc_clean)
            signature_params = method_match.group("params").strip()
            signature_return = method_match.group("return").strip()

            http_method_match = re.search(r"method:\s*'([^']+)'", raw_text)
            path_match = re.search(r"url:\s*'([^']+)'", raw_text)
            request_type_match = re.search(r"\(\s*data:\s*([A-Za-z0-9_]+)", raw_text)
            response_type_match = re.search(
                r"CancelablePromise<\s*([A-Za-z0-9_]+)\s*>", raw_text
            )

            http_method = http_method_match.group(1) if http_method_match else None
            path = path_match.group(1) if path_match else None
            request_type = (
                request_type_match.group(1) if request_type_match else None
            )
            response_type = (
                response_type_match.group(1) if response_type_match else None
            )
            refs = sorted(set(REF_RE.findall(raw_text)))
            symbol = f"{class_name}.{method_name}"

            embed_lines = [
                f"KIND: sdk_method",
                f"SYMBOL: {symbol}",
            ]
            if http_method:
                embed_lines.append(f"HTTP_METHOD: {http_method}")
            if path:
                embed_lines.append(f"PATH: {path}")
            if request_type:
                embed_lines.append(f"REQUEST_TYPE: {request_type}")
            if response_type:
                embed_lines.append(f"RESPONSE_TYPE: {response_type}")
            if summary:
                embed_lines.append(f"SUMMARY: {summary}")
            if doc_params:
                embed_lines.append(f"PARAMS: {', '.join(doc_params)}")
            elif signature_params:
                embed_lines.append(f"SIGNATURE_PARAMS: {signature_params}")
            if doc_returns:
                embed_lines.append(f"RETURNS: {doc_returns}")
            else:
                embed_lines.append(f"SIGNATURE_RETURN: {signature_return}")
            if refs:
                embed_lines.append(f"SCHEMA_REFS: {', '.join(refs)}")
            embed_lines.append("")
            embed_lines.append("SOURCE:")
            embed_lines.append(raw_text.strip())

            metadata: dict[str, Any] = {
                "kind": "sdk_method",
                "class_name": class_name,
                "method_name": method_name,
                "http_method": http_method,
                "path": path,
                "request_type": request_type,
                "response_type": response_type,
                "summary": summary or None,
                "doc_params": doc_params,
                "doc_returns": doc_returns,
                "schema_refs": refs,
            }

            chunks.append(
                CodeChunk(
                    chunk_key=f"sdk:{symbol}",
                    source_file=source_file,
                    symbol=symbol,
                    kind="sdk_method",
                    raw_text=raw_text.strip(),
                    embed_text="\n".join(embed_lines),
                    metadata=metadata,
                    start_line=_line_number(text, method_start),
                    end_line=_line_number(text, method_end),
                )
            )

    return chunks


def _extract_type_chunks(source_file: str, text: str) -> list[CodeChunk]:
    chunks: list[CodeChunk] = []
    type_names = {m.group("name") for m in TYPE_DECL_RE.finditer(text)}

    for type_match in TYPE_DECL_RE.finditer(text):
        name = type_match.group("name")
        eq_index = text.find("=", type_match.start(), type_match.end())
        end_index = _find_type_statement_end(text, eq_index + 1)
        raw_text = text[type_match.start() : end_index + 1]
        doc_clean = _clean_jsdoc(type_match.group("doc"))
        summary, _, _ = _extract_doc_fields(doc_clean)
        refs = [ref for ref in _extract_type_refs(raw_text, type_names) if ref != name]

        embed_lines = [
            "KIND: type",
            f"SYMBOL: {name}",
        ]
        if summary:
            embed_lines.append(f"SUMMARY: {summary}")
        if refs:
            embed_lines.append(f"TYPE_REFS: {', '.join(refs)}")
        embed_lines.append("")
        embed_lines.append("SOURCE:")
        embed_lines.append(raw_text.strip())

        chunks.append(
            CodeChunk(
                chunk_key=f"type:{name}",
                source_file=source_file,
                symbol=name,
                kind="type",
                raw_text=raw_text.strip(),
                embed_text="\n".join(embed_lines),
                metadata={
                    "kind": "type",
                    "summary": summary or None,
                    "type_refs": refs,
                },
                start_line=_line_number(text, type_match.start()),
                end_line=_line_number(text, end_index),
            )
        )

    return chunks


def _extract_schema_chunks(source_file: str, text: str) -> list[CodeChunk]:
    chunks: list[CodeChunk] = []

    for schema_match in SCHEMA_RE.finditer(text):
        name = schema_match.group("name")
        open_index = schema_match.end() - 1
        close_index = _find_matching_brace(text, open_index)

        tail_match = re.match(r"\s*as\s+const\s*;", text[close_index + 1 :])
        end_index = (
            close_index + 1 + tail_match.end() if tail_match else close_index + 1
        )
        raw_text = text[schema_match.start() : end_index]
        refs = sorted(set(REF_RE.findall(raw_text)))

        title_match = re.search(r"title:\s*'([^']+)'", raw_text)
        description_match = re.search(r"description:\s*'([^']+)'", raw_text)
        title = title_match.group(1) if title_match else None
        description = description_match.group(1) if description_match else None

        symbol = name.removesuffix("Schema")
        embed_lines = [
            "KIND: schema",
            f"SYMBOL: {symbol}",
            f"CONST_NAME: {name}",
        ]
        if title:
            embed_lines.append(f"TITLE: {title}")
        if description:
            embed_lines.append(f"DESCRIPTION: {description}")
        if refs:
            embed_lines.append(f"SCHEMA_REFS: {', '.join(refs)}")
        embed_lines.append("")
        embed_lines.append("SOURCE:")
        embed_lines.append(raw_text.strip())

        chunks.append(
            CodeChunk(
                chunk_key=f"schema:{symbol}",
                source_file=source_file,
                symbol=symbol,
                kind="schema",
                raw_text=raw_text.strip(),
                embed_text="\n".join(embed_lines),
                metadata={
                    "kind": "schema",
                    "const_name": name,
                    "title": title,
                    "description": description,
                    "schema_refs": refs,
                },
                start_line=_line_number(text, schema_match.start()),
                end_line=_line_number(text, end_index),
            )
        )

    return chunks


def _split_source_text(
    text: str, max_chars: int, overlap_lines: int = 4
) -> list[tuple[str, int, int]]:
    lines = text.splitlines()
    if not lines:
        return [("", 0, 0)]

    parts: list[tuple[str, int, int]] = []
    start = 0
    while start < len(lines):
        current_chars = 0
        end = start
        while end < len(lines):
            line_len = len(lines[end]) + 1
            if end > start and current_chars + line_len > max_chars:
                break
            current_chars += line_len
            end += 1

        if end == start:
            end += 1

        part_text = "\n".join(lines[start:end]).strip()
        parts.append((part_text, start, end))
        if end >= len(lines):
            break
        start = max(0, end - overlap_lines)

    return parts


def _expand_oversized_chunks(
    chunks: list[CodeChunk],
    *,
    max_embed_chars: int,
) -> list[CodeChunk]:
    expanded: list[CodeChunk] = []

    for chunk in chunks:
        if len(chunk.embed_text) <= max_embed_chars:
            expanded.append(chunk)
            continue

        header, sep, source = chunk.embed_text.partition("\nSOURCE:\n")
        if not sep:
            # Fallback: split embed_text directly when SOURCE marker is missing.
            source = chunk.embed_text
            header = "KIND: split\nSOURCE:"

        source_budget = max(500, max_embed_chars - len(header) - len("\nSOURCE:\n"))
        source_parts = _split_source_text(source, source_budget)
        total_parts = len(source_parts)

        for idx, (part_text, rel_start, rel_end) in enumerate(source_parts, start=1):
            part_key = f"{chunk.chunk_key}::part{idx}"
            metadata = dict(chunk.metadata)
            metadata["parent_chunk_key"] = chunk.chunk_key
            metadata["part_index"] = idx
            metadata["part_count"] = total_parts

            part_start_line = chunk.start_line + rel_start
            part_end_line = max(part_start_line, chunk.start_line + rel_end - 1)
            part_embed_text = f"{header}\nSOURCE:\n{part_text}".strip()

            expanded.append(
                CodeChunk(
                    chunk_key=part_key,
                    source_file=chunk.source_file,
                    symbol=chunk.symbol,
                    kind=chunk.kind,
                    raw_text=part_text,
                    embed_text=part_embed_text,
                    metadata=metadata,
                    start_line=part_start_line,
                    end_line=part_end_line,
                )
            )

    return expanded


def extract_code_chunks_from_exported(
    source_dir: Path,
    file_names: list[str],
) -> list[CodeChunk]:
    all_chunks: list[CodeChunk] = []

    for file_name in file_names:
        file_path = source_dir / file_name
        if not file_path.exists():
            raise FileNotFoundError(f"Exported file not found: {file_path}")

        text = file_path.read_text(encoding="utf-8")
        if file_name == "sdk.gen.ts":
            chunks = _extract_sdk_chunks(file_name, text)
        elif file_name == "types.gen.ts":
            chunks = _extract_type_chunks(file_name, text)
        elif file_name == "schemas.gen.ts":
            chunks = _extract_schema_chunks(file_name, text)
        else:
            raise ValueError(
                f"Unsupported file '{file_name}'. Supported files: {', '.join(DEFAULT_FILES)}"
            )

        all_chunks.extend(chunks)

    if not all_chunks:
        raise ValueError(f"No chunks produced from {source_dir}")
    return all_chunks


async def _embed_chunks(
    *,
    chunks: list[CodeChunk],
    model: str,
    dimensions: int,
    concurrency: int,
) -> list[tuple[CodeChunk, list[float]]]:
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    semaphore = asyncio.Semaphore(concurrency)

    async def run(chunk: CodeChunk) -> tuple[CodeChunk, list[float]]:
        async with semaphore:
            response = await client.embeddings.create(
                model=model,
                input=chunk.embed_text,
                dimensions=dimensions,
            )
            return chunk, response.data[0].embedding

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
            corpus TEXT NOT NULL,
            chunk_key TEXT NOT NULL,
            source_file TEXT NOT NULL,
            symbol TEXT NOT NULL,
            kind TEXT NOT NULL,
            start_line INTEGER NOT NULL,
            end_line INTEGER NOT NULL,
            raw_text TEXT NOT NULL,
            embed_text TEXT NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
            embedding VECTOR({dimensions}) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (corpus, chunk_key)
        )
        """
    )


async def index_exported_code_chunks(
    *,
    source_dir: Path,
    file_names: list[str],
    db_uri: str,
    table_name: str,
    corpus: str,
    model: str,
    dimensions: int,
    concurrency: int,
    max_embed_chars: int,
    replace_existing: bool,
    ensure_schema: bool,
) -> None:
    table_name = _validate_identifier(table_name)
    base_chunks = extract_code_chunks_from_exported(source_dir, file_names)
    chunks = _expand_oversized_chunks(base_chunks, max_embed_chars=max_embed_chars)
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

            if replace_existing:
                await conn.execute(
                    f"DELETE FROM {table_name} WHERE corpus = $1",
                    corpus,
                )

            records = [
                (
                    corpus,
                    chunk.chunk_key,
                    chunk.source_file,
                    chunk.symbol,
                    chunk.kind,
                    chunk.start_line,
                    chunk.end_line,
                    chunk.raw_text,
                    chunk.embed_text,
                    json.dumps(chunk.metadata),
                    _vector_literal(embedding),
                )
                for chunk, embedding in embedded
            ]

            await conn.executemany(
                f"""
                INSERT INTO {table_name} (
                    corpus,
                    chunk_key,
                    source_file,
                    symbol,
                    kind,
                    start_line,
                    end_line,
                    raw_text,
                    embed_text,
                    metadata,
                    embedding
                )
                VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10::jsonb, $11::vector
                )
                ON CONFLICT (corpus, chunk_key)
                DO UPDATE SET
                    source_file = EXCLUDED.source_file,
                    symbol = EXCLUDED.symbol,
                    kind = EXCLUDED.kind,
                    start_line = EXCLUDED.start_line,
                    end_line = EXCLUDED.end_line,
                    raw_text = EXCLUDED.raw_text,
                    embed_text = EXCLUDED.embed_text,
                    metadata = EXCLUDED.metadata,
                    embedding = EXCLUDED.embedding,
                    updated_at = NOW()
                """,
                records,
            )
    finally:
        await conn.close()

    by_kind: dict[str, int] = {}
    for chunk in chunks:
        by_kind[chunk.kind] = by_kind.get(chunk.kind, 0) + 1
    print(f"Indexed {len(chunks)} chunks into {table_name} (corpus={corpus}).")
    print(f"Breakdown: {by_kind}")


def _parse_csv_list(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Embed exported SDK/types/schemas chunks into Postgres pgvector.",
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "exported",
        help="Directory containing sdk.gen.ts, types.gen.ts, schemas.gen.ts.",
    )
    parser.add_argument(
        "--files",
        type=str,
        default=",".join(DEFAULT_FILES),
        help="Comma-separated file list. Supported: sdk.gen.ts,types.gen.ts,schemas.gen.ts",
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
        "--corpus",
        type=str,
        default=DEFAULT_CORPUS,
        help="Corpus namespace (used for scoped replace/upsert).",
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
        "--max-embed-chars",
        type=int,
        default=DEFAULT_MAX_EMBED_CHARS,
        help="Max chars per embedding input; larger chunks are split into ::partN.",
    )
    parser.add_argument(
        "--no-replace",
        action="store_true",
        help="Do not delete existing rows for this corpus before upsert.",
    )
    parser.add_argument(
        "--no-ensure-schema",
        action="store_true",
        help="Skip CREATE EXTENSION/TABLE step.",
    )
    return parser


async def _main() -> None:
    args = _build_parser().parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required to generate embeddings")
    if not args.db_uri:
        raise RuntimeError(
            "Database URI is required. Pass --db-uri or set DATABASE_URL/ASYNC_DATABASE_URL"
        )
    if args.concurrency <= 0:
        raise ValueError("--concurrency must be > 0")
    if args.dimensions <= 0:
        raise ValueError("--dimensions must be > 0")
    if args.max_embed_chars < 1000:
        raise ValueError("--max-embed-chars must be >= 1000")

    file_names = _parse_csv_list(args.files)
    await index_exported_code_chunks(
        source_dir=args.source_dir,
        file_names=file_names,
        db_uri=args.db_uri,
        table_name=args.table,
        corpus=args.corpus,
        model=args.model,
        dimensions=args.dimensions,
        concurrency=args.concurrency,
        max_embed_chars=args.max_embed_chars,
        replace_existing=not args.no_replace,
        ensure_schema=not args.no_ensure_schema,
    )


if __name__ == "__main__":
    asyncio.run(_main())
