# Proposal: Remediate Review Findings

## Why

A review of the v1.0 submission found three classes of problem:

1. **It did not build from a fresh clone.** `livekit-agents>=1.2.0` and the
   plugins were unpinned, so a new release pulled in a conflicting
   `prometheus-client`. Nothing in the repository would have caught it: there
   was no CI, and `docker-compose.yml` bind-mounted `./agent` over the image,
   so a local run never exercised the built image.
2. **A core requirement was unmet.** The assignment requires Redis as the
   backing state store for conversations. `RedisSessionRepository.append_turn()`
   existed but was never called, so no conversation was ever stored.
3. **The docs described a system that did not exist.** The README claimed
   direct speech-to-speech inference, the spec still carried
   `VOICE_PIPELINE_MODE` / `AGENT_DISPATCH_TYPE` / BYOK scenarios that had been
   removed, the Grafana dashboard plotted metrics nothing recorded, and
   `workflow.md` claimed "zero architecture drift" and "100% contract
   compliance" while the drift above was in the repository.

Several defects trace to APIs and model names that were assumed rather than
checked: `deepgram/flux-general` and `cartesia/sonic` are in the SDK's type
literals but are not the documented LiveKit Inference IDs, and Prometheus
metrics were recorded in the main process while jobs run in their own.

## What Changes

- Pin every runtime dependency exactly; drop the four unused provider plugins;
  move test-only dependencies to `requirements-dev.txt`.
- Remove the `./agent` bind mount; add `.dockerignore`; run the Python images
  as a non-root user; drop `build-essential`/`git`; remove `version:` from
  compose.
- Use documented LiveKit Inference model IDs, configurable from `.env`.
- Make the agent greet first, read the learner's subject from Redis, stream the
  visual-tag parser, drop unclosed tags, and strip tags exactly once.
- Persist every conversation turn to Redis from the agent with `redis.asyncio`;
  mark the session ended on shutdown; move the repository to `shared/state/`.
- Record `voice_tutor_e2e_latency_ms`, `voice_tutor_interruptions_total` and
  `voice_tutor_active_sessions_total` from real data, using Prometheus
  multiprocess mode; replace the per-session CSAT gauge with a histogram;
  remove the non-existent LiveKit scrape target.
- Remove the `devkey` credential fallback; fail fast on missing or placeholder
  configuration; scope CORS; generate room identity server-side; add `/ready`
  and container healthchecks.
- Rewrite the tests so they can fail: real Redis, no exception-to-skip.
- Add a GitHub Actions pipeline (lint, test, build, smoke, optional
  live-agent) and Dependabot.
- Rewrite `README.md`, this spec and `workflow.md` so every claim matches the
  code.

## Capabilities

### Modified Capabilities

- `devops-voice-tutor`: correcting the voice-pipeline, Redis persistence,
  visual-workspace, observability and packaging requirements to match a working
  implementation, and adding a continuous-integration requirement.

## Impact

- **`agent/`**: rewritten worker, factory, prompts, new `visual_tags.py` and
  `metrics.py`, new test suite.
- **`backend/`**: fail-fast config, middleware metrics, `/ready`, server-side
  session identity; `session_manager.py` removed.
- **`shared/state/`**: new shared Redis package (sync + async repositories).
- **`frontend/`**: transcript keying, `visual` topic filter, parser deleted.
- **`monitoring/`**: Prometheus targets, Grafana datasource uids, dashboard
  queries.
- **`.github/`**: new CI workflow, bake cache overlay, Dependabot.
- **Docs**: `README.md`, `workflow.md`, `.agents/AGENTS.md`, this spec.
