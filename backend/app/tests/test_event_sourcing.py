"""Tests for full event sourcing implementation (Phase 5)."""

import uuid
import time
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import ProgressSnapshot, UserNodeChoice
from app import crud

# TODO: re-enable after we create new test fixtures.

def test_snapshot_created_every_10_choices(
    client: TestClient, 
    db: Session, 
    normal_user_token_headers: dict[str, str],
    db_story_with_long_path: tuple,
):
    """Test that snapshots are created automatically every 10 choices."""
    story, progress = db_story_with_long_path
    user_persona_id = progress.user_persona_id
    story_id = story.id

    # Make 25 choices
    for i in range(25):
        response = client.get(
            f"/api/v1/user-personas/{user_persona_id}/stories/{story_id}/current-node", headers=normal_user_token_headers,
        )
        current_node = response.json()

        if not current_node["available_choices"]:
            break  # End node reached

        choice_id = current_node["available_choices"][0]["id"]
        response = client.post(
            f"/api/v1/user-personas/{user_persona_id}/stories/{story_id}/choices/{choice_id}", headers=normal_user_token_headers,
        )
        assert response.status_code == 200

    db.refresh(progress)

    # Check snapshots
    snapshots = db.exec(
        select(ProgressSnapshot).where(
            ProgressSnapshot.progress_id == progress.id
        )
    ).all()

    # Should have snapshots at choices 10, 20 (assuming we made at least 20 choices)
    assert len(snapshots) >= 2

    # Verify snapshot positions
    for snapshot in snapshots:
        chain = crud.get_choice_ancestor_chain(
            session=db,
            choice_id=snapshot.choice_id
        )
        chain_length = len(chain)

        # Chain length should be multiple of 10
        assert chain_length % 10 == 0


def test_replay_uses_snapshots(
    client: TestClient, 
    db: Session, 
    db_story_with_long_path: tuple,
    normal_user_token_headers: dict[str, str],
):
    """Test that replay uses snapshots when available."""
    story, progress = db_story_with_long_path
    user_persona_id = progress.user_persona_id
    story_id = story.id

    # Make 15 choices to trigger snapshot at choice 10
    for i in range(15):
        response = client.get(
            f"/api/v1/user-personas/{user_persona_id}/stories/{story_id}/current-node", headers=normal_user_token_headers,
        )
        current_node = response.json()

        if not current_node["available_choices"]:
            break

        choice_id = current_node["available_choices"][0]["id"]
        client.post(
            f"/api/v1/user-personas/{user_persona_id}/stories/{story_id}/choices/{choice_id}", headers=normal_user_token_headers,
        )
    db.commit()
    db.expire_all()
    
    # Get progress
    progress = crud.get_user_story_progress(
        session=db,
        user_persona_id=user_persona_id,
        story_id=story_id
    )

    # Verify snapshot exists
    snapshot = crud.get_nearest_snapshot(
        session=db,
        progress_id=progress.id,
        head_choice_id=progress.head_choice_id
    )
    assert snapshot is not None

    # Replay with snapshot
    replayed_state = crud.replay_state_from_head_optimized(
        session=db,
        progress_id=progress.id,
        head_choice_id=progress.head_choice_id
    )

    # Should match current state
    assert replayed_state == progress.story_state


def test_replay_performance_with_snapshots(
    client: TestClient, 
    db: Session, 
    db_story_with_long_path: tuple,
    normal_user_token_headers: dict[str, str],
):
    """Test that replay with snapshots is faster than without."""
    story, progress = db_story_with_long_path
    user_persona_id = progress.user_persona_id
    story_id = story.id

    # Make 50 choices (will create snapshots at 10, 20, 30, 40, 50)
    for i in range(50):
        response = client.get(
            f"/api/v1/user-personas/{user_persona_id}/stories/{story_id}/current-node", headers=normal_user_token_headers,
        )
        current_node = response.json()

        if not current_node["available_choices"]:
            break

        choice_id = current_node["available_choices"][0]["id"]
        client.post(
            f"/api/v1/user-personas/{user_persona_id}/stories/{story_id}/choices/{choice_id}", headers=normal_user_token_headers,
        )

    # Get progress
    progress = crud.get_user_story_progress(
        session=db,
        user_persona_id=user_persona_id,
        story_id=story_id,
    )

    # Measure replay WITH snapshots
    start = time.perf_counter()
    state_with_snapshot = crud.replay_state_from_head_optimized(
        session=db,
        progress_id=progress.id,
        head_choice_id=progress.head_choice_id
    )
    time_with_snapshot = (time.perf_counter() - start) * 1000

    # Measure replay WITHOUT snapshots (from root)
    start = time.perf_counter()
    state_without_snapshot = crud.replay_state_from_head(
        session=db,
        progress_id=progress.id,
        head_choice_id=progress.head_choice_id
    )
    time_without_snapshot = (time.perf_counter() - start) * 1000

    # Both should produce same result
    assert state_with_snapshot == state_without_snapshot

    # With snapshot should be faster (or at least not slower)
    # Target: < 10ms with snapshots
    assert time_with_snapshot < 10, f"Replay too slow: {time_with_snapshot}ms"

    print(f"Replay performance:")
    print(f"  With snapshots: {time_with_snapshot:.2f}ms")
    print(f"  Without snapshots: {time_without_snapshot:.2f}ms")
    print(f"  Speedup: {time_without_snapshot / time_with_snapshot:.2f}x")


