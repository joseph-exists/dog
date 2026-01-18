"""
LLM Catalog Management Commands

Commands for browsing and managing the LLM provider/model catalog.
These endpoints are public (no auth required) for read operations.

API Endpoints:
    GET  /llm-catalog/providers              - List providers
    GET  /llm-catalog/providers/{id}         - Get provider
    GET  /llm-catalog/providers/{id}/models  - List provider's models
    GET  /llm-catalog/models                 - List all models
    GET  /llm-catalog/models/grouped         - Models grouped by provider
    GET  /llm-catalog/models/{id}            - Get model details
"""
import json
from typing import Annotated

import httpx
import typer

app = typer.Typer(help="LLM Catalog - browse and manage providers/models")

BASE_URL = "http://localhost:8000/api/v1"


# ============================================================================
# Helper Functions
# ============================================================================


def _get_session() -> httpx.Client:
    """Get HTTP client (no auth needed for catalog endpoints)."""
    return httpx.Client(timeout=30.0)


def _print_provider(provider: dict, verbose: bool = False):
    """Pretty print a provider."""
    enabled = "✅" if provider.get("is_enabled") else "❌"
    system = "🔧" if provider.get("is_system") else "👤"
    model_count = provider.get("model_count", 0)

    typer.echo(f"  {enabled} {provider.get('name', 'Unknown')}")
    typer.echo(f"     ID: {provider.get('id', 'N/A')}")
    typer.echo(f"     Type: {provider.get('provider_type', 'N/A')} {system}")
    typer.echo(f"     Models: {model_count}")

    if provider.get("description"):
        typer.echo(f"     Desc: {provider['description']}")
    if provider.get("base_url"):
        typer.echo(f"     URL: {provider['base_url']}")

    if verbose:
        typer.echo(f"     Created: {provider.get('created_at', 'N/A')}")
        typer.echo(f"     Updated: {provider.get('updated_at', 'N/A')}")
    typer.echo()


def _print_model(model: dict, verbose: bool = False):
    """Pretty print a model."""
    enabled = "✅" if model.get("is_enabled") else "❌"
    default = "⭐" if model.get("is_default") else "  "
    deprecated = " ⚠️ DEPRECATED" if model.get("is_deprecated") else ""

    typer.echo(f"  {enabled}{default} {model.get('display_name', 'Unknown')}{deprecated}")
    typer.echo(f"      ID: {model.get('id', 'N/A')}")
    typer.echo(f"      Model ID: {model.get('model_id', 'N/A')}")

    if model.get("provider_name"):
        typer.echo(f"      Provider: {model['provider_name']} ({model.get('provider_type', '')})")

    if model.get("description"):
        typer.echo(f"      Desc: {model['description']}")

    # Capabilities
    caps = []
    if model.get("has_vision"):
        caps.append("vision")
    if model.get("has_function_calling"):
        caps.append("tools")
    if model.get("has_streaming"):
        caps.append("streaming")
    if model.get("has_json_mode"):
        caps.append("json")
    if caps:
        typer.echo(f"      Capabilities: {', '.join(caps)}")

    if model.get("context_window"):
        typer.echo(f"      Context: {model['context_window']:,} tokens")

    if verbose:
        typer.echo(f"      Sort Order: {model.get('sort_order', 0)}")
        typer.echo(f"      Created: {model.get('created_at', 'N/A')}")
        if model.get("deprecated_at"):
            typer.echo(f"      Deprecated: {model['deprecated_at']}")
        if model.get("sunset_at"):
            typer.echo(f"      Sunset: {model['sunset_at']}")
    typer.echo()


# ============================================================================
# Provider Commands
# ============================================================================


