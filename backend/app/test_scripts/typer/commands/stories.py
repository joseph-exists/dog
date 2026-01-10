"""
Story Management Commands

Commands for creating, managing, and testing CYOA stories in staging environments.
"""
import typer
import json
from typing_extensions import Annotated
from auth_helper import get_authenticated_session

app = typer.Typer(help="Story management commands")

BASE_URL = "http://localhost:8000/api/v1"

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


# ============================================================================
# Story Node Commands
# ============================================================================

@app.command()
def add_node(
    story_id: Annotated[str, typer.Argument(help="Story ID")],
    title: Annotated[str, typer.Option("--title", "-t", help="Node title")],
    content: Annotated[str, typer.Option("--content", "-c", help="Node content")],
    start: Annotated[bool, typer.Option("--start", help="Mark as start node")] = False,
    end: Annotated[bool, typer.Option("--end", help="Mark as end node")] = False,
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
        "story_version": 1,
        "title": title,
        "content": content,
        "node_type": "text",
        "content_format": "text",
        "is_start_node": start,
        "is_end_node": end
    }

    log(f"POST {BASE_URL}/storynodes")
    log(f"Payload: {json.dumps(payload, indent=2)}")

    response = session.post(f"{BASE_URL}/storynodes", json=payload)

    log(f"Response status: {response.status_code}")
    log(f"Response: {response.text[:500]}")

    if response.status_code == 200:
        node = response.json()
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

    payload = {
        "from_node_id": from_node,
        "to_node_id": to_node,
        "text": text,
        "order": order
    }

    log(f"POST {BASE_URL}/node-choices")
    log(f"Payload: {json.dumps(payload, indent=2)}")

    response = session.post(f"{BASE_URL}/node-choices", json=payload)

    log(f"Response status: {response.status_code}")
    log(f"Response: {response.text[:500]}")

    if response.status_code == 200:
        choice = response.json()
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
# Room Integration Commands
# ============================================================================

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


if __name__ == "__main__":
    app()
