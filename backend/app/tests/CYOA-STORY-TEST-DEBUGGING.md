FAILED app/tests/test_petri_timeline.py::test_undo_moves_to_parent - KeyError: 'available_choices'
FAILED app/tests/test_petri_timeline.py::test_undo_at_start_returns_error - assert 404 == 400
FAILED app/tests/test_petri_timeline.py::test_jump_to_ancestor - KeyError: 'available_choices'
FAILED app/tests/test_petri_timeline.py::test_jump_non_ancestor_returns_error - KeyError: 'available_choices'
FAILED app/tests/test_petri_timeline.py::test_jump_optimistic_concurrency - KeyError: 'available_choices'
FAILED app/tests/test_petri_timeline.py::test_timeline_shows_active_path_only - KeyError: 'available_choices'
FAILED app/tests/test_petri_timeline.py::test_make_choice_after_undo_creates_branch - KeyError: 'available_choices'
FAILED app/tests/test_story_replay.py::test_validate_state_endpoint - KeyError: 'available_choices'
FAILED app/tests/test_story_replay.py::test_replay_validates_progress_ownership - NameError: name 'session' is not defined
FAILED app/tests/test_story_timeline.py::test_undo_moves_to_parent - KeyError: 'available_choices'
FAILED app/tests/test_story_timeline.py::test_undo_at_start_returns_error - assert 404 == 400
FAILED app/tests/test_story_timeline.py::test_jump_to_ancestor - KeyError: 'available_choices'
FAILED app/tests/test_story_timeline.py::test_jump_non_ancestor_returns_error - KeyError: 'available_choices'
FAILED app/tests/test_story_timeline.py::test_jump_optimistic_concurrency - KeyError: 'available_choices'
FAILED app/tests/test_story_timeline.py::test_timeline_shows_active_path_only - KeyError: 'available_choices'
FAILED app/tests/test_story_timeline.py::test_make_choice_after_undo_creates_branch - KeyError: 'available_choices'
FAILED app/tests/test_user_story_tree.py::test_choice_creates_parent_link - assert 404 == 200
FAILED app/tests/test_user_story_tree.py::test_head_pointer_updates - KeyError: 'available_choices'
FAILED app/tests/test_user_story_tree.py::test_rng_data_field_exists - KeyError: 'available_choices'
FAILED app/tests/api/routes/test_node_choices.py::test_create_node_choice - NameError: name 'create_test_story' is not defined
FAILED app/tests/api/routes/test_node_choices.py::test_cannot_create_choice_from_end_node - NameError: name 'create_test_story' is not defined

FULL ERROR FOR test_petri_timeline.py:


app/tests/test_user_story_tree.py FFF                                                                            [100%]

======================================================= FAILURES =======================================================
___________________________________________ test_choice_creates_parent_link ____________________________________________

