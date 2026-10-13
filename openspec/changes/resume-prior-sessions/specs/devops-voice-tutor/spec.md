# Spec Delta

## MODIFIED Requirements

### Requirement: Real-Time WebRTC Audio Session Initialization
The system SHALL issue secure LiveKit JWT tokens and establish a bidirectional WebRTC audio session between the user's browser and the LiveKit Agent worker, using credentials loaded strictly from `.env`. The backend SHALL generate the room name and participant identity for new sessions, or validate and bind to an existing session when a valid `resume_session_id` is supplied. The backend SHALL fail at startup when a LiveKit credential is missing or still set to its `.env.example` placeholder.

#### Scenario: Successful WebRTC session join
- **WHEN** the user launches the application and clicks "Start Voice Lesson"
- **THEN** the backend generates a room name and participant identity, signs a LiveKit JWT with credentials from `.env`, and the frontend connects to that room with active audio streaming.

#### Scenario: Resuming an existing session
- **WHEN** the user selects a prior session and requests a token with `resume_session_id`
- **THEN** the backend verifies that the session exists in Redis, sets its status back to active, signs a LiveKit JWT for the existing session room name, and returns the token and room details.

#### Scenario: Attempting to resume a non-existent or expired session
- **WHEN** a token request includes a `resume_session_id` that is not found in Redis
- **THEN** the backend returns an HTTP 404 error and does not issue a LiveKit token.

#### Scenario: Missing or placeholder credentials
- **WHEN** `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` or `LIVEKIT_URL` is absent or still holds its `.env.example` placeholder
- **THEN** the backend raises a configuration error at startup naming the variable, rather than issuing tokens that cannot connect.

#### Scenario: Client cannot choose its own room
- **WHEN** a client includes arbitrary unvalidated `room_name` or `participant_identity` in the token request without a valid resume target
- **THEN** the backend ignores them and returns a server-generated room name and identity.

### Requirement: Socratic DevOps Voice Interaction
The LiveKit Agent worker SHALL process voice turns using a Socratic SRE persona with a cascaded pipeline (STT → LLM → TTS) served by LiveKit Inference (`from livekit.agents import inference`), requiring no third-party model provider API keys. The model IDs SHALL be configurable via `STT_MODEL`, `LLM_MODEL` and `TTS_MODEL` in `.env`. When joining a room with pre-existing session history, the agent worker SHALL restore the previous turns into its conversation context and deliver a resumption greeting.

#### Scenario: Real-time voice interaction with Socratic response
- **WHEN** the student speaks a DevOps question or answer into the microphone
- **THEN** the agent responds concisely (< 3 sentences) in a warm, Socratic SRE voice and asks a follow-up guiding question.

#### Scenario: Agent greets the learner first
- **WHEN** the agent session starts for a room
- **THEN** the agent speaks a greeting via `session.generate_reply(...)` before the learner has said anything.

#### Scenario: Agent restores history and greets learner on resumed sessions
- **WHEN** the agent session starts for a room with existing turns in Redis history
- **THEN** the agent loads the prior conversation turns into its session chat history and speaks a contextual resumption greeting acknowledging where the conversation left off.

#### Scenario: Lesson is anchored to the chosen subject
- **WHEN** the learner selected a subject before starting, and the backend wrote it to `session:<room>:metadata`
- **THEN** the agent reads that subject from Redis on job start and includes it in its instructions.

#### Scenario: Model IDs are configurable and verified
- **WHEN** `STT_MODEL`, `LLM_MODEL` or `TTS_MODEL` is set in `.env`
- **THEN** the agent uses that model ID, and each default ID is one the installed LiveKit Agents SDK declares in its model type literals.

### Requirement: Redis State Management and Session Persistence
The system SHALL persist session metadata, every conversation turn, post-session feedback, one-line session summaries, and user session indices in Redis under `session:<session_id>:*` and `user:<user_id>:sessions` with a TTL, using an asynchronous client in the agent so Redis never blocks the voice event loop. Redis read and write failures SHALL degrade gracefully rather than failing a request.

#### Scenario: Conversation turns are persisted
- **WHEN** a user or assistant turn is added to the conversation
- **THEN** the agent appends the role, text, timestamp and interrupted flag to `session:<session_id>:history` and refreshes its TTL.

#### Scenario: User sessions are indexed
- **WHEN** a session is created or resumed with a `user_id`
- **THEN** the backend adds or updates the session ID in the user's sorted set `user:<user_id>:sessions` scored by recency timestamp.

#### Scenario: One-line session summary generation and storage
- **WHEN** an agent job finishes a session or conversation turns have occurred
- **THEN** the system stores a concise, one-line summary in `session:<session_id>:metadata` describing the topic covered.

#### Scenario: Listing past sessions for a user
- **WHEN** a client queries `GET /api/sessions?user_id=<user_id>`
- **THEN** the backend retrieves the user's indexed session IDs, fetches their metadata including one-line summaries and turn counts, and returns them sorted by recency.

#### Scenario: Session is marked ended
- **WHEN** the agent job shuts down
- **THEN** `session:<session_id>:metadata` is updated with `status=ended` and `ended_at`.

#### Scenario: Redis is unavailable
- **WHEN** Redis cannot be reached
- **THEN** `/ready` reports the backend as degraded with HTTP 503, session endpoints return empty results marked `storage_available: false`, and no endpoint returns a 500.

## ADDED Requirements

### Requirement: Learner Prior Session History and Resumption Interface
The frontend application SHALL allow learners to view their past tutoring sessions along with one-line summaries, and resume any past session, displaying previous transcripts and continuing voice interactions seamlessly.

#### Scenario: Viewing prior sessions list
- **WHEN** the learner opens the past sessions view in the web application
- **THEN** the application queries the backend for the user's prior sessions and displays each session with its one-line summary, subject tag, date, and turn count.

#### Scenario: Resuming a prior session from the UI
- **WHEN** the learner selects a prior session to resume and clicks resume
- **THEN** the frontend fetches the session's prior transcript turns into the workspace transcript view and connects to the LiveKit voice room for that session ID.
