"""
LLM Provider & Model Catalog Commands

This module provides CLI commands for managing LLM providers and browsing models.

=============================================================================
ARCHITECTURE OVERVIEW
=============================================================================

The LLM system has THREE main concepts:

1. LLMProviderType (the "catalog" of provider types)
   - System-defined entries like "openai", "anthropic", "google"
   - Each has a UUID that links models to their compatible providers
   - Users typically don't create these; they're seeded in the database

2. UserAccessProvider (your configured provider instances)
   - YOUR API key + settings for a specific provider type
   - Links to an LLMProviderType via `alpha_provider_type_id`
   - Example: "My OpenAI Account" with your API key

3. LLMModel (available models in the catalog)
   - Models like "gpt-4o", "claude-3-opus", etc.
   - Each model is linked to a provider type
   - Has capability flags (vision, tools, streaming, json_mode)

=============================================================================
API ENDPOINTS
=============================================================================

/llm-providers/ (requires auth - manages YOUR provider configs):
    GET  /                           - List your configured providers
    GET  /provider-type-list         - List available provider types
    GET  /by_name/{name}             - Get provider type by name
    POST /                           - Create new provider config (with API key)
    GET  /{id}                       - Get your provider config
    PATCH /{id}                      - Update provider config
    DELETE /{id}                     - Delete provider config

/llm-catalog/ (requires auth - browses models):
    GET  /providers/types/{id}       - Get provider type details
    GET  /providers/{id}/models      - List models for your provider
    GET  /models                     - List all available models
    GET  /models/{id}                - Get single model details
    POST /models                     - Create model (superuser)
    PATCH /models/{id}               - Update model (superuser)
    DELETE /models/{id}              - Delete model (superuser)
    GET  /models/uap?id=...          - List models for a specific UAP's type

=============================================================================
CSV IMPORT/EXPORT FORMAT
=============================================================================

The bulk import/export commands use this CSV format:

    provider_name,model_id,display_name,description,context_window,
    is_default,is_enabled,sort_order,has_vision,has_function_calling,
    has_streaming,has_json_mode

Provider names are mapped to UUIDs automatically:
    OpenAI           -> 673f1787-8474-4e1c-986c-8e19f14c989c
    Anthropic        -> 008dc763-4309-43cd-ba5f-1eb1323a0964
    Google           -> ae07eb0b-929e-4844-8b75-4fe6abca09df
    OpenAI Compatible -> e09ade10-8563-4748-8deb-1a6c87c97134
    Custom           -> 186672e2-f50a-4457-a7dd-a50084077ff7

=============================================================================
"""
import csv
import json
import sys
from io import StringIO
from pathlib import Path
from typing import Annotated

import typer

from auth_helper import get_authenticated_session


# =============================================================================
# PROVIDER TYPE MAPPINGS
# =============================================================================
# Maps friendly provider names to their UUIDs for CSV import/export.
# These must match the database-seeded provider types.
# =============================================================================

PROVIDER_NAME_TO_UUID = {
    "OpenAI": "673f1787-8474-4e1c-986c-8e19f14c989c",
    "Anthropic": "008dc763-4309-43cd-ba5f-1eb1323a0964",
    "Google": "ae07eb0b-929e-4844-8b75-4fe6abca09df",
    "OpenAI Compatible": "e09ade10-8563-4748-8deb-1a6c87c97134",
    "Custom": "186672e2-f50a-4457-a7dd-a50084077ff7",
    "Empty": "37520103-0644-4d29-99b6-583eb0996370",
    # Lowercase aliases for convenience
    "openai": "673f1787-8474-4e1c-986c-8e19f14c989c",
    "anthropic": "008dc763-4309-43cd-ba5f-1eb1323a0964",
    "google": "ae07eb0b-929e-4844-8b75-4fe6abca09df",
    "openai_compatible": "e09ade10-8563-4748-8deb-1a6c87c97134",
    "custom": "186672e2-f50a-4457-a7dd-a50084077ff7",
}

# Reverse mapping for export
PROVIDER_UUID_TO_NAME = {
    "673f1787-8474-4e1c-986c-8e19f14c989c": "OpenAI",
    "008dc763-4309-43cd-ba5f-1eb1323a0964": "Anthropic",
    "ae07eb0b-929e-4844-8b75-4fe6abca09df": "Google",
    "e09ade10-8563-4748-8deb-1a6c87c97134": "OpenAI Compatible",
    "186672e2-f50a-4457-a7dd-a50084077ff7": "Custom",
    "37520103-0644-4d29-99b6-583eb0996370": "Empty",
}

# CSV column headers for import/export
CSV_HEADERS = [
    "provider_name",
    "model_id",
    "display_name",
    "description",
    "context_window",
    "is_default",
    "is_enabled",
    "sort_order",
    "has_vision",
    "has_function_calling",
    "has_streaming",
    "has_json_mode",
]

# Create the typer app for this command group
app = typer.Typer(
    help="LLM Provider & Model Catalog - manage your providers and browse models"
)

# API base URL (adjust for your environment)
BASE_URL = "http://localhost:8000/api/v1"


# =============================================================================
# PROVIDER TYPE COMMANDS
# =============================================================================
# Provider types are the "catalog" of available providers (openai, anthropic, etc.)
# These are typically system-defined and you query them to see what's available.
# =============================================================================


