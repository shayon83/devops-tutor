# devops-voice-tutor Specification

## Purpose
Provides a real-time, low-latency DevOps voice tutoring web application powered by LiveKit WebRTC, Direct Speech-to-Speech LLM inference, Redis state management, and a Grafana telemetry stack.

## Requirements

### Requirement: Real-Time WebRTC Audio Session Initialization
The system SHALL issue secure LiveKit JWT tokens and establish a bidirectional WebRTC audio session between the user's browser and the LiveKit Agent worker using environment variables loaded strictly from `.env`.

#### Scenario: Successful WebRTC session join
- **WHEN** the user launches the application and clicks "Start Tutoring Session"
- **THEN** the backend API validates configuration secrets from `.env`, generates a signed LiveKit JWT, and the frontend connects to the LiveKit room with active audio streaming.

### Requirement: Socratic DevOps Voice Interaction and Dual-Pipeline Support
The LiveKit Agent worker SHALL process voice turns using a Socratic SRE persona with Direct Speech-to-Speech LLM inference (~350ms response latency), while supporting configurable `.env` feature flags (`VOICE_PIPELINE_MODE=realtime|modular`) to switch between realtime audio streaming and modular cascaded VAD + STT + LLM + TTS processing.

#### Scenario: Real-time voice interaction with Socratic response
- **WHEN** the student speaks a DevOps question or answer into the microphone
- **THEN** the agent responds concisely (< 3 sentences) in a warm, Socratic SRE voice and asks a follow-up guiding question.

#### Scenario: Pipeline mode toggle via environment variable
- **WHEN** `VOICE_PIPELINE_MODE` is set to `modular` in `.env`
- **THEN** the agent worker instantiates the modular VAD (Silero) + Deepgram STT + LLM (GPT-4o-mini/Gemini) + ElevenLabs/OpenAI TTS pipeline without altering the WebRTC or Redis interface.

#### Scenario: LiveKit Managed Inference mode toggle
- **WHEN** `AGENT_DISPATCH_TYPE` is set to `cloud` in `.env`
- **THEN** the agent worker connects and routes audio and AI tokens through LiveKit Cloud managed infrastructure.

### Requirement: Real-Time DevOps Visual Workspace Rendering
The system SHALL transmit visual workspace payloads (Mermaid.js architectural diagrams, YAML manifests, syntax-highlighted code cards) over the LiveKit WebRTC Data Channel (`DataTrack`) for real-time rendering in the Web UI.

#### Scenario: Live Mermaid diagram rendering during explanation
- **WHEN** the tutor explains a Kubernetes deployment rollout or CI/CD pipeline
- **THEN** the agent emits a structured data packet over the LiveKit Data Channel and the frontend UI dynamically renders the corresponding Mermaid.js architectural diagram.

### Requirement: Redis State Management and Session Persistence
The system SHALL persist all conversation turns, lesson summaries, takeaways, and user preferences in Redis 7 with automatic session metadata indexing and TTL support.

#### Scenario: Session state synchronization to Redis
- **WHEN** a voice turn or lesson milestone completes
- **THEN** the agent worker asynchronously writes the conversation turn and summary key-value data to Redis under `session:<session_id>:*`.

### Requirement: Observability Telemetry and Pre-Configured Grafana Dashboards
The system SHALL expose Prometheus metrics for RED signals, End-to-End voice turn latency, barge-in frequency, and talk-time ratios, while scraping native LiveKit SFU metrics (`livekit_room_count`, `livekit_audio_packet_loss_ratio`, `livekit_audio_jitter_ms`), shipping container logs to Loki and provisioning Grafana dashboards automatically on startup.

#### Scenario: Prometheus metric scraping and Grafana dashboard visualization
- **WHEN** voice turns occur during an active session
- **THEN** Prometheus scrapes latency and turn metrics from the application endpoints and Grafana displays real-time latency waterfall and session health dashboards on port 3000.

#### Scenario: Native LiveKit SFU Prometheus metrics scraping
- **WHEN** Prometheus scrapes metrics from the configured targets
- **THEN** Prometheus collects both application turn metrics and native LiveKit SFU audio quality metrics for Grafana visualization.

### Requirement: Post-Session Learner CSAT Feedback Collection
The system SHALL prompt the user for post-session rating (1–5 stars) and qualitative feedback tags upon ending a session, storing responses in Redis and exporting satisfaction metrics to Prometheus.

#### Scenario: Submitting post-session feedback
- **WHEN** the user ends a tutoring session and submits a 5-star rating with quick feedback tags
- **THEN** the frontend POSTs the feedback to the backend API, saving it to Redis and updating `voice_tutor_csat_rating_stars` metrics in Prometheus.

### Requirement: Single-Command Docker Compose Packaging
The system SHALL provide a `docker-compose.yml` file that builds and orchestrates `frontend`, `backend`, `agent`, `redis`, `prometheus`, `loki`, and `grafana` containers reading configuration entirely from `.env`.

#### Scenario: Launching the entire stack with docker compose
- **WHEN** an evaluator clones the repository, copies `.env.example` to `.env`, and runs `docker compose up --build`
- **THEN** all application and observability containers build, initialize, and run cleanly without hardcoded secret errors.

### Requirement: Agent Worker Dispatch and Deployment Target Control
The system SHALL support an explicit environment configuration (`AGENT_DISPATCH_TYPE=local|cloud`) to govern agent worker lifecycle and room job dispatch independently of the voice pipeline processing mode.

#### Scenario: Self-hosted local container worker dispatch
- **WHEN** `AGENT_DISPATCH_TYPE` is set to `local` in `.env`
- **THEN** the agent worker initializes within the local container environment (Docker Compose) and registers directly with the LiveKit SFU instance to listen for incoming room job requests.

#### Scenario: LiveKit Cloud managed serverless dispatch
- **WHEN** `AGENT_DISPATCH_TYPE` is set to `cloud` in `.env`
- **THEN** room connection requests automatically route job dispatching to LiveKit Cloud Agents serverless infrastructure.
