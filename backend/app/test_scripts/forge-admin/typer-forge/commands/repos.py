"""
Repository Management Commands

Commands for creating and managing Forgejo repositories.
"""

import typer
import json
from typing import Annotated

# Import forge client and SDK
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from forge_client import get_repository_api, get_user_api, get_admin_api
from openapi_client.models.create_repo_option import CreateRepoOption
from openapi_client.rest import ApiException

app = typer.Typer(help="Repository management commands")


# =============================================================================
# Helper Functions
# =============================================================================

def handle_api_error(e: ApiException, context: str = "operation"):
    """Standard error handling for API exceptions."""
    typer.secho(f"❌ Failed to {context}: {e.status} - {e.reason}", fg=typer.colors.RED)
    if e.body:
        typer.echo(f"   {e.body[:300]}")
    raise typer.Exit(1)


def format_repo(repo, verbose: bool = False) -> None:
    """Format and print repository info."""
    private_badge = "🔒" if repo.get('private') else "🌐"
    fork_badge = " (fork)" if repo.get('fork') else ""

    typer.echo(f"  {private_badge} {repo.get('full_name')}{fork_badge}")
    typer.echo(f"     ID: {repo.get('id')}")

    if repo.get('description'):
        typer.echo(f"     Desc: {repo.get('description')[:60]}...")

    if verbose:
        typer.echo(f"     Default Branch: {repo.get('default_branch', 'N/A')}")
        typer.echo(f"     Stars: {repo.get('stars_count', 0)} | Forks: {repo.get('forks_count', 0)}")
        typer.echo(f"     Clone: {repo.get('clone_url', 'N/A')}")

    typer.echo()


# =============================================================================
# Repository Commands
# =============================================================================

