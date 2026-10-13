# Design

## Context

See [proposal.md](file:///Users/sbhattacharya/code/sayan/demo/devops-tutor/openspec/changes/fix-resumed-session-silence/proposal.md) for motivation and problem background.

The DevOps Voice Tutor uses LiveKit Cloud with automatic agent dispatch. The application stores conversation state in Redis under `session:<session_id>:*`. During investigation, two root causes were verified:
1. LiveKit Cloud automatic dispatch executes only once per unique room name. Reusing the previous room name during session resumption resulted in a room with no agent worker.
2. In LiveKit Agents 1.8.2, `session.history` and `agent._chat_ctx` are distinct objects. Restoring prior turns only to `session.history` left the agent's internal chat context empty, breaking turn continuity and subsequent speech handling.

## Goals / Non-Goals

**Goals:**
- Guarantee immediate agent worker dispatch on every session join and resumption by issuing unique WebRTC room names.
- Decouple the ephemeral WebRTC room name from the persistent Redis `session_id`.
- Provide a deterministic session ID resolver (`extract_session_id`) in `agent/src/agent.py`.
- Synchronize restored conversation turns into both `session.history` and `agent.update_chat_ctx(...)`.
- Ensure the agent speaks the resumption greeting and actively listens for learner voice turns upon resumption.
- Maintain backward compatibility with un-delimited room names in existing test suites.

**Non-Goals:**
- Changing Redis schema or key formats (`session:<session_id>:*` remains the contract).
- Adding complex server-side dispatch toggles or changing the agent worker registration pattern defined in `.agents/AGENTS.md`.

## Decisions

### Decision 1: Delimited Unique Room Name Pattern (`<session_id>--call-<nonce>`)
- **Choice**: When issuing a LiveKit token in `backend/src/main.py`, generate a unique room name formatted as `{session_id}--call-{uuid.uuid4().hex[:8]}` for both new and resumed sessions.
- **Rationale**: LiveKit Cloud recognizes every unique room name as a fresh room requiring automatic agent dispatch. Because the session ID is preserved as the prefix before `--`, the agent worker extracts `session_id = room_name.split("--")[0]` with zero network calls or out-of-band coordination.
- **Alternatives Considered**:
  - *Deleting the room via LiveKit Room API before reconnecting*: Empirically rejected. LiveKit Cloud auto-dispatch does not re-dispatch to a previously used room name even after explicit deletion.
  - *Explicit dispatch via LiveKit AgentDispatchServiceClient*: Rejected because `.agents/AGENTS.md` explicitly mandates no dispatch toggles and automatic worker registration.
  - *Passing session ID in room metadata*: Feasible, but room name encoding is simpler, immediately available before room metadata fetch, and works seamlessly with all LiveKit token grants.

### Decision 2: Synchronized Dual Chat Context Restoration
- **Choice**: In `agent/src/agent.py`, when `prior_turns` exist in Redis, restore messages to both `session.history` and `await agent.update_chat_ctx(restored_ctx)`.
- **Rationale**: `AgentActivity` uses `self._agent._chat_ctx` for pipeline replies and creates copies for `on_user_turn_completed`. Populating both guarantees that initial greeting replies and subsequent user voice turns retain the full transcript history.
- **Alternatives Considered**:
  - *Only populating `agent.chat_ctx`*: Rejected because `session.history` is used by the LiveKit session host and handoff events.
  - *Only passing `chat_ctx` to `generate_reply`*: Rejected because subsequent user audio turns use `self._agent.chat_ctx`, leaving later turns without context.

### Decision 3: Update TokenResponse with Session ID
- **Choice**: Add `session_id: str` to `TokenResponse` in `backend/src/main.py`. The frontend stores `sessionId` for session-scoped operations (`/api/session/${sessionId}/feedback`) and connects to `data.room_name`.
- **Rationale**: Decouples the logical session from the WebRTC transport room in the client cleanly.

## Risks / Trade-offs

- **[Risk] Backward compatibility with existing tests and raw room names** → Mitigation: `extract_session_id(room_name: str)` checks if `"--"` is present. If absent, it returns `room_name` as-is, ensuring all existing tests pass without modification.
- **[Risk] Multiple rooms per session in LiveKit Cloud** → Mitigation: Ephemeral rooms cleanly terminate and close when the participant leaves; LiveKit auto-cleans empty rooms within its configured timeout.
- **[Risk] LLM silence when last turn in history is an assistant message** → Mitigation: Resumption greeting instructions guide the LLM to welcome the learner back and invite continuation.
