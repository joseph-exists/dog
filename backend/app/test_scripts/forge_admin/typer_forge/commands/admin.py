"""
Admin Commands

Administrative operations for Forgejo - listing users, orgs, etc.

Note: Path setup is handled by main.py - no sys.path manipulation needed here.
"""

import json
from typing import Annotated

import typer
from openapi_client import ApiException

# Forge client and SDK imports (paths set up by main.py)
from app.test_scripts.forge_admin.typer_forge.forge_client import get_admin_api

app = typer.Typer(help="Admin operations")


# =============================================================================
# Helper Functions
# =============================================================================

def handle_api_error(e: ApiException, context: str = "operation"):
    """Standard error handling for API exceptions."""
    typer.secho(f"❌ Failed to {context}: {e.status} - {e.reason}", fg=typer.colors.RED)
    if e.body:
        typer.echo(f"   {e.body[:300]}")
    raise typer.Exit(1)


# =============================================================================
# Admin Commands
# =============================================================================

@app.command("list-users")
def list_users(
    limit: Annotated[int, typer.Option(help="Max users to return")] = 20,
    page: Annotated[int, typer.Option(help="Page number")] = 1,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """
    List all users (admin only).

    Example:
        python main.py admin list-users
        python main.py admin list-users --limit 50 --json
    """
    try:
        admin = get_admin_api()
        users = admin.admin_get_all_users(limit=limit, page=page)

        if json_output:
            users_list = [u.to_dict() for u in users]
            typer.echo(json.dumps(users_list, indent=2, default=str))
        else:
            typer.echo(f"\n👥 Users (page {page}, limit {limit}):\n")

            if not users:
                typer.secho("  No users found", fg=typer.colors.YELLOW)
            else:
                for user in users:
                    admin_badge = " [Admin]" if user.is_admin else ""
                    typer.echo(f"  • {user.login}{admin_badge}")
                    typer.echo(f"    Email: {user.email or 'N/A'}")
                    typer.echo(f"    ID: {user.id}")
                    typer.echo()

                typer.echo(f"  Showing {len(users)} users")

    except ApiException as e:
        if e.status == 403:
            typer.secho("❌ Permission denied - token needs read:admin scope", fg=typer.colors.RED)
            raise typer.Exit(1)
        handle_api_error(e, "list users")


@app.command("list-orgs")
def list_orgs(
    limit: Annotated[int, typer.Option(help="Max orgs to return")] = 20,
    page: Annotated[int, typer.Option(help="Page number")] = 1,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """
    List all organizations (admin only).

    Example:
        python main.py admin list-orgs
    """
    try:
        admin = get_admin_api()
        orgs = admin.admin_get_all_orgs(limit=limit, page=page)

        if json_output:
            orgs_list = [o.to_dict() for o in orgs]
            typer.echo(json.dumps(orgs_list, indent=2, default=str))
        else:
            typer.echo(f"\n🏢 Organizations (page {page}):\n")

            if not orgs:
                typer.secho("  No organizations found", fg=typer.colors.YELLOW)
            else:
                for org in orgs:
                    typer.echo(f"  • {org.name}")
                    typer.echo(f"    Full Name: {org.full_name or 'N/A'}")
                    typer.echo(f"    ID: {org.id}")
                    typer.echo()

    except ApiException as e:
        if e.status == 403:
            typer.secho("❌ Permission denied - token needs read:admin scope", fg=typer.colors.RED)
            raise typer.Exit(1)
        handle_api_error(e, "list organizations")


@app.command("list-emails")
def list_emails(
    limit: Annotated[int, typer.Option(help="Max emails to return")] = 20,
    page: Annotated[int, typer.Option(help="Page number")] = 1,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """
    List all registered emails (admin only).

    Example:
        python main.py admin list-emails
    """
    try:
        admin = get_admin_api()
        emails = admin.admin_get_all_emails(limit=limit, page=page)

        if json_output:
            emails_list = [e.to_dict() for e in emails]
            typer.echo(json.dumps(emails_list, indent=2, default=str))
        else:
            typer.echo(f"\n📧 Registered Emails (page {page}):\n")

            if not emails:
                typer.secho("  No emails found", fg=typer.colors.YELLOW)
            else:
                for email in emails:
                    verified = "✓" if email.verified else "○"
                    primary = " [Primary]" if email.primary else ""
                    typer.echo(f"  {verified} {email.email}{primary}")
                    typer.echo(f"    User ID: {email.user_id}")
                    typer.echo()

    except ApiException as e:
        if e.status == 403:
            typer.secho("❌ Permission denied - token needs read:admin scope", fg=typer.colors.RED)
            raise typer.Exit(1)
        handle_api_error(e, "list emails")


@app.command("cron")
def list_cron(
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """
    List cron tasks (admin only).

    Example:
        python main.py admin cron
    """
    try:
        admin = get_admin_api()
        cron_tasks = admin.admin_cron_list()

        if json_output:
            tasks_list = [t.to_dict() for t in cron_tasks]
            typer.echo(json.dumps(tasks_list, indent=2, default=str))
        else:
            typer.echo(f"\n⏰ Cron Tasks:\n")

            if not cron_tasks:
                typer.secho("  No cron tasks found", fg=typer.colors.YELLOW)
            else:
                for task in cron_tasks:
                    typer.echo(f"  • {task.name}")
                    typer.echo(f"    Schedule: {task.schedule}")
                    typer.echo(f"    Next: {task.next}")
                    typer.echo(f"    Prev: {task.prev}")
                    typer.echo()

    except ApiException as e:
        if e.status == 403:
            typer.secho("❌ Permission denied - token needs read:admin scope", fg=typer.colors.RED)
            raise typer.Exit(1)
        handle_api_error(e, "list cron tasks")


# =============================================================================
# Direct execution
# =============================================================================

if __name__ == "__main__":
    app()
