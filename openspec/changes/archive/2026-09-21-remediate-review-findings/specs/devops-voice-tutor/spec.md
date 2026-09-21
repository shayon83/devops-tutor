# Spec Delta

## MODIFIED Requirements

### Requirement: Real-Time WebRTC Audio Session Initialization
The system SHALL issue secure LiveKit JWT tokens and establish a bidirectional WebRTC audio session between the user's browser and the LiveKit Agent worker, using credentials loaded strictly from `.env`. The backend SHALL generate the room name and participant identity, and SHALL fail at startup when a LiveKit credential is missing or still set to its `.env.example` placeholder.

#### Scenario: Successful WebRTC session join
- **WHEN** the user launches the application and clicks "Start Voice Lesson"
- **THEN** the backend generates a room name and participant identity, signs a LiveKit JWT with credentials from `.env`, and the frontend connects to that room with active audio streaming.

#### Scenario: Missing or placeholder credentials
- **WHEN** `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` or `LIVEKIT_URL` is absent or still holds its `.env.example` placeholder
- **THEN** the backend raises a configuration error at startup naming the variable, rather than issuing tokens that cannot connect.

#### Scenario: Client cannot choose its own room
- **WHEN** a client includes a `room_name` or `participant_identity` in the token request
- **THEN** the backend ignores them and returns a server-generated room name and identity.

### Requirement: Socratic DevOps Voice Interaction
The LiveKit Agent worker SHALL process voice turns using a Socratic SRE persona with a cascaded pipeline (STT → LLM → TTS) served by LiveKit Inference (`from livekit.agents import inference`), requiring no third-party model provider API keys. The model IDs SHALL be configurable via `STT_MODEL`, `LLM_MODEL` and `TTS_MODEL` in `.env`.

#### Scenario: Real-time voice interaction with Socratic response
- **WHEN** the student speaks a DevOps question or answer into the microphone
- **THEN** the agent responds concisely (< 3 sentences) in a warm, Socratic SRE voice and asks a follow-up guiding question.

#### Scenario: Agent greets the learner first
- **WHEN** the agent session starts for a room
- **THEN** the agent speaks a greeting via `session.generate_reply(...)` before the learner has said anything.

#### Scenario: Lesson is anchored to the chosen subject
- **WHEN** the learner selected a subject before starting, and the backend wrote it to `session:<room>:metadata`
- **THEN** the agent reads that subject from Redis on job start and includes it in its instructions.

#### Scenario: Model IDs are configurable and verified
- **WHEN** `STT_MODEL`, `LLM_MODEL` or `TTS_MODEL` is set in `.env`
- **THEN** the agent uses that model ID, and each default ID is one the installed LiveKit Agents SDK declares in its model type literals.

### Requirement: Real-Time DevOps Visual Workspace Rendering
The system SHALL transmit visual workspace payloads (Mermaid diagrams, YAML manifests, summary cards) over the LiveKit WebRTC data channel under the topic `visual`, and SHALL remove the corresponding tags from the spoken text, the transcript and the persisted history in a single place on the agent side.

#### Scenario: Live Mermaid diagram rendering during explanation
- **WHEN** the tutor explains a Kubernetes rollout or CI/CD pipeline and emits a `[DIAGRAM: ...]` tag
- **THEN** the agent publishes a data message on the `visual` topic and the frontend renders the Mermaid diagram, filtering on that topic.

#### Scenario: Spoken text streams before a tag closes
- **WHEN** the model is still generating a visual tag at the end of a response
- **THEN** the text preceding the tag has already been passed to TTS, rather than being held until the whole response is complete.

#### Scenario: Unclosed tag is discarded
- **WHEN** a response is truncated part-way through a visual tag
- **THEN** the incomplete tag content is dropped and never spoken or persisted.

### Requirement: Redis State Management and Session Persistence
The system SHALL persist session metadata, every conversation turn, and post-session feedback in Redis under `session:<session_id>:*` with a TTL, using an asynchronous client in the agent so Redis never blocks the voice event loop. Redis read and write failures SHALL degrade gracefully rather than failing a request.

#### Scenario: Conversation turns are persisted
- **WHEN** a user or assistant turn is added to the conversation
- **THEN** the agent appends the role, text, timestamp and interrupted flag to `session:<session_id>:history` and refreshes its TTL.

#### Scenario: Session is marked ended
- **WHEN** the agent job shuts down
- **THEN** `session:<session_id>:metadata` is updated with `status=ended` and `ended_at`.

