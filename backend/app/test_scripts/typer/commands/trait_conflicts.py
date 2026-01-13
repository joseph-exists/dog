"""
Trait Conflicts Command Module

Commands for managing trait conflict groups for Carroll logic implementation.
Supports contradictory, contrary, and subcontrary conflict types.

Usage:
    python main.py conflicts create-group "Mortality" --type contradictory --reason "Cannot be both mortal and immortal"
    python main.py conflicts list-groups
    python main.py conflicts add-member GROUP_ID TRAIT_ID
    python main.py conflicts check-persona PERSONA_ID --trait TRAIT_ID
"""
import typer
import json
from typing import Annotated
from auth_helper import get_authenticated_session

# Create typer app for this command group
app = typer.Typer(help="Trait conflict group management for logical contradictions")

# Configuration
BASE_URL = "http://localhost:8000/api/v1"


# ============================================================================
# Conflict Group Commands
# ============================================================================

@app.command("create-group")
def create_group(
    name: Annotated[str, typer.Argument(help="Name of the conflict group")],
    conflict_type: Annotated[str, typer.Option(
        "--type", "-t",
        help="Conflict type: contradictory, contrary, or subcontrary"
    )] = "contradictory",
    description: Annotated[str, typer.Option("--desc", "-d", help="Description")] = "",
    reason: Annotated[str, typer.Option("--reason", "-r", help="Explanation of why these traits conflict")] = "",
    trait_ids: Annotated[str, typer.Option(
        "--traits",
        help="Comma-separated trait IDs to add as initial members"
    )] = "",
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False
):
    """
    Create a new trait conflict group.

    Conflict types:
    - contradictory: Exactly one must be true (e.g., Mortal/Immortal)
    - contrary: At most one can be true (e.g., Hot/Warm/Cold)
    - subcontrary: At least one must be true

    Examples:
        python main.py conflicts create-group "Mortality" --type contradictory \\
            --reason "A being cannot be both mortal and immortal"

        python main.py conflicts create-group "Temperature" --type contrary \\
            --desc "Temperature states" --traits "trait1,trait2,trait3"
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    # Validate conflict type
    valid_types = ["contradictory", "contrary", "subcontrary"]
    if conflict_type not in valid_types:
        typer.secho(f"❌ Invalid conflict type: {conflict_type}", fg=typer.colors.RED, err=True)
        typer.echo(f"   Valid types: {', '.join(valid_types)}")
        raise typer.Exit(1)

    log(f"Creating conflict group: {name}")

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    payload = {
        "name": name,
        "conflict_type": conflict_type,
    }
    if description:
        payload["description"] = description
    if reason:
        payload["reason"] = reason
    if trait_ids:
        payload["trait_ids"] = [tid.strip() for tid in trait_ids.split(",")]

    log(f"POST {BASE_URL}/trait-conflicts")
    log(f"Payload: {json.dumps(payload, indent=2)}")

    response = session.post(f"{BASE_URL}/trait-conflicts", json=payload)

    log(f"Response status: {response.status_code}")
    log(f"Response: {response.text[:500]}")

    if response.status_code in [200, 201]:
        group = response.json()
        typer.secho("✅ Conflict group created successfully!", fg=typer.colors.GREEN)
        typer.echo(f"ID: {group['id']}")
        typer.echo(f"Name: {group['name']}")
        typer.echo(f"Type: {group['conflict_type']}")
        if group.get('reason'):
            typer.echo(f"Reason: {group['reason']}")
    else:
        typer.secho(f"❌ Failed to create conflict group", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command("list-groups")
def list_groups(
    limit: Annotated[int, typer.Option(help="Max groups to list")] = 20,
    offset: Annotated[int, typer.Option(help="Pagination offset")] = 0,
    conflict_type: Annotated[str, typer.Option(
        "--type", "-t",
        help="Filter by type: contradictory, contrary, subcontrary"
    )] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False
):
    """
    List all trait conflict groups.

    Examples:
        python main.py conflicts list-groups
        python main.py conflicts list-groups --type contradictory
        python main.py conflicts list-groups --json
    """

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    params = {"limit": limit, "offset": offset}
    if conflict_type:
        params["conflict_type"] = conflict_type

    response = session.get(f"{BASE_URL}/trait-conflicts", params=params)

    if response.status_code == 200:
        data = response.json()
        groups = data.get("data", [])
        total = data.get("count", 0)

        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            type_filter = f" (type: {conflict_type})" if conflict_type else ""
            typer.echo(f"\n⚡ Conflict Groups ({len(groups)} of {total}){type_filter}:\n")

            if not groups:
                typer.secho("  No conflict groups found", fg=typer.colors.YELLOW)
            else:
                for group in groups:
                    type_emoji = {
                        "contradictory": "⊕",
                        "contrary": "⊗",
                        "subcontrary": "⊙"
                    }.get(group.get('conflict_type', ''), "•")

                    typer.echo(f"  {type_emoji} {group['name']}")
                    typer.echo(f"    ID: {group['id']}")
                    typer.echo(f"    Type: {group.get('conflict_type', 'N/A')}")
                    if group.get('description'):
                        typer.echo(f"    Desc: {group['description'][:60]}...")
                    if group.get('reason'):
                        typer.echo(f"    Reason: {group['reason'][:60]}...")
                    typer.echo()
    else:
        typer.secho(f"❌ Failed to list conflict groups", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command("get-group")
def get_group(
    group_id: Annotated[str, typer.Argument(help="Conflict group ID")],
    json_output: Annotated[bool, typer.Option("--json")] = False
):
    """
    Get details of a specific conflict group.

    Example:
        python main.py conflicts get-group abc123
    """

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(f"{BASE_URL}/trait-conflicts/{group_id}")

    if response.status_code == 200:
        group = response.json()

        if json_output:
            typer.echo(json.dumps(group, indent=2))
        else:
            typer.echo(f"\n⚡ Conflict Group Details:\n")
            typer.echo(f"  ID: {group['id']}")
            typer.echo(f"  Name: {group['name']}")
            typer.echo(f"  Type: {group.get('conflict_type', 'N/A')}")
            if group.get('description'):
                typer.echo(f"  Description: {group['description']}")
            if group.get('reason'):
                typer.echo(f"  Reason: {group['reason']}")
            typer.echo(f"  Created: {group.get('created_at', 'N/A')}")
            if group.get('updated_at'):
                typer.echo(f"  Updated: {group['updated_at']}")
    elif response.status_code == 404:
        typer.secho(f"❌ Conflict group not found: {group_id}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    else:
        typer.secho("❌ Failed to get conflict group", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command("update-group")
def update_group(
    group_id: Annotated[str, typer.Argument(help="Conflict group ID")],
    name: Annotated[str, typer.Option("--name", "-n", help="New name")] = None,
    conflict_type: Annotated[str, typer.Option("--type", "-t", help="New conflict type")] = None,
    description: Annotated[str, typer.Option("--desc", "-d", help="New description")] = None,
    reason: Annotated[str, typer.Option("--reason", "-r", help="New reason")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False
):
    """
    Update a conflict group's properties.

    Example:
        python main.py conflicts update-group abc123 --name "New Name" --reason "Updated reason"
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    # Build update payload with only provided fields
    payload = {}
    if name is not None:
        payload["name"] = name
    if conflict_type is not None:
        valid_types = ["contradictory", "contrary", "subcontrary"]
        if conflict_type not in valid_types:
            typer.secho(f"❌ Invalid conflict type: {conflict_type}", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)
        payload["conflict_type"] = conflict_type
    if description is not None:
        payload["description"] = description
    if reason is not None:
        payload["reason"] = reason

    if not payload:
        typer.secho("⚠️  No updates provided", fg=typer.colors.YELLOW)
        raise typer.Exit(0)

    log(f"Updating group {group_id}")
    log(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.put(f"{BASE_URL}/trait-conflicts/{group_id}", json=payload)

    if response.status_code == 200:
        group = response.json()
        typer.secho("✅ Conflict group updated successfully!", fg=typer.colors.GREEN)
        typer.echo(f"Name: {group['name']}")
        typer.echo(f"Type: {group.get('conflict_type', 'N/A')}")
    elif response.status_code == 404:
        typer.secho(f"❌ Conflict group not found: {group_id}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    else:
        typer.secho(f"❌ Failed to update conflict group", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command("delete-group")
def delete_group(
    group_id: Annotated[str, typer.Argument(help="Conflict group ID")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False
):
    """
    Delete a conflict group and all its members.

    Example:
        python main.py conflicts delete-group abc123
        python main.py conflicts delete-group abc123 --force
    """

    if not force:
        typer.secho(f"⚠️  This will delete conflict group {group_id} and all its members", fg=typer.colors.YELLOW)
        if not typer.confirm("Are you sure?"):
            typer.echo("Cancelled.")
            raise typer.Exit(0)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.delete(f"{BASE_URL}/trait-conflicts/{group_id}")

    if response.status_code in [200, 204]:
        typer.secho("✅ Conflict group deleted successfully", fg=typer.colors.GREEN)
    elif response.status_code == 404:
        typer.secho(f"❌ Conflict group not found: {group_id}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    else:
        typer.secho(f"❌ Failed to delete conflict group", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# ============================================================================
# Member Commands
# ============================================================================

@app.command("list-members")
def list_members(
    group_id: Annotated[str, typer.Argument(help="Conflict group ID")],
    json_output: Annotated[bool, typer.Option("--json")] = False
):
    """
    List all trait members of a conflict group.

    Example:
        python main.py conflicts list-members abc123
    """

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(f"{BASE_URL}/trait-conflicts/{group_id}/members")

    if response.status_code == 200:
        data = response.json()
        members = data.get("data", [])
        count = data.get("count", len(members))

        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.echo(f"\n🔗 Group Members ({count}):\n")

            if not members:
                typer.secho("  No members in this group", fg=typer.colors.YELLOW)
            else:
                for member in members:
                    typer.echo(f"  • Trait ID: {member.get('trait_id', 'N/A')}")
                    typer.echo(f"    Member ID: {member.get('id', 'N/A')}")
                    typer.echo(f"    Added: {member.get('created_at', 'N/A')}")
                    typer.echo()
    elif response.status_code == 404:
        typer.secho(f"❌ Conflict group not found: {group_id}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    else:
        typer.secho(f"❌ Failed to list members", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command("add-member")
def add_member(
    group_id: Annotated[str, typer.Argument(help="Conflict group ID")],
    trait_id: Annotated[str, typer.Argument(help="Trait ID to add")],
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False
):
    """
    Add a trait to a conflict group.

    Example:
        python main.py conflicts add-member group123 trait456
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    log(f"Adding trait {trait_id} to group {group_id}")

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    payload = {"trait_id": trait_id}

    response = session.post(f"{BASE_URL}/trait-conflicts/{group_id}/members", json=payload)

    log(f"Response status: {response.status_code}")

    if response.status_code in [200, 201]:
        member = response.json()
        typer.secho("✅ Trait added to conflict group!", fg=typer.colors.GREEN)
        typer.echo(f"Member ID: {member.get('id', 'N/A')}")
        typer.echo(f"Trait ID: {member.get('trait_id', 'N/A')}")
    elif response.status_code == 400:
        typer.secho(f"❌ Cannot add trait", fg=typer.colors.RED, err=True)
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)
    elif response.status_code == 404:
        typer.secho(f"❌ Group or trait not found", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    else:
        typer.secho(f"❌ Failed to add trait to group", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command("remove-member")
def remove_member(
    group_id: Annotated[str, typer.Argument(help="Conflict group ID")],
    trait_id: Annotated[str, typer.Argument(help="Trait ID to remove")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False
):
    """
    Remove a trait from a conflict group.

    Example:
        python main.py conflicts remove-member group123 trait456
    """

    if not force:
        typer.secho(f"⚠️  Remove trait {trait_id} from group {group_id}?", fg=typer.colors.YELLOW)
        if not typer.confirm("Confirm?"):
            typer.echo("Cancelled.")
            raise typer.Exit(0)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.delete(f"{BASE_URL}/trait-conflicts/{group_id}/members/{trait_id}")

    if response.status_code in [200, 204]:
        typer.secho("✅ Trait removed from conflict group", fg=typer.colors.GREEN)
    elif response.status_code == 404:
        typer.secho(f"❌ Trait not found in group", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    else:
        typer.secho(f"❌ Failed to remove trait", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# ============================================================================
# Conflict Checking Commands
# ============================================================================

@app.command("check-persona")
def check_persona(
    persona_id: Annotated[str, typer.Argument(help="Persona ID to check")],
    trait_id: Annotated[str, typer.Option("--trait", "-t", help="Trait ID to check for conflicts")],
    json_output: Annotated[bool, typer.Option("--json")] = False
):
    """
    Check if adding a trait to a persona would create a conflict.

    Example:
        python main.py conflicts check-persona persona123 --trait trait456
    """

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(
        f"{BASE_URL}/trait-conflicts/check/persona/{persona_id}",
        params={"trait_id": trait_id}
    )

    if response.status_code == 200:
        result = response.json()

        if json_output:
            typer.echo(json.dumps(result, indent=2))
        else:
            has_conflicts = result.get("has_conflicts", False)
            conflicts = result.get("conflicts", [])

            if has_conflicts:
                typer.secho(f"\n❌ CONFLICT DETECTED!", fg=typer.colors.RED)
                typer.echo(f"\nAdding this trait would create {len(conflicts)} conflict(s):\n")

                for conflict in conflicts:
                    typer.echo(f"  ⚡ {conflict.get('group_name', 'Unknown')}")
                    typer.echo(f"    Type: {conflict.get('conflict_type', 'N/A')}")
                    if conflict.get('reason'):
                        typer.echo(f"    Reason: {conflict['reason']}")
                    typer.echo(f"    Conflicting traits: {', '.join(conflict.get('conflicting_trait_ids', []))}")
                    typer.echo()

                raise typer.Exit(1)
            else:
                typer.secho(f"\n✅ No conflicts - safe to add trait", fg=typer.colors.GREEN)
    else:
        typer.secho(f"❌ Failed to check conflicts", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command("check-archetype")
def check_archetype(
    archetype_id: Annotated[str, typer.Argument(help="Archetype ID to check")],
    trait_id: Annotated[str, typer.Option("--trait", "-t", help="Trait ID to check for conflicts")],
    json_output: Annotated[bool, typer.Option("--json")] = False
):
    """
    Check if adding a trait to an archetype would create a conflict.

    Example:
        python main.py conflicts check-archetype archetype123 --trait trait456
    """

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(
        f"{BASE_URL}/trait-conflicts/check/archetype/{archetype_id}",
        params={"trait_id": trait_id}
    )

    if response.status_code == 200:
        result = response.json()

        if json_output:
            typer.echo(json.dumps(result, indent=2))
        else:
            has_conflicts = result.get("has_conflicts", False)
            conflicts = result.get("conflicts", [])

            if has_conflicts:
                typer.secho(f"\n❌ CONFLICT DETECTED!", fg=typer.colors.RED)
                typer.echo(f"\nAdding this trait would create {len(conflicts)} conflict(s):\n")

                for conflict in conflicts:
                    typer.echo(f"  ⚡ {conflict.get('group_name', 'Unknown')}")
                    typer.echo(f"    Type: {conflict.get('conflict_type', 'N/A')}")
                    if conflict.get('reason'):
                        typer.echo(f"    Reason: {conflict['reason']}")
                    typer.echo(f"    Conflicting traits: {', '.join(conflict.get('conflicting_trait_ids', []))}")
                    typer.echo()

                raise typer.Exit(1)
            else:
                typer.secho(f"\n✅ No conflicts - safe to add trait", fg=typer.colors.GREEN)
    else:
        typer.secho(f"❌ Failed to check conflicts", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command("by-trait")
def by_trait(
    trait_id: Annotated[str, typer.Argument(help="Trait ID to look up")],
    json_output: Annotated[bool, typer.Option("--json")] = False
):
    """
    Get all conflict groups containing a specific trait.

    Useful for understanding what conflicts a trait participates in.

    Example:
        python main.py conflicts by-trait trait123
    """

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(f"{BASE_URL}/trait-conflicts/by-trait/{trait_id}")

    if response.status_code == 200:
        data = response.json()
        groups = data.get("data", [])
        count = data.get("count", len(groups))

        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.echo(f"\n🔍 Conflict groups containing trait ({count}):\n")

            if not groups:
                typer.secho("  Trait is not in any conflict groups", fg=typer.colors.YELLOW)
            else:
                for group in groups:
                    type_emoji = {
                        "contradictory": "⊕",
                        "contrary": "⊗",
                        "subcontrary": "⊙"
                    }.get(group.get('conflict_type', ''), "•")

                    typer.echo(f"  {type_emoji} {group['name']}")
                    typer.echo(f"    ID: {group['id']}")
                    typer.echo(f"    Type: {group.get('conflict_type', 'N/A')}")
                    if group.get('reason'):
                        typer.echo(f"    Reason: {group['reason'][:80]}...")
                    typer.echo()
    else:
        typer.secho(f"❌ Failed to look up trait", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command("validate")
def validate_group(
    group_id: Annotated[str, typer.Argument(help="Conflict group ID to validate")],
    json_output: Annotated[bool, typer.Option("--json")] = False
):
    """
    Validate that a conflict group has appropriate member count for its type.

    - contradictory: Should have exactly 2 members
    - contrary/subcontrary: Should have at least 2 members

    Example:
        python main.py conflicts validate abc123
    """

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(f"{BASE_URL}/trait-conflicts/{group_id}/validate")

    if response.status_code == 200:
        result = response.json()

        if json_output:
            typer.echo(json.dumps(result, indent=2))
        else:
            is_valid = result.get("valid", False)
            conflict_type = result.get("conflict_type", "unknown")
            member_count = result.get("member_count", 0)
            warnings = result.get("warnings", [])
            errors = result.get("errors", [])

            typer.echo(f"\n🔍 Validation Results:\n")
            typer.echo(f"  Group ID: {group_id}")
            typer.echo(f"  Type: {conflict_type}")
            typer.echo(f"  Members: {member_count}")

            if is_valid:
                typer.secho(f"\n  ✅ VALID", fg=typer.colors.GREEN)
            else:
                typer.secho(f"\n  ❌ INVALID", fg=typer.colors.RED)

            if warnings:
                typer.echo(f"\n  ⚠️  Warnings:")
                for warning in warnings:
                    typer.secho(f"    • {warning}", fg=typer.colors.YELLOW)

            if errors:
                typer.echo(f"\n  ❌ Errors:")
                for error in errors:
                    typer.secho(f"    • {error}", fg=typer.colors.RED)

            if not is_valid:
                raise typer.Exit(1)
    elif response.status_code == 404:
        typer.secho(f"❌ Conflict group not found: {group_id}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    else:
        typer.secho(f"❌ Failed to validate group", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# ============================================================================
# Main (for testing module directly)
# ============================================================================

if __name__ == "__main__":
    app()
