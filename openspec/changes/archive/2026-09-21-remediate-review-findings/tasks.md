# Tasks

## 1. Make it build

- [x] 1.1 Pin `livekit-agents==1.8.2` and every direct runtime dependency; remove the unused openai/deepgram/elevenlabs/silero plugins; move pytest and test-only deps to `requirements-dev.txt`. Verified with `pip check` on the agent, backend and combined dev sets.
- [x] 1.2 Remove the `./agent:/app/agent` bind mount from `docker-compose.yml` and ship the dev override as `docker-compose.override.yml.example`, with the real file gitignored so a fresh clone and CI cannot load it.
- [x] 1.3 Add `.dockerignore` at the repo root (and one for the frontend context) excluding `.git`, `.env`, `node_modules`, `.venv`, caches and `openspec/`.
- [x] 1.4 Drop `build-essential`, `git` and `curl` from the agent image, run the Python images as uid 10001, remove the obsolete `version:` key. Verified with `hadolint` on all three Dockerfiles.

## 2. Make the voice agent work

- [x] 2.1 Switch to `deepgram/flux-general-en` and `cartesia/sonic-3`, configurable via `STT_MODEL`/`LLM_MODEL`/`TTS_MODEL`. Verified against the SDK model literals by `agent/tests/test_factory.py`.
- [x] 2.2 Greet the learner via `session.generate_reply(...)` after `session.start`; delete the fake welcome line from `App.jsx`.
- [x] 2.3 Read the subject from `session:<room>:metadata` on job start and fold it into the instructions.
- [x] 2.4 Rewrite the visual-tag handling as `agent/src/visual_tags.py`: streaming, unclosed tags dropped, stripped once in `llm_node`, published with `topic="visual"` and awaited. Unit tests cover nested brackets, YAML lists, unclosed tags, no tags and streaming equivalence.
- [x] 2.5 Key transcripts by `segment.id`, update in place, carry `segment.final`; filter data messages on the `visual` topic and delete the frontend parser.

## 3. Redis as the conversation store

- [x] 3.1 Persist each user/assistant `ChatMessage` from `conversation_item_added` to `session:<room>:history`.
- [x] 3.2 Use `redis.asyncio` in the agent, with bounded timeouts and a capped retry policy.
- [x] 3.3 Move the repository to `shared/state/`, copied by both images; delete `backend/src/session_manager.py`.
- [x] 3.4 Mark the session `ended` with `ended_at` in the job shutdown callback.
- [x] 3.5 Make `get_session_summary` degrade gracefully; add `/ready`, which pings Redis, separate from `/health`.
- [x] 3.6 Give Redis a named volume with `appendonly yes` and a healthcheck; stop publishing 6379 to the host.

## 4. Observability that tells the truth

- [x] 4.1 Record `voice_tutor_e2e_latency_ms` from `ChatMessage.metrics["e2e_latency"]` and `voice_tutor_interruptions_total` from `ChatMessage.interrupted`.
- [x] 4.2 Start the worker with `prometheus_port` and `prometheus_multiproc_dir`; prove with a subprocess test that job-process samples reach the parent registry.
- [x] 4.3 Track `voice_tutor_active_sessions_total` in the agent (up on job start, down on shutdown); remove it from the token endpoint.
- [x] 4.4 Replace the per-session CSAT gauge with a histogram.
- [x] 4.5 Remove the `livekit:7880` scrape target and retitle the health panel to count the two real targets.
- [x] 4.6 Move backend request metrics into middleware so every route is covered.
- [x] 4.7 Take the Grafana admin password from `.env`; set explicit datasource uids and reference them from the dashboard JSON.
- [x] 4.8 Remove promtail's `/var/lib/docker/containers` bind mount; `docker_sd_configs` does not need it.

## 5. Security and config cleanup

- [x] 5.1 Remove the `devkey`/`secretsecret...` fallback; fail fast on missing or placeholder LiveKit credentials.
- [x] 5.2 Remove `voice_pipeline_mode`; wire `BACKEND_PORT`/`FRONTEND_PORT` into compose so they are no longer decorative.
- [x] 5.3 Scope CORS to `CORS_ALLOW_ORIGINS`; generate the room name and participant identity server-side; bound the subject and rating.
- [x] 5.4 Add backend and frontend healthchecks with `depends_on: condition: service_healthy`.

## 6. Tests

- [x] 6.1 Run backend and shared-store tests against a real Redis, asserting metadata, history and feedback round-trip.
- [x] 6.2 Unit-test the turn-persistence handler, the visual publisher and the `llm_node` strip-and-publish path with a fake room and repository.
- [x] 6.3 Set dummy credentials in the agent test suite so it can never skip, and remove the exception-to-skip in the factory test.

## 7. CI

- [x] 7.1 Add `.github/workflows/ci.yml` with `lint`, `test`, `build`, `smoke` and an optional secrets-gated `live-agent` job.
- [x] 7.2 Add a CI badge to the README and enable Dependabot for pip, npm, docker and github-actions.

## 8. Docs

- [x] 8.1 Rewrite `README.md`: honest architecture diagram (Promtail → Loki, Grafana reading both), cascade rather than speech-to-speech, design decisions, product choices, a real 10k-session section, and a "verified vs not verified" note.
- [x] 8.2 Rewrite this capability spec and `.agents/AGENTS.md` to drop `VOICE_PIPELINE_MODE`, `AGENT_DISPATCH_TYPE`, BYOK, speech-to-speech and the LiveKit server-metrics claims; fix the Grafana port and the button label.
- [x] 8.3 Rewrite `workflow.md`: remove the false claims and add an honest account of where the AI got things wrong and how CI became the guardrail.
