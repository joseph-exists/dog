"""
User Information Commands

Commands for viewing current user information and their associated data.
"""
import typer
import json
from typing_extensions import Annotated
from auth_helper import get_authenticated_session

app = typer.Typer(help="User information and data commands")

from cli_config import get_api_v1_url

BASE_URL = get_api_v1_url()

# ============================================================================
# User Info Commands
# ============================================================================

@app.command()
def me(
    json_output: Annotated[bool, typer.Option("--json")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False
):
    """
    Get current user information.

    Example:
        python main.py users me
        python main.py users me --json
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    log("Fetching current user info")

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    log(f"GET {BASE_URL}/users/me")
    response = session.get(f"{BASE_URL}/users/me")

    log(f"Response status: {response.status_code}")
    log(f"Response: {response.text[:500]}")

    if response.status_code == 200:
        user = response.json()

        if json_output:
            typer.echo(json.dumps(user, indent=2))
        else:
            typer.echo(f"\n👤 Current User:\n")
            typer.echo(f"ID: {user.get('id', 'N/A')}")
            typer.echo(f"Email: {user.get('email', 'N/A')}")
            typer.echo(f"Full Name: {user.get('full_name', 'N/A')}")
            typer.echo(f"Superuser: {'Yes' if user.get('is_superuser') else 'No'}")
            typer.echo(f"Active: {'Yes' if user.get('is_active', True) else 'No'}")

            if verbose and user.get('created_at'):
                typer.echo(f"Created: {user['created_at']}")
    else:
        typer.secho(f"❌ Failed to get user info", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def whoami():
    """
    Quick current user identification.

    Example:
        python main.py users whoami
    """

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(f"{BASE_URL}/users/me")

    if response.status_code == 200:
        user = response.json()
        typer.echo(f"👤 {user.get('email', 'Unknown')} (ID: {user.get('id', 'N/A')[:8]}...)")
        if user.get('is_superuser'):
            typer.secho("   [Superuser]", fg=typer.colors.YELLOW)
    else:
        typer.secho(f"❌ Failed to identify user", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)


# ============================================================================
# User's Data Commands
# ============================================================================

@app.command()
def my_rooms(
    limit: Annotated[int, typer.Option(help="Max rooms to list")] = 20,
    json_output: Annotated[bool, typer.Option("--json")] = False
):
    """
    List your rooms.

    Example:
        python main.py users my-rooms
        python main.py users my-rooms --limit 10
    """

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(
        f"{BASE_URL}/rooms",
        params={"limit": limit}
    )

    if response.status_code == 200:
        data = response.json()
        rooms = data.get("data", [])
        total = data.get("count", 0)

        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.echo(f"\n💬 Your Rooms ({len(rooms)} of {total}):\n")

            if not rooms:
                typer.secho("  No rooms found", fg=typer.colors.YELLOW)
                typer.echo("  Create one with: rooms create \"Room Name\"")
            else:
                for room in rooms:
                    typer.echo(f"  • {room.get('title', 'Untitled')}")
                    typer.echo(f"    ID: {room.get('room_id', 'N/A')}")
                    typer.echo(f"    Created: {room.get('created_at', 'N/A')}")
                    if room.get('story_id'):
                        typer.echo(f"    Story: {room['story_id'][:8]}...")
                    typer.echo()
    else:
        typer.secho(f"❌ Failed to list rooms", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def my_personas(
    limit: Annotated[int, typer.Option(help="Max personas to list")] = 50,
    json_output: Annotated[bool, typer.Option("--json")] = False
):
    """
    List your user-personas.

    Example:
        python main.py users my-personas
        python main.py users my-personas --limit 10
    """

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(
        f"{BASE_URL}/user-personas",
        params={"limit": limit}
    )

    if response.status_code == 200:
        data = response.json()
        personas = data.get("data", [])
        total = data.get("count", 0)

        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.echo(f"\n🎮 Your Personas ({len(personas)} of {total}):\n")

            if not personas:
                typer.secho("  No user-personas found", fg=typer.colors.YELLOW)
                typer.echo("  Create one with: personas create-user-persona <persona-id>")
            else:
                for up in personas:
                    typer.echo(f"  • User-Persona ID: {up['id'][:8]}...")
                    typer.echo(f"    Template: {up.get('persona_id', 'N/A')[:8]}...")
                    typer.echo()
    else:
        typer.secho(f"❌ Failed to list user-personas", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def my_stories(
    limit: Annotated[int, typer.Option(help="Max stories to list")] = 20,
    json_output: Annotated[bool, typer.Option("--json")] = False
):
    """
    List your stories.

    Example:
        python main.py users my-stories
        python main.py users my-stories --limit 10
    """

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(
        f"{BASE_URL}/stories",
        params={"limit": limit}
    )

    if response.status_code == 200:
        data = response.json()
        stories = data.get("data", [])
        total = data.get("count", 0)

        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.echo(f"\n📚 Your Stories ({len(stories)} of {total}):\n")

            if not stories:
                typer.secho("  No stories found", fg=typer.colors.YELLOW)
                typer.echo("  Create one with: stories create \"Story Title\"")
            else:
                for story in stories:
                    pub_status = "✓" if story.get('is_published') else "○"
                    typer.echo(f"  {pub_status} {story['title']}")
                    typer.echo(f"    ID: {story['id'][:8]}...")
                    typer.echo(f"    Version: {story.get('current_version', 'N/A')}")
                    if story.get('is_published'):
                        typer.echo(f"    Published: v{story.get('published_version', 'N/A')}")
                    typer.echo()
    else:
        typer.secho(f"❌ Failed to list stories", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def my_progress(
    user_persona_id: Annotated[str, typer.Argument(help="User-persona ID")],
    story_id: Annotated[str, typer.Argument(help="Story ID")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False
):
    """
    Get your story progress for a specific user-persona and story.

    Example:
        python main.py users my-progress user_persona123 story456
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    log(f"Fetching progress: user-persona={user_persona_id}, story={story_id}")

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    log(f"GET {BASE_URL}/user-personas/{user_persona_id}/stories/{story_id}")
    response = session.get(f"{BASE_URL}/user-personas/{user_persona_id}/stories/{story_id}")

    log(f"Response status: {response.status_code}")
    log(f"Response: {response.text[:500]}")

    if response.status_code == 200:
        progress = response.json()

        if json_output:
            typer.echo(json.dumps(progress, indent=2))
        else:
            typer.echo(f"\n📊 Story Progress:\n")
            typer.echo(f"Progress ID: {progress.get('id', 'N/A')[:8]}...")
            typer.echo(f"User-Persona: {progress.get('user_persona_id', 'N/A')[:8]}...")
            typer.echo(f"Story: {progress.get('story_id', 'N/A')[:8]}...")
            typer.echo(f"Story Version: {progress.get('story_version', 'N/A')}")
            typer.echo(f"Head Version: {progress.get('head_version', 'N/A')}")

            if progress.get('head_choice_id'):
                typer.echo(f"Current Choice: {progress['head_choice_id'][:8]}...")
            else:
                typer.echo("Current Position: Start of story")

            story_state = progress.get('story_state', {})
            if story_state:
                typer.echo(f"\nStory State:")
                for key, value in story_state.items():
                    typer.echo(f"  {key}: {value}")
            else:
                typer.echo("\nNo story state yet")

            if progress.get('created_at'):
                typer.echo(f"\nStarted: {progress['created_at']}")
            if progress.get('updated_at'):
                typer.echo(f"Last Updated: {progress['updated_at']}")
    else:
        typer.secho(f"❌ Failed to get progress", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")

        if response.status_code == 404:
            typer.echo("\n💡 Tip: Story progress doesn't exist yet. Start playing with:")
            typer.echo(f"   POST /user-personas/{user_persona_id}/stories/{story_id}")

        raise typer.Exit(1)


@app.command()
def my_timeline(
    user_persona_id: Annotated[str, typer.Argument(help="User-persona ID")],
    story_id: Annotated[str, typer.Argument(help="Story ID")],
    json_output: Annotated[bool, typer.Option("--json")] = False
):
    """
    Get your story timeline (history of choices made).

    Example:
        python main.py users my-timeline user_persona123 story456
    """

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(
        f"{BASE_URL}/user-personas/{user_persona_id}/stories/{story_id}/timeline"
    )

    if response.status_code == 200:
        timeline = response.json()

        if json_output:
            typer.echo(json.dumps(timeline, indent=2))
        else:
            events = timeline.get('events', [])
            head_version = timeline.get('head_version', 0)

            typer.echo(f"\n📜 Story Timeline (Head Version: {head_version}):\n")

            if not events:
                typer.secho("  No events in timeline", fg=typer.colors.YELLOW)
            else:
                for i, event in enumerate(events, 1):
                    event_type = event.get('event_type', 'unknown')

                    if event_type == 'story_start':
                        typer.echo(f"  {i}. 🏁 Story Start")
                    elif event_type == 'choice':
                        choice_text = event.get('choice_text', 'Unknown choice')
                        typer.echo(f"  {i}. ➡️  {choice_text}")
                        if event.get('choice_id'):
                            typer.echo(f"      Choice ID: {event['choice_id'][:8]}...")

                    if event.get('timestamp'):
                        typer.echo(f"      Time: {event['timestamp']}")

                    typer.echo()
    else:
        typer.secho(f"❌ Failed to get timeline", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def summary(
    json_output: Annotated[bool, typer.Option("--json")] = False
):
    """
    Get a summary of all your data (rooms, personas, stories).

    Example:
        python main.py users summary
    """

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    # Fetch all user data
    user_response = session.get(f"{BASE_URL}/users/me")
    rooms_response = session.get(f"{BASE_URL}/rooms", params={"limit": 100})
    personas_response = session.get(f"{BASE_URL}/user-personas", params={"limit": 100})
    stories_response = session.get(f"{BASE_URL}/stories", params={"limit": 100})

    if user_response.status_code != 200:
        typer.secho(f"❌ Failed to get user info", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    user = user_response.json()
    rooms = rooms_response.json().get('data', []) if rooms_response.status_code == 200 else []
    personas = personas_response.json().get('data', []) if personas_response.status_code == 200 else []
    stories = stories_response.json().get('data', []) if stories_response.status_code == 200 else []

    published_stories = [s for s in stories if s.get('is_published')]
    draft_stories = [s for s in stories if not s.get('is_published')]

    summary_data = {
        "user": {
            "email": user.get('email'),
            "id": user.get('id'),
            "is_superuser": user.get('is_superuser', False)
        },
        "counts": {
            "rooms": len(rooms),
            "user_personas": len(personas),
            "stories": len(stories),
            "published_stories": len(published_stories),
            "draft_stories": len(draft_stories)
        }
    }

    if json_output:
        typer.echo(json.dumps(summary_data, indent=2))
    else:
        typer.echo(f"\n📊 Account Summary:\n")
        typer.echo(f"User: {user.get('email', 'Unknown')}")
        typer.echo(f"ID: {user.get('id', 'N/A')[:8]}...")
        if user.get('is_superuser'):
            typer.secho("Status: Superuser", fg=typer.colors.YELLOW)

        typer.echo(f"\n📈 Statistics:")
        typer.echo(f"  💬 Rooms: {len(rooms)}")
        typer.echo(f"  🎮 User-Personas: {len(personas)}")
        typer.echo(f"  📚 Stories: {len(stories)}")
        typer.echo(f"     ✓ Published: {len(published_stories)}")
        typer.echo(f"     ○ Drafts: {len(draft_stories)}")


if __name__ == "__main__":
    app()
