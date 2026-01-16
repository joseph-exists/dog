"""
Issue Management Commands

Commands for creating and managing Forgejo issues.

Note: Path setup is handled by main.py - no sys.path manipulation needed here.
"""

import json
from typing import Annotated

import typer

from openapi_client import CreateIssueCommentOption, CreateIssueOption, EditIssueOption, ApiException


from app.test_scripts.forge_admin.typer_forge.forge_client import get_issue_api

app = typer.Typer(help="Issue management commands")


# =============================================================================
# Helper Functions
# =============================================================================

def handle_api_error(e: ApiException, context: str = "operation"):
    """Standard error handling for API exceptions."""
    typer.secho(f"❌ Failed to {context}: {e.status} - {e.reason}", fg=typer.colors.RED)
    if e.body:
        typer.echo(f"   {e.body[:300]}")
    raise typer.Exit(1)


def format_issue(issue: dict, verbose: bool = False) -> None:
    """Format and print issue info."""
    state_icon = "🟢" if issue.get('state') == 'open' else "🔴"

    typer.echo(f"  {state_icon} #{issue.get('number')} {issue.get('title')}")
    typer.echo(f"     State: {issue.get('state')} | Comments: {issue.get('comments', 0)}")

    if issue.get('assignee'):
        typer.echo(f"     Assignee: {issue['assignee'].get('login', 'N/A')}")

    if verbose and issue.get('body'):
        body_preview = issue['body'][:100].replace('\n', ' ')
        typer.echo(f"     Body: {body_preview}...")

    if issue.get('labels'):
        labels = [l.get('name') for l in issue['labels']]
        typer.echo(f"     Labels: {', '.join(labels)}")

    typer.echo()


# =============================================================================
# Issue Commands
# =============================================================================

