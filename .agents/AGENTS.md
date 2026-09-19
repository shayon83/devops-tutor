# DevOps LLM Voice Tutor - AGY Agent Context & Workspace Rules

This repository contains the **DevOps LLM Voice Tutor**, an assessment-ready real-time WebRTC voice application built with LiveKit, FastAPI, Redis, React + Vite, and a Prometheus/Loki/Grafana telemetry stack.

## Architecture Overview & 2D Matrix Configuration

The agent worker architecture is governed by a **2D Orthogonal Settings Matrix**:

1. **`VOICE_PIPELINE_MODE`** (`realtime` | `modular`)
   - `realtime`: Direct Speech-to-Speech (S2S) multimodal audio session via Azure OpenAI or standard OpenAI Realtime WebRTC model (~350ms latency).
   - `modular`: Cascaded pipeline using Silero VAD + Deepgram STT + LLM (GPT-4o-mini/Gemini) + ElevenLabs/OpenAI TTS.

2. **`AGENT_DISPATCH_TYPE`** (`local` | `cloud`)
   - `local`: Self-hosted agent worker running inside local Docker Compose or `.venv` container listening for SFU job assignments.
   - `cloud`: Serverless agent worker dispatched via LiveKit Cloud Agents infrastructure.

## Environment & Run Commands

- **Python Virtualenv**: `.venv` (Python 3.10 required due to PyO3 compatibility).
- **Environment File**: `.env` (loaded strictly via `dotenv`, zero hardcoded secrets).
- **Local Multi-Container Stack**: `docker compose up --build`
- **Backend API Tests**: `pytest backend/tests/` (Redis calls wrapped for offline test resilience).
- **Agent Factory Tests**: `pytest agent/tests/`

## Core Directory Structure

- `backend/`: FastAPI token issuer (`POST /api/token`), session management (`/api/session/*`), and Redis repository.
- `agent/`: LiveKit Agent worker, `VoicePipelineFactory`, Socratic SRE prompts, and `DataTrack` visual card/diagram emitter.
- `frontend/`: React + Vite SPA featuring visual workspace (Mermaid.js SVG rendering + YAML cards) and CSAT feedback modal.
- `monitoring/`: Prometheus (`8000`, `8001`, LiveKit SFU scrape targets), Loki, Promtail, and Grafana dashboard provisioning (port `3001`).
- `openspec/`: OpenSpec spec-driven SDD harness with master specification at `openspec/specs/devops-voice-tutor/spec.md`.

## OpenSpec SDD Workflow Rules for AGY

- **Specification Source of Truth**: Always consult `openspec/specs/devops-voice-tutor/spec.md` before making architectural or spec changes.
- **Proposing Changes**: Use `/opsx-propose` or `openspec new change <name>`.
- **Applying & Syncing**: Use `/opsx-apply` and `openspec archive <name>` to sync deltas into master specs.