@app.command("providers")
def list_providers(
    provider_type: Annotated[
        str | None,
        typer.Option("--type", "-t", help="Filter by type: openai, anthropic, google, openai_compatible"),
    ] = None,
    enabled_only: Annotated[
        bool, typer.Option("--enabled", "-e", help="Show only enabled providers")
    ] = False,
    include_deleted: Annotated[
        bool, typer.Option("--deleted", help="Include soft-deleted providers")
    ] = False,
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
):
    """
    List all LLM providers in the catalog.

    Examples:
        python main.py catalog providers
        python main.py catalog providers --type anthropic
        python main.py catalog providers --enabled --json
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    with _get_session() as session:
        params = {}
        if provider_type:
            params["provider_type"] = provider_type
        if enabled_only:
            params["is_enabled"] = True
        if include_deleted:
            params["include_deleted"] = True

        log(f"GET /llm-catalog/providers with params: {params}")
        response = session.get(f"{BASE_URL}/llm-catalog/providers", params=params)
        log(f"Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            providers = data.get("data", [])
            total = data.get("count", 0)

            if json_output:
                typer.echo(json.dumps(data, indent=2))
            else:
                typer.echo(f"\n🏢 LLM Providers ({len(providers)} of {total}):\n")

                if not providers:
                    typer.secho("  No providers found", fg=typer.colors.YELLOW)
                else:
                    for provider in providers:
                        _print_provider(provider, verbose)
        else:
            typer.secho("❌ Failed to list providers", fg=typer.colors.RED, err=True)
            typer.echo(f"Status: {response.status_code}")
            typer.echo(f"Error: {response.text}")
            raise typer.Exit(1)


@app.command("provider")
def get_provider(
    provider_id: Annotated[str, typer.Argument(help="Provider UUID")],
    with_models: Annotated[
        bool, typer.Option("--models", "-m", help="Include provider's models")
    ] = False,
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
):
    """
    Get details for a specific provider.

    Examples:
        python main.py catalog provider <uuid>
        python main.py catalog provider <uuid> --models
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    with _get_session() as session:
        log(f"GET /llm-catalog/providers/{provider_id}")
        response = session.get(f"{BASE_URL}/llm-catalog/providers/{provider_id}")

        if response.status_code == 200:
            provider = response.json()

            if json_output and not with_models:
                typer.echo(json.dumps(provider, indent=2))
            elif not with_models:
                typer.echo(f"\n🏢 Provider Details:\n")
                _print_provider(provider, verbose=True)

            # Fetch models if requested
            if with_models:
                log(f"GET /llm-catalog/providers/{provider_id}/models")
                models_response = session.get(
                    f"{BASE_URL}/llm-catalog/providers/{provider_id}/models"
                )

                if models_response.status_code == 200:
                    models_data = models_response.json()

                    if json_output:
                        combined = {
                            "provider": provider,
                            "models": models_data
                        }
                        typer.echo(json.dumps(combined, indent=2))
                    else:
                        typer.echo(f"\n🏢 Provider Details:\n")
                        _print_provider(provider, verbose=True)

                        models = models_data.get("data", [])
                        typer.echo(f"📦 Models ({len(models)}):\n")
                        for model in models:
                            _print_model(model, verbose)
        elif response.status_code == 404:
            typer.secho(f"❌ Provider not found: {provider_id}", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)
        else:
            typer.secho("❌ Failed to get provider", fg=typer.colors.RED, err=True)
            typer.echo(f"Status: {response.status_code}")
            typer.echo(f"Error: {response.text}")
            raise typer.Exit(1)


# ============================================================================
# Model Commands
# ============================================================================


