# AI-Assisted Engineering Workflow

This document records the AI tools, models and harnesses used to build the
**DevOps Voice Tutor**, how they were used, and — just as importantly — where
they got things wrong and what now catches that.

---

## Tools, models & harnesses

### 1. Primary AI model
- **Model**: **Gemini 3.6 Flash (High Reasoning)**
- **Role**: system design, architecture exploration, code generation, and test
  suite synthesis.

### 2. Autonomous agentic harness: Google Antigravity CLI (`agy`)
- **Harness**: **Google Antigravity Agentic Assistant**
- **Role**: pair programming, codebase inspection, terminal command execution,
  file editing and Git workflow automation.

### 3. Specification harness: OpenSpec (`openspec`)
- **Framework**: **OpenSpec Spec-Driven Development (SDD)**
- **Role**: structured planning and spec contracts — `proposal.md`,
  `specs/<capability>/spec.md`, `design.md`, `tasks.md` — with changes archived
  into a master specification.

---

## Step-by-step workflow

```text
+---------------------------------------------------------------------------------------+
|                              SPEC-FIRST AI WORKFLOW                                   |
+---------------------------------------------------------------------------------------+
|                                                                                       |
|  [ Step 1: Exploration ]      [ Step 2: Propose & Spec ]    [ Step 3: Spec-First PR ] |
|  /opsx-explore                /opsx-propose                 - Create feature branch   |
|  - Architectural design       - Generate proposal.md,       - Commit planning files   |
|  - Pipeline tradeoff            specs/devops-voice-tutor,   - Open PR on GitHub       |
|    analysis                     design.md & tasks.md        - Address review feedback |
|                                                                                       |
|  [ Step 4: Apply & Build ]    [ Step 5: Verification ]      [ Step 6: Archive & Merge]|
|  /opsx-apply                  - Run pytest suites           - openspec archive        |
|  - Task-by-task coding        - Lint + hadolint             - Squash & Merge PR       |
|  - Conventional Commits       - CI: build + smoke the stack - Delete feature branch   |
+---------------------------------------------------------------------------------------+
```

### Phase 1: Architecture exploration (`/opsx-explore`)
Analysed the tradeoffs between a realtime speech-to-speech model, a modular
BYOK pipeline (Silero VAD + Deepgram + an LLM + ElevenLabs), and LiveKit
Inference. Settled on a five-tier split: React SPA, FastAPI token/session
backend, Python LiveKit agent worker, Redis state, and a Prometheus/Loki/
Grafana telemetry stack.

### Phase 2: Spec-driven proposal (`/opsx-propose`)
Scaffolded the `create-devops-voice-tutor` change artifacts and wrote
`specs/devops-voice-tutor/spec.md` with `SHALL` contracts and BDD-style
`#### Scenario:` blocks.

### Phase 3: Spec-first pull request
Feature branch, Conventional Commits, planning artifacts committed before code,
PR opened on GitHub, review comments addressed, squash-merged.

### Phase 4: Implementation (`/opsx-apply`)
Implemented tasks in order, with `pytest` suites for token generation, the
agent factory and the CSAT feedback endpoint.

### Phase 5: Review and remediation
An independent review of the v1.0 submission found that the project did not
build from a fresh clone, that a core requirement was unmet, and that the docs
described a system that did not exist. The findings were worked as a single
spec-driven change (`remediate-review-findings`), which is where the CI
pipeline described below came from.

---

## Where the AI got it wrong, and how it was caught

The interesting part of using AI heavily is not the code it writes quickly; it
is the specific ways it is confidently wrong, and what you have to build to
notice.

**1. Guessed model names.** `factory.py` shipped with
`deepgram/flux-general` and `cartesia/sonic`. Both are plausible, both appear
in the SDK's type literals, and neither is the documented LiveKit Inference ID
(`deepgram/flux-general-en`, `cartesia/sonic-3`). Type checking could not catch
it because the literals still contain the old names; only a live call or the
documentation would have. *Caught by*: a human review comparing the code
against <https://docs.livekit.io/agents/models/>. *Now caught by*: a unit test
that asserts every default model ID is a member of the SDK's `STTModels` /
`LLMModels` / `TTSModels` literals, plus a rule in `.agents/AGENTS.md` to read
the installed SDK source rather than recall an API.

