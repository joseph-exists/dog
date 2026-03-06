import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import User
from app.tests.utils.user import authentication_token_from_email


def test_story_access_grants_viewer_then_editor(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    other_email = "phase0.other.user@example.com"
    other_headers = authentication_token_from_email(client=client, email=other_email, db=db)
    other_user = db.exec(select(User).where(User.email == other_email)).first()
    assert other_user is not None

    # Create a story as the owner.
    create = client.post(
        f"{settings.API_V1_STR}/stories/",
        headers=normal_user_token_headers,
        json={"title": "Phase0 Shared Story"},
    )
    assert create.status_code == 200, create.text
    story_id = create.json()["id"]

    # Grant viewer (default) to the other user.
    grant_viewer = client.post(
        f"{settings.API_V1_STR}/access/story/{story_id}",
        headers=normal_user_token_headers,
        json={
            "subject_type": "user",
            "subject_id": str(other_user.id),
            "role": "viewer",
        },
    )
    assert grant_viewer.status_code == 200, grant_viewer.text

    # Other user can read, but cannot edit.
    read = client.get(
        f"{settings.API_V1_STR}/stories/{story_id}",
        headers=other_headers,
    )
    assert read.status_code == 200, read.text

    edit_denied = client.put(
        f"{settings.API_V1_STR}/stories/{story_id}",
        headers=other_headers,
        json={"title": "Should Fail"},
    )
    assert edit_denied.status_code == 400

    # Upgrade to editor; now edits should work.
    grant_editor = client.post(
        f"{settings.API_V1_STR}/access/story/{story_id}",
        headers=normal_user_token_headers,
        json={
            "subject_type": "user",
            "subject_id": str(other_user.id),
            "role": "editor",
        },
    )
    assert grant_editor.status_code == 200, grant_editor.text

    edit_ok = client.put(
        f"{settings.API_V1_STR}/stories/{story_id}",
        headers=other_headers,
        json={"title": "Edited by Co-author"},
    )
    assert edit_ok.status_code == 200, edit_ok.text


def test_demo_session_sharing_invites_user_to_room(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    other_email = "phase0.demo.viewer@example.com"
    other_headers = authentication_token_from_email(client=client, email=other_email, db=db)
    other_user = db.exec(select(User).where(User.email == other_email)).first()
    assert other_user is not None

    # Create a personal demo config owned by the current user.
    slug = f"phase0-demo-{uuid.uuid4().hex[:10]}"
    config_resp = client.post(
        f"{settings.API_V1_STR}/demos/",
        headers=normal_user_token_headers,
        json={
            "slug": slug,
            "title": "Phase0 Demo",
            "scope": "personal",
        },
    )
    assert config_resp.status_code == 201, config_resp.text
    demo_config_id = config_resp.json()["id"]

    # Create the owner's demo session.
    session_resp = client.post(
        f"{settings.API_V1_STR}/demos/sessions",
        headers=normal_user_token_headers,
        json={"demo_config_id": demo_config_id},
    )
    assert session_resp.status_code == 201, session_resp.text
    demo_session_id = session_resp.json()["id"]
    room_id = session_resp.json()["room_id"]

    # Share the demo session to the other user (viewer role).
    grant = client.post(
        f"{settings.API_V1_STR}/access/demo_session/{demo_session_id}",
        headers=normal_user_token_headers,
        json={
            "subject_type": "user",
            "subject_id": str(other_user.id),
            "role": "viewer",
        },
    )
    assert grant.status_code == 200, grant.text

    # The other user can fetch the shared session...
    shared_session = client.get(
        f"{settings.API_V1_STR}/demos/sessions/{demo_session_id}",
        headers=other_headers,
    )
    assert shared_session.status_code == 200, shared_session.text

    # ...and can access the backing room because sharing invited them as a participant.
    participants = client.get(
        f"{settings.API_V1_STR}/rooms/{room_id}/participants",
        headers=other_headers,
    )
    assert participants.status_code == 200, participants.text


def test_project_grant_inherits_to_attached_story(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    other_email = "phase0.project.member@example.com"
    other_headers = authentication_token_from_email(client=client, email=other_email, db=db)
    other_user = db.exec(select(User).where(User.email == other_email)).first()
    assert other_user is not None

    # Owner creates a project
    project_resp = client.post(
        f"{settings.API_V1_STR}/projects/",
        headers=normal_user_token_headers,
        json={"name": f"Phase0 Project {uuid.uuid4().hex[:8]}"},
    )
    assert project_resp.status_code == 201, project_resp.text
    project_id = project_resp.json()["id"]

    # Owner creates a story
    story_resp = client.post(
        f"{settings.API_V1_STR}/stories/",
        headers=normal_user_token_headers,
        json={"title": "Project Story"},
    )
    assert story_resp.status_code == 200, story_resp.text
    story_id = story_resp.json()["id"]

    # Attach the story to the project
    attach = client.post(
        f"{settings.API_V1_STR}/projects/{project_id}/resources",
        headers=normal_user_token_headers,
        json={"resource_type": "story", "resource_id": story_id},
    )
    assert attach.status_code == 201, attach.text

    # Grant viewer on the project to the other user
    grant = client.post(
        f"{settings.API_V1_STR}/access/project/{project_id}",
        headers=normal_user_token_headers,
        json={
            "subject_type": "user",
            "subject_id": str(other_user.id),
            "role": "viewer",
        },
    )
    assert grant.status_code == 200, grant.text

    # Other user can read the attached story via inherited project access.
    read = client.get(
        f"{settings.API_V1_STR}/stories/{story_id}",
        headers=other_headers,
    )
    assert read.status_code == 200, read.text


def test_project_page_auth_viewer_read_editor_write(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    viewer_email = "phase0.project.page.viewer@example.com"
    viewer_headers = authentication_token_from_email(client=client, email=viewer_email, db=db)
    viewer_user = db.exec(select(User).where(User.email == viewer_email)).first()
    assert viewer_user is not None

    outsider_email = "phase0.project.page.outsider@example.com"
    outsider_headers = authentication_token_from_email(
        client=client, email=outsider_email, db=db
    )

    # Owner creates project and initial page layout.
    project_resp = client.post(
        f"{settings.API_V1_STR}/projects/",
        headers=normal_user_token_headers,
        json={"name": f"Phase0 Project Page {uuid.uuid4().hex[:8]}"},
    )
    assert project_resp.status_code == 201, project_resp.text
    project_id = project_resp.json()["id"]

    first_layout = client.post(
        f"{settings.API_V1_STR}/pages/project/{project_id}/layout",
        headers=normal_user_token_headers,
        json={
            "layout_json": [{"id": "owner-block", "type": "identity"}],
            "layout_version": 1,
        },
    )
    assert first_layout.status_code == 200, first_layout.text
    page_id = first_layout.json()["id"]

    # Grant viewer to collaborator.
    grant_viewer = client.post(
        f"{settings.API_V1_STR}/access/project/{project_id}",
        headers=normal_user_token_headers,
        json={
            "subject_type": "user",
            "subject_id": str(viewer_user.id),
            "role": "viewer",
        },
    )
    assert grant_viewer.status_code == 200, grant_viewer.text

    # Viewer can read project page...
    read_ok = client.get(
        f"{settings.API_V1_STR}/pages/project/{project_id}",
        headers=viewer_headers,
    )
    assert read_ok.status_code == 200, read_ok.text

    # ...but cannot mutate layout.
    upsert_denied = client.post(
        f"{settings.API_V1_STR}/pages/project/{project_id}/layout",
        headers=viewer_headers,
        json={"layout_json": [{"id": "viewer-block"}], "layout_version": 2},
    )
    assert upsert_denied.status_code == 403, upsert_denied.text

    update_denied = client.put(
        f"{settings.API_V1_STR}/pages/{page_id}",
        headers=viewer_headers,
        json={"layout_json": [{"id": "viewer-block"}], "layout_version": 2},
    )
    assert update_denied.status_code == 403, update_denied.text

    delete_denied = client.delete(
        f"{settings.API_V1_STR}/pages/{page_id}",
        headers=viewer_headers,
    )
    assert delete_denied.status_code == 403, delete_denied.text

    # Non-member cannot read.
    read_denied = client.get(
        f"{settings.API_V1_STR}/pages/project/{project_id}",
        headers=outsider_headers,
    )
    assert read_denied.status_code == 403, read_denied.text

    # Upgrade collaborator to editor; page write should succeed.
    grant_editor = client.post(
        f"{settings.API_V1_STR}/access/project/{project_id}",
        headers=normal_user_token_headers,
        json={
            "subject_type": "user",
            "subject_id": str(viewer_user.id),
            "role": "editor",
        },
    )
    assert grant_editor.status_code == 200, grant_editor.text

    upsert_ok = client.post(
        f"{settings.API_V1_STR}/pages/project/{project_id}/layout",
        headers=viewer_headers,
        json={
            "layout_json": [{"id": "editor-block", "type": "identity"}],
            "layout_version": 3,
        },
    )
    assert upsert_ok.status_code == 200, upsert_ok.text


def test_project_my_effective_role_endpoint(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    member_email = "phase0.project.role.member@example.com"
    member_headers = authentication_token_from_email(client=client, email=member_email, db=db)
    member_user = db.exec(select(User).where(User.email == member_email)).first()
    assert member_user is not None

    outsider_email = "phase0.project.role.outsider@example.com"
    outsider_headers = authentication_token_from_email(
        client=client, email=outsider_email, db=db
    )

    project_resp = client.post(
        f"{settings.API_V1_STR}/projects/",
        headers=normal_user_token_headers,
        json={"name": f"Phase0 Project Role {uuid.uuid4().hex[:8]}"},
    )
    assert project_resp.status_code == 201, project_resp.text
    project_id = project_resp.json()["id"]

    # Owner resolves as manager.
    owner_role_resp = client.get(
        f"{settings.API_V1_STR}/access/project/{project_id}/me",
        headers=normal_user_token_headers,
    )
    assert owner_role_resp.status_code == 200, owner_role_resp.text
    assert owner_role_resp.json()["role"] == "manager"

    # Viewer grant resolves as viewer.
    grant_viewer = client.post(
        f"{settings.API_V1_STR}/access/project/{project_id}",
        headers=normal_user_token_headers,
        json={
            "subject_type": "user",
            "subject_id": str(member_user.id),
            "role": "viewer",
        },
    )
    assert grant_viewer.status_code == 200, grant_viewer.text

    viewer_role_resp = client.get(
        f"{settings.API_V1_STR}/access/project/{project_id}/me",
        headers=member_headers,
    )
    assert viewer_role_resp.status_code == 200, viewer_role_resp.text
    assert viewer_role_resp.json()["role"] == "viewer"

    # Upgrade to editor; endpoint should reflect editor.
    grant_editor = client.post(
        f"{settings.API_V1_STR}/access/project/{project_id}",
        headers=normal_user_token_headers,
        json={
            "subject_type": "user",
            "subject_id": str(member_user.id),
            "role": "editor",
        },
    )
    assert grant_editor.status_code == 200, grant_editor.text

    editor_role_resp = client.get(
        f"{settings.API_V1_STR}/access/project/{project_id}/me",
        headers=member_headers,
    )
    assert editor_role_resp.status_code == 200, editor_role_resp.text
    assert editor_role_resp.json()["role"] == "editor"

    # No membership resolves as null role.
    outsider_role_resp = client.get(
        f"{settings.API_V1_STR}/access/project/{project_id}/me",
        headers=outsider_headers,
    )
    assert outsider_role_resp.status_code == 200, outsider_role_resp.text
    assert outsider_role_resp.json()["role"] is None
