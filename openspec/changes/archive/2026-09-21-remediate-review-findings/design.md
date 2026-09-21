# Technical Design: Remediate Review Findings

## Context

See `proposal.md` for motivation. The recurring theme is that nothing in the
repository could tell the difference between "works" and "works on the machine
that built it": no CI, a bind mount hiding the image, unpinned dependencies,
tests that passed with Redis stopped, and a factory test that converted any
exception into a skip.

## Goals / Non-Goals

**Goals:**
- A fresh clone plus a filled-in `.env` builds and starts with `docker compose up --build`.
- Redis actually stores the conversation, as the assignment requires.
- Every API and model name used is verified against the installed SDK.
- Every metric on the dashboard is one the code records.
- CI proves the build and the boot without a local cache.
- Every documented claim is true.

**Non-Goals:**
- Authenticating the token endpoint (documented as a demo tradeoff instead).
- Replacing the cascade with a realtime speech-to-speech model.
- Any redesign of the UI beyond the transcript and data-channel fixes.

## Decisions

### Decision 1: Pin exactly, and let CI prove it

Pin `livekit-agents==1.8.2` and every other direct runtime dependency. The
`build` CI job does a clean-checkout `docker buildx bake` over the compose
file, so a future conflict fails a pull request rather than a reviewer's clone.

**Alternative considered:** a `uv`/`pip-tools` lockfile. Rejected for a
project this size: exact pins on a handful of direct dependencies give the same
reproducibility without adding a tool to the contributor's path.

### Decision 2: `shared/state/` rather than a second repository in the agent

The `session:<room>:*` layout is a contract between the backend (creates the
session) and the agent (reads the subject, appends turns, marks it ended). Two
copies drift silently, and a drifted key shows up only as an empty history.
Both images `COPY shared/`; a test asserts the agent reads what the backend
wrote. The cost is that changing the package rebuilds both images, which is
acceptable at this size.

**Alternative considered:** a thin agent-local repository. Cheaper to build,
but it reintroduces exactly the duplication that the frontend tag parser had
already demonstrated the cost of.

### Decision 3: Inline visual tags, stripped in `llm_node`

Keeping inline tags over a `show_visual` function tool: a tool call makes the
model emit the call before speaking and then take a second inference pass, so
the learner waits an extra round trip. A tag at the end of the reply lets the
spoken part stream first.

That makes the parser's incremental behaviour load-bearing:
`agent/src/visual_tags.py` passes text through, buffers only inside an open
tag, holds back a partial opener across a chunk boundary, and drops a tag that
never closes.

Stripping happens in an `llm_node` override rather than in `tts_text_transforms`
because `llm_node` is upstream of the TTS node, the transcription node and the
chat context. One strip, so the audio, the browser transcript and the Redis
history agree, and the frontend needs no parser.

### Decision 4: Prometheus multiprocess mode

LiveKit Agents runs each job in a separate process
(`WorkerOptions.multiprocessing_context`), so a `start_http_server` in the
parent never sees a counter incremented in a job. The worker is started with
`prometheus_port` and `prometheus_multiproc_dir`; the SDK's `/metrics` handler
aggregates with `MultiProcessCollector` when `PROMETHEUS_MULTIPROC_DIR` is set.
The active-sessions gauge uses `multiprocess_mode="livesum"` so it reports one
total rather than one series per PID. A test drives a real subprocess to prove
the samples cross the boundary.

### Decision 5: Fail fast on configuration

`backend/src/config.py` raises at import when a LiveKit variable is missing or
still holds its `.env.example` placeholder. A stack that cannot possibly work
should say so at startup, not mint tokens that fail at connect time. The
consequence is that CI cannot boot the stack from a verbatim `.env.example`
copy, so `scripts/ci-dummy-env.sh` substitutes fake-but-valid credentials and
fails if a variable it expects has disappeared from the template.

### Decision 6: Verify every SDK API against the installed source

Model IDs, `ConversationItemAddedEvent`, `MetricsReport.e2e_latency`,
`ChatMessage.interrupted`, `publish_data(topic=...)`,
`ctx.add_shutdown_callback` and the `prometheus_*` worker options were all read
out of `site-packages/livekit/agents/...` for version 1.8.2 rather than
recalled. `agent/tests/test_factory.py` asserts each default model ID is a
member of the SDK's `STTModels` / `LLMModels` / `TTSModels` literals, so a
guessed name fails CI instead of failing a live demo.

## Risks / Trade-offs

- **Pinned to `livekit-agents==1.8.2`.** Dependabot raises the bump; CI's
  build and test jobs decide whether it lands.
- **CI cannot verify a voice conversation.** With dummy credentials the agent
  cannot register with LiveKit Cloud. Mitigated by an optional secrets-gated
  `live-agent` job and by saying so plainly in the README.
- **`llm_node` override couples to an SDK extension point.** If its signature
  changes, the agent tests fail loudly rather than silently degrading.
