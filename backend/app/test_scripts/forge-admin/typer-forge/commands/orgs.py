"""
Organization Management Commands

Commands for creating and managing Forgejo organizations.
"""

import typer
import json
from typing import Annotated

# Import forge client and SDK
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from forge_client import get_organization_api, get_admin_api
from openapi_client.models.create_org_option import CreateOrgOption
from openapi_client.models.edit_org_option import EditOrgOption
from openapi_client.rest import ApiException

app = typer.Typer(help="Organization management commands")


# =============================================================================
# Helper Functions
# =============================================================================

def handle_api_error(e: ApiException, context: str = "operation"):
    """Standard error handling for API exceptions."""
    typer.secho(f"❌ Failed to {context}: {e.status} - {e.reason}", fg=typer.colors.RED)
    if e.body:
        typer.echo(f"   {e.body[:300]}")
    raise typer.Exit(1)


def format_org(org: dict, verbose: bool = False) -> None:
    """Format and print organization info."""
    visibility_icon = {
        'public': '🌐',
        'limited': '🔓',
        'private': '🔒'
    }.get(org.get('visibility', 'public'), '🌐')

    typer.echo(f"  {visibility_icon} {org.get('name')}")

    if org.get('full_name'):
        typer.echo(f"     Full Name: {org.get('full_name')}")

    if org.get('description'):
        typer.echo(f"     Desc: {org.get('description')[:60]}...")

    if verbose:
        typer.echo(f"     ID: {org.get('id')}")
        typer.echo(f"     Location: {org.get('location') or 'N/A'}")
        typer.echo(f"     Website: {org.get('website') or 'N/A'}")

    typer.echo()


# =============================================================================
# Organization Commands
# =============================================================================

