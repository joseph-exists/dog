"""
Persona & Character System Commands

Commands for managing archetypes, traits, qualities, personas, and user-personas.
"""
import typer
import json
from typing_extensions import Annotated
from auth_helper import get_authenticated_session

app = typer.Typer(help="Persona and character system commands")

BASE_URL = "http://localhost:8000/api/v1"

# ============================================================================
# Archetype Commands
# ============================================================================

@app.command()
def create_archetype(
    name: Annotated[str, typer.Argument(help="Archetype name")],
    description: Annotated[str, typer.Option("--desc", "-d", help="Description")] = "",
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False
):
    """
    Create a new archetype.

    Example:
        python main.py personas create-archetype "The Warrior" --desc "Brave and strong"
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    log(f"Creating archetype: {name}")

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    payload = {
        "name": name,
        "description": description
    }

    log(f"POST {BASE_URL}/archetypes")
    log(f"Payload: {json.dumps(payload, indent=2)}")

    response = session.post(f"{BASE_URL}/archetypes", json=payload)

    log(f"Response status: {response.status_code}")
    log(f"Response: {response.text[:500]}")

    if response.status_code in [200, 201]:
        archetype = response.json()
        typer.secho("✅ Archetype created successfully!", fg=typer.colors.GREEN)
        typer.echo(f"ID: {archetype['id']}")
        typer.echo(f"Name: {archetype['name']}")
        if archetype.get('description'):
            typer.echo(f"Description: {archetype['description']}")
    else:
        typer.secho(f"❌ Failed to create archetype", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def list_archetypes(
    limit: Annotated[int, typer.Option(help="Max archetypes to list")] = 20,
    offset: Annotated[int, typer.Option(help="Pagination offset")] = 0,
    json_output: Annotated[bool, typer.Option("--json")] = False
):
    """
    List all archetypes.

    Example:
        python main.py personas list-archetypes
    """

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(
        f"{BASE_URL}/archetypes",
        params={"limit": limit, "offset": offset}
    )

    if response.status_code == 200:
        data = response.json()
        archetypes = data.get("data", [])
        total = data.get("count", 0)

        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.echo(f"\n🎭 Archetypes ({len(archetypes)} of {total}):\n")

            if not archetypes:
                typer.secho("  No archetypes found", fg=typer.colors.YELLOW)
            else:
                for archetype in archetypes:
                    typer.echo(f"  • {archetype['name']}")
                    typer.echo(f"    ID: {archetype['id']}")
                    if archetype.get('description'):
                        typer.echo(f"    Desc: {archetype['description'][:60]}...")
                    typer.echo()
    else:
        typer.secho(f"❌ Failed to list archetypes", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# ============================================================================
# Trait Commands
# ============================================================================

@app.command()
def create_trait(
    name: Annotated[str, typer.Argument(help="Trait name")],
    description: Annotated[str, typer.Option("--desc", "-d", help="Description")] = "",
    archetype_id: Annotated[str, typer.Option("--archetype", "-a", help="Archetype ID")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False
):
    """
    Create a new trait.

    Example:
        python main.py personas create-trait "Brave" --desc "Faces danger without fear"
        python main.py personas create-trait "Analytical" --archetype abc123
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    log(f"Creating trait: {name}")

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    payload = {
        "name": name,
        "description": description
    }
    if archetype_id:
        payload["archetype_id"] = archetype_id

    log(f"POST {BASE_URL}/traits")
    log(f"Payload: {json.dumps(payload, indent=2)}")

    response = session.post(f"{BASE_URL}/traits", json=payload)

    log(f"Response status: {response.status_code}")
    log(f"Response: {response.text[:500]}")

    if response.status_code in [200, 201]:
        trait = response.json()
        typer.secho("✅ Trait created successfully!", fg=typer.colors.GREEN)
        typer.echo(f"ID: {trait['id']}")
        typer.echo(f"Name: {trait['name']}")
    else:
        typer.secho(f"❌ Failed to create trait", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def list_traits(
    limit: Annotated[int, typer.Option(help="Max traits to list")] = 50,
    offset: Annotated[int, typer.Option(help="Pagination offset")] = 0,
    json_output: Annotated[bool, typer.Option("--json")] = False
):
    """
    List all traits.

    Example:
        python main.py personas list-traits --limit 20
    """

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(
        f"{BASE_URL}/traits",
        params={"limit": limit, "offset": offset}
    )

    if response.status_code == 200:
        data = response.json()
        traits = data.get("data", [])
        total = data.get("count", 0)

        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.echo(f"\n✨ Traits ({len(traits)} of {total}):\n")

            if not traits:
                typer.secho("  No traits found", fg=typer.colors.YELLOW)
            else:
                for trait in traits:
                    typer.echo(f"  • {trait['name']}")
                    typer.echo(f"    ID: {trait['id']}")
                    if trait.get('description'):
                        typer.echo(f"    Desc: {trait['description'][:60]}...")
                    typer.echo()
    else:
        typer.secho(f"❌ Failed to list traits", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# ============================================================================
# Quality Commands
# ============================================================================

@app.command()
def create_quality(
    name: Annotated[str, typer.Argument(help="Quality name")],
    description: Annotated[str, typer.Option("--desc", "-d", help="Description")] = "",
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False
):
    """
    Create a new quality.

    Example:
        python main.py personas create-quality "Strength" --desc "Physical power"
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    log(f"Creating quality: {name}")

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    payload = {
        "name": name,
        "description": description
    }

    log(f"POST {BASE_URL}/qualities")
    log(f"Payload: {json.dumps(payload, indent=2)}")

    response = session.post(f"{BASE_URL}/qualities", json=payload)

    log(f"Response status: {response.status_code}")
    log(f"Response: {response.text[:500]}")

    if response.status_code in [200, 201]:
        quality = response.json()
        typer.secho("✅ Quality created successfully!", fg=typer.colors.GREEN)
        typer.echo(f"ID: {quality['id']}")
        typer.echo(f"Name: {quality['name']}")
    else:
        typer.secho(f"❌ Failed to create quality", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def list_qualities(
    limit: Annotated[int, typer.Option(help="Max qualities to list")] = 20,
    offset: Annotated[int, typer.Option(help="Pagination offset")] = 0,
    json_output: Annotated[bool, typer.Option("--json")] = False
):
    """
    List all qualities.

    Example:
        python main.py personas list-qualities
    """

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(
        f"{BASE_URL}/qualities",
        params={"limit": limit, "offset": offset}
    )

    if response.status_code == 200:
        data = response.json()
        qualities = data.get("data", [])
        total = data.get("count", 0)

        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.echo(f"\n⭐ Qualities ({len(qualities)} of {total}):\n")

            if not qualities:
                typer.secho("  No qualities found", fg=typer.colors.YELLOW)
            else:
                for quality in qualities:
                    typer.echo(f"  • {quality['name']}")
                    typer.echo(f"    ID: {quality['id']}")
                    if quality.get('description'):
                        typer.echo(f"    Desc: {quality['description'][:60]}...")
                    typer.echo()
    else:
        typer.secho(f"❌ Failed to list qualities", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# ============================================================================
# Persona Commands
# ============================================================================

@app.command()
def create_persona(
    name: Annotated[str, typer.Argument(help="Persona name")],
    description: Annotated[str, typer.Option("--desc", "-d", help="Description")] = "",
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False
):
    """
    Create a new persona.

    Example:
        python main.py personas create-persona "The Wanderer" --desc "A lone traveler"
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    log(f"Creating persona: {name}")

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    payload = {
        "name": name,
        "description": description
    }

    log(f"POST {BASE_URL}/personas")
    log(f"Payload: {json.dumps(payload, indent=2)}")

    response = session.post(f"{BASE_URL}/personas", json=payload)

    log(f"Response status: {response.status_code}")
    log(f"Response: {response.text[:500]}")

    if response.status_code in [200, 201]:
        persona = response.json()
        typer.secho("✅ Persona created successfully!", fg=typer.colors.GREEN)
        typer.echo(f"ID: {persona['id']}")
        typer.echo(f"Name: {persona['name']}")
    else:
        typer.secho(f"❌ Failed to create persona", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def create_persona_from_archetype(
    archetype_id: Annotated[str, typer.Argument(help="Archetype ID")],
    name: Annotated[str, typer.Option("--name", "-n", help="Persona name")],
    description: Annotated[str, typer.Option("--desc", "-d", help="Description")] = "",
    long_desc: Annotated[str, typer.Option("--long-desc", "-l", help="Long description")] = "",
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False
):
    """
    Create a new persona from an archetype (inherits traits).

    Example:
        python main.py personas create-persona-from-archetype abc123 \
          --name "The Sage" \
          --desc "Seeks wisdom"
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    log(f"Creating persona from archetype: {archetype_id}")

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    payload = {
        "name": name,
        "description": description
    }
    if long_desc:
        payload["long_description"] = long_desc

    log(f"POST {BASE_URL}/personas/from-archetype/{archetype_id}")
    log(f"Payload: {json.dumps(payload, indent=2)}")

    response = session.post(
        f"{BASE_URL}/personas/from-archetype/{archetype_id}",
        json=payload
    )

    log(f"Response status: {response.status_code}")
    log(f"Response: {response.text[:500]}")

    if response.status_code in [200, 201]:
        persona = response.json()
        typer.secho("✅ Persona created from archetype!", fg=typer.colors.GREEN)
        typer.echo(f"ID: {persona['id']}")
        typer.echo(f"Name: {persona['name']}")
        typer.echo(f"Archetype ID: {archetype_id}")
        typer.secho("  (Traits inherited from archetype)", fg=typer.colors.CYAN)
    else:
        typer.secho(f"❌ Failed to create persona", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def list_personas(
    limit: Annotated[int, typer.Option(help="Max personas to list")] = 50,
    offset: Annotated[int, typer.Option(help="Pagination offset")] = 0,
    json_output: Annotated[bool, typer.Option("--json")] = False
):
    """
    List all personas.

    Example:
        python main.py personas list-personas --limit 20
    """

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(
        f"{BASE_URL}/personas",
        params={"limit": limit, "offset": offset}
    )

    if response.status_code == 200:
        data = response.json()
        personas = data.get("data", [])
        total = data.get("count", 0)

        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.echo(f"\n👤 Personas ({len(personas)} of {total}):\n")

            if not personas:
                typer.secho("  No personas found", fg=typer.colors.YELLOW)
            else:
                for persona in personas:
                    typer.echo(f"  • {persona['name']}")
                    typer.echo(f"    ID: {persona['id']}")
                    if persona.get('description'):
                        typer.echo(f"    Desc: {persona['description'][:60]}...")
                    typer.echo()
    else:
        typer.secho(f"❌ Failed to list personas", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def get_persona(
    persona_id: Annotated[str, typer.Argument(help="Persona ID")],
    json_output: Annotated[bool, typer.Option("--json")] = False
):
    """
    Get details for a specific persona.

    Example:
        python main.py personas get-persona abc123
    """

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(f"{BASE_URL}/personas/{persona_id}")

    if response.status_code == 200:
        persona = response.json()

        if json_output:
            typer.echo(json.dumps(persona, indent=2))
        else:
            typer.echo(f"\n👤 Persona Details:\n")
            typer.echo(f"Name: {persona['name']}")
            typer.echo(f"ID: {persona['id']}")
            if persona.get('description'):
                typer.echo(f"\nDescription:\n{persona['description']}")
            if persona.get('long_description'):
                typer.echo(f"\nLong Description:\n{persona['long_description']}")
    else:
        typer.secho(f"❌ Persona not found", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# ============================================================================
# UserPersona Commands
# ============================================================================

@app.command()
def create_user_persona(
    persona_id: Annotated[str, typer.Argument(help="Persona template ID")],
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False
):
    """
    Create a user-persona (user's instance of a persona for gameplay).

    Example:
        python main.py personas create-user-persona abc123
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    log(f"Creating user-persona from template: {persona_id}")

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    payload = {
        "persona_id": persona_id
    }

    log(f"POST {BASE_URL}/user-personas")
    log(f"Payload: {json.dumps(payload, indent=2)}")

    response = session.post(f"{BASE_URL}/user-personas", json=payload)

    log(f"Response status: {response.status_code}")
    log(f"Response: {response.text[:500]}")

    if response.status_code in [200, 201]:
        user_persona = response.json()
        typer.secho("✅ User-persona created successfully!", fg=typer.colors.GREEN)
        typer.echo(f"User-Persona ID: {user_persona['id']}")
        typer.echo(f"Template Persona ID: {persona_id}")
        typer.echo(f"User ID: {user_persona.get('user_id', 'N/A')}")
    else:
        typer.secho(f"❌ Failed to create user-persona", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def list_user_personas(
    limit: Annotated[int, typer.Option(help="Max user-personas to list")] = 50,
    offset: Annotated[int, typer.Option(help="Pagination offset")] = 0,
    json_output: Annotated[bool, typer.Option("--json")] = False
):
    """
    List user's personas.

    Example:
        python main.py personas list-user-personas
    """

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(
        f"{BASE_URL}/user-personas",
        params={"limit": limit, "offset": offset}
    )

    if response.status_code == 200:
        data = response.json()
        user_personas = data.get("data", [])
        total = data.get("count", 0)

        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.echo(f"\n🎮 Your Personas ({len(user_personas)} of {total}):\n")

            if not user_personas:
                typer.secho("  No user-personas found", fg=typer.colors.YELLOW)
                typer.echo("  Create one with: personas create-user-persona <persona-id>")
            else:
                for up in user_personas:
                    typer.echo(f"  • User-Persona ID: {up['id']}")
                    typer.echo(f"    Template: {up.get('persona_id', 'N/A')}")
                    typer.echo(f"    User: {up.get('user_id', 'N/A')}")
                    typer.echo()
    else:
        typer.secho(f"❌ Failed to list user-personas", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def get_user_persona(
    user_persona_id: Annotated[str, typer.Argument(help="User-persona ID")],
    json_output: Annotated[bool, typer.Option("--json")] = False
):
    """
    Get details for a specific user-persona.

    Example:
        python main.py personas get-user-persona abc123
    """

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(f"{BASE_URL}/user-personas/{user_persona_id}")

    if response.status_code == 200:
        user_persona = response.json()

        if json_output:
            typer.echo(json.dumps(user_persona, indent=2))
        else:
            typer.echo(f"\n🎮 User-Persona Details:\n")
            typer.echo(f"User-Persona ID: {user_persona['id']}")
            typer.echo(f"Template Persona ID: {user_persona.get('persona_id', 'N/A')}")
            typer.echo(f"User ID: {user_persona.get('user_id', 'N/A')}")
    else:
        typer.secho(f"❌ User-persona not found", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