@app.command("types")
def list_provider_types(
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON for scripting")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show debug output")
    ] = False,
):
    """
    List all available LLM provider types.

    Provider types are the "catalog" entries like openai, anthropic, google.
    Use this to find the `alpha_provider_type_id` when creating a new provider config.

    Examples:
        python main.py catalog types
        python main.py catalog types --json
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    log("GET /llm-providers/provider-type-list")
    response = session.get(f"{BASE_URL}/llm-providers/provider-type-list")
    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        types = data.get("data", [])
        count = data.get("count", 0)

        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.echo(f"\n🏷️  Provider Types ({count}):\n")

            if not types:
                typer.secho("  No provider types found", fg=typer.colors.YELLOW)
            else:
                for pt in types:
                    _print_provider_type(pt, verbose)
    else:
        typer.secho("❌ Failed to list provider types", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command("type")
def get_provider_type(
    provider_type_id: Annotated[str, typer.Argument(help="Provider type UUID")],
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show debug output")
    ] = False,
):
    """
    Get details for a specific provider type by UUID.

    Examples:
        python main.py catalog type <uuid>
        python main.py catalog type <uuid> --json
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    log(f"GET /llm-catalog/providers/types/{provider_type_id}")
    response = session.get(f"{BASE_URL}/llm-catalog/providers/types/{provider_type_id}")
    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        pt = response.json()

        if json_output:
            typer.echo(json.dumps(pt, indent=2))
        else:
            typer.echo(f"\n🏷️  Provider Type Details:\n")
            _print_provider_type(pt, verbose=True)
    elif response.status_code == 404:
        typer.secho(f"❌ Provider type not found: {provider_type_id}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    else:
        typer.secho("❌ Failed to get provider type", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command("type-by-name")
def get_provider_type_by_name(
    name: Annotated[str, typer.Argument(help="Provider type name (e.g., 'openai')")],
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show debug output")
    ] = False,
):
    """
    Get provider type by name (e.g., "openai", "anthropic").

    This is a convenient way to look up a provider type when you know
    the name but not the UUID.

    Examples:
        python main.py catalog type-by-name openai
        python main.py catalog type-by-name anthropic --json
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    log(f"GET /llm-providers/by_name/{name}")
    response = session.get(f"{BASE_URL}/llm-providers/by_name/{name}")
    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        pt = response.json()

        if json_output:
            typer.echo(json.dumps(pt, indent=2))
        else:
            typer.echo(f"\n🏷️  Provider Type: {name}\n")
            _print_provider_type(pt, verbose=True)
    elif response.status_code == 404:
        typer.secho(f"❌ Provider type not found: {name}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    else:
        typer.secho("❌ Failed to get provider type", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# =============================================================================
# USER ACCESS PROVIDER COMMANDS
# =============================================================================
# These are YOUR configured provider instances - your API keys and settings.
# Each one links to a provider type (openai, anthropic, etc.)
# =============================================================================


@app.command("providers")
def list_user_providers(
    limit: Annotated[int, typer.Option(help="Maximum items to list")] = 50,
    skip: Annotated[int, typer.Option(help="Pagination offset")] = 0,
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show debug output")
    ] = False,
):
    """
    List your configured LLM providers.

    These are your personal provider configurations with API keys.
    Each one links to a provider type (like openai or anthropic).

    Examples:
        python main.py catalog providers
        python main.py catalog providers --json
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    params = {"skip": skip, "limit": limit}

    log(f"GET /llm-providers/ with params: {params}")
    response = session.get(f"{BASE_URL}/llm-providers/", params=params)
    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        providers = data.get("data", [])
        count = data.get("count", 0)

        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.echo(f"\n🔑 Your LLM Providers ({len(providers)} of {count}):\n")

            if not providers:
                typer.secho("  No providers configured", fg=typer.colors.YELLOW)
                typer.echo("\n  💡 Use 'catalog create-provider' to add one!")
            else:
                for provider in providers:
                    _print_user_provider(provider, verbose)
    else:
        typer.secho("❌ Failed to list providers", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command("provider")
def get_user_provider(
    provider_id: Annotated[str, typer.Argument(help="Your provider config UUID")],
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show debug output")
    ] = False,
):
    """
    Get details of your specific provider configuration.

    Examples:
        python main.py catalog provider <uuid>
        python main.py catalog provider <uuid> --json
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    log(f"GET /llm-providers/{provider_id}")
    response = session.get(f"{BASE_URL}/llm-providers/{provider_id}")
    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        provider = response.json()

        if json_output:
            typer.echo(json.dumps(provider, indent=2))
        else:
            typer.echo(f"\n🔑 Provider Configuration:\n")
            _print_user_provider(provider, verbose=True)
    elif response.status_code == 404:
        typer.secho(f"❌ Provider not found: {provider_id}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    else:
        typer.secho("❌ Failed to get provider", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command("create-provider")
def create_user_provider(
    name: Annotated[str, typer.Argument(help="Friendly name for this provider config")],
    provider_type: Annotated[
        str,
        typer.Option(
            "--type", "-t",
            help="Provider type name (e.g., 'openai') or UUID"
        ),
    ],
    api_key: Annotated[
        str,
        typer.Option(
            "--api-key", "-k",
            help="API key (will be encrypted at rest)",
            prompt="API Key",  # Prompts securely if not provided
            hide_input=True,   # Hides input when prompting
        ),
    ],
    base_url: Annotated[
        str | None,
        typer.Option("--base-url", "-u", help="Custom base URL (for self-hosted)")
    ] = None,
    description: Annotated[
        str | None,
        typer.Option("--desc", "-d", help="Description")
    ] = None,
    is_default: Annotated[
        bool,
        typer.Option("--default/--no-default", help="Set as your default provider")
    ] = False,
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show debug output")
    ] = False,
):
    """
    Create a new LLM provider configuration with your API key.

    The API key is encrypted at rest and never returned in responses.

    You need to specify the provider type - either by name (e.g., "openai")
    or by UUID. Use 'catalog types' to see available types.

    Examples:
        # By provider type name (will look up UUID)
        python main.py catalog create-provider "My OpenAI" --type openai -k sk-xxx

        # By provider type UUID
        python main.py catalog create-provider "My Claude" \\
            --type 008dc763-4309-43cd-ba5f-1eb1323a0964 -k sk-xxx

        # With custom endpoint (for Azure, self-hosted, etc.)
        python main.py catalog create-provider "Azure OpenAI" \\
            --type openai \\
            --base-url https://my-resource.openai.azure.com \\
            -k xxx
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    # Resolve provider type name to UUID if needed
    # (If it's already a UUID, the lookup will fail and we use it directly)
    alpha_provider_type_id = provider_type
    if not _is_uuid(provider_type):
        log(f"Looking up provider type by name: {provider_type}")
        response = session.get(f"{BASE_URL}/llm-providers/by_name/{provider_type}")
        if response.status_code == 200:
            pt = response.json()
            alpha_provider_type_id = pt.get("id")
            log(f"Resolved '{provider_type}' to UUID: {alpha_provider_type_id}")
        else:
            typer.secho(f"❌ Provider type not found: {provider_type}", fg=typer.colors.RED, err=True)
            typer.echo("Use 'catalog types' to see available provider types")
            raise typer.Exit(1)

    # Build the payload
    payload = {
        "name": name,
        "alpha_provider_type_id": alpha_provider_type_id,
        "api_key": api_key,
        "is_default": is_default,
        "is_enabled": True,
    }

    # Add optional fields
    if base_url:
        payload["base_url"] = base_url
    if description:
        payload["description"] = description

    # Don't log the full payload (contains API key!)
    log(f"POST /llm-providers/ (payload contains API key, not logging)")
    log(f"Provider name: {name}, type: {alpha_provider_type_id}")

    response = session.post(f"{BASE_URL}/llm-providers/", json=payload)
    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        provider = response.json()

        if json_output:
            typer.echo(json.dumps(provider, indent=2))
        else:
            typer.secho("✅ Provider created successfully!", fg=typer.colors.GREEN)
            typer.echo()
            _print_user_provider(provider, verbose=True)
    elif response.status_code == 400:
        typer.secho("❌ Invalid request", fg=typer.colors.RED, err=True)
        typer.echo(f"Error: {response.json().get('detail', response.text)}")
        raise typer.Exit(1)
    elif response.status_code == 422:
        typer.secho("❌ Validation error", fg=typer.colors.RED, err=True)
        detail = response.json().get("detail", [])
        for err in detail:
            if isinstance(err, dict):
                typer.echo(f"  • {err.get('msg', err)}")
            else:
                typer.echo(f"  • {err}")
        raise typer.Exit(1)
    else:
        typer.secho("❌ Failed to create provider", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command("update-provider")
def update_user_provider(
    provider_id: Annotated[str, typer.Argument(help="Provider config UUID to update")],
    name: Annotated[
        str | None,
        typer.Option("--name", "-n", help="New name")
    ] = None,
    api_key: Annotated[
        str | None,
        typer.Option("--api-key", "-k", help="New API key (will be encrypted)")
    ] = None,
    base_url: Annotated[
        str | None,
        typer.Option("--base-url", "-u", help="New base URL")
    ] = None,
    description: Annotated[
        str | None,
        typer.Option("--desc", "-d", help="New description")
    ] = None,
    enabled: Annotated[
        bool | None,
        typer.Option("--enabled/--disabled", help="Enable or disable")
    ] = None,
    is_default: Annotated[
        bool | None,
        typer.Option("--default/--no-default", help="Set as default")
    ] = None,
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show debug output")
    ] = False,
):
    """
    Update your LLM provider configuration.

    Only provide the fields you want to change.

    Examples:
        python main.py catalog update-provider <uuid> --name "Renamed Provider"
        python main.py catalog update-provider <uuid> --api-key NEW_KEY
        python main.py catalog update-provider <uuid> --disabled
        python main.py catalog update-provider <uuid> --default
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    # Build payload with only provided fields
    payload = {}
    if name is not None:
        payload["name"] = name
    if api_key is not None:
        payload["api_key"] = api_key
    if base_url is not None:
        payload["base_url"] = base_url
    if description is not None:
        payload["description"] = description
    if enabled is not None:
        payload["is_enabled"] = enabled
    if is_default is not None:
        payload["is_default"] = is_default

    if not payload:
        typer.secho("⚠️  No updates provided", fg=typer.colors.YELLOW)
        raise typer.Exit(0)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    # Don't log payload if it contains API key
    has_api_key = "api_key" in payload
    log(f"PATCH /llm-providers/{provider_id}")
    if has_api_key:
        log("Payload contains API key (not logging full payload)")
    else:
        log(f"Payload: {json.dumps(payload, indent=2)}")

    response = session.patch(f"{BASE_URL}/llm-providers/{provider_id}", json=payload)
    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        provider = response.json()

        if json_output:
            typer.echo(json.dumps(provider, indent=2))
        else:
            typer.secho("✅ Provider updated successfully!", fg=typer.colors.GREEN)
            typer.echo()
            _print_user_provider(provider, verbose=True)
    elif response.status_code == 404:
        typer.secho(f"❌ Provider not found: {provider_id}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    else:
        typer.secho("❌ Failed to update provider", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command("delete-provider")
def delete_user_provider(
    provider_id: Annotated[str, typer.Argument(help="Provider config UUID to delete")],
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Skip confirmation prompt")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show debug output")
    ] = False,
):
    """
    Delete your LLM provider configuration.

    ⚠️  This will also delete the stored API key!

    Examples:
        python main.py catalog delete-provider <uuid>
        python main.py catalog delete-provider <uuid> --force
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    if not force:
        typer.secho(f"⚠️  This will delete provider {provider_id}", fg=typer.colors.YELLOW)
        typer.echo("   This will also delete the stored API key!")
        if not typer.confirm("Are you sure?"):
            typer.echo("Cancelled.")
            raise typer.Exit(0)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    log(f"DELETE /llm-providers/{provider_id}")
    response = session.delete(f"{BASE_URL}/llm-providers/{provider_id}")
    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        typer.secho("✅ Provider deleted successfully", fg=typer.colors.GREEN)
    elif response.status_code == 404:
        typer.secho(f"❌ Provider not found: {provider_id}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    else:
        typer.secho("❌ Failed to delete provider", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# =============================================================================
# MODEL COMMANDS
# =============================================================================
# Models are the actual LLM models (gpt-4o, claude-3-opus, etc.)
# Each model is linked to a provider type.
# =============================================================================


@app.command("models")
def list_models(
    limit: Annotated[int, typer.Option(help="Maximum items to list")] = 100,
    skip: Annotated[int, typer.Option(help="Pagination offset")] = 0,
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show debug output")
    ] = False,
):
    """
    List all available LLM models in the catalog.

    Examples:
        python main.py catalog models
        python main.py catalog models --limit 20
        python main.py catalog models --json
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    params = {"skip": skip, "limit": limit}

    log(f"GET /llm-catalog/models with params: {params}")
    response = session.get(f"{BASE_URL}/llm-catalog/models", params=params)
    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        models = data.get("data", [])
        count = data.get("count", 0)

        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.echo(f"\n🤖 LLM Models ({len(models)} of {count}):\n")

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


@app.command("provider-models")
def list_provider_models(
    provider_id: Annotated[
        str,
        typer.Argument(help="Your provider config UUID")
    ],
    limit: Annotated[int, typer.Option(help="Maximum items to list")] = 100,
    skip: Annotated[int, typer.Option(help="Pagination offset")] = 0,
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show debug output")
    ] = False,
):
    """
    List models available for one of your configured providers.

    This returns models compatible with the provider type of your config.

    Examples:
        python main.py catalog provider-models <your-provider-uuid>
        python main.py catalog provider-models <uuid> --json
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    params = {"skip": skip, "limit": limit}

    log(f"GET /llm-catalog/providers/{provider_id}/models with params: {params}")
    response = session.get(
        f"{BASE_URL}/llm-catalog/providers/{provider_id}/models",
        params=params
    )
    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        models = data.get("data", [])
        count = data.get("count", 0)

        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.echo(f"\n🤖 Models for Provider ({len(models)} of {count}):\n")

            if not models:
                typer.secho("  No models found for this provider", fg=typer.colors.YELLOW)
            else:
                for model in models:
                    _print_model(model, verbose)
    elif response.status_code == 404:
        typer.secho(f"❌ Provider not found: {provider_id}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    else:
        typer.secho("❌ Failed to list provider models", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command("model")
def get_model(
    model_uuid: Annotated[str, typer.Argument(help="Model UUID from catalog")],
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show debug output")
    ] = False,
):
    """
    Get details of a specific model by UUID.

    Examples:
        python main.py catalog model <uuid>
        python main.py catalog model <uuid> --json
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    log(f"GET /llm-catalog/models/{model_uuid}")
    response = session.get(f"{BASE_URL}/llm-catalog/models/{model_uuid}")
    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        model = response.json()

        if json_output:
            typer.echo(json.dumps(model, indent=2))
        else:
            typer.echo(f"\n🤖 Model Details:\n")
            _print_model_detail(model)
    elif response.status_code == 404:
        typer.secho(f"❌ Model not found: {model_uuid}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    else:
        typer.secho("❌ Failed to get model", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# =============================================================================
# MODEL ADMIN COMMANDS (Superuser Only)
# =============================================================================
# These commands modify the model catalog and require superuser privileges.
# Regular users will get 403 Forbidden errors.
# =============================================================================


@app.command("create-model")
def create_model(
    model_id: Annotated[
        str,
        typer.Argument(help="Model identifier (e.g., 'gpt-4o-mini', 'claude-3-haiku')")
    ],
    display_name: Annotated[
        str,
        typer.Argument(help="Human-friendly display name (e.g., 'GPT 4o Mini')")
    ],
    provider_type: Annotated[
        str,
        typer.Option(
            "--provider", "-p",
            help="Provider type name (e.g., 'openai') or UUID"
        ),
    ],
    description: Annotated[
        str | None,
        typer.Option("--desc", "-d", help="Model description")
    ] = None,
    context_window: Annotated[
        int | None,
        typer.Option("--context", "-c", help="Context window size in tokens")
    ] = None,
    has_vision: Annotated[
        bool | None,
        typer.Option("--vision/--no-vision", help="Supports image input")
    ] = None,
    has_tools: Annotated[
        bool | None,
        typer.Option("--tools/--no-tools", help="Supports function calling")
    ] = None,
    has_streaming: Annotated[
        bool | None,
        typer.Option("--streaming/--no-streaming", help="Supports streaming")
    ] = None,
    has_json_mode: Annotated[
        bool | None,
        typer.Option("--json-mode/--no-json-mode", help="Supports JSON output mode")
    ] = None,
    is_default: Annotated[
        bool,
        typer.Option("--default/--no-default", help="Mark as default model for provider")
    ] = False,
    is_enabled: Annotated[
        bool,
        typer.Option("--enabled/--disabled", help="Enable or disable the model")
    ] = True,
    sort_order: Annotated[
        int,
        typer.Option("--sort", "-s", help="Sort order within provider (lower = first)")
    ] = 0,
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show debug output")
    ] = False,
):
    """
    Create a new LLM model in the catalog.

    ⚠️  SUPERUSER ONLY - requires admin privileges.

    The model_id must be unique per provider type. Use the actual model
    identifier that the API expects (e.g., 'gpt-4o', not 'openai:gpt-4o').

    Examples:
        # Create a basic model
        python main.py catalog create-model gpt-4o-mini "GPT 4o Mini" --provider openai

        # Create with capabilities
        python main.py catalog create-model claude-3-haiku "Claude 3 Haiku" \\
            --provider anthropic \\
            --context 200000 \\
            --vision \\
            --tools \\
            --streaming

        # Create as default model for provider
        python main.py catalog create-model gpt-4o-mini "GPT 4o Mini" \\
            --provider openai \\
            --default \\
            --desc "Fast and affordable"
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    # Resolve provider type name to UUID if needed
    primary_provider_type_id = provider_type
    if not _is_uuid(provider_type):
        log(f"Looking up provider type by name: {provider_type}")
        response = session.get(f"{BASE_URL}/llm-providers/by_name/{provider_type}")
        if response.status_code == 200:
            pt = response.json()
            primary_provider_type_id = pt.get("id")
            log(f"Resolved '{provider_type}' to UUID: {primary_provider_type_id}")
        else:
            typer.secho(f"❌ Provider type not found: {provider_type}", fg=typer.colors.RED, err=True)
            typer.echo("Use 'catalog types' to see available provider types")
            raise typer.Exit(1)

    # Build the payload
    payload = {
        "model_id": model_id,
        "display_name": display_name,
        "primary_provider_type_id": primary_provider_type_id,
        "is_default": is_default,
        "is_enabled": is_enabled,
        "sort_order": sort_order,
    }

    # Add optional fields (only if explicitly set)
    if description is not None:
        payload["description"] = description
    if context_window is not None:
        payload["context_window"] = context_window
    if has_vision is not None:
        payload["has_vision"] = has_vision
    if has_tools is not None:
        payload["has_function_calling"] = has_tools
    if has_streaming is not None:
        payload["has_streaming"] = has_streaming
    if has_json_mode is not None:
        payload["has_json_mode"] = has_json_mode

    log(f"POST /llm-catalog/models with payload:")
    log(json.dumps(payload, indent=2))

    response = session.post(f"{BASE_URL}/llm-catalog/models", json=payload)
    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        model = response.json()

        if json_output:
            typer.echo(json.dumps(model, indent=2))
        else:
            typer.secho("✅ Model created successfully!", fg=typer.colors.GREEN)
            typer.echo()
            _print_model_detail(model)
    elif response.status_code == 400:
        typer.secho("❌ Invalid request", fg=typer.colors.RED, err=True)
        typer.echo(f"Error: {response.json().get('detail', response.text)}")
        raise typer.Exit(1)
    elif response.status_code == 403:
        typer.secho("❌ Permission denied - superuser required", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    elif response.status_code == 422:
        typer.secho("❌ Validation error", fg=typer.colors.RED, err=True)
        detail = response.json().get("detail", [])
        for err in detail:
            if isinstance(err, dict):
                typer.echo(f"  • {err.get('loc', '')}: {err.get('msg', err)}")
            else:
                typer.echo(f"  • {err}")
        raise typer.Exit(1)
    else:
        typer.secho("❌ Failed to create model", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command("update-model")
def update_model(
    model_uuid: Annotated[str, typer.Argument(help="Model UUID to update")],
    model_id: Annotated[
        str | None,
        typer.Option("--model-id", help="New model identifier")
    ] = None,
    display_name: Annotated[
        str | None,
        typer.Option("--name", "-n", help="New display name")
    ] = None,
    description: Annotated[
        str | None,
        typer.Option("--desc", "-d", help="New description")
    ] = None,
    context_window: Annotated[
        int | None,
        typer.Option("--context", "-c", help="New context window size")
    ] = None,
    has_vision: Annotated[
        bool | None,
        typer.Option("--vision/--no-vision", help="Update vision capability")
    ] = None,
    has_tools: Annotated[
        bool | None,
        typer.Option("--tools/--no-tools", help="Update function calling capability")
    ] = None,
    has_streaming: Annotated[
        bool | None,
        typer.Option("--streaming/--no-streaming", help="Update streaming capability")
    ] = None,
    has_json_mode: Annotated[
        bool | None,
        typer.Option("--json-mode/--no-json-mode", help="Update JSON mode capability")
    ] = None,
    is_default: Annotated[
        bool | None,
        typer.Option("--default/--no-default", help="Set as default")
    ] = None,
    is_enabled: Annotated[
        bool | None,
        typer.Option("--enabled/--disabled", help="Enable or disable")
    ] = None,
    is_deprecated: Annotated[
        bool | None,
        typer.Option("--deprecated/--not-deprecated", help="Mark as deprecated")
    ] = None,
    sort_order: Annotated[
        int | None,
        typer.Option("--sort", "-s", help="New sort order")
    ] = None,
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show debug output")
    ] = False,
):
    """
    Update an LLM model in the catalog.

    ⚠️  SUPERUSER ONLY - requires admin privileges.

    Only provide the fields you want to change.

    Examples:
        # Update display name
        python main.py catalog update-model <uuid> --name "GPT 4o (Updated)"

        # Add capabilities
        python main.py catalog update-model <uuid> --vision --tools

        # Deprecate a model
        python main.py catalog update-model <uuid> --deprecated

        # Disable a model
        python main.py catalog update-model <uuid> --disabled

        # Update multiple fields
        python main.py catalog update-model <uuid> \\
            --desc "New description" \\
            --context 128000 \\
            --sort 5
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    # Build payload with only provided fields
    payload = {}
    if model_id is not None:
        payload["model_id"] = model_id
    if display_name is not None:
        payload["display_name"] = display_name
    if description is not None:
        payload["description"] = description
    if context_window is not None:
        payload["context_window"] = context_window
    if has_vision is not None:
        payload["has_vision"] = has_vision
    if has_tools is not None:
        payload["has_function_calling"] = has_tools
    if has_streaming is not None:
        payload["has_streaming"] = has_streaming
    if has_json_mode is not None:
        payload["has_json_mode"] = has_json_mode
    if is_default is not None:
        payload["is_default"] = is_default
    if is_enabled is not None:
        payload["is_enabled"] = is_enabled
    if is_deprecated is not None:
        payload["is_deprecated"] = is_deprecated
    if sort_order is not None:
        payload["sort_order"] = sort_order

    if not payload:
        typer.secho("⚠️  No updates provided", fg=typer.colors.YELLOW)
        raise typer.Exit(0)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    log(f"PATCH /llm-catalog/models/{model_uuid}")
    log(f"Payload: {json.dumps(payload, indent=2)}")

    response = session.patch(f"{BASE_URL}/llm-catalog/models/{model_uuid}", json=payload)
    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        model = response.json()

        if json_output:
            typer.echo(json.dumps(model, indent=2))
        else:
            typer.secho("✅ Model updated successfully!", fg=typer.colors.GREEN)
            typer.echo()
            _print_model_detail(model)
    elif response.status_code == 400:
        typer.secho("❌ Invalid request", fg=typer.colors.RED, err=True)
        typer.echo(f"Error: {response.json().get('detail', response.text)}")
        raise typer.Exit(1)
    elif response.status_code == 403:
        typer.secho("❌ Permission denied - superuser required", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    elif response.status_code == 404:
        typer.secho(f"❌ Model not found: {model_uuid}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    else:
        typer.secho("❌ Failed to update model", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command("delete-model")
def delete_model(
    model_uuid: Annotated[str, typer.Argument(help="Model UUID to delete")],
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Skip confirmation prompt")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show debug output")
    ] = False,
):
    """
    Delete an LLM model from the catalog.

    ⚠️  SUPERUSER ONLY - requires admin privileges.
    ⚠️  This is permanent and may affect agents using this model!

    Examples:
        python main.py catalog delete-model <uuid>
        python main.py catalog delete-model <uuid> --force
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    # Fetch model details first for confirmation
    if not force:
        log(f"GET /llm-catalog/models/{model_uuid}")
        response = session.get(f"{BASE_URL}/llm-catalog/models/{model_uuid}")
        if response.status_code == 200:
            model = response.json()
            typer.secho(f"⚠️  This will delete model:", fg=typer.colors.YELLOW)
            typer.echo(f"   Name: {model.get('display_name', 'Unknown')}")
            typer.echo(f"   ID:   {model.get('model_id', 'Unknown')}")
            typer.echo(f"   UUID: {model_uuid}")
            typer.secho("\n   This may affect agents using this model!", fg=typer.colors.RED)
            if not typer.confirm("\nAre you sure?"):
                typer.echo("Cancelled.")
                raise typer.Exit(0)
        elif response.status_code == 404:
            typer.secho(f"❌ Model not found: {model_uuid}", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)

    log(f"DELETE /llm-catalog/models/{model_uuid}")
    response = session.delete(f"{BASE_URL}/llm-catalog/models/{model_uuid}")
    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        typer.secho("✅ Model deleted successfully", fg=typer.colors.GREEN)
    elif response.status_code == 403:
        typer.secho("❌ Permission denied - superuser required", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    elif response.status_code == 404:
        typer.secho(f"❌ Model not found: {model_uuid}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    else:
        typer.secho("❌ Failed to delete model", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# =============================================================================
# CONVENIENCE COMMANDS
# =============================================================================
# Shortcuts for common operations.
# =============================================================================


@app.command("enable-model")
def enable_model(
    model_uuid: Annotated[str, typer.Argument(help="Model UUID to enable")],
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show debug output")
    ] = False,
):
    """
    Enable a model (shortcut for update-model --enabled).

    ⚠️  SUPERUSER ONLY

    Example:
        python main.py catalog enable-model <uuid>
    """
    update_model(model_uuid, is_enabled=True, verbose=verbose, json_output=False)


@app.command("disable-model")
def disable_model(
    model_uuid: Annotated[str, typer.Argument(help="Model UUID to disable")],
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show debug output")
    ] = False,
):
    """
    Disable a model (shortcut for update-model --disabled).

    ⚠️  SUPERUSER ONLY

    Example:
        python main.py catalog disable-model <uuid>
    """
    update_model(model_uuid, is_enabled=False, verbose=verbose, json_output=False)


@app.command("deprecate-model")
def deprecate_model(
    model_uuid: Annotated[str, typer.Argument(help="Model UUID to deprecate")],
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show debug output")
    ] = False,
):
    """
    Mark a model as deprecated (shortcut for update-model --deprecated).

    Deprecated models still work but show a warning.

    ⚠️  SUPERUSER ONLY

    Example:
        python main.py catalog deprecate-model <uuid>
    """
    update_model(model_uuid, is_deprecated=True, verbose=verbose, json_output=False)


# =============================================================================
# BULK IMPORT/EXPORT COMMANDS
# =============================================================================
# Commands for importing models from CSV and exporting to CSV.
# Useful for managing model catalogs across environments.
# =============================================================================


@app.command("export-models")
def export_models(
    output_file: Annotated[
        str | None,
        typer.Option("--output", "-o", help="Output CSV file path (default: stdout)")
    ] = None,
    provider: Annotated[
        str | None,
        typer.Option("--provider", "-p", help="Filter by provider name or UUID")
    ] = None,
    enabled_only: Annotated[
        bool,
        typer.Option("--enabled", "-e", help="Only export enabled models")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show debug output")
    ] = False,
):
    """
    Export models from the catalog to CSV format.

    The CSV can be edited and re-imported with import-models.

    Examples:
        # Export all models to stdout
        python main.py catalog export-models

        # Export to file
        python main.py catalog export-models -o models.csv

        # Export only OpenAI models
        python main.py catalog export-models --provider openai -o openai-models.csv

        # Export only enabled models
        python main.py catalog export-models --enabled -o active-models.csv
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN, err=True)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    # Fetch all models (we'll filter client-side for simplicity)
    log("GET /llm-catalog/models?limit=1000")
    response = session.get(f"{BASE_URL}/llm-catalog/models", params={"limit": 1000})

    if response.status_code != 200:
        typer.secho("❌ Failed to fetch models", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        raise typer.Exit(1)

    data = response.json()
    models = data.get("data", [])

    # Resolve provider filter to UUID if provided
    provider_uuid_filter = None
    if provider:
        if _is_uuid(provider):
            provider_uuid_filter = provider
        else:
            provider_uuid_filter = PROVIDER_NAME_TO_UUID.get(provider)
            if not provider_uuid_filter:
                # Try API lookup
                resp = session.get(f"{BASE_URL}/llm-providers/by_name/{provider}")
                if resp.status_code == 200:
                    provider_uuid_filter = resp.json().get("id")
                else:
                    typer.secho(f"❌ Unknown provider: {provider}", fg=typer.colors.RED, err=True)
                    raise typer.Exit(1)

    # Filter models
    filtered_models = []
    for model in models:
        # Provider filter
        if provider_uuid_filter:
            if model.get("primary_provider_type_id") != provider_uuid_filter:
                continue
        # Enabled filter
        if enabled_only and not model.get("is_enabled", True):
            continue
        filtered_models.append(model)

    log(f"Exporting {len(filtered_models)} models (filtered from {len(models)})")

    # Build CSV
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_HEADERS)
    writer.writeheader()

    for model in filtered_models:
        # Map UUID to provider name for readability
        provider_uuid = model.get("primary_provider_type_id", "")
        provider_name = PROVIDER_UUID_TO_NAME.get(provider_uuid, provider_uuid)

        row = {
            "provider_name": provider_name,
            "model_id": model.get("model_id", ""),
            "display_name": model.get("display_name", ""),
            "description": model.get("description", "") or "",
            "context_window": model.get("context_window", "") or "",
            "is_default": str(model.get("is_default", False)).lower(),
            "is_enabled": str(model.get("is_enabled", True)).lower(),
            "sort_order": model.get("sort_order", 0),
            "has_vision": _bool_to_csv(model.get("has_vision")),
            "has_function_calling": _bool_to_csv(model.get("has_function_calling")),
            "has_streaming": _bool_to_csv(model.get("has_streaming")),
            "has_json_mode": _bool_to_csv(model.get("has_json_mode")),
        }
        writer.writerow(row)

    csv_content = output.getvalue()

    # Output to file or stdout
    if output_file:
        Path(output_file).write_text(csv_content)
        typer.secho(f"✅ Exported {len(filtered_models)} models to {output_file}", fg=typer.colors.GREEN)
    else:
        typer.echo(csv_content)


@app.command("import-models")
def import_models(
    csv_file: Annotated[
        str,
        typer.Argument(help="Path to CSV file to import")
    ],
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", "-n", help="Preview changes without applying")
    ] = False,
    update_existing: Annotated[
        bool,
        typer.Option("--update", "-u", help="Update existing models instead of skipping")
    ] = False,
    skip_errors: Annotated[
        bool,
        typer.Option("--skip-errors", help="Continue on errors instead of aborting")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show debug output")
    ] = False,
):
    """
    Import models from a CSV file into the catalog.

    ⚠️  SUPERUSER ONLY - requires admin privileges.

    CSV Format (see export-models for template):
        provider_name,model_id,display_name,description,context_window,
        is_default,is_enabled,sort_order,has_vision,has_function_calling,
        has_streaming,has_json_mode

    Provider names: OpenAI, Anthropic, Google, OpenAI Compatible, Custom

    Boolean values: true/false, yes/no, 1/0, or empty (unknown)

    Examples:
        # Preview what would be imported
        python main.py catalog import-models models.csv --dry-run

        # Import, skipping duplicates
        python main.py catalog import-models models.csv

        # Import, updating existing models
        python main.py catalog import-models models.csv --update

        # Import, continuing on errors
        python main.py catalog import-models models.csv --skip-errors
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    # Check file exists
    csv_path = Path(csv_file)
    if not csv_path.exists():
        typer.secho(f"❌ File not found: {csv_file}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    # First, fetch existing models to check for duplicates
    log("Fetching existing models for duplicate detection...")
    response = session.get(f"{BASE_URL}/llm-catalog/models", params={"limit": 1000})
    if response.status_code != 200:
        typer.secho("❌ Failed to fetch existing models", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    existing_models = response.json().get("data", [])

    # Build lookup: (provider_type_id, model_id) -> model
    existing_lookup = {}
    for model in existing_models:
        key = (model.get("primary_provider_type_id"), model.get("model_id"))
        existing_lookup[key] = model

    log(f"Found {len(existing_models)} existing models")

    # Parse CSV
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # Validate headers
        if reader.fieldnames:
            missing_headers = set(["provider_name", "model_id", "display_name"]) - set(reader.fieldnames)
            if missing_headers:
                typer.secho(f"❌ Missing required columns: {missing_headers}", fg=typer.colors.RED, err=True)
                raise typer.Exit(1)

        rows = list(reader)

    typer.echo(f"\n📋 Processing {len(rows)} rows from {csv_file}\n")

    if dry_run:
        typer.secho("🔍 DRY RUN - No changes will be made\n", fg=typer.colors.YELLOW)

    # Statistics
    stats = {
        "created": 0,
        "updated": 0,
        "skipped": 0,
        "errors": 0,
    }

    for i, row in enumerate(rows, 1):
        provider_name = row.get("provider_name", "").strip()
        model_id = row.get("model_id", "").strip()
        display_name = row.get("display_name", "").strip()

        # Skip empty rows
        if not provider_name or not model_id or not display_name:
            log(f"Row {i}: Skipping empty row")
            continue

        # Resolve provider name to UUID
        provider_uuid = PROVIDER_NAME_TO_UUID.get(provider_name)
        if not provider_uuid:
            typer.secho(f"  ⚠️  Row {i}: Unknown provider '{provider_name}' - skipping", fg=typer.colors.YELLOW)
            stats["skipped"] += 1
            continue

        # Check if exists
        existing = existing_lookup.get((provider_uuid, model_id))

        # Build payload
        payload = {
            "model_id": model_id,
            "display_name": display_name,
            "primary_provider_type_id": provider_uuid,
            "description": row.get("description", "").strip() or None,
            "context_window": _parse_int(row.get("context_window")),
            "is_default": _parse_bool(row.get("is_default", "false")),
            "is_enabled": _parse_bool(row.get("is_enabled", "true")),
            "sort_order": _parse_int(row.get("sort_order")) or 0,
        }

        # Capability flags (handle unknown/empty as None)
        for cap_field, csv_field in [
            ("has_vision", "has_vision"),
            ("has_function_calling", "has_function_calling"),
            ("has_streaming", "has_streaming"),
            ("has_json_mode", "has_json_mode"),
        ]:
            csv_value = row.get(csv_field, "").strip()
            if csv_value:
                payload[cap_field] = _parse_bool(csv_value)
            # If empty, don't include (will be None/unknown)

        if existing:
            if update_existing:
                # Update existing model
                if dry_run:
                    typer.echo(f"  🔄 Would UPDATE: {display_name} ({model_id}) [{provider_name}]")
                    stats["updated"] += 1
                else:
                    log(f"PATCH /llm-catalog/models/{existing['id']}")
                    resp = session.patch(
                        f"{BASE_URL}/llm-catalog/models/{existing['id']}",
                        json=payload
                    )
                    if resp.status_code == 200:
                        typer.secho(f"  🔄 Updated: {display_name} ({model_id}) [{provider_name}]", fg=typer.colors.BLUE)
                        stats["updated"] += 1
                    elif resp.status_code == 403:
                        typer.secho(f"  ❌ Permission denied (superuser required)", fg=typer.colors.RED, err=True)
                        if not skip_errors:
                            raise typer.Exit(1)
                        stats["errors"] += 1
                    else:
                        typer.secho(f"  ❌ Failed to update: {resp.text}", fg=typer.colors.RED, err=True)
                        if not skip_errors:
                            raise typer.Exit(1)
                        stats["errors"] += 1
            else:
                typer.echo(f"  ⏭️  Skipping (exists): {display_name} ({model_id})")
                stats["skipped"] += 1
        else:
            # Create new model
            if dry_run:
                typer.echo(f"  ✨ Would CREATE: {display_name} ({model_id}) [{provider_name}]")
                stats["created"] += 1
            else:
                log(f"POST /llm-catalog/models")
                log(f"Payload: {json.dumps(payload, indent=2)}")
                resp = session.post(f"{BASE_URL}/llm-catalog/models", json=payload)
                if resp.status_code == 200:
                    typer.secho(f"  ✅ Created: {display_name} ({model_id}) [{provider_name}]", fg=typer.colors.GREEN)
                    stats["created"] += 1
                    # Add to lookup so we don't try to create again
                    new_model = resp.json()
                    existing_lookup[(provider_uuid, model_id)] = new_model
                elif resp.status_code == 400:
                    detail = resp.json().get("detail", resp.text)
                    typer.secho(f"  ❌ Failed: {detail}", fg=typer.colors.RED, err=True)
                    if not skip_errors:
                        raise typer.Exit(1)
                    stats["errors"] += 1
                elif resp.status_code == 403:
                    typer.secho(f"  ❌ Permission denied (superuser required)", fg=typer.colors.RED, err=True)
                    if not skip_errors:
                        raise typer.Exit(1)
                    stats["errors"] += 1
                else:
                    typer.secho(f"  ❌ Failed: {resp.text}", fg=typer.colors.RED, err=True)
                    if not skip_errors:
                        raise typer.Exit(1)
                    stats["errors"] += 1

    # Summary
    typer.echo()
    if dry_run:
        typer.secho("📊 DRY RUN Summary:", fg=typer.colors.YELLOW, bold=True)
    else:
        typer.secho("📊 Import Summary:", fg=typer.colors.GREEN, bold=True)

    typer.echo(f"   Created: {stats['created']}")
    typer.echo(f"   Updated: {stats['updated']}")
    typer.echo(f"   Skipped: {stats['skipped']}")
    if stats["errors"]:
        typer.secho(f"   Errors:  {stats['errors']}", fg=typer.colors.RED)

    if dry_run:
        typer.echo("\n💡 Run without --dry-run to apply changes")


@app.command("template")
def export_template(
    output_file: Annotated[
        str | None,
        typer.Option("--output", "-o", help="Output file path (default: stdout)")
    ] = None,
):
    """
    Export a CSV template with example rows.

    Use this as a starting point for creating your own model catalog CSV.

    Examples:
        python main.py catalog template
        python main.py catalog template -o template.csv
    """

    template = '''provider_name,model_id,display_name,description,context_window,is_default,is_enabled,sort_order,has_vision,has_function_calling,has_streaming,has_json_mode
OpenAI,gpt-4o,GPT-4o,Latest multimodal flagship,128000,false,true,0,true,true,true,true
OpenAI,gpt-4o-mini,GPT-4o Mini,Fast and affordable,128000,true,true,1,true,true,true,true
Anthropic,claude-3-5-sonnet-latest,Claude 3.5 Sonnet,Balanced intelligence,200000,false,true,0,true,true,true,true
Anthropic,claude-3-5-haiku-latest,Claude 3.5 Haiku,Fast and affordable,200000,true,true,1,true,true,true,true
Google,gemini-1.5-flash,Gemini 1.5 Flash,Fast and capable,1048576,true,true,0,true,true,true,true
'''

    if output_file:
        Path(output_file).write_text(template)
        typer.secho(f"✅ Template saved to {output_file}", fg=typer.colors.GREEN)
    else:
        typer.echo(template)


# =============================================================================
# SEARCH & FILTER COMMANDS
# =============================================================================
# Commands for finding models by various criteria.
# =============================================================================


@app.command("search")
def search_models(
    query: Annotated[
        str | None,
        typer.Argument(help="Search term (searches model_id and display_name)")
    ] = None,
    provider: Annotated[
        str | None,
        typer.Option("--provider", "-p", help="Filter by provider name or UUID")
    ] = None,
    vision: Annotated[
        bool | None,
        typer.Option("--vision/--no-vision", help="Filter by vision capability")
    ] = None,
    tools: Annotated[
        bool | None,
        typer.Option("--tools/--no-tools", help="Filter by function calling")
    ] = None,
    streaming: Annotated[
        bool | None,
        typer.Option("--streaming/--no-streaming", help="Filter by streaming")
    ] = None,
    json_mode: Annotated[
        bool | None,
        typer.Option("--json-mode/--no-json-mode", help="Filter by JSON mode")
    ] = None,
    enabled_only: Annotated[
        bool,
        typer.Option("--enabled", "-e", help="Only show enabled models")
    ] = False,
    defaults_only: Annotated[
        bool,
        typer.Option("--defaults", "-d", help="Only show default models")
    ] = False,
    min_context: Annotated[
        int | None,
        typer.Option("--min-context", help="Minimum context window size")
    ] = None,
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show debug output")
    ] = False,
):
    """
    Search and filter models in the catalog.

    Combines text search with capability and attribute filters.

    Examples:
        # Search by name
        python main.py catalog search gpt

        # Find vision-capable models
        python main.py catalog search --vision

        # Find OpenAI models with tools
        python main.py catalog search --provider openai --tools

        # Find models with large context
        python main.py catalog search --min-context 100000

        # Find default models (cheapest per provider)
        python main.py catalog search --defaults

        # Combine filters
        python main.py catalog search claude --vision --tools --enabled
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    # Fetch all models
    log("GET /llm-catalog/models?limit=1000")
    response = session.get(f"{BASE_URL}/llm-catalog/models", params={"limit": 1000})

    if response.status_code != 200:
        typer.secho("❌ Failed to fetch models", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    models = response.json().get("data", [])
    log(f"Fetched {len(models)} models, applying filters...")

    # Resolve provider filter
    provider_uuid_filter = None
    if provider:
        if _is_uuid(provider):
            provider_uuid_filter = provider
        else:
            provider_uuid_filter = PROVIDER_NAME_TO_UUID.get(provider) or PROVIDER_NAME_TO_UUID.get(provider.lower())
            if not provider_uuid_filter:
                resp = session.get(f"{BASE_URL}/llm-providers/by_name/{provider}")
                if resp.status_code == 200:
                    provider_uuid_filter = resp.json().get("id")

    # Apply filters
    filtered = []
    for model in models:
        # Text search (case-insensitive)
        if query:
            q = query.lower()
            model_id = (model.get("model_id") or "").lower()
            display_name = (model.get("display_name") or "").lower()
            description = (model.get("description") or "").lower()
            if q not in model_id and q not in display_name and q not in description:
                continue

        # Provider filter
        if provider_uuid_filter:
            if model.get("primary_provider_type_id") != provider_uuid_filter:
                continue

        # Capability filters
        if vision is not None and model.get("has_vision") != vision:
            continue
        if tools is not None and model.get("has_function_calling") != tools:
            continue
        if streaming is not None and model.get("has_streaming") != streaming:
            continue
        if json_mode is not None and model.get("has_json_mode") != json_mode:
            continue

        # Attribute filters
        if enabled_only and not model.get("is_enabled", True):
            continue
        if defaults_only and not model.get("is_default", False):
            continue

        # Context window filter
        if min_context is not None:
            ctx = model.get("context_window") or 0
            if ctx < min_context:
                continue

        filtered.append(model)

    log(f"Filtered to {len(filtered)} models")

    # Output
    if json_output:
        typer.echo(json.dumps({"data": filtered, "count": len(filtered)}, indent=2))
    else:
        # Build filter description
        filters_desc = []
        if query:
            filters_desc.append(f"'{query}'")
        if provider:
            filters_desc.append(f"provider={provider}")
        if vision is not None:
            filters_desc.append(f"vision={'yes' if vision else 'no'}")
        if tools is not None:
            filters_desc.append(f"tools={'yes' if tools else 'no'}")
        if streaming is not None:
            filters_desc.append(f"streaming={'yes' if streaming else 'no'}")
        if json_mode is not None:
            filters_desc.append(f"json_mode={'yes' if json_mode else 'no'}")
        if enabled_only:
            filters_desc.append("enabled")
        if defaults_only:
            filters_desc.append("defaults")
        if min_context:
            filters_desc.append(f"context>={min_context:,}")

        filter_str = ", ".join(filters_desc) if filters_desc else "none"

        typer.echo(f"\n🔍 Search Results ({len(filtered)} models)")
        typer.echo(f"   Filters: {filter_str}\n")

        if not filtered:
            typer.secho("  No models match the criteria", fg=typer.colors.YELLOW)
        else:
            # Group by provider for cleaner output
            by_provider = {}
            for model in filtered:
                provider_uuid = model.get("primary_provider_type_id", "unknown")
                provider_name = PROVIDER_UUID_TO_NAME.get(provider_uuid, provider_uuid[:8] + "...")
                if provider_name not in by_provider:
                    by_provider[provider_name] = []
                by_provider[provider_name].append(model)

            for provider_name, provider_models in sorted(by_provider.items()):
                typer.secho(f"  {provider_name} ({len(provider_models)}):", fg=typer.colors.BLUE, bold=True)
                for model in provider_models:
                    _print_model_compact(model)
                typer.echo()


@app.command("stats")
def catalog_stats(
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show debug output")
    ] = False,
):
    """
    Show statistics about the model catalog.

    Provides an overview of models by provider, capabilities, and status.

    Examples:
        python main.py catalog stats
        python main.py catalog stats --json
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    # Fetch all models
    response = session.get(f"{BASE_URL}/llm-catalog/models", params={"limit": 1000})
    if response.status_code != 200:
        typer.secho("❌ Failed to fetch models", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    models = response.json().get("data", [])

    # Calculate stats
    stats = {
        "total": len(models),
        "enabled": sum(1 for m in models if m.get("is_enabled", True)),
        "disabled": sum(1 for m in models if not m.get("is_enabled", True)),
        "deprecated": sum(1 for m in models if m.get("is_deprecated", False)),
        "defaults": sum(1 for m in models if m.get("is_default", False)),
        "by_provider": {},
        "capabilities": {
            "vision": sum(1 for m in models if m.get("has_vision")),
            "tools": sum(1 for m in models if m.get("has_function_calling")),
            "streaming": sum(1 for m in models if m.get("has_streaming")),
            "json_mode": sum(1 for m in models if m.get("has_json_mode")),
        },
        "context_windows": {
            "min": None,
            "max": None,
            "avg": None,
        },
    }

    # By provider
    for model in models:
        provider_uuid = model.get("primary_provider_type_id", "unknown")
        provider_name = PROVIDER_UUID_TO_NAME.get(provider_uuid, "Other")
        if provider_name not in stats["by_provider"]:
            stats["by_provider"][provider_name] = {"total": 0, "enabled": 0}
        stats["by_provider"][provider_name]["total"] += 1
        if model.get("is_enabled", True):
            stats["by_provider"][provider_name]["enabled"] += 1

    # Context window stats
    context_windows = [m.get("context_window") for m in models if m.get("context_window")]
    if context_windows:
        stats["context_windows"]["min"] = min(context_windows)
        stats["context_windows"]["max"] = max(context_windows)
        stats["context_windows"]["avg"] = sum(context_windows) // len(context_windows)

    if json_output:
        typer.echo(json.dumps(stats, indent=2))
    else:
        typer.echo("\n📊 Model Catalog Statistics\n")

        typer.echo(f"  Total Models:    {stats['total']}")
        typer.echo(f"  Enabled:         {stats['enabled']}")
        typer.echo(f"  Disabled:        {stats['disabled']}")
        typer.echo(f"  Deprecated:      {stats['deprecated']}")
        typer.echo(f"  Default Models:  {stats['defaults']}")

        typer.echo("\n  By Provider:")
        for provider, pstats in sorted(stats["by_provider"].items()):
            typer.echo(f"    {provider:20} {pstats['total']:3} total, {pstats['enabled']:3} enabled")

        typer.echo("\n  Capabilities:")
        typer.echo(f"    Vision:            {stats['capabilities']['vision']}")
        typer.echo(f"    Function Calling:  {stats['capabilities']['tools']}")
        typer.echo(f"    Streaming:         {stats['capabilities']['streaming']}")
        typer.echo(f"    JSON Mode:         {stats['capabilities']['json_mode']}")

        if stats["context_windows"]["min"]:
            typer.echo("\n  Context Windows:")
            typer.echo(f"    Min:  {stats['context_windows']['min']:,} tokens")
            typer.echo(f"    Max:  {stats['context_windows']['max']:,} tokens")
            typer.echo(f"    Avg:  {stats['context_windows']['avg']:,} tokens")


# =============================================================================
# OUTPUT HELPERS
# =============================================================================
# Pretty-print functions for displaying data in the terminal.
# =============================================================================


def _is_uuid(value: str) -> bool:
    """Check if a string looks like a UUID."""
    import re
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_pattern.match(value))


def _parse_bool(val: str | None) -> bool:
    """
    Parse a boolean from CSV value.

    Accepts: true/false, yes/no, 1/0, t/f
    Returns False for empty/None values.
    """
    if not val or not str(val).strip():
        return False
    return str(val).strip().lower() in ("true", "1", "yes", "t")


def _parse_int(val: str | None) -> int | None:
    """
    Parse an integer from CSV value.

    Returns None for empty/invalid values.
    """
    if not val or not str(val).strip():
        return None
    try:
        return int(str(val).strip())
    except ValueError:
        return None


def _bool_to_csv(val: bool | None) -> str:
    """
    Convert a boolean to CSV format.

    None (unknown) -> empty string
    True/False -> lowercase string
    """
    if val is None:
        return ""
    return "true" if val else "false"


def _print_provider_type(pt: dict, verbose: bool = False) -> None:
    """
    Pretty-print a provider type (catalog entry).

    Provider types are like "openai", "anthropic" - the available integrations.
    """
    name = pt.get("name", "Unknown")
    pt_id = pt.get("id", "N/A")
    is_system = pt.get("is_system", False)
    validated = pt.get("validated", False)

    # Status indicators
    system_badge = " 🔧 [system]" if is_system else ""
    validated_badge = " ✅" if validated else " ⚠️"

    typer.secho(f"  • {name}{system_badge}{validated_badge}", fg=typer.colors.CYAN)
    typer.echo(f"    ID: {pt_id}")

    if pt.get("details"):
        typer.echo(f"    Details: {pt['details']}")

    if verbose:
        typer.echo(f"    Validated: {'Yes' if validated else 'No'}")
        typer.echo(f"    System: {'Yes' if is_system else 'No'}")

    typer.echo()


def _print_user_provider(provider: dict, verbose: bool = False) -> None:
    """
    Pretty-print a user's provider configuration.

    These are YOUR configured providers with API keys.
    Note: API keys are never returned from the API (encrypted at rest).
    """
    name = provider.get("name", "Unnamed")
    provider_id = provider.get("id", "N/A")
    enabled = provider.get("is_enabled", True)
    is_default = provider.get("is_default", False)
    alpha_type_id = provider.get("alpha_provider_type_id", "N/A")

    # Status indicators
    status = "✅" if enabled else "❌"
    default_badge = " ⭐ [default]" if is_default else ""

    typer.echo(f"  {status} ", nl=False)
    typer.secho(f"{name}{default_badge}", fg=typer.colors.CYAN)
    typer.echo(f"    ID: {provider_id}")
    typer.echo(f"    Provider Type ID: {alpha_type_id}")

    if provider.get("base_url"):
        typer.echo(f"    Base URL: {provider['base_url']}")

    if provider.get("description"):
        typer.echo(f"    Description: {provider['description']}")

    # Note about API keys
    typer.secho(f"    API Key: [encrypted - never returned]", fg=typer.colors.MAGENTA)

    if verbose:
        typer.echo(f"    Enabled: {'Yes' if enabled else 'No'}")
        typer.echo(f"    Default: {'Yes' if is_default else 'No'}")
        typer.echo(f"    Validated: {'Yes' if provider.get('is_validated') else 'No'}")
        typer.echo(f"    Owner ID: {provider.get('owner_id', 'N/A')}")

    typer.echo()


def _print_model(model: dict, verbose: bool = False) -> None:
    """
    Pretty-print an LLM model from the catalog (list view).

    Models are the actual LLM models (gpt-4o, claude-3-opus, etc.)
    """
    display_name = model.get("display_name", "Unknown")
    model_id = model.get("model_id", "N/A")  # The actual model identifier
    db_id = model.get("id", "N/A")  # Database UUID
    enabled = model.get("is_enabled", True)
    is_default = model.get("is_default", False)
    is_deprecated = model.get("is_deprecated", False)

    # Status indicators
    status = "✅" if enabled else "❌"
    default_badge = " ⭐" if is_default else ""
    deprecated_badge = " ⚠️ DEPRECATED" if is_deprecated else ""

    typer.echo(f"  {status}{default_badge} ", nl=False)
    typer.secho(f"{display_name}{deprecated_badge}", fg=typer.colors.CYAN)
    typer.echo(f"    Model ID: {model_id}")
    typer.echo(f"    UUID: {db_id}")

    if model.get("description"):
        desc = model["description"]
        if len(desc) > 60:
            desc = desc[:60] + "..."
        typer.echo(f"    Desc: {desc}")

    # Capabilities (show what this model can do)
    caps = []
    if model.get("has_vision"):
        caps.append("👁️ vision")
    if model.get("has_function_calling"):
        caps.append("🔧 tools")
    if model.get("has_streaming"):
        caps.append("📡 streaming")
    if model.get("has_json_mode"):
        caps.append("📋 json")
    if caps:
        typer.echo(f"    Capabilities: {', '.join(caps)}")

    if model.get("context_window"):
        ctx = model["context_window"]
        typer.echo(f"    Context: {ctx:,} tokens")

    if verbose:
        typer.echo(f"    Provider Type ID: {model.get('primary_provider_type_id', 'N/A')}")
        typer.echo(f"    Sort Order: {model.get('sort_order', 0)}")
        typer.echo(f"    System: {'Yes' if model.get('is_system') else 'No'}")

    typer.echo()


def _print_model_detail(model: dict) -> None:
    """
    Pretty-print detailed LLM model information (single model view).

    Shows all available fields for a model.
    """
    # Basic info
    typer.echo(f"  UUID:         {model.get('id', 'N/A')}")
    typer.echo(f"  Model ID:     {model.get('model_id', 'N/A')}")
    typer.echo(f"  Display Name: {model.get('display_name', 'N/A')}")

    # Provider
    typer.echo(f"  Provider Type ID: {model.get('primary_provider_type_id', 'N/A')}")

    # Status flags with color
    enabled = model.get("is_enabled", True)
    typer.echo(f"  Enabled:      ", nl=False)
    typer.secho("Yes" if enabled else "No", fg=typer.colors.GREEN if enabled else typer.colors.RED)

    is_default = model.get("is_default", False)
    if is_default:
        typer.secho(f"  Default:      ⭐ Yes (cheapest for provider)", fg=typer.colors.YELLOW)
    else:
        typer.echo(f"  Default:      No")

    is_deprecated = model.get("is_deprecated", False)
    if is_deprecated:
        typer.secho(f"  Deprecated:   ⚠️ Yes", fg=typer.colors.YELLOW)
    else:
        typer.echo(f"  Deprecated:   No")

    is_system = model.get("is_system", False)
    typer.echo(f"  System:       {'Yes' if is_system else 'No'}")

    # Description
    if model.get("description"):
        typer.echo(f"  Description:  {model['description']}")

    # Context window
    if model.get("context_window"):
        ctx = model["context_window"]
        typer.echo(f"  Context:      {ctx:,} tokens")

    # Sort order
    typer.echo(f"  Sort Order:   {model.get('sort_order', 0)}")

    # Capabilities section
    typer.echo()
    typer.secho("  Capabilities:", fg=typer.colors.BLUE, bold=True)

    def _cap_display(value: bool | None, name: str) -> str:
        if value is True:
            return f"✅ {name}"
        elif value is False:
            return f"❌ {name}"
        else:
            return f"❓ {name} (unknown)"

    typer.echo(f"    {_cap_display(model.get('has_vision'), 'Vision (image input)')}")
    typer.echo(f"    {_cap_display(model.get('has_function_calling'), 'Function Calling (tools)')}")
    typer.echo(f"    {_cap_display(model.get('has_streaming'), 'Streaming')}")
    typer.echo(f"    {_cap_display(model.get('has_json_mode'), 'JSON Mode')}")

    # Secondary capabilities (if any)
    if model.get("secondary_capabilities"):
        typer.echo()
        typer.secho("  Secondary Capabilities:", fg=typer.colors.BLUE, bold=True)
        typer.echo(f"    {json.dumps(model['secondary_capabilities'], indent=4)}")

    # Owner
    if model.get("owner_id"):
        typer.echo()
        typer.echo(f"  Owner ID:     {model['owner_id']}")


def _print_model_compact(model: dict) -> None:
    """
    Print a compact one-line model summary for search results.

    Format: [status] display_name (model_id) - caps - context
    """
    display_name = model.get("display_name", "Unknown")
    model_id = model.get("model_id", "")
    enabled = model.get("is_enabled", True)
    is_default = model.get("is_default", False)
    is_deprecated = model.get("is_deprecated", False)

    # Status indicators
    status = "✅" if enabled else "❌"
    badges = []
    if is_default:
        badges.append("⭐")
    if is_deprecated:
        badges.append("⚠️")

    # Capabilities (short form)
    caps = []
    if model.get("has_vision"):
        caps.append("👁️")
    if model.get("has_function_calling"):
        caps.append("🔧")
    if model.get("has_streaming"):
        caps.append("📡")
    if model.get("has_json_mode"):
        caps.append("📋")

    # Context window (abbreviated)
    ctx_str = ""
    if model.get("context_window"):
        ctx = model["context_window"]
        if ctx >= 1000000:
            ctx_str = f" [{ctx // 1000000}M ctx]"
        elif ctx >= 1000:
            ctx_str = f" [{ctx // 1000}K ctx]"

    # Build the line
    badge_str = " ".join(badges) + " " if badges else ""
    caps_str = " ".join(caps) if caps else ""

    typer.echo(f"    {status} {badge_str}", nl=False)
    typer.secho(f"{display_name}", fg=typer.colors.CYAN, nl=False)
    typer.echo(f" ({model_id}) {caps_str}{ctx_str}")


# =============================================================================
# MAIN (for testing module directly)
# =============================================================================

if __name__ == "__main__":
    app()
