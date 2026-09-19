# Proposal: DevOps Voice Tutor Web Application

## Why

Students and engineers learning DevOps need an interactive, low-latency, voice-first learning experience that combines natural conversational instruction with real-time visual architectural feedback. This project delivers an enterprise-grade, assessment-ready DevOps Voice Tutor application utilizing LiveKit for real-time WebRTC audio, Direct Speech-to-Speech LLM inference, Redis for state persistence, and a full Grafana observability stack, all runnable with a single `docker compose up` command.

## What Changes

- **WebRTC Voice Pipeline & Agent**: Real-time voice conversation layer powered by LiveKit Agents and Direct Speech-to-Speech LLM (OpenAI/Gemini Realtime API), with a configurable `.env` fallback toggle for modular (STT -> LLM -> TTS) pipelines.
- **DevOps Socratic Persona & Visual Workspace**: Custom Socratic SRE system prompts and live interactive Web UI rendering real-time Mermaid.js architecture diagrams, YAML manifests, and syntax-highlighted code cards via LiveKit Data Packets.
- **Session & Conversation State (Redis)**: Decoupled session manager and history repository using Redis 7 to persist turns, user preferences, takeaways, and post-session feedback.
- **Observability Stack (Prometheus + Loki + Grafana)**: Complete monitoring suite in Docker Compose tracking RED signals (request rate, error rate, duration), End-to-End voice turn latency, barge-in rates, speech ratios, and CSAT ratings.
- **Post-Session Learner CSAT Feedback**: Interactive post-lesson evaluation collecting star ratings, qualitative tags, and user comments exported to Redis and Prometheus.
- **Submission & Deployment Packaging**: Single-command `docker-compose.yml`, zero-hardcoded secret `.env.example`, `README.md` (Architecture, Tradeoffs, 10k Session Scaling), `workflow.md` (OpenSpec + Antigravity AI workflow), and `PROMPT.md`.

## Capabilities

### New Capabilities
- `devops-voice-tutor`: Interactive voice tutoring application featuring real-time WebRTC audio, Socratic DevOps persona, live Mermaid/YAML visual workspace, Redis state persistence, Prometheus/Grafana telemetry, and Docker Compose packaging.

### Modified Capabilities
*(None - Greenfield project)*

## Impact

- **Frontend**: React + Vite + Vanilla CSS application utilizing `@livekit/components-react`, `mermaid`, and `react-syntax-highlighter`.
- **Backend**: Python FastAPI token & session server providing room JWT tokens, session lifecycle, and Prometheus metrics.
- **Agent Worker**: Python LiveKit Agent worker handling real-time audio streaming, Socratic prompt orchestration, data packet emission, and Redis sync.
- **Databases & Telemetry**: Redis 7 Alpine, Prometheus, Grafana, Loki.
- **Packaging & CI/CD**: `docker-compose.yml`, `.env.example`, GitHub CLI PR & Codeowner branch protection rules.
