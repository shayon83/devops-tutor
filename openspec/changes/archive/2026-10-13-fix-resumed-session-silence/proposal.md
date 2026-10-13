# Proposal

## Why

When a learner resumes a prior session, the voice tutor remains completely silent and unresponsive to learner speech. LiveKit Cloud's automatic agent dispatch runs only once per unique room name, leaving reused room names unpopulated by an agent worker. Additionally, the agent worker did not synchronize restored Redis history into `agent._chat_ctx` (only updating `session.history`), causing speech and conversation turns to lack context and stall on resumption.

## What Changes

- **Unique Room Names for WebRTC Connections**: Update the backend token issuer (`POST /api/token`) so that each WebRTC audio connection receives a unique room name (e.g. `<session_id>--call-<nonce>`) while maintaining the persistent logical session ID in Redis.
- **Session ID Resolution**: Add a deterministic session ID resolver (`extract_session_id`) in the agent worker to map the WebRTC room name back to the underlying Redis session store (`session:<session_id>:*`).
- **Synchronized Chat Context Restoration**: When resuming a session with prior turns, populate both `session.history` and `agent.update_chat_ctx(...)` so that subsequent LLM turns and speech tasks possess full conversational history.
- **Resumption Greeting & Turn Initiation**: Ensure `session.generate_reply` on session resumption speaks the resumption greeting and leaves the voice pipeline actively listening for learner speech.
- **Frontend Session ID & Room Decoupling**: Update the frontend to track `sessionId` as the logical conversation handle (for history and CSAT feedback) while connecting to the unique `room_name` issued by LiveKit.

## Capabilities

### Modified Capabilities
- `devops-voice-tutor`: Updates `Real-Time WebRTC Audio Session Initialization` and `Socratic DevOps Voice Interaction` requirements to guarantee unique LiveKit room dispatch for session resumption, session ID resolution, complete chat context restoration on the agent, and responsive voice turn processing upon reconnection.

## Impact

- **Backend**: `backend/src/main.py` generates unique LiveKit room names per connection attempt while binding to the existing or new `session_id`, returning both in `TokenResponse`.
- **Agent**: `agent/src/agent.py` extracts the logical `session_id` from the room name to access Redis, restores prior turns to both `session.history` and `agent.update_chat_ctx`, and executes the resumption greeting.
- **Frontend**: `frontend/src/App.jsx` handles separate `sessionId` and LiveKit WebRTC `room_name`.
- **Tests**: Add unit and regression tests in `backend/tests/test_api.py` and `agent/tests/test_agent.py` covering unique room generation, session ID parsing, agent chat context restoration, and resume greeting replies.