**2. A dependency conflict nobody could see.** `livekit-agents>=1.2.0` plus
four unpinned plugins meant a new release pulled in a `prometheus-client`
version that conflicted with the backend's. The build had worked on the machine
that built it, because `docker-compose.yml` bind-mounted `./agent` over the
image and Docker's local layer cache never re-resolved the requirements.
*Caught by*: someone trying to build from a clean clone. *Now caught by*: exact
pins, the bind mount removed, and a CI `build` job that resolves the
requirements from scratch on a runner with no cache.

**3. A design that was dropped in code but not in the spec.** The
`simplify-app-architecture` change removed `VOICE_PIPELINE_MODE` and
`AGENT_DISPATCH_TYPE` from the code, but its spec delta re-stated the old
requirement with all the BYOK and dual-pipeline scenarios still in it. Because
the archive step folds the delta into the master spec verbatim, the removed
design outlived the code it described by three changes, and then propagated
into `README.md` and `.agents/AGENTS.md`. *Now caught by*: a `## REMOVED
Requirements` section in the delta, and a note in `.agents/AGENTS.md` that a
change removing a capability must declare it.

**4. Plausible-looking telemetry that measured nothing.**
`voice_tutor_e2e_latency_ms` and `voice_tutor_interruptions_total` were
declared and exported but never recorded, so the Grafana panels were
permanently empty; `voice_tutor_active_sessions_total` only ever went up;
Prometheus scraped a `livekit:7880` that does not exist; and CSAT carried a
per-session label, which is unbounded cardinality. The dashboard looked
convincing precisely because a dashboard always does. There was also a subtler
one: LiveKit Agents runs each job in a separate process, so metrics recorded
inside a job would not have appeared on the parent's `/metrics` even once they
were recorded. *Now caught by*: the smoke job asserts Prometheus has no down
targets, and a test spawns a real subprocess to prove job-process samples reach
the parent registry.

**5. Tests that could not fail.** The backend tests passed with Redis stopped,
because every Redis error was caught and logged. The agent factory test wrapped
construction in `try/except` and turned any exception into `pytest.skip`, so
the guessed model names above sailed through it. In CI, where
`LIVEKIT_API_KEY` is unset, it would have skipped every time. Green tests were
reporting on nothing. *Now*: the suite runs against a real Redis and fails
rather than skipping when it is absent, and the factory test constructs the
agent with dummy credentials and lets exceptions propagate.

**6. Documentation as aspiration.** The README described "Direct
Speech-to-Speech LLM Inference" for a cascade, told the reader to set an
`OPENAI_API_KEY` that nothing reads, and hardcoded a personal LiveKit project
URL. This file previously claimed "Zero Architecture Drift" and "100% contract
compliance" while items 1–5 were sitting in the repository, and claimed pytest
coverage of "Redis history sync" and "pipeline switching" — neither of which
existed. Writing the documentation from the plan rather than from the code is
the failure mode, and it is an easy one when an assistant will happily produce
either.

The pattern across all six: AI-generated code fails in ways that look finished.
It compiles, it has tests, it has a dashboard, it has a README. What it lacks
is any mechanism that would notice the difference between working and merely
plausible.

---

## The guardrail that came out of this

`.github/workflows/ci.yml` runs on every pull request:

| Job | What it proves |
| --- | --- |
| `lint` | ruff, `docker compose config`, hadolint on all three Dockerfiles |
| `test` | the suite against a real Redis service container, no skips |
| `build` | every compose image builds from a clean checkout with no local cache |
| `smoke` | the stack comes up; `/health`, `/ready`, a token landing in Redis, the SPA, Prometheus targets, the Grafana dashboard, and the agent image constructing its Agent |
| `live-agent` | (optional, secrets-gated) the worker registers with LiveKit Cloud |

The `build` job is the one that matters most: it is the check that would have
caught the dependency conflict before it reached a reviewer, and it is the
reason the bind mount had to go. Dependabot raises dependency bumps, and these
jobs decide whether they land.

The remaining honest gap is stated in the README: CI cannot hold a voice
conversation. Everything past worker registration — STT, the LLM, TTS,
barge-in, the visual rendering — was verified by hand against a real LiveKit
Cloud project.
