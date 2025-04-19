import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.tests.utils.persona import create_random_persona
from app.tests.utils.archetype import create_random_archetype


def test_create_persona(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    # Create an archetype first
    archetype = create_random_archetype(db)
    
    data = {
        "title": "Test Persona",
        "description": "A test persona description",
        "archetype_id": str(archetype.id)
    }
    response = client.post(
        f"{settings.API_V1_STR}/personas/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]
    assert "id" in content


def test_read_persona(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    persona = create_random_persona(db)
    response = client.get(
        f"{settings.API_V1_STR}/personas/{persona.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == persona.title
    assert content["description"] == persona.description
    assert content["id"] == str(persona.id)


def test_read_persona_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/personas/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "persona not found"


def test_read_persona_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    persona = create_random_persona(db)
    response = client.get(
        f"{settings.API_V1_STR}/personas/{persona.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 400
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def test_read_personas(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    create_random_persona(db)
    create_random_persona(db)
    response = client.get(
        f"{settings.API_V1_STR}/personas/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) >= 2


def test_update_persona(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    persona = create_random_persona(db)
    data = {
        "title": "Updated Persona Title",
        "description": "Updated persona description"
    }
    response = client.put(
        f"{settings.API_V1_STR}/personas/{persona.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]
    assert content["id"] == str(persona.id)


def test_update_persona_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {
        "title": "Updated Persona Title",
        "description": "Updated persona description"
    }
    response = client.put(
        f"{settings.API_V1_STR}/personas/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Persona not found"


def test_update_persona_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    persona = create_random_persona(db)
    data = {
        "title": "Updated Persona Title", 
        "description": "Updated persona description"
    }
    response = client.put(
        f"{settings.API_V1_STR}/personas/{persona.id}",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 400
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def test_delete_persona(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    persona = create_random_persona(db)
    response = client.delete(
        f"{settings.API_V1_STR}/personas/{persona.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["message"] == "Persona deleted successfully"


def test_delete_persona_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.delete(
        f"{settings.API_V1_STR}/personas/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "persona not found"


def test_delete_persona_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    persona = create_random_persona(db)
    response = client.delete(
        f"{settings.API_V1_STR}/personas/{persona.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 400
    content = response.json()
    assert content["detail"] == "Not enough permissions"
