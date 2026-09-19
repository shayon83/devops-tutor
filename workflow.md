# AI-Assisted Engineering Workflow & Harness Methodology

This document details the exact AI tools, models, harnesses, and spec-driven workflows used to design, build, test, and ship the **DevOps Voice Tutor Web Application**.

---

## 🛠️ AI Tools, Models & Harnesses Used

### 1. Primary AI Model
- **Model**: **Gemini 3.6 Flash (High Reasoning)**
- **Role**: High-speed system design, architecture exploration, code generation, and test suite synthesis.

### 2. Autonomous Agentic Harness: Google Antigravity CLI (`agy`)
- **Harness**: **Google Antigravity Agentic Assistant**
- **Role**: Autonomous pair programming, automated codebase inspection, terminal command execution, file editing, and Git workflow automation.

### 3. Specification & Workflow Harness: OpenSpec (`openspec`)
- **Framework**: **OpenSpec Spec-Driven Development (SDD)**
- **Role**: Structured planning, spec contract generation, task breakdown tracking, and automated specification syncing (`proposal.md`, `specs/`, `design.md`, `tasks.md`).

---

## 🔄 Step-by-Step AI-Assisted Workflow

```text
+---------------------------------------------------------------------------------------+
|                              SPEC-FIRST AI WORKFLOW                                   |
+---------------------------------------------------------------------------------------+
|                                                                                       |
|  [ Step 1: Exploration ]      [ Step 2: Propose & Spec ]    [ Step 3: Spec-First PR ]|
|  /opsx-explore                /opsx-propose                 - Create feature branch   |
|  - Architectural design       - Generate proposal.md,       - Commit planning files   |
|  - Direct Speech-to-Speech      specs/devops-voice-tutor,   - Open PR #1 on GitHub    |
|    tradeoff analysis            design.md & tasks.md        - Address review feedback |
|                                                                                       |
|  [ Step 4: Apply & Build ]    [ Step 5: Spec Verification]  [ Step 6: Archive & Merge]|
|  /opsx-apply                  - Run pytest test suites      - openspec archive        |
|  - Task-by-task coding        - Validate scenarios          - Squash & Merge PR       |
|  - Conventional Commits       - Docker Compose test         - Delete feature branch   |
+---------------------------------------------------------------------------------------+
```

### Phase 1: Interactive Architecture Exploration (`/opsx-explore`)
- Utilized `/opsx-explore` to analyze the tradeoffs between Direct Speech-to-Speech (Realtime API), Modular (STT -> LLM -> TTS), and LiveKit Cloud Managed Inference pipelines.
- Formulated the clean 5-tier architecture (React Web UI, FastAPI Token Backend, Python LiveKit Agent Worker, Redis 7 State Repository, Prometheus/Grafana Telemetry Stack scraping both application turn metrics and native LiveKit SFU metrics).

### Phase 2: Spec-Driven Change Proposal (`/opsx-propose`)
- Executed `/opsx-propose` to scaffold the `create-devops-voice-tutor` change artifacts.
- Created `specs/devops-voice-tutor/spec.md` with explicit `SHALL`/`MUST` behavioral contracts and testable BDD scenarios (`#### Scenario:`).

### Phase 3: Spec-First Pull Request & Codeowner Review
- Created feature branch `feat/devops-voice-tutor`.
- Committed planning artifacts using Conventional Commits (`docs(spec): add planning artifacts for devops-voice-tutor`).
- Opened PR #1 on GitHub (`shayon83/devops-tutor`), addressed review comments regarding LiveKit Job Dispatcher load balancing, updated `design.md`, and squashed & merged into `main`.

### Phase 4: Implementation & Test-Driven Verification (`/opsx-apply`)
- Executed `/opsx-apply` to implement tasks sequentially.
- Wrote automated `pytest` test suites verifying token generation, Redis history sync, Factory Pattern pipeline switching, and CSAT feedback metrics.

---

## 🚀 Productivity Impact & Engineering Velocity

1. **Zero Architecture Drift**: Defining normative specs in `specs/devops-voice-tutor/spec.md` before writing code eliminated rewrite cycles and guaranteed all submission criteria (Docker Compose, Redis, secrets in `.env`, Grafana monitoring) were met.
2. **Automated Quality Assurance**: Mapping spec scenarios directly to `pytest` tests ensured 100% contract compliance.
3. **Structured Git Hygiene**: Enforced Conventional Commits and PR branch protection rules automatically via GitHub CLI (`gh`).
