# Typer Code Agent Guide

Purpose: this file defines how code agents should add, modify, and validate commands in `backend/app/test_scripts/typer/`.

## Scope

- CLI entrypoint: `backend/app/test_scripts/typer/main.py`
- Command modules: `backend/app/test_scripts/typer/commands/*.py`
- Auth helper: `backend/app/test_scripts/typer/auth_helper.py`
- User docs: `backend/app/test_scripts/typer/TYPER-README.md`
- Command catalog: `backend/app/test_scripts/typer/COMMANDS.md`
- Patterns/reference: `backend/app/test_scripts/typer/REFERENCE.md`

## Environment And Execution

Agents must activate the backend virtual environment before validating commands.

- From `backend/`:
```bash
source .venv/bin/activate
```

- From `backend/app/test_scripts/typer/`:
```bash
source ../../../.venv/bin/activate
```

Current CLI import style in `main.py` and command modules uses local absolute imports (`import auth_helper`, `from commands import ...`). For this reason, run validation from the `typer/` directory unless imports are refactored.

- Preferred validation entrypoint:
```bash
python main.py --help
```

## Command Design Constraints (Typer-Specific)

When adding a new command group:

1. Create a new module under `commands/` with:
   - `app = typer.Typer(help="...")`
   - one or more `@app.command()` functions
2. Register the module in `main.py` via:
   - `from commands import <module>`
   - `app.add_typer(<module>.app, name="<group>")`
3. Use `Annotated` + `typer.Argument` / `typer.Option` so help text is explicit.
4. Keep command behavior scriptable:
   - support `--json` on read/list style commands where useful
   - use consistent exit codes (`raise typer.Exit(1)` on failures)
5. For API-backed commands:
   - use `get_authenticated_session()` from `auth_helper.py`
   - use `BASE_URL = "http://localhost:8000/api/v1"` convention unless intentionally different
6. Keep debug output behind `--verbose` and a local `log()` helper.

## Output And Error Conventions

- Success: `typer.secho(..., fg=typer.colors.GREEN)`
- Failure: `typer.secho(..., fg=typer.colors.RED, err=True)` and exit non-zero
- Optional debug: `typer.secho(f"[DEBUG] ...", fg=typer.colors.CYAN)`
- Machine-readable responses: `typer.echo(json.dumps(..., indent=2))`

## Validation Checklist

After edits, validate at minimum:

1. Environment active (`source ../../../.venv/bin/activate` from `typer/`).
2. CLI loads:
```bash
python main.py --help
```
3. New command group loads:
```bash
python main.py <group> --help
```
4. New command help renders:
```bash
python main.py <group> <command> --help
```
5. If command executes network/DB/OpenAI operations, verify argument parsing and required env checks first; run live calls only when required credentials/services are available.

## Embedder Command Notes

The embedder Typer group is registered as `embedder` with:

- `embedder api-query`
- `embedder code-query`

These commands depend on runtime environment values:

- `OPENAI_API_KEY` (required)
- `DATABASE_URL` or `ASYNC_DATABASE_URL` unless `--db-uri` is passed

## Documentation Maintenance Requirements

When CLI behavior changes, keep docs synchronized:

1. Update `TYPER-README.md` for setup/usage examples.
2. Update `COMMANDS.md` with exact command syntax and options.
3. Update `REFERENCE.md` only when introducing a new reusable pattern (not for every feature-specific command).

## Common Pitfalls

- Forgetting to register a new command module in `main.py`.
- Adding options without help text, leading to weak `--help` output.
- Returning error text without non-zero exit status.
- Running validation without activating `backend/.venv`.
- Assuming services are available during validation when only help-level checks were needed.
