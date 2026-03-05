"""
Room Management Commands

Commands for creating and managing chat rooms, participants, and messages.
"""
import typer
import json
from typing_extensions import Annotated
from auth_helper import get_authenticated_session

app = typer.Typer(help="Room management commands")

BASE_URL = "http://localhost:8000/api/v1"

# ============================================================================
# Room CRUD Commands
# ============================================================================

@app.command()
def create(
    title: Annotated[str, typer.Argument(help="Room title")],
    story_id: Annotated[str, typer.Option("--story", "-s", help="Associate with story ID")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False
):
    """
    Create a new room.

    Example:
        python main.py rooms create "Adventure Room"
        python main.py rooms create "Story Room" --story abc123
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    log(f"Creating room: {title}")

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    payload = {
        "title": title
    }
    if story_id:
        payload["story_id"] = story_id

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
        typer.echo(f"Creator ID: {room.get('creator_id', 'N/A')}")
        if story_id:
            typer.echo(f"Story ID: {story_id}")
    else:
        typer.secho(f"❌ Failed to create room", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def list(
    limit: Annotated[int, typer.Option(help="Max rooms to list")] = 20,
    offset: Annotated[int, typer.Option(help="Pagination offset")] = 0,
    json_output: Annotated[bool, typer.Option("--json")] = False
):
    """
    List all rooms for the current user.

    Example:
        python main.py rooms list --limit 10
        python main.py rooms list --json
    """

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(
        f"{BASE_URL}/rooms",
        params={"limit": limit, "offset": offset}
    )

    if response.status_code == 200:
        data = response.json()
        rooms = data.get("data", [])
        total = data.get("count", 0)

        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.echo(f"\n💬 Rooms ({len(rooms)} of {total}):\n")

            if not rooms:
                typer.secho("  No rooms found", fg=typer.colors.YELLOW)
            else:
                for room in rooms:
                    typer.echo(f"  • {room.get('title', 'Untitled')}")
                    typer.echo(f"    ID: {room.get('room_id', 'N/A')}")
                    typer.echo(f"    Created: {room.get('created_at', 'N/A')}")
                    if room.get('story_id'):
                        typer.echo(f"    Story: {room['story_id']}")
                    typer.echo()
    else:
        typer.secho(f"❌ Failed to list rooms", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def get(
    room_id: Annotated[str, typer.Argument(help="Room ID")],
    json_output: Annotated[bool, typer.Option("--json")] = False
):
    """
    Get details for a specific room.

    Example:
        python main.py rooms get abc123
    """

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(f"{BASE_URL}/rooms/{room_id}")

    if response.status_code == 200:
        room = response.json()

        if json_output:
            typer.echo(json.dumps(room, indent=2))
        else:
            typer.echo(f"\n💬 Room Details:\n")
            typer.echo(f"Title: {room.get('title', 'Untitled')}")
            typer.echo(f"Room ID: {room.get('room_id', 'N/A')}")
            typer.echo(f"Creator: {room.get('creator_id', 'N/A')}")
            typer.echo(f"Created: {room.get('created_at', 'N/A')}")
            typer.echo(f"Last Activity: {room.get('last_activity', 'N/A')}")
            if room.get('story_id'):
                typer.echo(f"Story ID: {room['story_id']}")
    else:
        typer.secho(f"❌ Room not found", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def update(
    room_id: Annotated[str, typer.Argument(help="Room ID")],
    title: Annotated[str, typer.Option("--title", "-t", help="New room title")],
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False
):
    """
    Update room metadata.

    Example:
        python main.py rooms update abc123 --title "New Room Name"
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    log(f"Updating room: {room_id}")

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    payload = {
        "title": title
    }

    log(f"PATCH {BASE_URL}/rooms/{room_id}")
    log(f"Payload: {json.dumps(payload, indent=2)}")

    response = session.patch(f"{BASE_URL}/rooms/{room_id}", json=payload)

    log(f"Response status: {response.status_code}")
    log(f"Response: {response.text[:500]}")

    if response.status_code in [200, 201]:
        room = response.json()
        typer.secho("✅ Room updated successfully!", fg=typer.colors.GREEN)
        typer.echo(f"New Title: {room.get('title', 'N/A')}")
    else:
        typer.secho(f"❌ Failed to update room", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def delete(
    room_id: Annotated[str, typer.Argument(help="Room ID")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False
):
    """
    Delete a room (soft delete - marks as inactive).

    Example:
        python main.py rooms delete abc123
        python main.py rooms delete abc123 --force
    """

    # Confirmation prompt (unless --force)
    if not force:
        typer.secho(f"⚠️  This will delete room {room_id}", fg=typer.colors.YELLOW)
        if not typer.confirm("Are you sure?"):
            typer.echo("Cancelled.")
            raise typer.Exit(0)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.delete(f"{BASE_URL}/rooms/{room_id}")

    if response.status_code in [200, 204]:
        typer.secho("✅ Room deleted successfully", fg=typer.colors.GREEN)
    else:
        typer.secho(f"❌ Failed to delete room", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# ============================================================================
# Participant Management Commands
# ============================================================================

@app.command()
def add_participant(
    room_id: Annotated[str, typer.Argument(help="Room ID")],
    participant_id: Annotated[str, typer.Argument(help="Participant ID (user ID or agent name)")],
    participant_type: Annotated[str, typer.Option("--type", "-t", help="Participant type: user or agent")] = "user",
    role: Annotated[str, typer.Option("--role", "-r", help="Role: owner, member, or observer")] = "member",
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False
):
    """
    Add a participant to a room.

    Example:
        python main.py rooms add-participant abc123 user456 --type user --role member
        python main.py rooms add-participant abc123 StoryAdvisor --type agent --role member
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    log(f"Adding participant to room: {room_id}")

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    payload = {
        "participant_id": participant_id,
        "participant_type": participant_type,
        "role": role
    }

    log(f"POST {BASE_URL}/rooms/{room_id}/participants")
    log(f"Payload: {json.dumps(payload, indent=2)}")

    response = session.post(f"{BASE_URL}/rooms/{room_id}/participants", json=payload)

    log(f"Response status: {response.status_code}")
    log(f"Response: {response.text[:500]}")

    if response.status_code in [200, 201]:
        participant = response.json()
        typer.secho("✅ Participant added successfully!", fg=typer.colors.GREEN)
        typer.echo(f"Participant ID: {participant.get('participant_id', 'N/A')}")
        typer.echo(f"Type: {participant.get('participant_type', 'N/A')}")
        typer.echo(f"Role: {participant.get('role', 'N/A')}")
    else:
        typer.secho(f"❌ Failed to add participant", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def list_participants(
    room_id: Annotated[str, typer.Argument(help="Room ID")],
    json_output: Annotated[bool, typer.Option("--json")] = False
):
    """
    List all participants in a room.

    Example:
        python main.py rooms list-participants abc123
    """

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(f"{BASE_URL}/rooms/{room_id}/participants")

    if response.status_code == 200:
        data = response.json()
        participants = data.get("data", [])
        total = data.get("count", 0)

        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.echo(f"\n👥 Participants ({len(participants)} of {total}):\n")

            if not participants:
                typer.secho("  No participants found", fg=typer.colors.YELLOW)
            else:
                for p in participants:
                    active = "✓" if p.get('active') else "✗"
                    typer.echo(f"  {active} {p.get('participant_id', 'Unknown')} ({p.get('participant_type', 'unknown')})")
                    typer.echo(f"    Role: {p.get('role', 'N/A')}")
                    typer.echo(f"    Joined: {p.get('joined_at', 'N/A')}")
                    if not p.get('active') and p.get('left_at'):
                        typer.echo(f"    Left: {p['left_at']}")
                    typer.echo()
    else:
        typer.secho(f"❌ Failed to list participants", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def change_role(
    room_id: Annotated[str, typer.Argument(help="Room ID")],
    participant_id: Annotated[str, typer.Argument(help="Participant ID")],
    new_role: Annotated[str, typer.Argument(help="New role: owner, member, or observer")],
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False
):
    """
    Change a participant's role in a room.

    Example:
        python main.py rooms change-role abc123 user456 owner
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    log(f"Changing participant role: {participant_id} -> {new_role}")

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    payload = {
        "new_role": new_role
    }

    log(f"PATCH {BASE_URL}/rooms/{room_id}/participants/{participant_id}/role")
    log(f"Payload: {json.dumps(payload, indent=2)}")

    response = session.patch(
        f"{BASE_URL}/rooms/{room_id}/participants/{participant_id}/role",
        json=payload
    )

    log(f"Response status: {response.status_code}")
    log(f"Response: {response.text[:500]}")

    if response.status_code in [200, 201]:
        participant = response.json()
        typer.secho("✅ Role changed successfully!", fg=typer.colors.GREEN)
        typer.echo(f"Participant: {participant.get('participant_id', 'N/A')}")
        typer.echo(f"New Role: {participant.get('role', 'N/A')}")
    else:
        typer.secho(f"❌ Failed to change role", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def remove_participant(
    room_id: Annotated[str, typer.Argument(help="Room ID")],
    participant_id: Annotated[str, typer.Argument(help="Participant ID")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False
):
    """
    Remove a participant from a room (soft delete).

    Example:
        python main.py rooms remove-participant abc123 user456
    """

    # Confirmation prompt (unless --force)
    if not force:
        typer.secho(f"⚠️  This will remove {participant_id} from room {room_id}", fg=typer.colors.YELLOW)
        if not typer.confirm("Are you sure?"):
            typer.echo("Cancelled.")
            raise typer.Exit(0)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.delete(f"{BASE_URL}/rooms/{room_id}/participants/{participant_id}")

    if response.status_code in [200, 204]:
        typer.secho("✅ Participant removed successfully", fg=typer.colors.GREEN)
    else:
        typer.secho(f"❌ Failed to remove participant", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# ============================================================================
# Message Commands
# ============================================================================

@app.command()
def send_message(
    room_id: Annotated[str, typer.Argument(help="Room ID")],
    content: Annotated[str, typer.Argument(help="Message content")],
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False
):
    """
    Send a message to a room.

    Example:
        python main.py rooms send-message abc123 "Hello, everyone!"
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    log(f"Sending message to room: {room_id}")

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    payload = {
        "content": content
    }

    log(f"POST {BASE_URL}/rooms/{room_id}/messages")
    log(f"Payload: {json.dumps(payload, indent=2)}")

    response = session.post(f"{BASE_URL}/rooms/{room_id}/messages", json=payload)

    log(f"Response status: {response.status_code}")
    log(f"Response: {response.text[:500]}")

    if response.status_code in [200, 201]:
        message = response.json()
        typer.secho("✅ Message sent successfully!", fg=typer.colors.GREEN)
        typer.echo(f"Message ID: {message.get('message_id', 'N/A')}")
        typer.echo(f"Content: {message.get('content', 'N/A')}")
    else:
        typer.secho(f"❌ Failed to send message", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def list_messages(
    room_id: Annotated[str, typer.Argument(help="Room ID")],
    limit: Annotated[int, typer.Option(help="Max messages to list")] = 20,
    before: Annotated[str, typer.Option(help="Cursor: messages before this timestamp")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False
):
    """
    List messages in a room (with cursor-based pagination).

    Example:
        python main.py rooms list-messages abc123 --limit 10
        python main.py rooms list-messages abc123 --before "2024-01-01T12:00:00"
    """

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    params = {"limit": limit}
    if before:
        params["before"] = before

    response = session.get(f"{BASE_URL}/rooms/{room_id}/messages", params=params)

    if response.status_code == 200:
        data = response.json()
        messages = data.get("data", [])
        total = data.get("count", 0)

        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.echo(f"\n💬 Messages ({len(messages)} of {total}):\n")

            if not messages:
                typer.secho("  No messages found", fg=typer.colors.YELLOW)
            else:
                for msg in messages:
                    sender = msg.get('sender_id', 'Unknown')
                    sender_type = msg.get('sender_type', 'unknown')
                    timestamp = msg.get('created_at', 'N/A')

                    typer.echo(f"  [{timestamp}] {sender} ({sender_type}):")
                    typer.echo(f"    {msg.get('content', '')}")
                    typer.echo()
    else:
        typer.secho(f"❌ Failed to list messages", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
