"""
Wiki Management Commands

Commands for creating and managing Forgejo repository wikis.
"""

import typer
import json
import base64
from typing import Annotated

# Import forge client and SDK
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from forge_client import get_repository_api
from openapi_client.models.create_wiki_page_options import CreateWikiPageOptions
from openapi_client.rest import ApiException

app = typer.Typer(help="Wiki management commands")


# =============================================================================
# Helper Functions
# =============================================================================

def handle_api_error(e: ApiException, context: str = "operation"):
    """Standard error handling for API exceptions."""
    typer.secho(f"❌ Failed to {context}: {e.status} - {e.reason}", fg=typer.colors.RED)
    if e.body:
        typer.echo(f"   {e.body[:300]}")
    raise typer.Exit(1)


def encode_content(content: str) -> str:
    """Base64 encode content for wiki API."""
    return base64.b64encode(content.encode('utf-8')).decode('utf-8')


def decode_content(content_base64: str) -> str:
    """Decode base64 content from wiki API."""
    return base64.b64decode(content_base64).decode('utf-8')


# =============================================================================
# Wiki Commands
# =============================================================================

@app.command()
def create(
    owner: Annotated[str, typer.Argument(help="Repository owner")],
    repo: Annotated[str, typer.Argument(help="Repository name")],
    title: Annotated[str, typer.Argument(help="Wiki page title")],
    content: Annotated[str, typer.Option("--content", "-c", help="Page content (markdown)")] = None,
    file: Annotated[Path, typer.Option("--file", "-f", help="Read content from file")] = None,
    message: Annotated[str, typer.Option("--message", "-m", help="Commit message")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose output")] = False,
):
    """
    Create a new wiki page.

    Example:
        python main.py wiki create owner repo "Home" --content "# Welcome"
        python main.py wiki create owner repo "Setup" --file ./docs/setup.md
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    # Get content from file or option
    if file:
        if not file.exists():
            typer.secho(f"❌ File not found: {file}", fg=typer.colors.RED)
            raise typer.Exit(1)
        page_content = file.read_text()
        log(f"Read {len(page_content)} chars from {file}")
    elif content:
        page_content = content
    else:
        # Default content
        page_content = f"# {title}\n\nThis page was created via the Forge CLI."

    log(f"Creating wiki page: {title}")
    log(f"Content length: {len(page_content)} chars")

    # Encode content as base64
    content_b64 = encode_content(page_content)

    wiki_options = CreateWikiPageOptions(
        title=title,
        content_base64=content_b64,
        message=message or f"Create page: {title}",
    )

    log(f"Commit message: {wiki_options.message}")

    try:
        repo_api = get_repository_api()
        wiki_page = repo_api.repo_create_wiki_page(
            owner=owner,
            repo=repo,
            body=wiki_options
        )
        page_dict = wiki_page.to_dict()

        if json_output:
            typer.echo(json.dumps(page_dict, indent=2, default=str))
        else:
            typer.secho("✅ Wiki page created successfully!", fg=typer.colors.GREEN)
            typer.echo(f"\nTitle: {page_dict.get('title')}")
            typer.echo(f"URL: {page_dict.get('html_url')}")
            if page_dict.get('last_commit'):
                commit = page_dict['last_commit']
                typer.echo(f"Commit: {commit.get('sha', 'N/A')[:8]}...")

    except ApiException as e:
        if e.status == 409:
            typer.secho(f"❌ Wiki page '{title}' already exists", fg=typer.colors.RED)
            raise typer.Exit(1)
        handle_api_error(e, "create wiki page")


@app.command()
def get(
    owner: Annotated[str, typer.Argument(help="Repository owner")],
    repo: Annotated[str, typer.Argument(help="Repository name")],
    title: Annotated[str, typer.Argument(help="Wiki page title")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    raw: Annotated[bool, typer.Option("--raw", help="Output raw content only")] = False,
):
    """
    Get a wiki page.

    Example:
        python main.py wiki get owner repo "Home"
        python main.py wiki get owner repo "Setup" --raw > setup.md
    """
    try:
        repo_api = get_repository_api()
        wiki_page = repo_api.repo_get_wiki_page(owner=owner, repo=repo, page_name=title)
        page_dict = wiki_page.to_dict()

        if raw:
            # Output just the content (decoded)
            if page_dict.get('content_base64'):
                typer.echo(decode_content(page_dict['content_base64']))
            else:
                typer.echo("")
        elif json_output:
            typer.echo(json.dumps(page_dict, indent=2, default=str))
        else:
            typer.echo(f"\n📄 Wiki: {page_dict.get('title')}\n")
            typer.echo(f"URL: {page_dict.get('html_url')}")
            typer.echo(f"Sub-URL: {page_dict.get('sub_url')}")

            if page_dict.get('last_commit'):
                commit = page_dict['last_commit']
                typer.echo(f"\nLast commit: {commit.get('sha', 'N/A')[:8]}...")
                if commit.get('committer'):
                    typer.echo(f"Author: {commit['committer'].get('name', 'N/A')}")

            if page_dict.get('content_base64'):
                content = decode_content(page_dict['content_base64'])
                typer.echo(f"\n--- Content ({len(content)} chars) ---\n")
                # Show first 500 chars
                if len(content) > 500:
                    typer.echo(content[:500])
                    typer.echo(f"\n... ({len(content) - 500} more chars, use --raw for full content)")
                else:
                    typer.echo(content)

    except ApiException as e:
        if e.status == 404:
            typer.secho(f"❌ Wiki page '{title}' not found", fg=typer.colors.RED)
            raise typer.Exit(1)
        handle_api_error(e, "get wiki page")


@app.command("list")
def list_pages(
    owner: Annotated[str, typer.Argument(help="Repository owner")],
    repo: Annotated[str, typer.Argument(help="Repository name")],
    limit: Annotated[int, typer.Option(help="Max pages to return")] = 50,
    page: Annotated[int, typer.Option(help="Page number")] = 1,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """
    List all wiki pages in a repository.

    Example:
        python main.py wiki list owner repo
    """
    try:
        repo_api = get_repository_api()
        wiki_pages = repo_api.repo_get_wiki_pages(owner=owner, repo=repo, limit=limit, page=page)

        if json_output:
            pages_list = [p.to_dict() for p in wiki_pages]
            typer.echo(json.dumps(pages_list, indent=2, default=str))
        else:
            typer.echo(f"\n📚 Wiki pages in {owner}/{repo}:\n")

            if not wiki_pages:
                typer.secho("  No wiki pages found", fg=typer.colors.YELLOW)
                typer.echo("  Create one with: wiki create owner repo \"Home\"")
            else:
                for wp in wiki_pages:
                    p = wp.to_dict()
                    typer.echo(f"  • {p.get('title')}")
                    if p.get('last_commit'):
                        commit = p['last_commit']
                        sha = commit.get('sha', '')[:8]
                        typer.echo(f"    Last commit: {sha}...")
                    typer.echo()

                typer.echo(f"  Showing {len(wiki_pages)} pages")

    except ApiException as e:
        if e.status == 404:
            typer.secho(f"❌ Repository '{owner}/{repo}' not found or wiki disabled", fg=typer.colors.RED)
            raise typer.Exit(1)
        handle_api_error(e, "list wiki pages")


@app.command()
def edit(
    owner: Annotated[str, typer.Argument(help="Repository owner")],
    repo: Annotated[str, typer.Argument(help="Repository name")],
    title: Annotated[str, typer.Argument(help="Wiki page title")],
    content: Annotated[str, typer.Option("--content", "-c", help="New page content")] = None,
    file: Annotated[Path, typer.Option("--file", "-f", help="Read content from file")] = None,
    message: Annotated[str, typer.Option("--message", "-m", help="Commit message")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """
    Edit an existing wiki page.

    Example:
        python main.py wiki edit owner repo "Home" --content "# Updated content"
        python main.py wiki edit owner repo "Setup" --file ./docs/setup.md -m "Update setup docs"
    """
    # Get content from file or option
    if file:
        if not file.exists():
            typer.secho(f"❌ File not found: {file}", fg=typer.colors.RED)
            raise typer.Exit(1)
        page_content = file.read_text()
    elif content:
        page_content = content
    else:
        typer.secho("❌ Must provide --content or --file", fg=typer.colors.RED)
        raise typer.Exit(1)

    # Encode content as base64
    content_b64 = encode_content(page_content)

    from openapi_client.models.create_wiki_page_options import CreateWikiPageOptions
    wiki_options = CreateWikiPageOptions(
        title=title,
        content_base64=content_b64,
        message=message or f"Update page: {title}",
    )

    try:
        repo_api = get_repository_api()
        wiki_page = repo_api.repo_edit_wiki_page(
            owner=owner,
            repo=repo,
            page_name=title,
            body=wiki_options
        )
        page_dict = wiki_page.to_dict()

        if json_output:
            typer.echo(json.dumps(page_dict, indent=2, default=str))
        else:
            typer.secho("✅ Wiki page updated!", fg=typer.colors.GREEN)
            typer.echo(f"\nTitle: {page_dict.get('title')}")
            typer.echo(f"URL: {page_dict.get('html_url')}")

    except ApiException as e:
        if e.status == 404:
            typer.secho(f"❌ Wiki page '{title}' not found", fg=typer.colors.RED)
            raise typer.Exit(1)
        handle_api_error(e, "edit wiki page")


@app.command()
def delete(
    owner: Annotated[str, typer.Argument(help="Repository owner")],
    repo: Annotated[str, typer.Argument(help="Repository name")],
    title: Annotated[str, typer.Argument(help="Wiki page title")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False,
):
    """
    Delete a wiki page.

    Example:
        python main.py wiki delete owner repo "Old Page"
    """
    if not force:
        typer.secho(f"⚠️  This will delete wiki page '{title}'", fg=typer.colors.YELLOW)
        if not typer.confirm("Are you sure?"):
            typer.echo("Cancelled.")
            raise typer.Exit(0)

    try:
        repo_api = get_repository_api()
        repo_api.repo_delete_wiki_page(owner=owner, repo=repo, page_name=title)
        typer.secho(f"✅ Wiki page '{title}' deleted", fg=typer.colors.GREEN)

    except ApiException as e:
        if e.status == 404:
            typer.secho(f"❌ Wiki page '{title}' not found", fg=typer.colors.RED)
            raise typer.Exit(1)
        handle_api_error(e, "delete wiki page")


@app.command()
def history(
    owner: Annotated[str, typer.Argument(help="Repository owner")],
    repo: Annotated[str, typer.Argument(help="Repository name")],
    title: Annotated[str, typer.Argument(help="Wiki page title")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """
    Show revision history of a wiki page.

    Example:
        python main.py wiki history owner repo "Home"
    """
    try:
        repo_api = get_repository_api()
        revisions = repo_api.repo_get_wiki_page_revisions(owner=owner, repo=repo, page_name=title)
        rev_dict = revisions.to_dict()

        if json_output:
            typer.echo(json.dumps(rev_dict, indent=2, default=str))
        else:
            commits = rev_dict.get('commits', [])
            typer.echo(f"\n📜 Revision history for '{title}':\n")

            if not commits:
                typer.secho("  No revisions found", fg=typer.colors.YELLOW)
            else:
                for commit in commits:
                    sha = commit.get('sha', 'N/A')[:8]
                    message = commit.get('message', 'No message')
                    author = commit.get('committer', {}).get('name', 'Unknown')
                    date = commit.get('committer', {}).get('date', 'N/A')

                    typer.echo(f"  • {sha}  {message}")
                    typer.echo(f"    by {author} at {date}")
                    typer.echo()

                typer.echo(f"  Total: {rev_dict.get('count', len(commits))} revisions")

    except ApiException as e:
        if e.status == 404:
            typer.secho(f"❌ Wiki page '{title}' not found", fg=typer.colors.RED)
            raise typer.Exit(1)
        handle_api_error(e, "get wiki history")


# =============================================================================
# Direct execution
# =============================================================================

if __name__ == "__main__":
    app()
