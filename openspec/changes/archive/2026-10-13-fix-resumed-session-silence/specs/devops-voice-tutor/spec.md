# Spec Delta

## MODIFIED Requirements

### Requirement: Real-Time WebRTC Audio Session Initialization
The system SHALL issue secure LiveKit JWT tokens and establish a bidirectional WebRTC audio session between the user's browser and the LiveKit Agent worker, using credentials loaded strictly from `.env`. The backend SHALL generate a unique WebRTC room name for every connection and reconnection, binding to a new session or an existing `resume_session_id`, and returning both the unique room name and the session ID. The backend SHALL fail at startup when a LiveKit credential is missing or still set to its `.env.example` placeholder.

#### Scenario: Successful WebRTC session join
- **WHEN** the user launches the application and clicks "Start Voice Lesson"
- **THEN** the backend generates a unique room name and participant identity, initializes a new session in Redis, signs a LiveKit JWT with credentials from `.env`, and the frontend connects to that room with active audio streaming.

#### Scenario: Resuming an existing session
- **WHEN** the user selects a prior session and requests a token with `resume_session_id`
- **THEN** the backend verifies that the session exists in Redis, sets its status back to active, signs a LiveKit JWT for a fresh unique room name bound to the existing `session_id`, and returns the token, unique room name, and session ID.

#### Scenario: Attempting to resume a non-existent or expired session
- **WHEN** a token request includes a `resume_session_id` that is not found in Redis
- **THEN** the backend returns an HTTP 404 error and does not issue a LiveKit token.

#### Scenario: Missing or placeholder credentials
- **WHEN** `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` or `LIVEKIT_URL` is absent or still holds its `.env.example` placeholder
- **THEN** the backend raises a configuration error at startup naming the variable, rather than issuing tokens that cannot connect.

#### Scenario: Client cannot choose its own room
- **WHEN** a client includes arbitrary unvalidated `room_name` or `participant_identity` in the token request without a valid resume target
- **THEN** the backend ignores them and returns a server-generated unique room name and identity.

### Requirement: Socratic DevOps Voice Interaction
The LiveKit Agent worker SHALL process voice turns using a Socratic SRE persona with a cascaded pipeline (STT → LLM → TTS) served by LiveKit Inference (`from livekit.agents import inference`), requiring no third-party model provider API keys. The model IDs SHALL be configurable via `STT_MODEL`, `LLM_MODEL` and `TTS_MODEL` in `.env`. When joining a room with pre-existing session history, the agent worker SHALL extract the underlying session ID, restore the previous turns into both the session history and the agent's chat context, and deliver a spoken resumption greeting that invites the learner to continue.

#### Scenario: Real-time voice interaction with Socratic response
- **WHEN** the student speaks a DevOps question or answer into the microphone
- **THEN** the agent responds concisely (< 3 sentences) in a warm, Socratic SRE voice and asks a follow-up guiding question.

#### Scenario: Agent greets the learner first
- **WHEN** the agent session starts for a new room without prior turns
- **THEN** the agent speaks a greeting via `session.generate_reply(...)` before the learner has said anything.

#### Scenario: Agent restores history and greets learner on resumed sessions
- **WHEN** the agent session starts for a room with existing turns in Redis history
- **THEN** the agent extracts the underlying session ID, loads prior conversation turns into both `session.history` and the agent's internal chat context, and speaks a contextual resumption greeting acknowledging where the conversation left off.

#### Scenario: Learner speaks after resuming session
- **WHEN** the learner speaks a DevOps question or comment into the microphone after resuming a session
- **THEN** the agent worker's STT pipeline captures the speech and the LLM produces a responsive turn utilizing the restored conversation context.

#### Scenario: Lesson is anchored to the chosen subject
- **WHEN** the learner selected a subject before starting, and the backend wrote it to `session:<room>:metadata`
- **THEN** the agent reads that subject from Redis on job start and includes it in its instructions.

#### Scenario: Model IDs are configurable and verified
- **WHEN** `STT_MODEL`, `LLM_MODEL` or `TTS_MODEL` is set in `.env`
- **THEN** the agent uses that model ID, and each default ID is one the installed LiveKit Agents SDK declares in its model type literals.
