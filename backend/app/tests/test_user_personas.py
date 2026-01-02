import pytest
from sqlmodel import Session, select
from fastapi.testclient import TestClient

from app.models import User, Persona, UserPersona

def test_create_user_persona(client: TestClient, session: Session, test_user: User, test_persona: Persona):
    # Create a UserPersona
    user_persona = UserPersona(
        user_id=test_user.id,
        persona_id=test_persona.id,
        nickname="Test Nickname"
    )
    session.add(user_persona)
    session.commit()
    session.refresh(user_persona)

    # Verify it was created
    assert user_persona.id is not None
    assert user_persona.user_id == test_user.id
    assert user_persona.persona_id == test_persona.id
    assert user_persona.nickname == "Test Nickname"

    # Verify relationship with User
    statement = select(User).where(User.id == test_user.id)
    db_user = session.exec(statement).one()
    assert len(db_user.user_personas) == 1
    assert db_user.user_personas[0].id == user_persona.id

    # Verify relationship with Persona
    statement = select(Persona).where(Persona.id == test_persona.id)
    db_persona = session.exec(statement).one()
    assert len(db_persona.user_personas) == 1
    assert db_persona.user_personas[0].id == user_persona.id


def test_delete_user_persona(session: Session, test_user: User, test_persona: Persona):
    # Create a UserPersona
    user_persona = UserPersona(
        user_id=test_user.id,
        persona_id=test_persona.id,
        nickname="Test Nickname"
    )
    session.add(user_persona)
    session.commit()

    # Delete the UserPersona
    session.delete(user_persona)
    session.commit()

    # Verify it was deleted
    statement = select(UserPersona).where(UserPersona.id == user_persona.id)
    result = session.exec(statement).first()
    assert result is None

    # Verify User and Persona still exist
    statement = select(User).where(User.id == test_user.id)
    db_user = session.exec(statement).one()
    assert db_user is not None

    statement = select(Persona).where(Persona.id == test_persona.id)
    db_persona = session.exec(statement).one()
    assert db_persona is not None
