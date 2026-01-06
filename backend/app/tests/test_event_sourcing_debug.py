"""Debug version of test_replay_uses_snapshots to diagnose snapshot issue."""

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import ProgressSnapshot, UserNodeChoice
from app import crud


def test_snapshot_debug(
    client: TestClient,
    db: Session,
    db_story_with_long_path: tuple,
    normal_user_token_headers: dict[str, str],
):
    """Debug: Check if snapshots are being created."""
    story, progress = db_story_with_long_path
    user_persona_id = progress.user_persona_id
    story_id = story.id

    print(f"\n=== Starting test ===")
    print(f"Progress ID: {progress.id}")
    print(f"Initial head_choice_id: {progress.head_choice_id}")

    # Make 15 choices
    for i in range(15):
        response = client.get(
            f"/api/v1/user-personas/{user_persona_id}/stories/{story_id}/current-node",
            headers=normal_user_token_headers,
        )
        current_node = response.json()

        if not current_node["available_choices"]:
            print(f"Stopped at choice {i+1} - no more choices")
            break

        choice_id = current_node["available_choices"][0]["id"]
        response = client.post(
            f"/api/v1/user-personas/{user_persona_id}/stories/{story_id}/choices/{choice_id}",
            headers=normal_user_token_headers,
        )
        assert response.status_code == 200
        print(f"Made choice {i+1}")

    # Force refresh the db session
    db.commit()  # Commit any pending changes
    db.expire_all()  # Expire all cached objects

    # Get fresh progress
    progress = crud.get_user_story_progress(
        session=db,
        user_persona_id=user_persona_id,
        story_id=story_id
    )

    print(f"\n=== After making choices ===")
    print(f"Progress head_choice_id: {progress.head_choice_id}")
    print(f"Progress head_version: {progress.head_version}")

    # Check chain length
    if progress.head_choice_id:
        chain = crud.get_choice_ancestor_chain(
            session=db,
            choice_id=progress.head_choice_id
        )
        print(f"Chain length: {len(chain)}")

    # Query ALL snapshots for this progress (not just nearest)
    all_snapshots = db.exec(
        select(ProgressSnapshot).where(
            ProgressSnapshot.progress_id == progress.id
        )
    ).all()

    print(f"\n=== Snapshots found: {len(all_snapshots)} ===")
    for snap in all_snapshots:
        # Get position of each snapshot
        if snap.choice_id:
            chain = crud.get_choice_ancestor_chain(
                session=db,
                choice_id=snap.choice_id
            )
            print(f"Snapshot at choice position {len(chain)}, choice_id: {snap.choice_id}")

    # Check all UserNodeChoices
    all_choices = db.exec(
        select(UserNodeChoice).where(
            UserNodeChoice.progress_id == progress.id
        )
    ).all()
    print(f"\n=== UserNodeChoices found: {len(all_choices)} ===")

    # Now test get_nearest_snapshot
    snapshot = crud.get_nearest_snapshot(
        session=db,
        progress_id=progress.id,
        head_choice_id=progress.head_choice_id
    )

    print(f"\n=== get_nearest_snapshot result: {snapshot} ===")

    if snapshot is None:
        print("FAIL: No snapshot found")
        print("\n=== Checking why... ===")

        # Manually check if chain_length at position 10 meets criteria
        if progress.head_choice_id:
            chain = crud.get_choice_ancestor_chain(db, progress.head_choice_id)
            print(f"Current chain: {[str(c.id)[:8] for c in chain]}")

            # Check if any choice in chain has snapshot
            for idx, choice in enumerate(chain):
                pos = idx + 1
                has_snapshot = db.exec(
                    select(ProgressSnapshot).where(
                        ProgressSnapshot.progress_id == progress.id,
                        ProgressSnapshot.choice_id == choice.id
                    )
                ).first()
                if has_snapshot:
                    print(f"  Position {pos}: HAS snapshot")
                elif pos % 10 == 0:
                    print(f"  Position {pos}: SHOULD have snapshot but doesn't!")
    else:
        print(f"SUCCESS: Found snapshot at choice_id: {snapshot.choice_id}")

    # This will fail if snapshot is None - that's the point
    assert snapshot is not None, f"No snapshot found after making 15 choices. Found {len(all_snapshots)} total snapshots, {len(all_choices)} total choices"
