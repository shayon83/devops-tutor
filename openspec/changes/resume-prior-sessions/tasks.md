# Tasks

## 1. Shared State & Redis Layer

- [x] 1.1 Add Redis key helper `user_sessions_key(user_id)` in `shared/state/keys.py` and verify with unit tests in `shared/state/tests/test_keys.py`.
- [x] 1.2 Implement `index_user_session`, `get_user_sessions`, and `update_summary` in `shared/state/repository.py` and verify by running repository tests against Redis.
- [x] 1.3 Implement async equivalents for user session indexing and summary updates in `shared/state/async_repository.py` and verify with async Redis tests.

## 2. Backend API

- [x] 2.1 Update `POST /api/token` in `backend/src/main.py` to accept `user_id` and optional `resume_session_id`, validate target session existence, and index the session; verify via unit tests in `backend/tests/test_token.py`.
- [x] 2.2 Add `GET /api/sessions` endpoint in `backend/src/main.py` querying prior sessions with one-line summaries for a user; verify with tests in `backend/tests/test_sessions.py`.

## 3. Agent Worker Context Restoration & Summary Generation

- [x] 3.1 Add `RESUME_GREETING_INSTRUCTIONS` in `agent/src/tutor_prompts.py` and verify prompt formatting via unit tests in `agent/tests/test_prompts.py`.
- [x] 3.2 Update `entrypoint` in `agent/src/agent.py` to populate `session.history` with existing turns when joining a room with pre-existing history and speak the resume greeting; verify with unit tests in `agent/tests/test_agent.py`.
- [x] 3.3 Add one-line summary generation on agent shutdown in `agent/src/agent.py` to persist a concise summary to Redis metadata; verify with unit tests in `agent/tests/test_agent.py`.

## 4. Frontend Past Sessions View & Resume Flow

- [x] 4.1 Introduce persistent `userId` management in `frontend/src/App.jsx` using `localStorage` and ensure it is passed to session token requests.
- [x] 4.2 Create `PastSessionsModal.jsx` to render the list of past sessions with one-line summaries, subjects, turn counts, and resume buttons.
- [x] 4.3 Add a "Past Sessions" button in `Header.jsx`, and connect session resumption in `App.jsx` to fetch prior transcripts and connect to the existing room name.

## 5. Verification & Testing

- [x] 5.1 Run `ruff check .` across the workspace and verify zero lint errors.
- [x] 5.2 Run backend and agent unit test suites with `pytest` and verify all tests pass.