@app.command()
def create(
    owner: Annotated[str, typer.Argument(help="Repository owner")],
    repo: Annotated[str, typer.Argument(help="Repository name")],
    title: Annotated[str, typer.Argument(help="Issue title")],
    body: Annotated[str, typer.Option("--body", "-b", help="Issue body/description")] = "",
    assignee: Annotated[str, typer.Option("--assignee", "-a", help="Assign to user")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose output")] = False,
):
    """
    Create a new issue.

    Example:
        python main.py issues create myuser myrepo "Bug: something broke"
        python main.py issues create myuser myrepo "Feature request" --body "Please add..."
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    log(f"Creating issue in {owner}/{repo}")

    issue_options = CreateIssueOption(
        title=title,
        body=body or None,
        assignees=[assignee] if assignee else None,
    )

    log(f"Payload: {issue_options.to_dict()}")

    try:
        issue_api = get_issue_api()
        issue = issue_api.issue_create_issue(owner=owner, repo=repo, body=issue_options)
        issue_dict = issue.to_dict()

        if json_output:
            typer.echo(json.dumps(issue_dict, indent=2, default=str))
        else:
            typer.secho("✅ Issue created successfully!", fg=typer.colors.GREEN)
            typer.echo(f"\n#{issue_dict.get('number')}: {issue_dict.get('title')}")
            typer.echo(f"URL: {issue_dict.get('html_url')}")
            typer.echo(f"State: {issue_dict.get('state')}")

    except ApiException as e:
        if e.status == 404:
            typer.secho(f"❌ Repository '{owner}/{repo}' not found", fg=typer.colors.RED)
            raise typer.Exit(1)
        handle_api_error(e, "create issue")


@app.command()
def get(
    owner: Annotated[str, typer.Argument(help="Repository owner")],
    repo: Annotated[str, typer.Argument(help="Repository name")],
    number: Annotated[int, typer.Argument(help="Issue number")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """
    Get issue details.

    Example:
        python main.py issues get myuser myrepo 1
    """
    try:
        issue_api = get_issue_api()
        issue = issue_api.issue_get_issue(owner=owner, repo=repo, index=number)
        issue_dict = issue.to_dict()

        if json_output:
            typer.echo(json.dumps(issue_dict, indent=2, default=str))
        else:
            state_icon = "🟢" if issue_dict.get('state') == 'open' else "🔴"

            typer.echo(f"\n{state_icon} #{issue_dict.get('number')}: {issue_dict.get('title')}\n")
            typer.echo(f"State: {issue_dict.get('state')}")
            typer.echo(f"Author: {issue_dict.get('user', {}).get('login', 'N/A')}")

            if issue_dict.get('assignee'):
                typer.echo(f"Assignee: {issue_dict['assignee'].get('login')}")

            typer.echo(f"Comments: {issue_dict.get('comments', 0)}")
            typer.echo(f"Created: {issue_dict.get('created_at')}")
            typer.echo(f"URL: {issue_dict.get('html_url')}")

            if issue_dict.get('body'):
                typer.echo(f"\n--- Body ---\n{issue_dict['body']}\n")

    except ApiException as e:
        if e.status == 404:
            typer.secho(f"❌ Issue #{number} not found in '{owner}/{repo}'", fg=typer.colors.RED)
            raise typer.Exit(1)
        handle_api_error(e, "get issue")


@app.command("list")
def list_issues(
    owner: Annotated[str, typer.Argument(help="Repository owner")],
    repo: Annotated[str, typer.Argument(help="Repository name")],
    state: Annotated[str, typer.Option(help="Filter by state: open, closed, all")] = "open",
    limit: Annotated[int, typer.Option(help="Max issues to return")] = 20,
    page: Annotated[int, typer.Option(help="Page number")] = 1,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show more details")] = False,
):
    """
    List issues in a repository.

    Example:
        python main.py issues list myuser myrepo
        python main.py issues list myuser myrepo --state closed
    """
    try:
        issue_api = get_issue_api()
        issues = issue_api.issue_list_issues(
            owner=owner,
            repo=repo,
            state=state,
            limit=limit,
            page=page
        )

        if json_output:
            issues_list = [i.to_dict() for i in issues]
            typer.echo(json.dumps(issues_list, indent=2, default=str))
        else:
            typer.echo(f"\n📋 Issues in {owner}/{repo} ({state}, page {page}):\n")

            if not issues:
                typer.secho("  No issues found", fg=typer.colors.YELLOW)
            else:
                for issue in issues:
                    format_issue(issue.to_dict(), verbose=verbose)

                typer.echo(f"  Showing {len(issues)} issues")

    except ApiException as e:
        if e.status == 404:
            typer.secho(f"❌ Repository '{owner}/{repo}' not found", fg=typer.colors.RED)
            raise typer.Exit(1)
        handle_api_error(e, "list issues")


@app.command()
def close(
    owner: Annotated[str, typer.Argument(help="Repository owner")],
    repo: Annotated[str, typer.Argument(help="Repository name")],
    number: Annotated[int, typer.Argument(help="Issue number")],
):
    """
    Close an issue.

    Example:
        python main.py issues close myuser myrepo 1
    """
    try:
        issue_api = get_issue_api()
        edit_options = EditIssueOption(state="closed")
        issue = issue_api.issue_edit_issue(owner=owner, repo=repo, index=number, body=edit_options)

        typer.secho(f"✅ Issue #{number} closed", fg=typer.colors.GREEN)

    except ApiException as e:
        if e.status == 404:
            typer.secho(f"❌ Issue #{number} not found", fg=typer.colors.RED)
            raise typer.Exit(1)
        handle_api_error(e, "close issue")


@app.command()
def reopen(
    owner: Annotated[str, typer.Argument(help="Repository owner")],
    repo: Annotated[str, typer.Argument(help="Repository name")],
    number: Annotated[int, typer.Argument(help="Issue number")],
):
    """
    Reopen a closed issue.

    Example:
        python main.py issues reopen myuser myrepo 1
    """
    try:
        issue_api = get_issue_api()
        edit_options = EditIssueOption(state="open")
        issue = issue_api.issue_edit_issue(owner=owner, repo=repo, index=number, body=edit_options)

        typer.secho(f"✅ Issue #{number} reopened", fg=typer.colors.GREEN)

    except ApiException as e:
        if e.status == 404:
            typer.secho(f"❌ Issue #{number} not found", fg=typer.colors.RED)
            raise typer.Exit(1)
        handle_api_error(e, "reopen issue")


@app.command()
def comment(
    owner: Annotated[str, typer.Argument(help="Repository owner")],
    repo: Annotated[str, typer.Argument(help="Repository name")],
    number: Annotated[int, typer.Argument(help="Issue number")],
    body: Annotated[str, typer.Argument(help="Comment text")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """
    Add a comment to an issue.

    Example:
        python main.py issues comment myuser myrepo 1 "Thanks for reporting!"
    """
    try:
        issue_api = get_issue_api()
        comment_options = CreateIssueCommentOption(body=body)
        comment = issue_api.issue_create_comment(
            owner=owner,
            repo=repo,
            index=number,
            body=comment_options
        )
        comment_dict = comment.to_dict()

        if json_output:
            typer.echo(json.dumps(comment_dict, indent=2, default=str))
        else:
            typer.secho(f"✅ Comment added to issue #{number}", fg=typer.colors.GREEN)
            typer.echo(f"Comment ID: {comment_dict.get('id')}")

    except ApiException as e:
        if e.status == 404:
            typer.secho(f"❌ Issue #{number} not found", fg=typer.colors.RED)
            raise typer.Exit(1)
        handle_api_error(e, "add comment")


@app.command()
def comments(
    owner: Annotated[str, typer.Argument(help="Repository owner")],
    repo: Annotated[str, typer.Argument(help="Repository name")],
    number: Annotated[int, typer.Argument(help="Issue number")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """
    List comments on an issue.

    Example:
        python main.py issues comments myuser myrepo 1
    """
    try:
        issue_api = get_issue_api()
        comments = issue_api.issue_get_comments(owner=owner, repo=repo, index=number)

        if json_output:
            comments_list = [c.to_dict() for c in comments]
            typer.echo(json.dumps(comments_list, indent=2, default=str))
        else:
            typer.echo(f"\n💬 Comments on #{number}:\n")

            if not comments:
                typer.secho("  No comments yet", fg=typer.colors.YELLOW)
            else:
                for comment in comments:
                    c = comment.to_dict()
                    user = c.get('user', {}).get('login', 'Unknown')
                    created = c.get('created_at', 'N/A')
                    body = c.get('body', '')[:200]

                    typer.echo(f"  📝 {user} ({created}):")
                    typer.echo(f"     {body}")
                    if len(c.get('body', '')) > 200:
                        typer.echo("     ...")
                    typer.echo()

    except ApiException as e:
        if e.status == 404:
            typer.secho(f"❌ Issue #{number} not found", fg=typer.colors.RED)
            raise typer.Exit(1)
        handle_api_error(e, "list comments")


# =============================================================================
# Direct execution
# =============================================================================

if __name__ == "__main__":
    app()
