"""
Shadow validation commands for Forgejo service accounts.

These helpers load the local `.env` so we can exercise each `SHADOW_*_TOKEN`
against the Forgejo API and confirm the token, login, and repo access behave as
expected.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from collections.abc import Iterable
from typing import Final

import typer
from openapi_client import ApiClient, ApiException, Configuration, UserApi

from app.test_scripts.forge_admin.typer_forge import forge_client

app = typer.Typer(help="Shadow Forgejo verification helpers")

TOKEN_PREFIX: Final[str] = "SHADOW_"
TOKEN_SUFFIX: Final[str] = "_TOKEN"

SERVICE_ACCOUNT_USERNAMES: Final[dict[str, str]] = {
    "users": "SHADOW_USERS",
    "agents": "SHADOW_AGENTS",
    "stories": "SHADOW_STORIES",
    "rooms": "SHADOW_ROOMS",
    "archetypes": "SHADOW_ARCHETYPES",
    "personas": "SHADOW_PERSONAS",
    "qualities": "SHADOW_QUALITIES",
    "traits": "SHADOW_TRAITS",
    "llm_models": "SHADOW_LLMMODELS",
    "user_llm_providers": "SHADOW_USERLLMPROVIDERS",
    "prompts": "SHADOW_PROMPTS",
}

DEFAULT_SHADOW_URL: Final[str] = forge_client.FORGE_URL


@dataclass
class TokenCheckResult:
    env_var: str
    entity_key: str
    expected_login: str
    actual_login: str | None = None
    status: str = "unknown"
    notes: list[str] = field(default_factory=list)
    repo_accessible: bool | None = None


def _find_env_file(explicit: Path | None) -> Path:
    if explicit:
        if explicit.exists():
            return explicit
        raise typer.BadParameter(f".env file not found at {explicit}")

    for candidate in Path(__file__).resolve().parents:
        env_path = candidate / ".env"
        if env_path.exists():
            return env_path

    raise typer.Exit("Unable to locate .env (upward search from CLI module failed)")


def _parse_env_file(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = _strip_quotes(value.strip())
    return env


def _strip_quotes(value: str) -> str:
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def _shadow_url_from_env(env: dict[str, str]) -> str:
    return (
        env.get("SHADOW_FORGEJO_URL")
        or env.get("FORGEJO_ROOT_URL")
        or DEFAULT_SHADOW_URL
    )


def _collect_shadow_tokens(env: dict[str, str]) -> dict[str, str]:
    return {
        key: value
        for key, value in env.items()
        if key.startswith(TOKEN_PREFIX) and key.endswith(TOKEN_SUFFIX)
    }


def _derive_entity_key(env_var: str) -> str:
    return env_var[len(TOKEN_PREFIX) : -len(TOKEN_SUFFIX)].lower()


def _derive_expected_login(entity_key: str) -> str:
    return SERVICE_ACCOUNT_USERNAMES.get(
        entity_key, f"shadow-{entity_key.replace('_', '-')}"
    )


def _check_token(
    *,
    token: str,
    env_var: str,
    entity_key: str,
    expected_login: str,
    base_url: str,
) -> TokenCheckResult:
    result = TokenCheckResult(
        env_var=env_var,
        entity_key=entity_key,
        expected_login=expected_login,
    )

    if not token:
        result.status = "missing_token"
        result.notes.append("empty token value")
        return result

    config = Configuration(host=base_url)
    config.api_key["AuthorizationHeaderToken"] = token
    config.api_key_prefix["AuthorizationHeaderToken"] = "token"
    api_client = ApiClient(config)
    try:
        user_api = UserApi(api_client)
        current = user_api.user_get_current()
        login = current.login
        result.actual_login = login
        result.notes.append(f"login: {login}")
        if login != expected_login:
            result.status = "login_mismatch"
            result.notes.append(f"expected login: {expected_login}")
        else:
            result.status = "ok"

        try:
            user_api.user_current_list_repos(limit=1)
            result.repo_accessible = True
        except ApiException as exc:
            result.repo_accessible = False
            result.notes.append(f"repo list failed: {exc.status} {exc.reason}")
            if result.status == "ok":
                result.status = "repo_warning"
        except Exception as exc:  # pragma: no cover - unlikely
            result.repo_accessible = False
            result.notes.append(f"repo list error: {exc}")
            if result.status == "ok":
                result.status = "repo_warning"
    except ApiException as exc:
        result.status = "auth_failed"
        result.notes.append(f"auth failed: {exc.status} {exc.reason}")
    except Exception as exc:
        result.status = "auth_failed"
        result.notes.append(f"auth error: {exc}")
    finally:
        try:
            api_client.close()
        except Exception:
            pass

    return result


def _format_notes(notes: Iterable[str]) -> list[str]:
    return [note for note in notes if note]


STATUS_SYMBOLS: Final[dict[str, str]] = {
    "ok": "✅",
    "repo_warning": "⚠️",
    "login_mismatch": "⚠️",
    "auth_failed": "❌",
    "missing_token": "⚠️",
}


def _symbol_for_status(status: str) -> str:
    return STATUS_SYMBOLS.get(status, "❔")


def _normalize_entity_choice(choice: str) -> str:
    normalized = choice.strip()
    if not normalized:
        raise typer.BadParameter("Empty entity name supplied to --entity")

    lower = normalized.lower()
    if lower in SERVICE_ACCOUNT_USERNAMES:
        return lower

    upper = normalized.upper()
    if upper.startswith(TOKEN_PREFIX) and upper.endswith(TOKEN_SUFFIX):
        entity = _derive_entity_key(upper)
        if entity in SERVICE_ACCOUNT_USERNAMES:
            return entity

    raise typer.BadParameter(
        f"Unknown shadow account `{choice}`; choose from "
        f"{', '.join(sorted(SERVICE_ACCOUNT_USERNAMES.keys()))} "
        "or supply the full SHADOW_*_TOKEN env var name"
    )


@app.command("validate")
def validate(
    env_file: Path | None = typer.Option(
        None,
        "--env-file",
        "-e",
        help="Explicit path to the .env file that defines the SHADOW_* tokens",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit the validation report as JSON"
    ),
    entities: tuple[str, ...] | None = typer.Option(
        None,
        "--entity",
        "-E",
        help="Restrict validation to the named shadow accounts (entity names or SHADOW_* token names)",
    ),
):
    """
    Validate every SHADOW_*_TOKEN from the repo's .env against the configured
    Forgejo Shadow account.
    """
    env_path = _find_env_file(env_file)
    env = _parse_env_file(env_path)
    base_url = _shadow_url_from_env(env)
    shadow_tokens = _collect_shadow_tokens(env)

    typer.echo(f"🔎 Validating shadow tokens against {base_url}\n")

    results: list[TokenCheckResult] = []
    processed: set[str] = set()
    selected_entities: set[str] | None = None

    if entities:
        selected_entities = {_normalize_entity_choice(choice) for choice in entities}

    for entity_key, expected_login in SERVICE_ACCOUNT_USERNAMES.items():
        if selected_entities is not None and entity_key not in selected_entities:
            continue
        env_var = f"{TOKEN_PREFIX}{entity_key.upper()}{TOKEN_SUFFIX}"
        token_value = shadow_tokens.get(env_var)
        if token_value is None:
            result = TokenCheckResult(
                env_var=env_var,
                entity_key=entity_key,
                expected_login=expected_login,
                status="missing_token",
                notes=["env var not defined"],
            )
        else:
            result = _check_token(
                token=token_value,
                env_var=env_var,
                entity_key=entity_key,
                expected_login=expected_login,
                base_url=base_url,
            )
            processed.add(env_var)
        results.append(result)

    extra_vars = set(shadow_tokens) - processed
    if selected_entities is None:
        target_extra = extra_vars
    else:
        target_extra = {
            env_var
            for env_var in extra_vars
            if _derive_entity_key(env_var) in selected_entities
        }

    for env_var in target_extra:
        entity_key = _derive_entity_key(env_var)
        expected_login = _derive_expected_login(entity_key)
        result = _check_token(
            token=shadow_tokens[env_var],
            env_var=env_var,
            entity_key=entity_key,
            expected_login=expected_login,
            base_url=base_url,
        )
        results.append(result)

    if json_output:
        typer.echo(
            json.dumps(
                {
                    "base_url": base_url,
                    "results": [asdict(result) for result in results],
                },
                indent=2,
            )
        )
        return

    failures = 0
    for result in results:
        symbol = _symbol_for_status(result.status)
        typer.echo(
            f"{symbol} {result.env_var} → expected `{result.expected_login}`"
            f" (entity: {result.entity_key})"
        )
        if result.actual_login:
            typer.echo(f"    resolved login: {result.actual_login}")
        notes = _format_notes(result.notes)
        for note in notes:
            typer.echo(f"    {note}")
        if result.status not in {"ok", "repo_warning"}:
            failures += 1

    if failures:
        typer.secho(
            f"\n❌ {failures} shadow token(s) failed validation", fg=typer.colors.RED
        )
        raise typer.Exit(1)

    typer.secho("\n✅ All shadow tokens validated (or noted with warnings)", fg=typer.colors.GREEN)