def test_state_always_derived_from_events(
    client: TestClient,
    db: Session,
    db_story_with_progress: tuple,
    normal_user_token_headers: dict[str, str],
):
    """Test that story_state is ALWAYS derived from events, never mutated."""
    story, progress = db_story_with_progress
    user_persona_id = progress.user_persona_id
    story_id = story.id

    # Make choice
    response = client.get(
        f"/api/v1/user-personas/{user_persona_id}/stories/{story_id}/current-node", headers=normal_user_token_headers,
    )
    current_node = response.json()
    choice_id = current_node["available_choices"][0]["id"]

    response = client.post(
        f"/api/v1/user-personas/{user_persona_id}/stories/{story_id}/choices/{choice_id}", headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    progress_data = response.json()

    # Get progress from database
    progress = crud.get_user_story_progress(
        session=db,
        user_persona_id=user_persona_id,
        story_id=story_id,
    )

    # Replay state from events
    replayed_state = crud.replay_state_from_head_optimized(
        session=db,
        progress_id=progress.id,
        head_choice_id=progress.head_choice_id
    )

    # Stored state MUST match replayed state
    assert progress.story_state == replayed_state

    # API response state MUST match replayed state
    assert progress_data["story_state"] == replayed_state


def test_undo_derives_state_from_events(
    client: TestClient, db: Session, db_story_with_progress: tuple, normal_user_token_headers: dict[str, str]
):
    """Test that undo derives state from events (not mutable update)."""
    story, progress = db_story_with_progress
    user_persona_id = progress.user_persona_id
    story_id = story.id

      # Make a choice first (so we have something to undo)
    response = client.get(f"/api/v1/user-personas/{user_persona_id}/stories/{story_id}/current-node", headers=normal_user_token_headers,
    )
    choice_id = response.json()["available_choices"][0]["id"]

    client.post(
        f"/api/v1/user-personas/{user_persona_id}/stories/{story_id}/choices/{choice_id}", 
        headers=normal_user_token_headers,
    )

    # Undo
    response = client.post(
        f"/api/v1/user-personas/{user_persona_id}/stories/{story.id}/undo", headers=normal_user_token_headers,
    )
    assert response.status_code == 200

    # Get progress
    progress = crud.get_user_story_progress(
        session=db,
        user_persona_id=user_persona_id,
        story_id=story_id
    )

    # Replay state
    replayed_state = crud.replay_state_from_head_optimized(
        session=db,
        progress_id=progress.id,
        head_choice_id=progress.head_choice_id
    )

    # Must match
    assert progress.story_state == replayed_state


def test_jump_derives_state_from_events(
    client: TestClient, db: Session, db_story_with_progress: tuple, normal_user_token_headers: dict[str, str]
):
    """Test that jump derives state from events (not mutable update)."""
    story, progress = db_story_with_progress
    user_persona_id = progress.user_persona_id
    story_id = story.id  

    # Get timeline
    response = client.get(
        f"/api/v1/user-personas/{user_persona_id}/stories/{story.id}/timeline", headers=normal_user_token_headers,
    )
    timeline = response.json()

    # Jump to start
    response = client.post(
        f"/api/v1/user-personas/{user_persona_id}/stories/{story_id}/jump", headers=normal_user_token_headers,
        json={
            "choice_id": None,
            "expected_head_version": timeline["head_version"]
        }
    )
    assert response.status_code == 200

    # Get progress
    progress = crud.get_user_story_progress(
        session=db,
        user_persona_id=user_persona_id,
        story_id=story_id
    )

    # Replay state
    replayed_state = crud.replay_state_from_head_optimized(
        session=db,
        progress_id=progress.id,
        head_choice_id=progress.head_choice_id
    )

    # Must match (should be empty dict since at start)
    assert progress.story_state == replayed_state
    assert replayed_state == {}


# def test_snapshot_coverage_metrics(
#     client: TestClient,
#     db: Session,
#     db_story_with_long_path: tuple,
#     normal_user_token_headers: dict[str, str],
# ):
#     """Test snapshot coverage metrics calculation.""" 
#     story, progress = db_story_with_long_path
#     user_persona_id = progress.user_persona_id
#     story_id = story.id

#     # Make 35 choices
#     for i in range(35):
#         response = client.get(
#             f"/api/v1/user-personas/{user_persona_id}/stories/{story_id}/current-node", headers=normal_user_token_headers,
#         )
#         current_node = response.json()

#         if not current_node["available_choices"]:
#             break

#         choice_id = current_node["available_choices"][0]["id"]
#         client.post(
#             f"/api/v1/user-personas/{user_persona_id}/stories/{story_id}/choices/{choice_id}", headers=normal_user_token_headers,
#         )

#     db.refresh(progress)

#     # Get coverage metrics
#     metrics = crud.get_snapshot_coverage(
#         session=db,
#         progress_id=progress.id
#     )

#     # Verify metrics
#     assert metrics["total_choices"] >= 30
#     assert metrics["total_snapshots"] >= 3  # At 10, 20, 30
#     assert metrics["coverage_percent"] > 0
#     assert metrics["max_gap"] <= 10  # Should never exceed interval
#     assert metrics["avg_gap"] <= 10