#### Scenario: Redis is unavailable
- **WHEN** Redis cannot be reached
- **THEN** `/ready` reports the backend as degraded with HTTP 503, session endpoints return empty results marked `storage_available: false`, and no endpoint returns a 500.

### Requirement: Observability Telemetry and Pre-Configured Grafana Dashboards
The system SHALL expose Prometheus metrics for HTTP RED signals on every route, end-to-end voice turn latency, barge-in interruptions, active sessions and CSAT, ship container logs to Loki via Promtail, and provision Grafana dashboards and datasources on startup. Every metric on the dashboard SHALL be one the application actually records, and metric labels SHALL be bounded.

#### Scenario: Prometheus metric scraping and Grafana dashboard visualization
- **WHEN** voice turns occur during an active session
- **THEN** Prometheus scrapes `backend:8000` and `agent:8001`, and Grafana on port 3001 displays latency, interruption, active-session and CSAT panels populated from those metrics.

#### Scenario: Metrics recorded inside a job process are exported
- **WHEN** the agent records a metric inside a job, which runs in its own process
- **THEN** the sample is written to the worker's Prometheus multiprocess directory and appears on the worker's `/metrics` endpoint.

#### Scenario: Metric cardinality stays bounded
- **WHEN** many sessions complete and submit feedback
- **THEN** no metric gains a per-session label; CSAT is recorded as a histogram and HTTP metrics are labelled with the route template.

### Requirement: Post-Session Learner CSAT Feedback Collection
The system SHALL prompt the user for a post-session rating (1–5 stars) and qualitative feedback tags upon ending a session, storing responses in Redis and exporting satisfaction metrics to Prometheus.

#### Scenario: Submitting post-session feedback
- **WHEN** the user ends a tutoring session and submits a 5-star rating with quick feedback tags
- **THEN** the frontend POSTs the feedback to the backend API, which saves it to `session:<session_id>:feedback` and observes it on the `voice_tutor_csat_rating_stars` histogram.

#### Scenario: Rating outside the permitted range
- **WHEN** a rating below 1 or above 5 is submitted
- **THEN** the request is rejected with a validation error and nothing is written to Redis.

### Requirement: Single-Command Docker Compose Packaging
The system SHALL provide a `docker-compose.yml` that builds and orchestrates `frontend`, `backend`, `agent`, `redis`, `prometheus`, `loki`, `promtail` and `grafana` from a clean checkout, reading all configuration from `.env`, with no bind-mounted application source and no dependency on a local image cache.

#### Scenario: Launching the entire stack with docker compose
- **WHEN** an evaluator clones the repository, copies `.env.example` to `.env`, fills in the LiveKit credentials, and runs `docker compose up --build`
- **THEN** all application and observability containers build and start cleanly, with backend and frontend reporting healthy and Redis persisting to a named volume.

#### Scenario: Image contents match the repository
- **WHEN** the stack is started from a fresh clone with no override file present
- **THEN** no application source is bind-mounted over an image, so what runs is what was built.

## ADDED Requirements

### Requirement: Continuous Integration Verification
The system SHALL provide a GitHub Actions pipeline that, on every pull request and push to `main`, lints the code and Dockerfiles, runs the test suite against a real Redis, builds every compose image from a clean checkout, and smoke-tests the running stack.

#### Scenario: A dependency conflict is caught before merge
- **WHEN** a dependency change makes an image unbuildable from a clean checkout
- **THEN** the `build` job fails, independently of any local Docker layer cache.

#### Scenario: Smoke test asserts the stack is actually working
- **WHEN** the `smoke` job brings the stack up with dummy credentials
- **THEN** it asserts backend `/health` and `/ready` return 200, that an issued token's session appears in Redis, that the frontend serves the SPA, that no Prometheus target except the agent is down, that Grafana is healthy with the dashboard provisioned, and that the agent image can import its entrypoint and construct the Agent.

## REMOVED Requirements

### Requirement: Agent Worker Dispatch and Deployment Target Control
**Reason**: `AGENT_DISPATCH_TYPE` was removed from the code in the `simplify-app-architecture` change but survived in the master spec, along with the BYOK and `VOICE_PIPELINE_MODE` scenarios under "Socratic DevOps Voice Interaction and Dual-Pipeline Support". Nothing reads those variables.

**Migration**: None. The agent worker runs in the compose stack and registers with LiveKit Cloud using `LIVEKIT_URL`/`LIVEKIT_API_KEY`/`LIVEKIT_API_SECRET`; there is no dispatch or pipeline toggle.
