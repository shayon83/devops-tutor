# Tasks

## 1. Backend Token & Room Generation

- [x] 1.1 Update `TokenResponse` in `backend/src/main.py` to include `session_id: str` alongside `room_name` and verify model validation in `backend/tests/test_api.py`
- [x] 1.2 Update `POST /api/token` in `backend/src/main.py` to generate unique room names formatted as `{session_id}--call-{nonce}` for both initial and resumed sessions while binding to the session ID in Redis, and verify with unit tests
- [x] 1.3 Add backend tests in `backend/tests/test_api.py` verifying that resuming a session produces a fresh unique room name while preserving the existing session ID and metadata

## 2. Agent Session Resolution & Chat Context Synchronization

- [x] 2.1 Implement `extract_session_id(room_name: str) -> str` in `agent/src/agent.py` and verify unit tests in `agent/tests/test_agent.py` with both delimited (`session--call-123`) and un-delimited (`room-abc`) room names
- [x] 2.2 Update `entrypoint` in `agent/src/agent.py` to resolve `session_id = extract_session_id(ctx.room.name)` for all Redis repository operations (`get_subject`, `get_history`, `append_turn`, `update_summary`, `end_session`)
- [x] 2.3 Update history restoration in `agent/src/agent.py` to populate both `session.history` and `await agent.update_chat_ctx(...)`, and verify with unit tests in `agent/tests/test_agent.py`
- [x] 2.4 Verify agent resume greeting invocation and ensure voice pipeline readiness for subsequent learner speech in `agent/src/agent.py`

## 3. Frontend Session Handling & Reconnection

- [x] 3.1 Update `frontend/src/App.jsx` in `handleStartSession` and `handleResumeSession` to store `sessionId` from `data.session_id || data.room_name` while connecting the WebRTC Room to `data.room_name`
- [x] 3.2 Ensure frontend audio track subscription and mic publish cleanly bind upon session resumption in `frontend/src/App.jsx`

## 4. Verification & Testing

- [x] 4.1 Run full pytest test suite (`pytest -q`) and verify all backend, agent, and shared state tests pass
- [x] 4.2 Run linter (`ruff check .`) and verify clean formatting and style