@app.command("models")
def list_models(
    provider_type: Annotated[
        str | None,
        typer.Option("--type", "-t", help="Filter by provider type"),
    ] = None,
    provider_id: Annotated[
        str | None,
        typer.Option("--provider", "-p", help="Filter by provider UUID"),
    ] = None,
    enabled_only: Annotated[
        bool, typer.Option("--enabled", "-e", help="Show only enabled models")
    ] = False,
    defaults_only: Annotated[
        bool, typer.Option("--defaults", "-d", help="Show only default models")
    ] = False,
    has_vision: Annotated[
        bool | None, typer.Option("--vision", help="Filter by vision capability")
    ] = None,
    has_tools: Annotated[
        bool | None, typer.Option("--tools", help="Filter by function calling capability")
    ] = None,
    limit: Annotated[int, typer.Option(help="Maximum items to list")] = 50,
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
):
    """
    List all LLM models (flat list).

    Examples:
        python main.py catalog models
        python main.py catalog models --type anthropic
        python main.py catalog models --vision --tools
        python main.py catalog models --defaults
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    with _get_session() as session:
        params = {"limit": limit}
        if provider_type:
            params["provider_type"] = provider_type
        if provider_id:
            params["provider_id"] = provider_id
        if enabled_only:
            params["is_enabled"] = True
        if defaults_only:
            params["is_default"] = True
        if has_vision is not None:
            params["has_vision"] = has_vision
        if has_tools is not None:
            params["has_function_calling"] = has_tools

        log(f"GET /llm-catalog/models with params: {params}")
        response = session.get(f"{BASE_URL}/llm-catalog/models", params=params)
        log(f"Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            models = data.get("data", [])
            total = data.get("count", 0)

            if json_output:
                typer.echo(json.dumps(data, indent=2))
            else:
                typer.echo(f"\n🤖 LLM Models ({len(models)} of {total}):\n")

                if not models:
                    typer.secho("  No models found", fg=typer.colors.YELLOW)
                else:
                    for model in models:
                        _print_model(model, verbose)
        else:
            typer.secho("❌ Failed to list models", fg=typer.colors.RED, err=True)
            typer.echo(f"Status: {response.status_code}")
            typer.echo(f"Error: {response.text}")
            raise typer.Exit(1)


@app.command("models-grouped")
def list_models_grouped(
    provider_type: Annotated[
        str | None,
        typer.Option("--type", "-t", help="Filter by provider type"),
    ] = None,
    enabled_only: Annotated[
        bool, typer.Option("--enabled", "-e", help="Show only enabled")
    ] = False,
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
):
    """
    List models grouped by provider (useful for UI display).

    Examples:
        python main.py catalog models-grouped
        python main.py catalog models-grouped --type openai
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    with _get_session() as session:
        params = {}
        if provider_type:
            params["provider_type"] = provider_type
        if enabled_only:
            params["is_enabled"] = True

        log(f"GET /llm-catalog/models/grouped with params: {params}")
        response = session.get(f"{BASE_URL}/llm-catalog/models/grouped", params=params)
        log(f"Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            providers = data.get("providers", [])
            total_models = data.get("total_models", 0)

            if json_output:
                typer.echo(json.dumps(data, indent=2))
            else:
                typer.echo(f"\n📊 LLM Catalog ({total_models} models across {len(providers)} providers):\n")

                for provider in providers:
                    enabled = "✅" if provider.get("is_enabled") else "❌"
                    model_count = provider.get("model_count", 0)

                    typer.secho(
                        f"┌─ {enabled} {provider.get('name', 'Unknown')} ({model_count} models)",
                        fg=typer.colors.BLUE,
                        bold=True
                    )
                    typer.echo(f"│  Type: {provider.get('provider_type', 'N/A')}")

                    models = provider.get("models", [])
                    for i, model in enumerate(models):
                        is_last = i == len(models) - 1
                        prefix = "└──" if is_last else "├──"

                        default = " ⭐" if model.get("is_default") else ""
                        enabled = "✅" if model.get("is_enabled") else "❌"
                        deprecated = " ⚠️" if model.get("is_deprecated") else ""

                        typer.echo(f"│  {prefix} {enabled} {model.get('display_name', 'Unknown')}{default}{deprecated}")
                        typer.echo(f"│      model_id: {model.get('model_id', 'N/A')}")

                        if verbose:
                            caps = []
                            if model.get("has_vision"):
                                caps.append("vision")
                            if model.get("has_function_calling"):
                                caps.append("tools")
                            if caps:
                                typer.echo(f"│      caps: {', '.join(caps)}")

                    typer.echo()
        else:
            typer.secho("❌ Failed to list grouped models", fg=typer.colors.RED, err=True)
            typer.echo(f"Status: {response.status_code}")
            typer.echo(f"Error: {response.text}")
            raise typer.Exit(1)


@app.command("model")
def get_model(
    model_id: Annotated[str, typer.Argument(help="Model UUID")],
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
):
    """
    Get details for a specific model.

    Examples:
        python main.py catalog model <uuid>
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    with _get_session() as session:
        log(f"GET /llm-catalog/models/{model_id}")
        response = session.get(f"{BASE_URL}/llm-catalog/models/{model_id}")

        if response.status_code == 200:
            model = response.json()

            if json_output:
                typer.echo(json.dumps(model, indent=2))
            else:
                typer.echo(f"\n🤖 Model Details:\n")
                _print_model(model, verbose=True)

                # Show full capability breakdown
                typer.echo("  Capabilities:")
                typer.echo(f"    Vision: {_bool_display(model.get('has_vision'))}")
                typer.echo(f"    Function Calling: {_bool_display(model.get('has_function_calling'))}")
                typer.echo(f"    Streaming: {_bool_display(model.get('has_streaming'))}")
                typer.echo(f"    JSON Mode: {_bool_display(model.get('has_json_mode'))}")

                if model.get("secondary_capabilities"):
                    typer.echo(f"    Secondary: {json.dumps(model['secondary_capabilities'])}")
        elif response.status_code == 404:
            typer.secho(f"❌ Model not found: {model_id}", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)
        else:
            typer.secho("❌ Failed to get model", fg=typer.colors.RED, err=True)
            typer.echo(f"Status: {response.status_code}")
            typer.echo(f"Error: {response.text}")
            raise typer.Exit(1)


def _bool_display(value: bool | None) -> str:
    """Display boolean or unknown."""
    if value is None:
        return "❓ Unknown"
    return "✅ Yes" if value else "❌ No"


# ============================================================================
# Quick Reference Commands
# ============================================================================


@app.command("defaults")
def list_defaults(
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
):
    """
    Quick list of default (cheapest) models per provider.

    Examples:
        python main.py catalog defaults
    """
    with _get_session() as session:
        response = session.get(
            f"{BASE_URL}/llm-catalog/models",
            params={"is_default": True, "is_enabled": True}
        )

        if response.status_code == 200:
            data = response.json()
            models = data.get("data", [])

            if json_output:
                typer.echo(json.dumps(data, indent=2))
            else:
                typer.echo("\n⭐ Default Models (cheapest per provider):\n")

                for model in models:
                    provider = model.get("provider_name", "Unknown")
                    typer.echo(f"  {provider}: {model.get('display_name')} ({model.get('model_id')})")
        else:
            typer.secho("❌ Failed to fetch defaults", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)


@app.command("vision")
def list_vision_models(
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
):
    """
    Quick list of models with vision capability.

    Examples:
        python main.py catalog vision
    """
    with _get_session() as session:
        response = session.get(
            f"{BASE_URL}/llm-catalog/models",
            params={"has_vision": True, "is_enabled": True}
        )

        if response.status_code == 200:
            data = response.json()
            models = data.get("data", [])

            if json_output:
                typer.echo(json.dumps(data, indent=2))
            else:
                typer.echo("\n👁️ Vision-Capable Models:\n")

                for model in models:
                    provider = model.get("provider_name", "Unknown")
                    typer.echo(f"  {provider}: {model.get('display_name')} ({model.get('model_id')})")
        else:
            typer.secho("❌ Failed to fetch vision models", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)


# ============================================================================
# Main (for testing module directly)
# ============================================================================

if __name__ == "__main__":
    app()
