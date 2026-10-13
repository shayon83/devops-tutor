# Proposal

## Why

Currently, every time a student interacts with the DevOps Voice Tutor, the application mints a fresh, random room name and user identity, discarding any previous context when the session terminates. Learners who disconnect or wish to continue troubleshooting a complex scenario (e.g. an ongoing incident simulation or Kubernetes debugging exercise) cannot resume where they left off. Enabling users to browse and resume their past sessions preserves educational momentum, maintains conversation context across disconnections, and improves the overall tutoring experience.

## What Changes

- **User Identity Continuity**: Introduce a lightweight, persistent client user identifier stored in browser `localStorage` and sent to the backend to correlate sessions for the learner without introducing an authentication wall.
- **Session Indexing by User**: Index session IDs by user in Redis (`user:<user_id>:sessions` sorted set) to support fast queries of a user's session history ordered by recency.
- **Session Summary Generation**: Generate and store a concise one-line summary in Redis session metadata (`session:<session_id>:metadata`) summarizing the topic/conversation, updating upon session shutdown or completion.
- **Session Listing API**: Add a backend endpoint `GET /api/sessions?user_id=...` returning the user's prior sessions, their one-line summaries, subjects, timestamps, and turn counts.
- **Resumed Session Token Minting**: Update `POST /api/token` to accept an optional `resume_session_id` and `user_id`. When specified, the backend validates session existence, re-activates the session, and issues a LiveKit JWT for the existing room name.
- **Agent Worker Context Restoration**: Update the LiveKit agent worker to inspect Redis history on job start. If prior turns exist, restore them into `AgentSession.history` (`ChatContext`) and emit an informed resume greeting referencing the prior topic rather than a cold start greeting.
- **Frontend Prior Sessions View & Resume**: Add a "Past Sessions" view/drawer in the frontend displaying prior sessions with their one-line summaries, subjects, and dates, with a one-click action to resume the session and restore existing transcripts in the UI workspace.

## Capabilities

### Modified Capabilities
- `devops-voice-tutor`: Updates session initialization to support resuming prior session rooms by ID, updates Redis state management to index sessions per user and maintain one-line session summaries, updates agent worker startup to restore chat context and deliver contextual resume greetings, and updates the frontend to view and resume prior sessions.

## Impact

- **Backend**: `backend/src/main.py` gains `GET /api/sessions` and `POST /api/token` accepts `resume_session_id` and `user_id`.
- **Shared State**: `shared/state/keys.py`, `shared/state/repository.py`, and `shared/state/async_repository.py` gain user-to-sessions indexing (`user:<user_id>:sessions`) and session summary handling.
- **Agent Worker**: `agent/src/agent.py` and `agent/src/tutor_prompts.py` load prior conversation turns into `session.history` and speak an appropriate resumption greeting when starting a resumed room.
- **Frontend**: `frontend/src/App.jsx`, `Header.jsx`, and a new `PastSessionsModal.jsx` (or drawer component) to list and resume sessions, storing the client user ID in `localStorage`.
- **Tests & CI**: Backend and agent unit tests updated to verify session listing, token issuance with resume IDs, context restoration, and summary generation.
