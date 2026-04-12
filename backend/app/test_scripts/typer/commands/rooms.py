"""
Room Management Commands

Commands for creating and managing chat rooms, participants, and messages.
"""
import typer
import json
from pathlib import Path
import sys
from typing_extensions import Annotated
from auth_helper import get_authenticated_session

app = typer.Typer(help="Room management commands")

from cli_config import get_api_v1_url

BASE_URL = get_api_v1_url()
TEST_SCRIPTS_ROOT = Path(__file__).resolve().parents[2]
if str(TEST_SCRIPTS_ROOT) not in sys.path:
    sys.path.append(str(TEST_SCRIPTS_ROOT))

from rooms.hermes_workspace_roundtrip import (
    HermesWorkspaceRoundTripConfig,
    HermesWorkspaceRoundTripError,
    run_hermes_workspace_roundtrip,
)

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


# ============================================================================
# Room Runtime Commands
# ============================================================================

@app.command()
def runtime_get(
    room_id: Annotated[str, typer.Argument(help="Room ID")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """Get room runtime projection."""
    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(f"{BASE_URL}/rooms/{room_id}/runtime")

    if response.status_code == 200:
        data = response.json()
        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.echo(f"\n🧩 Room Runtime:\n")
            typer.echo(f"Room ID: {data.get('room_id')}")
            typer.echo(f"Story ID: {data.get('story_id')}")
            typer.echo(f"Version: {data.get('story_version')}")
            typer.echo(f"Revision: {data.get('revision')}")
    else:
        typer.secho("❌ Failed to read room runtime", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def runtime_put(
    room_id: Annotated[str, typer.Argument(help="Room ID")],
    user_persona_id: Annotated[str, typer.Option("--user-persona-id", help="User persona ID")] = None,
    story_version: Annotated[int | None, typer.Option("--story-version", help="Story version override")] = None,
    expected_revision: Annotated[int | None, typer.Option("--expected-revision", help="Optimistic revision check")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """Initialize or reset a room runtime."""
    if not user_persona_id:
        typer.secho("❌ --user-persona-id is required", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    payload = {
        "user_persona_id": user_persona_id,
        "story_version": story_version,
        "expected_revision": expected_revision,
    }
    payload = {k: v for k, v in payload.items() if v is not None}

    response = session.put(
        f"{BASE_URL}/rooms/{room_id}/runtime",
        json=payload,
    )

    if response.status_code == 200:
        data = response.json()
        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.secho("✅ Room runtime initialized!", fg=typer.colors.GREEN)
            typer.echo(f"Revision: {data.get('revision')}")
    else:
        typer.secho("❌ Failed to put room runtime", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def runtime_advance(
    room_id: Annotated[str, typer.Argument(help="Room ID")],
    choice_id: Annotated[str, typer.Option("--choice-id", help="Choice ID")] = None,
    expected_revision: Annotated[int | None, typer.Option("--expected-revision", help="Optimistic revision check")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """Advance room runtime by choosing a path."""
    if not choice_id:
        typer.secho("❌ --choice-id is required", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    payload = {"choice_id": choice_id, "expected_revision": expected_revision}
    payload = {k: v for k, v in payload.items() if v is not None}

    response = session.post(
        f"{BASE_URL}/rooms/{room_id}/runtime/advance",
        json=payload,
    )

    if response.status_code == 200:
        data = response.json()
        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.secho("✅ Room runtime advanced!", fg=typer.colors.GREEN)
            typer.echo(f"Revision: {data.get('revision')}")
    else:
        typer.secho("❌ Failed to advance room runtime", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def runtime_rewind(
    room_id: Annotated[str, typer.Argument(help="Room ID")],
    target_choice_id: Annotated[str, typer.Option("--target-choice-id", help="Target choice ID")] = None,
    expected_revision: Annotated[int | None, typer.Option("--expected-revision", help="Optimistic revision check")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """Rewind room runtime to a prior choice."""
    if not target_choice_id:
        typer.secho("❌ --target-choice-id is required", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    payload = {
        "target_choice_id": target_choice_id,
        "expected_revision": expected_revision,
    }
    payload = {k: v for k, v in payload.items() if v is not None}

    response = session.post(
        f"{BASE_URL}/rooms/{room_id}/runtime/rewind",
        json=payload,
    )

    if response.status_code == 200:
        data = response.json()
        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.secho("✅ Room runtime rewound!", fg=typer.colors.GREEN)
            typer.echo(f"Revision: {data.get('revision')}")
    else:
        typer.secho("❌ Failed to rewind room runtime", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def runtime_reset(
    room_id: Annotated[str, typer.Argument(help="Room ID")],
    expected_revision: Annotated[int | None, typer.Option("--expected-revision", help="Optimistic revision check")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """Reset room runtime to story start."""
    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    payload = {"expected_revision": expected_revision}
    payload = {k: v for k, v in payload.items() if v is not None}

    response = session.post(
        f"{BASE_URL}/rooms/{room_id}/runtime/reset",
        json=payload,
    )

    if response.status_code == 200:
        data = response.json()
        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.secho("✅ Room runtime reset!", fg=typer.colors.GREEN)
            typer.echo(f"Revision: {data.get('revision')}")
    else:
        typer.secho("❌ Failed to reset room runtime", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command("hermes-roundtrip")
def hermes_roundtrip(
    workspace_name: Annotated[str, typer.Option("--workspace-name", help="Workspace name")] = "Hermes API Validation Workspace",
    room_title: Annotated[str, typer.Option("--room-title", help="Room title")] = "Hermes API Validation Room",
    prompt: Annotated[str, typer.Option("--prompt", help="Prompt sent through room workspace runtime")] = (
        "Reply with exactly: HERMES_ROOM_RUNTIME_OK. Do not add any other words."
    ),
    timeout_seconds: Annotated[int, typer.Option("--timeout-seconds", help="Overall readiness timeout")] = 240,
    poll_interval_seconds: Annotated[float, typer.Option("--poll-interval-seconds", help="Polling interval")] = 3.0,
    cleanup: Annotated[bool, typer.Option("--cleanup", help="Destroy created room and workspace when finished")] = False,
    output_file: Annotated[str, typer.Option("--output-file", help="JSON output file; use 'none' to disable")] = str(
        TEST_SCRIPTS_ROOT / "rooms" / "test_results_hermes_workspace_roundtrip.json"
    ),
):
    """Provision a Hermes workspace, attach it to a room, and validate one runtime round trip."""
    output_path = None if output_file.lower() == "none" else Path(output_file)
    config = HermesWorkspaceRoundTripConfig(
        base_url=BASE_URL.removesuffix("/api/v1"),
        workspace_name=workspace_name,
        room_title=room_title,
        prompt=prompt,
        timeout_seconds=timeout_seconds,
        poll_interval_seconds=poll_interval_seconds,
        cleanup=cleanup,
        output_file=output_path,
    )
    try:
        result = run_hermes_workspace_roundtrip(config, verbose=True)
    except HermesWorkspaceRoundTripError as exc:
        typer.secho(f"❌ Hermes round trip failed: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc
    except Exception as exc:
        typer.secho(f"❌ Hermes round trip could not start: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1) from exc

    typer.secho("✅ Hermes room/runtime round trip succeeded!", fg=typer.colors.GREEN)
    typer.echo(f"Workspace ID: {result['workspace']['id']}")
    typer.echo(f"Room ID: {result['room']['id']}")
    typer.echo(f"Runtime output: {result['invocation']['output_text']}")
    if output_path is not None:
        typer.echo(f"Result file: {output_path}")


if __name__ == "__main__":
    app()
