import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.tests.utils.archetype import create_random_archetype


def test_create_archetype(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {
        "title": "Test Archetype",
        "description": "A test archetype description"
    }
    response = client.post(
        f"{settings.API_V1_STR}/archetypes/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]
    assert "id" in content


def test_read_archetype(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    archetype = create_random_archetype(db)
    response = client.get(
        f"{settings.API_V1_STR}/archetypes/{archetype.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == archetype.title
    assert content["description"] == archetype.description
    assert content["id"] == str(archetype.id)


def test_read_archetype_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/archetypes/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "archetype not found"


def test_read_archetypes(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    create_random_archetype(db)
    create_random_archetype(db)
    response = client.get(
        f"{settings.API_V1_STR}/archetypes/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) >= 2


def test_update_archetype(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    archetype = create_random_archetype(db)
    data = {
        "title": "Updated Archetype Title",
        "description": "Updated archetype description"
    }
    response = client.put(
        f"{settings.API_V1_STR}/archetypes/{archetype.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]
    assert content["id"] == str(archetype.id)


def test_update_archetype_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {
        "title": "Updated Archetype Title",
        "description": "Updated archetype description"
    }
    response = client.put(
        f"{settings.API_V1_STR}/archetypes/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Archetype not found"


def test_update_archetype_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    archetype = create_random_archetype(db)
    data = {
        "title": "Updated Archetype Title", 
        "description": "Updated archetype description"
    }
    response = client.put(
        f"{settings.API_V1_STR}/archetypes/{archetype.id}",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 400
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def test_delete_archetype(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    archetype = create_random_archetype(db)
    response = client.delete(
        f"{settings.API_V1_STR}/archetypes/{archetype.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["message"] == "Archetype deleted successfully"


def test_delete_archetype_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.delete(
        f"{settings.API_V1_STR}/archetypes/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "archetype not found"


def test_delete_archetype_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    archetype = create_random_archetype(db)
    response = client.delete(
        f"{settings.API_V1_STR}/archetypes/{archetype.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 400
    content = response.json()
    assert content["detail"] == "Not enough permissions"