@app.command()
def create(
    name: Annotated[str, typer.Argument(help="Repository name")],
    description: Annotated[str, typer.Option("--desc", "-d", help="Repository description")] = "",
    private: Annotated[bool, typer.Option("--private", "-p", help="Make repository private")] = False,
    auto_init: Annotated[bool, typer.Option("--init", help="Initialize with README")] = True,
    default_branch: Annotated[str, typer.Option("--branch", "-b", help="Default branch name")] = "main",
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose output")] = False,
):
    """
    Create a new repository for the current user.

    Example:
        python main.py repos create my-repo
        python main.py repos create my-repo --desc "My project" --private
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    log(f"Creating repository: {name}")

    repo_options = CreateRepoOption(
        name=name,
        description=description or None,
        private=private,
        auto_init=auto_init,
        default_branch=default_branch,
    )

    log(f"Payload: {repo_options.to_dict()}")

    try:
        repo_api = get_repository_api()
        repo = repo_api.create_current_user_repo(body=repo_options)
        repo_dict = repo.to_dict()

        if json_output:
            typer.echo(json.dumps(repo_dict, indent=2, default=str))
        else:
            typer.secho("✅ Repository created successfully!", fg=typer.colors.GREEN)
            typer.echo(f"\nName: {repo_dict.get('full_name')}")
            typer.echo(f"URL: {repo_dict.get('html_url')}")
            typer.echo(f"Clone: {repo_dict.get('clone_url')}")
            typer.echo(f"Private: {'Yes' if repo_dict.get('private') else 'No'}")

    except ApiException as e:
        if e.status == 409:
            typer.secho(f"❌ Repository '{name}' already exists", fg=typer.colors.RED)
            raise typer.Exit(1)
        handle_api_error(e, "create repository")


@app.command()
def get(
    owner: Annotated[str, typer.Argument(help="Repository owner (user or org)")],
    repo: Annotated[str, typer.Argument(help="Repository name")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """
    Get repository information.

    Example:
        python main.py repos get myuser myrepo
    """
    try:
        repo_api = get_repository_api()
        repository = repo_api.repo_get(owner=owner, repo=repo)
        repo_dict = repository.to_dict()

        if json_output:
            typer.echo(json.dumps(repo_dict, indent=2, default=str))
        else:
            private_badge = "🔒 Private" if repo_dict.get('private') else "🌐 Public"

            typer.echo(f"\n📦 {repo_dict.get('full_name')} ({private_badge})\n")
            typer.echo(f"ID: {repo_dict.get('id')}")
            typer.echo(f"Description: {repo_dict.get('description') or 'N/A'}")
            typer.echo(f"Default Branch: {repo_dict.get('default_branch')}")
            typer.echo(f"\nStats:")
            typer.echo(f"  ⭐ Stars: {repo_dict.get('stars_count', 0)}")
            typer.echo(f"  🍴 Forks: {repo_dict.get('forks_count', 0)}")
            typer.echo(f"  👁️  Watchers: {repo_dict.get('watchers_count', 0)}")
            typer.echo(f"  📝 Open Issues: {repo_dict.get('open_issues_count', 0)}")
            typer.echo(f"\nURLs:")
            typer.echo(f"  Web: {repo_dict.get('html_url')}")
            typer.echo(f"  Clone: {repo_dict.get('clone_url')}")

    except ApiException as e:
        if e.status == 404:
            typer.secho(f"❌ Repository '{owner}/{repo}' not found", fg=typer.colors.RED)
            raise typer.Exit(1)
        handle_api_error(e, "get repository")


@app.command("list")
def list_repos(
    owner: Annotated[str, typer.Option("--owner", "-o", help="Filter by owner")] = None,
    limit: Annotated[int, typer.Option(help="Max repos to return")] = 20,
    page: Annotated[int, typer.Option(help="Page number")] = 1,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show more details")] = False,
):
    """
    List repositories. Lists current user's repos by default.

    Example:
        python main.py repos list
        python main.py repos list --owner someuser
    """
    try:
        user_api = get_user_api()

        if owner:
            # List repos for specific user
            repos = user_api.user_list_repos(username=owner, limit=limit, page=page)
        else:
            # List current user's repos
            repos = user_api.user_current_list_repos(limit=limit, page=page)

        if json_output:
            repos_list = [r.to_dict() for r in repos]
            typer.echo(json.dumps(repos_list, indent=2, default=str))
        else:
            owner_str = f" for {owner}" if owner else " (yours)"
            typer.echo(f"\n📦 Repositories{owner_str} (page {page}):\n")

            if not repos:
                typer.secho("  No repositories found", fg=typer.colors.YELLOW)
            else:
                for repo in repos:
                    format_repo(repo.to_dict(), verbose=verbose)

                typer.echo(f"  Showing {len(repos)} repositories")

    except ApiException as e:
        if e.status == 404:
            typer.secho(f"❌ User '{owner}' not found", fg=typer.colors.RED)
            raise typer.Exit(1)
        handle_api_error(e, "list repositories")


@app.command()
def delete(
    owner: Annotated[str, typer.Argument(help="Repository owner")],
    repo: Annotated[str, typer.Argument(help="Repository name")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False,
):
    """
    Delete a repository (cannot be undone!).

    Example:
        python main.py repos delete myuser myrepo
        python main.py repos delete myuser myrepo --force
    """
    if not force:
        typer.secho(f"⚠️  This will PERMANENTLY delete '{owner}/{repo}'", fg=typer.colors.RED)
        typer.secho("   All issues, PRs, and data will be lost!", fg=typer.colors.RED)
        if not typer.confirm("Are you absolutely sure?"):
            typer.echo("Cancelled.")
            raise typer.Exit(0)

    try:
        repo_api = get_repository_api()
        repo_api.repo_delete(owner=owner, repo=repo)
        typer.secho(f"✅ Repository '{owner}/{repo}' deleted", fg=typer.colors.GREEN)

    except ApiException as e:
        if e.status == 404:
            typer.secho(f"❌ Repository '{owner}/{repo}' not found", fg=typer.colors.RED)
            raise typer.Exit(1)
        elif e.status == 403:
            typer.secho(f"❌ Permission denied", fg=typer.colors.RED)
            raise typer.Exit(1)
        handle_api_error(e, "delete repository")


@app.command()
def fork(
    owner: Annotated[str, typer.Argument(help="Source repository owner")],
    repo: Annotated[str, typer.Argument(help="Source repository name")],
    new_name: Annotated[str, typer.Option("--name", "-n", help="Name for the fork")] = None,
    org: Annotated[str, typer.Option("--org", "-o", help="Fork to organization")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """
    Fork a repository.

    Example:
        python main.py repos fork someuser somerepo
        python main.py repos fork someuser somerepo --name my-fork
    """
    try:
        repo_api = get_repository_api()

        # Build fork options
        from openapi_client.models.create_fork_option import CreateForkOption
        fork_options = CreateForkOption(
            name=new_name,
            organization=org,
        )

        forked = repo_api.create_fork(owner=owner, repo=repo, body=fork_options)
        forked_dict = forked.to_dict()

        if json_output:
            typer.echo(json.dumps(forked_dict, indent=2, default=str))
        else:
            typer.secho("✅ Repository forked successfully!", fg=typer.colors.GREEN)
            typer.echo(f"\nForked to: {forked_dict.get('full_name')}")
            typer.echo(f"URL: {forked_dict.get('html_url')}")

    except ApiException as e:
        if e.status == 404:
            typer.secho(f"❌ Repository '{owner}/{repo}' not found", fg=typer.colors.RED)
            raise typer.Exit(1)
        elif e.status == 409:
            typer.secho(f"❌ Fork already exists", fg=typer.colors.RED)
            raise typer.Exit(1)
        handle_api_error(e, "fork repository")


@app.command()
def search(
    query: Annotated[str, typer.Argument(help="Search query")],
    limit: Annotated[int, typer.Option(help="Max results")] = 20,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """
    Search for repositories.

    Example:
        python main.py repos search "python api"
    """
    try:
        repo_api = get_repository_api()
        result = repo_api.repo_search(q=query, limit=limit)

        # result has 'data' and 'ok' fields
        repos = result.data if hasattr(result, 'data') else []

        if json_output:
            typer.echo(json.dumps([r.to_dict() for r in repos], indent=2, default=str))
        else:
            typer.echo(f"\n🔍 Search results for '{query}':\n")

            if not repos:
                typer.secho("  No repositories found", fg=typer.colors.YELLOW)
            else:
                for repo in repos:
                    format_repo(repo.to_dict())

                typer.echo(f"  Found {len(repos)} repositories")

    except ApiException as e:
        handle_api_error(e, "search repositories")


# =============================================================================
# Direct execution
# =============================================================================

if __name__ == "__main__":
    app()
