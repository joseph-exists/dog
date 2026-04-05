"""
Story Management Commands

Commands for creating, managing, and testing CYOA stories in staging environments.
"""
import json
from typing import Annotated

import typer
from auth_helper import get_authenticated_session

app = typer.Typer(help="Story management commands")

BASE_URL = "http://localhost:8000/api/v1"


def _parse_json_option(value: str | None, label: str) -> dict | None:
    if value is None:
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} must be valid JSON: {exc}") from exc
    if parsed is None:
        return None
    if not isinstance(parsed, dict):
        raise ValueError(f"{label} must be a JSON object")
    return parsed

# ============================================================================
# Story CRUD Commands
# ============================================================================

@app.command()
def create(
    title: Annotated[str, typer.Argument(help="Story title")],
    description: Annotated[str, typer.Option("--desc", "-d", help="Story description")] = "",
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False
):
    """
    Create a new story.

    Example:
        python main.py stories create "The Enchanted Forest" --desc "A mystical adventure"
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    log(f"Creating story: {title}")

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    payload = {
        "title": title,
        "description": description,
        "current_version": 1
    }

    log(f"POST {BASE_URL}/stories")
    log(f"Payload: {json.dumps(payload, indent=2)}")

    response = session.post(f"{BASE_URL}/stories", json=payload)

    log(f"Response status: {response.status_code}")
    log(f"Response: {response.text[:500]}")

    if response.status_code == 200:
        story = response.json()
        typer.secho("✅ Story created successfully!", fg=typer.colors.GREEN)
        typer.echo(f"ID: {story['id']}")
        typer.echo(f"Title: {story['title']}")
        typer.echo(f"Version: {story['current_version']}")

        if verbose:
            typer.echo("\nFull response:")
            typer.echo(json.dumps(story, indent=2))
    else:
        typer.secho(f"❌ Failed to create story", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def list(
    limit: Annotated[int, typer.Option(help="Max stories to list")] = 10,
    offset: Annotated[int, typer.Option(help="Pagination offset")] = 0,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False
):
    """
    List all stories.

    Example:
        python main.py stories list --limit 5
        python main.py stories list --json
    """

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(
        f"{BASE_URL}/stories",
        params={"limit": limit, "offset": offset}
    )

    if response.status_code == 200:
        data = response.json()
        stories = data.get("data", [])
        total = data.get("count", 0)

        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.echo(f"\n📚 Stories ({len(stories)} of {total}):\n")

            if not stories:
                typer.secho("  No stories found", fg=typer.colors.YELLOW)
            else:
                for story in stories:
                    pub_status = "✓ Published" if story.get('is_published') else "○ Draft"
                    typer.echo(f"  • {story['title']} [{pub_status}]")
                    typer.echo(f"    ID: {story['id']}")
                    typer.echo(f"    Version: {story.get('current_version', 'N/A')}")
                    if story.get('description'):
                        typer.echo(f"    Desc: {story['description'][:60]}...")
                    typer.echo()
    else:
        typer.secho(f"❌ Failed to list stories", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def get(
    story_id: Annotated[str, typer.Argument(help="Story ID")],
    json_output: Annotated[bool, typer.Option("--json")] = False
):
    """
    Get details for a specific story.

    Example:
        python main.py stories get abc123
    """

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(f"{BASE_URL}/stories/{story_id}")

    if response.status_code == 200:
        story = response.json()

        if json_output:
            typer.echo(json.dumps(story, indent=2))
        else:
            typer.echo(f"\n📖 Story Details:\n")
            typer.echo(f"Title: {story['title']}")
            typer.echo(f"ID: {story['id']}")
            typer.echo(f"Published: {'Yes' if story.get('is_published') else 'No'}")
            typer.echo(f"Current Version: {story.get('current_version', 'N/A')}")
            if story.get('published_version'):
                typer.echo(f"Published Version: {story['published_version']}")
            if story.get('description'):
                typer.echo(f"\nDescription:\n{story['description']}")
    else:
        typer.secho(f"❌ Story not found", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def publish(
    story_id: Annotated[str, typer.Argument(help="Story ID to publish")],
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False
):
    """
    Publish a story (makes it immutable and playable).

    Example:
        python main.py stories publish abc123
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    log(f"Publishing story: {story_id}")

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    log(f"PUT {BASE_URL}/stories/{story_id}/publish")

    response = session.put(f"{BASE_URL}/stories/{story_id}/publish")

    log(f"Response status: {response.status_code}")
    log(f"Response: {response.text[:500]}")

    if response.status_code == 200:
        story = response.json()

        if not story.get("is_published"):
            typer.secho("⚠️  Story not marked as published", fg=typer.colors.YELLOW)
            raise typer.Exit(1)

        typer.secho("✅ Story published successfully!", fg=typer.colors.GREEN)
        typer.echo(f"Published Version: {story.get('published_version', 'N/A')}")
        typer.echo(f"Current Version: {story.get('current_version', 'N/A')}")
    else:
        typer.secho(f"❌ Failed to publish story", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def unpublish(
    story_id: Annotated[str, typer.Argument(help="Story ID to unpublish")],
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False
):
    """Unpublish a story (return to draft)."""

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    log(f"PUT {BASE_URL}/stories/{story_id}/unpublish")
    response = session.put(f"{BASE_URL}/stories/{story_id}/unpublish")

    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        story = response.json()
        typer.secho("✅ Story unpublished successfully!", fg=typer.colors.GREEN)
        typer.echo(f"Current Version: {story.get('current_version', 'N/A')}")
        typer.echo(f"Published Version: {story.get('published_version', 'N/A')}")
    else:
        typer.secho("❌ Failed to unpublish story", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def new_version(
    story_id: Annotated[str, typer.Argument(help="Story ID")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False
):
    """Create a new draft version for a story."""

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    log(f"POST {BASE_URL}/stories/{story_id}/new-version")
    response = session.post(f"{BASE_URL}/stories/{story_id}/new-version")

    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        story = response.json()
        if json_output:
            typer.echo(json.dumps(story, indent=2))
        else:
            typer.secho("✅ New story version created!", fg=typer.colors.GREEN)
            typer.echo(f"Current Version: {story.get('current_version', 'N/A')}")
            typer.echo(f"Published Version: {story.get('published_version', 'N/A')}")
    else:
        typer.secho("❌ Failed to create new version", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def update(
    story_id: Annotated[str, typer.Argument(help="Story ID")],
    title: Annotated[str | None, typer.Option("--title", help="Story title")] = None,
    description: Annotated[str | None, typer.Option("--desc", "-d", help="Story description")] = None,
    content_format: Annotated[str | None, typer.Option("--content-format", help="Content format (e.g. text, markdown)")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False
):
    """Update story metadata."""

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    payload = {
        "title": title,
        "description": description,
        "content_format": content_format,
    }
    payload = {k: v for k, v in payload.items() if v is not None}

    if not payload:
        typer.secho("⚠️  No fields to update provided", fg=typer.colors.YELLOW)
        raise typer.Exit(0)

    log(f"PUT {BASE_URL}/stories/{story_id}")
    log(f"Payload: {json.dumps(payload, indent=2)}")

    response = session.put(f"{BASE_URL}/stories/{story_id}", json=payload)

    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        story = response.json()
        if json_output:
            typer.echo(json.dumps(story, indent=2))
        else:
            typer.secho("✅ Story updated successfully!", fg=typer.colors.GREEN)
            typer.echo(f"Title: {story.get('title')}")
            typer.echo(f"ID: {story.get('id')}")
    else:
        typer.secho("❌ Failed to update story", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def delete(
    story_id: Annotated[str, typer.Argument(help="Story ID")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False
):
    """Delete a story."""
    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    if not force:
        typer.secho(f"⚠️  This will delete story {story_id}", fg=typer.colors.YELLOW)
        if not typer.confirm("Are you sure?"):
            typer.echo("Cancelled.")
            raise typer.Exit(0)

    response = session.delete(f"{BASE_URL}/stories/{story_id}")

    if response.status_code in [200, 204]:
        typer.secho("✅ Story deleted!", fg=typer.colors.GREEN)
    else:
        typer.secho("❌ Failed to delete story", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# ============================================================================
# Story Node Commands
# ============================================================================

@app.command()
def add_node(
    story_id: Annotated[str, typer.Argument(help="Story ID")],
    title: Annotated[str, typer.Option("--title", "-t", help="Node title")],
    content: Annotated[str, typer.Option("--content", "-c", help="Node content")],
    version: Annotated[int, typer.Option("--version", "-V", help="Story version")] = 1,
    node_type: Annotated[str | None, typer.Option("--node-type", help="Node type tag")] = None,
    content_format: Annotated[str | None, typer.Option("--content-format", help="Content format (e.g. text, markdown)")] = None,
    start: Annotated[bool, typer.Option("--start", help="Mark as start node")] = False,
    end: Annotated[bool, typer.Option("--end", help="Mark as end node")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False
):
    """
    Add a node to a story.

    Example:
        python main.py stories add-node abc123 --title "Forest Entrance" --content "You stand..." --start
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    log(f"Adding node to story: {story_id}")

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    payload = {
        "story_id": story_id,
        "story_version": version,
        "title": title,
        "content": content,
        "node_type": node_type,
        "content_format": content_format,
        "is_start_node": start,
        "is_end_node": end
    }

    payload = {k: v for k, v in payload.items() if v is not None}

    log(f"POST {BASE_URL}/storynodes")
    log(f"Payload: {json.dumps(payload, indent=2)}")

    response = session.post(f"{BASE_URL}/storynodes", json=payload)

    log(f"Response status: {response.status_code}")
    log(f"Response: {response.text[:500]}")

    if response.status_code == 200:
        node = response.json()
        if json_output:
            typer.echo(json.dumps(node, indent=2))
        else:
            typer.secho("✅ Node added successfully!", fg=typer.colors.GREEN)
            typer.echo(f"Node ID: {node['id']}")
            typer.echo(f"Title: {node['title']}")
            if start:
                typer.echo("  (Start node)")
            if end:
                typer.echo("  (End node)")
    else:
        typer.secho(f"❌ Failed to add node", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def add_choice(
    from_node: Annotated[str, typer.Argument(help="Source node ID")],
    to_node: Annotated[str, typer.Argument(help="Destination node ID")],
    text: Annotated[str, typer.Option("--text", "-t", help="Choice text")],
    order: Annotated[int, typer.Option("--order", "-o", help="Choice order")] = 0,
    requires_state: Annotated[str | None, typer.Option("--requires-state", help="JSON object of required state conditions")] = None,
    sets_state: Annotated[str | None, typer.Option("--sets-state", help="JSON object of state mutations")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False
):
    """
    Add a choice between two nodes.

    Example:
        python main.py stories add-choice node1 node2 --text "Take the left path"
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    log(f"Adding choice: {from_node} -> {to_node}")

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    try:
        parsed_requires = _parse_json_option(requires_state, "requires_state")
        parsed_sets = _parse_json_option(sets_state, "sets_state")
    except ValueError as exc:
        typer.secho(f"❌ {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    payload = {
        "from_node_id": from_node,
        "to_node_id": to_node,
        "text": text,
        "order": order,
        "requires_state": parsed_requires,
        "sets_state": parsed_sets,
    }

    payload = {k: v for k, v in payload.items() if v is not None}

    log(f"POST {BASE_URL}/node-choices")
    log(f"Payload: {json.dumps(payload, indent=2)}")

    response = session.post(f"{BASE_URL}/node-choices", json=payload)

    log(f"Response status: {response.status_code}")
    log(f"Response: {response.text[:500]}")

    if response.status_code == 200:
        choice = response.json()
        if json_output:
            typer.echo(json.dumps(choice, indent=2))
        else:
            typer.secho("✅ Choice added successfully!", fg=typer.colors.GREEN)
            typer.echo(f"Choice ID: {choice['id']}")
            typer.echo(f"Text: {choice['text']}")
            typer.echo(f"From: {choice['from_node_id']}")
            typer.echo(f"To: {choice['to_node_id']}")
    else:
        typer.secho(f"❌ Failed to add choice", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# ============================================================================
# Story Node/Choice CRUD Commands
# ============================================================================

@app.command()
def list_nodes(
    story_id: Annotated[str, typer.Argument(help="Story ID")],
    version: Annotated[int | None, typer.Option("--version", "-v", help="Story version")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """List story nodes (via story tree, filtered to this story)."""
    try:
        session = get_authenticated_session()
    except Exception as exc:
        typer.secho(f"❌ Authentication failed: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    params: dict = {}
    if version is not None:
        params["version"] = version

    response = session.get(f"{BASE_URL}/stories/{story_id}/tree", params=params)

    if response.status_code == 200:
        tree = response.json()

        # Flatten recursive tree into ordered list
        def flatten(node: dict) -> list:
            result = [node]
            for child in node.get("children", []):
                result.extend(flatten(child))
            return result

        root = tree.get("root")
        nodes = flatten(root) if root else []
        orphans = tree.get("orphaned_nodes", [])

        if json_output:
            typer.echo(json.dumps({"nodes": nodes, "orphaned_nodes": orphans}, indent=2))
            return

        typer.echo(f"\n📚 Story Nodes ({len(nodes)} reachable, {len(orphans)} orphaned):\n")
        if not nodes:
            typer.secho("  No nodes found", fg=typer.colors.YELLOW)
        else:
            for node in nodes:
                tags = []
                if node.get("is_start_node"):
                    tags.append("START")
                if node.get("is_end_node"):
                    tags.append("END")
                indent = "  " + ("  " * node.get("level", 0))
                tag_str = f" [{' '.join(tags)}]" if tags else ""
                typer.echo(f"{indent}• {node.get('title', 'Untitled')}{tag_str}")
                typer.echo(f"{indent}  ID: {node.get('id')}")
        if orphans:
            typer.echo(f"\n⚠️  Orphaned nodes ({len(orphans)}):\n")
            for node in orphans:
                typer.echo(f"  • {node.get('title', 'Untitled')}")
                typer.echo(f"    ID: {node.get('id')}")
    else:
        typer.secho("❌ Failed to list nodes", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def get_node(
    node_id: Annotated[str, typer.Argument(help="Node ID")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """Get details for a specific node."""
    try:
        session = get_authenticated_session()
    except Exception as exc:
        typer.secho(f"❌ Authentication failed: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(f"{BASE_URL}/storynodes/{node_id}")

    if response.status_code == 200:
        node = response.json()
        if json_output:
            typer.echo(json.dumps(node, indent=2))
        else:
            typer.echo(f"\n📄 Node Details:\n")
            typer.echo(f"Title: {node.get('title')}")
            typer.echo(f"ID: {node.get('id')}")
            typer.echo(f"Story ID: {node.get('story_id')}")
            typer.echo(f"Version: {node.get('story_version')}")
            if node.get("node_type"):
                typer.echo(f"Type: {node.get('node_type')}")
            if node.get("content"):
                typer.echo(f"\nContent:\n{node.get('content')}")
    else:
        typer.secho("❌ Node not found", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def update_node(
    node_id: Annotated[str, typer.Argument(help="Node ID")],
    title: Annotated[str | None, typer.Option("--title", "-t", help="Node title")] = None,
    content: Annotated[str | None, typer.Option("--content", "-c", help="Node content")] = None,
    node_type: Annotated[str | None, typer.Option("--node-type", help="Node type tag")] = None,
    content_format: Annotated[str | None, typer.Option("--content-format", help="Content format (e.g. text, markdown)")] = None,
    start: Annotated[bool | None, typer.Option("--start/--no-start", help="Set start node flag")] = None,
    end: Annotated[bool | None, typer.Option("--end/--no-end", help="Set end node flag")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
):
    """Update a story node."""

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    try:
        session = get_authenticated_session()
    except Exception as exc:
        typer.secho(f"❌ Authentication failed: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    payload = {
        "title": title,
        "content": content,
        "node_type": node_type,
        "content_format": content_format,
        "is_start_node": start,
        "is_end_node": end,
    }
    payload = {k: v for k, v in payload.items() if v is not None}

    if not payload:
        typer.secho("⚠️  No fields to update provided", fg=typer.colors.YELLOW)
        raise typer.Exit(0)

    log(f"PUT {BASE_URL}/storynodes/{node_id}")
    log(f"Payload: {json.dumps(payload, indent=2)}")

    response = session.put(f"{BASE_URL}/storynodes/{node_id}", json=payload)

    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        node = response.json()
        if json_output:
            typer.echo(json.dumps(node, indent=2))
        else:
            typer.secho("✅ Node updated successfully!", fg=typer.colors.GREEN)
            typer.echo(f"ID: {node.get('id')}")
            typer.echo(f"Title: {node.get('title')}")
    else:
        typer.secho("❌ Failed to update node", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def delete_node(
    node_id: Annotated[str, typer.Argument(help="Node ID")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False,
):
    """Delete a story node."""
    try:
        session = get_authenticated_session()
    except Exception as exc:
        typer.secho(f"❌ Authentication failed: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    if not force:
        typer.secho(f"⚠️  This will delete node {node_id}", fg=typer.colors.YELLOW)
        if not typer.confirm("Are you sure?"):
            typer.echo("Cancelled.")
            raise typer.Exit(0)

    response = session.delete(f"{BASE_URL}/storynodes/{node_id}")

    if response.status_code in [200, 204]:
        typer.secho("✅ Node deleted!", fg=typer.colors.GREEN)
    else:
        typer.secho("❌ Failed to delete node", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def list_choices(
    story_id: Annotated[str | None, typer.Option("--story-id", help="Story ID filter")] = None,
    node_id: Annotated[str | None, typer.Option("--node-id", help="Node ID filter")] = None,
    limit: Annotated[int, typer.Option(help="Max choices to list")] = 50,
    offset: Annotated[int, typer.Option(help="Pagination offset")] = 0,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """List node choices."""
    try:
        session = get_authenticated_session()
    except Exception as exc:
        typer.secho(f"❌ Authentication failed: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    params = {"limit": limit, "offset": offset}

    if node_id:
        response = session.get(f"{BASE_URL}/storynodes/{node_id}/choices", params=params)
    else:
        if story_id:
            params["story_id"] = story_id
        response = session.get(f"{BASE_URL}/node-choices", params=params)

    if response.status_code == 200:
        data = response.json()
        if json_output:
            typer.echo(json.dumps(data, indent=2))
            return
        choices = data.get("data", [])
        total = data.get("count", 0)
        typer.echo(f"\n🔀 Choices ({len(choices)} of {total}):\n")
        if not choices:
            typer.secho("  No choices found", fg=typer.colors.YELLOW)
        else:
            for choice in choices:
                typer.echo(f"  • {choice.get('text', 'Untitled')}")
                typer.echo(f"    ID: {choice.get('id')}")
                typer.echo(f"    From: {choice.get('from_node_id')}  To: {choice.get('to_node_id')}")
                typer.echo()
    else:
        typer.secho("❌ Failed to list choices", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def get_choice(
    choice_id: Annotated[str, typer.Argument(help="Choice ID")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """Get details for a specific choice."""
    try:
        session = get_authenticated_session()
    except Exception as exc:
        typer.secho(f"❌ Authentication failed: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(f"{BASE_URL}/node-choices/{choice_id}")

    if response.status_code == 200:
        choice = response.json()
        if json_output:
            typer.echo(json.dumps(choice, indent=2))
        else:
            typer.echo(f"\n🔀 Choice Details:\n")
            typer.echo(f"Text: {choice.get('text')}")
            typer.echo(f"ID: {choice.get('id')}")
            typer.echo(f"From: {choice.get('from_node_id')}")
            typer.echo(f"To: {choice.get('to_node_id')}")
    else:
        typer.secho("❌ Choice not found", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def update_choice(
    choice_id: Annotated[str, typer.Argument(help="Choice ID")],
    text: Annotated[str | None, typer.Option("--text", "-t", help="Choice text")] = None,
    order: Annotated[int | None, typer.Option("--order", "-o", help="Choice order")] = None,
    to_node_id: Annotated[str | None, typer.Option("--to-node-id", help="Destination node ID")] = None,
    requires_state: Annotated[str | None, typer.Option("--requires-state", help="JSON object of required state conditions")] = None,
    sets_state: Annotated[str | None, typer.Option("--sets-state", help="JSON object of state mutations")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
):
    """Update a node choice."""

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    try:
        session = get_authenticated_session()
    except Exception as exc:
        typer.secho(f"❌ Authentication failed: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    try:
        parsed_requires = _parse_json_option(requires_state, "requires_state")
        parsed_sets = _parse_json_option(sets_state, "sets_state")
    except ValueError as exc:
        typer.secho(f"❌ {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    payload = {
        "text": text,
        "order": order,
        "to_node_id": to_node_id,
        "requires_state": parsed_requires,
        "sets_state": parsed_sets,
    }
    payload = {k: v for k, v in payload.items() if v is not None}

    if not payload:
        typer.secho("⚠️  No fields to update provided", fg=typer.colors.YELLOW)
        raise typer.Exit(0)

    log(f"PUT {BASE_URL}/node-choices/{choice_id}")
    log(f"Payload: {json.dumps(payload, indent=2)}")

    response = session.put(f"{BASE_URL}/node-choices/{choice_id}", json=payload)

    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        choice = response.json()
        if json_output:
            typer.echo(json.dumps(choice, indent=2))
        else:
            typer.secho("✅ Choice updated successfully!", fg=typer.colors.GREEN)
            typer.echo(f"ID: {choice.get('id')}")
            typer.echo(f"Text: {choice.get('text')}")
    else:
        typer.secho("❌ Failed to update choice", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def delete_choice(
    choice_id: Annotated[str, typer.Argument(help="Choice ID")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False,
):
    """Delete a node choice."""
    try:
        session = get_authenticated_session()
    except Exception as exc:
        typer.secho(f"❌ Authentication failed: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    if not force:
        typer.secho(f"⚠️  This will delete choice {choice_id}", fg=typer.colors.YELLOW)
        if not typer.confirm("Are you sure?"):
            typer.echo("Cancelled.")
            raise typer.Exit(0)

    response = session.delete(f"{BASE_URL}/node-choices/{choice_id}")

    if response.status_code in [200, 204]:
        typer.secho("✅ Choice deleted!", fg=typer.colors.GREEN)
    else:
        typer.secho("❌ Failed to delete choice", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def start_node(
    story_id: Annotated[str, typer.Argument(help="Story ID")],
    version: Annotated[int | None, typer.Option("--version", "-v", help="Story version")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """Get the start node for a story."""
    try:
        session = get_authenticated_session()
    except Exception as exc:
        typer.secho(f"❌ Authentication failed: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    params = {}
    if version is not None:
        params["version"] = version

    response = session.get(f"{BASE_URL}/stories/{story_id}/start-node", params=params)

    if response.status_code == 200:
        node = response.json()
        if json_output:
            typer.echo(json.dumps(node, indent=2))
        else:
            typer.echo(f"\n🚀 Start Node:\n")
            typer.echo(f"Title: {node.get('title')}")
            typer.echo(f"ID: {node.get('id')}")
            typer.echo(f"Version: {node.get('story_version')}")
    else:
        typer.secho("❌ Failed to get start node", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# ============================================================================
# Room Integration Commands
# ============================================================================

@app.command()
def list_rooms(
    story_id: Annotated[str, typer.Argument(help="Story ID")],
    limit: Annotated[int, typer.Option(help="Max rooms to list")] = 10,
    offset: Annotated[int, typer.Option(help="Pagination offset")] = 0,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False
):
    """
    List rooms associated with a story.

    Example:
        python main.py stories list-rooms abc123
        python main.py stories list-rooms abc123 --limit 5 --json
    """

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(
        f"{BASE_URL}/rooms/story/{story_id}",
        params={"skip": offset, "limit": limit}
    )

    if response.status_code == 200:
        data = response.json()
        rooms = data.get("data", [])
        total = data.get("count", 0)

        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.echo(f"\n💬 Rooms for story ({len(rooms)} of {total}):\n")

            if not rooms:
                typer.secho("  No rooms found for this story", fg=typer.colors.YELLOW)
            else:
                for room in rooms:
                    typer.echo(f"  • {room.get('title', 'Untitled')}")
                    typer.echo(f"    Room ID: {room.get('room_id', 'N/A')}")
                    typer.echo(f"    Created: {room.get('created_at', 'N/A')}")
                    typer.echo(f"    Last Activity: {room.get('last_activity', 'N/A')}")
                    typer.echo()
    else:
        typer.secho(f"❌ Failed to list rooms for story", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def create_room(
    story_id: Annotated[str, typer.Argument(help="Story ID")],
    title: Annotated[str, typer.Option("--title", "-t", help="Room title")],
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False
):
    """
    Create a room associated with a story.

    Example:
        python main.py stories create-room abc123 --title "Adventure Room"
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    log(f"Creating room for story: {story_id}")

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    payload = {
        "title": title,
        "story_id": story_id
    }

    log(f"POST {BASE_URL}/rooms")
    log(f"Payload: {json.dumps(payload, indent=2)}")

    response = session.post(f"{BASE_URL}/rooms", json=payload)

    log(f"Response status: {response.status_code}")
    log(f"Response: {response.text[:500]}")

    if response.status_code in [200, 201]:
        room = response.json()
        typer.secho("✅ Room created successfully!", fg=typer.colors.GREEN)
        typer.echo(f"Room ID: {room.get('room_id', 'N/A')}")
        typer.echo(f"Title: {room.get('title', 'N/A')}")
        typer.echo(f"Story ID: {story_id}")
    else:
        typer.secho(f"❌ Failed to create room", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# ============================================================================
# Story Requirements Commands
# ============================================================================

@app.command()
def list_requirements(
    story_id: Annotated[str, typer.Argument(help="Story ID")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False
):
    """List access requirements for a story."""
    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(f"{BASE_URL}/stories/{story_id}/requirements")

    if response.status_code == 200:
        data = response.json()
        if json_output:
            typer.echo(json.dumps(data, indent=2))
            return
        requirements = data.get("data", [])
        total = data.get("count", 0)
        typer.echo(f"\n🔒 Requirements ({len(requirements)} of {total}):\n")
        if not requirements:
            typer.secho("  No requirements found", fg=typer.colors.YELLOW)
        else:
            for req in requirements:
                typer.echo(f"  • {req.get('requirement_type')} -> {req.get('target_id')}")
                if req.get("description"):
                    typer.echo(f"    {req.get('description')}")
                typer.echo(f"    ID: {req.get('id')}")
                typer.echo()
    else:
        typer.secho("❌ Failed to list requirements", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def add_requirement(
    story_id: Annotated[str, typer.Argument(help="Story ID")],
    requirement_type: Annotated[str, typer.Option("--type", "-t", help="Requirement type")] = None,
    target_id: Annotated[str, typer.Option("--target-id", help="Target UUID")] = None,
    description: Annotated[str | None, typer.Option("--desc", "-d", help="Requirement description")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False
):
    """Add an access requirement to a story."""

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    if not requirement_type or not target_id:
        typer.secho("❌ --type and --target-id are required", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    payload = {
        "requirement_type": requirement_type,
        "target_id": target_id,
        "description": description,
    }
    payload = {k: v for k, v in payload.items() if v is not None}

    log(f"POST {BASE_URL}/stories/{story_id}/requirements")
    log(f"Payload: {json.dumps(payload, indent=2)}")

    response = session.post(f"{BASE_URL}/stories/{story_id}/requirements", json=payload)

    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        requirement = response.json()
        if json_output:
            typer.echo(json.dumps(requirement, indent=2))
        else:
            typer.secho("✅ Requirement added!", fg=typer.colors.GREEN)
            typer.echo(f"Type: {requirement.get('requirement_type')}")
            typer.echo(f"Target: {requirement.get('target_id')}")
            typer.echo(f"ID: {requirement.get('id')}")
    else:
        typer.secho("❌ Failed to add requirement", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def delete_requirement(
    story_id: Annotated[str, typer.Argument(help="Story ID")],
    requirement_id: Annotated[str, typer.Argument(help="Requirement ID")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False
):
    """Delete a story requirement."""
    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    if not force:
        typer.secho(
            f"⚠️  This will delete requirement {requirement_id} from story {story_id}",
            fg=typer.colors.YELLOW,
        )
        if not typer.confirm("Are you sure?"):
            typer.echo("Cancelled.")
            raise typer.Exit(0)

    response = session.delete(
        f"{BASE_URL}/stories/{story_id}/requirements/{requirement_id}"
    )

    if response.status_code in [200, 204]:
        typer.secho("✅ Requirement deleted!", fg=typer.colors.GREEN)
    else:
        typer.secho("❌ Failed to delete requirement", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# ============================================================================
# Story Progress Commands
# ============================================================================

@app.command()
def list_progress(
    user_persona_id: Annotated[str, typer.Argument(help="User persona ID")],
    limit: Annotated[int, typer.Option(help="Max items to list")] = 20,
    offset: Annotated[int, typer.Option(help="Pagination offset")] = 0,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """List story progress records for a user persona."""
    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(
        f"{BASE_URL}/user-personas/{user_persona_id}/stories/",
        params={"limit": limit, "skip": offset},
    )

    if response.status_code == 200:
        data = response.json()
        if json_output:
            typer.echo(json.dumps(data, indent=2))
            return
        progress_list = data.get("data", [])
        total = data.get("count", 0)
        typer.echo(f"\n📈 Story Progress ({len(progress_list)} of {total}):\n")
        if not progress_list:
            typer.secho("  No progress found", fg=typer.colors.YELLOW)
        else:
            for progress in progress_list:
                typer.echo(f"  • Story ID: {progress.get('story_id')}")
                typer.echo(f"    Progress ID: {progress.get('id')}")
                typer.echo(f"    Version: {progress.get('story_version')}")
                typer.echo()
    else:
        typer.secho("❌ Failed to list progress", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def get_progress(
    user_persona_id: Annotated[str, typer.Argument(help="User persona ID")],
    story_id: Annotated[str, typer.Argument(help="Story ID")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """Get a user's progress for a specific story."""
    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(
        f"{BASE_URL}/user-personas/{user_persona_id}/stories/{story_id}"
    )

    if response.status_code == 200:
        progress = response.json()
        if json_output:
            typer.echo(json.dumps(progress, indent=2))
        else:
            typer.echo(f"\n📈 Story Progress:\n")
            typer.echo(f"ID: {progress.get('id')}")
            typer.echo(f"Story ID: {progress.get('story_id')}")
            typer.echo(f"Version: {progress.get('story_version')}")
            typer.echo(f"Completed: {progress.get('is_completed')}")
    else:
        typer.secho("❌ Progress not found", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def create_progress(
    user_persona_id: Annotated[str, typer.Argument(help="User persona ID")],
    story_id: Annotated[str, typer.Argument(help="Story ID")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """Create a new story progress for a persona."""
    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.post(
        f"{BASE_URL}/user-personas/{user_persona_id}/stories/{story_id}"
    )

    if response.status_code == 200:
        progress = response.json()
        if json_output:
            typer.echo(json.dumps(progress, indent=2))
        else:
            typer.secho("✅ Progress created!", fg=typer.colors.GREEN)
            typer.echo(f"ID: {progress.get('id')}")
            typer.echo(f"Version: {progress.get('story_version')}")
    else:
        typer.secho("❌ Failed to create progress", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def update_progress(
    user_persona_id: Annotated[str, typer.Argument(help="User persona ID")],
    story_id: Annotated[str, typer.Argument(help="Story ID")],
    current_node_id: Annotated[str | None, typer.Option("--current-node-id", help="Current node ID")] = None,
    is_completed: Annotated[bool | None, typer.Option("--completed/--not-completed", help="Set completion flag")] = None,
    story_state: Annotated[str | None, typer.Option("--story-state", help="JSON object for story state")] = None,
    head_choice_id: Annotated[str | None, typer.Option("--head-choice-id", help="Head choice ID")] = None,
    head_version: Annotated[int | None, typer.Option("--head-version", help="Head version (optimistic lock)")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
):
    """Update story progress (admin/debug)."""

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    try:
        parsed_state = _parse_json_option(story_state, "story_state")
    except ValueError as exc:
        typer.secho(f"❌ {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    payload = {
        "current_node_id": current_node_id,
        "is_completed": is_completed,
        "story_state": parsed_state,
        "head_choice_id": head_choice_id,
        "head_version": head_version,
    }
    payload = {k: v for k, v in payload.items() if v is not None}

    if not payload:
        typer.secho("⚠️  No fields to update provided", fg=typer.colors.YELLOW)
        raise typer.Exit(0)

    log(f"PUT {BASE_URL}/user-personas/{user_persona_id}/stories/{story_id}")
    log(f"Payload: {json.dumps(payload, indent=2)}")

    response = session.put(
        f"{BASE_URL}/user-personas/{user_persona_id}/stories/{story_id}",
        json=payload,
    )

    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        progress = response.json()
        if json_output:
            typer.echo(json.dumps(progress, indent=2))
        else:
            typer.secho("✅ Progress updated!", fg=typer.colors.GREEN)
            typer.echo(f"ID: {progress.get('id')}")
    else:
        typer.secho("❌ Failed to update progress", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def current_node(
    user_persona_id: Annotated[str, typer.Argument(help="User persona ID")],
    story_id: Annotated[str, typer.Argument(help="Story ID")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """Get current node and available choices for progress."""
    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(
        f"{BASE_URL}/user-personas/{user_persona_id}/stories/{story_id}/current-node"
    )

    if response.status_code == 200:
        data = response.json()
        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            node = data.get("node", {})
            choices = data.get("available_choices", [])
            typer.echo(f"\n📍 Current Node:\n")
            typer.echo(f"Title: {node.get('title')}")
            typer.echo(f"ID: {node.get('id')}")
            typer.echo(f"\nChoices ({len(choices)}):")
            for choice in choices:
                typer.echo(f"  • {choice.get('text')} ({choice.get('id')})")
    else:
        typer.secho("❌ Failed to fetch current node", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def make_choice(
    user_persona_id: Annotated[str, typer.Argument(help="User persona ID")],
    story_id: Annotated[str, typer.Argument(help="Story ID")],
    choice_id: Annotated[str, typer.Argument(help="Choice ID")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """Make a story choice and advance progress."""
    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.post(
        f"{BASE_URL}/user-personas/{user_persona_id}/stories/{story_id}/choices/{choice_id}"
    )

    if response.status_code == 200:
        progress = response.json()
        if json_output:
            typer.echo(json.dumps(progress, indent=2))
        else:
            typer.secho("✅ Choice applied!", fg=typer.colors.GREEN)
            typer.echo(f"Head choice: {progress.get('head_choice_id')}")
            typer.echo(f"Completed: {progress.get('is_completed')}")
    else:
        typer.secho("❌ Failed to apply choice", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def validate_state(
    user_persona_id: Annotated[str, typer.Argument(help="User persona ID")],
    story_id: Annotated[str, typer.Argument(help="Story ID")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """Validate story state against replayed state."""
    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(
        f"{BASE_URL}/user-personas/{user_persona_id}/stories/{story_id}/validate-state"
    )

    if response.status_code == 200:
        data = response.json()
        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.secho("✅ Validation complete", fg=typer.colors.GREEN)
            typer.echo(f"Match: {data.get('match')}")
    else:
        typer.secho("❌ Failed to validate state", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def undo(
    user_persona_id: Annotated[str, typer.Argument(help="User persona ID")],
    story_id: Annotated[str, typer.Argument(help="Story ID")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """Undo last choice (rewind one step)."""
    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.post(
        f"{BASE_URL}/user-personas/{user_persona_id}/stories/{story_id}/undo"
    )

    if response.status_code == 200:
        progress = response.json()
        if json_output:
            typer.echo(json.dumps(progress, indent=2))
        else:
            typer.secho("✅ Undo complete", fg=typer.colors.GREEN)
            typer.echo(f"Head choice: {progress.get('head_choice_id')}")
    else:
        typer.secho("❌ Failed to undo", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def jump(
    user_persona_id: Annotated[str, typer.Argument(help="User persona ID")],
    story_id: Annotated[str, typer.Argument(help="Story ID")],
    expected_head_version: Annotated[int, typer.Option("--expected-head-version", help="Expected head version")] = None,
    choice_id: Annotated[str | None, typer.Option("--choice-id", help="Target choice ID (null = start)")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """Jump head to an ancestor choice."""
    if expected_head_version is None:
        typer.secho("❌ --expected-head-version is required", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    payload = {
        "choice_id": choice_id,
        "expected_head_version": expected_head_version,
    }

    response = session.post(
        f"{BASE_URL}/user-personas/{user_persona_id}/stories/{story_id}/jump",
        json=payload,
    )

    if response.status_code == 200:
        progress = response.json()
        if json_output:
            typer.echo(json.dumps(progress, indent=2))
        else:
            typer.secho("✅ Jump complete", fg=typer.colors.GREEN)
            typer.echo(f"Head choice: {progress.get('head_choice_id')}")
            typer.echo(f"Head version: {progress.get('head_version')}")
    else:
        typer.secho("❌ Failed to jump", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def timeline(
    user_persona_id: Annotated[str, typer.Argument(help="User persona ID")],
    story_id: Annotated[str, typer.Argument(help="Story ID")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """Get active timeline (root to head)."""
    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(
        f"{BASE_URL}/user-personas/{user_persona_id}/stories/{story_id}/timeline"
    )

    if response.status_code == 200:
        data = response.json()
        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            events = data.get("events", [])
            typer.echo(f"\n🧭 Timeline ({len(events)} events):\n")
            for event in events:
                marker = "•"
                if event.get("is_current"):
                    marker = "*"
                typer.echo(f"  {marker} {event.get('choice_text')}")
    else:
        typer.secho("❌ Failed to load timeline", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def snapshots(
    user_persona_id: Annotated[str, typer.Argument(help="User persona ID")],
    story_id: Annotated[str, typer.Argument(help="Story ID")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """List snapshots for a story progress."""
    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(
        f"{BASE_URL}/user-personas/{user_persona_id}/stories/{story_id}/snapshots"
    )

    if response.status_code == 200:
        data = response.json()
        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            snapshots = data.get("data", [])
            typer.echo(f"\n📸 Snapshots ({len(snapshots)}):\n")
            for snap in snapshots:
                typer.echo(f"  • {snap.get('id')} @ {snap.get('created_at')}")
    else:
        typer.secho("❌ Failed to list snapshots", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def create_snapshot(
    user_persona_id: Annotated[str, typer.Argument(help="User persona ID")],
    story_id: Annotated[str, typer.Argument(help="Story ID")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """Create a snapshot at current head."""
    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.post(
        f"{BASE_URL}/user-personas/{user_persona_id}/stories/{story_id}/snapshots/create"
    )

    if response.status_code == 200:
        snapshot = response.json()
        if json_output:
            typer.echo(json.dumps(snapshot, indent=2))
        else:
            typer.secho("✅ Snapshot created!", fg=typer.colors.GREEN)
            typer.echo(f"ID: {snapshot.get('id')}")
    else:
        typer.secho("❌ Failed to create snapshot", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# ============================================================================
# State Schema Commands
# ============================================================================

@app.command()
def list_state_vars(
    story_id: Annotated[str, typer.Argument(help="Story ID")],
    version: Annotated[int, typer.Option("--version", "-v", help="Story version")] = 1,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False
):
    """
    List state variables defined for a story version.

    Example:
        python main.py stories list-state-vars abc123
        python main.py stories list-state-vars abc123 --version 2 --json
    """

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(
        f"{BASE_URL}/stories/{story_id}/versions/{version}/state-schema"
    )

    if response.status_code == 200:
        data = response.json()
        variables = data.get("data", [])
        total = data.get("count", 0)

        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.echo(f"\n📋 State Variables (v{version}): {len(variables)} of {total}\n")

            if not variables:
                typer.secho("  No state variables defined", fg=typer.colors.YELLOW)
            else:
                # Group by category
                categorized = {}
                uncategorized = []
                for var in variables:
                    cat = var.get("category")
                    if cat:
                        categorized.setdefault(cat, []).append(var)
                    else:
                        uncategorized.append(var)

                # Print categorized
                for category, vars_list in sorted(categorized.items()):
                    typer.secho(f"  [{category}]", fg=typer.colors.BLUE)
                    for var in vars_list:
                        _print_state_var(var)

                # Print uncategorized
                if uncategorized:
                    if categorized:
                        typer.secho("  [uncategorized]", fg=typer.colors.BLUE)
                    for var in uncategorized:
                        _print_state_var(var)
    else:
        typer.secho(f"❌ Failed to list state variables", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


def _print_state_var(var: dict):
    """Helper to print a state variable."""
    key = var.get("key", "unknown")
    vtype = var.get("value_type", "unknown")
    default = var.get("default_value")

    type_info = vtype
    if vtype == "enum":
        enum_vals = var.get("enum_values", [])
        type_info = f"enum[{', '.join(enum_vals[:3])}{'...' if len(enum_vals) > 3 else ''}]"

    default_str = f" = {default}" if default is not None else ""

    typer.echo(f"    • {key}: {type_info}{default_str}")
    typer.echo(f"      ID: {var.get('id', 'N/A')}")
    if var.get("description"):
        typer.echo(f"      {var['description'][:60]}...")


@app.command()
def add_state_var(
    story_id: Annotated[str, typer.Argument(help="Story ID")],
    key: Annotated[str, typer.Option("--key", "-k", help="Variable key/name")],
    value_type: Annotated[str, typer.Option("--type", "-t", help="Type: boolean, number, string, enum")],
    default: Annotated[str, typer.Option("--default", "-d", help="Default value")] = None,
    enum_values: Annotated[str, typer.Option("--enum-values", "-e", help="Enum values (comma-separated)")] = None,
    description: Annotated[str, typer.Option("--desc", help="Description")] = None,
    category: Annotated[str, typer.Option("--category", "-c", help="Category for grouping")] = None,
    version: Annotated[int, typer.Option("--version", "-v", help="Story version")] = 1,
    verbose: Annotated[bool, typer.Option("--verbose")] = False
):
    """
    Add a state variable to a story's schema.

    Example:
        python main.py stories add-state-var abc123 --key has_sword --type boolean --default false
        python main.py stories add-state-var abc123 --key courage --type number --default 0 --category stats
        python main.py stories add-state-var abc123 --key faction --type enum --enum-values "rebel,empire,neutral"
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    log(f"Adding state variable '{key}' to story {story_id}")

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    # Build payload
    payload = {
        "key": key,
        "value_type": value_type,
    }

    # Parse default value based on type
    if default is not None:
        if value_type == "boolean":
            payload["default_value"] = default.lower() in ("true", "1", "yes")
        elif value_type == "number":
            try:
                payload["default_value"] = float(default) if "." in default else int(default)
            except ValueError:
                typer.secho(f"❌ Invalid number default: {default}", fg=typer.colors.RED, err=True)
                raise typer.Exit(1)
        else:
            payload["default_value"] = default

    # Parse enum values
    if enum_values:
        payload["enum_values"] = [v.strip() for v in enum_values.split(",")]

    if description:
        payload["description"] = description

    if category:
        payload["category"] = category

    log(f"POST {BASE_URL}/stories/{story_id}/versions/{version}/state-schema")
    log(f"Payload: {json.dumps(payload, indent=2)}")

    response = session.post(
        f"{BASE_URL}/stories/{story_id}/versions/{version}/state-schema",
        json=payload
    )

    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        var = response.json()
        typer.secho("✅ State variable created!", fg=typer.colors.GREEN)
        typer.echo(f"ID: {var.get('id')}")
        typer.echo(f"Key: {var.get('key')}")
        typer.echo(f"Type: {var.get('value_type')}")
        if var.get("default_value") is not None:
            typer.echo(f"Default: {var.get('default_value')}")
        if var.get("enum_values"):
            typer.echo(f"Enum Values: {', '.join(var.get('enum_values'))}")
        if var.get("category"):
            typer.echo(f"Category: {var.get('category')}")
    else:
        typer.secho(f"❌ Failed to create state variable", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def update_state_var(
    story_id: Annotated[str, typer.Argument(help="Story ID")],
    var_id: Annotated[str, typer.Argument(help="Variable ID to update")],
    key: Annotated[str, typer.Option("--key", "-k", help="New variable key")] = None,
    default: Annotated[str, typer.Option("--default", "-d", help="New default value")] = None,
    enum_values: Annotated[str, typer.Option("--enum-values", "-e", help="New enum values (comma-separated)")] = None,
    description: Annotated[str, typer.Option("--desc", help="New description")] = None,
    category: Annotated[str, typer.Option("--category", "-c", help="New category")] = None,
    version: Annotated[int, typer.Option("--version", "-v", help="Story version")] = 1,
    verbose: Annotated[bool, typer.Option("--verbose")] = False
):
    """
    Update a state variable in a story's schema.

    Example:
        python main.py stories update-state-var abc123 var456 --desc "Updated description"
        python main.py stories update-state-var abc123 var456 --default 100 --category "stats"
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    log(f"Updating state variable {var_id}")

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    # Build payload with only provided fields
    payload = {}
    if key is not None:
        payload["key"] = key
    if default is not None:
        # Try to parse as appropriate type
        if default.lower() in ("true", "false"):
            payload["default_value"] = default.lower() == "true"
        else:
            try:
                payload["default_value"] = float(default) if "." in default else int(default)
            except ValueError:
                payload["default_value"] = default
    if enum_values is not None:
        payload["enum_values"] = [v.strip() for v in enum_values.split(",")]
    if description is not None:
        payload["description"] = description
    if category is not None:
        payload["category"] = category

    if not payload:
        typer.secho("⚠️  No fields to update provided", fg=typer.colors.YELLOW)
        raise typer.Exit(0)

    log(f"PUT {BASE_URL}/stories/{story_id}/versions/{version}/state-schema/{var_id}")
    log(f"Payload: {json.dumps(payload, indent=2)}")

    response = session.put(
        f"{BASE_URL}/stories/{story_id}/versions/{version}/state-schema/{var_id}",
        json=payload
    )

    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        var = response.json()
        typer.secho("✅ State variable updated!", fg=typer.colors.GREEN)
        typer.echo(f"Key: {var.get('key')}")
        typer.echo(f"Type: {var.get('value_type')}")
        if var.get("default_value") is not None:
            typer.echo(f"Default: {var.get('default_value')}")
        if var.get("description"):
            typer.echo(f"Description: {var.get('description')}")
    else:
        typer.secho(f"❌ Failed to update state variable", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def delete_state_var(
    story_id: Annotated[str, typer.Argument(help="Story ID")],
    var_id: Annotated[str, typer.Argument(help="Variable ID to delete")],
    version: Annotated[int, typer.Option("--version", "-v", help="Story version")] = 1,
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False
):
    """
    Delete a state variable from a story's schema.

    Example:
        python main.py stories delete-state-var abc123 var456
        python main.py stories delete-state-var abc123 var456 --force
    """

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    if not force:
        typer.secho(f"⚠️  This will delete state variable {var_id}", fg=typer.colors.YELLOW)
        if not typer.confirm("Are you sure?"):
            typer.echo("Cancelled.")
            raise typer.Exit(0)

    response = session.delete(
        f"{BASE_URL}/stories/{story_id}/versions/{version}/state-schema/{var_id}"
    )

    if response.status_code in [200, 204]:
        typer.secho("✅ State variable deleted!", fg=typer.colors.GREEN)
    else:
        typer.secho(f"❌ Failed to delete state variable", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def validate_state_schema(
    story_id: Annotated[str, typer.Argument(help="Story ID")],
    version: Annotated[int, typer.Option("--version", "-v", help="Story version")] = 1,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False
):
    """
    Validate state schema against choices (check for undefined variables).

    Returns list of undefined variables used in choices but not defined in schema.
    Use this before publishing to ensure all state variables are properly defined.

    Example:
        python main.py stories validate-state-schema abc123
        python main.py stories validate-state-schema abc123 --json
    """

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(
        f"{BASE_URL}/stories/{story_id}/versions/{version}/state-schema/validate"
    )

    if response.status_code == 200:
        data = response.json()

        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            is_valid = data.get("is_valid", False)
            defined = data.get("defined_variables", [])
            used = data.get("used_variables", [])
            undefined = data.get("undefined_variables", [])
            errors = data.get("errors", [])

            typer.echo(f"\n🔍 State Schema Validation (v{version}):\n")

            if is_valid:
                typer.secho("  ✅ VALID - All variables are defined!\n", fg=typer.colors.GREEN)
            else:
                typer.secho("  ❌ INVALID - Undefined variables found!\n", fg=typer.colors.RED)

            typer.echo(f"  Defined Variables ({len(defined)}):")
            if defined:
                for v in defined:
                    typer.echo(f"    • {v}")
            else:
                typer.secho("    (none)", fg=typer.colors.YELLOW)

            typer.echo(f"\n  Used in Choices ({len(used)}):")
            if used:
                for v in used:
                    status = "✓" if v in defined else "✗"
                    color = typer.colors.GREEN if v in defined else typer.colors.RED
                    typer.secho(f"    {status} {v}", fg=color)
            else:
                typer.secho("    (none)", fg=typer.colors.YELLOW)

            if undefined:
                typer.echo(f"\n  ⚠️  Undefined Variables ({len(undefined)}):")
                for v in undefined:
                    typer.secho(f"    • {v}", fg=typer.colors.RED)

                typer.echo(f"\n  Errors ({len(errors)}):")
                for err in errors[:10]:  # Show first 10
                    typer.secho(f"    • '{err.get('variable_key')}' in {err.get('used_in')}", fg=typer.colors.RED)
                    typer.echo(f"      Choice: \"{err.get('choice_text', 'N/A')[:40]}...\"")
                    typer.echo(f"      Node: {err.get('from_node_title', 'N/A')}")
                if len(errors) > 10:
                    typer.echo(f"    ... and {len(errors) - 10} more errors")

            typer.echo()

            if not is_valid:
                raise typer.Exit(1)
    else:
        typer.secho(f"❌ Failed to validate state schema", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# ============================================================================
# Story Validation Commands (Graph Structure)
# ============================================================================


@app.command()
def validate(
    story_id: Annotated[str, typer.Argument(help="Story ID to validate")],
    version: Annotated[int, typer.Option("--version", "-v", help="Story version")] = None,
    include_state_schema: Annotated[bool, typer.Option("--include-state-schema/--no-state-schema", help="Include state schema validation")] = True,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    verbose: Annotated[bool, typer.Option("--verbose")] = False,
):
    """
    Validate story graph structure for publishing.

    Checks:
    - At least one node exists
    - Exactly one start node
    - At least one end node
    - All choices point to valid nodes
    - Reachability analysis (warnings)
    - Dead-end detection (warnings)
    - State schema validation (optional)

    Example:
        python main.py stories validate abc123
        python main.py stories validate abc123 --version 2
        python main.py stories validate abc123 --no-state-schema
        python main.py stories validate abc123 --json
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    log(f"Validating story: {story_id}")

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    params = {"include_state_schema": include_state_schema}
    if version is not None:
        params["version"] = version

    log(f"POST {BASE_URL}/stories/{story_id}/validate")
    log(f"Params: {json.dumps(params, indent=2)}")

    response = session.post(
        f"{BASE_URL}/stories/{story_id}/validate",
        params=params
    )

    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()

        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            is_valid = data.get("is_valid", False)
            errors = data.get("errors", [])
            warnings = data.get("warnings", [])
            node_count = data.get("node_count", 0)
            choice_count = data.get("choice_count", 0)
            start_count = data.get("start_node_count", 0)
            end_count = data.get("end_node_count", 0)
            orphan_count = data.get("orphaned_node_count", 0)
            state_validation = data.get("state_schema_validation")

            typer.echo(f"\n🔍 Story Validation Results:\n")

            # Status
            if is_valid:
                typer.secho("  ✅ VALID - Story is ready for publishing!\n", fg=typer.colors.GREEN)
            else:
                typer.secho("  ❌ INVALID - Story has errors that must be fixed\n", fg=typer.colors.RED)

            # Statistics
            typer.echo("  📊 Statistics:")
            typer.echo(f"    • Nodes: {node_count}")
            typer.echo(f"    • Choices: {choice_count}")
            typer.echo(f"    • Start nodes: {start_count}")
            typer.echo(f"    • End nodes: {end_count}")
            if orphan_count > 0:
                typer.secho(f"    • Orphaned nodes: {orphan_count}", fg=typer.colors.YELLOW)

            # Errors
            if errors:
                typer.echo(f"\n  ❌ Errors ({len(errors)}):")
                for err in errors:
                    typer.secho(f"    • {err}", fg=typer.colors.RED)

            # Warnings
            if warnings:
                typer.echo(f"\n  ⚠️  Warnings ({len(warnings)}):")
                for warn in warnings:
                    typer.secho(f"    • {warn}", fg=typer.colors.YELLOW)

            # State schema validation
            if state_validation:
                state_valid = state_validation.get("is_valid", True)
                undefined = state_validation.get("undefined_variables", [])
                if state_valid:
                    typer.secho("\n  ✅ State schema: All variables defined", fg=typer.colors.GREEN)
                else:
                    typer.secho(f"\n  ⚠️  State schema: {len(undefined)} undefined variable(s)", fg=typer.colors.YELLOW)
                    for v in undefined[:5]:
                        typer.echo(f"      • {v}")
                    if len(undefined) > 5:
                        typer.echo(f"      ... and {len(undefined) - 5} more")

            typer.echo()

            if not is_valid:
                raise typer.Exit(1)
    else:
        typer.secho(f"❌ Failed to validate story", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# ============================================================================
# Story Tree Structure Commands
# ============================================================================


@app.command()
def tree(
    story_id: Annotated[str, typer.Argument(help="Story ID")],
    version: Annotated[int, typer.Option("--version", "-v", help="Story version")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    max_depth: Annotated[int, typer.Option("--max-depth", "-d", help="Max depth to display")] = 10,
):
    """
    Display story node tree structure.

    Shows hierarchical tree of nodes starting from start node.
    Orphaned nodes (not reachable from start) are listed separately.

    Example:
        python main.py stories tree abc123
        python main.py stories tree abc123 --version 2
        python main.py stories tree abc123 --max-depth 3
        python main.py stories tree abc123 --json
    """

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    params = {}
    if version is not None:
        params["version"] = version

    response = session.get(
        f"{BASE_URL}/stories/{story_id}/tree",
        params=params
    )

    if response.status_code == 200:
        data = response.json()

        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            root = data.get("root")
            orphaned = data.get("orphaned_nodes", [])
            total = data.get("total_nodes", 0)
            reachable = data.get("reachable_nodes", 0)

            typer.echo(f"\n🌳 Story Tree Structure:\n")
            typer.echo(f"  Total nodes: {total}")
            typer.echo(f"  Reachable: {reachable}")
            if orphaned:
                typer.secho(f"  Orphaned: {len(orphaned)}", fg=typer.colors.YELLOW)
            typer.echo()

            if root:
                _print_tree_node(root, max_depth=max_depth)
            else:
                typer.secho("  No start node found!", fg=typer.colors.RED)

            if orphaned:
                typer.echo()
                typer.secho("  📦 Orphaned Nodes (not reachable from start):", fg=typer.colors.YELLOW)
                for node in orphaned:
                    node_type = ""
                    if node.get("is_end_node"):
                        node_type = " [END]"
                    typer.echo(f"    • {node.get('title', 'Untitled')}{node_type}")
                    typer.echo(f"      ID: {node.get('id', 'N/A')}")

            typer.echo()
    else:
        typer.secho(f"❌ Failed to get story tree", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


def _print_tree_node(node: dict, indent: str = "  ", max_depth: int = 10, current_depth: int = 0):
    """Helper to recursively print tree nodes."""
    if current_depth > max_depth:
        typer.secho(f"{indent}... (max depth reached)", fg=typer.colors.YELLOW)
        return

    title = node.get("title", "Untitled")
    is_start = node.get("is_start_node", False)
    is_end = node.get("is_end_node", False)
    children = node.get("children", [])

    # Build node label
    label = title
    tags = []
    if is_start:
        tags.append("START")
    if is_end:
        tags.append("END")
    if tags:
        label = f"{title} [{', '.join(tags)}]"

    # Color based on node type
    if is_start:
        typer.secho(f"{indent}🚀 {label}", fg=typer.colors.GREEN)
    elif is_end:
        typer.secho(f"{indent}🏁 {label}", fg=typer.colors.BLUE)
    else:
        typer.echo(f"{indent}📄 {label}")

    # Print children
    for i, child in enumerate(children):
        is_last = i == len(children) - 1
        child_indent = indent + ("    " if is_last else "│   ")
        connector = "└── " if is_last else "├── "
        typer.echo(f"{indent}{connector}", nl=False)
        _print_tree_node(child, child_indent, max_depth, current_depth + 1)


if __name__ == "__main__":
    app()
