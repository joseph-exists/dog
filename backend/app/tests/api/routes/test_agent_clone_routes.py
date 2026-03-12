import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.core.provider_types import TYPE1
from app.models import User, UserAgentConfig
from app.tests.utils.user import authentication_token_from_email
from app.tests.utils.utils import random_email


def _create_agent(
    *,
    db: Session,
    owner_id: uuid.UUID,
    scope: str,
    is_visible: bool = False,
    is_clonable: bool = False,
    user_access_provider: uuid.UUID | None = None,
) -> UserAgentConfig:
    agent = UserAgentConfig(
        id=uuid.uuid4(),
        owner_id=owner_id,
        name=f"Agent {uuid.uuid4().hex[:6]}",
        slug=f"agent-{uuid.uuid4().hex[:8]}",
        description="test",
        provider_type=uuid.UUID(TYPE1),
        model_name="gpt-4o-mini",
        model="gpt-4o-mini",
        system_prompt="You are a test agent.",
        participation_mode="on_mention",
        scope=scope,
        is_enabled=True,
        is_visible=is_visible,
        is_clonable=is_clonable,
        user_access_provider=user_access_provider,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


def test_clone_system_agent_creates_personal_and_clears_provider_link(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    owner = db.exec(select(User).where(User.email == settings.FIRST_SUPERTESTUSER)).first()
    assert owner

    source_uap_id = uuid.uuid4()
    source = _create_agent(
        db=db,
        owner_id=owner.id,
        scope="system",
        is_visible=True,
        is_clonable=True,
        user_access_provider=source_uap_id,
    )

    r = client.post(
        f"{settings.API_V1_STR}/agents/{source.id}/clone",
        headers=normal_user_token_headers,
        json={},
    )
    assert r.status_code == 200, r.text
    cloned = r.json()
    assert cloned["scope"] == "personal"
    assert cloned["user_access_provider"] is None
    assert cloned["id"] != str(source.id)
    assert cloned["slug"] != source.slug


def test_copy_own_agent_can_retain_provider_link(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    owner = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert owner

    source_uap_id = uuid.uuid4()
    source = _create_agent(
        db=db,
        owner_id=owner.id,
        scope="personal",
        user_access_provider=source_uap_id,
    )

    r = client.post(
        f"{settings.API_V1_STR}/agents/{source.id}/clone",
        headers=normal_user_token_headers,
        json={"retain_user_access_provider": True},
    )
    assert r.status_code == 200, r.text
    cloned = r.json()
    assert cloned["scope"] == "personal"
    assert cloned["user_access_provider"] == str(source_uap_id)


def test_clone_other_user_personal_requires_visible_and_clonable(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    other_email = random_email()
    other_headers = authentication_token_from_email(client=client, email=other_email, db=db)
    assert other_headers

    other_user = db.exec(select(User).where(User.email == other_email)).first()
    assert other_user

    hidden_source = _create_agent(
        db=db,
        owner_id=other_user.id,
        scope="personal",
        is_visible=True,
        is_clonable=False,
    )

    denied = client.post(
        f"{settings.API_V1_STR}/agents/{hidden_source.id}/clone",
        headers=normal_user_token_headers,
        json={},
    )
    assert denied.status_code == 403

    shared_source = _create_agent(
        db=db,
        owner_id=other_user.id,
        scope="personal",
        is_visible=True,
        is_clonable=True,
        user_access_provider=uuid.uuid4(),
    )

    allowed = client.post(
        f"{settings.API_V1_STR}/agents/{shared_source.id}/clone",
        headers=normal_user_token_headers,
        json={},
    )
    assert allowed.status_code == 200, allowed.text
    cloned = allowed.json()
    assert cloned["scope"] == "personal"
    assert cloned["user_access_provider"] is None
