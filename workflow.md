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
An independent review using Claude Opus 5 of the v1.0 submission found that the project did not
build from a fresh clone, that a core requirement was unmet, and that the docs
described a system that did not exist. The findings were worked as a single
spec-driven change (`remediate-review-findings`), which is where the CI
pipeline below came from.

### Phase 6: Manual Review and doc updates
Go over the files and docs manually and make minor adjustments to docs along with a high level review of the code.