client = <starlette.testclient.TestClient object at 0x72f7a324f2e0>
db = <sqlmodel.orm.session.Session object at 0x72f7a320b2e0>
normal_user_token_headers = {'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjgyNDM4MzQsInN1YiI6ImEyZDQ3MmJhLWYyMjgtNGI3Yi1hOGZjLWNkMjQ0N2NkOGFhMSJ9.a4ZDPZcKn5iLb-iTJtR3wr_wGJxG86R9SvaM9cMbVQ0'}
db_story_with_progress = (Story(owner_id=UUID('b550a0af-1076-441b-8a79-7473f3ff59a7'), created_at=datetime.datetime(2026, 1, 4, 18, 50, 34, 822...0f865-8706-40fe-8bf5-d26ee5c66bd2'), head_choice_id=None, updated_at=datetime.datetime(2026, 1, 4, 18, 50, 34, 99545)))

    def test_choice_creates_parent_link(
        client: TestClient,
        db: Session,
        normal_user_token_headers: dict[str, str],
        db_story_with_progress: tuple,  # Assumes fixture exists
    ) -> None:
        """
        Test that making a choice sets parent_choice_id correctly.

        Given: A story progress at start (head_choice_id = None)
        When: Player makes first choice
        Then: New choice has parent_choice_id = None

        When: Player makes second choice
        Then: New choice has parent_choice_id = first_choice.id
        """
        story, progress = db_story_with_progress
        persona_id = progress.user_persona_id

        # Get available choices
        response = client.get(
            f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
            headers=normal_user_token_headers,
        )
>       assert response.status_code == 200
E       assert 404 == 200
E        +  where 404 = <Response [404 Not Found]>.status_code

app/tests/test_user_story_tree.py:34: AssertionError
------------------------------------------------ Captured stderr setup -------------------------------------------------
INFO:app.tests.conftest:Initializing test database
INFO:app.tests.conftest:Creating test client
DEBUG:asyncio:Using selector: EpollSelector
INFO:app.tests.conftest:Setting up normal user token headers
DEBUG:passlib.handlers.bcrypt:detected 'bcrypt' backend, version '4.0.1'
DEBUG:passlib.handlers.bcrypt:'bcrypt' backend lacks $2$ support, enabling workaround
DEBUG:python_multipart.multipart:Calling on_field_start with no data
DEBUG:python_multipart.multipart:Calling on_field_name with data[0:8]
DEBUG:python_multipart.multipart:Calling on_field_data with data[9:27]
DEBUG:python_multipart.multipart:Calling on_field_end with no data
DEBUG:python_multipart.multipart:Calling on_field_start with no data
DEBUG:python_multipart.multipart:Calling on_field_name with data[28:36]
DEBUG:python_multipart.multipart:Calling on_field_data with data[37:69]
DEBUG:python_multipart.multipart:Calling on_field_end with no data
DEBUG:python_multipart.multipart:Calling on_end with no data
INFO:httpx:HTTP Request: POST http://testserver/api/v1/login/access-token "HTTP/1.1 200 OK"
-------------------------------------------------- Captured log setup --------------------------------------------------
INFO     app.tests.conftest:conftest.py:51 Initializing test database
INFO     app.tests.conftest:conftest.py:64 Creating test client
DEBUG    asyncio:selector_events.py:54 Using selector: EpollSelector
INFO     app.tests.conftest:conftest.py:95 Setting up normal user token headers
DEBUG    passlib.handlers.bcrypt:bcrypt.py:625 detected 'bcrypt' backend, version '4.0.1'
DEBUG    passlib.handlers.bcrypt:bcrypt.py:406 'bcrypt' backend lacks $2$ support, enabling workaround
DEBUG    python_multipart.multipart:multipart.py:628 Calling on_field_start with no data
DEBUG    python_multipart.multipart:multipart.py:625 Calling on_field_name with data[0:8]
DEBUG    python_multipart.multipart:multipart.py:625 Calling on_field_data with data[9:27]
DEBUG    python_multipart.multipart:multipart.py:628 Calling on_field_end with no data
DEBUG    python_multipart.multipart:multipart.py:628 Calling on_field_start with no data
DEBUG    python_multipart.multipart:multipart.py:625 Calling on_field_name with data[28:36]
DEBUG    python_multipart.multipart:multipart.py:625 Calling on_field_data with data[37:69]
DEBUG    python_multipart.multipart:multipart.py:628 Calling on_field_end with no data
DEBUG    python_multipart.multipart:multipart.py:628 Calling on_end with no data
INFO     httpx:_client.py:1025 HTTP Request: POST http://testserver/api/v1/login/access-token "HTTP/1.1 200 OK"
------------------------------------------------- Captured stderr call -------------------------------------------------
INFO:httpx:HTTP Request: GET http://testserver/api/v1/user-personas/804b716d-7df3-4cca-8eb5-b7c3764d08a6/stories/7050f865-8706-40fe-8bf5-d26ee5c66bd2/current-node "HTTP/1.1 404 Not Found"
-------------------------------------------------- Captured log call ---------------------------------------------------
INFO     httpx:_client.py:1025 HTTP Request: GET http://testserver/api/v1/user-personas/804b716d-7df3-4cca-8eb5-b7c3764d08a6/stories/7050f865-8706-40fe-8bf5-d26ee5c66bd2/current-node "HTTP/1.1 404 Not Found"
______________________________________________ test_head_pointer_updates _______________________________________________

client = <starlette.testclient.TestClient object at 0x72f7a324f2e0>
db = <sqlmodel.orm.session.Session object at 0x72f7a320b2e0>
normal_user_token_headers = {'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjgyNDM4MzQsInN1YiI6ImEyZDQ3MmJhLWYyMjgtNGI3Yi1hOGZjLWNkMjQ0N2NkOGFhMSJ9.a4ZDPZcKn5iLb-iTJtR3wr_wGJxG86R9SvaM9cMbVQ0'}
db_story_with_progress = (Story(owner_id=UUID('b550a0af-1076-441b-8a79-7473f3ff59a7'), created_at=datetime.datetime(2026, 1, 4, 18, 50, 34, 175...4180-52dc-4b4c-b21f-5fcbd3414fbb'), head_choice_id=None, updated_at=datetime.datetime(2026, 1, 4, 18, 50, 34, 187890)))

    def test_head_pointer_updates(
        client: TestClient,
        db: Session,
        normal_user_token_headers: dict[str, str],
        db_story_with_progress: tuple,
    ) -> None:
        """
        Test that head_choice_id and head_version update correctly.

        Given: Progress at start (head_choice_id=None, head_version=0)
        When: Player makes choice
        Then: head_choice_id = new_choice.id, head_version = 1
        """
        story, progress = db_story_with_progress
        persona_id = progress.user_persona_id

        # Verify initial state
        db.refresh(progress)
        assert progress.head_choice_id is None
        assert progress.head_version == 0

        # Make choice
        response = client.get(
            f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
            headers=normal_user_token_headers,
        )
>       choice_id = response.json()["available_choices"][0]["id"]
E       KeyError: 'available_choices'

app/tests/test_user_story_tree.py:103: KeyError
------------------------------------------------- Captured stderr call -------------------------------------------------
INFO:httpx:HTTP Request: GET http://testserver/api/v1/user-personas/2b74eafb-598f-4aa4-ade8-c4e9feaf4d3b/stories/bc924180-52dc-4b4c-b21f-5fcbd3414fbb/current-node "HTTP/1.1 404 Not Found"
-------------------------------------------------- Captured log call ---------------------------------------------------
INFO     httpx:_client.py:1025 HTTP Request: GET http://testserver/api/v1/user-personas/2b74eafb-598f-4aa4-ade8-c4e9feaf4d3b/stories/bc924180-52dc-4b4c-b21f-5fcbd3414fbb/current-node "HTTP/1.1 404 Not Found"
______________________________________________ test_rng_data_field_exists ______________________________________________

client = <starlette.testclient.TestClient object at 0x72f7a324f2e0>
db = <sqlmodel.orm.session.Session object at 0x72f7a320b2e0>
normal_user_token_headers = {'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjgyNDM4MzQsInN1YiI6ImEyZDQ3MmJhLWYyMjgtNGI3Yi1hOGZjLWNkMjQ0N2NkOGFhMSJ9.a4ZDPZcKn5iLb-iTJtR3wr_wGJxG86R9SvaM9cMbVQ0'}
db_story_with_progress = (Story(owner_id=UUID('b550a0af-1076-441b-8a79-7473f3ff59a7'), created_at=datetime.datetime(2026, 1, 4, 18, 50, 34, 205...6989-1845-4bf1-9c73-3c21bdc52258'), head_choice_id=None, updated_at=datetime.datetime(2026, 1, 4, 18, 50, 34, 215467)))

    def test_rng_data_field_exists(
        client: TestClient,
        db: Session,
        normal_user_token_headers: dict[str, str],
        db_story_with_progress: tuple,
    ) -> None:
        """
        Test that rng_data field can be set (even if null in Phase 1).

        Given: A choice is made
        Then: UserNodeChoice has rng_data field (even if null)
        """
        story, progress = db_story_with_progress
        persona_id = progress.user_persona_id

        # Make choice
        response = client.get(
            f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
            headers=normal_user_token_headers,
        )
>       choice_id = response.json()["available_choices"][0]["id"]
E       KeyError: 'available_choices'

app/tests/test_user_story_tree.py:142: KeyError
------------------------------------------------- Captured stderr call -------------------------------------------------
INFO:httpx:HTTP Request: GET http://testserver/api/v1/user-personas/4d7be64b-8894-4bf5-91f4-8d46fa0d8f23/stories/68d06989-1845-4bf1-9c73-3c21bdc52258/current-node "HTTP/1.1 404 Not Found"
-------------------------------------------------- Captured log call ---------------------------------------------------
INFO     httpx:_client.py:1025 HTTP Request: GET http://testserver/api/v1/user-personas/4d7be64b-8894-4bf5-91f4-8d46fa0d8f23/stories/68d06989-1845-4bf1-9c73-3c21bdc52258/current-node "HTTP/1.1 404 Not Found"
----------------------------------------------- Captured stderr teardown -----------------------------------------------
INFO:app.tests.conftest:Cleaning up test database
------------------------------------------------ Captured log teardown -------------------------------------------------
INFO     app.tests.conftest:conftest.py:55 Cleaning up test database
=================================================== warnings summary ===================================================
../usr/local/lib/python3.10/abc.py:106
../usr/local/lib/python3.10/abc.py:106
  /usr/local/lib/python3.10/abc.py:106: DeprecationWarning: You should use `Logger` instead. Deprecated since version 1.39.0 and will be removed in a future release.
    cls = super().__new__(mcls, name, bases, namespace, **kwargs)

../usr/local/lib/python3.10/abc.py:106
../usr/local/lib/python3.10/abc.py:106
  /usr/local/lib/python3.10/abc.py:106: DeprecationWarning: You should use `LoggerProvider` instead. Deprecated since version 1.39.0 and will be removed in a future release.
    cls = super().__new__(mcls, name, bases, namespace, **kwargs)

.venv/lib/python3.10/site-packages/opentelemetry/_events/__init__.py:201
  /app/.venv/lib/python3.10/site-packages/opentelemetry/_events/__init__.py:201: DeprecationWarning: You should use `ProxyLoggerProvider` instead. Deprecated since version 1.39.0 and will be removed in a future release.
    _PROXY_EVENT_LOGGER_PROVIDER = ProxyEventLoggerProvider()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=============================================== short test summary info ================================================
FAILED app/tests/test_user_story_tree.py::test_choice_creates_parent_link - assert 404 == 200
FAILED app/tests/test_user_story_tree.py::test_head_pointer_updates - KeyError: 'available_choices'
FAILED app/tests/test_user_story_tree.py::test_rng_data_field_exists - KeyError: 'available_choices'
============================================ 3 failed, 5 warnings in 0.63s =============================================
root@08b7c291196b:/app# pytest app/tests/test_petri_timeline.py -v
================================================= test session starts ==================================================
platform linux -- Python 3.10.19, pytest-7.4.4, pluggy-1.6.0 -- /app/.venv/bin/python
cachedir: .pytest_cache
rootdir: /app
plugins: asyncio-0.23.8, anyio-4.12.0, logfire-4.16.0
asyncio: mode=strict
collected 7 items

app/tests/test_petri_timeline.py::test_undo_moves_to_parent FAILED                                               [ 14%]
app/tests/test_petri_timeline.py::test_undo_at_start_returns_error FAILED                                        [ 28%]
app/tests/test_petri_timeline.py::test_jump_to_ancestor FAILED                                                   [ 42%]
app/tests/test_petri_timeline.py::test_jump_non_ancestor_returns_error FAILED                                    [ 57%]
app/tests/test_petri_timeline.py::test_jump_optimistic_concurrency FAILED                                        [ 71%]
app/tests/test_petri_timeline.py::test_timeline_shows_active_path_only FAILED                                    [ 85%]
app/tests/test_petri_timeline.py::test_make_choice_after_undo_creates_branch FAILED                              [100%]

======================================================= FAILURES =======================================================
______________________________________________ test_undo_moves_to_parent _______________________________________________

client = <starlette.testclient.TestClient object at 0x79e41575ea10>
db = <sqlmodel.orm.session.Session object at 0x79e4157137c0>
normal_user_token_headers = {'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjgyNDM4NjAsInN1YiI6ImEyZDQ3MmJhLWYyMjgtNGI3Yi1hOGZjLWNkMjQ0N2NkOGFhMSJ9.Rtzvso4vZ-U5DmA6Nx3jItPxFUmg9Jarpb9pn8vhZks'}
db_story_with_progress = (Story(published_version=None, created_at=datetime.datetime(2026, 1, 4, 18, 51, 0, 868702), owner_id=UUID('b550a0af-10...6f55e-b4f1-4672-a53e-f414df25a9eb'), head_choice_id=None, updated_at=datetime.datetime(2026, 1, 4, 18, 51, 0, 885917)))

    def test_undo_moves_to_parent(
        client: TestClient,
        db: Session,
        normal_user_token_headers: dict[str, str],
        db_story_with_progress: tuple,
    ) -> None:
        """
        Test that undo moves head to parent choice.

        Given: Progress with 2 choices (A → B), head at B
        When: POST /undo
        Then: head moves to A, state replayed from A
        """
        story, progress = db_story_with_progress
        persona_id = progress.user_persona_id

        # Make 2 choices
        for _ in range(2):
            response = client.get(
                f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
                headers=normal_user_token_headers,
            )
>           choice_id = response.json()["available_choices"][0]["id"]
E           KeyError: 'available_choices'

app/tests/test_petri_timeline.py:34: KeyError
------------------------------------------------ Captured stderr setup -------------------------------------------------
INFO:app.tests.conftest:Initializing test database
INFO:app.tests.conftest:Creating test client
DEBUG:asyncio:Using selector: EpollSelector
INFO:app.tests.conftest:Setting up normal user token headers
DEBUG:passlib.handlers.bcrypt:detected 'bcrypt' backend, version '4.0.1'
DEBUG:passlib.handlers.bcrypt:'bcrypt' backend lacks $2$ support, enabling workaround
DEBUG:python_multipart.multipart:Calling on_field_start with no data
DEBUG:python_multipart.multipart:Calling on_field_name with data[0:8]
DEBUG:python_multipart.multipart:Calling on_field_data with data[9:27]
DEBUG:python_multipart.multipart:Calling on_field_end with no data
DEBUG:python_multipart.multipart:Calling on_field_start with no data
DEBUG:python_multipart.multipart:Calling on_field_name with data[28:36]
DEBUG:python_multipart.multipart:Calling on_field_data with data[37:69]
DEBUG:python_multipart.multipart:Calling on_field_end with no data
DEBUG:python_multipart.multipart:Calling on_end with no data
INFO:httpx:HTTP Request: POST http://testserver/api/v1/login/access-token "HTTP/1.1 200 OK"
-------------------------------------------------- Captured log setup --------------------------------------------------
INFO     app.tests.conftest:conftest.py:51 Initializing test database
INFO     app.tests.conftest:conftest.py:64 Creating test client
DEBUG    asyncio:selector_events.py:54 Using selector: EpollSelector
INFO     app.tests.conftest:conftest.py:95 Setting up normal user token headers
DEBUG    passlib.handlers.bcrypt:bcrypt.py:625 detected 'bcrypt' backend, version '4.0.1'
DEBUG    passlib.handlers.bcrypt:bcrypt.py:406 'bcrypt' backend lacks $2$ support, enabling workaround
DEBUG    python_multipart.multipart:multipart.py:628 Calling on_field_start with no data
DEBUG    python_multipart.multipart:multipart.py:625 Calling on_field_name with data[0:8]
DEBUG    python_multipart.multipart:multipart.py:625 Calling on_field_data with data[9:27]
DEBUG    python_multipart.multipart:multipart.py:628 Calling on_field_end with no data
DEBUG    python_multipart.multipart:multipart.py:628 Calling on_field_start with no data
DEBUG    python_multipart.multipart:multipart.py:625 Calling on_field_name with data[28:36]
DEBUG    python_multipart.multipart:multipart.py:625 Calling on_field_data with data[37:69]
DEBUG    python_multipart.multipart:multipart.py:628 Calling on_field_end with no data
DEBUG    python_multipart.multipart:multipart.py:628 Calling on_end with no data
INFO     httpx:_client.py:1025 HTTP Request: POST http://testserver/api/v1/login/access-token "HTTP/1.1 200 OK"
------------------------------------------------- Captured stderr call -------------------------------------------------
INFO:httpx:HTTP Request: GET http://testserver/api/v1/user-personas/1aa783f5-db13-4748-807f-ab00871a5e45/stories/f216f55e-b4f1-4672-a53e-f414df25a9eb/current-node "HTTP/1.1 404 Not Found"
-------------------------------------------------- Captured log call ---------------------------------------------------
INFO     httpx:_client.py:1025 HTTP Request: GET http://testserver/api/v1/user-personas/1aa783f5-db13-4748-807f-ab00871a5e45/stories/f216f55e-b4f1-4672-a53e-f414df25a9eb/current-node "HTTP/1.1 404 Not Found"
___________________________________________ test_undo_at_start_returns_error ___________________________________________

client = <starlette.testclient.TestClient object at 0x79e41575ea10>
normal_user_token_headers = {'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjgyNDM4NjAsInN1YiI6ImEyZDQ3MmJhLWYyMjgtNGI3Yi1hOGZjLWNkMjQ0N2NkOGFhMSJ9.Rtzvso4vZ-U5DmA6Nx3jItPxFUmg9Jarpb9pn8vhZks'}
db_story_with_progress = (Story(published_version=None, created_at=datetime.datetime(2026, 1, 4, 18, 51, 0, 966967), owner_id=UUID('b550a0af-10...baf70-7549-491b-9c3b-0300226cef70'), head_choice_id=None, updated_at=datetime.datetime(2026, 1, 4, 18, 51, 0, 978598)))

    def test_undo_at_start_returns_error(
        client: TestClient,
        normal_user_token_headers: dict[str, str],
        db_story_with_progress: tuple,
    ) -> None:
        """
        Test that undo at story start returns 400 error.

        Given: Progress at story start (head_choice_id = None)
        When: POST /undo
        Then: Returns 400 "Already at story start"
        """
        story, progress = db_story_with_progress
        persona_id = progress.user_persona_id

        # Attempt undo at start
        response = client.post(
            f"/api/v1/user-personas/{persona_id}/stories/{story.id}/undo",
            headers=normal_user_token_headers,
        )

>       assert response.status_code == 400
E       assert 404 == 400
E        +  where 404 = <Response [404 Not Found]>.status_code

app/tests/test_petri_timeline.py:82: AssertionError
------------------------------------------------- Captured stderr call -------------------------------------------------
INFO:httpx:HTTP Request: POST http://testserver/api/v1/user-personas/50b076bf-15f0-4bf4-bb77-0b35bc1034e5/stories/dcbbaf70-7549-491b-9c3b-0300226cef70/undo "HTTP/1.1 404 Not Found"
-------------------------------------------------- Captured log call ---------------------------------------------------
INFO     httpx:_client.py:1025 HTTP Request: POST http://testserver/api/v1/user-personas/50b076bf-15f0-4bf4-bb77-0b35bc1034e5/stories/dcbbaf70-7549-491b-9c3b-0300226cef70/undo "HTTP/1.1 404 Not Found"
________________________________________________ test_jump_to_ancestor _________________________________________________

client = <starlette.testclient.TestClient object at 0x79e41575ea10>
db = <sqlmodel.orm.session.Session object at 0x79e4157137c0>
normal_user_token_headers = {'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjgyNDM4NjAsInN1YiI6ImEyZDQ3MmJhLWYyMjgtNGI3Yi1hOGZjLWNkMjQ0N2NkOGFhMSJ9.Rtzvso4vZ-U5DmA6Nx3jItPxFUmg9Jarpb9pn8vhZks'}
db_story_with_progress = (Story(published_version=None, created_at=datetime.datetime(2026, 1, 4, 18, 51, 0, 999480), owner_id=UUID('b550a0af-10...e272a6-c9a7-4243-b4e3-96d44280dd63'), head_choice_id=None, updated_at=datetime.datetime(2026, 1, 4, 18, 51, 1, 10008)))

    def test_jump_to_ancestor(
        client: TestClient,
        db: Session,
        normal_user_token_headers: dict[str, str],
        db_story_with_progress: tuple,
    ) -> None:
        """
        Test that jump moves head to specified ancestor.

        Given: Chain A → B → C → D, head at D
        When: POST /jump with target=B
        Then: head moves to B, state replayed from B
        """
        story, progress = db_story_with_progress
        persona_id = progress.user_persona_id

        # Make 4 choices
        choice_ids = []
        for _ in range(4):
            response = client.get(
                f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
                headers=normal_user_token_headers,
            )
>           choice_id = response.json()["available_choices"][0]["id"]
E           KeyError: 'available_choices'

app/tests/test_petri_timeline.py:109: KeyError
------------------------------------------------- Captured stderr call -------------------------------------------------
INFO:httpx:HTTP Request: GET http://testserver/api/v1/user-personas/20baaf38-837a-42ad-a385-1aa407d1af86/stories/6ee272a6-c9a7-4243-b4e3-96d44280dd63/current-node "HTTP/1.1 404 Not Found"
-------------------------------------------------- Captured log call ---------------------------------------------------
INFO     httpx:_client.py:1025 HTTP Request: GET http://testserver/api/v1/user-personas/20baaf38-837a-42ad-a385-1aa407d1af86/stories/6ee272a6-c9a7-4243-b4e3-96d44280dd63/current-node "HTTP/1.1 404 Not Found"
_________________________________________ test_jump_non_ancestor_returns_error _________________________________________

client = <starlette.testclient.TestClient object at 0x79e41575ea10>
db = <sqlmodel.orm.session.Session object at 0x79e4157137c0>
normal_user_token_headers = {'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjgyNDM4NjAsInN1YiI6ImEyZDQ3MmJhLWYyMjgtNGI3Yi1hOGZjLWNkMjQ0N2NkOGFhMSJ9.Rtzvso4vZ-U5DmA6Nx3jItPxFUmg9Jarpb9pn8vhZks'}
db_story_with_progress = (Story(published_version=None, created_at=datetime.datetime(2026, 1, 4, 18, 51, 1, 29982), owner_id=UUID('b550a0af-107...9e0e36-9cb7-463e-9b89-85eeed5500d8'), head_choice_id=None, updated_at=datetime.datetime(2026, 1, 4, 18, 51, 1, 41327)))

    def test_jump_non_ancestor_returns_error(
        client: TestClient,
        db: Session,
        normal_user_token_headers: dict[str, str],
        db_story_with_progress: tuple,
    ) -> None:
        """
        Test that jump to non-ancestor returns 400 error.

        Given: Linear chain A → B, head at B
        When: Create abandoned branch C from A (via manual DB insert)
        And: POST /jump with target=C
        Then: Returns 400 "not an ancestor"
        """
        story, progress = db_story_with_progress
        persona_id = progress.user_persona_id

        # Make 2 choices (A → B)
        for _ in range(2):
            response = client.get(
                f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
                headers=normal_user_token_headers,
            )
>           choice_id = response.json()["available_choices"][0]["id"]
E           KeyError: 'available_choices'

app/tests/test_petri_timeline.py:164: KeyError
------------------------------------------------- Captured stderr call -------------------------------------------------
INFO:httpx:HTTP Request: GET http://testserver/api/v1/user-personas/3dd2116a-06fc-4a07-ada2-a65f1cebfb08/stories/809e0e36-9cb7-463e-9b89-85eeed5500d8/current-node "HTTP/1.1 404 Not Found"
-------------------------------------------------- Captured log call ---------------------------------------------------
INFO     httpx:_client.py:1025 HTTP Request: GET http://testserver/api/v1/user-personas/3dd2116a-06fc-4a07-ada2-a65f1cebfb08/stories/809e0e36-9cb7-463e-9b89-85eeed5500d8/current-node "HTTP/1.1 404 Not Found"
___________________________________________ test_jump_optimistic_concurrency ___________________________________________

client = <starlette.testclient.TestClient object at 0x79e41575ea10>
db = <sqlmodel.orm.session.Session object at 0x79e4157137c0>
normal_user_token_headers = {'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjgyNDM4NjAsInN1YiI6ImEyZDQ3MmJhLWYyMjgtNGI3Yi1hOGZjLWNkMjQ0N2NkOGFhMSJ9.Rtzvso4vZ-U5DmA6Nx3jItPxFUmg9Jarpb9pn8vhZks'}
db_story_with_progress = (Story(published_version=None, created_at=datetime.datetime(2026, 1, 4, 18, 51, 1, 61432), owner_id=UUID('b550a0af-107...660591-a9ce-486d-a9c1-5afde2d46085'), head_choice_id=None, updated_at=datetime.datetime(2026, 1, 4, 18, 51, 1, 71458)))

    def test_jump_optimistic_concurrency(
        client: TestClient,
        db: Session,
        normal_user_token_headers: dict[str, str],
        db_story_with_progress: tuple,
    ) -> None:
        """
        Test that jump rejects stale head_version.

        Given: Progress at version N
        When: POST /jump with expected_head_version=N-1
        Then: Returns 409 conflict
        """
        story, progress = db_story_with_progress
        persona_id = progress.user_persona_id

        # Make choice
        response = client.get(
            f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
            headers=normal_user_token_headers,
        )
>       choice_id = response.json()["available_choices"][0]["id"]
E       KeyError: 'available_choices'

app/tests/test_petri_timeline.py:225: KeyError
------------------------------------------------- Captured stderr call -------------------------------------------------
INFO:httpx:HTTP Request: GET http://testserver/api/v1/user-personas/a757924e-8c9a-48b1-896b-67c3e7f0c8d0/stories/96660591-a9ce-486d-a9c1-5afde2d46085/current-node "HTTP/1.1 404 Not Found"
-------------------------------------------------- Captured log call ---------------------------------------------------
INFO     httpx:_client.py:1025 HTTP Request: GET http://testserver/api/v1/user-personas/a757924e-8c9a-48b1-896b-67c3e7f0c8d0/stories/96660591-a9ce-486d-a9c1-5afde2d46085/current-node "HTTP/1.1 404 Not Found"
_________________________________________ test_timeline_shows_active_path_only _________________________________________

client = <starlette.testclient.TestClient object at 0x79e41575ea10>
db = <sqlmodel.orm.session.Session object at 0x79e4157137c0>
normal_user_token_headers = {'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjgyNDM4NjAsInN1YiI6ImEyZDQ3MmJhLWYyMjgtNGI3Yi1hOGZjLWNkMjQ0N2NkOGFhMSJ9.Rtzvso4vZ-U5DmA6Nx3jItPxFUmg9Jarpb9pn8vhZks'}
db_story_with_progress = (Story(published_version=None, created_at=datetime.datetime(2026, 1, 4, 18, 51, 1, 93713), owner_id=UUID('b550a0af-107...0c36a-c22f-4e02-aea0-d5f4b388987e'), head_choice_id=None, updated_at=datetime.datetime(2026, 1, 4, 18, 51, 1, 103564)))

    def test_timeline_shows_active_path_only(
        client: TestClient,
        db: Session,
        normal_user_token_headers: dict[str, str],
        db_story_with_progress: tuple,
    ) -> None:
        """
        Test that timeline returns only active path, not abandoned branches.

        Given: Path A → B → C, then undo to A, then make D (abandons B, C)
        When: GET /timeline
        Then: Returns [Start, A, D] only (not B or C)
        """
        story, progress = db_story_with_progress
        persona_id = progress.user_persona_id

        # Make 3 choices (A → B → C)
        for i in range(3):
            response = client.get(
                f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
                headers=normal_user_token_headers,
            )
>           choice_id = response.json()["available_choices"][0]["id"]
E           KeyError: 'available_choices'

app/tests/test_petri_timeline.py:272: KeyError
------------------------------------------------- Captured stderr call -------------------------------------------------
INFO:httpx:HTTP Request: GET http://testserver/api/v1/user-personas/5b95b43c-7cbd-4658-88a2-9f9b6a062dcd/stories/6b40c36a-c22f-4e02-aea0-d5f4b388987e/current-node "HTTP/1.1 404 Not Found"
-------------------------------------------------- Captured log call ---------------------------------------------------
INFO     httpx:_client.py:1025 HTTP Request: GET http://testserver/api/v1/user-personas/5b95b43c-7cbd-4658-88a2-9f9b6a062dcd/stories/6b40c36a-c22f-4e02-aea0-d5f4b388987e/current-node "HTTP/1.1 404 Not Found"
______________________________________ test_make_choice_after_undo_creates_branch ______________________________________

client = <starlette.testclient.TestClient object at 0x79e41575ea10>
db = <sqlmodel.orm.session.Session object at 0x79e4157137c0>
normal_user_token_headers = {'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjgyNDM4NjAsInN1YiI6ImEyZDQ3MmJhLWYyMjgtNGI3Yi1hOGZjLWNkMjQ0N2NkOGFhMSJ9.Rtzvso4vZ-U5DmA6Nx3jItPxFUmg9Jarpb9pn8vhZks'}
db_story_with_progress = (Story(published_version=None, created_at=datetime.datetime(2026, 1, 4, 18, 51, 1, 124157), owner_id=UUID('b550a0af-10...8daa6-7aa7-4e12-a396-d3843defc75f'), head_choice_id=None, updated_at=datetime.datetime(2026, 1, 4, 18, 51, 1, 133598)))

    def test_make_choice_after_undo_creates_branch(
        client: TestClient,
        db: Session,
        normal_user_token_headers: dict[str, str],
        db_story_with_progress: tuple,
    ) -> None:
        """
        Test that making choice after undo creates new branch.

        Given: Chain A → B, head at B
        When: Undo to A, then make choice C
        Then: Tree is A → B (abandoned), A → C (active)
        And: Timeline shows only [Start, A, C]
        """
        story, progress = db_story_with_progress
        persona_id = progress.user_persona_id

        # Make 2 choices (A → B)
        for _ in range(2):
            response = client.get(
                f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
                headers=normal_user_token_headers,
            )
>           choice_id = response.json()["available_choices"][0]["id"]
E           KeyError: 'available_choices'

app/tests/test_petri_timeline.py:341: KeyError
------------------------------------------------- Captured stderr call -------------------------------------------------
INFO:httpx:HTTP Request: GET http://testserver/api/v1/user-personas/4cbda0be-0462-44ed-835d-3ba981b05606/stories/d378daa6-7aa7-4e12-a396-d3843defc75f/current-node "HTTP/1.1 404 Not Found"
-------------------------------------------------- Captured log call ---------------------------------------------------
INFO     httpx:_client.py:1025 HTTP Request: GET http://testserver/api/v1/user-personas/4cbda0be-0462-44ed-835d-3ba981b05606/stories/d378daa6-7aa7-4e12-a396-d3843defc75f/current-node "HTTP/1.1 404 Not Found"
----------------------------------------------- Captured stderr teardown -----------------------------------------------
INFO:app.tests.conftest:Cleaning up test database
------------------------------------------------ Captured log teardown -------------------------------------------------
INFO     app.tests.conftest:conftest.py:55 Cleaning up test database
=================================================== warnings summary ===================================================
[note: snipped logger warnings]
=============================================== short test summary info ================================================
FAILED app/tests/test_petri_timeline.py::test_undo_moves_to_parent - KeyError: 'available_choices'
FAILED app/tests/test_petri_timeline.py::test_undo_at_start_returns_error - assert 404 == 400
FAILED app/tests/test_petri_timeline.py::test_jump_to_ancestor - KeyError: 'available_choices'
FAILED app/tests/test_petri_timeline.py::test_jump_non_ancestor_returns_error - KeyError: 'available_choices'
FAILED app/tests/test_petri_timeline.py::test_jump_optimistic_concurrency - KeyError: 'available_choices'
FAILED app/tests/test_petri_timeline.py::test_timeline_shows_active_path_only - KeyError: 'available_choices'
FAILED app/tests/test_petri_timeline.py::test_make_choice_after_undo_creates_branch - KeyError: 'available_choices'
============================================ 7 failed, 5 warnings in 0.77s =============================================