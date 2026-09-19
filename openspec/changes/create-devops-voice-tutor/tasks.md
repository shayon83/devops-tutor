# Tasks: DevOps Voice Tutor Web Application

## 1. Project Scaffolding & Docker Observability Infrastructure

- [x] 1.1 Create `.env.example` containing all required secrets (`LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `OPENAI_API_KEY`, `DEEPGRAM_API_KEY`, `ELEVENLABS_API_KEY`, `VOICE_PIPELINE_MODE`) and verify zero hardcoded defaults in code.
- [x] 1.2 Create Prometheus (`prometheus.yml`), Loki (`loki-config.yaml`), and Grafana provisioning configuration files (datasources and 3 dashboards: Web Infra, Voice Latency Waterfall, Tutor CSAT).
- [x] 1.3 Create `docker-compose.yml` orchestrating `frontend`, `backend`, `agent`, `redis`, `prometheus`, `loki`, and `grafana` containers.

## 2. Backend Session API & Redis State Manager

- [x] 2.1 Implement `backend/` FastAPI application with LiveKit JWT room token generation endpoint (`POST /api/token`) and environment configuration validation.
- [x] 2.2 Implement `RedisSessionRepository` managing session metadata, conversation turn history (`RPUSH`), summary notes, and CSAT feedback (`session:<id>:*`).
- [x] 2.3 Implement CSAT feedback submission endpoint (`POST /api/session/{id}/feedback`) and instrument `/metrics` endpoint with `prometheus_client`.

## 3. LiveKit Agent Worker & Voice Pipeline

- [x] 3.1 Implement `agent/src/tutor_prompts.py` containing Socratic SRE persona prompts and structured JSON control tags for visual workspace output (`[DIAGRAM: ...]`, `[YAML: ...]`).
- [x] 3.2 Implement `VoicePipelineFactory` supporting both Direct Speech-to-Speech (`MultimodalAgent`) and Modular (`VoicePipelineAgent`) based on `VOICE_PIPELINE_MODE` in `.env`.
- [x] 3.3 Implement WebRTC Data Channel emitter publishing visual payloads to the frontend, syncing turns asynchronously to Redis, and recording E2E turn latency metrics to Prometheus.

## 4. Frontend Web UI & Visual Workspace

- [x] 4.1 Create `frontend/` React + Vite Web Application with modern dark-mode CSS styling and LiveKit WebRTC audio connection components (`@livekit/components-react`).
- [x] 4.2 Implement Interactive DevOps Visual Workspace component with real-time Mermaid.js diagram rendering and syntax-highlighted YAML/code cards.
- [x] 4.3 Implement Post-Session CSAT Learner Feedback modal (star ratings, quick tag pills, comment text box) submitting responses to `POST /api/session/{id}/feedback`.

## 5. Documentation & Submission Deliverables

- [x] 5.1 Create `README.md` containing Architecture Overview (ASCII diagram), Key Design Decisions & Tradeoffs, 10,000 Concurrent Session Scaling Strategy, and Docker Compose launch instructions.
- [x] 5.2 Create `workflow.md` detailing the AI-assisted development process, models used (Gemini 3.6 Flash), harness tooling (OpenSpec spec-driven development), and Antigravity agent CLI capabilities.
- [x] 5.3 Copy exact user prompt verbatim to `PROMPT.md`.

## 6. End-to-End Verification & Conventional Commit Finalization

- [x] 6.1 Build and launch the complete stack with `docker compose up --build` and verify WebRTC voice streaming, Redis state writes, and Grafana dashboard metric visualization.
- [ ] 6.2 Audit git commit history for 100% adherence to Conventional Commits standards and push updates via Pull Request to `shayon83/devops-tutor`.