@app.command()
def create(
    name: Annotated[str, typer.Argument(help="Organization username/slug")],
    full_name: Annotated[str, typer.Option("--full-name", "-n", help="Full display name")] = None,
    description: Annotated[str, typer.Option("--desc", "-d", help="Description")] = None,
    website: Annotated[str, typer.Option("--website", "-w", help="Website URL")] = None,
    location: Annotated[str, typer.Option("--location", "-l", help="Location")] = None,
    visibility: Annotated[str, typer.Option("--visibility", help="public, limited, or private")] = "public",
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose output")] = False,
):
    """
    Create a new organization.

    Example:
        python main.py orgs create myorg
        python main.py orgs create myorg --full-name "My Organization" --desc "We do things"
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    log(f"Creating organization: {name}")

    org_options = CreateOrgOption(
        username=name,
        full_name=full_name,
        description=description,
        website=website,
        location=location,
        visibility=visibility,
    )

    log(f"Payload: {org_options.to_dict()}")

    try:
        org_api = get_organization_api()
        org = org_api.org_create(organization=org_options)
        org_dict = org.to_dict()

        if json_output:
            typer.echo(json.dumps(org_dict, indent=2, default=str))
        else:
            typer.secho("✅ Organization created successfully!", fg=typer.colors.GREEN)
            typer.echo(f"\nName: {org_dict.get('name')}")
            typer.echo(f"Full Name: {org_dict.get('full_name') or 'N/A'}")
            typer.echo(f"Visibility: {org_dict.get('visibility')}")
            typer.echo(f"ID: {org_dict.get('id')}")

    except ApiException as e:
        if e.status == 422:
            typer.secho(f"❌ Validation error (422)", fg=typer.colors.RED)
            typer.echo(f"   {e.body}")
            raise typer.Exit(1)
        elif e.status == 409:
            typer.secho(f"❌ Organization '{name}' already exists", fg=typer.colors.RED)
            raise typer.Exit(1)
        handle_api_error(e, "create organization")


@app.command()
def get(
    name: Annotated[str, typer.Argument(help="Organization name")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """
    Get organization details.

    Example:
        python main.py orgs get myorg
    """
    try:
        org_api = get_organization_api()
        org = org_api.org_get(org=name)
        org_dict = org.to_dict()

        if json_output:
            typer.echo(json.dumps(org_dict, indent=2, default=str))
        else:
            visibility_icon = {
                'public': '🌐 Public',
                'limited': '🔓 Limited',
                'private': '🔒 Private'
            }.get(org_dict.get('visibility', 'public'), '🌐 Public')

            typer.echo(f"\n🏢 {org_dict.get('name')} ({visibility_icon})\n")
            typer.echo(f"Full Name: {org_dict.get('full_name') or 'N/A'}")
            typer.echo(f"Description: {org_dict.get('description') or 'N/A'}")
            typer.echo(f"Location: {org_dict.get('location') or 'N/A'}")
            typer.echo(f"Website: {org_dict.get('website') or 'N/A'}")
            typer.echo(f"ID: {org_dict.get('id')}")

    except ApiException as e:
        if e.status == 404:
            typer.secho(f"❌ Organization '{name}' not found", fg=typer.colors.RED)
            raise typer.Exit(1)
        handle_api_error(e, "get organization")


@app.command("list")
def list_orgs(
    limit: Annotated[int, typer.Option(help="Max orgs to return")] = 20,
    page: Annotated[int, typer.Option(help="Page number")] = 1,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show more details")] = False,
):
    """
    List all public organizations.

    Example:
        python main.py orgs list
        python main.py orgs list --limit 50
    """
    try:
        org_api = get_organization_api()
        orgs = org_api.org_get_all(limit=limit, page=page)

        if json_output:
            orgs_list = [o.to_dict() for o in orgs]
            typer.echo(json.dumps(orgs_list, indent=2, default=str))
        else:
            typer.echo(f"\n🏢 Organizations (page {page}):\n")

            if not orgs:
                typer.secho("  No organizations found", fg=typer.colors.YELLOW)
            else:
                for org in orgs:
                    format_org(org.to_dict(), verbose=verbose)

                typer.echo(f"  Showing {len(orgs)} organizations")

    except ApiException as e:
        handle_api_error(e, "list organizations")


@app.command()
def delete(
    name: Annotated[str, typer.Argument(help="Organization name")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False,
):
    """
    Delete an organization (cannot be undone!).

    Example:
        python main.py orgs delete myorg
    """
    if not force:
        typer.secho(f"⚠️  This will PERMANENTLY delete organization '{name}'", fg=typer.colors.RED)
        typer.secho("   All repositories, teams, and data will be lost!", fg=typer.colors.RED)
        if not typer.confirm("Are you absolutely sure?"):
            typer.echo("Cancelled.")
            raise typer.Exit(0)

    try:
        org_api = get_organization_api()
        org_api.org_delete(org=name)
        typer.secho(f"✅ Organization '{name}' deleted", fg=typer.colors.GREEN)

    except ApiException as e:
        if e.status == 404:
            typer.secho(f"❌ Organization '{name}' not found", fg=typer.colors.RED)
            raise typer.Exit(1)
        elif e.status == 403:
            typer.secho(f"❌ Permission denied", fg=typer.colors.RED)
            raise typer.Exit(1)
        handle_api_error(e, "delete organization")


@app.command()
def members(
    name: Annotated[str, typer.Argument(help="Organization name")],
    limit: Annotated[int, typer.Option(help="Max members to return")] = 50,
    page: Annotated[int, typer.Option(help="Page number")] = 1,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """
    List organization members.

    Example:
        python main.py orgs members myorg
    """
    try:
        org_api = get_organization_api()
        members = org_api.org_list_members(org=name, limit=limit, page=page)

        if json_output:
            members_list = [m.to_dict() for m in members]
            typer.echo(json.dumps(members_list, indent=2, default=str))
        else:
            typer.echo(f"\n👥 Members of {name}:\n")

            if not members:
                typer.secho("  No members found", fg=typer.colors.YELLOW)
            else:
                for member in members:
                    m = member.to_dict()
                    admin_badge = " [Admin]" if m.get('is_admin') else ""
                    typer.echo(f"  • {m.get('login')}{admin_badge}")
                    if m.get('full_name'):
                        typer.echo(f"    {m.get('full_name')}")
                    typer.echo()

                typer.echo(f"  Showing {len(members)} members")

    except ApiException as e:
        if e.status == 404:
            typer.secho(f"❌ Organization '{name}' not found", fg=typer.colors.RED)
            raise typer.Exit(1)
        handle_api_error(e, "list members")


@app.command()
def repos(
    name: Annotated[str, typer.Argument(help="Organization name")],
    limit: Annotated[int, typer.Option(help="Max repos to return")] = 20,
    page: Annotated[int, typer.Option(help="Page number")] = 1,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """
    List organization repositories.

    Example:
        python main.py orgs repos myorg
    """
    try:
        org_api = get_organization_api()
        repos = org_api.org_list_repos(org=name, limit=limit, page=page)

        if json_output:
            repos_list = [r.to_dict() for r in repos]
            typer.echo(json.dumps(repos_list, indent=2, default=str))
        else:
            typer.echo(f"\n📦 Repositories in {name}:\n")

            if not repos:
                typer.secho("  No repositories found", fg=typer.colors.YELLOW)
            else:
                for repo in repos:
                    r = repo.to_dict()
                    private_badge = "🔒" if r.get('private') else "🌐"
                    typer.echo(f"  {private_badge} {r.get('name')}")
                    if r.get('description'):
                        typer.echo(f"     {r.get('description')[:50]}...")
                    typer.echo()

                typer.echo(f"  Showing {len(repos)} repositories")

    except ApiException as e:
        if e.status == 404:
            typer.secho(f"❌ Organization '{name}' not found", fg=typer.colors.RED)
            raise typer.Exit(1)
        handle_api_error(e, "list repositories")


@app.command()
def teams(
    name: Annotated[str, typer.Argument(help="Organization name")],
    limit: Annotated[int, typer.Option(help="Max teams to return")] = 50,
    page: Annotated[int, typer.Option(help="Page number")] = 1,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """
    List organization teams.

    Example:
        python main.py orgs teams myorg
    """
    try:
        org_api = get_organization_api()
        teams = org_api.org_list_teams(org=name, limit=limit, page=page)

        if json_output:
            teams_list = [t.to_dict() for t in teams]
            typer.echo(json.dumps(teams_list, indent=2, default=str))
        else:
            typer.echo(f"\n👥 Teams in {name}:\n")

            if not teams:
                typer.secho("  No teams found", fg=typer.colors.YELLOW)
            else:
                for team in teams:
                    t = team.to_dict()
                    typer.echo(f"  • {t.get('name')}")
                    typer.echo(f"    Permission: {t.get('permission', 'N/A')}")
                    typer.echo(f"    Members: {t.get('members_count', 0)} | Repos: {t.get('repos_count', 0)}")
                    typer.echo()

                typer.echo(f"  Showing {len(teams)} teams")

    except ApiException as e:
        if e.status == 404:
            typer.secho(f"❌ Organization '{name}' not found", fg=typer.colors.RED)
            raise typer.Exit(1)
        handle_api_error(e, "list teams")


# =============================================================================
# Direct execution
# =============================================================================

if __name__ == "__main__":
    app()
