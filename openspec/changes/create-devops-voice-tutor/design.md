# Technical Design: DevOps Voice Tutor Web Application

## Context

See `proposal.md` for overall motivation. The project requires building an interactive DevOps Voice Tutor application utilizing LiveKit for WebRTC voice communication, an LLM for Socratic tutoring, Redis for session state, Prometheus/Grafana for observability, and single-command Docker Compose orchestration.

## Goals / Non-Goals

**Goals:**
- Provide ultra-low latency (~350ms) natural voice interaction using Direct Speech-to-Speech LLM (OpenAI/Gemini Realtime API).
- Provide a `VOICE_PIPELINE_MODE=realtime|modular` feature flag toggle using the Factory Pattern for testing modular STT->LLM->TTS pipelines.
- Render live interactive DevOps workspace assets (Mermaid.js architectural diagrams, YAML code cards) over LiveKit Data Channels.
- Store session history, user preferences, takeaways, and CSAT feedback in Redis 7.
- Instrument RED metrics, E2E voice turn latency, barge-in rates, and CSAT ratings in Prometheus & Grafana.
- Zero hardcoded secrets, reading strictly from `.env`.

**Non-Goals:**
- Building a custom WebRTC SFU (we leverage LiveKit Cloud / Server).
- Training or fine-tuning custom LLM models.

## System Topology & Data Flow

```text
                               +--------------------------------------------+
                               |              DOCKER COMPOSE                |
                               |                                            |
 +------------------+          |  +------------------+                      |
 |   User Browser   | <=======>|  |  frontend (Web)  | Nginx / Vite static  |
 | (WebRTC + Audio) |          |  +------------------+                      |
 +------------------+          |                                            |
          ||                   |  +------------------+  Logs (stdout)       |
          || WebRTC Audio      |  |  backend (API)   | -------------------+ |
          v                    |  |  Token & State   |                    | |
 +------------------+          |  +------------------+                    | |
 |  LiveKit Cloud   |          |           |                              | |
 |  (or Local SFU)  |          |           v                              | |
 +------------------+          |  +------------------+                    | |
          ^                    |  |  redis (Store)   |                    v v
          || WebRTC Audio      |  | Session/History  |           +--------------------+
          v                    |  +------------------+           |    Loki (Logs)     |
 +------------------+          |           ^                     +--------------------+
 |   agent Worker   | <====================+ (Sync turns & state)         ^
 | (Python/LiveKit) |          |                                          |
 +------------------+          |                                          v
                               |  +-------------------+          +--------------------+
                               |  | Prometheus        | -------->| Grafana Dashboards |
                               |  | (Metrics Engine)  |          | (Port 3000)        |
                               |  +-------------------+          +--------------------+
                               +--------------------------------------------+
```

## Decisions

### 1. Backend Architecture: Python (FastAPI) + LiveKit Agents Python SDK
- **Decision**: Use Python for the `agent` worker service with `livekit-agents` and FastAPI for the `backend` API.
- **Rationale**: Python's LiveKit Agents SDK has native support for Voice Activity Detection (VAD), barge-in handling, and standard plugins for OpenAI Realtime, Gemini Multimodal Live, Deepgram, and ElevenLabs.
- **Alternatives Considered**: Node.js LiveKit SDK (fewer turnkey voice pipeline abstractions).

### 2. Voice AI Pipeline: Direct Speech-to-Speech with Factory Pattern Toggle
- **Decision**: Default to Direct Speech-to-Speech (Realtime API) for ~350ms latency and expressive human voice prosody. Implement a `VoicePipelineFactory` in Python that instantiates either `MultimodalAgent` or `VoicePipelineAgent` based on `VOICE_PIPELINE_MODE` in `.env`.
- **Rationale**: Gives learners an outstanding conversational experience while allowing evaluators to switch to modular STT->LLM->TTS for step-by-step latency inspection.
- **Alternatives Considered**: Fixed modular pipeline (robotic TTS, ~900ms latency).

### 3. Real-Time Workspace Transport: LiveKit Data Channels (`DataTrack`)
- **Decision**: Emit structured JSON events (`[DIAGRAM: ...]`, `[YAML: ...]`) directly over the existing WebRTC Data Channel.
- **Rationale**: Eliminates the need to maintain secondary WebSocket servers or HTTP polling loops.
- **Alternatives Considered**: Server-Sent Events (SSE) or custom WebSockets over FastAPI.

### 4. Telemetry Stack: Prometheus + Loki + Grafana
- **Decision**: Use `prometheus_client` in Python to expose `/metrics` endpoints. Configure Loki for log aggregation and auto-provision 3 Grafana dashboards (Web Infrastructure, Voice Latency Waterfall, and Tutor Quality & CSAT).
- **Rationale**: Enterprise-grade observability out of the box with `docker compose up`.

---

## Risks & Trade-offs

- **[Risk]** High API costs if Realtime voice sessions run indefinitely.
  - *Mitigation*: Implement session timeouts (e.g. 15 minutes) and TTL expiry on Redis keys.
- **[Risk]** Audio packet loss on poor client networks.
  - *Mitigation*: Monitor LiveKit packet loss and jitter metrics in Grafana; display connection quality status on the Web UI.

---

## 10,000 Concurrent Sessions Scaling Strategy (For README)

1. **State Tier**: Migrate single Redis instance to a **Redis Cluster** with sharding on `session_id` hash tags (`session:{<session_id>}:...`).
2. **Agent Tier**: Scale LiveKit Agent workers horizontally on Kubernetes using HPA (Horizontal Pod Autoscaler) based on CPU/RAM and active job metrics. LiveKit Server's built-in **Job Dispatcher** automatically distributes incoming room job requests (`JobRequest`) across the pool of registered Agent Worker instances.
3. **API Tier**: Keep token backend stateless behind AWS ALB / NGINX ingress.
