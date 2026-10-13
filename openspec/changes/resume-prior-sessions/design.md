# Design

## Context

The DevOps Voice Tutor currently treats each voice lesson as ephemeral. A new session generates a random room name (`devops-room-<uuid>`) and participant identity (`student-<uuid>`), persisting turns to Redis (`session:<room>:history`). Once disconnected, the room closes, and there is no way for the student to list or reconnect to that session.

See `proposal.md` for motivation and high-level scope.

## Goals / Non-Goals

**Goals:**
- Provide client-side user identification across browser sessions without requiring passwords or external authentication providers.
- Maintain a fast, sorted index of sessions per user in Redis (`user:<user_id>:sessions`).
- Automatically assign and persist a concise one-line summary for each session.
- Allow the user to view prior sessions in the UI and select one to resume.
- Restore previous conversation turns into LiveKit Agents `AgentSession.history` (`ChatContext`) and the frontend transcript panel when resuming.
- Use a dedicated resumption greeting from the tutor rather than a cold start greeting.

**Non-Goals:**
- Multi-user authentication, OAuth, or user registration flows.
- Merging disparate sessions into one.
- Editing or deleting past session transcripts from the UI.
- Synchronizing session history across multiple devices (browser `localStorage` scope is sufficient for demo usage).

## Decisions

### 1. Persistent Anonymous User Identifier
- **Decision**: Frontend generates a UUID on first load, stores it in browser `localStorage` as `devops_tutor_user_id`, and sends it with session listing and token requests.
- **Rationale**: Preserves the zero-setup, unauthenticated demo model while giving the backend a persistent identity key to group sessions.
- **Alternatives Considered**:
  - *IP-based tracking*: Ineffective across NAT, mobile networks, VPNs, and local Docker networking.
  - *OAuth / user login*: Introduces schema complexity, third-party credentials, and onboarding friction that violates the demo's design principles.

### 2. Redis Key Layout and Sorted Set Indexing
- **Decision**:
  - Use `user:<user_id>:sessions` as a Redis Sorted Set (ZSET), where the member is `session_id` and the score is the epoch timestamp of the last activity (`updated_at`).
  - Extend `session:<session_id>:metadata` to include `summary`, `user_id`, and `updated_at`.
  - Add helper methods in `shared/state/repository.py` and `async_repository.py`:
    - `index_user_session(user_id, session_id, timestamp)`
    - `get_user_sessions(user_id, limit=20)`
    - `update_summary(session_id, summary)`
- **Rationale**: ZSET allows retrieving a learner's recent sessions in reverse chronological order via `ZREVRANGEBYSCORE` or `ZREVRANGE` in $O(\log N + M)$ time, avoiding costly and unsafe `KEYS` or `SCAN` operations.
- **Alternatives Considered**:
  - *Redis List (`RPUSH`)*: Prone to duplicate entries when a session is resumed multiple times unless manually filtered.
  - *Scanning keys `session:*:metadata`*: Poor performance and unbounded CPU overhead in Redis.

### 3. One-Line Session Summary Generation
- **Decision**:
  - At session initialization, assign a default summary: `f"Discussion on {subject}"`.
  - In `agent/src/agent.py`, during session shutdown (`on_shutdown`), if the session has at least 2 turns and a non-empty history, the agent invokes LiveKit Inference LLM with a brief one-shot prompt requesting a summary in 8 words or fewer without terminal punctuation.
  - The generated summary is persisted to `session:<session_id>:metadata` via `repository.update_summary(session_id, summary)`.
  - If the LLM invocation fails or times out, the system falls back to a clean rule-based summary (e.g., `f"{subject}: {first_turn_snippet}"`) or retains the default.
- **Rationale**: Leverages the agent worker's existing LiveKit Inference LLM without burdening the backend with inference API dependencies, ensuring each past session has an intelligible, human-readable name in the UI.
- **Alternatives Considered**:
  - *Summarizing in the FastAPI backend*: Would require backend credentials for LLM providers, breaking the architectural rule that all inference happens in LiveKit Inference via the agent worker.
  - *Summarizing on every turn*: Incurs unnecessary latency and token usage during active voice conversation.

### 4. Agent Chat History Restoration on Session Resume
- **Decision**:
  - When the agent worker entrypoint starts in `agent/src/agent.py`:
    1. Fetches `history = await repository.get_history(room_name)`.
    2. If `history` is non-empty:
       - Iterates over turns and adds each to `session.history` (`ChatContext`) using `session.history.add_message(role=turn["role"], content=turn["text"])`.
       - Issues a resumption greeting via `session.generate_reply(instructions=RESUME_GREETING_INSTRUCTIONS.format(subject=subject))` instructing the tutor to welcome the student back, reference where they left off, and ask how to proceed.
    3. If `history` is empty:
       - Follows the existing flow: issues `GREETING_INSTRUCTIONS`.
- **Rationale**: `AgentSession.history` directly populates the LLM's conversation context. Restoring turns ensures the model remembers all prior questions, explanations, and diagrams seamlessly.
- **Alternatives Considered**:
  - *Stuffing history into the system prompt*: Degrades prompt structure and confuses multi-turn speaker attribution.

### 5. Frontend Session Browser and Resume Flow
- **Decision**:
  - Add a "Past Sessions" button in `Header.jsx`.
  - Introduce `PastSessionsModal.jsx` displaying the list of prior sessions retrieved from `GET /api/sessions?user_id=...`.
  - Each item card shows:
    - Session one-line summary
    - Subject tag
    - Relative date / time
    - Number of turns
    - "Resume Session" button
  - When "Resume" is clicked:
    1. The frontend calls `GET /api/session/{session_id}` to load the existing turns into `transcripts`.
    2. The frontend calls `POST /api/token` with `{ resume_session_id: sessionId, user_id }`.
    3. The frontend connects to the room and enters the active voice session workspace.
- **Rationale**: Gives users clear visual confirmation of their past discussion history and immediate access to resume their lesson.

## Risks / Trade-offs

- **[Risk] Room cleanup in LiveKit Cloud after session disconnect** → LiveKit Cloud automatically cleans up empty rooms after an empty timeout. Re-requesting a token with the same room name creates a fresh WebRTC session for that room name, while the agent restores the state from Redis.
- **[Risk] Agent shutdown summary latency** → The summary generation is awaited during `on_shutdown` with a strict 3-second timeout; if it times out, the shutdown continues without blocking container shutdown.
- **[Risk] Stale or expired Redis sessions** → Redis keys have a TTL (`DEFAULT_SESSION_TTL_SECONDS`). When an expired session is requested for resumption, the backend returns a clean 404 and the frontend notifies the user and cleans up the list.
