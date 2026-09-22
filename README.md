# DevOps Voice Tutor

[![CI](https://github.com/shayon83/devops-tutor/actions/workflows/ci.yml/badge.svg)](https://github.com/shayon83/devops-tutor/actions/workflows/ci.yml)

A real-time voice tutor for DevOps and SRE topics. You talk to it; it teaches
Socratically, draws the architecture as it explains, and keeps the transcript.

Built on **LiveKit Agents** (Python) with **LiveKit Inference** for STT, LLM
and TTS, a **FastAPI** token/session service, a **React + Vite** SPA, **Redis**
as the conversation store, and **Prometheus + Loki + Grafana** for
observability. Everything runs with `docker compose up --build`.

---

## Architecture

```text
                       WebRTC audio + data channel
  ┌──────────────────┐ <═════════════════════════════> ┌────────────────────┐
  │  React + Vite    │                                 │   LiveKit Cloud    │
  │  SPA (:3000)     │                                 │   (SFU + Inference)│
  └──────────────────┘                                 └────────────────────┘
          │ POST /api/token                                  ▲          │
          │ POST /api/session/{id}/feedback                  │ WebRTC   │ STT / LLM / TTS
          ▼                                                  │          ▼
  ┌──────────────────┐                                 ┌────────────────────┐
  │  FastAPI backend │                                 │  LiveKit agent     │
  │  (:8000)         │                                 │  worker (Python)   │
  └──────────────────┘                                 └────────────────────┘
          │ create_session                                   │ append_turn
          │ save_feedback                                    │ end_session
          ▼                                                  ▼
  ┌───────────────────────────────────────────────────────────────────────┐
  │  Redis  ·  session:<room>:metadata | :history | :feedback  (TTL 24h)   │
  └───────────────────────────────────────────────────────────────────────┘

  ┌──────────────┐  scrapes   ┌──────────────┐        ┌──────────────┐
  │  Prometheus  │ <───────── │ backend:8000 │        │  Promtail    │
  │  (:9090)     │            │ agent:8001   │        │ (docker logs)│
  └──────────────┘            └──────────────┘        └──────┬───────┘
          │                                                  │ pushes
          │  queries                                         ▼
          │                                           ┌──────────────┐
          └──────────────────┐             ┌────────> │  Loki (:3100)│
                             ▼             │ queries  └──────────────┘
                     ┌────────────────────┴─┐
                     │  Grafana (:3001)     │
                     └──────────────────────┘
```

**The voice pipeline is a cascade, not speech-to-speech.** Audio goes
STT → LLM → TTS, each hop served by LiveKit Inference, which is why the project
needs no third-party model API keys — only LiveKit Cloud credentials.

Separation of concerns:

| Concern | Lives in | Notes |
| --- | --- | --- |
| Session identity, tokens, CSAT | `backend/` | FastAPI; generates the room name and participant identity |
| Voice turns, teaching, visuals | `agent/` | LiveKit Agents worker; one OS process per job |
| Conversation state | `shared/state/` | One Redis key layout, copied into both images |
| UI | `frontend/` | React + Vite, served by nginx |
| Telemetry | `monitoring/` | Prometheus, Loki, Promtail, Grafana provisioning |

---

## Quick start

```bash
git clone https://github.com/shayon83/devops-tutor.git
cd devops-tutor
cp .env.example .env         # fill in LIVEKIT_URL / KEY / SECRET
docker compose up --build
```

Get free LiveKit Cloud credentials at <https://cloud.livekit.io>. The backend
refuses to start if they are missing or still set to the `.env.example`
placeholders, so a misconfigured stack fails loudly instead of handing out
tokens that can never connect.

| Service | URL |
| --- | --- |
| Web UI | <http://localhost:3000> |
| Backend API docs | <http://localhost:8000/docs> |
| Grafana | <http://localhost:3001> (`admin` / `GRAFANA_ADMIN_PASSWORD`) |
| Prometheus | <http://localhost:9090> |

Click **Start Voice Lesson**, allow the microphone, and the tutor greets you
first.

### Running the tests

```bash
pip install -r requirements-dev.txt
docker compose up -d redis     # the tests use a real Redis, and fail without one
pytest -q
```

### Optional dev override

`docker-compose.override.yml.example` bind-mounts the agent source over the
image so edits take effect on `docker compose restart agent`. Copy it to
`docker-compose.override.yml` (gitignored) if you want it. It is deliberately
not committed: an override that compose loads automatically is how an image
and the code it supposedly contains drift apart without anyone noticing.

---

## Key design decisions & tradeoffs

**LiveKit Inference instead of provider SDKs.** STT, LLM and TTS all resolve
through LiveKit Cloud, so a reviewer needs one set of credentials instead of
four, and the agent image carries no provider plugins. The tradeoff is a hard
dependency on LiveKit Cloud and on its model catalogue; the model IDs are in
`.env` (`STT_MODEL`, `LLM_MODEL`, `TTS_MODEL`) so they can be swapped without a
rebuild, and a unit test asserts each default exists in the SDK's model
literals so a guessed name cannot ship.

**Cascade (STT → LLM → TTS), not a realtime speech-to-speech model.** A cascade
costs some latency at each hop, but it gives a real text transcript of every
turn — which is what makes the Redis conversation store, the visual workspace
and the transcript panel possible at all. For a tutor, being able to show and
replay what was said is worth more than the last hundred milliseconds.

**Redis holds the conversation; nothing else does.** `session:<room>:metadata`
carries who and what subject, `:history` is the ordered turn list, `:feedback`
the CSAT. All three expire after `SESSION_TTL_SECONDS` (24h by default) — a
lesson is a transcript, not a system of record. The agent writes turns with
`redis.asyncio` so a slow Redis cannot stall the event loop that is carrying
audio, and every method degrades to a warning rather than an exception, so a
Redis outage costs you the recording, not the lesson.

**A shared `shared/state/` package rather than a per-service repository.** The
key layout is a contract between two services: the backend creates the session
at token time, the agent reads the subject back and appends turns. Two copies
of that layout drift silently, and a drifted key is invisible until someone
notices an empty history. Both images `COPY shared/`, and a test asserts the
agent reads the subject the backend wrote. The cost is that a change to the
package rebuilds both images.

**Inline visual tags, not a `show_visual` function tool.** The tutor appends
`[DIAGRAM: ...]`, `[YAML: ...]` or `[CARD: ...]` to its answer, and
`agent/src/visual_tags.py` lifts them out of the stream. A function tool would
be tidier to parse, but it forces the model to emit the tool call before it
speaks and then take a second inference pass, so the learner waits through an
extra round trip before hearing anything. A tag at the end of the reply lets
the spoken part stream first. The parser therefore has to be incremental:
text passes straight through, only the inside of an open tag is buffered, and
a tag that never closes is dropped rather than spoken.

**Stripped once, in `llm_node`.** Tags are removed upstream of TTS, the
transcription node and the chat context, so the spoken audio, the browser
transcript and the persisted history all see the same clean text and the
frontend needs no parser of its own.

**Server-generated room names.** The token endpoint takes only a subject; the
room name and participant identity come from the server, so a client cannot
name (or join) somebody else's room. The endpoint is unauthenticated because
this is a demo you should be able to run from a clean clone — see the scaling
section for what would have to change.

**Prometheus multiprocess mode.** LiveKit Agents runs each job in its own
process, so a counter incremented inside a job is invisible to a metrics
server in the parent. The worker starts with
`WorkerOptions(prometheus_port=..., prometheus_multiproc_dir=...)`, and a test
drives a real subprocess to prove samples written in a job reach the parent's
registry.

---

## Product choices

**Socratic, not lecturing.** A voice tutor that monologues is a podcast. The
system prompt caps answers at two or three sentences and requires a guiding
question, so the learner is doing the reasoning and the turn-taking stays
conversational — which is also what makes barge-in worth supporting.

**A visual workspace, because DevOps is diagrams.** You cannot say "the
ingress fronts a ClusterIP service which fronts three pods" out loud and expect
it to land. The tutor emits Mermaid diagrams, YAML manifests and summary cards
over the WebRTC data channel, rendered live beside the conversation. The
spoken text never reads the syntax aloud.

**A subject picker up front.** Five tracks (Kubernetes, CI/CD & GitOps,
observability, Terraform, Linux/SRE incident response). Choosing before you
start means the first question is already on-topic, instead of spending a turn
establishing what you want. The choice is written to Redis at token time and
read by the agent when the job starts.

**CSAT at the end of the lesson.** One to five stars plus quick tags, prompted
when the session ends. Tutoring quality is subjective and does not show up in
latency graphs; a rating per lesson is the cheapest honest signal of whether
the thing is any good, and it lands on the same Grafana dashboard as the
technical metrics so they can be read together.

---

## Observability

The Grafana dashboard (`DevOps Voice Tutor Overview & Telemetry`, provisioned
on startup) shows only metrics that are actually recorded:

| Metric | Source |
| --- | --- |
| `voice_tutor_e2e_latency_ms` | `ChatMessage.metrics["e2e_latency"]` on each assistant turn |
| `voice_tutor_interruptions_total` | `ChatMessage.interrupted` — the learner barging in |
| `voice_tutor_active_sessions_total` | agent job start / shutdown |
| `voice_tutor_csat_rating_stars` | the feedback endpoint (a Histogram; no per-session labels) |
| `http_requests_total`, `http_request_duration_seconds` | backend middleware, every route |

Prometheus scrapes `backend:8000` and `agent:8001`. There is no LiveKit scrape
target: LiveKit runs in LiveKit Cloud, which exposes no Prometheus endpoint.
Promtail reads container logs through the Docker API (`docker_sd_configs`) and
pushes them to Loki; Grafana reads from both.

---

## Scaling to 10,000 concurrent sessions

1. **LiveKit Inference is the first ceiling.** 10k concurrent sessions means
   10k concurrent STT streams and a comparable TTS rate. That needs negotiated
   capacity and per-model rate-limit headroom, fallback models configured for
   each hop, and a circuit breaker that degrades to text rather than queueing
   voice turns behind a rate limiter.
2. **Sessions per agent worker.** The default is one OS process per job, which
   is robust but costs hundreds of MB per session. At this scale you size
   workers by memory, not CPU, and run many replicas with
   `num_idle_processes` tuned so a new job does not pay process startup.
   LiveKit's job dispatcher spreads jobs across registered workers; workers
   scale on active job count, not CPU.
3. **Redis: one write per turn, so plan for the write rate.** At roughly a turn
   every few seconds per session that is thousands of writes per second. Use a
   managed cluster with `session:{<id>}:*` hash tags so a session's keys stay
   on one shard, keep the async client, batch the turn append and the TTL
   refresh into one pipeline (as the repository already does), and keep TTLs
   short. If the history has to outlive the lesson, stream it to object storage
   asynchronously rather than growing Redis.
4. **Keep metrics low-cardinality.** The per-session CSAT gauge in the original
   version would have created 10,000 time series an hour. Labels must be
   bounded: route templates, not paths; histograms, not per-entity gauges.
   Session-level detail belongs in logs and traces.
5. **The token endpoint needs auth and rate limiting.** Today it is open, which
   is fine for a demo and not fine at scale: it mints room-join credentials.
   Put it behind real user auth, rate-limit per account, and cap concurrent
   sessions per user.
6. **Region placement dominates perceived latency.** Voice is unforgiving —
   audio round-trips to the SFU, then to inference, then back. Run the SPA,
   the backend and the agent workers in the same regions as the LiveKit
   deployment and pin sessions regionally, with Redis replicated per region
   rather than one global instance.

Stateless pieces (the backend, the SPA) scale the boring way: more replicas
behind a load balancer.

---

## Verified vs not verified

**Verified by CI on every pull request** (`.github/workflows/ci.yml`):
ruff and hadolint pass; every compose image builds from a clean checkout with
no local layer cache and is scanned with Trivy, which fails the build on any
HIGH or CRITICAL vulnerability that has a fix available; the whole stack starts;
backend `/health` and `/ready` return 200; a token is issued and its session
appears in Redis with the right subject; the frontend serves the SPA; Prometheus
has no down targets except the agent; Grafana is healthy with the dashboard and
both datasource uids provisioned; the agent image imports its entrypoint and
constructs the Agent with the configured models. The test job runs the full
pytest suite against a real Redis service container.

**Not verified by CI**: an actual voice conversation. CI has no LiveKit
credentials, so the agent cannot register with LiveKit Cloud, audio never
flows, and nothing exercises STT, the LLM, TTS, barge-in or the visual
rendering end to end. There is an optional `live-agent` job that starts the
agent with real credentials and asserts it registers — it runs only if the
`LIVEKIT_URL` / `LIVEKIT_API_KEY` / `LIVEKIT_API_SECRET` repository secrets are
set, and never on fork pull requests. Everything beyond registration was
checked by hand against a real LiveKit Cloud project.

---

## Repository layout

```text
agent/        LiveKit agent worker: factory, prompts, visual-tag parser, metrics
backend/      FastAPI token + session API
shared/state/ Redis key layout and the sync + async repositories
frontend/     React + Vite SPA
monitoring/   Prometheus, Loki, Promtail and Grafana provisioning
openspec/     Spec-driven development artifacts (see workflow.md)
scripts/      CI env generator and a Playwright traffic simulator
```
