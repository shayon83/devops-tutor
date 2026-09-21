# DevOps Voice Tutor - agent context & workspace rules

This repository contains the **DevOps Voice Tutor**, a real-time WebRTC voice
tutoring application built with LiveKit Agents, FastAPI, Redis, React + Vite,
and a Prometheus/Loki/Grafana telemetry stack.

## Architecture

The voice pipeline is a **cascade**: STT → LLM → TTS, with every hop served by
**LiveKit Inference** (`from livekit.agents import inference`). There is no
speech-to-speech mode, no bring-your-own-key path, and no dispatch toggle --
the agent worker runs in the compose stack and registers with LiveKit Cloud
using `LIVEKIT_URL`, `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET`.

Model IDs are configurable from `.env`:

| Variable | Default |
| --- | --- |
| `STT_MODEL` | `deepgram/flux-general-en` |
| `LLM_MODEL` | `openai/gpt-4o-mini` |
| `TTS_MODEL` | `cartesia/sonic-3` |

**Verify LiveKit APIs and model IDs against the installed SDK**
(`site-packages/livekit/agents/...`, currently `livekit-agents==1.8.2`) and
<https://docs.livekit.io>, not from memory. Guessed model names and guessed
APIs are the single largest source of defects this repository has had.
`agent/tests/test_factory.py` asserts each default model ID is a member of the
SDK's model literals, so a guess fails CI.

## Environment & run commands

- **Environment file**: `.env` (loaded via `dotenv`, zero hardcoded secrets).
  Every variable the code reads must appear in `.env.example`.
- **Full stack**: `docker compose up --build`
- **Tests**: `pip install -r requirements-dev.txt && docker compose up -d redis && pytest -q`
  The suite talks to a real Redis and **fails** (never skips) without one.
- **Lint**: `ruff check .` and `hadolint` on the three Dockerfiles.
- **CI**: `.github/workflows/ci.yml` runs lint, test, build, smoke and an
  optional secrets-gated live-agent job on every pull request.

## Directory structure

- `backend/`: FastAPI token issuer (`POST /api/token`), session endpoints
  (`/api/session/*`), `/health`, `/ready`, `/metrics`. Fails fast when LiveKit
  configuration is missing or still holds a placeholder.
- `agent/`: LiveKit Agents worker. `factory.py` builds the tutor agent,
  `visual_tags.py` is the streaming tag parser, `metrics.py` holds the
  Prometheus metrics, `tutor_prompts.py` the Socratic system prompt.
- `shared/state/`: the Redis key layout plus the sync (backend) and async
  (agent) repositories. Both images copy this package; it is the contract
  between the two services, so change it in one place.
- `frontend/`: React + Vite SPA. Mermaid rendering, YAML preview, transcript
  panel and the CSAT modal. The start button reads **"Start Voice Lesson"**.
- `monitoring/`: Prometheus (scrapes `backend:8000` and `agent:8001` only --
  LiveKit Cloud exposes no scrape endpoint), Loki, Promtail and Grafana
  provisioning. Grafana is published on port **3001**.
- `openspec/`: OpenSpec artifacts, master specification at
  `openspec/specs/devops-voice-tutor/spec.md`.

## OpenSpec SDD workflow rules

- **Source of truth**: consult `openspec/specs/devops-voice-tutor/spec.md`
  before making architectural changes.
- **Proposing**: `/opsx-propose` or `openspec new change <name>`.
- **Applying & syncing**: `/opsx-apply`, then `openspec archive <name>` to fold
  the delta into the master spec.
- A change that removes a capability must carry a `## REMOVED Requirements`
  section. The `simplify-app-architecture` change dropped `VOICE_PIPELINE_MODE`
  and `AGENT_DISPATCH_TYPE` from the code but not from the spec, and the stale
  requirements survived for two more changes.
