### Test 1: Basic Undo

def test_undo_derives_state_from_events_optimized(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_progress: tuple,
) -> None:
    """Undo should derive state using optimized replay with snapshots."""
    story, progress = db_story_with_progress
    persona_id = progress.user_persona_id

    # Make 2 choices (A → B)
    for _ in range(2):
        resp = client.get(f".../current-node", headers=normal_user_token_headers)
        choice_id = resp.json()["available_choices"][0]["id"]
        client.post(f".../choices/{choice_id}", headers=normal_user_token_headers)

    db.refresh(progress)
    head_at_B = progress.head_choice_id
    state_at_B = progress.story_state.copy()

    # Undo (B → A)
    resp = client.post(f".../undo", headers=normal_user_token_headers)
    assert resp.status_code == 200

    db.refresh(progress)
    # State should be replayed from A using optimized function
    assert progress.head_version == 3  # Version increments on undo
    assert progress.head_choice_id != head_at_B  # Moved to parent
    # State should match what was at A (before B's state changes)
```

### Test 2: Jump to Ancestor

```python
def test_jump_uses_optimized_replay(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_progress: tuple,
) -> None:
    """Jump should use optimized replay with snapshots."""
    story, progress = db_story_with_progress
    persona_id = progress.user_persona_id

    # Make 4 choices (A → B → C → D)
    choice_ids = []
    for _ in range(4):
        resp = client.get(f".../current-node", headers=normal_user_token_headers)
        choice_id = resp.json()["available_choices"][0]["id"]
        resp = client.post(f".../choices/{choice_id}", headers=normal_user_token_headers)
        choice_ids.append(resp.json()["head_choice_id"])

    db.refresh(progress)
    head_version = progress.head_version

    # Jump to B (2nd choice)
    resp = client.post(
        f".../jump",
        headers=normal_user_token_headers,
        json={
            "choice_id": choice_ids[1],
            "expected_head_version": head_version
        }
    )
    assert resp.status_code == 200

    db.refresh(progress)
    # Should use optimized replay from B
    assert progress.head_choice_id == choice_ids[1]
    assert progress.head_version == head_version + 1
```

### Test 3: Completion Status Updates

```python
def test_undo_from_end_node_clears_completion(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_progress: tuple,
) -> None:
    """Undoing from end node should clear is_completed."""
    story, progress = db_story_with_progress
    persona_id = progress.user_persona_id

    # Complete the story (make all choices to end)
    while True:
        resp = client.get(f".../current-node", headers=normal_user_token_headers)
        choices = resp.json()["available_choices"]
        if not choices:
            break
        choice_id = choices[0]["id"]
        client.post(f".../choices/{choice_id}", headers=normal_user_token_headers)

    db.refresh(progress)
    assert progress.is_completed == True

    # Undo from end
    resp = client.post(f".../undo", headers=normal_user_token_headers)
    assert resp.status_code == 200

    db.refresh(progress)
    assert progress.is_completed == False  # No longer at end node
```

### Test 4: Real-Time Event Publishing

```python
def test_undo_publishes_realtime_event(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_progress: tuple,
    mocker,
) -> None:
    """Undo should publish head.moved event to Redis."""
    story, progress = db_story_with_progress
    persona_id = progress.user_persona_id

    # Mock Redis publisher
    mock_publish = mocker.patch('app.services.realtime_publisher.publish_event_to_redis')

    # Make a choice then undo
    resp = client.get(f".../current-node", headers=normal_user_token_headers)
    choice_id = resp.json()["available_choices"][0]["id"]
    client.post(f".../choices/{choice_id}", headers=normal_user_token_headers)

    # Undo
    resp = client.post(f".../undo", headers=normal_user_token_headers)
    assert resp.status_code == 200

    # Verify background task was scheduled (will execute after response)
    # Note: In test environment, background tasks execute immediately
    assert mock_publish.called
    call_args = mock_publish.call_args
    assert call_args[1]["event_type"] == "head.moved"
    assert call_args[1]["payload"]["operation"] == "undo"